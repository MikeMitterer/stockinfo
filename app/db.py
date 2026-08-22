"""SQLite-Anbindung und Schema-Initialisierung.

Kapselt Verbindungsaufbau und Schema. Raw-SQL für Fachlogik gehört in die
Repository-Schicht (repository.py), nicht hierher.
"""

import sqlite3
import uuid
from pathlib import Path

import structlog

from app.models import OVERRIDE_FIELDS
from app.exchanges import split_symbol

logger = structlog.get_logger()

# Schema — instruments (langsam veränderliche Metadaten) + quotes (Zeitreihe).
_SCHEMA = """
CREATE TABLE IF NOT EXISTS instruments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    isin            TEXT UNIQUE,
    symbol          TEXT NOT NULL,
    exchange        TEXT,
    name            TEXT,
    type            TEXT,
    currency        TEXT,
    provider        TEXT,
    ter             REAL,
    replication     TEXT,
    fund_size       REAL,
    volatility      REAL,
    accumulating    INTEGER,
    fund_domicile   TEXT,
    fund_currency   TEXT,
    source          TEXT,
    first_seen      TEXT NOT NULL,
    meta_fetched_at TEXT
);

CREATE TABLE IF NOT EXISTS quotes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id INTEGER NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    price         REAL NOT NULL,
    quote_time    TEXT NOT NULL,
    volume        INTEGER,
    currency      TEXT,
    fetched_at    TEXT NOT NULL,
    UNIQUE (instrument_id, quote_time)
);

CREATE INDEX IF NOT EXISTS idx_quotes_instrument_time
    ON quotes (instrument_id, quote_time DESC);

CREATE TABLE IF NOT EXISTS daily_closes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id INTEGER NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    date          TEXT NOT NULL,
    close         REAL NOT NULL,
    currency      TEXT,
    UNIQUE (instrument_id, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_instrument_date
    ON daily_closes (instrument_id, date);

CREATE TABLE IF NOT EXISTS daily_meta (
    instrument_id INTEGER PRIMARY KEY REFERENCES instruments(id) ON DELETE CASCADE,
    fetched_from  TEXT,
    fetched_to    TEXT
);

-- Von Hand nachgetragene Kennzahlen.
--
-- Bewusst eine eigene Tabelle statt zusätzlicher Spalten in `instruments`:
-- Der Hintergrund-Refresh schreibt dort bei jeder Runde, und ein manueller
-- Wert, der in derselben Zeile steht, wäre eine Zeile vom nächsten Upsert
-- entfernt. Getrennt kann der Refresh nichts überschreiben, was er nicht kennt.
--
-- NULL heißt „nicht gepflegt" — nicht „0" und nicht „nein".
CREATE TABLE IF NOT EXISTS instrument_overrides (
    instrument_id INTEGER PRIMARY KEY REFERENCES instruments(id) ON DELETE CASCADE,
    ter           REAL,
    volatility    REAL,
    accumulating  INTEGER,
    provider      TEXT,
    replication   TEXT,
    fund_size     REAL,
    fund_domicile TEXT,
    fund_currency TEXT,
    updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fx_rates (
    base       TEXT NOT NULL,
    quote      TEXT NOT NULL,
    rate       REAL NOT NULL,
    quote_time TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (base, quote)
);
"""


def get_connection(database_path: str) -> sqlite3.Connection:
    """Öffnet eine SQLite-Verbindung und legt das Zielverzeichnis bei Bedarf an.

    Args:
        database_path: Pfad zur SQLite-Datei (z.B. 'data/stockinfo.db').

    Returns:
        Verbindung mit Row-Factory (Zugriff per Spaltenname), aktivierten
        Foreign-Keys und WAL-Modus (Request-Threadpool und Scheduler schreiben
        parallel).
    """
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=10.0, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def init_db(database_path: str) -> None:
    """Erstellt das Datenbankschema, falls es noch nicht existiert.

    Args:
        database_path: Pfad zur SQLite-Datei.
    """
    connection = get_connection(database_path)
    try:
        connection.executescript(_SCHEMA)
        _migrate(connection)
        connection.commit()
    finally:
        connection.close()


def _migrate(connection: sqlite3.Connection) -> None:
    """Ergänzt fehlende Spalten/Indizes in bestehenden Datenbanken (idempotent)."""
    _add_missing_columns(
        connection,
        "instruments",
        (
            ("volatility", "REAL"),
            ("accumulating", "INTEGER"),
            ("fund_domicile", "TEXT"),
            ("fund_currency", "TEXT"),
            # Woher die Kennzahlen stammen ('yfinance' bzw. 'yfinance+justetf').
            # Der Detailbereich nennt das; ohne Nachzug bliebe die Angabe auf jeder
            # bestehenden Datenbank für immer leer.
            ("source", "TEXT"),
        ),
    )
    # Die Override-Tabelle wuchs mit: Nachgetragen wird jetzt alles, was
    # justETF beisteuert — nicht mehr nur die drei aus T-09.
    _add_missing_columns(
        connection,
        "instrument_overrides",
        (
            ("provider", "TEXT"),
            ("replication", "TEXT"),
            ("fund_size", "REAL"),
            ("fund_domicile", "TEXT"),
            ("fund_currency", "TEXT"),
        ),
    )

    _migrate_identity(connection)


# Die kanonische Identität aus T-21. `identity_status` sagt, ob sie feststeht.
_IDENTITY_RESOLVED = "resolved"
_IDENTITY_UNRESOLVED = "legacy_unresolved"


def _migrate_identity(connection: sqlite3.Connection) -> None:
    """Legt `(ticker, mic)` neben `symbol` und vergibt jede `listing_id`.

    Der Identifikator eines Papiers war bisher das Yahoo-Symbol — in der
    Datenbank, in der API, im Dashboard. Damit wäre yfinance nicht ersetzbar,
    sondern nur ergänzbar: Jede zweite Kursquelle müsste Yahoos
    Suffix-Schreibweise nachbilden.

    **Melden statt raten.** Zerlegt wird nur, was die eigene Börsentabelle
    eindeutig hergibt. Alles andere bleibt offen (`legacy_unresolved`) und
    wird protokolliert; der Datensatz bleibt dabei lesbar und nutzbar. Ohne
    diesen Zwischenzustand müsste die Migration raten, den Start blockieren
    oder Daten löschen — genau die drei Auswege, die T-21 ausschließt.

    Der Index zieht mit: Der globale `UNIQUE` auf `symbol` hielt Yahoo in der
    Identität und weicht `(ticker, mic)`. Dass mehrere offene Zeilen dort
    `NULL` tragen, ist kein Konflikt — SQLite behandelt `NULL` in eindeutigen
    Indizes als jeweils eigenen Wert.
    """
    _add_missing_columns(
        connection,
        "instruments",
        (
            ("ticker", "TEXT"),
            ("mic", "TEXT"),
            # Opake UUID, bei Anlage einmal erzeugt und nicht aus ticker, mic,
            # ISIN oder dem lokalen Schlüssel abgeleitet (Vertrag in T-24).
            ("listing_id", "TEXT"),
            ("identity_status", "TEXT"),
        ),
    )

    for row in connection.execute(
        "SELECT id, symbol, listing_id, identity_status FROM instruments"
    ).fetchall():
        if not row["listing_id"]:
            connection.execute(
                "UPDATE instruments SET listing_id = ? WHERE id = ?",
                (str(uuid.uuid4()), row["id"]),
            )
        if row["identity_status"]:
            continue  # schon einmal betrachtet — Bestand nicht überschreiben
        ticker, mic = split_symbol(row["symbol"])
        connection.execute(
            "UPDATE instruments SET ticker = ?, mic = ?, identity_status = ? "
            "WHERE id = ?",
            (
                ticker,
                mic,
                _IDENTITY_RESOLVED if mic else _IDENTITY_UNRESOLVED,
                row["id"],
            ),
        )

    # Erst jetzt bereinigen: Vorher stünde die kanonische Identität noch nicht
    # in der Zeile, und die Bereinigung müsste wieder nach `symbol` gruppieren
    # — genau der Fehler, den sie seit T-21 nicht mehr machen darf.
    _dedupe_symbols(connection)

    connection.execute("DROP INDEX IF EXISTS idx_instruments_symbol")
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_instruments_ticker_mic "
        "ON instruments (ticker, mic)"
    )
    # Die `listing_id` ist der Maschinenschlüssel des öffentlichen Vertrags.
    # Ohne Index wäre „opake UUID, einmal erzeugt" eine Absichtserklärung: Ein
    # zweiter Schreiber könnte denselben Wert eintragen, und wer darüber
    # adressiert, bekäme zwei Papiere.
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_instruments_listing_id "
        "ON instruments (listing_id)"
    )
    _report_unresolved(connection)


def _report_unresolved(connection: sqlite3.Connection) -> None:
    """Protokolliert die offenen Zuordnungen — sonst weiß niemand von ihnen.

    „Später von Hand zuordnen" ist ohne diese Meldung ein Versprechen, das
    niemand einlösen kann.
    """
    unresolved = [
        row["symbol"]
        for row in connection.execute(
            "SELECT symbol FROM instruments WHERE identity_status = ? ORDER BY symbol",
            (_IDENTITY_UNRESOLVED,),
        )
    ]
    if unresolved:
        logger.info(
            "identity_unresolved", count=len(unresolved), symbols=unresolved
        )


def _merge_overrides(
    connection: sqlite3.Connection, keeper_id: int, duplicate_id: int
) -> None:
    """Zieht die von Hand gepflegten Kennzahlen eines Duplikats auf den Keeper.

    Zusammengeführt wird **feldweise**, nicht zeilenweise: Was am Keeper steht,
    bleibt stehen; wo er eine Lücke hat, füllt das Duplikat sie. So geht kein
    einziger Wert verloren, und bei einem echten Konflikt behält die Zeile mit
    der ISIN das letzte Wort — sie ist die kanonische.

    Args:
        connection: Offene Verbindung.
        keeper_id: Instrument, das bestehen bleibt.
        duplicate_id: Instrument, das gleich gelöscht wird.
    """
    duplicate = connection.execute(
        "SELECT * FROM instrument_overrides WHERE instrument_id = ?", (duplicate_id,)
    ).fetchone()
    if duplicate is None:
        return

    keeper = connection.execute(
        "SELECT * FROM instrument_overrides WHERE instrument_id = ?", (keeper_id,)
    ).fetchone()
    if keeper is None:
        connection.execute(
            "UPDATE instrument_overrides SET instrument_id = ? WHERE instrument_id = ?",
            (keeper_id, duplicate_id),
        )
        return

    merged = [
        keeper[field] if keeper[field] is not None else duplicate[field]
        for field in OVERRIDE_FIELDS
    ]
    assignments = ", ".join(f"{field} = ?" for field in OVERRIDE_FIELDS)
    connection.execute(
        f"UPDATE instrument_overrides SET {assignments}, updated_at = ? "
        "WHERE instrument_id = ?",
        [*merged, max(keeper["updated_at"], duplicate["updated_at"]), keeper_id],
    )
    connection.execute(
        "DELETE FROM instrument_overrides WHERE instrument_id = ?", (duplicate_id,)
    )


def _merge_daily_meta(
    connection: sqlite3.Connection, keeper_id: int, duplicate_id: int
) -> None:
    """Zieht das Daily-Wasserzeichen eines Duplikats auf den Keeper.

    Das Wasserzeichen sagt „diese Spanne ist geholt". Zwei Spannen werden
    deshalb **nur bei Überlappung** zu einer zusammengezogen: Läge dazwischen
    eine Lücke, behauptete der zusammengefasste Bereich, Tage seien geholt
    worden, die niemand geholt hat — und der nächste Abgleich überspränge sie
    für immer. Ohne Überlappung bleibt die Spanne des Keepers stehen; im
    schlimmsten Fall wird einmal zu viel geholt, und das ist folgenlos.

    Args:
        connection: Offene Verbindung.
        keeper_id: Instrument, das bestehen bleibt.
        duplicate_id: Instrument, das gleich gelöscht wird.
    """
    duplicate = connection.execute(
        "SELECT * FROM daily_meta WHERE instrument_id = ?", (duplicate_id,)
    ).fetchone()
    if duplicate is None:
        return

    keeper = connection.execute(
        "SELECT * FROM daily_meta WHERE instrument_id = ?", (keeper_id,)
    ).fetchone()
    if keeper is None:
        connection.execute(
            "UPDATE daily_meta SET instrument_id = ? WHERE instrument_id = ?",
            (keeper_id, duplicate_id),
        )
        return

    if _ranges_overlap(keeper, duplicate):
        connection.execute(
            "UPDATE daily_meta SET fetched_from = ?, fetched_to = ? "
            "WHERE instrument_id = ?",
            (
                min(keeper["fetched_from"], duplicate["fetched_from"]),
                max(keeper["fetched_to"], duplicate["fetched_to"]),
                keeper_id,
            ),
        )
    connection.execute(
        "DELETE FROM daily_meta WHERE instrument_id = ?", (duplicate_id,)
    )


def _ranges_overlap(left: sqlite3.Row, right: sqlite3.Row) -> bool:
    """Überlappen sich zwei Daily-Spannen?

    ISO-Datumsstrings vergleichen sich lexikografisch richtig, ein Parsen ist
    also nicht nötig. Fehlt an einer Zeile eine Grenze, ist ihre Spanne nicht
    bestimmbar — dann wird nicht zusammengezogen.

    Args:
        left: Zeile aus `daily_meta`.
        right: Zeile aus `daily_meta`.

    Returns:
        ``True`` wenn sich beide Spannen berühren oder überschneiden.
    """
    bounds = (
        left["fetched_from"], left["fetched_to"],
        right["fetched_from"], right["fetched_to"],
    )
    if any(bound is None for bound in bounds):
        return False
    return max(bounds[0], bounds[2]) <= min(bounds[1], bounds[3])


def _add_missing_columns(
    connection: sqlite3.Connection, table: str, columns: tuple[tuple[str, str], ...]
) -> None:
    """Fügt fehlende Spalten hinzu; vorhandene bleiben unangetastet."""
    existing = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}
    for column, ddl in columns:
        if column not in existing:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def _dedupe_symbols(connection: sqlite3.Connection) -> None:
    """Führt **gleiche** Instrumente zusammen (Zeile mit ISIN gewinnt).

    Duplikate konnten vor dem UNIQUE-Index durch parallele Erst-Requests
    entstehen. Kurs-Historie und Tages-Schlusskurse werden auf das verbleibende
    Instrument umgehängt; Kollisionen (gleicher Zeitpunkt/Tag) verfallen mit
    dem gelöschten Duplikat.

    **Gleiches Symbol ist seit T-21 kein Identitätsnachweis.** Die
    Eindeutigkeit liegt auf `(ticker, mic)`, und sobald `US` in `XNYS` und
    `XNAS` zerfällt, tragen zwei verschiedene Listings dasselbe Symbol.

    Zusammengeführt wird deshalb **nur bei bewiesener Gleichheit**: dieselbe
    aufgelöste `(ticker, mic)`. Alles andere bleibt stehen — auch zwei
    unaufgelöste Zeilen mit demselben Symbol. Die wären früher zusammengefasst
    worden, „weil das der alte Fall aus parallelen Erst-Requests ist"; genau
    das ist aber die Vermutung, die diese Migration nicht anstellen darf. Zwei
    offene Zeilen mit demselben Symbol können zwei verschiedene Papiere sein,
    und ihre ISINs sagen es oft sogar.

    Nötig ist das Zusammenführen ohnehin nicht mehr: Es gab die Funktion, weil
    der `UNIQUE`-Index auf `symbol` sonst nicht anzulegen war. Diesen Index
    gibt es nicht mehr.

    **Alles Abhängige muss mitwandern.** Umgehängt wurden lange nur `quotes`
    und `daily_closes` — `daily_meta` und `instrument_overrides` blieben am
    Duplikat und verschwanden mit ihm durch `ON DELETE CASCADE`. Damit gingen
    ausgerechnet die Daten verloren, die niemand wiederbeschaffen kann: von
    Hand gepflegte Kennzahlen. Die beiden Tabellen tragen je eine eigene
    Merge-Regel, siehe `_merge_overrides` und `_merge_daily_meta`.
    """
    # Gruppiert wird ausschließlich über die aufgelöste Identität. Zeilen ohne
    # sie fallen durch das `WHERE` und bleiben unangetastet.
    identity = "ticker || '|' || mic"
    duplicated = connection.execute(
        f"SELECT {identity} AS identity FROM instruments "
        "WHERE ticker IS NOT NULL AND mic IS NOT NULL "
        f"GROUP BY {identity} HAVING COUNT(*) > 1"
    ).fetchall()
    for row in duplicated:
        identity_value = row["identity"]
        keeper = connection.execute(
            f"SELECT id, symbol FROM instruments WHERE {identity} = ? "
            "ORDER BY (isin IS NULL), id LIMIT 1",
            (identity_value,),
        ).fetchone()
        symbol = keeper["symbol"]
        duplicates = connection.execute(
            f"SELECT id FROM instruments WHERE {identity} = ? AND id != ?",
            (identity_value, keeper["id"]),
        ).fetchall()
        for duplicate in duplicates:
            for table in ("quotes", "daily_closes"):
                connection.execute(
                    f"UPDATE OR IGNORE {table} SET instrument_id = ? "
                    "WHERE instrument_id = ?",
                    (keeper["id"], duplicate["id"]),
                )
            _merge_overrides(connection, keeper["id"], duplicate["id"])
            _merge_daily_meta(connection, keeper["id"], duplicate["id"])
            connection.execute(
                "DELETE FROM instruments WHERE id = ?", (duplicate["id"],)
            )
        logger.warning(
            "duplicate_symbol_merged", symbol=symbol, kept_id=keeper["id"]
        )

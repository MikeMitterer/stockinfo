"""SQLite-Anbindung und Schema-Initialisierung.

Kapselt Verbindungsaufbau und Schema. Raw-SQL für Fachlogik gehört in die
Repository-Schicht (repository.py), nicht hierher.
"""

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import structlog

from app.models import OVERRIDE_FIELDS
from app.migration import (
    IDENTITY_CHECK,
    MigrationPlan,
    apply_migration,
    harden_identity_schema,
    plan_migration,
)

logger = structlog.get_logger()

# Schema — instruments (langsam veränderliche Metadaten) + quotes (Zeitreihe).
_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS instruments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    isin            TEXT UNIQUE,
    symbol          TEXT NOT NULL,
    -- Die kanonische Identität ist **Pflicht** (T-21 Teil 3, `#2b2`) — seit
    -- T-31 aber je **Form** verschieden, weil nicht jedes Papier an einer
    -- Börse gehandelt wird: Eine Coin hat keinen MIC, eine OTC-Anleihe keinen
    -- Ticker. Was „vollständig" heißt, sagt darum der `CHECK` am Tabellenende;
    -- er verlangt je `kind` die Felder dieser Form **und schließt die der
    -- beiden anderen aus**. Halbe wie doppelte Identitäten bleiben unmöglich.
    --
    -- `NOT NULL` an den Spalten wäre dafür das falsche Werkzeug: Es gälte für
    -- alle Formen zugleich und verböte gerade die, für die dieses Ticket da
    -- ist.
    kind            TEXT NOT NULL DEFAULT 'listed',
    ticker          TEXT,
    mic             TEXT,
    base            TEXT,
    quote_currency  TEXT,
    -- Opake UUID, bei Anlage einmal erzeugt und nicht aus ticker, mic, ISIN
    -- oder dem lokalen Schlüssel abgeleitet (Vertrag in T-24).
    listing_id      TEXT,
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
    meta_fetched_at TEXT,
    {IDENTITY_CHECK}
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
    -- Wer den Kurs geliefert hat. Ohne diese Spalte war die Herkunft nach dem
    -- ersten Cache-Treffer verloren, und `_from_cache` setzte ersatzweise
    -- `"cache"` ein — eine Angabe, die `cached: true` schon macht, und die
    -- den eigentlichen Lieferanten verschwieg (Codex, T-36 Runde 3).
    source     TEXT,
    PRIMARY KEY (base, quote)
);

-- Was die Datenbank über sich selbst weiß — damit eine Sicherung ohne
-- Manifest zuordenbar bleibt. Was hier steht, beschreibt die Datei, nicht
-- ihren Inhalt.
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

SCHEMA_VERSION = 2
"""Die Form dieses Schemas — als **Zahl**, die nur wächst.

`schema_outdated()` prüft die Form *strukturell* und beantwortet „ist hier
etwas nachzuholen?". Die Gegenrichtung — **„ist diese Datei neuer als ich?"** —
kann es nicht beantworten. Genau die entscheidet, ob eine Sicherung überhaupt
lesbar ist, und sie duldet später kein `force`: Eine höhere Nummer heißt, dass
die App die Datei nicht lesen *kann*.

`VACUUM INTO` trägt den Wert in die Kopie mit; jede Sicherung erklärt ihr
Schema damit selbst und ist nicht auf ihr Manifest angewiesen.
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


def init_db(database_path: str) -> bool:
    """Erstellt das Schema und sagt, ob ein Identitäts-Umzug **aussteht**.

    **Der Bestand wird hier nicht angefasst.** Bis T-21 Teil 3 zerlegte diese
    Funktion die Altzeilen gleich mit — im FastAPI-Lifespan, also bevor die App
    den ersten Request bedient. Seit die Migration Zeilen auch **ablehnt**,
    geht das nicht mehr: Ein UI, das erst nach dem Lifespan erreichbar wird,
    könnte niemanden mehr warnen, und der Benutzer stünde vor einem Bestand,
    aus dem etwas fehlt.

    Ergänzt werden deshalb nur Dinge, die nichts verwerfen: das Grundschema
    und nachgetragene Metadatenspalten. Ob etwas aussteht, entscheidet die
    Vorschau — und die schreibt nicht.

    **Verlustlos wird ohne Rückfrage erledigt.** Fehlen nur Spalten oder
    Zuordnungen und geht dabei nichts verloren, läuft der Umzug hier durch: Es
    gibt nichts zu warnen, und eine Bestätigung für nichts wäre bloß eine
    Hürde. Die Zustimmung schützt vor **Datenverlust**, nicht vor Schemaarbeit.

    Args:
        database_path: Pfad zur SQLite-Datei.

    Returns:
        ``True``, wenn ein Umzug aussteht, **bei dem etwas verloren geht** —
        dann gehört der Dienst in den Pending-Zustand.
    """
    connection = get_connection(database_path)
    try:
        connection.executescript(_SCHEMA)
        _migrate(connection)
        from app.detail_store import initialize

        initialize(connection)
        _create_identity_indices(connection)
        # Erst wenn das Schema wirklich steht: Die Nummer ist eine Zusage an
        # eine spätere Wiederherstellung.
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.commit()
        plan = plan_migration(connection)
    finally:
        connection.close()

    if plan.needs_confirmation:
        return True

    if plan.needs_migration:
        # Verlustlos: Spalten, Zuordnungen, Härtung — nichts davon kostet den
        # Benutzer etwas, also fragt hier auch niemand.
        logger.info(
            "migration_lossless",
            migrated=len(plan.migrated),
            schema_outdated=plan.schema_outdated,
        )
        run_migration(database_path, rejected_at=_now())
    return False


def _now() -> str:
    """Der aktuelle Zeitpunkt als ISO-8601-String."""
    return datetime.now(timezone.utc).isoformat()


def run_migration(database_path: str, rejected_at: str) -> MigrationPlan:
    """Führt den bestätigten Umzug aus — Phase 2, **alles oder nichts**.

    Aufgerufen erst nach der ausdrücklichen Bestätigung des Benutzers, nie im
    Lifespan.

    `PRAGMA foreign_keys` steht **vor** der Transaktion: SQLite ignoriert das
    PRAGMA innerhalb einer, und der Tabellen-Neuaufbau in
    `harden_identity_schema` kopiert `instruments` um — mit eingeschalteten
    Fremdschlüsseln nähme er die Kurszeilen mit.

    Args:
        database_path: Pfad zur SQLite-Datei.
        rejected_at: Zeitstempel für die Berichtseinträge (ISO-8601).

    Returns:
        Die Bilanz des Laufs — dieselbe, die die Vorschau gezeigt hat.
    """
    connection = get_connection(database_path)
    try:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("BEGIN")
        plan = apply_migration(connection, rejected_at)
        _assign_listing_ids(connection)
        _dedupe_symbols(connection)
        harden_identity_schema(connection)
        for statement in _IDENTITY_INDICES:
            connection.execute(statement)
        connection.commit()
        return plan
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.close()


# Die Indizes der kanonischen Identität — als **einzelne** Anweisungen.
#
# Sie stehen **nicht** im Grundschema, und das ist kein Versehen: Auf einer
# Alt-Datenbank lässt `CREATE TABLE IF NOT EXISTS` die alte Tabelle stehen,
# und ein `CREATE INDEX ... (ticker, mic)` bräche dann mit „no such column".
# Der Start einer noch nicht umgezogenen Installation wäre damit unmöglich —
# das genaue Gegenteil von „erkennen statt ausführen".
#
# Nach dem Tabellen-Neuaufbau müssen sie ohnehin neu entstehen: Ein `DROP
# TABLE` nimmt sie mit, und `PRAGMA table_info` kennt `UNIQUE` gar nicht.
#
# **Warum kein Script.** Hier stand ein `executescript`, und das setzt vor dem
# Ausführen ein `COMMIT` ab. Innerhalb von `run_migration` beendete es damit
# die offene Transaktion: Ein Fehler beim letzten Index ließ Identitäten,
# Berichtstabelle und gehärtetes Schema dauerhaft zurück, obwohl die Funktion
# „alles oder nichts" zusagt.
#
# Derselbe Fehler war in `app/migration.py` bereits gefunden, behoben und im
# Kommentar festgehalten — und hier zwei Stunden später wieder eingebaut
# (Codex, Runde 30). Eine Liste statt eines Scripts macht ihn unmöglich.
#
# **Je Form ein partieller Index — und zwei globale daneben** (T-31). Der
# `(ticker, mic)`-Index liefe für zwei der drei Formen leer, weil beide Spalten
# dort `NULL` sind und SQLite `NULL` nie als gleich ansieht. Je Form einer
# schließt die Lücke.
#
# Die beiden globalen Zusagen bleiben trotzdem stehen, und das ist kein
# Versehen:
#
# * `isin` ist über **alle** Formen eindeutig. Ein partieller Index nur für
#   `isin_only` ließe dieselbe ISIN einmal als `listed` und einmal als
#   `isin_only` zu — zwei Zeilen für dasselbe Papier, in zwei Identitätsformen.
# * `listing_id` ist die opake Kennung der Zeile und von `kind` unabhängig.
_IDENTITY_INDICES = (
    "DROP INDEX IF EXISTS idx_instruments_symbol",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_instruments_ticker_mic "
    "ON instruments (ticker, mic) WHERE kind = 'listed'",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_instruments_pair "
    "ON instruments (base, quote_currency) WHERE kind = 'pair'",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_instruments_listing_id "
    "ON instruments (listing_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_instruments_isin "
    "ON instruments (isin)",
)


def _create_identity_indices(connection: sqlite3.Connection) -> None:
    """Legt die Identitätsindizes an — **nur**, wenn die Spalten da sind.

    Auf einer frischen Installation trägt `instruments` sie vom ersten Moment
    an; auf einer Alt-Datenbank kommen sie erst mit dem bestätigten Umzug, und
    bis dahin gibt es nichts zu indizieren.

    Args:
        connection: Offene Verbindung.
    """
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(instruments)")
    }
    if {"kind", "ticker", "mic", "base", "quote_currency", "listing_id"} <= columns:
        for statement in _IDENTITY_INDICES:
            connection.execute(statement)


def _assign_listing_ids(connection: sqlite3.Connection) -> None:
    """Vergibt jeder Zeile ihre `listing_id`, die noch keine hat.

    Args:
        connection: Offene Verbindung innerhalb der Transaktion.
    """
    for row in connection.execute(
        "SELECT id FROM instruments WHERE listing_id IS NULL"
    ).fetchall():
        connection.execute(
            "UPDATE instruments SET listing_id = ? WHERE id = ?",
            (str(uuid.uuid4()), row["id"]),
        )


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
            # Die Identitaetsform und ihre Felder (T-31). Der `CHECK` steht nur
            # im frischen Schema — eine Alt-Datenbank bekaeme ihn erst beim
            # Tabellen-Neuaufbau, und den gibt es hier nicht: Mikes Entscheidung
            # vom 2026-08-29 verwirft die Entwicklungsdatenbank, statt sie
            # umzuziehen. Die Spalten kommen trotzdem mit, damit eine solche
            # Datenbank lesbar bleibt statt beim ersten SELECT zu brechen.
            ("kind", "TEXT NOT NULL DEFAULT 'listed'"),
            ("base", "TEXT"),
            ("quote_currency", "TEXT"),
        ),
    )
    # Die Herkunft eines Wechselkurses. Bestehende Datenbanken haben die
    # Spalte nicht; ohne Nachzug bliebe die Angabe dort für immer leer.
    _add_missing_columns(connection, "fx_rates", (("source", "TEXT"),))
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
            for table, columns in (
                ('detail_values', 'field,source,value,currency,as_of'),
                ('detail_overrides', 'field,value,currency,as_of'),
            ):
                connection.execute(
                    f'INSERT OR IGNORE INTO {table}(instrument_id,{columns}) '
                    f'SELECT ?,{columns} FROM {table} WHERE instrument_id=?',
                    (keeper['id'], duplicate['id']),
                )
                connection.execute(f'DELETE FROM {table} WHERE instrument_id=?', (duplicate['id'],))
            _merge_overrides(connection, keeper["id"], duplicate["id"])
            _merge_daily_meta(connection, keeper["id"], duplicate["id"])
            connection.execute(
                "DELETE FROM instruments WHERE id = ?", (duplicate["id"],)
            )
        logger.warning(
            "duplicate_symbol_merged", symbol=symbol, kept_id=keeper["id"]
        )

"""Phase 2 des Identitäts-Umzugs — was tatsächlich geschieht (T-21 2A).

Das Gegenstück zu `test_migration_plan.py`: Dort wird vorgerechnet, hier wird
ausgeführt. Zwei Zusagen tragen den ganzen Schritt, und beide werden hier
geprüft statt behauptet:

* **`#2b4`** — Bericht und Ablehnung entstehen in *derselben* Transaktion, ein
  zweiter Lauf dupliziert sie nicht, und der Eintrag bleibt abrufbar, nachdem
  die aktive Zeile weg ist.
* **`#2b2`** — danach trägt keine Zeile mehr eine halbe Identität, und das
  steht im **Schema**, nicht in einer Prüfung, die man vergessen kann.
"""

import sqlite3

import pytest

from app.db import run_migration
from app.migration import (
    REASON_NO_SUFFIX,
    REASON_NON_CANONICAL_TICKER,
    apply_migration,
    harden_identity_schema,
    plan_migration,
)

_STAMP = "2026-08-25T12:00:00+00:00"


def _legacy_database(path: str, rows: list[tuple[str, str | None]]) -> None:
    """Legt eine Datenbank im Stand **vor** T-21 an und füllt sie.

    Args:
        path: Dateipfad der SQLite-Datenbank.
        rows: Paare aus Symbol und ISIN (``None`` erlaubt).
    """
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE instruments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isin TEXT UNIQUE, symbol TEXT NOT NULL,
                exchange TEXT, name TEXT, type TEXT, currency TEXT,
                first_seen TEXT NOT NULL
            );
            CREATE TABLE quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instrument_id INTEGER NOT NULL REFERENCES instruments(id),
                price REAL NOT NULL, quote_time TEXT NOT NULL,
                fetched_at TEXT NOT NULL, UNIQUE (instrument_id, quote_time)
            );
            CREATE TABLE daily_closes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instrument_id INTEGER NOT NULL REFERENCES instruments(id),
                date TEXT NOT NULL, close REAL NOT NULL,
                UNIQUE (instrument_id, date)
            );
            """
        )
        connection.executemany(
            "INSERT INTO instruments (symbol, isin, name, first_seen) "
            "VALUES (?, ?, ?, ?)",
            [(symbol, isin, f"Papier {symbol}", "2026-01-01T00:00:00+00:00")
             for symbol, isin in rows],
        )


def _add_prices(path: str, symbol: str, quotes: int, daily: int) -> None:
    """Hängt einem Papier Kurspunkte an, damit der Verlust zählbar wird."""
    with sqlite3.connect(path) as connection:
        instrument_id = connection.execute(
            "SELECT id FROM instruments WHERE symbol = ?", (symbol,)
        ).fetchone()[0]
        connection.executemany(
            "INSERT INTO quotes (instrument_id, price, quote_time, fetched_at) "
            "VALUES (?, ?, ?, ?)",
            [(instrument_id, 1.0, f"2026-01-{day + 1:02d}T10:00:00+00:00", "x")
             for day in range(quotes)],
        )
        connection.executemany(
            "INSERT INTO daily_closes (instrument_id, date, close) VALUES (?, ?, ?)",
            [(instrument_id, f"2026-02-{day + 1:02d}", 1.0) for day in range(daily)],
        )


def _connect(path: str) -> sqlite3.Connection:
    """Öffnet die Testdatenbank so, wie der Umzug sie braucht.

    `PRAGMA foreign_keys = OFF` gehört dazu: Der Tabellen-Neuaufbau kopiert
    `instruments` um, und SQLite ignoriert das PRAGMA innerhalb einer
    Transaktion — es muss also vorher stehen.
    """
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = OFF")
    return connection


def _migrate(path: str) -> None:
    """Führt einen vollständigen Umzug aus — anwenden und Schema härten."""
    connection = _connect(path)
    try:
        connection.execute("BEGIN")
        apply_migration(connection, rejected_at=_STAMP)
        harden_identity_schema(connection)
        connection.commit()
    finally:
        connection.close()


@pytest.fixture
def bestand(tmp_path) -> str:
    """Vier bezeichnende Fälle: zwei migrieren, zwei gehen.

    `GOLD.SG` trägt hier dieselben **257** Tagesschlusskurse wie im echten
    Bestand — es ist der Fall, an dem die Reihenfolge „Katalog vor Migration"
    hängt.
    """
    path = str(tmp_path / "alt.db")
    _legacy_database(
        path,
        [
            ("EUNL.DE", "IE00B4L5Y983"),
            ("GOLD.SG", "DE000A0S9GB0"),
            ("VTI", "US9229087690"),
            ("BRK-B.DE", None),
        ],
    )
    _add_prices(path, "GOLD.SG", quotes=2, daily=257)
    _add_prices(path, "VTI", quotes=1, daily=0)
    _add_prices(path, "BRK-B.DE", quotes=4, daily=9)
    return path


def test_was_geht_hinterlaesst_seinen_bericht(bestand) -> None:
    """`#2b4`: Der Eintrag bleibt, **nachdem** die aktive Zeile weg ist.

    Das ist der ganze Zweck des Speichers. Verschwände er mit der Zeile,
    fehlte genau die Information, die den Verlust erklären soll — und der
    Benutzer stünde vor einem Bestand, aus dem etwas fehlt, ohne zu erfahren,
    was und warum.
    """
    _migrate(bestand)

    with _connect(bestand) as connection:
        aktiv = [row["symbol"] for row in connection.execute(
            "SELECT symbol FROM instruments ORDER BY symbol")]
        bericht = [
            (row["symbol"], row["reason"], row["quotes"], row["daily_closes"])
            for row in connection.execute(
                "SELECT symbol, reason, quotes, daily_closes "
                "FROM migration_rejections ORDER BY symbol")
        ]

    assert aktiv == ["EUNL.DE", "GOLD.SG"]
    assert bericht == [
        ("BRK-B.DE", REASON_NON_CANONICAL_TICKER, 4, 9),
        ("VTI", REASON_NO_SUFFIX, 1, 0),
    ]


def test_der_bericht_nennt_genug_zur_neuerfassung(bestand) -> None:
    """Ein Bericht, der nur ein Symbol nennt, hilft beim Neuanlegen nicht.

    Die Aufforderung lautet „erfasse das Papier neu" — dafür braucht der
    Benutzer wenigstens ISIN und Namen, und beide sind nach dem Löschen der
    Zeile nirgends sonst mehr zu holen.
    """
    _migrate(bestand)

    with _connect(bestand) as connection:
        row = connection.execute(
            "SELECT * FROM migration_rejections WHERE symbol = 'VTI'"
        ).fetchone()

    assert (row["isin"], row["name"]) == ("US9229087690", "Papier VTI")
    assert row["rejected_at"] == _STAMP


def test_ein_zweiter_lauf_dupliziert_den_bericht_nicht(bestand) -> None:
    """`#2b4`: Idempotenz — und zwar **verhaltensmäßig**, nicht per UNIQUE.

    Eine Eindeutigkeitsbedingung auf `symbol` hätte denselben Test bestanden,
    ohne dass der Lauf idempotent wäre: Sie hätte die zweite Einfügung nur
    verboten. Geprüft wird deshalb der Lauf selbst — er findet beim zweiten
    Mal schlicht nichts mehr abzulehnen.
    """
    _migrate(bestand)
    _migrate(bestand)

    with _connect(bestand) as connection:
        anzahl = connection.execute(
            "SELECT COUNT(*) FROM migration_rejections"
        ).fetchone()[0]
        plan = plan_migration(connection)

    assert anzahl == 2
    assert plan.needs_migration is False


def test_ein_abbruch_laesst_alles_stehen(bestand) -> None:
    """Bericht **und** Ablehnung in derselben Transaktion — oder keines von beidem.

    Ohne diese Kopplung könnte ein Abbruch dazwischen eine Zeile entfernen,
    deren Verschwinden danach niemand mehr erklären kann.
    """
    connection = _connect(bestand)
    try:
        connection.execute("BEGIN")
        apply_migration(connection, rejected_at=_STAMP)
        connection.rollback()
    finally:
        connection.close()

    with _connect(bestand) as connection:
        aktiv = [row["symbol"] for row in connection.execute(
            "SELECT symbol FROM instruments ORDER BY symbol")]
        tabellen = {row["name"] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}

    assert aktiv == ["BRK-B.DE", "EUNL.DE", "GOLD.SG", "VTI"]
    assert "migration_rejections" not in tabellen


def test_die_kurspunkte_der_bleibenden_ueberleben(bestand) -> None:
    """Der gemessene Fall: `GOLD.SG` behält seine 257 Tagesschlusskurse.

    Und die abgelehnten Zeilen hinterlassen keine Waisen — gelöscht wird
    ausdrücklich, nicht über eine Kaskade, die beim Tabellen-Neuaufbau
    abgeschaltet ist.
    """
    _migrate(bestand)

    with _connect(bestand) as connection:
        gold = connection.execute(
            "SELECT COUNT(*) FROM daily_closes d JOIN instruments i "
            "ON i.id = d.instrument_id WHERE i.symbol = 'GOLD.SG'"
        ).fetchone()[0]
        waisen = connection.execute(
            "SELECT COUNT(*) FROM quotes q LEFT JOIN instruments i "
            "ON i.id = q.instrument_id WHERE i.id IS NULL"
        ).fetchone()[0]

    assert gold == 257
    assert waisen == 0


def test_nach_dem_umzug_ist_die_halbe_identitaet_unmoeglich(bestand) -> None:
    """`#2b2`: Die Invariante steht im Schema, nicht in einer Prüfung.

    Eine Zählung `COUNT(*) WHERE ticker IS NULL` sagt nur, dass gerade keine
    solche Zeile *da* ist. `NOT NULL` sagt, dass keine mehr **entstehen kann**
    — auch nicht durch einen Endpunkt, den jemand übersehen hat.
    """
    _migrate(bestand)

    with _connect(bestand) as connection:
        offen = connection.execute(
            "SELECT COUNT(*) FROM instruments WHERE ticker IS NULL OR mic IS NULL"
        ).fetchone()[0]
        spalten = {row["name"] for row in connection.execute(
            "PRAGMA table_info(instruments)")}

        assert offen == 0
        assert "identity_status" not in spalten

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO instruments (symbol, first_seen) VALUES ('X.DE', 'jetzt')"
            )


def _symbols(path: str) -> list[str]:
    """Die Symbole des aktiven Bestands, sortiert."""
    with _connect(path) as connection:
        return sorted(
            row["symbol"]
            for row in connection.execute("SELECT symbol FROM instruments")
        )


def _columns(path: str) -> set[tuple[str, int]]:
    """Spaltennamen samt `NOT NULL`-Flag — das Schema in vergleichbarer Form."""
    with _connect(path) as connection:
        return {
            (row["name"], row["notnull"])
            for row in connection.execute("PRAGMA table_info(instruments)")
        }


def test_ein_spaeter_fehler_rollt_den_ganzen_umzug_zurueck(
    bestand, monkeypatch
) -> None:
    """`run_migration` als **ganzer** Weg — nicht nur `apply_migration`.

    Der bisherige Rollback-Test rief nur den Anwendungsteil. Genau dazwischen
    stand der Fehler: `run_migration` setzte die Indizes mit `executescript`,
    und das committet vorher implizit. Ein Fehler beim **letzten** Index ließ
    migrierte Identitäten, Berichtstabelle und gehärtetes Schema dauerhaft
    zurück — obwohl die Funktion „alles oder nichts" zusagt (Codex, Runde 30).

    Ausgelöst wird der Fehler deshalb an der spätesten Stelle, die es gibt.
    """
    from app import db as db_modul

    vorher_symbols = _symbols(bestand)
    vorher_spalten = _columns(bestand)

    monkeypatch.setattr(
        db_modul,
        "_IDENTITY_INDICES",
        (
            *db_modul._IDENTITY_INDICES,
            "CREATE UNIQUE INDEX kaputt ON instruments (gibt_es_nicht)",
        ),
    )

    with pytest.raises(sqlite3.Error):
        run_migration(bestand, rejected_at=_STAMP)

    assert _symbols(bestand) == vorher_symbols, "Zeilen sind verschwunden"
    assert _columns(bestand) == vorher_spalten, "das Schema wurde gehärtet"

    with _connect(bestand) as connection:
        tabellen = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert "migration_rejections" not in tabellen, "der Bericht blieb stehen"


def test_eine_gesetzte_zuordnung_ueberlebt_den_umzug(tmp_path) -> None:
    """Handarbeit wird nicht zurückgenommen.

    `AAPL` lässt sich nicht zerlegen — die Zeile trägt ihre Identität aber
    bereits. Würde die Migration sie neu bewerten, flöge ausgerechnet das
    Papier hinaus, das jemand vorher richtig zugeordnet hat.
    """
    path = str(tmp_path / "handarbeit.db")
    _legacy_database(path, [("AAPL", "US0378331005")])
    with sqlite3.connect(path) as connection:
        connection.execute("ALTER TABLE instruments ADD COLUMN ticker TEXT")
        connection.execute("ALTER TABLE instruments ADD COLUMN mic TEXT")
        connection.execute("UPDATE instruments SET ticker = 'AAPL', mic = 'XNAS'")

    _migrate(path)

    with _connect(path) as connection:
        rows = [(row["symbol"], row["ticker"], row["mic"]) for row in
                connection.execute("SELECT symbol, ticker, mic FROM instruments")]
        abgelehnt = connection.execute(
            "SELECT COUNT(*) FROM migration_rejections"
        ).fetchone()[0]

    assert rows == [("AAPL", "AAPL", "XNAS")]
    assert abgelehnt == 0

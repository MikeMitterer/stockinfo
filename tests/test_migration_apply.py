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

from app.persistence.db import run_migration
from app.persistence.migration import (
    REASON_NO_SUFFIX,
    REASON_NON_CANONICAL_TICKER,
    apply_migration,
    harden_identity_schema,
    plan_migration,
)
from tests.legacy_schema import add_prices, create_legacy_tables

_STAMP = "2026-08-25T12:00:00+00:00"


def _legacy_database(path: str, rows: list[tuple[str, str | None]]) -> None:
    """Legt eine Datenbank im Stand **vor** T-21 an und füllt sie.

    Args:
        path: Dateipfad der SQLite-Datenbank.
        rows: Paare aus Symbol und ISIN (``None`` erlaubt).
    """
    with sqlite3.connect(path) as connection:
        create_legacy_tables(connection)
        connection.executemany(
            "INSERT INTO instruments (symbol, isin, name, first_seen) "
            "VALUES (?, ?, ?, ?)",
            [(symbol, isin, f"Papier {symbol}", "2026-01-01T00:00:00+00:00")
             for symbol, isin in rows],
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
def populated_db(tmp_path) -> str:
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
    add_prices(path, "GOLD.SG", quotes=2, daily=257)
    add_prices(path, "VTI", quotes=1, daily=0)
    add_prices(path, "BRK-B.DE", quotes=4, daily=9)
    return path


def test_was_geht_hinterlaesst_seinen_bericht(populated_db) -> None:
    """`#2b4`: Der Eintrag bleibt, **nachdem** die aktive Zeile weg ist.

    Das ist der ganze Zweck des Speichers. Verschwände er mit der Zeile,
    fehlte genau die Information, die den Verlust erklären soll — und der
    Benutzer stünde vor einem Bestand, aus dem etwas fehlt, ohne zu erfahren,
    was und warum.
    """
    _migrate(populated_db)

    with _connect(populated_db) as connection:
        active = [row["symbol"] for row in connection.execute(
            "SELECT symbol FROM instruments ORDER BY symbol")]
        report = [
            (row["symbol"], row["reason"], row["quotes"], row["daily_closes"])
            for row in connection.execute(
                "SELECT symbol, reason, quotes, daily_closes "
                "FROM migration_rejections ORDER BY symbol")
        ]

    assert active == ["EUNL.DE", "GOLD.SG"]
    assert report == [
        ("BRK-B.DE", REASON_NON_CANONICAL_TICKER, 4, 9),
        ("VTI", REASON_NO_SUFFIX, 1, 0),
    ]


def test_der_bericht_nennt_genug_zur_neuerfassung(populated_db) -> None:
    """Ein Bericht, der nur ein Symbol nennt, hilft beim Neuanlegen nicht.

    Die Aufforderung lautet „erfasse das Papier neu" — dafür braucht der
    Benutzer wenigstens ISIN und Namen, und beide sind nach dem Löschen der
    Zeile nirgends sonst mehr zu holen.
    """
    _migrate(populated_db)

    with _connect(populated_db) as connection:
        row = connection.execute(
            "SELECT * FROM migration_rejections WHERE symbol = 'VTI'"
        ).fetchone()

    assert (row["isin"], row["name"]) == ("US9229087690", "Papier VTI")
    assert row["rejected_at"] == _STAMP


def test_ein_zweiter_lauf_dupliziert_den_bericht_nicht(populated_db) -> None:
    """`#2b4`: Idempotenz — und zwar **verhaltensmäßig**, nicht per UNIQUE.

    Eine Eindeutigkeitsbedingung auf `symbol` hätte denselben Test bestanden,
    ohne dass der Lauf idempotent wäre: Sie hätte die zweite Einfügung nur
    verboten. Geprüft wird deshalb der Lauf selbst — er findet beim zweiten
    Mal schlicht nichts mehr abzulehnen.
    """
    _migrate(populated_db)
    _migrate(populated_db)

    with _connect(populated_db) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM migration_rejections"
        ).fetchone()[0]
        plan = plan_migration(connection)

    assert count == 2
    assert plan.needs_migration is False


def test_ein_abbruch_laesst_alles_stehen(populated_db) -> None:
    """Bericht **und** Ablehnung in derselben Transaktion — oder keines von beidem.

    Ohne diese Kopplung könnte ein Abbruch dazwischen eine Zeile entfernen,
    deren Verschwinden danach niemand mehr erklären kann.
    """
    connection = _connect(populated_db)
    try:
        connection.execute("BEGIN")
        apply_migration(connection, rejected_at=_STAMP)
        connection.rollback()
    finally:
        connection.close()

    with _connect(populated_db) as connection:
        active = [row["symbol"] for row in connection.execute(
            "SELECT symbol FROM instruments ORDER BY symbol")]
        tables = {row["name"] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}

    assert active == ["BRK-B.DE", "EUNL.DE", "GOLD.SG", "VTI"]
    assert "migration_rejections" not in tables


def test_die_kurspunkte_der_bleibenden_ueberleben(populated_db) -> None:
    """Der gemessene Fall: `GOLD.SG` behält seine 257 Tagesschlusskurse.

    Und die abgelehnten Zeilen hinterlassen keine Waisen — gelöscht wird
    ausdrücklich, nicht über eine Kaskade, die beim Tabellen-Neuaufbau
    abgeschaltet ist.
    """
    _migrate(populated_db)

    with _connect(populated_db) as connection:
        gold = connection.execute(
            "SELECT COUNT(*) FROM daily_closes d JOIN instruments i "
            "ON i.id = d.instrument_id WHERE i.symbol = 'GOLD.SG'"
        ).fetchone()[0]
        orphans = connection.execute(
            "SELECT COUNT(*) FROM quotes q LEFT JOIN instruments i "
            "ON i.id = q.instrument_id WHERE i.id IS NULL"
        ).fetchone()[0]

    assert gold == 257
    assert orphans == 0


def test_nach_dem_umzug_ist_die_halbe_identitaet_unmoeglich(populated_db) -> None:
    """`#2b2`: Die Invariante steht im Schema, nicht in einer Prüfung.

    Eine Zählung `COUNT(*) WHERE ticker IS NULL` sagt nur, dass gerade keine
    solche Zeile *da* ist. `NOT NULL` sagt, dass keine mehr **entstehen kann**
    — auch nicht durch einen Endpunkt, den jemand übersehen hat.
    """
    _migrate(populated_db)

    with _connect(populated_db) as connection:
        open_rows = connection.execute(
            "SELECT COUNT(*) FROM instruments WHERE ticker IS NULL OR mic IS NULL"
        ).fetchone()[0]
        columns = {row["name"] for row in connection.execute(
            "PRAGMA table_info(instruments)")}

        assert open_rows == 0
        assert "identity_status" not in columns

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
    populated_db, monkeypatch
) -> None:
    """`run_migration` als **ganzer** Weg — nicht nur `apply_migration`.

    Der bisherige Rollback-Test rief nur den Anwendungsteil. Genau dazwischen
    stand der Fehler: `run_migration` setzte die Indizes mit `executescript`,
    und das committet vorher implizit. Ein Fehler beim **letzten** Index ließ
    migrierte Identitäten, Berichtstabelle und gehärtetes Schema dauerhaft
    zurück — obwohl die Funktion „alles oder nichts" zusagt (Codex, Runde 30).

    Ausgelöst wird der Fehler deshalb an der spätesten Stelle, die es gibt.
    """
    from app.persistence import db as db_module

    symbols_before = _symbols(populated_db)
    columns_before = _columns(populated_db)

    monkeypatch.setattr(
        db_module,
        "_IDENTITY_INDICES",
        (
            *db_module._IDENTITY_INDICES,
            "CREATE UNIQUE INDEX fails ON instruments (missing_column)",
        ),
    )

    with pytest.raises(sqlite3.Error):
        run_migration(populated_db, rejected_at=_STAMP)

    assert _symbols(populated_db) == symbols_before, "Zeilen sind verschwunden"
    assert _columns(populated_db) == columns_before, "das Schema wurde gehärtet"

    with _connect(populated_db) as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert "migration_rejections" not in tables, "der Bericht blieb stehen"


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
        rejected_count = connection.execute(
            "SELECT COUNT(*) FROM migration_rejections"
        ).fetchone()[0]

    assert rows == [("AAPL", "AAPL", "XNAS")]
    assert rejected_count == 0

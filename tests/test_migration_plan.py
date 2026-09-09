"""Die Vorschau des Identitäts-Umzugs — was sie sagt, und dass sie nichts tut.

Phase 1 aus T-21 Teil 3, Übergabe 2A. `init_db()` läuft im FastAPI-Lifespan,
also bevor die App den ersten Request bedient; ein UI, das erst danach
erreichbar wird, kann niemanden mehr warnen. Deshalb muss die Vorschau ohne
jede Schreiboperation auskommen — und genau das prüft `#2b5` hier, nicht durch
Zusicherung, sondern an einer schreibgeschützten Verbindung.
"""

import sqlite3

import pytest

from app.db import init_db
from app.migration import (
    REASON_NO_SUFFIX,
    REASON_NON_CANONICAL_TICKER,
    REASON_UNKNOWN_SUFFIX,
    identity_of,
    keeps_its_identity,
    plan_migration,
    rejection_reason,
)
from tests.legacy_schema import create_legacy_tables


def _legacy_database(path: str, rows: list[tuple[str, str | None]]) -> None:
    """Legt eine Datenbank im Stand **vor** T-21 an — ohne Identitätsspalten.

    Bewusst das alte Schema und nicht `init_db()`: Der interessante Fall ist
    der Bestand, der den Umzug noch vor sich hat. Eine Datenbank, die schon
    durch `init_db()` gelaufen ist, hat die Spalten bereits.

    Args:
        path: Dateipfad der SQLite-Datenbank.
        rows: Paare aus Symbol und ISIN (``None`` erlaubt).
    """
    with sqlite3.connect(path) as connection:
        create_legacy_tables(connection)
        connection.executemany(
            "INSERT INTO instruments (symbol, isin, first_seen) VALUES (?, ?, ?)",
            [(symbol, isin, "2026-01-01T00:00:00+00:00") for symbol, isin in rows],
        )


def _add_prices(path: str, symbol: str, quotes: int, daily: int) -> None:
    """Hängt einem Papier Kurspunkte an, damit der Preis der Ablehnung zählbar wird."""
    with sqlite3.connect(path) as connection:
        instrument_id = connection.execute(
            "SELECT id FROM instruments WHERE symbol = ?", (symbol,)
        ).fetchone()[0]
        connection.executemany(
            "INSERT INTO quotes (instrument_id, price, quote_time, fetched_at) "
            "VALUES (?, ?, ?, ?)",
            [
                (instrument_id, 1.0, f"2026-01-{day + 1:02d}T10:00:00+00:00", "x")
                for day in range(quotes)
            ],
        )
        connection.executemany(
            "INSERT INTO daily_closes (instrument_id, date, close) VALUES (?, ?, ?)",
            [(instrument_id, f"2026-02-{day + 1:02d}", 1.0) for day in range(daily)],
        )


def _connect(path: str, read_only: bool = False) -> sqlite3.Connection:
    """Öffnet die Testdatenbank, auf Wunsch **schreibgeschützt**."""
    uri = f"file:{path}?mode=ro" if read_only else path
    connection = sqlite3.connect(uri, uri=read_only)
    connection.row_factory = sqlite3.Row
    return connection


@pytest.mark.parametrize(
    ("symbol", "expected"),
    [
        ("VTI", REASON_NO_SUFFIX),
        ("AAPL", REASON_NO_SUFFIX),
        ("", REASON_NO_SUFFIX),
        ("FOO.ZZ", REASON_UNKNOWN_SUFFIX),
        ("EUNL.XETR", REASON_UNKNOWN_SUFFIX),
        ("BRK-B.DE", REASON_NON_CANONICAL_TICKER),
        ("RDS-A.L", REASON_NON_CANONICAL_TICKER),
    ],
    ids=[
        "suffixlos",
        "suffixlos_us",
        "leer",
        "unbekanntes_suffix",
        "mic_als_suffix",
        "bindestrich_ticker",
        "yahoo_schreibweise",
    ],
)
def test_jede_ablehnung_nennt_ihren_grund(symbol: str, expected: str) -> None:
    """Drei Gründe, drei ausgeschriebene Erwartungen.

    `EUNL.XETR` ist der lehrreiche Fall: Der MIC als Suffix ist **kein**
    gültiges Altsymbol — die zweite Eingabeform kommt erst mit dem
    Aufnahmeweg, und im Bestand hat sie nie gestanden. Für die Migration ist
    `XETR` deshalb ein unbekanntes Suffix, nicht der Handelsplatz.
    """
    assert rejection_reason(symbol) == expected


@pytest.mark.parametrize(
    ("symbol", "expected"),
    [
        ("EUNL.DE", ("EUNL", "XETR")),
        ("GOLD.SG", ("GOLD", "XSTU")),
        ("VGWL.DE", ("VGWL", "XETR")),
    ],
    ids=["xetra", "stuttgart", "xetra_zweites"],
)
def test_was_migriert_bekommt_keinen_ablehnungsgrund(
    symbol: str, expected: tuple[str, str]
) -> None:
    """Grund und Identität sind **Gegenstücke** — genau eines von beiden.

    Ein Grund für `EUNL.DE` wäre ein Zustand, den es nicht gibt: eine Zeile,
    die migriert und zugleich abgelehnt ist. Der Typ soll ihn nicht ausdrücken
    können, also liefert `rejection_reason` hier `None`.
    """
    assert identity_of(symbol) == expected
    assert rejection_reason(symbol) is None


def test_die_vorschau_trennt_migration_von_ablehnung(tmp_path) -> None:
    """Der Kern: Wer bleibt, wer geht — und was das kostet.

    Die Erwartungen stehen ausgeschrieben da. Sie mit `identity_of`
    nachzurechnen hieße, die Vorschau mit sich selbst zu bestätigen.
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
    _add_prices(path, "GOLD.SG", quotes=3, daily=257)
    _add_prices(path, "VTI", quotes=1, daily=0)
    _add_prices(path, "BRK-B.DE", quotes=4, daily=9)

    with _connect(path) as connection:
        plan = plan_migration(connection)

    assert plan.needs_migration
    assert [
        (migration.symbol, migration.ticker, migration.mic)
        for migration in plan.migrated
    ] == [
        ("EUNL.DE", "EUNL", "XETR"),
        ("GOLD.SG", "GOLD", "XSTU"),
    ]
    assert [
        (
            rejection.symbol,
            rejection.reason,
            rejection.quotes,
            rejection.daily_closes,
        )
        for rejection in plan.rejected
    ] == [
        ("BRK-B.DE", REASON_NON_CANONICAL_TICKER, 4, 9),
        ("VTI", REASON_NO_SUFFIX, 1, 0),
    ]
    assert (plan.lost_quotes, plan.lost_daily_closes) == (5, 9)


def test_stuttgart_rettet_die_tagesschlusskurse(tmp_path) -> None:
    """Die Reihenfolgewarnung des Entwurfs, als Test statt als Fußnote.

    Ohne `XSTU` im Katalog wäre `GOLD.SG` nicht auflösbar und stünde hier in
    der Ablehnungsliste — mit **257** Tagesschlusskursen daneben. Übergabe 1
    hat den Eintrag gebracht; dieser Test hält fest, was daran hängt.
    """
    path = str(tmp_path / "gold.db")
    _legacy_database(path, [("GOLD.SG", "DE000A0S9GB0")])
    _add_prices(path, "GOLD.SG", quotes=0, daily=257)

    with _connect(path) as connection:
        plan = plan_migration(connection)

    assert plan.rejected == ()
    assert (plan.lost_daily_closes, plan.lost_quotes) == (0, 0)
    assert [(migration.ticker, migration.mic) for migration in plan.migrated] == [
        ("GOLD", "XSTU")
    ]


def test_die_vorschau_schreibt_nicht(tmp_path) -> None:
    """`#2b5`: Phase 1 ändert nichts — geprüft, nicht zugesagt.

    Die Verbindung wird **schreibgeschützt** geöffnet. Legte die Vorschau auch
    nur die fehlenden Identitätsspalten an, schlüge SQLite hier fehl. Ein Test,
    der bloß die Zeilen hinterher vergleicht, hätte die Schemaänderung
    übersehen.
    """
    path = str(tmp_path / "ro.db")
    _legacy_database(path, [("EUNL.DE", "IE00B4L5Y983"), ("VTI", None)])

    with _connect(path, read_only=True) as connection:
        plan = plan_migration(connection)

    assert plan.needs_migration
    with _connect(path) as connection:
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(instruments)")
        }
    assert "ticker" not in columns
    assert "mic" not in columns


def test_ein_leeres_alt_schema_ist_arbeit_ohne_rueckfrage(tmp_path) -> None:
    """**Hier stand die falsche Zusage** — und sie war betriebsgefährdend.

    Der Test hieß „ein leerer Bestand steht nicht aus" und behauptete
    `is_pending is False`. Das stimmte für die Zeilen und war für das
    **Schema** falsch: Einer leeren Pre-T-21-Datenbank fehlen `ticker`, `mic`
    und `listing_id` ganz. Der Dienst wäre normal gestartet, und die erste
    Neuanlage wäre an den fehlenden Spalten gebrochen (Codex, Runde 30).

    Richtig ist die Unterscheidung: Es **ist** etwas zu tun, aber es geht
    nichts verloren — also läuft es beim Start durch, ohne Rückfrage. Die
    Zustimmung schützt vor Datenverlust, nicht vor Schemaarbeit.
    """
    path = str(tmp_path / "leer.db")
    _legacy_database(path, [])

    with _connect(path) as connection:
        plan = plan_migration(connection)

    assert plan.needs_migration is True, "die Identitätsspalten fehlen"
    assert plan.needs_confirmation is False, "es geht nichts verloren"
    assert plan.schema_outdated is True
    assert (plan.migrated, plan.rejected, plan.unchanged) == ((), (), 0)


def test_ein_vollstaendig_zugeordneter_altbestand_braucht_die_haertung(
    tmp_path,
) -> None:
    """Der zweite Fall aus Runde 30: Teil 1 ist durch, die Härtung nicht.

    Jede Zeile trägt `ticker` und `mic`, es ist also nichts zu migrieren und
    nichts abzulehnen. Trotzdem sind die Spalten **nullable**, und
    `identity_status` steht noch — die zugesagte Invariante wäre schlicht
    falsch gewesen, und der alte `is_pending` hätte `False` gesagt.
    """
    path = str(tmp_path / "teil1.db")
    _legacy_database(path, [("EUNL.DE", "IE00B4L5Y983")])
    with sqlite3.connect(path) as connection:
        for column in ("ticker", "mic", "listing_id", "identity_status"):
            connection.execute(f"ALTER TABLE instruments ADD COLUMN {column} TEXT")
        connection.execute(
            "UPDATE instruments SET ticker = 'EUNL', mic = 'XETR', "
            "listing_id = 'alt-1', identity_status = 'resolved'"
        )

    with _connect(path) as connection:
        plan = plan_migration(connection)

    assert plan.unchanged == 1, "die Zeile ist bereits zugeordnet"
    assert (plan.migrated, plan.rejected) == ((), ())
    assert plan.schema_outdated is True, "nullable Spalten und identity_status"
    assert plan.needs_migration is True
    assert plan.needs_confirmation is False


def test_ein_fertiger_bestand_hat_nichts_mehr_zu_tun(tmp_path) -> None:
    """Die Gegenprobe — sonst wäre `schema_outdated` immer wahr.

    Nach `init_db` auf einer frischen Datei steht die Zielform: nullable
    `ticker`/`mic`, getaggte Identität mit `CHECK`, `identity_status` weg.
    """
    path = str(tmp_path / "fertig.db")
    assert init_db(path) is False

    with _connect(path) as connection:
        plan = plan_migration(connection)
        columns = {
            row["name"]: row
            for row in connection.execute("PRAGMA table_info(instruments)")
        }

    assert plan.needs_migration is False
    assert plan.schema_outdated is False
    assert "identity_status" not in columns
    # **Bis T-31 stand hier `NOT NULL` auf `ticker`/`mic`** — die richtige
    # Invariante, solange es nur Listings gab. Genau diese Zeile hat den P0 aus
    # Runde 4 gedeckt: Der Frischstart härtete zurück und warf den `CHECK` weg,
    # und der Test nannte das die Zielform.
    assert not any(columns[name]["notnull"] for name in ("ticker", "mic")), (
        "ticker/mic sind seit T-31 nullable — der CHECK bindet sie je Form"
    )
    assert {"kind", "base", "quote_currency"} <= set(columns)
    with _connect(path) as connection:
        ddl = connection.execute(
            "SELECT sql FROM sqlite_master WHERE name = 'instruments'"
        ).fetchone()["sql"]
    assert "kind = 'listed'" in ddl, "die Formregel steht im Schema"


def test_ein_verlustloser_altbestand_wird_beim_start_gehaertet(tmp_path) -> None:
    """Die Kehrseite: `init_db` erledigt es wirklich, statt es nur zu melden.

    Das ist der Fall, in dem der Dienst ohne Rückfrage weiterläuft — dann muss
    das Schema hinterher aber auch **stehen**. Sonst hätte die Unterscheidung
    nur den Namen der Lüge geändert.
    """
    path = str(tmp_path / "verlustlos.db")
    _legacy_database(path, [("EUNL.DE", "IE00B4L5Y983"), ("GOLD.SG", None)])

    assert init_db(path) is False, "nichts geht verloren, also keine Rückfrage"

    with _connect(path) as connection:
        plan = plan_migration(connection)
        rows = {
            row["symbol"]: (row["ticker"], row["mic"])
            for row in connection.execute(
                "SELECT symbol, ticker, mic FROM instruments"
            )
        }

    assert plan.needs_migration is False
    assert rows == {"EUNL.DE": ("EUNL", "XETR"), "GOLD.SG": ("GOLD", "XSTU")}


@pytest.mark.parametrize(
    ("ticker", "mic", "expected"),
    [
        ("AAPL", "XNAS", True),
        ("VTI", "US", False),
        (None, "XETR", False),
        ("EUNL", None, False),
        ("", "XETR", False),
    ],
    ids=["vollstaendig", "laenderpraefix_als_mic", "ohne_ticker", "ohne_mic", "leerer_ticker"],
)
def test_nur_eine_vollstaendige_zuordnung_bleibt_unangetastet(
    ticker: str | None, mic: str | None, expected: bool
) -> None:
    """Das Länderpräfix `US` im MIC-Feld ist keine Identität, sondern ihr Gegenteil.

    Eine solche Zeile wird neu bewertet statt durchgewunken — sonst überlebte
    genau der Wert den Umzug, den T-21 austreibt.
    """
    assert keeps_its_identity(ticker, mic) is expected


@pytest.mark.parametrize(
    ("kind", "values"),
    [
        ("pair", {"symbol": "BTC-EUR", "base": "BTC", "quote_currency": "EUR"}),
        ("isin_only", {"symbol": "DE0001102531", "isin": "DE0001102531"}),
    ],
    ids=["waehrungspaar", "nur-isin"],
)
def test_die_anderen_identitaetsformen_ueberleben_die_vorschau(
    tmp_path, kind: str, values: dict
) -> None:
    """Paar und reine ISIN sind vollständige Identitäten, keine Altlasten."""
    path = str(tmp_path / "heute.db")
    assert init_db(path) is False

    columns = ", ".join(["kind", *values])
    placeholders = ", ".join("?" * (len(values) + 1))
    with sqlite3.connect(path) as connection:
        connection.execute(
            f"INSERT INTO instruments ({columns}, first_seen) "
            f"VALUES ({placeholders}, '2026-08-31T00:00:00+00:00')",
            (kind, *values.values()),
        )

    with _connect(path) as connection:
        plan = plan_migration(connection)

    assert plan.rejected == (), (
        f"eine {kind}-Identität soll den Umzug überleben, nicht ihn auslösen: "
        f"{[rejection.reason for rejection in plan.rejected]}"
    )
    assert plan.needs_migration is False
    assert plan.unchanged == 1

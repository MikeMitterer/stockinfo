"""Die Vorschau des Identitäts-Umzugs — was sie sagt, und dass sie nichts tut.

Phase 1 aus T-21 Teil 3, Übergabe 2A. `init_db()` läuft im FastAPI-Lifespan,
also bevor die App den ersten Request bedient; ein UI, das erst danach
erreichbar wird, kann niemanden mehr warnen. Deshalb muss die Vorschau ohne
jede Schreiboperation auskommen — und genau das prüft `#2b5` hier, nicht durch
Zusicherung, sondern an einer schreibgeschützten Verbindung.
"""

import sqlite3

import pytest

from app.migration import (
    REASON_NO_SUFFIX,
    REASON_NON_CANONICAL_TICKER,
    REASON_UNKNOWN_SUFFIX,
    identity_of,
    keeps_its_identity,
    plan_migration,
    rejection_reason,
)


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

    assert plan.is_pending
    assert [(m.symbol, m.ticker, m.mic) for m in plan.migrated] == [
        ("EUNL.DE", "EUNL", "XETR"),
        ("GOLD.SG", "GOLD", "XSTU"),
    ]
    assert [(r.symbol, r.reason, r.quotes, r.daily_closes) for r in plan.rejected] == [
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
    assert [(m.ticker, m.mic) for m in plan.migrated] == [("GOLD", "XSTU")]


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

    assert plan.is_pending
    with _connect(path) as connection:
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(instruments)")
        }
    assert "ticker" not in columns
    assert "mic" not in columns


def test_ein_leerer_bestand_steht_nicht_aus(tmp_path) -> None:
    """Eine frische Installation darf keine Bestätigung für nichts verlangen."""
    path = str(tmp_path / "leer.db")
    _legacy_database(path, [])

    with _connect(path) as connection:
        plan = plan_migration(connection)

    assert plan.is_pending is False
    assert (plan.migrated, plan.rejected, plan.unchanged) == ((), (), 0)


@pytest.mark.parametrize(
    ("ticker", "mic", "expected"),
    [
        ("AAPL", "XNAS", True),
        ("VTI", "US", False),
        (None, "XETR", False),
        ("EUNL", None, False),
        ("", "XETR", False),
    ],
    ids=["vollstaendig", "sammelcode_als_mic", "ohne_ticker", "ohne_mic", "leerer_ticker"],
)
def test_nur_eine_vollstaendige_zuordnung_bleibt_unangetastet(
    ticker: str | None, mic: str | None, expected: bool
) -> None:
    """Der Sammelcode `US` im MIC-Feld ist keine Identität, sondern ihr Gegenteil.

    Eine solche Zeile wird neu bewertet statt durchgewunken — sonst überlebte
    genau der Wert den Umzug, den T-21 austreibt.
    """
    assert keeps_its_identity(ticker, mic) is expected

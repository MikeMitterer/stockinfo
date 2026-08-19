"""Tests für das SQLite-Repository (temporäre DB, kein Netz)."""

from pathlib import Path

import pytest

from app.db import init_db
from app.models import QuoteResponse
from app.repository import QuoteRepository


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    """Repository auf einer frisch initialisierten temporären DB."""
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    return QuoteRepository(db_path)


def _quote(price: float, quote_time: str, fetched_at: str) -> QuoteResponse:
    return QuoteResponse(
        isin="IE00B3RBWM25",
        symbol="VGWL.DE",
        exchange="Xetra",
        name="Vanguard FTSE All-World",
        type="etf",
        currency="EUR",
        price=price,
        quote_time=quote_time,
        volume=1000,
        ter=0.19,
        provider="Vanguard",
        fetched_at=fetched_at,
    )


def test_save_und_lese_instrument_und_quote(repo: QuoteRepository) -> None:
    repo.save_quote(
        _quote(160.98, "2026-07-12T17:00:00+00:00", "2026-07-12T17:00:00+00:00")
    )

    instrument = repo.get_instrument_by_isin("IE00B3RBWM25")
    assert instrument is not None
    assert instrument["symbol"] == "VGWL.DE"
    assert instrument["ter"] == 0.19

    latest = repo.get_latest_quote(instrument["id"])
    assert latest is not None
    assert latest["price"] == 160.98


def test_upsert_aktualisiert_metadaten_ohne_duplikat(repo: QuoteRepository) -> None:
    repo.save_quote(
        _quote(160.0, "2026-07-12T17:00:00+00:00", "2026-07-12T17:00:00+00:00")
    )
    repo.save_quote(
        _quote(161.0, "2026-07-12T18:00:00+00:00", "2026-07-12T18:00:00+00:00")
    )

    instruments = repo.list_instruments()
    assert len(instruments) == 1  # nur ein Instrument

    history = repo.get_history(instruments[0]["id"])
    assert len(history) == 2  # zwei Kurspunkte
    assert history[0]["price"] == 161.0  # neueste zuerst


def test_dedup_gleicher_quote_time(repo: QuoteRepository) -> None:
    repo.save_quote(
        _quote(160.0, "2026-07-12T17:00:00+00:00", "2026-07-12T17:00:00+00:00")
    )
    repo.save_quote(
        _quote(999.0, "2026-07-12T17:00:00+00:00", "2026-07-12T18:00:00+00:00")
    )

    instrument = repo.get_instrument_by_isin("IE00B3RBWM25")
    history = repo.get_history(instrument["id"])
    assert len(history) == 1  # gleicher quote_time → kein zweiter Punkt


def test_history_limit_und_grenzen(repo: QuoteRepository) -> None:
    for hour in range(10, 15):
        ts = f"2026-07-12T{hour:02d}:00:00+00:00"
        repo.save_quote(_quote(100.0 + hour, ts, ts))

    instrument = repo.get_instrument_by_isin("IE00B3RBWM25")
    limited = repo.get_history(instrument["id"], limit=2)
    assert len(limited) == 2

    ranged = repo.get_history(
        instrument["id"],
        date_from="2026-07-12T12:00:00+00:00",
        date_to="2026-07-12T13:00:00+00:00",
    )
    assert len(ranged) == 2


def test_migration_ergaenzt_die_neuen_spalten(tmp_path) -> None:
    """Bestehende Datenbanken ziehen beim Start nach — ohne Zutun.

    Nachgestellt wird eine DB im alten Stand: beide Tabellen ohne die neuen
    Spalten. `init_db` muss sie ergaenzen, und ein zweiter Lauf darf nicht
    daran scheitern, dass sie schon da sind.
    """
    import sqlite3

    from app.db import init_db

    pfad = str(tmp_path / "alt.db")
    with sqlite3.connect(pfad) as verbindung:
        verbindung.executescript(
            """
            CREATE TABLE instruments (
                id INTEGER PRIMARY KEY, isin TEXT, symbol TEXT NOT NULL,
                exchange TEXT, name TEXT, type TEXT, currency TEXT,
                provider TEXT, ter REAL, replication TEXT, fund_size REAL,
                meta_fetched_at TEXT
            );
            CREATE TABLE instrument_overrides (
                instrument_id INTEGER PRIMARY KEY,
                ter REAL, volatility REAL, accumulating INTEGER,
                updated_at TEXT NOT NULL
            );
            """
        )

    init_db(pfad)
    init_db(pfad)  # zweimal: die Migration muss idempotent sein

    with sqlite3.connect(pfad) as verbindung:
        verbindung.row_factory = sqlite3.Row
        instrumente = {r["name"] for r in verbindung.execute("PRAGMA table_info(instruments)")}
        overrides = {
            r["name"] for r in verbindung.execute("PRAGMA table_info(instrument_overrides)")
        }

    # `source` gehört dazu: Der Detailbereich nennt die Quelle, und ohne Nachzug
    # stünde dort auf jeder bestehenden Datenbank dauerhaft nichts.
    assert {"fund_domicile", "fund_currency", "source"} <= instrumente
    assert {"provider", "replication", "fund_size", "fund_domicile", "fund_currency"} <= overrides


def test_duplikate_verlieren_weder_overrides_noch_daily_wasserzeichen(tmp_path) -> None:
    """Beim Zusammenführen von Symbol-Duplikaten darf nichts verschwinden.

    Vor dem UNIQUE-Index konnten durch parallele Erst-Requests zwei Zeilen mit
    demselben Symbol entstehen. Umgehängt wurden bisher nur `quotes` und
    `daily_closes` — `daily_meta` und `instrument_overrides` blieben am
    Duplikat hängen und fielen dem `ON DELETE CASCADE` zum Opfer.

    Nachgestellt wird der ungünstige Fall: Die von Hand gepflegten Kennzahlen
    und das Daily-Wasserzeichen liegen **am Duplikat**, nicht am Keeper.
    """
    import sqlite3

    from app.db import init_db

    pfad = str(tmp_path / "duplikate.db")
    with sqlite3.connect(pfad) as verbindung:
        verbindung.executescript(
            """
            CREATE TABLE instruments (
                id INTEGER PRIMARY KEY, isin TEXT, symbol TEXT NOT NULL,
                exchange TEXT, name TEXT, type TEXT, currency TEXT,
                provider TEXT, ter REAL, replication TEXT, fund_size REAL,
                first_seen TEXT NOT NULL, meta_fetched_at TEXT
            );
            CREATE TABLE quotes (
                id INTEGER PRIMARY KEY, instrument_id INTEGER NOT NULL,
                price REAL NOT NULL, currency TEXT, quote_time TEXT,
                fetched_at TEXT NOT NULL
            );
            CREATE TABLE daily_closes (
                instrument_id INTEGER NOT NULL, date TEXT NOT NULL,
                close REAL NOT NULL, currency TEXT,
                PRIMARY KEY (instrument_id, date)
            );
            CREATE TABLE daily_meta (
                instrument_id INTEGER PRIMARY KEY,
                fetched_from TEXT, fetched_to TEXT
            );
            CREATE TABLE instrument_overrides (
                instrument_id INTEGER PRIMARY KEY,
                ter REAL, volatility REAL, accumulating INTEGER,
                updated_at TEXT NOT NULL
            );

            -- 1 gewinnt (hat eine ISIN), 2 ist das Duplikat
            INSERT INTO instruments (id, isin, symbol, first_seen)
                 VALUES (1, 'IE00B4L5Y983', 'EUNL.DE', '2026-01-01');
            INSERT INTO instruments (id, isin, symbol, first_seen)
                 VALUES (2, NULL, 'EUNL.DE', '2026-01-02');

            INSERT INTO quotes (instrument_id, price, fetched_at)
                 VALUES (2, 128.7, '2026-01-02');
            INSERT INTO daily_closes (instrument_id, date, close)
                 VALUES (2, '2026-01-02', 128.7);
            INSERT INTO daily_meta (instrument_id, fetched_from, fetched_to)
                 VALUES (2, '2025-01-01', '2026-01-02');
            INSERT INTO instrument_overrides (instrument_id, ter, updated_at)
                 VALUES (2, 0.2, '2026-01-02');
            """
        )

    init_db(pfad)

    with sqlite3.connect(pfad) as verbindung:
        verbindung.row_factory = sqlite3.Row
        instrumente = verbindung.execute("SELECT id FROM instruments").fetchall()
        override = verbindung.execute(
            "SELECT instrument_id, ter FROM instrument_overrides"
        ).fetchall()
        meta = verbindung.execute(
            "SELECT instrument_id, fetched_from, fetched_to FROM daily_meta"
        ).fetchall()

    assert [r["id"] for r in instrumente] == [1], "das Duplikat muss verschwinden"

    assert len(override) == 1, "der von Hand gepflegte Wert darf nicht verlorengehen"
    assert override[0]["instrument_id"] == 1
    assert override[0]["ter"] == 0.2

    assert len(meta) == 1, "das Daily-Wasserzeichen darf nicht verlorengehen"
    assert meta[0]["instrument_id"] == 1
    assert (meta[0]["fetched_from"], meta[0]["fetched_to"]) == ("2025-01-01", "2026-01-02")


def _alte_db_mit_duplikat(pfad: str, zusatz_sql: str) -> None:
    """Legt eine DB im Vor-Index-Stand an: zwei Zeilen mit demselben Symbol.

    Args:
        pfad: Dateipfad der anzulegenden SQLite-Datei.
        zusatz_sql: Weitere INSERTs für den jeweiligen Testfall.
    """
    import sqlite3

    with sqlite3.connect(pfad) as verbindung:
        verbindung.executescript(
            """
            CREATE TABLE instruments (
                id INTEGER PRIMARY KEY, isin TEXT, symbol TEXT NOT NULL,
                exchange TEXT, name TEXT, type TEXT, currency TEXT,
                provider TEXT, ter REAL, replication TEXT, fund_size REAL,
                first_seen TEXT NOT NULL, meta_fetched_at TEXT
            );
            CREATE TABLE daily_meta (
                instrument_id INTEGER PRIMARY KEY,
                fetched_from TEXT, fetched_to TEXT
            );
            CREATE TABLE instrument_overrides (
                instrument_id INTEGER PRIMARY KEY,
                ter REAL, volatility REAL, accumulating INTEGER,
                updated_at TEXT NOT NULL
            );

            INSERT INTO instruments (id, isin, symbol, first_seen)
                 VALUES (1, 'IE00B4L5Y983', 'EUNL.DE', '2026-01-01');
            INSERT INTO instruments (id, isin, symbol, first_seen)
                 VALUES (2, NULL, 'EUNL.DE', '2026-01-02');
            """
            + zusatz_sql
        )


def test_overrides_werden_feldweise_zusammengefuehrt(tmp_path) -> None:
    """Bei einem Konflikt gewinnt der Keeper — aber nur Feld für Feld.

    Zeilenweise zu entscheiden hieße, die Lücken des Gewinners offen zu lassen,
    obwohl das Duplikat sie füllen könnte. Beides sind von Hand gepflegte
    Werte; keiner davon darf verlorengehen, nur weil der andere danebensteht.
    """
    import sqlite3

    from app.db import init_db

    pfad = str(tmp_path / "konflikt.db")
    _alte_db_mit_duplikat(
        pfad,
        """
        -- Keeper: TER gepflegt, Volatilität offen
        INSERT INTO instrument_overrides (instrument_id, ter, volatility, updated_at)
             VALUES (1, 0.20, NULL, '2026-01-01');
        -- Duplikat: beides gepflegt — die TER kollidiert
        INSERT INTO instrument_overrides (instrument_id, ter, volatility, updated_at)
             VALUES (2, 0.99, 12.5, '2026-02-01');
        """,
    )

    init_db(pfad)

    with sqlite3.connect(pfad) as verbindung:
        verbindung.row_factory = sqlite3.Row
        zeilen = verbindung.execute("SELECT * FROM instrument_overrides").fetchall()

    assert len(zeilen) == 1
    assert zeilen[0]["ter"] == 0.20, "der Keeper behält bei Konflikt das letzte Wort"
    assert zeilen[0]["volatility"] == 12.5, "seine Lücke füllt das Duplikat"
    assert zeilen[0]["updated_at"] == "2026-02-01", "der jüngere Stand zählt"


def test_daily_spannen_mit_luecke_werden_nicht_zusammengezogen(tmp_path) -> None:
    """Eine Lücke zwischen zwei Spannen darf nicht überdeckt werden.

    Das Wasserzeichen sagt „diese Spanne ist geholt". Würden zwei getrennte
    Spannen zu einer verschmolzen, behauptete es Tage als geholt, die niemand
    geholt hat — und der nächste Abgleich überspränge sie dauerhaft.
    """
    import sqlite3

    from app.db import init_db

    pfad = str(tmp_path / "luecke.db")
    _alte_db_mit_duplikat(
        pfad,
        """
        INSERT INTO daily_meta (instrument_id, fetched_from, fetched_to)
             VALUES (1, '2026-06-01', '2026-08-01');
        -- endet lange vor dem Keeper-Beginn: dazwischen fehlen Monate
        INSERT INTO daily_meta (instrument_id, fetched_from, fetched_to)
             VALUES (2, '2025-01-01', '2025-03-01');
        """,
    )

    init_db(pfad)

    with sqlite3.connect(pfad) as verbindung:
        verbindung.row_factory = sqlite3.Row
        zeilen = verbindung.execute("SELECT * FROM daily_meta").fetchall()

    assert len(zeilen) == 1
    assert zeilen[0]["instrument_id"] == 1
    assert (zeilen[0]["fetched_from"], zeilen[0]["fetched_to"]) == ("2026-06-01", "2026-08-01")


def test_ueberlappende_daily_spannen_werden_geweitet(tmp_path) -> None:
    """Überlappen sich die Spannen, ist die Vereinigung lückenlos — also zulässig."""
    import sqlite3

    from app.db import init_db

    pfad = str(tmp_path / "ueberlappung.db")
    _alte_db_mit_duplikat(
        pfad,
        """
        INSERT INTO daily_meta (instrument_id, fetched_from, fetched_to)
             VALUES (1, '2026-01-01', '2026-08-01');
        INSERT INTO daily_meta (instrument_id, fetched_from, fetched_to)
             VALUES (2, '2025-01-01', '2026-03-01');
        """,
    )

    init_db(pfad)

    with sqlite3.connect(pfad) as verbindung:
        verbindung.row_factory = sqlite3.Row
        zeile = verbindung.execute("SELECT * FROM daily_meta").fetchone()

    assert (zeile["fetched_from"], zeile["fetched_to"]) == ("2025-01-01", "2026-08-01")


def test_gescheiterte_anreicherung_loescht_die_gespeicherten_etf_daten_nicht(
    repo: QuoteRepository,
) -> None:
    """Ein Ausfall bei justETF darf den letzten bekannten Stand nicht wegwischen.

    Das ist am 2026-08-18 real passiert: Ein Refresh über einen Pfad ohne ISIN
    ließ die Anreicherung aus, die Antwort trug deshalb leere ETF-Felder — und
    der Upsert schrieb sie alle nach `NULL`. TER, Replikationsart,
    Fondsvolumen und Thesaurierung waren weg, obwohl niemand sie geändert hat.

    `metadata_complete=False` sagt: „Diese Antwort weiß über die ETF-Extras
    nichts." Sie darf den gespeicherten Stand dann nicht ersetzen.
    """
    vollstaendig = QuoteResponse(
        isin="IE00B4L5Y983",
        symbol="EUNL.DE",
        exchange="Xetra",
        name="iShares Core MSCI World",
        type="etf",
        currency="EUR",
        price=128.7,
        quote_time="2026-08-18T10:00:00+00:00",
        ter=0.2,
        provider="iShares",
        replication="Physical",
        fund_size=129445.0,
        fund_domicile="Ireland",
        fund_currency="USD",
        volatility=10.68,
        accumulating=True,
        source="yfinance+justetf",
        fetched_at="2026-08-18T10:00:00+00:00",
    )
    repo.save_quote(vollstaendig)

    # Derselbe Kurs, aber ohne jede ETF-Angabe — so sieht eine Antwort aus,
    # wenn justETF nicht erreichbar war.
    ohne_anreicherung = QuoteResponse(
        isin="IE00B4L5Y983",
        symbol="EUNL.DE",
        exchange="Xetra",
        name="iShares Core MSCI World",
        type="etf",
        currency="EUR",
        price=129.1,
        quote_time="2026-08-18T11:00:00+00:00",
        source="yfinance",
        metadata_complete=False,
        fetched_at="2026-08-18T11:00:00+00:00",
    )
    repo.save_quote(ohne_anreicherung)

    gespeichert = repo.get_instrument_by_isin("IE00B4L5Y983")

    assert gespeichert["ter"] == 0.2
    assert gespeichert["provider"] == "iShares"
    assert gespeichert["replication"] == "Physical"
    assert gespeichert["fund_size"] == 129445.0
    assert gespeichert["fund_domicile"] == "Ireland"
    assert gespeichert["fund_currency"] == "USD"
    assert gespeichert["volatility"] == 10.68
    assert gespeichert["accumulating"] == 1
    # Die Herkunft gehört zum selben Stand: Sie beschreibt die Werte, die
    # stehengeblieben sind — nicht den Abruf, der nichts geliefert hat.
    assert gespeichert["source"] == "yfinance+justetf"


def test_erfolgreiche_anreicherung_darf_felder_weiterhin_leeren(
    repo: QuoteRepository,
) -> None:
    """Die Gegenrichtung — sonst wäre aus dem Schutz ein Einbahnstraßen-Cache.

    Liefert justETF erfolgreich und lässt ein Feld dabei bewusst leer, muss der
    gespeicherte Wert verschwinden. „Erfolgreich abgefragt, Feld leer" ist eine
    Aussage; „nicht abgefragt" ist keine.
    """
    repo.save_quote(
        QuoteResponse(
            isin="IE00B4L5Y983", symbol="EUNL.DE", type="etf", price=128.7,
            quote_time="2026-08-18T10:00:00+00:00", ter=0.2, provider="iShares",
            fetched_at="2026-08-18T10:00:00+00:00",
        )
    )
    repo.save_quote(
        QuoteResponse(
            isin="IE00B4L5Y983", symbol="EUNL.DE", type="etf", price=129.1,
            quote_time="2026-08-18T11:00:00+00:00", ter=None, provider="iShares",
            fetched_at="2026-08-18T11:00:00+00:00",
        )
    )

    assert repo.get_instrument_by_isin("IE00B4L5Y983")["ter"] is None

"""Tests für das SQLite-Repository (temporäre DB, kein Netz)."""

import threading
from pathlib import Path

import pytest

from app.db import init_db
from app.models import QuoteResponse
from app.repository import IncompleteIdentityError, QuoteRepository, SavedQuote


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
        ticker="VGWL",
        mic="XETR",
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
        timestamp = f"2026-07-12T{hour:02d}:00:00+00:00"
        repo.save_quote(_quote(100.0 + hour, timestamp, timestamp))

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

    db_file = str(tmp_path / "alt.db")
    with sqlite3.connect(db_file) as connection:
        connection.executescript(
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

    init_db(db_file)
    init_db(db_file)  # zweimal: die Migration muss idempotent sein

    with sqlite3.connect(db_file) as connection:
        connection.row_factory = sqlite3.Row
        instrument_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(instruments)")
        }
        overrides = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(instrument_overrides)")
        }

    # `source` gehört dazu: Der Detailbereich nennt die Quelle, und ohne Nachzug
    # stünde dort auf jeder bestehenden Datenbank dauerhaft nichts.
    assert {"fund_domicile", "fund_currency", "source"} <= instrument_columns
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

    from app.db import init_db, run_migration

    db_file = str(tmp_path / "duplikate.db")
    with sqlite3.connect(db_file) as connection:
        connection.executescript(
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

    # Die Bereinigung läuft seit T-21 Teil 3 im **bestätigten** Umzug, nicht
    # mehr im Start: `init_db` erkennt nur noch, `run_migration` führt aus.
    init_db(db_file)
    run_migration(db_file, rejected_at="2026-08-25T12:00:00+00:00")

    with sqlite3.connect(db_file) as connection:
        connection.row_factory = sqlite3.Row
        instrument_rows = connection.execute("SELECT id FROM instruments").fetchall()
        override = connection.execute(
            "SELECT instrument_id, ter FROM instrument_overrides"
        ).fetchall()
        meta = connection.execute(
            "SELECT instrument_id, fetched_from, fetched_to FROM daily_meta"
        ).fetchall()

    assert [row["id"] for row in instrument_rows] == [1], (
        "das Duplikat muss verschwinden"
    )

    assert len(override) == 1, "der von Hand gepflegte Wert darf nicht verlorengehen"
    assert override[0]["instrument_id"] == 1
    assert override[0]["ter"] == 0.2

    assert len(meta) == 1, "das Daily-Wasserzeichen darf nicht verlorengehen"
    assert meta[0]["instrument_id"] == 1
    assert (meta[0]["fetched_from"], meta[0]["fetched_to"]) == ("2025-01-01", "2026-01-02")


def _legacy_db_with_duplicate(db_file: str, extra_sql: str) -> None:
    """Legt eine DB im Vor-Index-Stand an: zwei Zeilen mit demselben Symbol.

    Args:
        db_file: Dateipfad der anzulegenden SQLite-Datei.
        extra_sql: Weitere INSERTs für den jeweiligen Testfall.
    """
    import sqlite3

    with sqlite3.connect(db_file) as connection:
        connection.executescript(
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
            + extra_sql
        )


def test_overrides_werden_feldweise_zusammengefuehrt(tmp_path) -> None:
    """Bei einem Konflikt gewinnt der Keeper — aber nur Feld für Feld.

    Zeilenweise zu entscheiden hieße, die Lücken des Gewinners offen zu lassen,
    obwohl das Duplikat sie füllen könnte. Beides sind von Hand gepflegte
    Werte; keiner davon darf verlorengehen, nur weil der andere danebensteht.
    """
    import sqlite3

    from app.db import init_db, run_migration

    db_file = str(tmp_path / "konflikt.db")
    _legacy_db_with_duplicate(
        db_file,
        """
        -- Keeper: TER gepflegt, Volatilität offen
        INSERT INTO instrument_overrides (instrument_id, ter, volatility, updated_at)
             VALUES (1, 0.20, NULL, '2026-01-01');
        -- Duplikat: beides gepflegt — die TER kollidiert
        INSERT INTO instrument_overrides (instrument_id, ter, volatility, updated_at)
             VALUES (2, 0.99, 12.5, '2026-02-01');
        """,
    )

    # Die Bereinigung läuft seit T-21 Teil 3 im **bestätigten** Umzug, nicht
    # mehr im Start: `init_db` erkennt nur noch, `run_migration` führt aus.
    init_db(db_file)
    run_migration(db_file, rejected_at="2026-08-25T12:00:00+00:00")

    with sqlite3.connect(db_file) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("SELECT * FROM instrument_overrides").fetchall()

    assert len(rows) == 1
    assert rows[0]["ter"] == 0.20, "der Keeper behält bei Konflikt das letzte Wort"
    assert rows[0]["volatility"] == 12.5, "seine Lücke füllt das Duplikat"
    assert rows[0]["updated_at"] == "2026-02-01", "der jüngere Stand zählt"


def test_daily_spannen_mit_luecke_werden_nicht_zusammengezogen(tmp_path) -> None:
    """Eine Lücke zwischen zwei Spannen darf nicht überdeckt werden.

    Das Wasserzeichen sagt „diese Spanne ist geholt". Würden zwei getrennte
    Spannen zu einer verschmolzen, behauptete es Tage als geholt, die niemand
    geholt hat — und der nächste Abgleich überspränge sie dauerhaft.
    """
    import sqlite3

    from app.db import init_db, run_migration

    db_file = str(tmp_path / "luecke.db")
    _legacy_db_with_duplicate(
        db_file,
        """
        INSERT INTO daily_meta (instrument_id, fetched_from, fetched_to)
             VALUES (1, '2026-06-01', '2026-08-01');
        -- endet lange vor dem Keeper-Beginn: dazwischen fehlen Monate
        INSERT INTO daily_meta (instrument_id, fetched_from, fetched_to)
             VALUES (2, '2025-01-01', '2025-03-01');
        """,
    )

    # Die Bereinigung läuft seit T-21 Teil 3 im **bestätigten** Umzug, nicht
    # mehr im Start: `init_db` erkennt nur noch, `run_migration` führt aus.
    init_db(db_file)
    run_migration(db_file, rejected_at="2026-08-25T12:00:00+00:00")

    with sqlite3.connect(db_file) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("SELECT * FROM daily_meta").fetchall()

    assert len(rows) == 1
    assert rows[0]["instrument_id"] == 1
    assert (rows[0]["fetched_from"], rows[0]["fetched_to"]) == ("2026-06-01", "2026-08-01")


def test_ueberlappende_daily_spannen_werden_geweitet(tmp_path) -> None:
    """Überlappen sich die Spannen, ist die Vereinigung lückenlos — also zulässig."""
    import sqlite3

    from app.db import init_db, run_migration

    db_file = str(tmp_path / "ueberlappung.db")
    _legacy_db_with_duplicate(
        db_file,
        """
        INSERT INTO daily_meta (instrument_id, fetched_from, fetched_to)
             VALUES (1, '2026-01-01', '2026-08-01');
        INSERT INTO daily_meta (instrument_id, fetched_from, fetched_to)
             VALUES (2, '2025-01-01', '2026-03-01');
        """,
    )

    # Die Bereinigung läuft seit T-21 Teil 3 im **bestätigten** Umzug, nicht
    # mehr im Start: `init_db` erkennt nur noch, `run_migration` führt aus.
    init_db(db_file)
    run_migration(db_file, rejected_at="2026-08-25T12:00:00+00:00")

    with sqlite3.connect(db_file) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT * FROM daily_meta").fetchone()

    assert (row["fetched_from"], row["fetched_to"]) == ("2025-01-01", "2026-08-01")


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
    complete_response = QuoteResponse(
        isin="IE00B4L5Y983",
        symbol="EUNL.DE",
        ticker="EUNL",
        mic="XETR",
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
    repo.save_quote(complete_response)

    # Derselbe Kurs, aber ohne jede ETF-Angabe — so sieht eine Antwort aus,
    # wenn justETF nicht erreichbar war.
    without_enrichment = QuoteResponse(
        isin="IE00B4L5Y983",
        symbol="EUNL.DE",
        ticker="EUNL",
        mic="XETR",
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
    repo.save_quote(without_enrichment)

    stored = repo.get_instrument_by_isin("IE00B4L5Y983")

    assert stored["ter"] == 0.2
    assert stored["provider"] == "iShares"
    assert stored["replication"] == "Physical"
    assert stored["fund_size"] == 129445.0
    assert stored["fund_domicile"] == "Ireland"
    assert stored["fund_currency"] == "USD"
    assert stored["volatility"] == 10.68
    assert stored["accumulating"] == 1
    # Die Herkunft gehört zum selben Stand: Sie beschreibt die Werte, die
    # stehengeblieben sind — nicht den Abruf, der nichts geliefert hat.
    assert stored["source"] == "yfinance+justetf"


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
            isin="IE00B4L5Y983", symbol="EUNL.DE", ticker="EUNL", mic="XETR",
            currency="EUR", type="etf", price=128.7,
            quote_time="2026-08-18T10:00:00+00:00", ter=0.2, provider="iShares",
            fetched_at="2026-08-18T10:00:00+00:00",
        )
    )
    repo.save_quote(
        QuoteResponse(
            isin="IE00B4L5Y983", symbol="EUNL.DE", ticker="EUNL", mic="XETR",
            currency="EUR", type="etf", price=129.1,
            quote_time="2026-08-18T11:00:00+00:00", ter=None, provider="iShares",
            fetched_at="2026-08-18T11:00:00+00:00",
        )
    )

    assert repo.get_instrument_by_isin("IE00B4L5Y983")["ter"] is None


def test_erster_insert_mit_unvollstaendigen_metadaten(repo: QuoteRepository) -> None:
    """Ein neues Papier ohne belastbare ETF-Felder muss sich anlegen lassen.

    `_writable_fields` liefert bei `metadata_complete=False` nur die Nicht-ETF-
    Spalten. Baute der INSERT seine Spaltenliste weiter aus `_META_FIELDS`,
    zählte er dreizehn Platzhalter gegen vier Werte und brach mit
    `Incorrect number of bindings supplied` ab — ein 500 auf einem schlichten
    GET. Ausgelöst von jedem Papier, dessen justETF-Abruf beim ersten Kontakt
    scheitert.

    **Das Beispiel hat gewechselt.** Hier stand `BTC-USD`, weil eine
    Kryptowährung nie belastbare ETF-Felder mitbringt. Seit T-21 Teil 3 lässt
    sich ein Symbol ohne Handelsplatz nicht mehr anlegen; ob das so bleiben
    soll, klärt `T-31-papiere-ohne-mic.md`. Der geprüfte Fehler hing nie an
    der Gattung, sondern an der Platzhalterzahl — `GOLD.SG` mit leeren
    Metadaten löst ihn genauso aus.
    """
    repo.save_quote(
        QuoteResponse(
            isin=None, symbol="GOLD.SG", ticker="GOLD", mic="XSTU", type=None,
            currency="EUR", price=122.41,
            quote_time="2026-08-19T10:00:00+00:00",
            fetched_at="2026-08-19T10:00:00+00:00",
            metadata_complete=False,
        )
    )

    instrument = repo.get_instrument_by_symbol("GOLD.SG")
    assert instrument is not None
    assert instrument["currency"] == "EUR"
    # Die geschützten Felder bleiben leer statt mit Platzhaltern gefüllt.
    assert instrument["ter"] is None
    assert instrument["provider"] is None


def test_ein_papier_ohne_handelsplatz_wird_nicht_angelegt(
    repo: QuoteRepository,
) -> None:
    """Der Zustand nach T-21 Teil 3 — **festgehalten, nicht gutgeheißen**.

    Eine Kryptowährung hat keinen MIC nach ISO 10383; unter der Pflichtregel
    lässt sie sich deshalb nicht speichern. Ob StockInfo diese Gattung weiter
    bedienen soll, ist **offen** und liegt als `T-31-papiere-ohne-mic.md` auf
    dem Board. Dieser Test hält fest, was heute geschieht, damit die spätere
    Entscheidung eine sichtbare Stelle zum Ändern hat — er ist keine Zusage,
    dass es so bleibt.

    Abgelehnt wird mit einem eigenen Fehler statt mit einer
    `NOT NULL`-Verletzung: dieselbe Ablehnung, aber sie sagt, was fehlt.
    """
    # Seit Runde 40 mit einem **vorhandenen, aber ungültigen** Wert: `ticker`
    # und `mic` sind nicht-nullbare Pflichtfelder, „gar keine Identität" lässt
    # sich am Modell nicht mehr ausdrücken. Für eine Kryptowährung gibt es
    # keinen ISO-10383-MIC — der Sammelcode ist der nächstbeste Griff, und
    # genau den lehnt `canonical_identity` ab.
    with pytest.raises(IncompleteIdentityError) as rejected:
        repo.save_quote(
            QuoteResponse(
                isin=None, symbol="BTC-USD", ticker="BTC", mic="US",
                type=None, currency="USD",
                price=61234.0,
                quote_time="2026-08-19T10:00:00+00:00",
                fetched_at="2026-08-19T10:00:00+00:00",
                metadata_complete=False,
            )
        )

    assert rejected.value.symbol == "BTC-USD"
    assert repo.get_instrument_by_symbol("BTC-USD") is None


def test_unvollstaendige_antwort_setzt_den_metadaten_zeitstempel_nicht_hoch(
    repo: QuoteRepository,
) -> None:
    """Sonst läuft `metadata_ttl_days` leer und justETF wird nie wieder gefragt.

    `_etf_metadata_is_stale` liest genau diese Spalte. Wandert sie bei jeder
    unvollständigen Antwort mit, gilt der Stand dauerhaft als frisch — und der
    Scheduler läuft weit häufiger als die sieben Tage. Ein ETF, der seine
    Kennzahlen beim ersten Kontakt nicht bekam, behielte sie für immer leer.
    """
    repo.save_quote(
        QuoteResponse(
            isin="IE00B4L5Y983", symbol="EUNL.DE", ticker="EUNL", mic="XETR",
            currency="EUR", type="etf", price=128.7,
            quote_time="2026-08-01T10:00:00+00:00", ter=0.2, provider="iShares",
            fetched_at="2026-08-01T10:00:00+00:00",
        )
    )
    repo.save_quote(
        QuoteResponse(
            isin="IE00B4L5Y983", symbol="EUNL.DE", ticker="EUNL", mic="XETR",
            currency="EUR", type="etf", price=129.1,
            quote_time="2026-08-19T11:00:00+00:00",
            fetched_at="2026-08-19T11:00:00+00:00",
            metadata_complete=False,
        )
    )

    instrument = repo.get_instrument_by_isin("IE00B4L5Y983")
    assert instrument["meta_fetched_at"] == "2026-08-01T10:00:00+00:00"
    assert instrument["ter"] == 0.2  # der gepflegte Stand bleibt ohnehin stehen


def test_erster_insert_ohne_metadaten_gilt_sofort_als_faellig(
    repo: QuoteRepository,
) -> None:
    """Kein Zeitstempel heißt „nie geholt" — der nächste Abruf sieht nach."""
    repo.save_quote(
        QuoteResponse(
            isin="IE00B4L5Y983", symbol="EUNL.DE", ticker="EUNL", mic="XETR",
            currency="EUR", type="etf", price=128.7,
            quote_time="2026-08-19T10:00:00+00:00",
            fetched_at="2026-08-19T10:00:00+00:00",
            metadata_complete=False,
        )
    )

    assert repo.get_instrument_by_isin("IE00B4L5Y983")["meta_fetched_at"] is None


def test_ein_verlorenes_rennen_meldet_keine_neuanlage(
    repo: QuoteRepository, monkeypatch
) -> None:
    """`#2j2`: der Konfliktzweig, deterministisch — **das ist der Beleg**.

    Der Thread-Test darunter ist die realistische Probe, aber kein Beweis: Ob
    zwei Schreiber wirklich kollidieren, entscheidet das Timing, und eine
    Mutationsprobe hat gezeigt, dass der `IntegrityError`-Zweig dort nur in
    zwei von drei Läufen überhaupt erreicht wird.

    Hier wird das Rennen deshalb erzwungen: Der Preflight sieht die schon
    vorhandene Zeile **einmal** nicht — genau die Lage, in der ein
    konkurrierender Insert ihn überholt hat. Der `INSERT` läuft in den
    UNIQUE-Index, und die Antwort muss `created=False` lauten, nicht `201`.
    """
    stored = _quote(128.4, "2026-08-19T10:00:00+00:00", "2026-08-19T10:00:00+00:00")
    repo.save_quote(stored)

    real_find = QuoteRepository._find_instrument_id
    lookups: list[int] = []

    def blind_on_first_call(connection, isin, symbol, ticker=None, mic=None):
        lookups.append(1)
        if len(lookups) == 1:
            return None
        return real_find(connection, isin, symbol, ticker, mic)

    monkeypatch.setattr(
        QuoteRepository, "_find_instrument_id", staticmethod(blind_on_first_call)
    )

    saved = repo.save_quote(
        _quote(129.9, "2026-08-19T11:00:00+00:00", "2026-08-19T11:00:00+00:00")
    )

    assert len(lookups) == 2, "der zweite Blick gehört in den Konfliktzweig"
    assert saved.created is False, "ein verlorenes Rennen ist keine Neuanlage"
    assert repo.get_instrument_by_isin("IE00B3RBWM25")["symbol"] == "VGWL.DE"


def test_genau_ein_paralleler_erstschreiber_legt_an(repo: QuoteRepository) -> None:
    """`#2j2`: `created` kommt aus der schreibenden Transaktion.

    Acht gleichzeitige Erstanlagen desselben Papiers — nur **eine** darf
    `created=True` melden. Ein Existenzcheck *vor* dem Schreiben bestünde
    diesen Test nicht: Alle acht sähen eine leere Tabelle, alle acht meldeten
    Neuanlage, und der Aufnahmeweg antwortete siebenmal `201` für ein Papier,
    das ein anderer gerade angelegt hat.

    Geprüft wird deshalb mit echten Threads und einer Barriere, nicht
    nacheinander — wie schon die Verriegelung des Migrations-Gates.
    """
    parallel = 8
    at_the_line = threading.Barrier(parallel)
    results: list[SavedQuote] = []
    results_lock = threading.Lock()

    def save_it() -> None:
        at_the_line.wait(timeout=10)
        saved = repo.save_quote(
            _quote(128.4, "2026-08-19T10:00:00+00:00", "2026-08-19T10:00:00+00:00")
        )
        with results_lock:
            results.append(saved)

    threads = [threading.Thread(target=save_it) for _ in range(parallel)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)

    assert not any(thread.is_alive() for thread in threads), "ein Thread hängt"
    # **Die Gesamtzahl zuerst.** Eine Ausnahme in einem Thread lässt pytest
    # kalt — der Thread hängt dann schlicht nichts an `results`, und eine
    # Prüfung, die nur `count(True) == 1` fordert, bliebe grün, obwohl die
    # Hälfte der Schreiber abgestürzt ist. Genau das hat die Mutationsprobe
    # an diesem Test gezeigt.
    assert len(results) == parallel, f"{len(results)} von {parallel} Schreibern zurück"
    assert [saved.created for saved in results].count(True) == 1, (
        "genau einer legt an, die übrigen finden die Zeile vor"
    )
    assert len({saved.instrument_id for saved in results}) == 1, (
        "alle acht meinen dasselbe Instrument"
    )

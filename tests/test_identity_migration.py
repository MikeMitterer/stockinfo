"""Tests der Identitäts-Migration aus T-21 — `(ticker, mic)` neben `symbol`.

Der Identifikator eines Papiers war bisher das Yahoo-Symbol. Diese Migration
legt die kanonische Identität daneben: `ticker` und `mic`, dazu eine opake
`listing_id`.

Die Leitregel steht in jedem einzelnen Test: **melden statt raten.** Was sich
nicht sicher zerlegen lässt, bleibt offen und sichtbar — es wird nicht mit
einer plausiblen Vermutung gefüllt.
"""

import sqlite3

import pytest
import structlog

from app.db import init_db


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
                provider TEXT, ter REAL, replication TEXT, fund_size REAL,
                first_seen TEXT NOT NULL, meta_fetched_at TEXT
            );
            """
        )
        connection.executemany(
            "INSERT INTO instruments (symbol, isin, first_seen) VALUES (?, ?, ?)",
            [(symbol, isin, "2026-01-01T00:00:00+00:00") for symbol, isin in rows],
        )


def _instruments(path: str) -> dict[str, sqlite3.Row]:
    """Liest die Instrumentenzeilen, nach Symbol greifbar."""
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        return {
            row["symbol"]: row
            for row in connection.execute("SELECT * FROM instruments")
        }


@pytest.fixture
def migrated(tmp_path) -> str:
    """Eine Alt-Datenbank mit vier bezeichnenden Fällen, einmal migriert."""
    path = str(tmp_path / "alt.db")
    _legacy_database(
        path,
        [
            ("EUNL.DE", "IE00B4L5Y983"),  # Suffix bekannt → zerlegbar
            ("XIC.TO", None),             # dito, ohne ISIN
            ("AAPL", "US0378331005"),     # suffixlos → Sammelcode US, kein echter MIC
            ("BRK-B", "US0846707026"),    # aus dem Yahoo-Fallback, fremde Schreibweise
        ],
    )
    init_db(path)
    init_db(path)  # zweimal: die Migration muss idempotent sein
    return path


def test_die_neuen_spalten_kommen_dazu(migrated: str) -> None:
    """Ohne sie gibt es keine kanonische Identität."""
    with sqlite3.connect(migrated) as connection:
        connection.row_factory = sqlite3.Row
        columns = {
            column["name"]
            for column in connection.execute("PRAGMA table_info(instruments)")
        }

    assert {"ticker", "mic", "listing_id", "identity_status"} <= columns


def test_bekannte_suffixe_werden_zerlegt(migrated: str) -> None:
    """Die Börsentabelle kennt die Zuordnung — hier wird nichts geraten.

    Gemessen am 2026-08-19 über alle 33 Börsen: kein Suffix ist doppelt
    vergeben. Für Symbole aus der eigenen Regel ist die Rückrechnung deshalb
    eindeutig.
    """
    rows = _instruments(migrated)

    assert (rows["EUNL.DE"]["ticker"], rows["EUNL.DE"]["mic"]) == ("EUNL", "XETR")
    assert (rows["XIC.TO"]["ticker"], rows["XIC.TO"]["mic"]) == ("XIC", "XTSE")
    assert rows["EUNL.DE"]["identity_status"] == "resolved"


def test_suffixloses_symbol_wird_nicht_geraten(migrated: str) -> None:
    """`US` ist ein Sammelcode, kein MIC — und `XNYS`/`XNAS` steht nirgends.

    Die Börsentabelle führt `US` als OpenFIGI-Suchcode für NYSE und NASDAQ
    zusammen. Welcher der beiden echten MICs für `AAPL` gilt, weiß erst das
    aufgelöste Listing. Die Migration läuft offline beim Start; sie füllt das
    Feld deshalb **nicht**, sondern markiert den Fall.
    """
    row = _instruments(migrated)["AAPL"]

    assert row["mic"] is None
    assert row["ticker"] is None
    assert row["identity_status"] == "legacy_unresolved"


def test_fremde_schreibweise_wird_nicht_geraten(migrated: str) -> None:
    """`BRK-B` darf nicht per Bindestrich-Regel zu `BRK.B` werden.

    Die Zeichensetzung ist anbieterspezifisch und bedeutet bei anderen Tickern
    etwas anderes. Was der Yahoo-Fallback geliefert hat, folgt der eigenen
    Konvention nicht zwingend — solche Zeilen bleiben offen.
    """
    row = _instruments(migrated)["BRK-B"]

    assert row["ticker"] is None
    assert row["mic"] is None
    assert row["identity_status"] == "legacy_unresolved"


def test_jede_zeile_bekommt_eine_listing_id(migrated: str) -> None:
    """Auch die offenen Fälle — die ID hängt nicht an der Auflösung.

    So steht in T-24: „**jede** Zeile bekommt sofort eine `listing_id` — auch
    eine mit `identity_status = legacy_unresolved`."
    """
    rows = _instruments(migrated)
    listing_ids = [row["listing_id"] for row in rows.values()]

    assert all(listing_ids), "eine Zeile ohne listing_id"
    assert len(set(listing_ids)) == len(listing_ids), "listing_id ist nicht eindeutig"
    assert all(len(value) == 36 for value in listing_ids), "keine UUID-Schreibweise"


def test_die_listing_id_ueberlebt_einen_zweiten_lauf(migrated: str) -> None:
    """Sie ist die Identität für Maschinen — sie darf sich nie ändern."""
    before = {
        symbol: row["listing_id"]
        for symbol, row in _instruments(migrated).items()
    }

    init_db(migrated)

    assert {
        symbol: row["listing_id"]
        for symbol, row in _instruments(migrated).items()
    } == before


def test_die_eindeutigkeit_liegt_auf_ticker_und_mic(migrated: str) -> None:
    """Der globale Index auf `symbol` weicht — er hielt Yahoo in der Identität.

    `symbol` bleibt Pflichtfeld und Anzeigename, ist aber nicht mehr global
    eindeutig: Sobald `US` in `XNYS` und `XNAS` zerfällt, können zwei Listings
    dasselbe Symbol tragen.
    """
    with sqlite3.connect(migrated) as connection:
        connection.row_factory = sqlite3.Row
        indexes = {
            index["name"]: index
            for index in connection.execute("PRAGMA index_list(instruments)")
        }

    assert "idx_instruments_symbol" not in indexes
    assert indexes["idx_instruments_ticker_mic"]["unique"] == 1


def test_offene_faelle_duerfen_mehrfach_leer_sein(migrated: str) -> None:
    """Zwei unaufgelöste Zeilen sind kein Konflikt.

    Läge die Eindeutigkeit naiv auf `(ticker, mic)`, würde die zweite offene
    Zeile den Index verletzen — SQLite behandelt `NULL` in eindeutigen Indizes
    aber als jeweils eigenen Wert. Der Test hält fest, dass wir uns darauf
    verlassen: Ohne diese Eigenschaft könnte die Migration offene Fälle gar
    nicht stehen lassen.
    """
    with sqlite3.connect(migrated) as connection:
        connection.execute(
            "INSERT INTO instruments (symbol, first_seen, identity_status) "
            "VALUES ('NOCH.EIN.FALL', '2026-01-01T00:00:00+00:00', "
            "'legacy_unresolved')"
        )

    assert "NOCH.EIN.FALL" in _instruments(migrated)


def test_ein_echter_konflikt_bleibt_einer(migrated: str) -> None:
    """Dieselbe Identität zweimal muss weiterhin auffallen."""
    with sqlite3.connect(migrated) as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO instruments (symbol, first_seen, ticker, mic) "
            "VALUES ('EUNL.DE', '2026-01-01T00:00:00+00:00', 'EUNL', 'XETR')"
        )


def test_die_offenen_faelle_werden_gemeldet(migrated: str, capsys) -> None:
    """Melden statt raten heißt: Es muss auch jemand davon erfahren.

    Ohne Meldung wäre „später von Hand zuordnen" ein Versprechen, das niemand
    einlösen kann — man wüsste nicht, was offen ist.
    """
    with structlog.testing.capture_logs() as logs:
        init_db(migrated)

    messages = [entry for entry in logs if entry["event"] == "identity_unresolved"]
    assert messages, "kein Hinweis auf die offenen Zuordnungen"
    assert messages[0]["count"] == 2
    assert set(messages[0]["symbols"]) == {"AAPL", "BRK-B"}


def test_zwei_listings_mit_gleichem_symbol_ueberleben_den_neustart(tmp_path) -> None:
    """Der Fall, den die neue Eindeutigkeit gerade erst erlaubt hat.

    Sobald `US` in `XNYS` und `XNAS` zerfällt, tragen zwei **verschiedene**
    Listings dasselbe Symbol. Die Alt-Bereinigung gruppierte weiter nach
    `symbol` und löschte alles bis auf eine Zeile — sie hätte beim nächsten
    Start genau das zerstört, wofür der Index umgezogen ist.

    Geprüft wird alles, was daran hängt: beide Zeilen, ihre `listing_id` und
    ihre Kurspunkte.
    """
    path = str(tmp_path / "zwei-listings.db")
    _legacy_database(path, [("EUNL.DE", "IE00B4L5Y983")])
    init_db(path)

    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            INSERT INTO instruments (symbol, first_seen, ticker, mic, listing_id,
                                     identity_status)
            VALUES ('ABC', '2026-01-01T00:00:00+00:00', 'ABC', 'XNAS',
                    'aaaaaaaa-0000-4000-8000-000000000001', 'resolved'),
                   ('ABC', '2026-01-01T00:00:00+00:00', 'ABC', 'XNYS',
                    'aaaaaaaa-0000-4000-8000-000000000002', 'resolved');
            INSERT INTO quotes (instrument_id, price, quote_time, fetched_at)
            SELECT id, 1.0, '2026-08-01T00:00:00+00:00', '2026-08-01T00:00:00+00:00'
            FROM instruments WHERE symbol = 'ABC';
            """
        )

    init_db(path)  # der zweite Start — hier wurde vorher zusammengeführt

    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT mic, listing_id, id FROM instruments WHERE symbol = 'ABC' "
            "ORDER BY mic"
        ).fetchall()
        quote_count = connection.execute(
            "SELECT COUNT(*) AS anzahl FROM quotes WHERE instrument_id IN "
            "(SELECT id FROM instruments WHERE symbol = 'ABC')"
        ).fetchone()

    assert [row["mic"] for row in rows] == ["XNAS", "XNYS"]
    assert [row["listing_id"] for row in rows] == [
        "aaaaaaaa-0000-4000-8000-000000000001",
        "aaaaaaaa-0000-4000-8000-000000000002",
    ]
    assert quote_count["anzahl"] == 2, "abhängige Daten sind verloren gegangen"


def test_echte_altduplikate_werden_weiterhin_zusammengefuehrt(tmp_path) -> None:
    """Die Gegenprobe — der Grund, warum es die Bereinigung überhaupt gibt.

    Vor dem Index konnten durch parallele Erst-Requests zwei Zeilen mit
    demselben Symbol **und** derselben (noch unaufgelösten) Identität
    entstehen. Die gehören weiterhin zusammengeführt; sonst bliebe der Bestand
    doppelt.
    """
    path = str(tmp_path / "altduplikate.db")
    _legacy_database(path, [("EUNL.DE", "IE00B4L5Y983"), ("EUNL.DE", None)])

    init_db(path)

    rows = _instruments(path)
    assert len(rows) == 1
    assert rows["EUNL.DE"]["isin"] == "IE00B4L5Y983"  # die Zeile mit ISIN gewinnt


def test_die_listing_id_ist_eindeutig(migrated: str) -> None:
    """Sie ist der Maschinenschlüssel — zweimal derselbe Wert wäre wertlos.

    Der Vertrag aus T-24 nennt sie „opake UUID, bei Anlage einmal erzeugt".
    Ohne Index in der Datenbank wäre das eine Absichtserklärung: Ein zweiter
    Schreiber könnte denselben Wert eintragen, und ein Konsument, der darüber
    adressiert, bekäme zwei Papiere.
    """
    with sqlite3.connect(migrated) as connection:
        existing = connection.execute(
            "SELECT listing_id FROM instruments LIMIT 1"
        ).fetchone()[0]

    with sqlite3.connect(migrated) as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO instruments (symbol, first_seen, listing_id) "
            "VALUES ('DOPPELT.DE', '2026-01-01T00:00:00+00:00', ?)",
            (existing,),
        )


def test_zwei_offene_zeilen_mit_gleichem_symbol_bleiben_getrennt(tmp_path) -> None:
    """Gleiches Symbol ist bei offenen Zeilen **kein** Identitätsnachweis.

    Meine erste Fassung führte sie zusammen — mit der Begründung, das sei der
    alte Fall aus parallelen Erst-Requests. Das ist genau die Vermutung, die
    diese Migration nicht anstellen darf: Zwei unaufgelöste Zeilen mit
    demselben Symbol können zwei verschiedene Papiere sein, und ihre ISINs
    sagen es hier sogar.

    Zusammengeführt wird nur noch, was **beweisbar** dasselbe ist: gleiche
    aufgelöste `(ticker, mic)`. Alles andere bleibt stehen — der Index
    verlangt es auch nicht mehr, seit die Eindeutigkeit dort liegt.
    """
    path = str(tmp_path / "unresolved.db")
    _legacy_database(path, [("EUNL.DE", "IE00B4L5Y983")])
    init_db(path)

    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            INSERT INTO instruments (symbol, isin, first_seen, listing_id,
                                     identity_status)
            VALUES ('OPEN', 'US1111111111', '2026-01-01T00:00:00+00:00',
                    'bbbbbbbb-0000-4000-8000-000000000001', 'legacy_unresolved'),
                   ('OPEN', 'US2222222222', '2026-01-01T00:00:00+00:00',
                    'bbbbbbbb-0000-4000-8000-000000000002', 'legacy_unresolved');
            """
        )

    init_db(path)  # der nächste Start

    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT isin, listing_id FROM instruments WHERE symbol = 'OPEN' "
            "ORDER BY isin"
        ).fetchall()

    assert [row["isin"] for row in rows] == ["US1111111111", "US2222222222"]
    assert [row["listing_id"] for row in rows] == [
        "bbbbbbbb-0000-4000-8000-000000000001",
        "bbbbbbbb-0000-4000-8000-000000000002",
    ]


def test_ein_widerspruechlicher_status_wird_neu_bewertet(tmp_path) -> None:
    """`resolved` ohne Identität ist kein Zustand, den man konservieren darf.

    Die Migration übersprang bisher jede Zeile mit gesetztem
    `identity_status` — mit gutem Grund, denn eine bestehende Zuordnung darf
    sie nicht überschreiben. Eine Zeile, die `resolved` behauptet und weder
    Ticker noch MIC trägt, ist aber keine Zuordnung, sondern ein Widerspruch;
    sie bliebe sonst für immer stehen.

    Bewertet wird sie deshalb neu — und landet dort, wo sie hingehört: bei den
    offenen Fällen, wenn sich ihr Symbol nicht zerlegen lässt.
    """
    path = str(tmp_path / "widerspruch.db")
    _legacy_database(path, [("EUNL.DE", "IE00B4L5Y983"), ("VTI", "US9229087690")])
    init_db(path)

    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE instruments SET identity_status = 'resolved', "
            "ticker = NULL, mic = NULL WHERE symbol = 'VTI'"
        )

    init_db(path)  # der nächste Start

    row = _instruments(path)["VTI"]
    assert row["identity_status"] == "legacy_unresolved"
    assert (row["ticker"], row["mic"]) == (None, None)


def test_eine_gueltige_zuordnung_bleibt_unangetastet(tmp_path) -> None:
    """Die Gegenprobe — sonst wäre die Neubewertung eine Überschreibung.

    Ein von Hand gesetztes `VTI/XNAS` ist vollständig und trägt keinen
    Sammelcode. Die Migration lässt es in Ruhe, auch wenn sich `symbol` nicht
    zerlegen ließe.
    """
    path = str(tmp_path / "manuell.db")
    _legacy_database(path, [("VTI", "US9229087690")])
    init_db(path)

    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE instruments SET identity_status = 'resolved', "
            "ticker = 'VTI', mic = 'XNAS' WHERE symbol = 'VTI'"
        )

    init_db(path)

    row = _instruments(path)["VTI"]
    assert (row["ticker"], row["mic"]) == ("VTI", "XNAS")
    assert row["identity_status"] == "resolved"


def test_der_sammelcode_ueberlebt_die_migration_nicht(tmp_path) -> None:
    """`US` ist kein MIC — auch nicht, wenn eine Zeile ihn als solchen führt.

    Das Prüf-Script erkannte diesen Zustand, die Migration nicht: Sie sah zwei
    nichtleere Felder und ließ die Zeile in Ruhe. Damit blieb der ausdrücklich
    nichtkanonische Sammelcode dauerhaft als MIC gespeichert — der grüne
    Smoke-Lauf bewies nur, dass er ihn hinterher meldet.

    Vollständig ist eine Identität erst mit einem **echten** MIC. Alles andere
    wird neu bewertet und landet bei den offenen Fällen.
    """
    path = str(tmp_path / "sammelcode.db")
    _legacy_database(path, [("VTI", "US9229087690")])
    init_db(path)

    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE instruments SET identity_status = 'resolved', "
            "ticker = 'VTI', mic = 'US' WHERE symbol = 'VTI'"
        )

    init_db(path)

    row = _instruments(path)["VTI"]
    assert (row["ticker"], row["mic"]) == (None, None)
    assert row["identity_status"] == "legacy_unresolved"


def test_ein_kaputter_status_zerstoert_keine_gueltige_zuordnung(tmp_path) -> None:
    """Entschieden wird nach den **Daten**, nicht nach der Beschriftung.

    Meine erste Fassung behandelte jeden unbekannten Status als „keine
    Identität" und überschrieb die Felder aus dem Legacy-Symbol. Damit ging
    eine fachlich gültige, von Hand gesetzte Zuordnung lautlos verloren — genau
    das, was dieses Ticket verhindern will.

    Eine vollständige Identität bleibt jetzt stehen; korrigiert wird nur die
    Beschriftung, und der kaputte Status wird protokolliert.
    """
    path = str(tmp_path / "kaputter-status.db")
    _legacy_database(path, [("VTI", "US9229087690")])
    init_db(path)

    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE instruments SET identity_status = 'halbfertig', "
            "ticker = 'VTI', mic = 'XNAS' WHERE symbol = 'VTI'"
        )

    with structlog.testing.capture_logs() as logs:
        init_db(path)

    row = _instruments(path)["VTI"]
    assert (row["ticker"], row["mic"]) == ("VTI", "XNAS"), "die Zuordnung ist weg"
    assert row["identity_status"] == "resolved"

    repaired_entries = [
        entry for entry in logs if entry["event"] == "identity_status_repaired"
    ]
    assert repaired_entries, "der kaputte Status wurde stillschweigend geheilt"
    assert repaired_entries[0]["previous"] == "halbfertig"


def test_ein_unsinniger_mic_ueberlebt_die_migration_nicht(tmp_path) -> None:
    """Was nicht einmal wie ein MIC aussieht, ist keine gültige Zuordnung.

    `is_real_mic` ließ jeden der Tabelle unbekannten String durch — auch
    `NOT-A-MIC`. Die Migration hielt solche Zeilen damit für vollständig und
    ließ sie für immer stehen.
    """
    path = str(tmp_path / "unsinn.db")
    _legacy_database(path, [("VTI", "US9229087690")])
    init_db(path)

    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE instruments SET identity_status = 'resolved', "
            "ticker = 'VTI', mic = 'NOT-A-MIC' WHERE symbol = 'VTI'"
        )

    init_db(path)

    row = _instruments(path)["VTI"]
    assert (row["ticker"], row["mic"]) == (None, None)
    assert row["identity_status"] == "legacy_unresolved"

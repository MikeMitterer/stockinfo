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

from app.db import init_db


def _alte_datenbank(pfad: str, zeilen: list[tuple[str, str | None]]) -> None:
    """Legt eine Datenbank im Stand **vor** T-21 an und füllt sie.

    Args:
        pfad: Dateipfad der SQLite-Datenbank.
        zeilen: Paare aus Symbol und ISIN (``None`` erlaubt).
    """
    with sqlite3.connect(pfad) as verbindung:
        verbindung.executescript(
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
        verbindung.executemany(
            "INSERT INTO instruments (symbol, isin, first_seen) VALUES (?, ?, ?)",
            [(symbol, isin, "2026-01-01T00:00:00+00:00") for symbol, isin in zeilen],
        )


def _instrumente(pfad: str) -> dict[str, sqlite3.Row]:
    """Liest die Instrumentenzeilen, nach Symbol greifbar."""
    with sqlite3.connect(pfad) as verbindung:
        verbindung.row_factory = sqlite3.Row
        return {
            row["symbol"]: row
            for row in verbindung.execute("SELECT * FROM instruments")
        }


@pytest.fixture
def migriert(tmp_path) -> str:
    """Eine Alt-Datenbank mit vier bezeichnenden Fällen, einmal migriert."""
    pfad = str(tmp_path / "alt.db")
    _alte_datenbank(
        pfad,
        [
            ("EUNL.DE", "IE00B4L5Y983"),  # Suffix bekannt → zerlegbar
            ("XIC.TO", None),             # dito, ohne ISIN
            ("AAPL", "US0378331005"),     # suffixlos → Sammelcode US, kein echter MIC
            ("BRK-B", "US0846707026"),    # aus dem Yahoo-Fallback, fremde Schreibweise
        ],
    )
    init_db(pfad)
    init_db(pfad)  # zweimal: die Migration muss idempotent sein
    return pfad


def test_die_neuen_spalten_kommen_dazu(migriert: str) -> None:
    """Ohne sie gibt es keine kanonische Identität."""
    with sqlite3.connect(migriert) as verbindung:
        verbindung.row_factory = sqlite3.Row
        spalten = {
            r["name"] for r in verbindung.execute("PRAGMA table_info(instruments)")
        }

    assert {"ticker", "mic", "listing_id", "identity_status"} <= spalten


def test_bekannte_suffixe_werden_zerlegt(migriert: str) -> None:
    """Die Börsentabelle kennt die Zuordnung — hier wird nichts geraten.

    Gemessen am 2026-08-19 über alle 33 Börsen: kein Suffix ist doppelt
    vergeben. Für Symbole aus der eigenen Regel ist die Rückrechnung deshalb
    eindeutig.
    """
    zeilen = _instrumente(migriert)

    assert (zeilen["EUNL.DE"]["ticker"], zeilen["EUNL.DE"]["mic"]) == ("EUNL", "XETR")
    assert (zeilen["XIC.TO"]["ticker"], zeilen["XIC.TO"]["mic"]) == ("XIC", "XTSE")
    assert zeilen["EUNL.DE"]["identity_status"] == "resolved"


def test_suffixloses_symbol_wird_nicht_geraten(migriert: str) -> None:
    """`US` ist ein Sammelcode, kein MIC — und `XNYS`/`XNAS` steht nirgends.

    Die Börsentabelle führt `US` als OpenFIGI-Suchcode für NYSE und NASDAQ
    zusammen. Welcher der beiden echten MICs für `AAPL` gilt, weiß erst das
    aufgelöste Listing. Die Migration läuft offline beim Start; sie füllt das
    Feld deshalb **nicht**, sondern markiert den Fall.
    """
    zeile = _instrumente(migriert)["AAPL"]

    assert zeile["mic"] is None
    assert zeile["ticker"] is None
    assert zeile["identity_status"] == "legacy_unresolved"


def test_fremde_schreibweise_wird_nicht_geraten(migriert: str) -> None:
    """`BRK-B` darf nicht per Bindestrich-Regel zu `BRK.B` werden.

    Die Zeichensetzung ist anbieterspezifisch und bedeutet bei anderen Tickern
    etwas anderes. Was der Yahoo-Fallback geliefert hat, folgt der eigenen
    Konvention nicht zwingend — solche Zeilen bleiben offen.
    """
    zeile = _instrumente(migriert)["BRK-B"]

    assert zeile["ticker"] is None
    assert zeile["mic"] is None
    assert zeile["identity_status"] == "legacy_unresolved"


def test_jede_zeile_bekommt_eine_listing_id(migriert: str) -> None:
    """Auch die offenen Fälle — die ID hängt nicht an der Auflösung.

    So steht in T-24: „**jede** Zeile bekommt sofort eine `listing_id` — auch
    eine mit `identity_status = legacy_unresolved`."
    """
    zeilen = _instrumente(migriert)
    ids = [zeile["listing_id"] for zeile in zeilen.values()]

    assert all(ids), "eine Zeile ohne listing_id"
    assert len(set(ids)) == len(ids), "listing_id ist nicht eindeutig"
    assert all(len(kennung) == 36 for kennung in ids), "keine UUID-Schreibweise"


def test_die_listing_id_ueberlebt_einen_zweiten_lauf(migriert: str) -> None:
    """Sie ist die Identität für Maschinen — sie darf sich nie ändern."""
    vorher = {s: z["listing_id"] for s, z in _instrumente(migriert).items()}

    init_db(migriert)

    assert {s: z["listing_id"] for s, z in _instrumente(migriert).items()} == vorher


def test_die_eindeutigkeit_liegt_auf_ticker_und_mic(migriert: str) -> None:
    """Der globale Index auf `symbol` weicht — er hielt Yahoo in der Identität.

    `symbol` bleibt Pflichtfeld und Anzeigename, ist aber nicht mehr global
    eindeutig: Sobald `US` in `XNYS` und `XNAS` zerfällt, können zwei Listings
    dasselbe Symbol tragen.
    """
    with sqlite3.connect(migriert) as verbindung:
        verbindung.row_factory = sqlite3.Row
        indizes = {
            r["name"]: r
            for r in verbindung.execute("PRAGMA index_list(instruments)")
        }

    assert "idx_instruments_symbol" not in indizes
    assert indizes["idx_instruments_ticker_mic"]["unique"] == 1


def test_offene_faelle_duerfen_mehrfach_leer_sein(migriert: str) -> None:
    """Zwei unaufgelöste Zeilen sind kein Konflikt.

    Läge die Eindeutigkeit naiv auf `(ticker, mic)`, würde die zweite offene
    Zeile den Index verletzen — SQLite behandelt `NULL` in eindeutigen Indizes
    aber als jeweils eigenen Wert. Der Test hält fest, dass wir uns darauf
    verlassen: Ohne diese Eigenschaft könnte die Migration offene Fälle gar
    nicht stehen lassen.
    """
    with sqlite3.connect(migriert) as verbindung:
        verbindung.execute(
            "INSERT INTO instruments (symbol, first_seen, identity_status) "
            "VALUES ('NOCH.EIN.FALL', '2026-01-01T00:00:00+00:00', "
            "'legacy_unresolved')"
        )

    assert "NOCH.EIN.FALL" in _instrumente(migriert)


def test_ein_echter_konflikt_bleibt_einer(migriert: str) -> None:
    """Dieselbe Identität zweimal muss weiterhin auffallen."""
    with sqlite3.connect(migriert) as verbindung, pytest.raises(sqlite3.IntegrityError):
        verbindung.execute(
            "INSERT INTO instruments (symbol, first_seen, ticker, mic) "
            "VALUES ('EUNL.DE', '2026-01-01T00:00:00+00:00', 'EUNL', 'XETR')"
        )


def test_die_offenen_faelle_werden_gemeldet(migriert: str, capsys) -> None:
    """Melden statt raten heißt: Es muss auch jemand davon erfahren.

    Ohne Meldung wäre „später von Hand zuordnen" ein Versprechen, das niemand
    einlösen kann — man wüsste nicht, was offen ist.
    """
    import structlog

    with structlog.testing.capture_logs() as logs:
        init_db(migriert)

    meldungen = [e for e in logs if e["event"] == "identity_unresolved"]
    assert meldungen, "kein Hinweis auf die offenen Zuordnungen"
    assert meldungen[0]["count"] == 2
    assert set(meldungen[0]["symbols"]) == {"AAPL", "BRK-B"}

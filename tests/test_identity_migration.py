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

from app.db import init_db, run_migration
from app.migration import REASON_NO_SUFFIX


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


_STAMP = "2026-08-25T12:00:00+00:00"


def _rejections(path: str) -> dict[str, sqlite3.Row]:
    """Liest die Berichtseinträge, nach Symbol greifbar."""
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        return {
            row["symbol"]: row
            for row in connection.execute("SELECT * FROM migration_rejections")
        }


@pytest.fixture
def migrated(tmp_path) -> str:
    """Eine Alt-Datenbank mit vier bezeichnenden Fällen, einmal umgezogen.

    Der Ablauf ist seit T-21 Teil 3 **zweiphasig**: `init_db` erkennt nur,
    `run_migration` führt aus. Beides zweimal aufzurufen prüft nebenbei die
    Idempotenz — der zweite Lauf findet nichts mehr vor.
    """
    path = str(tmp_path / "alt.db")
    _legacy_database(
        path,
        [
            ("EUNL.DE", "IE00B4L5Y983"),  # Suffix bekannt → zerlegbar
            ("XIC.TO", None),             # dito, ohne ISIN
            ("AAPL", "US0378331005"),     # suffixlos → kein MIC ableitbar
            ("BRK-B", "US0846707026"),    # aus dem Yahoo-Fallback, fremde Schreibweise
        ],
    )
    assert init_db(path) is True
    run_migration(path, rejected_at=_STAMP)
    assert init_db(path) is False
    return path


def test_die_neuen_spalten_kommen_dazu(migrated: str) -> None:
    """Ohne sie gibt es keine kanonische Identität.

    `identity_status` steht bewusst **nicht** mehr dabei: Seit eine halbe
    Identität nirgends mehr weiterleben darf, trüge die Spalte nur noch einen
    einzigen Wert.
    """
    with sqlite3.connect(migrated) as connection:
        connection.row_factory = sqlite3.Row
        columns = {
            column["name"]
            for column in connection.execute("PRAGMA table_info(instruments)")
        }

    assert {"ticker", "mic", "listing_id"} <= columns
    assert "identity_status" not in columns


def test_bekannte_suffixe_werden_zerlegt(migrated: str) -> None:
    """Die Börsentabelle kennt die Zuordnung — hier wird nichts geraten.

    Gemessen am 2026-08-19 über alle 33 Börsen: kein Suffix ist doppelt
    vergeben. Für Symbole aus der eigenen Regel ist die Rückrechnung deshalb
    eindeutig.
    """
    rows = _instruments(migrated)

    assert (rows["EUNL.DE"]["ticker"], rows["EUNL.DE"]["mic"]) == ("EUNL", "XETR")
    assert (rows["XIC.TO"]["ticker"], rows["XIC.TO"]["mic"]) == ("XIC", "XTSE")


def test_suffixloses_symbol_verlaesst_den_bestand(migrated: str) -> None:
    """`AAPL` nennt seinen Handelsplatz nicht — und wird deshalb abgelehnt.

    **Hier stand bis T-21 Teil 3 das Gegenteil.** Die Zeile blieb als offener
    Fall liegen, mit leerem `ticker`, leerem `mic` und der Beschriftung
    `legacy_unresolved`. Seit der Entscheidung nach Runde 16 gibt es diesen
    Zustand nicht mehr: Was sich nicht auflösen lässt, kommt nicht in den
    gültigen Bestand — es wird gemeldet, mit Symbol und Grund.

    Welcher der fünf US-Plätze für `AAPL` gilt, weiß weiterhin erst das
    aufgelöste Listing; geraten wird nach wie vor nicht.
    """
    assert "AAPL" not in _instruments(migrated)

    bericht = _rejections(migrated)["AAPL"]
    assert bericht["reason"] == REASON_NO_SUFFIX
    assert bericht["isin"] == "US0378331005"


def test_fremde_schreibweise_wird_nicht_geraten(migrated: str) -> None:
    """`BRK-B` darf nicht per Bindestrich-Regel zu `BRK.B` werden.

    Die Zeichensetzung ist anbieterspezifisch und bedeutet bei anderen Tickern
    etwas anderes. Was der Yahoo-Fallback geliefert hat, folgt der eigenen
    Konvention nicht zwingend.

    Geraten wird also weiterhin nicht — nur bleibt die Zeile jetzt nicht mehr
    offen liegen, sondern verlässt den Bestand mit einer Begründung.
    """
    assert "BRK-B" not in _instruments(migrated)
    assert _rejections(migrated)["BRK-B"]["reason"] == REASON_NO_SUFFIX


def test_jede_verbliebene_zeile_bekommt_eine_listing_id(migrated: str) -> None:
    """Der Maschinenschlüssel des öffentlichen Vertrags (T-24).

    **Der Zusatz „auch die offenen Fälle" ist entfallen**, weil es sie nicht
    mehr gibt: Was den Bestand verlässt, braucht keinen Schlüssel — es steht
    im Bericht, nicht in der Tabelle.
    """
    rows = _instruments(migrated)
    listing_ids = [row["listing_id"] for row in rows.values()]

    assert sorted(rows) == ["EUNL.DE", "XIC.TO"]
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


def test_eine_zeile_ohne_identitaet_ist_nicht_mehr_einfuegbar(migrated: str) -> None:
    """**Die Umkehrung eines Tests, der genau das Gegenteil festhielt.**

    Hier stand: „Zwei unaufgelöste Zeilen sind kein Konflikt" — SQLite zählt
    `NULL` im eindeutigen Index als eigenen Wert, und die Migration verließ
    sich darauf, um offene Fälle stehen zu lassen.

    Seit der Entscheidung nach Runde 16 gibt es offene Fälle nicht mehr, und
    die Eigenschaft wird nicht mehr gebraucht. An ihre Stelle tritt die
    härtere Zusage: Eine Zeile **ohne** Identität lässt sich gar nicht erst
    einfügen. Das ist `#2b2` im Schema statt in einer Prüfung.
    """
    with sqlite3.connect(migrated) as connection, pytest.raises(
        sqlite3.IntegrityError
    ):
        connection.execute(
            "INSERT INTO instruments (symbol, first_seen) "
            "VALUES ('NOCH.EIN.FALL', '2026-01-01T00:00:00+00:00')"
        )


def test_ein_echter_konflikt_bleibt_einer(migrated: str) -> None:
    """Dieselbe Identität zweimal muss weiterhin auffallen."""
    with sqlite3.connect(migrated) as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO instruments (symbol, first_seen, ticker, mic) "
            "VALUES ('EUNL.DE', '2026-01-01T00:00:00+00:00', 'EUNL', 'XETR')"
        )


def test_die_abgelehnten_faelle_stehen_im_bericht(migrated: str) -> None:
    """Melden statt raten heißt: Es muss auch jemand davon erfahren.

    **Der Adressat hat gewechselt.** Vorher genügte eine Protokollmeldung —
    die Zeile blieb ja lesbar im Bestand, das Log war nur der Hinweis, dass
    jemand nachhelfen sollte. Jetzt verschwindet die Zeile, und damit ist ein
    Logeintrag zu wenig: Der Benutzer bekommt einen **dauerhaften Bericht**,
    den er auch morgen noch abrufen kann.

    Ein Log wäre außerdem der falsche Ort für eine Auskunft, die das UI in DE
    und EN anzeigen muss.
    """
    bericht = _rejections(migrated)

    assert set(bericht) == {"AAPL", "BRK-B"}
    assert all(row["rejected_at"] == _STAMP for row in bericht.values())


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
    run_migration(path, rejected_at=_STAMP)

    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            INSERT INTO instruments (symbol, first_seen, ticker, mic, listing_id)
            VALUES ('ABC', '2026-01-01T00:00:00+00:00', 'ABC', 'XNAS',
                    'aaaaaaaa-0000-4000-8000-000000000001'),
                   ('ABC', '2026-01-01T00:00:00+00:00', 'ABC', 'XNYS',
                    'aaaaaaaa-0000-4000-8000-000000000002');
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
    run_migration(path, rejected_at=_STAMP)

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


def test_zwei_unaufloesbare_zeilen_werden_einzeln_gemeldet(tmp_path) -> None:
    """Gleiches Symbol ist **kein** Identitätsnachweis — auch beim Ablehnen nicht.

    Der Test hieß „zwei offene Zeilen bleiben getrennt" und prüfte, dass die
    Bereinigung sie nicht zusammenführt. Meine erste Fassung tat genau das —
    mit der Begründung, das sei der alte Fall aus parallelen Erst-Requests.
    Das ist die Vermutung, die hier nicht angestellt werden darf: Zwei Zeilen
    mit demselben Symbol können zwei verschiedene Papiere sein, und ihre ISINs
    sagen es hier sogar.

    Offene Zeilen gibt es nicht mehr, die Vermutung aber schon. Sie hat nur
    einen neuen Ort: Werden beide abgelehnt, muss der Bericht **zwei**
    Einträge tragen. Einer wäre die Behauptung, es sei ein Papier gewesen —
    und der Benutzer erführe nie, dass er zwei neu erfassen muss.
    """
    path = str(tmp_path / "unresolved.db")
    _legacy_database(
        path, [("OPEN", "US1111111111"), ("OPEN", "US2222222222")]
    )

    init_db(path)
    run_migration(path, rejected_at=_STAMP)

    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        eintraege = connection.execute(
            "SELECT isin FROM migration_rejections WHERE symbol = 'OPEN' "
            "ORDER BY isin"
        ).fetchall()

    assert [row["isin"] for row in eintraege] == ["US1111111111", "US2222222222"]
    assert _instruments(path) == {}


def _mit_gesetzter_identitaet(
    path: str, symbol: str, ticker: str | None, mic: str | None
) -> None:
    """Setzt eine Zuordnung von Hand — der Zustand *vor* dem Umzug.

    Die Spalten werden eigens angelegt, weil eine Alt-Datenbank sie nicht hat.
    Das ist genau die Lage, in der eine gewachsene Installation steckt: Teil 1
    hat die Felder eingeführt, jemand hat eine Zeile korrigiert, und jetzt
    kommt Teil 3.
    """
    with sqlite3.connect(path) as connection:
        for column in ("ticker", "mic"):
            connection.execute(f"ALTER TABLE instruments ADD COLUMN {column} TEXT")
        connection.execute(
            "UPDATE instruments SET ticker = ?, mic = ? WHERE symbol = ?",
            (ticker, mic, symbol),
        )


def test_eine_gueltige_zuordnung_bleibt_unangetastet(tmp_path) -> None:
    """Handarbeit wird nicht zurückgenommen.

    Ein von Hand gesetztes `VTI/XNAS` ist vollständig und trägt keinen
    Sammelcode. Der Umzug lässt es in Ruhe, obwohl sich `symbol` nicht
    zerlegen ließe — sonst nähme er genau die Arbeit zurück, die jemand
    vorher hineingesteckt hat.
    """
    path = str(tmp_path / "manuell.db")
    _legacy_database(path, [("VTI", "US9229087690")])
    _mit_gesetzter_identitaet(path, "VTI", "VTI", "XNAS")

    init_db(path)
    run_migration(path, rejected_at=_STAMP)

    row = _instruments(path)["VTI"]
    assert (row["ticker"], row["mic"]) == ("VTI", "XNAS")
    assert _rejections(path) == {}


def test_der_sammelcode_ueberlebt_die_migration_nicht(tmp_path) -> None:
    """`US` ist kein MIC — auch nicht, wenn eine Zeile ihn als solchen führt.

    Das Prüf-Script erkannte diesen Zustand, die Migration nicht: Sie sah zwei
    nichtleere Felder und ließ die Zeile in Ruhe. Damit blieb der ausdrücklich
    nichtkanonische Sammelcode dauerhaft als MIC gespeichert — der grüne
    Smoke-Lauf bewies nur, dass er ihn hinterher meldet.

    Vollständig ist eine Identität erst mit einem **echten** MIC. Alles andere
    wird neu bewertet — und `VTI` verlässt dabei den Bestand, weil sich sein
    Symbol nicht zerlegen lässt.
    """
    path = str(tmp_path / "sammelcode.db")
    _legacy_database(path, [("VTI", "US9229087690")])
    _mit_gesetzter_identitaet(path, "VTI", "VTI", "US")

    init_db(path)
    run_migration(path, rejected_at=_STAMP)

    assert "VTI" not in _instruments(path)
    assert _rejections(path)["VTI"]["reason"] == REASON_NO_SUFFIX


# **Zwei Tests sind hier entfallen**, und zwar ersatzlos:
# `test_ein_widerspruechlicher_status_wird_neu_bewertet` und
# `test_ein_kaputter_status_zerstoert_keine_gueltige_zuordnung`. Beide prüften
# den Umgang mit einer **Beschriftung**, die es nicht mehr gibt: Ein `resolved`
# ohne Identität, ein `halbfertig` neben einer gültigen Zuordnung. Ihre Lehre —
# „entschieden wird nach den Daten, nicht nach dem Etikett" — ist mit dem
# Wegfall von `identity_status` strukturell geworden: Es gibt kein Etikett
# mehr, das widersprechen könnte. Ein Test dafür hätte nichts zu prüfen.
#
# Was von ihnen überlebt, steht oben: Eine gültige Zuordnung bleibt
# unangetastet, und eine unvollständige wird neu bewertet.


@pytest.mark.parametrize(
    ("mic", "warum"),
    [
        ("NOT-A-MIC", "sieht nicht einmal wie ein MIC aus"),
        ("XNAS\n", "trägt einen Zeilenumbruch"),
        ("US", "ist ein Sammelcode"),
    ],
    ids=["unsinn", "zeilenumbruch", "sammelcode"],
)
def test_ein_untauglicher_mic_ueberlebt_den_umzug_nicht(
    tmp_path, mic: str, warum: str
) -> None:
    """Was kein echter MIC ist, macht eine Zeile nicht vollständig.

    `is_real_mic` ließ früher jeden der Tabelle unbekannten String durch —
    auch `NOT-A-MIC`. Und `XNAS\\n` kam durch, weil Python `$` auch vor einem
    abschließenden Zeilenumbruch matchen lässt: ein Wert, den der
    Eindeutigkeits-Index sogar von `XNAS` unterscheidet, für jeden Menschen
    aber gleich aussieht.

    Solche Zeilen galten als vollständig und blieben für immer stehen. Jetzt
    werden sie neu bewertet — und `VTI` verlässt dabei den Bestand, weil sich
    sein Symbol nicht zerlegen lässt.
    """
    path = str(tmp_path / "untauglich.db")
    _legacy_database(path, [("VTI", "US9229087690")])
    _mit_gesetzter_identitaet(path, "VTI", "VTI", mic)

    init_db(path)
    run_migration(path, rejected_at=_STAMP)

    assert "VTI" not in _instruments(path), warum
    assert _rejections(path)["VTI"]["reason"] == REASON_NO_SUFFIX

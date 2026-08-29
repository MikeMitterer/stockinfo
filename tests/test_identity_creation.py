"""Ein neu aufgenommenes Papier bringt seine Identität mit (T-21, Teil 2, `#5`).

Das Gegenstück zu `test_identity_migration.py`: Dort wird der **Bestand**
zerlegt, hier entsteht ein **Neuzugang**. Ohne diesen Weg liefe die Migration
gegen einen Zulauf an — jedes zur Laufzeit angelegte Papier wäre wieder ein
offener Fall, und der Start müsste ihn beim nächsten Mal nachziehen.

Geprüft wird hier die **Speicherung**. Dass die Identität auf jedem Weg
überhaupt entsteht, prüft `test_identity_intake_paths.py` über die echte
Kette — dieser Unterschied hat in Runde 2 einen ganzen Aufnahmeweg verdeckt.
"""

from pathlib import Path

import pytest

from app.db import init_db
from app.models import ListedIdentityOut, QuoteResponse
from app.repository import IncompleteIdentityError, QuoteRepository


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    db_path = str(tmp_path / "identity.db")
    init_db(db_path)
    return QuoteRepository(db_path)


def _response(**overrides) -> QuoteResponse:
    """Eine Kurs-Antwort, wie der Quote-Service sie nach der Auflösung baut."""
    defaults = {
        "identity": ListedIdentityOut(
            ticker="VGWL", mic="XETR", isin="IE00B3RBWM25"
        ),
        "symbol": "VGWL.DE",
        "exchange": "Xetra",
        "name": "Vanguard FTSE All-World",
        "type": "etf",
        "currency": "EUR",
        "price": 123.45,
        "quote_time": "2026-08-23T10:00:00+00:00",
        "fetched_at": "2026-08-23T10:00:05+00:00",
    }
    return QuoteResponse(**{**defaults, **overrides})


def _row(repo: QuoteRepository, instrument_id: int) -> dict:
    with repo._connect() as connection:
        row = connection.execute(
            "SELECT ticker, mic, listing_id, symbol FROM instruments WHERE id = ?",
            (instrument_id,),
        ).fetchone()
    return dict(row)


def test_ein_neues_papier_wird_mit_ticker_und_mic_angelegt(repo) -> None:
    """Verify `#5`: `ticker`/`mic` werden gefüllt, `symbol` daraus erzeugt."""
    row = _row(repo, repo.save_quote(_response()).instrument_id)

    assert (row["ticker"], row["mic"]) == ("VGWL", "XETR")


@pytest.mark.parametrize(
    ("ticker", "mic", "symbol"),
    [
        ("VGWL", "XETR", "VGWL.DE"),
        ("GOLD", "XSTU", "GOLD.SG"),
        ("AAPL", "XNAS", "AAPL"),
    ],
    ids=["xetra", "stuttgart", "us_ohne_alias"],
)
def test_das_gespeicherte_symbol_passt_zur_identitaet(
    repo, ticker: str, mic: str, symbol: str
) -> None:
    """Symbol und Identität bleiben beim Speichern beieinander.

    Bis zu dieser Korrektur rief der Test `provider_alias` auf, um sich seine
    Erwartung selbst auszurechnen — dieselbe Funktion, die das Symbol beim
    Auflösen gebildet hatte. Ein Fehler in ihr wäre auf beiden Seiten
    aufgetreten und grün geblieben. Erwartung und Zuordnung stehen jetzt als
    Literale in der Parametrisierung; sie ändern sich nur von Hand.

    Dass die Börsentabelle aus `(ticker, mic)` das richtige Symbol bildet,
    prüft `test_exchange_catalog.py` — ebenfalls gegen ausgeschriebene Werte.
    Hier geht es allein um die **Speicherung**: Sie darf das Symbol weder
    hinter dem Aufrufer neu bilden noch von der Zuordnung trennen.

    Der US-Fall ist der interessante: Ohne Alias bleibt es beim nackten
    Ticker, und genau dort hätte ein Leerstring-Suffix ein `AAPL.` erzeugt.
    """
    row = _row(
        repo,
        repo.save_quote(_response(ticker=ticker, mic=mic, symbol=symbol)).instrument_id,
    )

    assert row["symbol"] == symbol
    assert (row["ticker"], row["mic"]) == (ticker, mic)


def test_jedes_neue_papier_bekommt_eine_eigene_listing_id(repo) -> None:
    """Die `listing_id` entsteht beim Anlegen, nicht erst beim nächsten Start.

    Sie wurde bisher allein in der Migration vergeben. Ein zur Laufzeit
    angelegtes Papier blieb damit ohne — und der eindeutige Index zählt
    `NULL` in SQLite als eigenen Wert, also fiel es nicht einmal auf.
    """
    first = _row(repo, repo.save_quote(_response()).instrument_id)
    second = _row(
        repo,
        repo.save_quote(
            _response(isin="IE00B4L5Y983", symbol="EUNL.DE", ticker="EUNL")
        ).instrument_id,
    )

    assert first["listing_id"]
    assert first["listing_id"] != second["listing_id"]


def test_ein_zweiter_kurs_laesst_die_identitaet_unangetastet(repo) -> None:
    """Die `listing_id` ist die dauerhafte Kennung — sie darf nicht wandern.

    Jeder Kursabruf läuft durch dieselbe Speicherung. Würde sie die Kennung
    neu vergeben, hinge jeder Verweis darauf an einem Zufallswert.
    """
    before = _row(repo, repo.save_quote(_response()).instrument_id)

    after = _row(repo, repo.save_quote(_response(price=130.0)).instrument_id)

    # Ohne die erste Zeile prüfte der Vergleich `None == None` und wäre auch
    # dann grün, wenn die Kennung nie vergeben würde.
    assert before["listing_id"] is not None
    assert after["listing_id"] == before["listing_id"]


def test_ohne_eindeutige_zuordnung_entsteht_gar_keine_zeile(repo) -> None:
    """**Die Umkehr aus T-21 Teil 3** — hier stand „bleibt die Zeile offen".

    Die alte Zusage lautete: Ein Papier ohne Zuordnung wird als **offen**
    angelegt statt mit geratenen Werten gefüllt, und die Liste offener Fälle
    kennt dann nur einen Status. Geraten wird weiterhin nicht — aber die
    offene Zeile ist nicht mehr der ehrlichere Zustand, sondern der, den es
    nicht mehr geben darf.

    Abgelehnt wird mit einem eigenen Fehler statt mit einer
    `NOT NULL`-Verletzung: dieselbe Ablehnung, aber sie sagt, was fehlt.

    **Geprüft wird seit Runde 40 mit einem *vorhandenen*, aber ungültigen
    Wert.** Eine leere Identität lässt sich am Modell nicht mehr ausdrücken —
    `ticker` und `mic` sind seit `core_version 2.0.0` nicht-nullbare
    Pflichtfelder. Der Sammelcode `US` ist der Fall, den es weiterhin gibt:
    Er steht da, ist aber kein Handelsplatz, und `canonical_identity` lehnt
    ihn ab. Die Verteidigung im Repository greift also unverändert — sie
    schützt jetzt gegen falsche statt gegen fehlende Werte.
    """
    with pytest.raises(IncompleteIdentityError):
        repo.save_quote(_response(symbol="VTI", ticker="VTI", mic="US"))

    with repo._connect() as connection:
        count = connection.execute("SELECT COUNT(*) FROM instruments").fetchone()[0]
    assert count == 0


def test_eine_ueberholte_zuordnung_wird_nachgezogen(repo) -> None:
    """Der im Ticket versprochene Nachtrag — hier passiert er.

    **Der Aufbau musste wechseln.** Vorher begann der Test mit einer *offenen*
    Zeile: `AAPL` ohne Handelsplatz, weil die Migration ihn offline nicht
    kennen konnte. Diesen Zustand gibt es nicht mehr. Was es weiterhin gibt,
    ist eine Zuordnung, die **nicht mehr stimmt** — etwa nach einem Wechsel
    der Vorzugsbörse. Auch sie muss der nächste Lauf nachziehen, sonst zeigte
    `symbol` auf den einen und `mic` auf den anderen Handelsplatz.
    """
    instrument_id = repo.save_quote(
        _response(isin="US0378331005", symbol="AAPL", ticker="AAPL", mic="XNYS")
    ).instrument_id

    repo.save_quote(
        _response(isin="US0378331005", symbol="AAPL", ticker="AAPL", mic="XNAS")
    )

    row = _row(repo, instrument_id)
    assert (row["ticker"], row["mic"]) == ("AAPL", "XNAS")


def test_eine_offene_aufloesung_verwirft_keine_bestehende_zuordnung(repo) -> None:
    """Rückwärts gilt es **nicht** — sonst wäre die Zuordnung wieder weg.

    Kommt eine Antwort mit einer Identität, die keine ist, bleibt der
    gespeicherte Stand stehen. Eine bestehende Zuordnung zu leeren ist
    Datenverlust — genau der Fehler, den Teil 1 in Runde 1 gemacht hat.

    **Der ungültige Fall hat seit Runde 40 eine andere Gestalt.** „Keine
    Identität" lässt sich am Modell nicht mehr ausdrücken; was es weiterhin
    gibt, ist ein Wert, der dasteht und trotzdem nichts bezeichnet — der
    Sammelcode `US`. `canonical_identity` lehnt ihn ab, und damit greift
    dieselbe Regel: Was nicht vollständig ist, ersetzt nichts.
    """
    instrument_id = repo.save_quote(_response()).instrument_id

    repo.save_quote(_response(price=130.0, ticker="VGWL", mic="US"))

    assert _row(repo, instrument_id)["ticker"] == "VGWL"
    assert _row(repo, instrument_id)["mic"] == "XETR", "der Sammelcode ersetzt nichts"


def test_ein_wechsel_des_handelsplatzes_wird_protokolliert(repo) -> None:
    """Eine Identität, die sich ändert, darf das nicht still tun.

    Stellt jemand die bevorzugte Börse um, löst dieselbe ISIN auf ein anderes
    Listing auf — `EQQQ.DE` wird zu `EQQQ.MI`. Die Identität muss mitwandern,
    sonst stünde `symbol` auf Mailand und `mic` auf Xetra. Wer sich hinterher
    fragt, warum die Kennung eine andere ist, findet die Antwort im Log.
    """
    import structlog

    instrument_id = repo.save_quote(
        _response(symbol="EQQQ.DE", ticker="EQQQ", mic="XETR")
    ).instrument_id

    with structlog.testing.capture_logs() as logs:
        repo.save_quote(_response(symbol="EQQQ.MI", ticker="EQQQ", mic="XMIL"))

    assert _row(repo, instrument_id)["mic"] == "XMIL"
    changes = [entry for entry in logs if entry["event"] == "identity_changed"]
    assert changes and changes[0]["previous_mic"] == "XETR"


def test_die_identitaet_steht_jetzt_in_der_rest_antwort() -> None:
    """**Der Test kehrt sich mit dem Vertrag um** (T-21 Übergabe 3).

    Bis `core_version 1.0.0` hielt diese Stelle fest, dass `ticker` und `mic`
    am REST-Rand *fehlen*: Sie reisten schon mit, damit die Speicherung sie
    sieht, aber sie auszuliefern wäre eine Zusage gewesen, die der Vertrag
    nicht trug.

    Mit `2.0.0` ist genau das zugesagt, und dieselbe Zeile hält jetzt das
    Gegenteil fest. `listing_id` bleibt draußen — sie entsteht erst beim
    Anlegen der Zeile, eine frisch beschaffte Antwort hat noch keine.
    """
    payload = _response().model_dump()

    assert payload["ticker"] == "VGWL"
    assert payload["mic"] == "XETR"
    assert "listing_id" not in payload

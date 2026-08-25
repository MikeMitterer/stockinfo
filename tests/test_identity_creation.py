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
from app.models import QuoteResponse
from app.repository import IncompleteIdentityError, QuoteRepository


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    db_path = str(tmp_path / "identity.db")
    init_db(db_path)
    return QuoteRepository(db_path)


def _response(**overrides) -> QuoteResponse:
    """Eine Kurs-Antwort, wie der Quote-Service sie nach der Auflösung baut."""
    defaults = {
        "isin": "IE00B3RBWM25",
        "symbol": "VGWL.DE",
        "ticker": "VGWL",
        "mic": "XETR",
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
    row = _row(repo, repo.save_quote(_response()))

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
    row = _row(repo, repo.save_quote(_response(ticker=ticker, mic=mic, symbol=symbol)))

    assert row["symbol"] == symbol
    assert (row["ticker"], row["mic"]) == (ticker, mic)


def test_jedes_neue_papier_bekommt_eine_eigene_listing_id(repo) -> None:
    """Die `listing_id` entsteht beim Anlegen, nicht erst beim nächsten Start.

    Sie wurde bisher allein in der Migration vergeben. Ein zur Laufzeit
    angelegtes Papier blieb damit ohne — und der eindeutige Index zählt
    `NULL` in SQLite als eigenen Wert, also fiel es nicht einmal auf.
    """
    first = _row(repo, repo.save_quote(_response()))
    second = _row(
        repo,
        repo.save_quote(_response(isin="IE00B4L5Y983", symbol="EUNL.DE", ticker="EUNL")),
    )

    assert first["listing_id"]
    assert first["listing_id"] != second["listing_id"]


def test_ein_zweiter_kurs_laesst_die_identitaet_unangetastet(repo) -> None:
    """Die `listing_id` ist die dauerhafte Kennung — sie darf nicht wandern.

    Jeder Kursabruf läuft durch dieselbe Speicherung. Würde sie die Kennung
    neu vergeben, hinge jeder Verweis darauf an einem Zufallswert.
    """
    before = _row(repo, repo.save_quote(_response()))

    after = _row(repo, repo.save_quote(_response(price=130.0)))

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
    """
    with pytest.raises(IncompleteIdentityError):
        repo.save_quote(_response(symbol="BRK-B", ticker=None, mic=None))

    with repo._connect() as connection:
        anzahl = connection.execute("SELECT COUNT(*) FROM instruments").fetchone()[0]
    assert anzahl == 0


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
    )

    repo.save_quote(
        _response(isin="US0378331005", symbol="AAPL", ticker="AAPL", mic="XNAS")
    )

    row = _row(repo, instrument_id)
    assert (row["ticker"], row["mic"]) == ("AAPL", "XNAS")


def test_eine_offene_aufloesung_verwirft_keine_bestehende_zuordnung(repo) -> None:
    """Rückwärts gilt es **nicht** — sonst wäre die Zuordnung wieder weg.

    Kommt eine Antwort ohne Identität (Yahoo hat nur ein Fremdsymbol, oder die
    Auflösung lief über einen Weg, der keine liefert), bleibt der gespeicherte
    Stand stehen. Eine bestehende Zuordnung zu leeren ist Datenverlust — und
    genau der Fehler, den Teil 1 in Runde 1 gemacht hat.
    """
    created = repo.save_quote(_response())

    repo.save_quote(_response(price=130.0, ticker=None, mic=None))

    assert _row(repo, created)["ticker"] == "VGWL"


def test_ein_wechsel_des_handelsplatzes_wird_protokolliert(repo) -> None:
    """Eine Identität, die sich ändert, darf das nicht still tun.

    Stellt jemand die bevorzugte Börse um, löst dieselbe ISIN auf ein anderes
    Listing auf — `EQQQ.DE` wird zu `EQQQ.MI`. Die Identität muss mitwandern,
    sonst stünde `symbol` auf Mailand und `mic` auf Xetra. Wer sich hinterher
    fragt, warum die Kennung eine andere ist, findet die Antwort im Log.
    """
    import structlog

    created = repo.save_quote(_response(symbol="EQQQ.DE", ticker="EQQQ", mic="XETR"))

    with structlog.testing.capture_logs() as logs:
        repo.save_quote(_response(symbol="EQQQ.MI", ticker="EQQQ", mic="XMIL"))

    assert _row(repo, created)["mic"] == "XMIL"
    changes = [entry for entry in logs if entry["event"] == "identity_changed"]
    assert changes and changes[0]["previous_mic"] == "XETR"


def test_die_identitaet_steht_nicht_in_der_rest_antwort() -> None:
    """Noch nicht — der Vertrag ändert sich erst in Teil 3.

    `ticker` und `mic` reisen bereits mit, damit die Speicherung sie sieht.
    Am REST-Rand aufzutauchen hätte den Vertrag aus T-24 gebrochen, ohne dass
    `core_version` erhöht wurde; der Schnappschuss-Test hätte es gemeldet.
    Diese Zeile hält fest, dass das Weglassen Absicht ist.
    """
    payload = _response().model_dump()

    assert "ticker" not in payload
    assert "mic" not in payload

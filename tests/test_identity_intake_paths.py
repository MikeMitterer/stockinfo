"""Jeder Aufnahmeweg erzeugt dieselbe Identität (T-21, Teil 2, Runde 3).

Verify `#5` gilt für **das Aufnehmen eines neuen Papiers** — nicht für einen
bestimmten Weg dorthin. StockInfo hat zwei: über die ISIN (dann löst der
Resolver auf) und über das fertige Symbol (dann nicht). Der zweite ging an der
Identitätsbildung vorbei, und keiner der Tests aus Runde 2 hat es gesehen:

* `tests/test_identity_creation.py` übergibt dem Repository die fertige
  Identität von Hand — das prüft die Speicherung, nicht ihre Herkunft.
* `tests/test_quote_service.py` prüft nur den ISIN-Pfad.

Deshalb läuft hier die **echte Kette**: Router → Cache-Dienst → Quote-Service →
Repository, mit echter SQLite-Datei. Ersetzt sind allein die Außengrenzen, an
denen sonst das Netz hinge — Kursquelle, ETF-Anreicherung, EOD-Historie.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.container import get_cached_quote_service
from app.db import init_db
from app.main import app
from app.providers.base import RawQuote
from app.repository import REASON_IDENTITY_CONFLICT, QuoteRepository
from app.services.quote_cache import CachedQuoteService
from app.services.quote_service import QuoteService
from stockinfo_plugin.types import NotFound
from tests.boundaries import EmptyEtfEnricher, empty_daily_sync

# Die echte ISIN von Apple. Sie steht hier als Konstante, weil sie in diesem
# Modul zwei getrennte Rollen spielt: Sie ist das, was die Kursquelle meldet,
# **und** das, was in der kollidierenden Zeile steht.
_APPLE_ISIN = "US0378331005"


class _QuoteSource:
    """Die Außengrenze zur Kursquelle — hier hinge sonst yfinance am Netz.

    `isin` ist optional, weil beides vorkommt: Zu `VGWL.DE` sagt yfinance
    nichts über die ISIN, zu `AAPL` sehr wohl. Der Unterschied ist keine
    Kosmetik — eine gemeldete ISIN entscheidet in `save_quote`, welche Zeile
    gefunden wird.
    """

    def __init__(self, isin: str | None = None) -> None:
        self._isin = isin

    def fetch_quote(self, symbol: str) -> RawQuote:
        return RawQuote(
            symbol=symbol,
            price=123.45,
            quote_time="2026-08-23T17:00:00+00:00",
            currency="EUR",
            type="etf",
            isin=self._isin,
        )


class _NoResolver:
    """Auf dem Symbol-Weg wird nicht aufgelöst — es gibt keine ISIN zu fragen.

    Genau das ist der Punkt: Die Identität kann hier **nicht** aus einer
    Auflösung kommen. Sie muss aus dem Symbol selbst entstehen, nach derselben
    Regel, mit der die Migration den Bestand zerlegt hat.
    """

    def handles(self, isin: str) -> bool:
        return True

    def resolve_isin(self, isin: str):
        return NotFound()


def _wire_chain(
    db_path: str, source: _QuoteSource
) -> tuple[TestClient, QuoteRepository]:
    """Baut die echte Kette über einer frischen Datei — nur die Quelle wechselt.

    Args:
        db_path: Pfad der frisch angelegten SQLite-Datei.
        source: Die Außengrenze zur Kursquelle.

    Returns:
        Client und Repository derselben Kette.
    """
    init_db(db_path)
    repository = QuoteRepository(db_path)
    service = CachedQuoteService(
        QuoteService(source, EmptyEtfEnricher(), _NoResolver()),
        repository,
        ttl_hours=0,
        daily_sync=empty_daily_sync(repository),
    )

    app.dependency_overrides[get_cached_quote_service] = lambda: service
    return TestClient(app), repository


@pytest.fixture
def client_and_repo(tmp_path: Path) -> Iterator[tuple[TestClient, QuoteRepository]]:
    yield _wire_chain(str(tmp_path / "aufnahme.db"), _QuoteSource())
    app.dependency_overrides.clear()


@pytest.fixture
def client_and_repo_reporting_isin(
    tmp_path: Path,
) -> Iterator[tuple[TestClient, QuoteRepository]]:
    """Dieselbe Kette, aber die Kursquelle nennt die ISIN von Apple."""
    yield _wire_chain(str(tmp_path / "aufnahme.db"), _QuoteSource(isin=_APPLE_ISIN))
    app.dependency_overrides.clear()


def _row(repository: QuoteRepository, symbol: str) -> dict:
    with repository._connect() as connection:
        row = connection.execute(
            "SELECT ticker, mic, listing_id FROM instruments WHERE symbol = ?",
            (symbol,),
        ).fetchone()
    return dict(row) if row else {}


def test_ein_zerlegbares_symbol_wird_zugeordnet(client_and_repo) -> None:
    """Der Befund aus Runde 3: `VGWL.DE` landete als offener Fall.

    Das Symbol ist eindeutig zerlegbar — dieselbe Rechnung, die die Migration
    auf den ganzen Bestand angewendet hat. Dass hier kein Resolver läuft,
    ändert daran nichts: Die Regel hängt am Symbol, nicht am Weg.
    """
    client, repository = client_and_repo

    response = client.get("/quote", params={"symbol": "VGWL.DE"})

    assert response.status_code == 200
    assert _row(repository, "VGWL.DE") | {"listing_id": None} == {
        "ticker": "VGWL",
        "mic": "XETR",
        "listing_id": None,
    }


def test_auch_dieser_weg_vergibt_eine_listing_id(client_and_repo) -> None:
    """Die dauerhafte Kennung darf nicht am Aufnahmeweg hängen."""
    client, repository = client_and_repo

    client.get("/quote", params={"symbol": "VGWL.DE"})

    assert _row(repository, "VGWL.DE")["listing_id"]


@pytest.mark.parametrize(
    ("symbol", "reason"),
    [
        ("AAPL", "nennt keine Börse"),
        ("BRK-B.DE", "trägt Yahoos Schreibweise im Ticker"),
    ],
    ids=["suffixlos", "fremde_schreibweise"],
)
def test_ein_unzuordenbares_symbol_wird_abgelehnt(
    client_and_repo, symbol: str, reason: str
) -> None:
    """**Die Umkehr aus T-21 Teil 3** — hier stand das Gegenteil.

    Der Test hieß „bleibt sichtbar offen" und begründete das so: Auf dem
    ISIN-Weg wähle StockInfo aus mehreren Notierungen eine aus, eine halb
    geratene Identität wäre also eine Entscheidung, die niemand getroffen hat.
    Hier nenne der Aufrufer das Listing dagegen selbst; ihm die Auskunft zu
    verweigern, nähme ihm eine Abfrage weg, die funktioniert.

    **Das Argument hielt nicht.** Genau dieser Weg war die Quelle, die
    dauerhaft offene Zeilen nachlieferte — und `get_quote_for_known` schloss
    sie nie, weil es nicht auflöst, sondern Kurse holt. Der Bestand füllte
    sich also schneller mit halben Identitäten, als eine Migration sie
    aufräumen konnte.

    Geraten wird weiterhin nicht. Neu ist nur, dass das Nichtwissen zu einer
    **Ablehnung** führt statt zu einer Zeile, die es konserviert.
    """
    client, repository = client_and_repo

    response = client.get("/quote", params={"symbol": symbol})

    assert response.status_code == 400, reason
    assert _row(repository, symbol) == {}, "eine halbe Zeile ist entstanden"


def test_die_ablehnung_nennt_beide_auswege(client_and_repo) -> None:
    """Ein `400`, das nur „geht nicht" sagt, ist eine Sackgasse.

    Der Benutzer hat zwei Möglichkeiten, und beide gehören in den Text: das
    Provider-Suffix und den echten MIC. Die ISIN wird als zuverlässigster Weg
    genannt, weil sie ohne Kenntnis der Schreibweise auskommt.
    """
    client, _ = client_and_repo

    detail = client.get("/quote", params={"symbol": "AAPL"}).json()["detail"]

    assert "EUNL.DE" in detail
    assert "EUNL.XETR" in detail
    assert "ISIN" in detail


def test_ein_bekanntes_papier_wird_beim_naechsten_kurs_nachgetragen(
    client_and_repo,
) -> None:
    """Der dritte Weg — und der, über den der Scheduler läuft.

    Ein Papier, das schon in der Datenbank steht, geht nicht mehr durch die
    Aufnahme, sondern durch `get_quote_for_known`. Auch dort entstand die
    Identität bisher nicht: Eine Zeile, die einmal offen war, blieb es bei
    jedem weiteren Kurs — obwohl ihr Symbol längst zerlegbar ist.

    Genau diese Lücke hatte ich in Runde 2 als „Nachtrag passiert nur auf dem
    ISIN-Weg" ins Ticket geschrieben. Sie gehört nicht in eine Fußnote,
    sondern behoben: Die Rechnung ist dieselbe und kostet nichts.

    **Der Aufbau musste wechseln.** Vorher stand hier eine Zeile *ohne*
    Identität — der Zustand, den die alte Migration hinterließ. Den gibt es
    seit T-21 Teil 3 nicht mehr; `NOT NULL` lässt ihn nicht entstehen. Geprüft
    wird deshalb der Fall, den es weiterhin gibt: eine **überholte**
    Zuordnung. Der geprüfte Weg ist derselbe, und die Zusage auch — was
    `get_quote_for_known` über die Identität weiß, trägt es nach.
    """
    client, repository = client_and_repo
    # Eine Zuordnung, die nicht mehr zum Symbol passt: `EUNL.DE` liegt an
    # Xetra, nicht in Mailand. So sieht die Zeile aus, nachdem jemand die
    # Vorzugsbörse umgestellt hat und dasselbe Papier neu aufgelöst wurde.
    with repository._connect() as connection:
        connection.execute(
            "INSERT INTO instruments (isin, symbol, first_seen, listing_id, "
            "ticker, mic) VALUES (?, ?, ?, ?, ?, ?)",
            ("IE00B4L5Y983", "EUNL.DE", "2026-08-01T00:00:00+00:00", "alt-1",
             "EUNL", "XMIL"),
        )

    client.get("/quote", params={"symbol": "EUNL.DE"})

    row = _row(repository, "EUNL.DE")
    assert (row["ticker"], row["mic"]) == ("EUNL", "XETR")
    assert row["listing_id"] == "alt-1", "die dauerhafte Kennung bleibt"


def test_der_resolver_ist_auf_diesem_weg_wirklich_stumm(client_and_repo) -> None:
    """Die Gegenprobe zum Aufbau dieses Tests.

    Liefe hier doch ein Resolver, käme die Identität aus ihm und der Test
    belegte nicht, was er behauptet. `_NoResolver` antwortet auf jede ISIN mit
    `NotFound` — was `VGWL.DE` zugeordnet hat, kann also nur das Symbol sein.
    """
    client, repository = client_and_repo

    client.get("/quote", params={"symbol": "VGWL.DE"})

    assert _row(repository, "VGWL.DE")["ticker"] == "VGWL"
    assert isinstance(_NoResolver().resolve_isin("IE00B3RBWM25"), NotFound)


# ---------------------------------------------------------------------------
# `POST /instruments/intake` — der zugesagte Aufnahmeweg (T-21 Übergabe 3).
#
# Dieselbe Kette, derselbe Aufbau: Nur die Außengrenzen sind ersetzt, keine
# eigene Core-Komponente. Der Endpunkt hängt über `Depends` am selben
# `CachedQuoteService`, den die Vorrichtung oben austauscht — genau deshalb
# belegen diese Zeilen die Verdrahtung und nicht bloß den Service.
# ---------------------------------------------------------------------------


def _intake(client: TestClient, identifier: str):
    """Ein Aufnahmeversuch über den echten Endpunkt."""
    return client.post("/instruments/intake", json={"identifier": identifier})


@pytest.mark.parametrize(
    ("identifier", "expected_symbol"),
    [
        ("EUNL.DE", "EUNL.DE"),
        ("EUNL.XETR", "EUNL.DE"),
    ],
    ids=["provider_suffix", "echter_mic"],
)
def test_beide_eingabeformen_ergeben_dasselbe_listing(
    client_and_repo, identifier: str, expected_symbol: str
) -> None:
    """`#2f`: Mikes Eingabeentscheidung, an der echten Kette geprüft.

    Ein Feld, zwei Formen — und **eine** Identität. Der Alias entsteht dabei
    ausschließlich im Core: Wer `EUNL.XETR` eingibt, bekommt trotzdem das
    Listing, das bei der Kursquelle `EUNL.DE` heißt.

    Beide Zeilen prüfen zusätzlich das gespeicherte `symbol`. Ein Test, der
    nur die Identität vergliche, hätte einen falschen Abrufalias nicht bemerkt
    — genau die Lücke, die in Teil 2 einen eigenen Befund kostete.
    """
    client, repository = client_and_repo

    response = _intake(client, identifier)

    assert response.status_code == 201
    body = response.json()
    assert (body["ticker"], body["mic"]) == ("EUNL", "XETR")
    assert body["symbol"] == expected_symbol
    assert _row(repository, expected_symbol)["ticker"] == "EUNL"


def test_ein_bekanntes_papier_antwortet_mit_200_statt_201(client_and_repo) -> None:
    """`#2i`: „war schon da" darf nicht als Neuanlage erscheinen.

    Beide Erfolgsfälle tragen denselben Rumpf; unterschieden wird allein der
    Status. Die zweite Aufnahme derselben Eingabe ist der Regelfall — jemand
    trägt ein Papier ein, das längst im Bestand steht.
    """
    client, _ = client_and_repo

    first = _intake(client, "EUNL.DE")
    second = _intake(client, "EUNL.DE")

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["listing_id"] == first.json()["listing_id"]


def test_die_zweite_form_findet_dasselbe_papier_wieder(client_and_repo) -> None:
    """Die schärfere Fassung des Falls darüber.

    `EUNL.DE` anlegen und danach `EUNL.XETR` schicken muss **dieselbe** Zeile
    treffen. Liefen die beiden Formen auseinander, entstünde ein zweites
    Listing desselben Papiers — und der Eindeutigkeitsindex auf `(ticker, mic)`
    hielte es nicht auf, weil er dieselbe Identität zweimal gar nicht sähe.
    """
    client, _ = client_and_repo

    created = _intake(client, "EUNL.DE")
    again = _intake(client, "EUNL.XETR")

    assert (created.status_code, again.status_code) == (201, 200)
    assert again.json()["listing_id"] == created.json()["listing_id"]


@pytest.mark.parametrize(
    ("identifier", "code"),
    [
        ("AAPL", "symbol_without_exchange_suffix"),
        ("AAPL.US", "unknown_exchange_suffix"),
        ("FOO.ZZ", "unknown_exchange_suffix"),
        ("BRK-B.XNYS", "non_canonical_ticker"),
    ],
    ids=["suffixlos", "sammelcode", "unbekannter_suffix", "fremde_schreibweise"],
)
def test_eine_unauflösbare_eingabe_wird_mit_kennung_abgelehnt(
    client_and_repo, identifier: str, code: str
) -> None:
    """`#2i`: `400` mit `{code, params}` — und **kein** halber Datensatz.

    Die Kennung ist maschinenlesbar; der Satz dazu steht im Dashboard, in DE
    und EN. Geprüft wird deshalb die Kennung, nicht ein Text — ein Test auf
    Prosa wäre bei der ersten Umformulierung rot, ohne dass sich etwas
    Fachliches geändert hätte.

    `AAPL.US` ist der Fall, den der Sammelcode kostet: `US` ist ein interner
    Suchcode, kein Handelsplatz.
    """
    client, repository = client_and_repo

    response = _intake(client, identifier)

    assert response.status_code == 400
    assert response.json()["code"] == code
    assert response.json()["params"]["identifier"] == identifier
    assert _row(repository, identifier) == {}, "eine halbe Zeile ist entstanden"


def test_eine_aliaslose_boerse_bleibt_die_genannte(client_and_repo) -> None:
    """**Befund 1 aus Runde 39** — auf leerem Bestand.

    `AAPL.XNAS` und `AAPL.XNYS` tragen denselben Abrufalias `AAPL`, weil die
    US-Plätze keinen Suffix führen. Der erste Entwurf bildete genau diesen
    Alias und schlug damit nach — die genannte Börse war weg, und der
    mehrdeutige Symbolweg entschied neu. Auf leerem Bestand endete das in
    einem `500`.

    Geprüft wird deshalb der Wert, den der Benutzer genannt hat: `XNAS`.
    """
    client, repository = client_and_repo

    response = _intake(client, "AAPL.XNAS")

    assert response.status_code == 201
    assert (response.json()["ticker"], response.json()["mic"]) == ("AAPL", "XNAS")
    assert _row(repository, "AAPL")["mic"] == "XNAS"


def test_eine_andere_boerse_desselben_tickers_wird_nicht_verwechselt(
    client_and_repo,
) -> None:
    """**Befund 1 aus Runde 39** — die schärfere Lage.

    Liegt `AAPL/XNYS` bereits im Bestand, fand die alte Fassung über das
    Symbol `AAPL` genau diese Zeile und antwortete mit `200` und `XNYS` — auf
    eine Eingabe, die ausdrücklich `XNAS` nannte. Das ist schlimmer als der
    `500` daneben: Es sieht wie ein Erfolg aus.

    Nachgeschlagen wird jetzt über `(ticker, mic)`, und das Paar ist eindeutig
    indiziert. `AAPL.XNAS` ist damit ein **anderes** Listing.
    """
    client, repository = client_and_repo
    with repository._connect() as connection:
        connection.execute(
            "INSERT INTO instruments (isin, symbol, first_seen, listing_id, "
            "ticker, mic) VALUES (?, ?, ?, ?, ?, ?)",
            (None, "AAPL", "2026-08-01T00:00:00+00:00", "nyse-1", "AAPL", "XNYS"),
        )

    response = _intake(client, "AAPL.XNAS")

    assert response.status_code == 201, "die andere Börse ist ein neues Listing"
    assert response.json()["mic"] == "XNAS"
    assert response.json()["listing_id"] != "nyse-1"

    with repository._connect() as connection:
        mics = [
            row["mic"]
            for row in connection.execute(
                "SELECT mic FROM instruments WHERE ticker = 'AAPL' ORDER BY mic"
            )
        ]
    assert mics == ["XNAS", "XNYS"], "beide Notierungen stehen nebeneinander"


def test_der_zweite_anspruch_auf_dieselbe_identitaet_ist_ein_409(
    client_and_repo_reporting_isin,
) -> None:
    """**Befund 1 aus Runde 43** — der Konflikt trat als `500` aus.

    `IdentityConflictError` entstand seit Runde 40 an der richtigen Stelle,
    wurde aber von niemandem behandelt: weder im `IntakeService` noch im
    Router. Am HTTP-Rand blieb davon `Internal Server Error` übrig — genau das
    `500`, das der Fehler abschaffen sollte.

    Der Aufbau ist der gewachsene Bestand aus dem Docstring des Fehlers:
    `AAPL/XNAS` ohne ISIN, `AAPL/XNYS` mit ihr. Der Aufnahmeweg für
    `AAPL.XNAS` findet die XNAS-Zeile, holt einen Kurs — und die Quelle nennt
    dabei die ISIN. Damit sucht `save_quote` über die ISIN, findet die
    XNYS-Zeile, und deren Aktualisierung kollidiert am `(ticker, mic)`-Index.

    Geprüft wird der **Rumpf**, nicht nur der Status: Ein `409` ohne
    unterscheidbare Kennung wäre von der zugesagten Symbol-Mehrdeutigkeit
    nicht zu trennen, und das Dashboard hätte nichts zu übersetzen.
    """
    client, repository = client_and_repo_reporting_isin
    with repository._connect() as connection:
        connection.executemany(
            "INSERT INTO instruments (isin, symbol, first_seen, listing_id, "
            "ticker, mic) VALUES (?, ?, ?, ?, ?, ?)",
            [
                (None, "AAPL", "2026-08-01T00:00:00+00:00", "nasdaq-1", "AAPL", "XNAS"),
                (
                    _APPLE_ISIN,
                    "AAPL",
                    "2026-08-01T00:00:00+00:00",
                    "nyse-1",
                    "AAPL",
                    "XNYS",
                ),
            ],
        )

    response = _intake(client, "AAPL.XNAS")

    assert response.status_code == 409, response.text
    body = response.json()
    assert set(body) == {"code", "params"}, "der Rumpf ist der Fehler, nicht `detail`"
    assert body["code"] == REASON_IDENTITY_CONFLICT
    assert body["params"] == {
        "ticker": "AAPL",
        "mic": "XNAS",
        "isin": _APPLE_ISIN,
    }, "der übersetzte Satz braucht beide Seiten des Konflikts"


def test_der_konflikt_steht_auch_in_der_veroeffentlichten_form(
    client_and_repo,
) -> None:
    """Ein Fehlerfall, den nur der Code kennt, ist nicht zugesagt.

    Der `409` entsteht zentral in `app/main.py` und damit an keinem Router
    sichtbar. Ohne eine ausdrückliche Zusage in den `responses` stünde er in
    keinem generierten Client — und der Schnappschuss hätte das Fehlen
    bestätigt statt bemerkt.

    Geprüft werden **alle drei** speichernden Vertragsendpunkte: Der Konflikt
    entsteht in `save_quote`, und dorthin führen sie alle. Nur den Aufnahmeweg
    zu prüfen wäre genau die punktuelle Bestätigung, die schon einmal eine
    halbe Regelumsetzung durchgehen ließ.
    """
    client, _ = client_and_repo

    document = client.get("/openapi.json").json()

    for path, method in (
        ("/instruments/intake", "post"),
        ("/quote", "get"),
        ("/quote/{isin}", "get"),
    ):
        responses = document["paths"][path][method]["responses"]
        assert "409" in responses, f"{method.upper()} {path} sagt den Konflikt nicht zu"
        schema = responses["409"]["content"]["application/json"]["schema"]
        assert schema["$ref"].endswith("/ErrorDetail"), (
            f"{method.upper()} {path} sagt den Konflikt ohne typisierten Rumpf zu"
        )


def test_die_ablehnung_kommt_nicht_unter_detail(client_and_repo) -> None:
    """Der Rumpf ist der Fehler — nicht FastAPIs Umschlag.

    `{"detail": {...}}` zwänge jeden Konsumenten, erst auszupacken, was er dann
    doch typisiert erwartet. Das Dashboard liest heute `response.text()` und
    zeigte rohes JSON; genau deshalb steht die Form hier fest.
    """
    client, _ = client_and_repo

    body = _intake(client, "AAPL").json()

    assert set(body) == {"code", "params"}


@pytest.mark.parametrize(
    "identifier", ["", " ", "   "], ids=["leer", "ein_leerzeichen", "leerraum"]
)
def test_eine_leere_eingabe_hat_genau_eine_fehlerform(
    client_and_repo, identifier: str
) -> None:
    """**Befund 4 aus Runde 39** — `""` und `" "` liefen auseinander.

    Ein `min_length=1` am Modell machte die exakt leere Eingabe zum
    Sonderfall: Sie endete in FastAPIs untypisiertem `422`, während ein
    Leerzeichen den zugesagten `400 identifier_empty` bekam. Damit war die
    Kennung ausgerechnet für den häufigeren Fall unerreichbar — ein leeres
    Feld abzuschicken ist normal, ein Leerzeichen hineinzuschreiben nicht.

    Der Fehlervertrag kennt eine Form, und der Service beantwortet die Leere.
    """
    client, _ = client_and_repo

    response = _intake(client, identifier)

    assert response.status_code == 400
    assert response.json()["code"] == "identifier_empty"


def test_eine_tote_quelle_ist_ein_502_mit_kennung(client_and_repo, monkeypatch) -> None:
    """**Befund 4 aus Runde 39** — die vierte Zeile des Erfolgsvertrags.

    Sie war zugesagt, im Snapshot beschrieben und von Codex von Hand
    nachgestellt, aber nicht als Regressionstest eingecheckt. Eine Zusage ohne
    Test hält genau bis zur nächsten Umbauwelle.

    Ausgefallen ist die **Außengrenze**, nicht eine Core-Komponente: Die
    Kursquelle liefert nichts, alles andere läuft echt. Der Aufrufer hat
    nichts falsch gemacht — deshalb `502` und nicht `400`.
    """
    client, _ = client_and_repo
    monkeypatch.setattr(_QuoteSource, "fetch_quote", lambda self, symbol: None)

    response = _intake(client, "EUNL.DE")

    assert response.status_code == 502
    assert response.json()["code"] == "quote_unavailable"
    assert set(response.json()) == {"code", "params"}


def test_der_router_kennt_die_eingabeformen_nicht(client_and_repo) -> None:
    """`#2j`: Die Fachregel liegt im Service, nicht im Transport.

    Die Gegenprobe ist mechanisch: Im Router-Modul darf keine der Grammatiken
    vorkommen — kein Punkt-Zerlegen, kein Katalog, keine ISIN-Form. Fiele die
    Regel dorthin zurück, stünde sie in der Schicht, die HTTP prüft, und das
    Dashboard bekäme über kurz oder lang seine eigene Kopie.
    """
    source = Path("app/routers/instruments.py").read_text(encoding="utf-8")

    for forbidden in ("identity_from_input", "split_symbol", "EXCHANGES", "is_isin"):
        assert forbidden not in source, f"{forbidden} gehört nicht in den Router"

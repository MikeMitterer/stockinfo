"""Tests der HTTP-Ebene via TestClient (Service gemockt, kein Netz, keine DB)."""

import sqlite3
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.container import get_cached_quote_service, get_daily_history_service
from app.main import app
from app.models import DailyPoint, ListedIdentityOut, QuotePoint, QuoteResponse
from app.services.quote_service import InstrumentNotFoundError, QuoteUnavailableError


class FakeDaily:
    """Ersetzt den DailyHistoryService."""

    def get_daily(
        self, *, isin: str | None = None, symbol: str | None = None, period: str = "1m"
    ) -> list[DailyPoint]:
        # Wie bei FakeService steuert das Praefix den Fehlerfall: XX = unbekannt,
        # ZZ = Provider tot. Nur so lassen sich 404 und 502 unterscheiden.
        identifier = isin or symbol or ""
        if identifier.startswith("XX"):
            raise InstrumentNotFoundError(identifier)
        if identifier.startswith("ZZ"):
            raise QuoteUnavailableError(identifier)
        return [
            DailyPoint(date="2026-07-10", close=160.0, currency="EUR"),
            DailyPoint(date="2026-07-13", close=162.0, currency="EUR"),
        ]


class FakeService:
    """Ersetzt den CachedQuoteService; steuert Erfolg/Fehler über Präfixe."""

    def count_instruments(self) -> int:
        """Erfüllt die von `/ready` verwendete Zähloperation.

        Die Zahl ist gleichgültig — die Route wertet nur aus, **ob** der Aufruf
        durchgeht. Der Fake braucht deshalb dieselbe Methode wie der echte
        Dienst, ohne dafür eine Datenbank zu öffnen.
        """
        return 3

    def get_by_isin(self, isin: str) -> QuoteResponse:
        if isin.startswith("XX"):
            raise InstrumentNotFoundError(isin)
        if isin.startswith("ZZ"):
            # Der Text ist der, den `CompositeResolver` zusammensetzt: Er nennt
            # die ausgefallenen Quellen, und genau das muss beim Client ankommen.
            raise QuoteUnavailableError(
                f"{isin}: keine Quelle konnte nachsehen — "
                "openfigi: HTTP 503; yahoo: timeout"
            )
        return QuoteResponse(
            symbol="VGWL.DE",
            name="VGWL.DE Testpapier",
            identity=ListedIdentityOut(ticker="VGWL", mic="XETR", isin=isin),
            currency="EUR",
            price=160.98,
            quote_time="2026-07-12T17:00:00+00:00",
            fetched_at="2026-07-12T17:00:00+00:00",
            type="etf",
            ter=0.19,
            provider="Vanguard",
            cached=True,
        )

    def get_by_symbol(self, symbol: str) -> QuoteResponse:
        if symbol == "NOPE":
            raise QuoteUnavailableError(symbol)
        return QuoteResponse(
            symbol=symbol,
            name="Testpapier",
            identity=ListedIdentityOut(ticker="MC", mic="XPAR", isin=None),
            currency="EUR",
            price=430.0,
            quote_time="2026-07-12T17:00:00+00:00",
            fetched_at="2026-07-12T17:00:00+00:00",
            type="stock",
        )

    def get_history(
        self,
        isin: str,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 100,
    ) -> list[QuotePoint]:
        if isin.startswith("XX"):
            raise InstrumentNotFoundError(isin)
        return [
            QuotePoint(price=160.0, quote_time="t1", fetched_at="t1", currency="EUR"),
            QuotePoint(price=161.0, quote_time="t2", fetched_at="t2", currency="EUR"),
        ]

    def get_history_by_symbol(
        self,
        symbol: str,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 100,
    ) -> list[QuotePoint]:
        return [
            QuotePoint(price=430.0, quote_time="t1", fetched_at="t1", currency="EUR")
        ]


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """TestClient ohne Lifespan (kein Scheduler/DB), Service überschrieben.

    `dependency_overrides` fängt Routen, die den Dienst als FastAPI-Dependency
    deklarieren. `/ready` holt ihn dagegen direkt aus dem Modulnamensraum von
    `app.main`; deshalb überschreibt die Fixture beide Zugriffswege.

    Die Naht gilt für die ganze Testdatei und hält deren DB-freie Zusage auch
    für neue Fälle. Ein Test mit einem eigenen Dienst — der `503`-Fall weiter
    unten — setzt ihn danach und gewinnt.
    """
    app.dependency_overrides[get_cached_quote_service] = FakeService
    app.dependency_overrides[get_daily_history_service] = FakeDaily
    monkeypatch.setattr(main_module, "get_cached_quote_service", FakeService)
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_quote_by_isin(client: TestClient) -> None:
    response = client.get("/quote/IE00B3RBWM25")
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "VGWL.DE"
    assert body["ter"] == 0.19
    assert body["currency"] == "EUR"
    assert body["cached"] is True


def test_quote_by_isin_unbekannt_404(client: TestClient) -> None:
    assert client.get("/quote/XX0000000000").status_code == 404


def test_quote_by_isin_ungueltiges_format_422(client: TestClient) -> None:
    assert client.get("/quote/NOT-AN-ISIN").status_code == 422


def test_quote_by_isin_lowercase_wird_normalisiert(client: TestClient) -> None:
    response = client.get("/quote/ie00b3rbwm25")
    assert response.status_code == 200
    assert response.json()["identity"]["isin"] == "IE00B3RBWM25"


def test_quote_by_isin_kein_kurs_502(client: TestClient) -> None:
    assert client.get("/quote/ZZ0000000000").status_code == 502


def test_quote_by_symbol(client: TestClient) -> None:
    response = client.get("/quote", params={"symbol": "BRYN.DE"})
    assert response.status_code == 200
    assert response.json()["type"] == "stock"


def test_quote_by_symbol_kein_kurs_502(client: TestClient) -> None:
    assert client.get("/quote", params={"symbol": "NOPE"}).status_code == 502


def test_quote_by_symbol_ohne_param_422(client: TestClient) -> None:
    assert client.get("/quote").status_code == 422


def test_history(client: TestClient) -> None:
    response = client.get("/quote/IE00B3RBWM25/history", params={"limit": 5})
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_history_unbekannt_404(client: TestClient) -> None:
    assert client.get("/quote/XX0000000000/history").status_code == 404


def test_history_ungueltiges_limit_422(client: TestClient) -> None:
    assert (
        client.get("/quote/IE00B3RBWM25/history", params={"limit": 0}).status_code
        == 422
    )


def test_history_by_symbol(client: TestClient) -> None:
    response = client.get("/quote/by-symbol/BRYN.DE/history")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_daily_by_isin(client: TestClient) -> None:
    response = client.get("/quote/IE00B3RBWM25/daily", params={"period": "1m"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2 and body[0]["close"] == 160.0


def test_daily_by_symbol(client: TestClient) -> None:
    response = client.get("/quote/by-symbol/BRYN.DE/daily", params={"period": "1y"})
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_daily_ungueltiger_zeitraum_422(client: TestClient) -> None:
    assert (
        client.get("/quote/IE00B3RBWM25/daily", params={"period": "5x"}).status_code
        == 422
    )


def test_readiness_meldet_die_datenbank(client: TestClient) -> None:
    """`/ready` sieht wirklich nach, statt nur zu antworten."""
    response = client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_readiness_meldet_503_wenn_die_datenbank_nicht_erreichbar_ist(
    client: TestClient, monkeypatch
) -> None:
    """Der eigentliche Zweck: eine kaputte Datenbank muss auffallen.

    `/health` antwortete immer mit ``ok`` — ein Container mit verschwundener
    SQLite-Datei galt bis zum ersten echten Request als gesund.

    **Der Docker-Healthcheck hängt seit T-21 Teil 3 nicht mehr hier**, sondern
    an `/operational`: Ein ausstehender Umzug ist kein Fehler, und `/ready`
    sagt in dieser Lage `503`. Diese Route bleibt trotzdem die Antwort auf
    „ist der Fachbetrieb freigegeben?" — der Grund für den Test ändert sich
    dadurch nicht.
    """
    import app.main as main_module

    class _BrokenService:
        def count_instruments(self) -> int:
            raise sqlite3.OperationalError("unable to open database file")

    monkeypatch.setattr(
        main_module, "get_cached_quote_service", lambda: _BrokenService()
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["database"] == "error"


def test_liveness_bleibt_billig(client: TestClient, monkeypatch) -> None:
    """`/health` darf von der Datenbank nicht abhängen.

    Liveness beantwortet **eine** Frage: Läuft der Prozess? Hängt sie an der
    Datenbank, beantwortet sie zwei — und keine davon zuverlässig.

    **Die frühere Begründung ist zurückgenommen.** Hier stand, die Antwort
    entscheide über einen Neustart. Für dieses Deployment stimmt das nicht:
    Ein `unhealthy`-Container wird von der Docker Engine nicht neu gestartet,
    und `--restart unless-stopped` reagiert auf einen beendeten Prozess. Die
    Trennung ist trotzdem richtig, nur nicht aus diesem Grund.
    """
    import app.main as main_module

    def _explodes() -> None:
        raise AssertionError("/health darf die Datenbank nicht anfassen")

    monkeypatch.setattr(main_module, "get_cached_quote_service", _explodes)

    assert client.get("/health").status_code == 200


@pytest.mark.parametrize("malformed", ["../etc/passwd", "A" * 30, "AB CD", "A;B", "."])
def test_unbrauchbare_symbole_werden_abgewiesen(client: TestClient, malformed) -> None:
    """Symbole hatten weder Längen- noch Zeichengrenze.

    Jede Zeichenkette ging damit an den Provider — und wurde bei Erfolg als
    neues Instrument gespeichert. 422 sagt „das war keine Eingabe", 502 hätte
    einen Ausfall bei Yahoo behauptet.
    """
    assert client.get("/quote", params={"symbol": malformed}).status_code == 422


def test_symbole_werden_normalisiert(client: TestClient) -> None:
    """Klein geschrieben ist dasselbe Papier — nicht ein zweites."""
    response = client.get("/quote", params={"symbol": "vgwl.de"})

    assert response.status_code == 200
    assert response.json()["symbol"] == "VGWL.DE"


@pytest.mark.parametrize(
    "invalid_boundary", ["2026-8-1", "01.08.2026", "gestern", "2026-13-01"]
)
def test_unbrauchbare_zeitgrenzen_werden_abgewiesen(
    client: TestClient, invalid_boundary
) -> None:
    """Die Abfrage vergleicht Zeitgrenzen lexikografisch gegen ISO-Zeitstempel.

    Eine andere Schreibweise liefert dann klaglos einen falschen Bereich,
    statt aufzufallen.
    """
    response = client.get(
        "/quote/IE00B3RBWM25/history", params={"from": invalid_boundary}
    )

    assert response.status_code == 422


def test_verdrehtes_zeitfenster_wird_abgewiesen(client: TestClient) -> None:
    """`from` nach `to` ist keine leere Antwort, sondern ein Eingabefehler."""
    response = client.get(
        "/quote/IE00B3RBWM25/history",
        params={"from": "2026-08-01T00:00:00+00:00", "to": "2026-01-01T00:00:00+00:00"},
    )

    assert response.status_code == 422


def test_gueltiges_zeitfenster_kommt_durch(client: TestClient) -> None:
    """Die Gegenrichtung — sonst wäre die Prüfung ein stiller Totalausfall."""
    response = client.get(
        "/quote/IE00B3RBWM25/history",
        params={"from": "2026-01-01", "to": "2026-12-31T23:59:59+00:00"},
    )

    assert response.status_code == 200


def test_unbekanntes_papier_ist_kein_providerausfall(client: TestClient) -> None:
    """Die Daily-Route warf beides als 502 — Eingabefehler wie Upstream-Ausfall.

    Ein Client konnte damit nicht unterscheiden, ob er die Anfrage korrigieren
    oder es später erneut versuchen soll. Die normale Quote-Route trennt beides
    seit jeher; die Daily-Route zieht nach.
    """
    assert client.get("/quote/XX0000000000/daily").status_code == 404
    assert client.get("/quote/ZZ0000000000/daily").status_code == 502


def test_unbekanntes_symbol_bleibt_ein_502(client: TestClient) -> None:
    """Auf dem Symbol-Pfad ist 404 nicht zu haben — und das ist kein Versehen.

    Eine ISIN wird aufgeloest; scheitert das, ist das Papier nachweislich
    unbekannt (404). Ein freies Symbol geht direkt an den Provider, und der
    liefert `None`, ob er es nicht kennt oder gerade nicht antwortet. Ein 404
    waere hier geraten.

    Der Test stand zuerst andersherum da und war gruen, weil das Double
    `InstrumentNotFoundError` warf — gegen die echte API kam 502. Gefunden
    wurde das erst beim Ausfuehren der Verify-Commands aus T-15.
    """
    assert client.get("/quote/by-symbol/ZZTEST/daily").status_code == 502


def test_ausgefallene_quellen_nennen_sich_im_antwortkoerper(
    client: TestClient,
) -> None:
    """T-20 `#3`: Der 502 soll sagen, wer nicht erreichbar war.

    Ohne die Namen steht dort nur „ging nicht" — und wer die App betreibt,
    weiß nicht, ob er auf OpenFIGI, Yahoo oder sein eigenes Netz schauen soll.
    """
    response = client.get("/quote/ZZ0000000000")

    assert response.status_code == 502
    # **Seit T-31 als `{code, params}`.** Die Anleihe braucht den
    # `quote_unavailable`-Zustand strukturiert — sie ist der Normalfall ohne
    # Kursquelle, keine Störung —, und zwei Rumpfformen an einem Endpunkt
    # wären schlimmer als der alte Freitext. Die Namen reisen als Diagnose in
    # `params.detail` mit; die geprüfte Aussage bleibt Wort für Wort dieselbe.
    body = response.json()
    assert body["code"] == "quote_unavailable"
    detail = body["params"]["detail"]
    assert "ZZ0000000000" in detail
    assert "openfigi" in detail and "yahoo" in detail

"""Tests der HTTP-Ebene via TestClient (Service gemockt, kein Netz, keine DB)."""

import sqlite3
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.container import get_cached_quote_service, get_daily_history_service
from app.main import app
from app.models import DailyPoint, QuotePoint, QuoteResponse
from app.services.quote_service import InstrumentNotFoundError, QuoteUnavailableError


class FakeDaily:
    """Ersetzt den DailyHistoryService."""

    def get_daily(
        self, *, isin: str | None = None, symbol: str | None = None, period: str = "1m"
    ) -> list[DailyPoint]:
        # Wie bei FakeService steuert das Praefix den Fehlerfall: XX = unbekannt,
        # ZZ = Provider tot. Nur so lassen sich 404 und 502 unterscheiden.
        kennung = isin or symbol or ""
        if kennung.startswith("XX"):
            raise InstrumentNotFoundError(kennung)
        if kennung.startswith("ZZ"):
            raise QuoteUnavailableError(kennung)
        return [
            DailyPoint(date="2026-07-10", close=160.0, currency="EUR"),
            DailyPoint(date="2026-07-13", close=162.0, currency="EUR"),
        ]


class FakeService:
    """Ersetzt den CachedQuoteService; steuert Erfolg/Fehler über Präfixe."""

    def get_by_isin(self, isin: str) -> QuoteResponse:
        if isin.startswith("XX"):
            raise InstrumentNotFoundError(isin)
        if isin.startswith("ZZ"):
            raise QuoteUnavailableError(isin)
        return QuoteResponse(
            isin=isin,
            symbol="VGWL.DE",
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
            isin=None,
            symbol=symbol,
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
            QuotePoint(price=160.0, quote_time="t1", fetched_at="t1"),
            QuotePoint(price=161.0, quote_time="t2", fetched_at="t2"),
        ]

    def get_history_by_symbol(
        self,
        symbol: str,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 100,
    ) -> list[QuotePoint]:
        return [QuotePoint(price=430.0, quote_time="t1", fetched_at="t1")]


@pytest.fixture
def client() -> Iterator[TestClient]:
    """TestClient ohne Lifespan (kein Scheduler/DB), Service überschrieben."""
    app.dependency_overrides[get_cached_quote_service] = FakeService
    app.dependency_overrides[get_daily_history_service] = FakeDaily
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
    assert response.json()["isin"] == "IE00B3RBWM25"


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
    assert client.get("/quote/IE00B3RBWM25/daily", params={"period": "5x"}).status_code == 422


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
    SQLite-Datei galt bis zum ersten echten Request als gesund. Der
    Docker-Healthcheck hängt daran.
    """
    import app.main as main_module

    class _KaputterDienst:
        def count_instruments(self) -> int:
            raise sqlite3.OperationalError("unable to open database file")

    monkeypatch.setattr(main_module, "get_cached_quote_service", lambda: _KaputterDienst())

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["database"] == "error"


def test_liveness_bleibt_billig(client: TestClient, monkeypatch) -> None:
    """`/health` darf von der Datenbank nicht abhängen.

    Die Antwort entscheidet über einen Neustart — und ein Neustart repariert
    keine kaputte Datenbank. Wer beides vermischt, bekommt eine Neustartschleife.
    """
    import app.main as main_module

    def _explodiert() -> None:
        raise AssertionError("/health darf die Datenbank nicht anfassen")

    monkeypatch.setattr(main_module, "get_cached_quote_service", _explodiert)

    assert client.get("/health").status_code == 200


@pytest.mark.parametrize("unfug", ["../etc/passwd", "A" * 30, "AB CD", "A;B", "."])
def test_unbrauchbare_symbole_werden_abgewiesen(client: TestClient, unfug) -> None:
    """Symbole hatten weder Längen- noch Zeichengrenze.

    Jede Zeichenkette ging damit an den Provider — und wurde bei Erfolg als
    neues Instrument gespeichert. 422 sagt „das war keine Eingabe", 502 hätte
    einen Ausfall bei Yahoo behauptet.
    """
    assert client.get("/quote", params={"symbol": unfug}).status_code == 422


def test_symbole_werden_normalisiert(client: TestClient) -> None:
    """Klein geschrieben ist dasselbe Papier — nicht ein zweites."""
    response = client.get("/quote", params={"symbol": "vgwl.de"})

    assert response.status_code == 200
    assert response.json()["symbol"] == "VGWL.DE"


@pytest.mark.parametrize("kaputt", ["2026-8-1", "01.08.2026", "gestern", "2026-13-01"])
def test_unbrauchbare_zeitgrenzen_werden_abgewiesen(client: TestClient, kaputt) -> None:
    """Die Abfrage vergleicht Zeitgrenzen lexikografisch gegen ISO-Zeitstempel.

    Eine andere Schreibweise liefert dann klaglos einen falschen Bereich,
    statt aufzufallen.
    """
    response = client.get("/quote/IE00B3RBWM25/history", params={"from": kaputt})

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


def test_unbekanntes_symbol_in_der_daily_route_ist_ein_404(client: TestClient) -> None:
    assert client.get("/quote/by-symbol/XXTEST/daily").status_code == 404
    assert client.get("/quote/by-symbol/ZZTEST/daily").status_code == 502

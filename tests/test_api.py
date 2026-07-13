"""Tests der HTTP-Ebene via TestClient (Service gemockt, kein Netz, keine DB)."""

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

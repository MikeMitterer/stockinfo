from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.container import get_cached_quote_service
from app.main import app
from app.models import QuoteResponse
from app.services.quote_cache import IsinConflictError
from app.services.quote_service import InstrumentNotFoundError


class FakeService:
    def list_instruments(self) -> list[dict]:
        return [{"symbol": "VGWL.DE", "isin": "IE00B3RBWM25", "history_count": 2,
                 "latest_price": 161.0}]

    def count_instruments(self) -> int:
        return 1

    def refresh_all(self) -> int:
        return 3

    def refresh_one(self, isin: str) -> QuoteResponse:
        if isin.startswith("XX"):
            raise InstrumentNotFoundError(isin)
        return QuoteResponse(isin=isin, symbol="VGWL.DE", currency="EUR",
                             price=161.0, quote_time="t", fetched_at="t", type="etf")

    def refresh_one_by_symbol(self, symbol: str) -> QuoteResponse:
        return QuoteResponse(isin=None, symbol=symbol, currency="EUR",
                             price=430.0, quote_time="t", fetched_at="t", type="stock")

    def delete_instrument(self, isin: str) -> bool:
        return not isin.startswith("XX")

    def delete_by_symbol(self, symbol: str) -> bool:
        return not symbol.startswith("XX")

    def set_isin(self, symbol: str, isin: str) -> None:
        if symbol.startswith("XX"):
            raise InstrumentNotFoundError(symbol)
        if isin == "IE00B4L5Y983":
            raise IsinConflictError(isin)


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_cached_quote_service] = FakeService
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_instruments(client: TestClient) -> None:
    r = client.get("/instruments")
    assert r.status_code == 200
    assert r.json()[0]["symbol"] == "VGWL.DE"


def test_env(client: TestClient) -> None:
    r = client.get("/env")
    assert r.status_code == 200
    body = r.json()
    assert body["default_exchange"] == "XETR"
    assert "openfigi_key_set" in body and "version" in body


def test_refresh_global(client: TestClient) -> None:
    r = client.post("/refresh")
    assert r.status_code == 200
    assert r.json()["refreshed"] == 3


def test_refresh_one_und_404(client: TestClient) -> None:
    assert client.post("/refresh/IE00B3RBWM25").status_code == 200
    assert client.post("/refresh/XX0000000000").status_code == 404


def test_delete(client: TestClient) -> None:
    assert client.delete("/instruments/IE00B3RBWM25").status_code == 204
    assert client.delete("/instruments/XX0000000000").status_code == 404


def test_refresh_by_symbol(client: TestClient) -> None:
    response = client.post("/refresh/by-symbol/BRYN.DE")
    assert response.status_code == 200
    assert response.json()["symbol"] == "BRYN.DE"


def test_delete_by_symbol(client: TestClient) -> None:
    assert client.delete("/instruments/by-symbol/BRYN.DE").status_code == 204
    assert client.delete("/instruments/by-symbol/XXNOPE").status_code == 404


def test_set_isin_ok(client: TestClient) -> None:
    r = client.put("/instruments/by-symbol/BRYN.DE/isin", json={"isin": "US0846707026"})
    assert r.status_code == 200
    assert r.json()["isin"] == "US0846707026"


def test_set_isin_normalisiert_und_validiert(client: TestClient) -> None:
    # klein + Leerzeichen → wird normalisiert
    r = client.put("/instruments/by-symbol/BRYN.DE/isin", json={"isin": " us0846707026 "})
    assert r.status_code == 200 and r.json()["isin"] == "US0846707026"
    # ungültiges Format → 422
    assert client.put("/instruments/by-symbol/BRYN.DE/isin", json={"isin": "nope"}).status_code == 422


def test_set_isin_unbekannt_404(client: TestClient) -> None:
    r = client.put("/instruments/by-symbol/XXNOPE/isin", json={"isin": "US0846707026"})
    assert r.status_code == 404


def test_set_isin_konflikt_409(client: TestClient) -> None:
    r = client.put("/instruments/by-symbol/BRYN.DE/isin", json={"isin": "IE00B4L5Y983"})
    assert r.status_code == 409

"""Tests des /fx-Endpoints."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.container import get_fx_service
from app.main import app
from app.models import FxRate


class _StubFx:
    def get_rate(self, base: str, quote: str) -> FxRate:
        return FxRate(
            base=base.upper(), quote=quote.upper(), rate=1.15,
            quote_time="t", source="yfinance", cached=False, stale=False, fetched_at="t",
        )


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_fx_service] = lambda: _StubFx()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_fx_liefert_rate(client: TestClient) -> None:
    body = client.get("/fx?base=EUR&quote=USD").json()
    assert body["rate"] == 1.15
    assert body["base"] == "EUR" and body["quote"] == "USD"


def test_fx_validiert_codes(client: TestClient) -> None:
    assert client.get("/fx?base=EU&quote=USD").status_code == 422
    assert client.get("/fx?base=EURO&quote=USD").status_code == 422
    assert client.get("/fx").status_code == 422  # fehlende Parameter

from pathlib import Path

import pytest

from app.db import init_db
from app.models import QuoteResponse
from app.repository import QuoteRepository
from app.services.quote_cache import CachedQuoteService


class FakeQuoteService:
    def __init__(self) -> None:
        self.calls = 0

    def get_quote_by_isin(self, isin: str) -> QuoteResponse:
        self.calls += 1
        return QuoteResponse(
            isin=isin, symbol="VGWL.DE", currency="EUR", price=200.0,
            quote_time="2026-07-12T20:00:00+00:00",
            fetched_at="2026-07-12T20:00:00+00:00", type="etf",
        )

    def get_quote_by_symbol(self, symbol: str) -> QuoteResponse:  # pragma: no cover
        return self.get_quote_by_isin(symbol)


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    db_path = str(tmp_path / "svc.db")
    init_db(db_path)
    return QuoteRepository(db_path)


def test_refresh_one_forciert_und_speichert(repo: QuoteRepository) -> None:
    fake = FakeQuoteService()
    service = CachedQuoteService(fake, repo, ttl_hours=6)

    result = service.refresh_one("IE00B3RBWM25")

    assert fake.calls == 1
    assert result.price == 200.0
    assert repo.get_instrument_by_isin("IE00B3RBWM25") is not None


def test_list_und_delete(repo: QuoteRepository) -> None:
    service = CachedQuoteService(FakeQuoteService(), repo, ttl_hours=6)
    service.refresh_one("IE00B3RBWM25")

    listed = service.list_instruments()
    assert len(listed) == 1 and listed[0]["symbol"] == "VGWL.DE"
    assert service.delete_instrument("IE00B3RBWM25") is True
    assert service.list_instruments() == []


def test_refresh_one_by_symbol(repo: QuoteRepository) -> None:
    service = CachedQuoteService(FakeQuoteService(), repo, ttl_hours=6)

    result = service.refresh_one_by_symbol("BRYN.DE")

    assert result.price == 200.0
    assert len(service.list_instruments()) == 1


def test_delete_by_symbol_service(repo: QuoteRepository) -> None:
    service = CachedQuoteService(FakeQuoteService(), repo, ttl_hours=6)
    service.refresh_one_by_symbol("BRYN.DE")
    saved = service.list_instruments()[0]

    assert service.delete_by_symbol(saved["symbol"]) is True
    assert service.list_instruments() == []


def test_get_history_by_symbol(repo: QuoteRepository) -> None:
    service = CachedQuoteService(FakeQuoteService(), repo, ttl_hours=6)
    service.refresh_one_by_symbol("BRYN.DE")
    saved = service.list_instruments()[0]

    history = service.get_history_by_symbol(saved["symbol"])
    assert len(history) >= 1

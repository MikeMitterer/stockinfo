"""Tests für die Cache-/TTL-Logik (echte temp-DB, gemockter QuoteService)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.db import init_db
from app.models import QuoteResponse
from app.repository import QuoteRepository
from app.services.quote_cache import CachedQuoteService
from app.services.quote_service import QuoteUnavailableError


class FakeQuoteService:
    """Zählt Aufrufe und liefert eine vorgegebene Antwort (oder wirft)."""

    def __init__(self, response: QuoteResponse | None, raises: bool = False) -> None:
        self._response = response
        self._raises = raises
        self.calls = 0

    def get_quote_by_isin(self, isin: str) -> QuoteResponse:
        self.calls += 1
        if self._raises:
            raise QuoteUnavailableError(isin)
        return self._response

    def get_quote_by_symbol(self, symbol: str) -> QuoteResponse:
        return self.get_quote_by_isin(symbol)


def _response(fetched_at: str, price: float = 160.98) -> QuoteResponse:
    return QuoteResponse(
        isin="IE00B3RBWM25",
        symbol="VGWL.DE",
        currency="EUR",
        price=price,
        quote_time=fetched_at,
        fetched_at=fetched_at,
        type="etf",
    )


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    db_path = str(tmp_path / "cache.db")
    init_db(db_path)
    return QuoteRepository(db_path)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hours_ago(hours: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def test_cache_miss_beschafft_und_speichert(repo: QuoteRepository) -> None:
    fake = FakeQuoteService(_response(_now()))
    service = CachedQuoteService(fake, repo, ttl_hours=6)

    result = service.get_by_isin("IE00B3RBWM25")

    assert fake.calls == 1
    assert result.cached is False
    assert repo.get_instrument_by_isin("IE00B3RBWM25") is not None


def test_frischer_cache_vermeidet_zweiten_fetch(repo: QuoteRepository) -> None:
    fake = FakeQuoteService(_response(_now()))
    service = CachedQuoteService(fake, repo, ttl_hours=6)

    service.get_by_isin("IE00B3RBWM25")  # füllt Cache
    result = service.get_by_isin("IE00B3RBWM25")  # Cache-Hit

    assert fake.calls == 1  # kein zweiter Live-Fetch
    assert result.cached is True
    assert result.stale is False


def test_abgelaufener_cache_beschafft_neu(repo: QuoteRepository) -> None:
    repo.save_quote(_response(_hours_ago(10)))  # alter Kurs
    fake = FakeQuoteService(_response(_now(), price=200.0))
    service = CachedQuoteService(fake, repo, ttl_hours=6)

    result = service.get_by_isin("IE00B3RBWM25")

    assert fake.calls == 1
    assert result.cached is False
    assert result.price == 200.0


def test_stale_bei_fehler_und_vorhandenem_cache(repo: QuoteRepository) -> None:
    repo.save_quote(_response(_hours_ago(10), price=155.0))  # alter Kurs
    fake = FakeQuoteService(None, raises=True)  # Live-Beschaffung schlägt fehl
    service = CachedQuoteService(fake, repo, ttl_hours=6)

    result = service.get_by_isin("IE00B3RBWM25")

    assert result.stale is True
    assert result.cached is True
    assert result.price == 155.0


def test_fehler_ohne_cache_propagiert(repo: QuoteRepository) -> None:
    fake = FakeQuoteService(None, raises=True)
    service = CachedQuoteService(fake, repo, ttl_hours=6)

    with pytest.raises(QuoteUnavailableError):
        service.get_by_isin("IE00B3RBWM25")

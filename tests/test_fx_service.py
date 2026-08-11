"""Tests für den cachenden FX-Service."""

from pathlib import Path

import pytest

from app.db import init_db
from app.repository import QuoteRepository
from app.services.fx_service import CachedFxService, FxUnavailableError


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    db_path = str(tmp_path / "fx.db")
    init_db(db_path)
    return QuoteRepository(db_path)


class _FakeFx:
    def __init__(self, rate: float | None) -> None:
        self.rate = rate
        self.calls = 0

    def fetch_fx_rate(self, base: str, quote: str) -> float | None:
        self.calls += 1
        return self.rate


def test_gleiche_waehrung_ist_eins_ohne_fetch(repo: QuoteRepository) -> None:
    provider = _FakeFx(None)
    service = CachedFxService(provider, repo, ttl_hours=1)
    result = service.get_rate("EUR", "EUR")
    assert result.rate == 1.0
    assert result.source == "identity"
    assert provider.calls == 0


def test_miss_holt_live_und_speichert(repo: QuoteRepository) -> None:
    provider = _FakeFx(1.15)
    service = CachedFxService(provider, repo, ttl_hours=1)
    result = service.get_rate("eur", "usd")  # wird normalisiert
    assert result.base == "EUR" and result.quote == "USD"
    assert result.rate == 1.15 and result.cached is False
    # zweiter Aufruf → Cache, kein weiterer Fetch
    provider.rate = 999.0
    again = service.get_rate("EUR", "USD")
    assert again.rate == 1.15 and again.cached is True and provider.calls == 1


def test_fetch_fehler_mit_cache_liefert_stale(repo: QuoteRepository) -> None:
    repo.save_fx_rate("EUR", "USD", 1.10, "2020-01-01T00:00:00+00:00",
                      "2020-01-01T00:00:00+00:00")  # uralt → nicht frisch
    provider = _FakeFx(None)  # Fetch schlägt fehl
    service = CachedFxService(provider, repo, ttl_hours=1)
    result = service.get_rate("EUR", "USD")
    assert result.rate == 1.10 and result.stale is True


def test_fetch_fehler_ohne_cache_wirft(repo: QuoteRepository) -> None:
    service = CachedFxService(_FakeFx(None), repo, ttl_hours=1)
    with pytest.raises(FxUnavailableError):
        service.get_rate("EUR", "USD")

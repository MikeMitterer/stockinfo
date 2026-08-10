"""Tests für die Cache-/TTL-Logik (echte temp-DB, gemockter QuoteService)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.db import init_db
from app.models import QuoteResponse
from app.repository import QuoteRepository
from app.services.daily_sync import DailyCloseSync
from app.services.quote_cache import CachedQuoteService, RefreshInProgressError
from app.services.quote_service import (
    InstrumentNotFoundError,
    QuoteUnavailableError,
    annualized_volatility,
)


class _EmptyDailyProvider:
    """Stub für Tests, die keine Volatilität interessiert: liefert nie Kurse."""

    def fetch_daily_closes(self, symbol: str, start: str | None = None) -> list[dict]:
        return []


def _stub_daily_sync(repo: QuoteRepository) -> DailyCloseSync:
    """Baut einen `DailyCloseSync`, der nie echte Tages-Schlusskurse liefert."""
    return DailyCloseSync(repo, _EmptyDailyProvider())


class FakeQuoteService:
    """Zählt Aufrufe und liefert eine vorgegebene Antwort (oder wirft)."""

    def __init__(
        self,
        response: QuoteResponse | None,
        raises: bool = False,
        exception: type[Exception] = QuoteUnavailableError,
    ) -> None:
        self._response = response
        self._raises = raises
        self._exception = exception
        self.calls = 0

    def get_quote_by_isin(self, isin: str) -> QuoteResponse:
        self.calls += 1
        if self._raises:
            raise self._exception(isin)
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
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=_stub_daily_sync(repo))

    result = service.get_by_isin("IE00B3RBWM25")

    assert fake.calls == 1
    assert result.cached is False
    assert repo.get_instrument_by_isin("IE00B3RBWM25") is not None


def test_frischer_cache_vermeidet_zweiten_fetch(repo: QuoteRepository) -> None:
    fake = FakeQuoteService(_response(_now()))
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=_stub_daily_sync(repo))

    service.get_by_isin("IE00B3RBWM25")  # füllt Cache
    result = service.get_by_isin("IE00B3RBWM25")  # Cache-Hit

    assert fake.calls == 1  # kein zweiter Live-Fetch
    assert result.cached is True
    assert result.stale is False


def test_abgelaufener_cache_beschafft_neu(repo: QuoteRepository) -> None:
    repo.save_quote(_response(_hours_ago(10)))  # alter Kurs
    fake = FakeQuoteService(_response(_now(), price=200.0))
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=_stub_daily_sync(repo))

    result = service.get_by_isin("IE00B3RBWM25")

    assert fake.calls == 1
    assert result.cached is False
    assert result.price == 200.0


def test_stale_bei_fehler_und_vorhandenem_cache(repo: QuoteRepository) -> None:
    repo.save_quote(_response(_hours_ago(10), price=155.0))  # alter Kurs
    fake = FakeQuoteService(None, raises=True)  # Live-Beschaffung schlägt fehl
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=_stub_daily_sync(repo))

    result = service.get_by_isin("IE00B3RBWM25")

    assert result.stale is True
    assert result.cached is True
    assert result.price == 155.0


def test_fehler_ohne_cache_propagiert(repo: QuoteRepository) -> None:
    fake = FakeQuoteService(None, raises=True)
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=_stub_daily_sync(repo))

    with pytest.raises(QuoteUnavailableError):
        service.get_by_isin("IE00B3RBWM25")


def test_stale_auch_bei_resolver_ausfall(repo: QuoteRepository) -> None:
    """Resolver-Ausfall (InstrumentNotFoundError) → stale Cache statt 404."""
    repo.save_quote(_response(_hours_ago(10), price=155.0))  # alter Kurs
    fake = FakeQuoteService(None, raises=True, exception=InstrumentNotFoundError)
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=_stub_daily_sync(repo))

    result = service.get_by_isin("IE00B3RBWM25")

    assert result.stale is True
    assert result.price == 155.0


def test_resolver_ausfall_ohne_cache_propagiert(repo: QuoteRepository) -> None:
    fake = FakeQuoteService(None, raises=True, exception=InstrumentNotFoundError)
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=_stub_daily_sync(repo))

    with pytest.raises(InstrumentNotFoundError):
        service.get_by_isin("IE00B3RBWM25")


def test_refresh_all_verweigert_parallellauf(repo: QuoteRepository) -> None:
    """Läuft bereits ein Refresh, wird ein zweiter Aufruf abgewiesen."""
    service = CachedQuoteService(
        FakeQuoteService(_response(_now())), repo, ttl_hours=6,
        daily_sync=_stub_daily_sync(repo),
    )

    assert service._refresh_lock.acquire(blocking=False)  # Lauf simulieren
    try:
        with pytest.raises(RefreshInProgressError):
            service.refresh_all()
    finally:
        service._refresh_lock.release()

    assert service.refresh_all() == 0  # nach Freigabe läuft es wieder


class _FakeDailyProvider:
    """Liefert feste Tages-Schlusskurse für die Volatilitätsberechnung."""

    def __init__(self, closes: list[float]) -> None:
        self._closes = closes

    def fetch_daily_closes(self, symbol: str, start: str | None = None):
        return [
            {"date": f"2026-01-{i + 1:02d}", "close": c, "currency": "EUR"}
            for i, c in enumerate(self._closes)
        ]


class _StockQuoteService:
    """Minimaler QuoteService-Stub: liefert eine Aktien-Antwort ohne Volatilität."""

    def get_quote_by_isin(self, isin: str) -> QuoteResponse:
        return QuoteResponse(
            isin=isin, symbol="AAPL.DE", currency="EUR", price=100.0,
            quote_time="2026-07-13T10:00:00+00:00",
            fetched_at="2026-07-13T10:00:00+00:00", type="stock", volatility=None,
        )


def test_refresh_one_berechnet_volatilitaet_aus_cache(tmp_path) -> None:
    db_path = str(tmp_path / "vola.db")
    init_db(db_path)
    repo = QuoteRepository(db_path)
    closes = [100.0, 101.0, 99.5, 102.0, 100.5, 103.0, 101.5]
    daily_sync = DailyCloseSync(repo, _FakeDailyProvider(closes))
    service = CachedQuoteService(_StockQuoteService(), repo, ttl_hours=6, daily_sync=daily_sync)

    result = service.refresh_one("US0378331005")

    assert result.volatility == annualized_volatility(closes)
    stored = repo.get_instrument_by_isin("US0378331005")
    assert stored["volatility"] == result.volatility


def test_refresh_behaelt_justetf_volatilitaet(tmp_path) -> None:
    """Liefert der QuoteService bereits eine Volatilität (justETF), wird sie nicht überschrieben."""

    class _EtfQuoteService:
        def get_quote_by_isin(self, isin: str) -> QuoteResponse:
            return QuoteResponse(
                isin=isin, symbol="VGWL.DE", currency="EUR", price=160.0,
                quote_time="2026-07-13T10:00:00+00:00",
                fetched_at="2026-07-13T10:00:00+00:00", type="etf", volatility=9.95,
            )

    db_path = str(tmp_path / "vola2.db")
    init_db(db_path)
    repo = QuoteRepository(db_path)
    daily_sync = DailyCloseSync(repo, _FakeDailyProvider([100.0, 200.0, 50.0, 300.0, 80.0]))
    service = CachedQuoteService(_EtfQuoteService(), repo, ttl_hours=6, daily_sync=daily_sync)

    result = service.refresh_one("IE00B3RBWM25")

    assert result.volatility == 9.95  # justETF-Wert bleibt

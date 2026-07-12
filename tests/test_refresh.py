"""Tests für den Hintergrund-Refresh und den Scheduler."""

from pathlib import Path

import pytest

from app.db import init_db
from app.models import QuoteResponse
from app.repository import QuoteRepository
from app.scheduler import RefreshScheduler
from app.services.quote_cache import CachedQuoteService
from app.services.quote_service import QuoteUnavailableError


class FakeQuoteService:
    """Liefert frische Antworten pro ISIN/Symbol; kann für eine ISIN fehlschlagen."""

    def __init__(self, failing_isin: str | None = None) -> None:
        self._failing_isin = failing_isin

    def get_quote_by_isin(self, isin: str) -> QuoteResponse:
        if isin == self._failing_isin:
            raise QuoteUnavailableError(isin)
        return QuoteResponse(
            isin=isin,
            symbol="SYM.DE",
            currency="EUR",
            price=200.0,
            quote_time="2026-07-12T20:00:00+00:00",
            fetched_at="2026-07-12T20:00:00+00:00",
            type="etf",
        )

    def get_quote_by_symbol(self, symbol: str) -> QuoteResponse:
        return QuoteResponse(
            isin=None,
            symbol=symbol,
            currency="USD",
            price=210.0,
            quote_time="2026-07-12T20:00:00+00:00",
            fetched_at="2026-07-12T20:00:00+00:00",
            type="stock",
        )


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    db_path = str(tmp_path / "refresh.db")
    init_db(db_path)
    return QuoteRepository(db_path)


def _seed(repo: QuoteRepository, isin: str | None, symbol: str) -> None:
    repo.save_quote(
        QuoteResponse(
            isin=isin,
            symbol=symbol,
            currency="EUR",
            price=100.0,
            quote_time="2026-07-12T10:00:00+00:00",
            fetched_at="2026-07-12T10:00:00+00:00",
            type="etf" if isin else "stock",
        )
    )


def test_refresh_all_aktualisiert_alle(repo: QuoteRepository) -> None:
    _seed(repo, "IE00B3RBWM25", "VGWL.DE")
    _seed(repo, None, "AAPL")
    service = CachedQuoteService(FakeQuoteService(), repo, ttl_hours=6)

    refreshed = service.refresh_all()

    assert refreshed == 2
    etf = repo.get_instrument_by_isin("IE00B3RBWM25")
    assert len(repo.get_history(etf["id"])) == 2  # alter + neuer Punkt


def test_refresh_all_isoliert_fehler(repo: QuoteRepository) -> None:
    _seed(repo, "IE00B3RBWM25", "VGWL.DE")  # wird fehlschlagen
    _seed(repo, None, "AAPL")  # bleibt erfolgreich
    service = CachedQuoteService(
        FakeQuoteService(failing_isin="IE00B3RBWM25"), repo, ttl_hours=6
    )

    refreshed = service.refresh_all()

    assert refreshed == 1  # nur AAPL
    etf = repo.get_instrument_by_isin("IE00B3RBWM25")
    assert len(repo.get_history(etf["id"])) == 1  # kein neuer Punkt für die Fehler-ISIN


class NoopService:
    """Minimaler Service für den Scheduler-Test."""

    def refresh_all(self) -> int:
        return 0


def test_scheduler_registriert_job_und_stoppt() -> None:
    scheduler = RefreshScheduler(NoopService(), interval_hours=1)
    scheduler.start()
    try:
        assert scheduler._scheduler.get_job("refresh_all") is not None
    finally:
        scheduler.shutdown()

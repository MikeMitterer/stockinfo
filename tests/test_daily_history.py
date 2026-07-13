"""Tests für die EOD-Tageshistorie: Repository + inkrementelles Caching."""

from datetime import date, timedelta
from pathlib import Path

import pytest

from app.db import init_db
from app.models import QuoteResponse
from app.repository import QuoteRepository
from app.services.daily_history import DailyHistoryService


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    db_path = str(tmp_path / "daily.db")
    init_db(db_path)
    return QuoteRepository(db_path)


def _seed(repo: QuoteRepository, isin: str = "IE00B3RBWM25", symbol: str = "VGWL.DE") -> dict:
    repo.save_quote(
        QuoteResponse(
            isin=isin, symbol=symbol, currency="EUR", price=100.0,
            quote_time="2026-07-13T10:00:00+00:00",
            fetched_at="2026-07-13T10:00:00+00:00", type="etf",
        )
    )
    return repo.get_instrument_by_isin(isin)


class FakeDailyProvider:
    """Zählt Aufrufe und liefert feste Tages-Schlusskurse."""

    def __init__(self) -> None:
        self.calls: list[str | None] = []

    def fetch_daily_closes(self, symbol: str, start: str | None = None) -> list[dict]:
        self.calls.append(start)
        return [
            {"date": "2026-07-10", "close": 160.0, "currency": "EUR"},
            {"date": "2026-07-11", "close": 161.0, "currency": "EUR"},
            {"date": "2026-07-13", "close": 162.0, "currency": "EUR"},
        ]


class FakeQuotes:
    """Stub — Instrument existiert bereits, muss nicht angelegt werden."""

    def get_by_isin(self, isin: str) -> None: ...
    def get_by_symbol(self, symbol: str) -> None: ...


def test_daily_repository_roundtrip(repo: QuoteRepository) -> None:
    inst = _seed(repo)
    repo.upsert_daily_closes(
        inst["id"],
        [
            {"date": "2026-07-10", "close": 160.0, "currency": "EUR"},
            {"date": "2026-07-11", "close": 161.0, "currency": "EUR"},
        ],
    )
    assert repo.daily_closes_range(inst["id"]) == ("2026-07-10", "2026-07-11")
    assert len(repo.get_daily_closes(inst["id"])) == 2

    # gleiches Datum → Update (Schlusskurs firmt sich)
    repo.upsert_daily_closes(inst["id"], [{"date": "2026-07-11", "close": 999.0, "currency": "EUR"}])
    rows = repo.get_daily_closes(inst["id"], "2026-07-11")
    assert len(rows) == 1 and rows[0]["close"] == 999.0


def test_daily_service_first_fetches_then_uses_cache(repo: QuoteRepository) -> None:
    _seed(repo)
    provider = FakeDailyProvider()
    service = DailyHistoryService(repo, provider, FakeQuotes())

    first = service.get_daily(isin="IE00B3RBWM25", period="1m")
    assert len(first) >= 1
    assert provider.calls == [
        (date.today() - timedelta(days=31)).isoformat()
    ]  # 1x befragt (Cache leer)

    # gleiche Anfrage → aus dem Cache, KEIN yfinance-Aufruf
    provider.calls.clear()
    second = service.get_daily(isin="IE00B3RBWM25", period="1m")
    assert provider.calls == []
    assert len(second) == len(first)

    # längerer Zeitraum → nur die Differenz (rückwärts) wird geholt
    service.get_daily(isin="IE00B3RBWM25", period="1y")
    assert provider.calls == [(date.today() - timedelta(days=366)).isoformat()]

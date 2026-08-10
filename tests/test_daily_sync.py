"""Tests für die gemeinsame inkrementelle EOD-Sync-Einheit."""

from datetime import date, timedelta
from pathlib import Path

import pytest

from app.db import init_db
from app.models import QuoteResponse
from app.repository import QuoteRepository
from app.services.daily_sync import DailyCloseSync


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    db_path = str(tmp_path / "sync.db")
    init_db(db_path)
    return QuoteRepository(db_path)


def _seed(repo: QuoteRepository) -> dict:
    repo.save_quote(
        QuoteResponse(
            isin="IE00B3RBWM25", symbol="VGWL.DE", currency="EUR", price=100.0,
            quote_time="2026-07-13T10:00:00+00:00",
            fetched_at="2026-07-13T10:00:00+00:00", type="etf",
        )
    )
    return repo.get_instrument_by_isin("IE00B3RBWM25")


class FakeProvider:
    def __init__(self, rows: list[dict] | None) -> None:
        self.calls: list[str | None] = []
        self._rows = rows

    def fetch_daily_closes(self, symbol: str, start: str | None = None):
        self.calls.append(start)
        return self._rows


def test_sync_holt_bei_leerem_cache_und_setzt_wasserzeichen(repo: QuoteRepository) -> None:
    inst = _seed(repo)
    provider = FakeProvider([{"date": "2026-07-11", "close": 161.0, "currency": "EUR"}])
    sync = DailyCloseSync(repo, provider)

    start = (date.today() - timedelta(days=370)).isoformat()
    assert sync.sync(inst["id"], inst["symbol"], start) is True
    assert repo.get_daily_meta(inst["id"]) is not None
    assert len(repo.get_daily_closes(inst["id"])) == 1


def test_sync_meldet_false_bei_fehlgeschlagenem_erstabruf(repo: QuoteRepository) -> None:
    inst = _seed(repo)
    sync = DailyCloseSync(repo, FakeProvider(None))  # Provider-Fehler
    assert sync.sync(inst["id"], inst["symbol"], None) is False
    assert repo.get_daily_meta(inst["id"]) is None


def test_sync_holt_beim_zweiten_lauf_nur_das_delta(repo: QuoteRepository) -> None:
    inst = _seed(repo)
    provider = FakeProvider([{"date": "2026-07-11", "close": 161.0, "currency": "EUR"}])
    sync = DailyCloseSync(repo, provider)
    start = (date.today() - timedelta(days=370)).isoformat()

    sync.sync(inst["id"], inst["symbol"], start)
    provider.calls.clear()
    sync.sync(inst["id"], inst["symbol"], start)  # gleicher Zeitraum, Cache aktuell genug

    # nur ein Delta-Fetch (fetched_to < heute), nicht erneut die volle Historie
    assert provider.calls == [repo.get_daily_meta(inst["id"])["fetched_to"]] or provider.calls == []

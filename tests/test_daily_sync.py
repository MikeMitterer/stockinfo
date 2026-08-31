"""Tests für die gemeinsame inkrementelle EOD-Sync-Einheit."""

from datetime import date, timedelta
from pathlib import Path

import pytest

from app.db import init_db
from app.models import ListedIdentityOut, QuoteResponse
from app.providers.base import SourceAnswer
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
            identity=ListedIdentityOut(ticker="VGWL", mic="XETR", isin="IE00B3RBWM25"),
            symbol="VGWL.DE",
            name="VGWL.DE Testpapier",
            currency="EUR",
            price=100.0,
            quote_time="2026-07-13T10:00:00+00:00",
            fetched_at="2026-07-13T10:00:00+00:00",
            type="etf",
        )
    )
    return repo.get_instrument_by_isin("IE00B3RBWM25")


class FakeProvider:
    def __init__(self, rows: list[dict] | None, *, disturbed: bool = False) -> None:
        """
        Args:
            rows: Die gelieferte Reihe; ``None`` heisst „keine Auskunft".
            disturbed: Ob das Ausbleiben eine Stoerung war. Seit T-44 muss das
                Double sagen, welchen Fall es meint.
        """
        self.calls: list[str | None] = []
        self._rows = rows
        self._disturbed = disturbed

    def fetch_daily_closes(
        self,
        symbol: str,
        start: str | None = None,
        *,
        identity: object | None = None,
        instrument_type: str | None = None,
    ) -> SourceAnswer[list[dict]]:
        self.calls.append(start)
        return SourceAnswer(self._rows, disturbed=self._disturbed)


def test_sync_holt_bei_leerem_cache_und_setzt_wasserzeichen(
    repo: QuoteRepository,
) -> None:
    inst = _seed(repo)
    provider = FakeProvider([{"date": "2026-07-11", "close": 161.0, "currency": "EUR"}])
    sync = DailyCloseSync(repo, provider)

    start = (date.today() - timedelta(days=370)).isoformat()
    assert sync.sync(inst["id"], inst["symbol"], start).value is True
    assert repo.get_daily_meta(inst["id"]) is not None
    assert len(repo.get_daily_closes(inst["id"])) == 1


def test_sync_meldet_die_stoerung_beim_erstabruf(repo: QuoteRepository) -> None:
    inst = _seed(repo)
    sync = DailyCloseSync(repo, FakeProvider(None, disturbed=True))

    answer = sync.sync(inst["id"], inst["symbol"], None)

    assert answer.is_hit is False
    assert answer.disturbed is True, "die Stoerung ging auf dem Weg verloren"
    assert repo.get_daily_meta(inst["id"]) is None


def test_sync_reicht_den_sauberen_nichttreffer_unveraendert_durch(
    repo: QuoteRepository,
) -> None:
    """**Die Gegenprobe zum Fall darueber.** Ohne sie waere `disturbed` auch
    dann gruen, wenn `sync` es fest auf `True` setzte — und damit jede fehlende
    Reihe wieder ein Ausfall.
    """
    inst = _seed(repo)
    sync = DailyCloseSync(repo, FakeProvider(None))

    answer = sync.sync(inst["id"], inst["symbol"], None)

    assert answer.is_hit is False
    assert answer.disturbed is False
    assert repo.get_daily_meta(inst["id"]) is None


def test_sync_holt_beim_zweiten_lauf_nur_das_delta(repo: QuoteRepository) -> None:
    inst = _seed(repo)
    provider = FakeProvider([{"date": "2026-07-11", "close": 161.0, "currency": "EUR"}])
    sync = DailyCloseSync(repo, provider)
    start = (date.today() - timedelta(days=370)).isoformat()

    sync.sync(inst["id"], inst["symbol"], start)
    provider.calls.clear()
    sync.sync(
        inst["id"], inst["symbol"], start
    )  # gleicher Zeitraum, Cache aktuell genug

    # Cache bereits vollständig für heute und den gewünschten Zeitraum → kein Fetch
    assert provider.calls == []

from pathlib import Path

import pytest

from app.db import init_db
from app.models import QuoteResponse
from app.repository import QuoteRepository


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    db_path = str(tmp_path / "dash.db")
    init_db(db_path)
    return QuoteRepository(db_path)


def _save(repo: QuoteRepository, isin: str, symbol: str, price: float, t: str) -> None:
    repo.save_quote(
        QuoteResponse(
            isin=isin, symbol=symbol, currency="EUR", price=price,
            quote_time=t, fetched_at=t, type="etf", ter=0.19, provider="Vanguard",
        )
    )


def test_list_instruments_with_latest(repo: QuoteRepository) -> None:
    _save(repo, "IE00B3RBWM25", "VGWL.DE", 160.0, "2026-07-12T10:00:00+00:00")
    _save(repo, "IE00B3RBWM25", "VGWL.DE", 161.0, "2026-07-12T11:00:00+00:00")

    rows = repo.list_instruments_with_latest()
    assert len(rows) == 1
    row = rows[0]
    assert row["symbol"] == "VGWL.DE"
    assert row["latest_price"] == 161.0  # jüngster Kurs
    assert row["history_count"] == 2


def test_delete_instrument(repo: QuoteRepository) -> None:
    _save(repo, "IE00B3RBWM25", "VGWL.DE", 160.0, "2026-07-12T10:00:00+00:00")

    assert repo.delete_instrument("IE00B3RBWM25") is True
    assert repo.get_instrument_by_isin("IE00B3RBWM25") is None
    assert repo.delete_instrument("IE00B3RBWM25") is False  # nichts mehr da


def test_count_instruments(repo: QuoteRepository) -> None:
    assert repo.count_instruments() == 0
    _save(repo, "IE00B3RBWM25", "VGWL.DE", 160.0, "2026-07-12T10:00:00+00:00")
    _save(repo, "IE0032077012", "EQQQ.DE", 635.0, "2026-07-12T10:00:00+00:00")
    assert repo.count_instruments() == 2

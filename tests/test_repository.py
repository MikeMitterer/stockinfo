"""Tests für das SQLite-Repository (temporäre DB, kein Netz)."""

from pathlib import Path

import pytest

from app.db import init_db
from app.models import QuoteResponse
from app.repository import QuoteRepository


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    """Repository auf einer frisch initialisierten temporären DB."""
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    return QuoteRepository(db_path)


def _quote(price: float, quote_time: str, fetched_at: str) -> QuoteResponse:
    return QuoteResponse(
        isin="IE00B3RBWM25",
        symbol="VGWL.DE",
        exchange="Xetra",
        name="Vanguard FTSE All-World",
        type="etf",
        currency="EUR",
        price=price,
        quote_time=quote_time,
        volume=1000,
        ter=0.19,
        provider="Vanguard",
        fetched_at=fetched_at,
    )


def test_save_und_lese_instrument_und_quote(repo: QuoteRepository) -> None:
    repo.save_quote(
        _quote(160.98, "2026-07-12T17:00:00+00:00", "2026-07-12T17:00:00+00:00")
    )

    instrument = repo.get_instrument_by_isin("IE00B3RBWM25")
    assert instrument is not None
    assert instrument["symbol"] == "VGWL.DE"
    assert instrument["ter"] == 0.19

    latest = repo.get_latest_quote(instrument["id"])
    assert latest is not None
    assert latest["price"] == 160.98


def test_upsert_aktualisiert_metadaten_ohne_duplikat(repo: QuoteRepository) -> None:
    repo.save_quote(
        _quote(160.0, "2026-07-12T17:00:00+00:00", "2026-07-12T17:00:00+00:00")
    )
    repo.save_quote(
        _quote(161.0, "2026-07-12T18:00:00+00:00", "2026-07-12T18:00:00+00:00")
    )

    instruments = repo.list_instruments()
    assert len(instruments) == 1  # nur ein Instrument

    history = repo.get_history(instruments[0]["id"])
    assert len(history) == 2  # zwei Kurspunkte
    assert history[0]["price"] == 161.0  # neueste zuerst


def test_dedup_gleicher_quote_time(repo: QuoteRepository) -> None:
    repo.save_quote(
        _quote(160.0, "2026-07-12T17:00:00+00:00", "2026-07-12T17:00:00+00:00")
    )
    repo.save_quote(
        _quote(999.0, "2026-07-12T17:00:00+00:00", "2026-07-12T18:00:00+00:00")
    )

    instrument = repo.get_instrument_by_isin("IE00B3RBWM25")
    history = repo.get_history(instrument["id"])
    assert len(history) == 1  # gleicher quote_time → kein zweiter Punkt


def test_history_limit_und_grenzen(repo: QuoteRepository) -> None:
    for hour in range(10, 15):
        ts = f"2026-07-12T{hour:02d}:00:00+00:00"
        repo.save_quote(_quote(100.0 + hour, ts, ts))

    instrument = repo.get_instrument_by_isin("IE00B3RBWM25")
    limited = repo.get_history(instrument["id"], limit=2)
    assert len(limited) == 2

    ranged = repo.get_history(
        instrument["id"],
        date_from="2026-07-12T12:00:00+00:00",
        date_to="2026-07-12T13:00:00+00:00",
    )
    assert len(ranged) == 2

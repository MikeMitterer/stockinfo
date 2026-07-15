"""Tests für die EOD-Tageshistorie: Repository + inkrementelles Caching."""

from datetime import date, timedelta
from pathlib import Path

import pytest

from app.db import init_db
from app.models import QuoteResponse
from app.repository import QuoteRepository
from app.services.daily_history import DailyHistoryService
from app.services.quote_service import QuoteUnavailableError


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
    """Stub — Instrument existiert bereits; reicht den Lookup ans Repo durch."""

    def __init__(self, repo: QuoteRepository) -> None:
        self._repo = repo

    def ensure_instrument(
        self, *, isin: str | None = None, symbol: str | None = None
    ) -> dict:
        if isin:
            return self._repo.get_instrument_by_isin(isin)
        return self._repo.get_instrument_by_symbol(symbol)


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
    service = DailyHistoryService(repo, provider, FakeQuotes(repo))

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


class FlakyDailyProvider:
    """Schlägt die ersten ``fail_first`` Aufrufe fehl (None), danach Daten."""

    def __init__(self, fail_first: int = 1) -> None:
        self.calls: list[str | None] = []
        self._fail_first = fail_first

    def fetch_daily_closes(
        self, symbol: str, start: str | None = None
    ) -> list[dict] | None:
        self.calls.append(start)
        if len(self.calls) <= self._fail_first:
            return None
        return [{"date": "2026-07-13", "close": 162.0, "currency": "EUR"}]


def test_fehlgeschlagener_erstabruf_setzt_kein_wasserzeichen(
    repo: QuoteRepository,
) -> None:
    """Provider-Fehler beim Erstabruf → Fehler statt dauerhaft leerer Historie."""
    inst = _seed(repo)
    provider = FlakyDailyProvider(fail_first=1)
    service = DailyHistoryService(repo, provider, FakeQuotes(repo))

    with pytest.raises(QuoteUnavailableError):
        service.get_daily(isin="IE00B3RBWM25", period="1m")
    assert repo.get_daily_meta(inst["id"]) is None  # kein Wasserzeichen gesetzt

    # nächster Versuch holt erneut und setzt das Wasserzeichen
    result = service.get_daily(isin="IE00B3RBWM25", period="1m")
    assert len(result) == 1
    assert repo.get_daily_meta(inst["id"]) is not None


def test_fehlgeschlagener_folgeabruf_liefert_cache_ohne_fortschreibung(
    repo: QuoteRepository,
) -> None:
    """Provider-Fehler beim Nachladen → Cache liefern, ``fetched_to`` unverändert."""
    inst = _seed(repo)
    repo.upsert_daily_closes(
        inst["id"], [{"date": "2026-07-10", "close": 160.0, "currency": "EUR"}]
    )
    stale_day = "2026-07-10"
    repo.set_daily_meta(inst["id"], "2026-06-13", stale_day)
    provider = FlakyDailyProvider(fail_first=99)  # jeder Fetch schlägt fehl
    service = DailyHistoryService(repo, provider, FakeQuotes(repo))

    result = service.get_daily(isin="IE00B3RBWM25", period="1m")

    assert len(result) == 1  # Cache wird geliefert
    meta = repo.get_daily_meta(inst["id"])
    assert meta["fetched_to"] == stale_day  # NICHT auf heute fortgeschrieben

"""Tests für den Hintergrund-Refresh und den Scheduler."""

import threading
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.models import ListedIdentityOut, QuoteResponse
from app.persistence.db import init_db
from app.persistence.repository import QuoteRepository
from app.scheduler import RefreshScheduler
from app.services.quote_cache import CachedQuoteService
from app.services.quote_service import QuoteUnavailableError
from tests.boundaries import empty_daily_sync


class FakeQuoteService:
    """Liefert frische Antworten pro ISIN/Symbol; kann für eine ISIN fehlschlagen."""

    def __init__(self, failing_isin: str | None = None) -> None:
        self._failing_isin = failing_isin

    def get_quote_by_isin(self, isin: str, enrich_etf: bool = True) -> QuoteResponse:
        if isin == self._failing_isin:
            raise QuoteUnavailableError(isin)
        return QuoteResponse(
            symbol="SYM.DE",
            name="SYM.DE Testpapier",
            identity=ListedIdentityOut(ticker="SYM", mic="XETR", isin=isin),
            currency="EUR",
            price=200.0,
            quote_time="2026-07-12T20:00:00+00:00",
            fetched_at="2026-07-12T20:00:00+00:00",
            type="etf",
        )

    def get_quote_by_symbol(
        self, symbol: str, enrich_etf: bool = True
    ) -> QuoteResponse:
        return QuoteResponse(
            symbol=symbol,
            name="Testpapier",
            identity=ListedIdentityOut(
                ticker=symbol.split(".")[0], mic="XETR", isin=None
            ),
            currency="USD",
            price=210.0,
            quote_time="2026-07-12T20:00:00+00:00",
            fetched_at="2026-07-12T20:00:00+00:00",
            type="stock",
        )

    def get_quote_for_known(
        self,
        symbol: str,
        isin: str | None = None,
        exchange: str | None = None,
        instrument_type: str | None = None,
        identity: object | None = None,
        enrich_etf: bool = True,
        name: str | None = None,
    ) -> QuoteResponse:
        """Der Weg des Sammelrefresh: bekanntes Listing, keine neue Auflösung."""
        if isin:
            return self.get_quote_by_isin(isin, enrich_etf)
        return self.get_quote_by_symbol(symbol, enrich_etf)


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    db_path = str(tmp_path / "refresh.db")
    init_db(db_path)
    return QuoteRepository(db_path)


def _seed(repo: QuoteRepository, isin: str | None, symbol: str) -> None:
    repo.save_quote(
        QuoteResponse(
            symbol=symbol,
            name="Testpapier",
            identity=ListedIdentityOut(
                ticker=symbol.split(".")[0], mic="XETR", isin=isin
            ),
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
    service = CachedQuoteService(
        FakeQuoteService(), repo, ttl_hours=6, daily_sync=empty_daily_sync(repo)
    )

    refreshed = service.refresh_all()

    assert refreshed == 2
    etf = repo.get_instrument_by_isin("IE00B3RBWM25")
    assert len(repo.get_history(etf["id"])) == 2  # alter + neuer Punkt


def test_refresh_all_isoliert_fehler(repo: QuoteRepository) -> None:
    _seed(repo, "IE00B3RBWM25", "VGWL.DE")  # wird fehlschlagen
    _seed(repo, None, "AAPL")  # bleibt erfolgreich
    service = CachedQuoteService(
        FakeQuoteService(failing_isin="IE00B3RBWM25"),
        repo,
        ttl_hours=6,
        daily_sync=empty_daily_sync(repo),
    )

    refreshed = service.refresh_all()

    assert refreshed == 1  # nur AAPL
    etf = repo.get_instrument_by_isin("IE00B3RBWM25")
    assert len(repo.get_history(etf["id"])) == 1  # kein neuer Punkt für die Fehler-ISIN


class CountingService:
    """Zählt die Refresh-Läufe des Schedulers und meldet den ersten."""

    def __init__(self) -> None:
        self.runs = 0
        self.first_run = threading.Event()

    def refresh_all(self) -> int:
        self.runs += 1
        self.first_run.set()
        return 0


def test_scheduler_registriert_job_und_stoppt() -> None:
    scheduler = RefreshScheduler(CountingService(), interval_minutes=60, run_on_start=False)
    scheduler.start()
    try:
        assert scheduler._scheduler.get_job("refresh_all") is not None
    finally:
        scheduler.shutdown()


@pytest.mark.parametrize(
    ("run_on_start", "expected_runs"),
    [
        pytest.param(True, 1, id="erster-lauf-direkt-nach-dem-start"),
        pytest.param(False, 0, id="ohne-startlauf-erst-nach-dem-intervall"),
    ],
)
def test_erster_refresh_laeuft_beim_start(run_on_start: bool, expected_runs: int) -> None:
    """Nach einem Neustart sind die Kurse nicht bis zu ein Intervall alt."""
    service = CountingService()
    scheduler = RefreshScheduler(service, interval_minutes=60, run_on_start=run_on_start)
    scheduler.start()
    try:
        service.first_run.wait(timeout=1)
    finally:
        scheduler.shutdown()

    assert service.runs == expected_runs


def _settings(monkeypatch, **environment: str) -> Settings:
    """Settings nur aus den übergebenen Umgebungswerten, ohne .env."""
    for name in ("REFRESH_INTERVAL_HOURS", "REFRESH_INTERVAL_MINUTES", "REFRESH_ON_START"):
        monkeypatch.delenv(name, raising=False)
    for name, value in environment.items():
        monkeypatch.setenv(name, value)
    return Settings(_env_file=None)


@pytest.mark.parametrize(
    ("environment", "expected_minutes"),
    [
        pytest.param({}, 360, id="vorgabe-6-stunden"),
        pytest.param({"REFRESH_INTERVAL_HOURS": "2"}, 120, id="stunden-wie-bisher"),
        pytest.param({"REFRESH_INTERVAL_MINUTES": "15"}, 15, id="minuten"),
        pytest.param(
            {"REFRESH_INTERVAL_HOURS": "2", "REFRESH_INTERVAL_MINUTES": "15"},
            15,
            id="minuten-gehen-vor-stunden",
        ),
        pytest.param({"REFRESH_INTERVAL_MINUTES": ""}, 360, id="leere-minuten-gelten-als-nicht-gesetzt"),
    ],
)
def test_refresh_intervall_in_minuten(
    monkeypatch, environment: dict[str, str], expected_minutes: int
) -> None:
    assert _settings(monkeypatch, **environment).refresh_minutes == expected_minutes


@pytest.mark.parametrize(
    ("name", "value"),
    [
        pytest.param("REFRESH_INTERVAL_MINUTES", "0", id="minuten-null"),
        pytest.param("REFRESH_INTERVAL_MINUTES", "-5", id="minuten-negativ"),
        pytest.param("REFRESH_INTERVAL_MINUTES", "viertel", id="minuten-keine-zahl"),
        pytest.param("REFRESH_INTERVAL_HOURS", "0", id="stunden-null"),
    ],
)
def test_ungueltiges_intervall_bricht_den_start_ab(monkeypatch, name: str, value: str) -> None:
    """Kein stiller Standard: Die Meldung nennt die Einstellung."""
    with pytest.raises(ValidationError) as raised:
        _settings(monkeypatch, **{name: value})

    assert name.lower() in str(raised.value)

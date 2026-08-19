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

    def get_quote_by_isin(self, isin: str, enrich_etf: bool = True) -> QuoteResponse:
        self.calls += 1
        if self._raises:
            raise self._exception(isin)
        return self._response

    def get_quote_by_symbol(self, symbol: str, enrich_etf: bool = True) -> QuoteResponse:
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

    def get_quote_by_isin(self, isin: str, enrich_etf: bool = True) -> QuoteResponse:
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
        def get_quote_by_isin(self, isin: str, enrich_etf: bool = True) -> QuoteResponse:
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


def test_refresh_behaelt_letzte_volatilitaet_bei_fehlgeschlagener_neuberechnung(
    tmp_path,
) -> None:
    """EOD-Cache leer und Delta-Fetch tot → letzter bekannter Wert bleibt erhalten."""

    class _FailingDailyProvider:
        """Liefert nie Kurse (leerer EOD-Cache, Delta-Fetch schlägt fehl)."""

        def fetch_daily_closes(self, symbol: str, start: str | None = None):
            return None

    db_path = str(tmp_path / "vola3.db")
    init_db(db_path)
    repo = QuoteRepository(db_path)
    daily_sync = DailyCloseSync(repo, _FailingDailyProvider())
    service = CachedQuoteService(_StockQuoteService(), repo, ttl_hours=6, daily_sync=daily_sync)

    repo.save_quote(_StockQuoteService().get_quote_by_isin("US0378331005"))
    stored_before = repo.get_instrument_by_isin("US0378331005")
    repo.set_volatility(stored_before["id"], 12.5)  # vorherige, bereits bekannte Volatilität

    result = service.refresh_one("US0378331005")

    assert result.volatility == 12.5  # nicht mit None überschrieben
    stored = repo.get_instrument_by_isin("US0378331005")
    assert stored["volatility"] == 12.5


class _MerkendeQuoteService:
    """Merkt sich, ob justETF gefragt werden sollte."""

    def __init__(self, response: QuoteResponse) -> None:
        self._response = response
        self.enrich_calls: list[bool] = []

    def get_quote_by_isin(self, isin: str, enrich_etf: bool = True) -> QuoteResponse:
        self.enrich_calls.append(enrich_etf)
        return self._response

    def get_quote_by_symbol(self, symbol: str, enrich_etf: bool = True) -> QuoteResponse:
        return self.get_quote_by_isin(symbol, enrich_etf)


def _alter_stand(repo: QuoteRepository, meta_fetched_at: str) -> None:
    """Setzt den Zeitstempel des Metadatenstands direkt in der DB."""
    import sqlite3

    with sqlite3.connect(repo._database_path) as verbindung:  # noqa: SLF001
        verbindung.execute(
            "UPDATE instruments SET meta_fetched_at = ?", (meta_fetched_at,)
        )


def test_junge_etf_kennzahlen_loesen_keinen_justetf_abruf_aus(repo) -> None:
    """`metadata_ttl_days` war reine Anzeige — justETF lief bei jedem Kurs mit.

    Kurse und Kennzahlen altern verschieden schnell: Ein Kurs ist nach Stunden
    veraltet, ein Fondsdomizil ändert sich in Jahren nicht. Der Sammelrefresh
    kostete dadurch einen Scrape je ETF und Runde.
    """
    fake = _MerkendeQuoteService(_response(_now()))
    repo.save_quote(_response("2026-01-01T00:00:00+00:00"))
    _alter_stand(repo, _now())  # Kennzahlen von gerade eben

    service = CachedQuoteService(
        fake, repo, ttl_hours=0, daily_sync=_stub_daily_sync(repo), metadata_ttl_days=7
    )
    service.get_by_isin("IE00B3RBWM25")

    assert fake.enrich_calls == [False], "junger Stand — justETF bleibt außen vor"


def test_alte_etf_kennzahlen_loesen_einen_justetf_abruf_aus(repo) -> None:
    fake = _MerkendeQuoteService(_response(_now()))
    repo.save_quote(_response("2026-01-01T00:00:00+00:00"))
    _alter_stand(repo, (datetime.now(timezone.utc) - timedelta(days=30)).isoformat())

    service = CachedQuoteService(
        fake, repo, ttl_hours=0, daily_sync=_stub_daily_sync(repo), metadata_ttl_days=7
    )
    service.get_by_isin("IE00B3RBWM25")

    assert fake.enrich_calls == [True]


def test_unbekanntes_papier_wird_immer_angereichert(repo) -> None:
    """Sonst bekäme ein frisch hinzugefügter ETF seine Kennzahlen nie."""
    fake = _MerkendeQuoteService(_response(_now()))
    service = CachedQuoteService(
        fake, repo, ttl_hours=6, daily_sync=_stub_daily_sync(repo), metadata_ttl_days=7
    )

    service.get_by_isin("IE00B3RBWM25")

    assert fake.enrich_calls == [True]


def test_handrefresh_uebergeht_die_metadaten_ttl(repo) -> None:
    """Wer bewusst auf ↻ drückt, will frische Zahlen — auch die Kennzahlen.

    Der Sammel- und der Hintergrundlauf halten sich an die TTL; der Griff zum
    einzelnen Papier ist die ausdrückliche Ansage, jetzt nachzusehen.
    """
    fake = _MerkendeQuoteService(_response(_now()))
    repo.save_quote(_response("2026-01-01T00:00:00+00:00"))
    _alter_stand(repo, _now())  # Kennzahlen taufrisch — die TTL griffe

    service = CachedQuoteService(
        fake, repo, ttl_hours=6, daily_sync=_stub_daily_sync(repo), metadata_ttl_days=7
    )
    service.refresh_one("IE00B3RBWM25")

    assert fake.enrich_calls == [True]

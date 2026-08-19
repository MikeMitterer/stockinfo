"""Composition-Root — verdrahtet Provider, Resolver, Repository und Services.

Eine einzige, gecachte Instanz des CachedQuoteService wird über FastAPIs
Dependency-Injection an die Router gereicht.
"""

from functools import lru_cache

from app.config import Settings, get_settings
from app.providers.base import InstrumentResolver
from app.providers.justetf_provider import JustEtfProvider
from app.providers.openfigi_provider import OpenFigiClient
from app.providers.yfinance_provider import YFinanceProvider
from app.repository import QuoteRepository
from app.resolver import CompositeResolver, OpenFigiResolver, YFinanceResolver
from app.services.analyzer import QuoteAnalyzer
from app.services.daily_history import DailyHistoryService
from app.services.daily_sync import DailyCloseSync
from app.services.fx_service import CachedFxService
from app.services.quote_cache import CachedQuoteService
from app.services.quote_service import QuoteService


def _build_resolver(settings: Settings) -> InstrumentResolver:
    """Baut den Resolver: strikt nur OpenFIGI, sonst mit Yahoo-Fallback."""
    figi_resolver = OpenFigiResolver(
        OpenFigiClient(settings.openfigi_api_key), settings.default_exchange
    )
    if settings.strict_exchange:
        return figi_resolver
    # Dieselbe Börse für beide: Sonst sucht der Fallback in eine andere
    # Richtung als der Hauptweg und liefert je nach Tagesform ein anderes
    # Listing — mit anderer Währung.
    return CompositeResolver(figi_resolver, YFinanceResolver(settings.default_exchange))


@lru_cache
def get_cached_quote_service() -> CachedQuoteService:
    """Baut den (gecachten) CachedQuoteService aus der aktuellen Konfiguration."""
    settings = get_settings()
    resolver = _build_resolver(settings)
    quote_service = QuoteService(YFinanceProvider(), JustEtfProvider(), resolver)
    repository = QuoteRepository(settings.database_path)
    daily_sync = DailyCloseSync(repository, YFinanceProvider())
    return CachedQuoteService(
        quote_service,
        repository,
        settings.cache_ttl_hours,
        daily_sync,
        settings.metadata_ttl_days,
    )


@lru_cache
def get_daily_history_service() -> DailyHistoryService:
    """Baut den (gecachten) DailyHistoryService für EOD-Historien."""
    settings = get_settings()
    return DailyHistoryService(
        QuoteRepository(settings.database_path),
        YFinanceProvider(),
        get_cached_quote_service(),
    )


@lru_cache
def get_quote_analyzer() -> QuoteAnalyzer:
    """Baut den (gecachten) QuoteAnalyzer aus der aktuellen Konfiguration."""
    settings = get_settings()
    resolver = _build_resolver(settings)
    return QuoteAnalyzer(resolver, JustEtfProvider())


@lru_cache
def get_fx_service() -> CachedFxService:
    """Baut den (gecachten) CachedFxService aus der aktuellen Konfiguration."""
    settings = get_settings()
    return CachedFxService(
        YFinanceProvider(),
        QuoteRepository(settings.database_path),
        settings.fx_ttl_hours,
    )

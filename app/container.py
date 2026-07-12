"""Composition-Root — verdrahtet Provider, Resolver, Repository und Services.

Eine einzige, gecachte Instanz des CachedQuoteService wird über FastAPIs
Dependency-Injection an die Router gereicht.
"""

from functools import lru_cache

from app.config import get_settings
from app.providers.justetf_provider import JustEtfProvider
from app.providers.openfigi_provider import OpenFigiClient
from app.providers.yfinance_provider import YFinanceProvider
from app.repository import QuoteRepository
from app.resolver import CompositeResolver, OpenFigiResolver, YFinanceResolver
from app.services.quote_cache import CachedQuoteService
from app.services.quote_service import QuoteService


@lru_cache
def get_cached_quote_service() -> CachedQuoteService:
    """Baut den (gecachten) CachedQuoteService aus der aktuellen Konfiguration."""
    settings = get_settings()
    resolver = CompositeResolver(
        OpenFigiResolver(
            OpenFigiClient(settings.openfigi_api_key), settings.default_exchange
        ),
        YFinanceResolver(),
    )
    quote_service = QuoteService(YFinanceProvider(), JustEtfProvider(), resolver)
    repository = QuoteRepository(settings.database_path)
    return CachedQuoteService(quote_service, repository, settings.cache_ttl_hours)

"""Composition-Root — verdrahtet Provider, Resolver, Repository und Services.

Eine einzige, gecachte Instanz des CachedQuoteService wird über FastAPIs
Dependency-Injection an die Router gereicht.
"""

from functools import lru_cache

from app.config import Settings, get_settings
from app.providers.base import EtfEnricher, InstrumentResolver
from app.providers.composite_etf import CompositeEtfEnricher
from app.providers.justetf_provider import JustEtfProvider
from app.providers.openfigi_provider import OpenFigiClient
from app.providers.yfinance_etf_provider import YFinanceEtfEnricher
from app.providers.yfinance_provider import YFinanceProvider
from app.repository import QuoteRepository
from app.resolver import CompositeResolver, OpenFigiResolver, YFinanceResolver
from app.services.analyzer import QuoteAnalyzer
from app.services.daily_history import DailyHistoryService
from app.services.daily_sync import DailyCloseSync
from app.services.fx_service import CachedFxService
from app.services.intake_service import IntakeService
from app.services.quote_cache import CachedQuoteService
from app.services.quote_service import QuoteService


def _build_resolver(settings: Settings) -> InstrumentResolver:
    """Baut den Resolver: strikt nur OpenFIGI, sonst mit Kaskade und Fallback.

    `strict_exchange` schaltet **beides** ab, was von der Vorgabebörse
    wegführen könnte: den Yahoo-Fallback und die Heimatbörsen-Kaskade. Wer die
    Einstellung wählt, will diese Börse oder gar nichts — eine Kaskade wäre
    genau die Überraschung in fremder Währung, die er ausgeschlossen hat.
    """
    figi_resolver = OpenFigiResolver(
        OpenFigiClient(settings.openfigi_api_key),
        settings.default_exchange,
        home_fallback=not settings.strict_exchange,
    )
    if settings.strict_exchange:
        return figi_resolver
    # Dieselbe Börse für beide: Sonst sucht der Fallback in eine andere
    # Richtung als der Hauptweg und liefert je nach Tagesform ein anderes
    # Listing — mit anderer Währung.
    return CompositeResolver(figi_resolver, YFinanceResolver(settings.default_exchange))


def _build_etf_enricher() -> EtfEnricher:
    """Baut die ETF-Metadatenquelle: justETF für Europa, Yahoo für den Rest.

    Die Reihenfolge ist die Rangfolge. justETF steht vorn, weil es für
    europäische UCITS-Papiere ungleich mehr liefert (TER, Replikationsart,
    Domizil, Thesaurierung); Yahoo springt nur dort ein, wo justETF nichts
    führt — und steuert dann bewusst nur den Anbieter bei.
    """
    return CompositeEtfEnricher(JustEtfProvider(), YFinanceEtfEnricher())


@lru_cache
def get_cached_quote_service() -> CachedQuoteService:
    """Baut den (gecachten) CachedQuoteService aus der aktuellen Konfiguration."""
    settings = get_settings()
    resolver = _build_resolver(settings)
    quote_service = QuoteService(YFinanceProvider(), _build_etf_enricher(), resolver)
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
def get_intake_service() -> IntakeService:
    """Baut den (gecachten) IntakeService für den Aufnahmeweg.

    Teilt sich den `CachedQuoteService` mit den Kursendpunkten — die Aufnahme
    ist derselbe Weg zur Quelle, nur mit der zusätzlichen Frage, ob das Papier
    dabei entstanden ist.
    """
    settings = get_settings()
    return IntakeService(
        get_cached_quote_service(), QuoteRepository(settings.database_path)
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
    """Baut den (gecachten) QuoteAnalyzer aus der aktuellen Konfiguration.

    Hier steht bewusst `JustEtfProvider` statt des Composite: Der Analyzer misst
    Laufzeiten je Schritt, und die Stufe heißt „justetf". Mit dem Composite
    meldete sie für ein US-Papier 0 ms und „ok" — richtig gemessen, aber falsch
    beschriftet. Der teure Schritt, den diese Seite sichtbar machen soll, ist
    der Scrape.
    """
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

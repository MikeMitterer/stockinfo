"""Composition-Root — verdrahtet Provider, Resolver, Repository und Services.

Eine einzige, gecachte Instanz des CachedQuoteService wird über FastAPIs
Dependency-Injection an die Router gereicht.
"""

from functools import lru_cache
from pathlib import Path
from typing import Annotated

import structlog
from fastapi import Depends

from app.config import get_settings
from app.exchange_catalog import covered_quote_mics
from app.providers.base import EtfEnricher, InstrumentResolver
from app.providers.composite_etf import CompositeEtfEnricher
from app.providers.composite_market import (
    CompositeDailyCloseProvider,
    CompositeQuoteProvider,
)
from app.repository import QuoteRepository
from app.resolver import CompositeResolver
from app.services.analyzer import ROLES as ANALYZED_ROLES
from app.services.analyzer import QuoteAnalyzer
from app.services.backup import BackupService
from app.services.daily_history import DailyHistoryService
from app.services.daily_sync import DailyCloseSync
from app.services.fx_service import CachedFxService
from app.services.intake_service import IntakeService
from app.services.quote_cache import CachedQuoteService
from app.services.quote_service import QuoteService
from app.sources_config import SourcesConfig, load_sources_config
from app.sources_registry import build_chain, describe_chain, detail_definitions

logger = structlog.get_logger()


def initialize_detail_catalog() -> None:
    """Persistiert das validierte Profilschema nach der DB-Initialisierung."""
    settings = get_settings()
    QuoteRepository(settings.database_path).detail_catalog(
        detail_definitions(get_sources_config(), settings)
    )


def sources_path(settings) -> Path:
    """Wo `sources.yaml` liegt — abgeleitet, nicht zusätzlich konfiguriert.

    Ketten und Bestand gehören in dasselbe Volume. Ein eigener Pfad in den
    Einstellungen wäre eine zweite Stelle, an der jemand den falschen Ort
    erwischt — und die Datei läge dann irgendwo, wo sie beim Sichern des
    Volumes fehlt.

    **Eine Funktion, zwei Aufrufer.** Die Verdrahtung fragt beim Start, der
    Leseweg `/sources` bei jedem Request mit den **injizierten** Einstellungen.
    Ohne den gemeinsamen Helfer läse der eine aus der echten Konfiguration,
    während der andere im Test auf eine Ersatzdatei zeigt — der Endpunkt hätte
    dann etwas anderes gemeldet, als die App tatsächlich benutzt.
    """
    return Path(settings.database_path).parent / "sources.yaml"


@lru_cache
def get_sources_config() -> SourcesConfig:
    """Die Quellen-Konfiguration der laufenden App — einmal gelesen."""
    settings = get_settings()
    return load_sources_config(sources_path(settings), settings)


def warm_all_chains() -> None:
    """Baut jede Rolle **einmal**, unabhängig vom ersten Fachrequest.

    Ohne das blieb `fx` bis zum ersten Aufruf ungeprüft — und bei ausstehender
    Migration startet der Scheduler gar nicht, dann waren **alle** Rollen
    spekulativ. `GET /sources` zeigte in dieser Lage eine Auskunft, die sich
    nach dem ersten Fachrequest still änderte.

    Ein Fehlschlag in einer Rolle kostet **diese** Rolle. Der Prozess, `/health`
    und die Diagnose bleiben erreichbar — auch wenn danach keine einzige
    Kursquelle übrig ist. Der Fachbetrieb ist dann nicht arbeitsfähig, und
    genau das soll man in `/sources` sehen, statt es aus einem abgestürzten
    Start zu erschließen.
    """
    from app.sources_config import ROLES

    for role in ROLES:
        try:
            _chain(role)
        except Exception as error:  # noqa: BLE001 — fremder Code in jeder Rolle
            logger.warning(
                "chain_warmup_failed",
                role=role,
                error=f"{type(error).__name__}: {error}",
            )


def _chain(role: str) -> list:
    """Die einsatzbereiten Quellen einer Rolle, in konfigurierter Rangfolge."""
    return build_chain(role, get_sources_config(), get_settings())


def _build_resolver() -> InstrumentResolver:
    """Baut den Resolver aus der konfigurierten Kette.

    **Die `if`-Kaskade ist weg.** Bis T-22 entschied `strict_exchange` hier
    über zwei Dinge zugleich: den Yahoo-Fallback und die Heimatbörsen-Kaskade.
    Das erste ist jetzt eine Frage der Kette — wer nur OpenFIGI will, trägt nur
    OpenFIGI ein —, das zweite bleibt ein Schalter der Quelle und wird ihr beim
    Bauen mitgegeben.

    Die Rangfolge kommt aus `sources.yaml` und wird nicht umsortiert: Sie ist
    die Aussage des Betreibers darüber, wem er zuerst glaubt.
    """
    resolvers = _chain("resolvers")
    if not resolvers:
        # Keine einsatzbereite Quelle ist ein Betriebszustand, kein Absturz:
        # Der Composite antwortet dann durchgehend `NotResponsible`, und der
        # Aufrufer sieht „keine Quelle war zuständig" statt eines Stacktrace.
        logger.warning("resolver_chain_empty")
    return CompositeResolver(*resolvers)


def _build_etf_enricher() -> EtfEnricher:
    """Baut die ETF-Metadatenkette aus der Konfiguration.

    Die Reihenfolge ist die Rangfolge — justETF steht in der Vorgabe vorn, weil
    es für europäische UCITS-Papiere ungleich mehr liefert. **Wer außerhalb
    Europas sitzt, dreht sie jetzt in einer Datei um**, statt den Quelltext zu
    ändern; das war der Anlass des ganzen Vorhabens.
    """
    return CompositeEtfEnricher(*_chain("etf_meta"))


def _market_chain(role: str) -> list:
    """Die **vollständige** Kette einer Marktrolle, in konfigurierter Rangfolge.

    Args:
        role: `quotes`, `daily` oder `fx`.

    Returns:
        Alle einsatzbereiten Quellen der Rolle. `build_chain` gibt für dieselbe
        Konfiguration **dieselben Objekte** zurück; zwei Aufrufer teilen sich
        die Quellen also, auch wenn jeder seine eigene (zustandslose) Kaskade
        darum legt.

    Raises:
        RuntimeError: Keine Quelle dieser Rolle ist einsatzbereit. Das ist
            ausdrücklich ein Startfehler und kein stiller Rückfall: Ohne
            Kursquelle kann die App ihre Hauptaufgabe nicht erfüllen, und ein
            eingebauter Ersatz würde die Konfiguration hinter dem Rücken des
            Betreibers überstimmen.
    """
    sources = _chain(role)
    if not sources:
        raise RuntimeError(
            f"Keine einsatzbereite Quelle für '{role}' konfiguriert — "
            f"`{role}:` in sources.yaml prüfen"
        )
    return sources


@lru_cache
def get_cached_quote_service() -> CachedQuoteService:
    """Baut den (gecachten) CachedQuoteService aus der aktuellen Konfiguration."""
    settings = get_settings()
    resolver = _build_resolver()
    quote_service = QuoteService(
        CompositeQuoteProvider(*_market_chain("quotes")),
        _build_etf_enricher(),
        resolver,
    )
    repository = QuoteRepository(settings.database_path)
    daily_sync = DailyCloseSync(
        repository, CompositeDailyCloseProvider(*_market_chain("daily"))
    )
    return CachedQuoteService(
        quote_service,
        repository,
        settings.cache_ttl_hours,
        daily_sync,
        settings.metadata_ttl_days,
    )


def get_intake_service(
    quotes: Annotated[CachedQuoteService, Depends(get_cached_quote_service)],
) -> IntakeService:
    """Baut den IntakeService für den Aufnahmeweg.

    Teilt sich den `CachedQuoteService` mit den Kursendpunkten — die Aufnahme
    ist derselbe Weg zur Quelle, nur mit der zusätzlichen Frage, ob das Papier
    dabei entstanden ist.

    **Über `Depends`, nicht per direktem Aufruf**, und ohne `lru_cache`: Nur so
    greift ein `dependency_overrides[get_cached_quote_service]` auch hier. Rief
    diese Funktion `get_cached_quote_service()` selbst auf, bekäme der
    Aufnahmeweg im Test den echten Dienst samt Netz und echter Datenbank,
    während die Kursendpunkte am Ersatz hingen — und der Kettentest liefe an
    der Verdrahtung vorbei, die er belegen soll.

    **Und genau ein Mitspieler**, kein eigenes Repository: Zwei Repositories in
    einem Request sind zwei Wahrheiten. Der erste Entwurf gab dem Dienst eines
    aus den Settings mit; im Test schrieb er damit in die Testdatenbank und las
    die Antwortzeile aus der echten.
    """
    _chain("quotes")
    return IntakeService(
        quotes, covered_quote_mics(describe_chain("quotes", get_sources_config()))
    )


@lru_cache
def get_daily_history_service() -> DailyHistoryService:
    """Baut den (gecachten) DailyHistoryService für EOD-Historien."""
    settings = get_settings()
    return DailyHistoryService(
        QuoteRepository(settings.database_path),
        CompositeDailyCloseProvider(*_market_chain("daily")),
        get_cached_quote_service(),
    )


@lru_cache
def get_quote_analyzer() -> QuoteAnalyzer:
    """Baut den (gecachten) QuoteAnalyzer aus der aktuellen Konfiguration.

    **Er bekommt dieselben Ketten wie der Betrieb**, nicht eigene Anbieter. Bis
    T-46 stand hier `JustEtfProvider` fest verdrahtet und daneben `yf.Ticker`
    im Analyzer selbst: Eine Instanz ohne Online-Quelle maß damit Yahoo und
    justETF — Zahlen zu einer Kette, die sie gar nicht führt.
    """
    return QuoteAnalyzer({role: _chain(role) for role in ANALYZED_ROLES})


@lru_cache
def get_backup_service() -> BackupService:
    """Baut den (gecachten) BackupService.

    **Dieselbe `SourcesConfig` wie der Betrieb.** Läse er die Datei selbst,
    beschriebe er eine Konfiguration, die gar nicht läuft — und die Kennung
    stünde für eine Lage, die es nicht gibt.
    """
    return BackupService(get_settings().database_path, get_sources_config())


@lru_cache
def get_fx_service() -> CachedFxService:
    """Baut den (gecachten) CachedFxService aus der aktuellen Konfiguration."""
    settings = get_settings()
    return CachedFxService(
        _market_chain("fx"),
        QuoteRepository(settings.database_path),
        settings.fx_ttl_hours,
    )

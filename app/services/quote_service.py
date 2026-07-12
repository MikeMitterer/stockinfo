"""Orchestriert die Kursbeschaffung — Auflösung, Abfrage, ETF-Anreicherung.

Kennt keine HTTP-Belange. Fehler werden als Domain-Exceptions signalisiert und
in der Router-Schicht auf HTTP-Statuscodes abgebildet.
"""

from datetime import datetime, timezone

import structlog

from app.models import QuoteResponse
from app.providers.base import (
    EtfEnricher,
    InstrumentResolver,
    QuoteProvider,
    ResolvedInstrument,
)

logger = structlog.get_logger()


class InstrumentNotFoundError(Exception):
    """Zu ISIN/Symbol konnte kein Wertpapier aufgelöst werden."""


class QuoteUnavailableError(Exception):
    """Es konnte kein aktueller Kurs beschafft werden."""


class QuoteService:
    """Beschafft einen vollständigen, angereicherten Kurs für ein Wertpapier."""

    def __init__(
        self,
        quote_provider: QuoteProvider,
        etf_provider: EtfEnricher,
        resolver: InstrumentResolver,
    ) -> None:
        """
        Args:
            quote_provider: Liefert den Rohkurs zu einem Symbol.
            etf_provider: Reichert ETFs anhand der ISIN an.
            resolver: Löst ISINs zu Symbolen auf.
        """
        self._quote_provider = quote_provider
        self._etf_provider = etf_provider
        self._resolver = resolver

    def get_quote_by_isin(self, isin: str) -> QuoteResponse:
        """Beschafft den Kurs zu einer ISIN.

        Args:
            isin: ISIN des Wertpapiers.

        Returns:
            Vollständige, ggf. angereicherte Kurs-Antwort.

        Raises:
            InstrumentNotFoundError: ISIN nicht auflösbar.
            QuoteUnavailableError: Kein Kurs beschaffbar.
        """
        resolved = self._resolver.resolve_isin(isin)
        if resolved is None:
            raise InstrumentNotFoundError(isin)
        return self._build(resolved)

    def get_quote_by_symbol(self, symbol: str) -> QuoteResponse:
        """Beschafft den Kurs zu einem vollständigen Yahoo-Symbol.

        Args:
            symbol: Vollständiges Yahoo-Symbol inkl. Börsen-Suffix, z.B.
                'VGWL.DE' (Xetra) oder 'AAPL' (US). Das Suffix wählt die Börse.

        Returns:
            Kurs-Antwort.

        Raises:
            QuoteUnavailableError: Kein Kurs beschaffbar.
        """
        resolved = ResolvedInstrument(symbol=symbol)
        return self._build(resolved)

    def _build(self, resolved: ResolvedInstrument) -> QuoteResponse:
        """Fragt den Kurs ab, baut die Antwort und reichert ETFs an."""
        raw = self._quote_provider.fetch_quote(resolved.symbol)
        if raw is None:
            raise QuoteUnavailableError(resolved.symbol)

        isin = raw.isin or resolved.isin
        instrument_type = raw.type or resolved.type
        response = QuoteResponse(
            isin=isin,
            symbol=resolved.symbol,
            exchange=resolved.exchange or raw.exchange,
            name=raw.name or resolved.name,
            type=instrument_type,
            currency=raw.currency or resolved.currency,
            price=raw.price,
            quote_time=raw.quote_time,
            volume=raw.volume,
            source="yfinance",
            cached=False,
            stale=False,
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )

        if instrument_type == "etf" and isin:
            self._enrich_etf(response, isin)
        return response

    def _enrich_etf(self, response: QuoteResponse, isin: str) -> None:
        """Ergänzt ETF-Details (TER, Anbieter, …) über justETF, best-effort."""
        details = self._etf_provider.fetch_etf(isin)
        if details is None:
            logger.debug("etf_enrichment_skipped", isin=isin)
            return
        response.ter = details.ter
        response.provider = details.provider
        response.replication = details.replication
        response.fund_size = details.fund_size
        response.name = response.name or details.name
        response.currency = response.currency or details.currency
        response.source = "yfinance+justetf"

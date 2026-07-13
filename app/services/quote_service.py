"""Orchestriert die Kursbeschaffung — Auflösung, Abfrage, ETF-Anreicherung.

Kennt keine HTTP-Belange. Fehler werden als Domain-Exceptions signalisiert und
in der Router-Schicht auf HTTP-Statuscodes abgebildet.
"""

import math
import statistics
from datetime import datetime, timedelta, timezone

import structlog

from app.models import QuoteResponse
from app.providers.base import (
    EtfEnricher,
    InstrumentResolver,
    QuoteProvider,
    ResolvedInstrument,
)

logger = structlog.get_logger()

# Handelstage pro Jahr — Standardfaktor zur Annualisierung der Tagesvolatilität.
_TRADING_DAYS_PER_YEAR = 252


def annualized_volatility(closes: list[float]) -> float | None:
    """Berechnet die annualisierte Volatilität aus Tages-Schlusskursen.

    Volatilität = Standardabweichung der täglichen Renditen × √252, in Prozent.

    Args:
        closes: Chronologisch geordnete Tages-Schlusskurse.

    Returns:
        Annualisierte Volatilität in Prozent (gerundet), oder ``None`` bei zu
        wenigen Datenpunkten.
    """
    if len(closes) < 5:
        return None
    returns = [
        closes[i] / closes[i - 1] - 1.0
        for i in range(1, len(closes))
        if closes[i - 1]
    ]
    if len(returns) < 2:
        return None
    daily_sd = statistics.stdev(returns)
    return round(daily_sd * math.sqrt(_TRADING_DAYS_PER_YEAR) * 100.0, 2)


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

        # Volatilität aus Tages-Schlusskursen berechnen, wenn justETF keine
        # liefert (Aktien generell, ETFs ohne justETF-Wert).
        if response.volatility is None:
            response.volatility = self._compute_volatility(resolved.symbol)
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
        response.volatility = details.volatility
        response.accumulating = details.accumulating
        response.source = "yfinance+justetf"

    def _compute_volatility(self, symbol: str) -> float | None:
        """Berechnet die 1-Jahres-Volatilität aus den Tages-Schlusskursen.

        Best-effort: greift auf ``fetch_daily_closes`` des Kurs-Providers zu,
        falls vorhanden. Fehler oder fehlende Daten ergeben ``None``.

        Args:
            symbol: Yahoo-Symbol des Wertpapiers.

        Returns:
            Annualisierte Volatilität in Prozent, oder ``None``.
        """
        fetch = getattr(self._quote_provider, "fetch_daily_closes", None)
        if fetch is None:
            return None
        start = (datetime.now(timezone.utc).date() - timedelta(days=370)).isoformat()
        try:
            rows = fetch(symbol, start=start)
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.debug("volatility_fetch_failed", symbol=symbol, error=str(exc))
            return None
        closes = [row["close"] for row in rows if row.get("close") is not None]
        return annualized_volatility(closes)

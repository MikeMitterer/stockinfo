"""Orchestriert die Kursbeschaffung — Auflösung, Abfrage, ETF-Anreicherung.

Kennt keine HTTP-Belange. Fehler werden als Domain-Exceptions signalisiert und
in der Router-Schicht auf HTTP-Statuscodes abgebildet.
"""

import math
import statistics
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

    def get_quote_by_isin(self, isin: str, enrich_etf: bool = True) -> QuoteResponse:
        """Beschafft den Kurs zu einer ISIN.

        Args:
            isin: ISIN des Wertpapiers.
            enrich_etf: Ob justETF gefragt wird. ``False`` heißt „der
                gespeicherte Metadatenstand ist jung genug" — die Antwort
                trägt die ETF-Extras dann nicht und ist als unvollständig
                markiert, damit sie den Bestand nicht überschreibt.

        Returns:
            Vollständige, ggf. angereicherte Kurs-Antwort.

        Raises:
            InstrumentNotFoundError: ISIN nicht auflösbar.
            QuoteUnavailableError: Kein Kurs beschaffbar.
        """
        resolved = self._resolver.resolve_isin(isin)
        if resolved is None:
            raise InstrumentNotFoundError(isin)
        return self._build(resolved, enrich_etf)

    def get_quote_by_symbol(self, symbol: str, enrich_etf: bool = True) -> QuoteResponse:
        """Beschafft den Kurs zu einem vollständigen Yahoo-Symbol.

        Args:
            symbol: Vollständiges Yahoo-Symbol inkl. Börsen-Suffix, z.B.
                'VGWL.DE' (Xetra) oder 'AAPL' (US). Das Suffix wählt die Börse.
            enrich_etf: Ob justETF gefragt wird — siehe `get_quote_by_isin`.

        Returns:
            Kurs-Antwort.

        Raises:
            QuoteUnavailableError: Kein Kurs beschaffbar.
        """
        resolved = ResolvedInstrument(symbol=symbol)
        return self._build(resolved, enrich_etf)

    def get_quote_for_known(
        self,
        symbol: str,
        isin: str | None = None,
        exchange: str | None = None,
        instrument_type: str | None = None,
        enrich_etf: bool = True,
    ) -> QuoteResponse:
        """Beschafft den Kurs für ein **bereits aufgelöstes** Instrument.

        Der Unterschied zu `get_quote_by_isin` ist der fehlende Resolver-Lauf,
        und der ist der ganze Zweck: Die Auflösung ist nicht stabil. Findet
        OpenFIGI kein Listing an der bevorzugten Börse — Zeitüberschreitung,
        Rate-Limit, leere Antwort —, springt der Yahoo-Fallback ein und liefert
        das primäre Listing, bei einem iShares-Papier also die Londoner oder
        US-Notierung. Wer ein bekanntes Papier über die ISIN auffrischt,
        bekommt so mal Xetra in EUR und mal London in GBP, und das Ergebnis
        wird gespeichert. Im Depot fällt die Position damit aus der
        Währungsrechnung, und Gesamtwert wie Anteile stimmen nicht mehr.

        ISIN und Gattung werden trotzdem mitgegeben, und beide aus gutem Grund:
        `_build` braucht die ISIN für die justETF-Anreicherung, und die Gattung
        entscheidet, ob der ETF-Zweig überhaupt betreten wird. Fiele sie auf
        ``None``, bliebe `metadata_complete` auf seiner Vorgabe ``True``, und das
        Repository dürfte die gepflegten justETF-Felder mit nichts überschreiben.
        Der Resolver war bisher der zweite Lieferant der Gattung — wer ihn
        überspringt, muss sie aus der gespeicherten Zeile mitbringen.

        Args:
            symbol: Gespeichertes Yahoo-Symbol inkl. Börsen-Suffix.
            isin: Gespeicherte ISIN, für die ETF-Anreicherung.
            exchange: Gespeicherte Börse — sie bleibt, was sie war.
            instrument_type: Gespeicherte Gattung ('etf', 'stock', …).
            enrich_etf: Ob justETF gefragt wird — siehe `get_quote_by_isin`.

        Returns:
            Kurs-Antwort für genau dieses Listing.

        Raises:
            QuoteUnavailableError: Kein Kurs beschaffbar.
        """
        resolved = ResolvedInstrument(
            symbol=symbol, isin=isin, exchange=exchange, type=instrument_type
        )
        return self._build(resolved, enrich_etf)

    def _build(
        self, resolved: ResolvedInstrument, enrich_etf: bool = True
    ) -> QuoteResponse:
        """Fragt den Kurs ab, baut die Antwort und reichert ETFs an.

        Args:
            resolved: Aufgelöstes Instrument (Symbol, ggf. ISIN und Typ).
            enrich_etf: Ob justETF gefragt wird.

        Returns:
            Kurs-Antwort; ``metadata_complete`` sagt, ob ihre ETF-Felder
            belastbar sind.
        """
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
            # Die Antwort weiß nur dann über die ETF-Extras Bescheid, wenn die
            # Anreicherung gelaufen ist **und** geliefert hat. Sonst darf sie
            # den gespeicherten Stand nicht ersetzen — siehe
            # `QuoteResponse.metadata_complete`. Übersprungen und
            # fehlgeschlagen sind hier dasselbe: In beiden Fällen weiß diese
            # Antwort nichts.
            response.metadata_complete = (
                self._enrich_etf(response, isin) if enrich_etf else False
            )
        return response

    def _enrich_etf(self, response: QuoteResponse, isin: str) -> bool:
        """Ergänzt ETF-Details (TER, Anbieter, …) über justETF, best-effort.

        Args:
            response: Antwort, die ergänzt wird.
            isin: ISIN für die Abfrage.

        Returns:
            ``True`` wenn justETF geantwortet hat — nur dann sind die
            ETF-Felder dieser Antwort belastbar. ``False`` heißt „nicht
            erreichbar", **nicht** „hat nichts". Der Unterschied entscheidet,
            ob der gespeicherte Stand überschrieben werden darf.
        """
        details = self._etf_provider.fetch_etf(isin)
        if details is None:
            logger.debug("etf_enrichment_skipped", isin=isin)
            return False
        response.ter = details.ter
        response.provider = details.provider
        response.replication = details.replication
        response.fund_size = details.fund_size
        response.name = response.name or details.name
        # Kein Rückfall auf die Handelswährung: Zwei Begriffe, zwei Felder.
        response.fund_currency = details.fund_currency
        response.fund_domicile = details.fund_domicile
        response.volatility = details.volatility
        response.accumulating = details.accumulating
        response.source = "yfinance+justetf"
        return True

"""ISIN → Symbol/Börse-Auflösung.

Primär über OpenFIGI (bevorzugte Börse, z.B. Xetra → Suffix ``.DE``), Fallback
über die Yahoo-Finance-Suche (fängt US-Aktien u.a. ohne Xetra-Listing).

Das Yahoo-Suffix wählt die *Börse* — die *Währung* wird NICHT daraus abgeleitet,
sondern stammt immer aus dem Live-Quote (siehe yfinance_provider).
"""

import structlog
import yfinance as yf

from app.providers.base import QUOTE_TYPE_MAP, InstrumentResolver, ResolvedInstrument
from app.providers.openfigi_provider import OpenFigiClient

logger = structlog.get_logger()

# Bevorzugte Börse (MIC) → (Yahoo-Suffix, Anzeigename).
# MIC wird 1:1 als OpenFIGI micCode verwendet.
EXCHANGES: dict[str, tuple[str, str]] = {
    "XETR": (".DE", "Xetra"),
    "XFRA": (".F", "Frankfurt"),
    "XLON": (".L", "London"),
    "XMIL": (".MI", "Milan"),
    "XPAR": (".PA", "Paris"),
    "XAMS": (".AS", "Amsterdam"),
    "XSWX": (".SW", "SIX Swiss"),
    "XMAD": (".MC", "Madrid"),
    "XWBO": (".VI", "Vienna"),
    "XBRU": (".BR", "Brussels"),
}
DEFAULT_EXCHANGE = "XETR"


class OpenFigiResolver:
    """Löst ISINs über OpenFIGI zum Listing einer bevorzugten Börse auf."""

    def __init__(
        self, client: OpenFigiClient, default_exchange: str = DEFAULT_EXCHANGE
    ) -> None:
        """
        Args:
            client: OpenFIGI-Client für das ISIN→Ticker-Mapping.
            default_exchange: MIC der bevorzugten Börse (z.B. 'XETR').
        """
        self._client = client
        self._default_exchange = default_exchange

    def resolve_isin(self, isin: str) -> ResolvedInstrument | None:
        """Löst eine ISIN zum Yahoo-Symbol der bevorzugten Börse auf.

        Args:
            isin: ISIN des Wertpapiers.

        Returns:
            Aufgelöstes Instrument oder ``None``, wenn OpenFIGI kein Listing an
            der bevorzugten Börse kennt.
        """
        suffix, label = EXCHANGES.get(
            self._default_exchange, EXCHANGES[DEFAULT_EXCHANGE]
        )
        ticker = self._client.map_isin(isin, self._default_exchange)
        if not ticker:
            logger.warning(
                "openfigi_resolve_empty", isin=isin, exchange=self._default_exchange
            )
            return None
        return ResolvedInstrument(symbol=f"{ticker}{suffix}", isin=isin, exchange=label)


class YFinanceResolver:
    """Löst ISINs über die Yahoo-Finance-Suche auf (Fallback, v.a. US-Titel)."""

    def resolve_isin(self, isin: str) -> ResolvedInstrument | None:
        """Sucht das primäre Listing zu einer ISIN über Yahoo.

        Args:
            isin: ISIN des Wertpapiers.

        Returns:
            Aufgelöstes Instrument oder ``None``, wenn nichts gefunden wurde.
        """
        try:
            quotes = yf.Search(isin).quotes
        except Exception as exc:
            # Netzwerk/Parsing kann fehlschlagen — defensiv behandeln.
            logger.warning("resolve_isin_failed", isin=isin, error=str(exc))
            return None

        if not quotes:
            logger.warning("resolve_isin_empty", isin=isin)
            return None

        top = quotes[0]
        symbol = top.get("symbol")
        if not symbol:
            logger.warning("resolve_isin_no_symbol", isin=isin)
            return None

        quote_type = (top.get("quoteType") or "").upper()
        return ResolvedInstrument(
            symbol=symbol,
            isin=isin,
            exchange=top.get("exchDisp") or top.get("exchange"),
            name=top.get("shortname") or top.get("longname"),
            type=QUOTE_TYPE_MAP.get(quote_type),
            currency=None,  # Währung kommt aus dem Live-Quote, nicht aus der Suche
        )


class CompositeResolver:
    """Probiert mehrere Resolver der Reihe nach — erster Treffer gewinnt."""

    def __init__(self, *resolvers: InstrumentResolver) -> None:
        """
        Args:
            *resolvers: Resolver in Prioritätsreihenfolge.
        """
        self._resolvers = resolvers

    def resolve_isin(self, isin: str) -> ResolvedInstrument | None:
        """Gibt das erste erfolgreiche Auflösungsergebnis zurück."""
        for resolver in self._resolvers:
            result = resolver.resolve_isin(isin)
            if result is not None:
                return result
        return None

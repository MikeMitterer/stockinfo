"""Kursabfrage über yfinance (Yahoo Finance).

Nutzt ``fast_info`` für die robusten Kernwerte (Preis, Währung, Volumen) und
``get_info`` best-effort für Name und Kurszeitpunkt.
"""

from datetime import datetime, timezone
from typing import Any

import structlog
import yfinance as yf

from app.providers.base import RawQuote

logger = structlog.get_logger()

# Yahoo quoteType → interner Typ
_QUOTE_TYPE_MAP = {"ETF": "etf", "MUTUALFUND": "etf", "EQUITY": "stock"}


class YFinanceProvider:
    """Holt aktuellen Kurs und Metadaten eines Symbols von Yahoo Finance."""

    def fetch_quote(self, symbol: str) -> RawQuote | None:
        """Fragt den aktuellen Kurs eines Symbols ab.

        Args:
            symbol: Yahoo-Symbol, z.B. 'SAP.DE' oder 'AAPL'.

        Returns:
            RawQuote mit Kurs/Metadaten oder ``None`` bei Fehler bzw. fehlendem
            Kurs.
        """
        try:
            ticker = yf.Ticker(symbol)
            fast = ticker.fast_info
            price = self._fast_attr(fast, "last_price")
        except Exception as exc:
            logger.warning("fetch_quote_failed", symbol=symbol, error=str(exc))
            return None

        if price is None:
            logger.warning("fetch_quote_no_price", symbol=symbol)
            return None

        info = self._safe_info(ticker)
        quote_type = (self._fast_attr(fast, "quote_type") or "").upper()
        return RawQuote(
            symbol=symbol,
            price=float(price),
            quote_time=self._quote_time(info),
            currency=self._fast_attr(fast, "currency"),
            volume=self._as_int(self._fast_attr(fast, "last_volume")),
            name=info.get("longName") or info.get("shortName"),
            type=_QUOTE_TYPE_MAP.get(quote_type),
            exchange=self._fast_attr(fast, "exchange"),
            isin=self._safe_isin(ticker),
        )

    @staticmethod
    def _fast_attr(fast: Any, name: str) -> Any:
        """Liest ein FastInfo-Feld per Attribut-Zugriff; ``None`` bei Fehler.

        FastInfo liefert Werte nur über Attribute (snake_case), nicht über
        ``.get()`` mit snake_case-Keys.
        """
        try:
            return getattr(fast, name)
        except Exception:
            return None

    def _safe_info(self, ticker: Any) -> dict:
        """Liefert ``ticker.get_info()`` defensiv — leeres Dict bei Fehler."""
        try:
            return ticker.get_info() or {}
        except Exception as exc:
            logger.debug("get_info_failed", error=str(exc))
            return {}

    def _safe_isin(self, ticker: Any) -> str | None:
        """Liefert die ISIN defensiv; ``None`` bei Fehler oder Platzhalter '-'."""
        try:
            isin = ticker.isin
        except Exception:
            return None
        return isin if isin and isin != "-" else None

    @staticmethod
    def _quote_time(info: dict) -> str:
        """Bestimmt den Kurszeitpunkt aus ``info`` oder fällt auf 'jetzt' zurück."""
        epoch = info.get("regularMarketTime")
        if isinstance(epoch, (int, float)):
            return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _as_int(value: Any) -> int | None:
        """Konvertiert einen Wert defensiv nach int; ``None`` bei Fehler."""
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

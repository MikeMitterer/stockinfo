"""Langfrist-Historie — echte Tages-Schlusskurse (yfinance), inkrementell gecacht.

Die erste Anfrage holt die Historie von yfinance und legt sie in SQLite ab.
Folgende Anfragen liefern aus dem Cache und laden nur die Differenz (neue bzw.
fehlende Tage) nach — nicht jede Anfrage landet bei yfinance.
"""

from datetime import date, timedelta

import structlog

from app.models import DailyPoint
from app.repository import QuoteRepository
from app.services.daily_sync import DailyCloseProvider, DailyCloseSync
from app.services.quote_cache import CachedQuoteService
from app.services.quote_service import QuoteUnavailableError

logger = structlog.get_logger()

# Zeitraum-Kürzel → Anzahl Tage rückwärts ('max' = alles)
_PERIOD_DAYS = {"1w": 7, "1m": 31, "3m": 93, "1y": 366}


class DailyHistoryService:
    """Liefert Tages-Schlusskurse über einen Zeitraum, inkrementell gecacht."""

    def __init__(
        self,
        repository: QuoteRepository,
        provider: DailyCloseProvider,
        quotes: CachedQuoteService,
    ) -> None:
        """
        Args:
            repository: SQLite-Persistenz (daily_closes).
            provider: Quelle für echte EOD-Kurse (yfinance).
            quotes: Dienst, um ein Instrument bei Bedarf erst anzulegen.
        """
        self._repository = repository
        self._sync = DailyCloseSync(repository, provider)
        self._quotes = quotes

    def get_daily(
        self,
        *,
        isin: str | None = None,
        symbol: str | None = None,
        period: str = "1m",
    ) -> list[DailyPoint]:
        """Gibt die Tages-Schlusskurse für den Zeitraum zurück.

        Raises:
            QuoteUnavailableError: Instrument unbekannt und nicht beschaffbar,
                oder Erst-Abruf der Historie fehlgeschlagen.
        """
        instrument = self._quotes.ensure_instrument(isin=isin, symbol=symbol)
        desired_start = self._period_start(period)
        if not self._sync.sync(instrument["id"], instrument["symbol"], desired_start):
            raise QuoteUnavailableError(instrument["symbol"])
        rows = self._repository.get_daily_closes(instrument["id"], desired_start)
        return [
            DailyPoint(date=row["date"], close=row["close"], currency=row["currency"])
            for row in rows
        ]

    @staticmethod
    def _period_start(period: str) -> str | None:
        """Berechnet das Startdatum zu einem Zeitraum-Kürzel ('max' = None)."""
        if period == "max":
            return None
        days = _PERIOD_DAYS.get(period, 31)
        return (date.today() - timedelta(days=days)).isoformat()

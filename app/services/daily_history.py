"""Langfrist-Historie — echte Tages-Schlusskurse (yfinance), inkrementell gecacht.

Die erste Anfrage holt die Historie von yfinance und legt sie in SQLite ab.
Folgende Anfragen liefern aus dem Cache und laden nur die Differenz (neue bzw.
fehlende Tage) nach — nicht jede Anfrage landet bei yfinance.
"""

from datetime import date, timedelta
from typing import Protocol

import structlog

from app.models import DailyPoint
from app.repository import QuoteRepository
from app.services.quote_cache import CachedQuoteService
from app.services.quote_service import QuoteUnavailableError

logger = structlog.get_logger()

# Zeitraum-Kürzel → Anzahl Tage rückwärts ('max' = alles)
_PERIOD_DAYS = {"1w": 7, "1m": 31, "3m": 93, "1y": 366}


class DailyCloseProvider(Protocol):
    """Liefert echte Tages-Schlusskurse zu einem Symbol.

    ``None`` signalisiert einen Fehler (Netz, Rate-Limit); eine leere Liste
    bedeutet 'erfolgreich abgefragt, aber keine Daten vorhanden'.
    """

    def fetch_daily_closes(
        self, symbol: str, start: str | None = None
    ) -> list[dict] | None: ...


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
        self._provider = provider
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
        self._sync(instrument, desired_start)
        rows = self._repository.get_daily_closes(instrument["id"], desired_start)
        return [
            DailyPoint(date=row["date"], close=row["close"], currency=row["currency"])
            for row in rows
        ]

    def _sync(self, instrument: dict, desired_start: str | None) -> None:
        """Lädt nur fehlende Tage nach — anhand der Fetch-Wasserzeichen.

        ``fetched_to`` = bis wann bereits abgefragt, ``fetched_from`` = ab wann
        (``None`` = gesamte Historie). So wird nichts doppelt geholt, selbst wenn
        yfinance für ältere Zeiträume keine Daten mehr hat. Wasserzeichen werden
        nur nach einem **erfolgreichen** Fetch fortgeschrieben — ein
        Provider-Fehler hinterlässt keine dauerhafte Datenlücke.

        Raises:
            QuoteUnavailableError: Erst-Abruf fehlgeschlagen (kein Cache vorhanden).
        """
        instrument_id = instrument["id"]
        symbol = instrument["symbol"]
        today = date.today().isoformat()
        meta = self._repository.get_daily_meta(instrument_id)

        if meta is None:  # noch nie abgefragt → gesamten Zeitraum holen
            if not self._fetch_and_store(instrument_id, symbol, desired_start):
                raise QuoteUnavailableError(symbol)
            self._repository.set_daily_meta(instrument_id, desired_start, today)
            return

        fetched_from = meta["fetched_from"]
        fetched_to = meta["fetched_to"]

        if fetched_to is None or fetched_to < today:  # neue Tage seither
            if self._fetch_and_store(instrument_id, symbol, fetched_to):
                fetched_to = today

        if fetched_from is not None:  # gesamte Historie noch nicht geholt
            if desired_start is None:  # 'max' verlangt → alles holen
                if self._fetch_and_store(instrument_id, symbol, None):
                    fetched_from = None
            elif desired_start < fetched_from:  # weiter zurück verlangt
                if self._fetch_and_store(instrument_id, symbol, desired_start):
                    fetched_from = desired_start

        self._repository.set_daily_meta(instrument_id, fetched_from, fetched_to)

    def _fetch_and_store(
        self, instrument_id: int, symbol: str, start: str | None
    ) -> bool:
        """Holt EOD-Kurse ab ``start`` und schreibt sie in den Cache.

        Returns:
            True bei erfolgreichem Fetch (auch ohne neue Zeilen), False wenn
            der Provider einen Fehler signalisiert.
        """
        rows = self._provider.fetch_daily_closes(symbol, start=start)
        if rows is None:
            logger.warning("daily_sync_failed", symbol=symbol, start=start)
            return False
        self._repository.upsert_daily_closes(instrument_id, rows)
        logger.debug("daily_synced", symbol=symbol, start=start, rows=len(rows))
        return True

    @staticmethod
    def _period_start(period: str) -> str | None:
        """Berechnet das Startdatum zu einem Zeitraum-Kürzel ('max' = None)."""
        if period == "max":
            return None
        days = _PERIOD_DAYS.get(period, 31)
        return (date.today() - timedelta(days=days)).isoformat()

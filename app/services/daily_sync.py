"""Inkrementelle EOD-Synchronisation — gemeinsam genutzte Einheit.

Zieht fehlende Tages-Schlusskurse anhand der Fetch-Wasserzeichen nach und
speichert sie im akkumulierenden ``daily_closes``-Cache. Wird sowohl vom
``DailyHistoryService`` (Chart-Historie) als auch vom ``CachedQuoteService``
(Volatilität) verwendet — daher zustandslos und ohne Kenntnis der Aufrufer.
"""

from datetime import date
from typing import Protocol

import structlog

from app.repository import QuoteRepository

logger = structlog.get_logger()


class DailyCloseProvider(Protocol):
    """Liefert echte Tages-Schlusskurse zu einem Symbol.

    ``None`` signalisiert einen Fehler (Netz, Rate-Limit); eine leere Liste
    bedeutet 'erfolgreich abgefragt, aber keine Daten vorhanden'.
    """

    def fetch_daily_closes(
        self, symbol: str, start: str | None = None
    ) -> list[dict] | None: ...


class DailyCloseSync:
    """Synchronisiert den ``daily_closes``-Cache inkrementell (nur fehlende Tage)."""

    def __init__(self, repository: QuoteRepository, provider: DailyCloseProvider) -> None:
        """
        Args:
            repository: SQLite-Persistenz (daily_closes, daily_meta).
            provider: Quelle für echte EOD-Kurse (yfinance).
        """
        self._repository = repository
        self._provider = provider

    def sync(self, instrument_id: int, symbol: str, desired_start: str | None) -> bool:
        """Lädt nur fehlende Tage nach — anhand der Fetch-Wasserzeichen.

        ``fetched_to`` = bis wann bereits abgefragt, ``fetched_from`` = ab wann
        (``None`` = gesamte Historie). Wasserzeichen werden nur nach einem
        **erfolgreichen** Fetch fortgeschrieben — ein Provider-Fehler hinterlässt
        keine dauerhafte Datenlücke.

        Returns:
            ``False`` nur, wenn noch nie abgefragt wurde und der Erst-Fetch
            fehlschlägt (kein Cache vorhanden); sonst ``True``.
        """
        today = date.today().isoformat()
        meta = self._repository.get_daily_meta(instrument_id)

        if meta is None:  # noch nie abgefragt → gesamten Zeitraum holen
            if not self._fetch_and_store(instrument_id, symbol, desired_start):
                return False
            self._repository.set_daily_meta(instrument_id, desired_start, today)
            return True

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
        return True

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

"""Inkrementelle EOD-Synchronisation — gemeinsam genutzte Einheit.

Zieht fehlende Tages-Schlusskurse anhand der Fetch-Wasserzeichen nach und
speichert sie im akkumulierenden ``daily_closes``-Cache. Wird sowohl vom
``DailyHistoryService`` (Chart-Historie) als auch vom ``CachedQuoteService``
(Volatilität) verwendet — daher zustandslos und ohne Kenntnis der Aufrufer.
"""

from datetime import date

import structlog

from stockinfo_plugin.types import Identity

from app.providers.base import DailyCloseProvider, SourceAnswer
from app.repository import QuoteRepository

logger = structlog.get_logger()


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

    def sync(
        self,
        instrument_id: int,
        symbol: str,
        desired_start: str | None,
        *,
        identity: Identity | None = None,
        instrument_type: str | None = None,
    ) -> SourceAnswer[bool]:
        """Lädt nur fehlende Tage nach — anhand der Fetch-Wasserzeichen.

        ``fetched_to`` = bis wann bereits abgefragt, ``fetched_from`` = ab wann
        (``None`` = gesamte Historie). Wasserzeichen werden nur nach einem
        **erfolgreichen** Fetch fortgeschrieben — ein Provider-Fehler hinterlässt
        keine dauerhafte Datenlücke.

        Returns:
            ``value=True``, sobald etwas Verwertbares vorliegt. Ohne Wert ist
            der Erst-Fetch fehlgeschlagen und es gibt keinen Cache — dann sagt
            `disturbed`, ob eine Quelle **gestört** war oder ob schlicht keine
            diese Reihe führt. Der Router macht daraus `502` oder `404`.
        """
        today = date.today().isoformat()
        meta = self._repository.get_daily_meta(instrument_id)

        if meta is None:  # noch nie abgefragt → gesamten Zeitraum holen
            first = self._fetch_and_store(
                instrument_id, symbol, desired_start, identity, instrument_type
            )
            if not first.is_hit:
                return SourceAnswer(disturbed=first.disturbed)
            self._repository.set_daily_meta(instrument_id, desired_start, today)
            return SourceAnswer(True)

        fetched_from = meta["fetched_from"]
        fetched_to = meta["fetched_to"]

        if fetched_to is None or fetched_to < today:  # neue Tage seither
            if self._fetch_and_store(
                instrument_id, symbol, fetched_to, identity, instrument_type
            ).is_hit:
                fetched_to = today

        if fetched_from is not None:  # gesamte Historie noch nicht geholt
            if desired_start is None:  # 'max' verlangt → alles holen
                if self._fetch_and_store(
                    instrument_id, symbol, None, identity, instrument_type
                ).is_hit:
                    fetched_from = None
            elif desired_start < fetched_from:  # weiter zurück verlangt
                if self._fetch_and_store(
                    instrument_id, symbol, desired_start, identity, instrument_type
                ).is_hit:
                    fetched_from = desired_start

        self._repository.set_daily_meta(instrument_id, fetched_from, fetched_to)
        # **Ein Wasserzeichen liegt vor.** Was danach fehlschlägt, kostet
        # frische Tage, nicht die Auskunft: Der gespeicherte Stand bleibt eine
        # Antwort, und der Aufrufer bekommt sie.
        return SourceAnswer(True)

    def _fetch_and_store(
        self,
        instrument_id: int,
        symbol: str,
        start: str | None,
        identity: Identity | None = None,
        instrument_type: str | None = None,
    ) -> SourceAnswer[bool]:
        """Holt EOD-Kurse ab ``start`` und schreibt sie in den Cache.

        Returns:
            ``value=True`` bei erfolgreichem Fetch, auch ohne neue Zeilen.
            Ohne Wert hat keine Quelle geliefert; `disturbed` reicht dabei
            durch, ob das eine Störung war.
        """
        # **Die Identität wird durchgereicht, nicht zurückgerechnet.** Ein
        # Symbol ohne Suffix — `AAPL` — gehört zu einer der fünf US-Börsen, die
        # absichtlich keinen Alias führen; aus ihm die Börse zu erraten ginge
        # nicht, und der Versuch hat in Runde 3 alle aliaslosen Plätze still
        # abgeschaltet: null Provider-Aufrufe, `None` als Ergebnis.
        answer = self._provider.fetch_daily_closes(
            symbol, start=start, identity=identity, instrument_type=instrument_type
        )
        if not answer.is_hit:
            logger.warning(
                "daily_sync_failed",
                symbol=symbol,
                start=start,
                disturbed=answer.disturbed,
            )
            return SourceAnswer(disturbed=answer.disturbed)
        rows = answer.value or []
        self._repository.upsert_daily_closes(instrument_id, rows)
        logger.debug("daily_synced", symbol=symbol, start=start, rows=len(rows))
        return SourceAnswer(True)

"""Cachende Kurs-Beschaffung — Lazy-TTL über dem QuoteService.

Bei einer Anfrage wird der Cache genutzt, solange der letzte Kurs jünger als
die TTL ist; sonst wird frisch beschafft und gespeichert. Schlägt eine frische
Beschaffung fehl, aber es liegt ein alter Wert vor, wird dieser als ``stale``
zurückgegeben statt eines Fehlers.
"""

from datetime import datetime, timezone

import structlog

from app.models import QuotePoint, QuoteResponse
from app.repository import QuoteRepository
from app.services.quote_service import QuoteService, QuoteUnavailableError

logger = structlog.get_logger()


class CachedQuoteService:
    """Legt einen TTL-Cache (SQLite) vor die Live-Kursbeschaffung."""

    def __init__(
        self,
        quote_service: QuoteService,
        repository: QuoteRepository,
        ttl_hours: int,
    ) -> None:
        """
        Args:
            quote_service: Live-Beschaffung (yfinance + justETF).
            repository: SQLite-Persistenz für Cache und Historie.
            ttl_hours: Maximales Alter eines Kurses, bevor neu beschafft wird.
        """
        self._quote_service = quote_service
        self._repository = repository
        self._ttl_hours = ttl_hours

    def get_by_isin(self, isin: str) -> QuoteResponse:
        """Liefert den Kurs zu einer ISIN aus Cache oder frisch beschafft.

        Raises:
            InstrumentNotFoundError: ISIN nicht auflösbar.
            QuoteUnavailableError: Kein Kurs beschaffbar und kein Cache vorhanden.
        """
        instrument = self._repository.get_instrument_by_isin(isin)
        return self._get(
            instrument, lambda: self._quote_service.get_quote_by_isin(isin)
        )

    def get_by_symbol(self, symbol: str) -> QuoteResponse:
        """Liefert den Kurs zu einem Yahoo-Symbol aus Cache oder frisch beschafft.

        Raises:
            QuoteUnavailableError: Kein Kurs beschaffbar und kein Cache vorhanden.
        """
        instrument = self._repository.get_instrument_by_symbol(symbol)
        return self._get(
            instrument, lambda: self._quote_service.get_quote_by_symbol(symbol)
        )

    def get_history(
        self,
        isin: str,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 100,
    ) -> list[QuotePoint]:
        """Gibt die Kurs-Historie zu einer ISIN zurück.

        Stellt sicher, dass das Instrument bekannt ist (beschafft es sonst
        einmalig), und liefert dann die gespeicherten Kurspunkte.

        Raises:
            InstrumentNotFoundError: ISIN nicht auflösbar.
            QuoteUnavailableError: Instrument unbekannt und nicht beschaffbar.
        """
        instrument = self._repository.get_instrument_by_isin(isin)
        if instrument is None:
            self.get_by_isin(isin)  # legt Instrument + ersten Punkt an
            instrument = self._repository.get_instrument_by_isin(isin)
        if instrument is None:
            raise QuoteUnavailableError(isin)

        rows = self._repository.get_history(instrument["id"], date_from, date_to, limit)
        return self._to_points(rows)

    def get_history_by_symbol(
        self,
        symbol: str,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 100,
    ) -> list[QuotePoint]:
        """Gibt die Kurs-Historie zu einem Symbol zurück (für Papiere ohne ISIN).

        Raises:
            QuoteUnavailableError: Instrument unbekannt und nicht beschaffbar.
        """
        instrument = self._repository.get_instrument_by_symbol(symbol)
        if instrument is None:
            self.get_by_symbol(symbol)  # legt Instrument + ersten Punkt an
            instrument = self._repository.get_instrument_by_symbol(symbol)
        if instrument is None:
            raise QuoteUnavailableError(symbol)

        rows = self._repository.get_history(instrument["id"], date_from, date_to, limit)
        return self._to_points(rows)

    @staticmethod
    def _to_points(rows: list[dict]) -> list[QuotePoint]:
        """Wandelt Quote-Zeilen in QuotePoint-Modelle um."""
        return [
            QuotePoint(
                price=row["price"],
                quote_time=row["quote_time"],
                volume=row["volume"],
                currency=row["currency"],
                fetched_at=row["fetched_at"],
            )
            for row in rows
        ]

    def refresh_all(self) -> int:
        """Aktualisiert alle bekannten Instrumente live und speichert sie.

        Wird vom Hintergrund-Scheduler aufgerufen. Umgeht die TTL bewusst. Ein
        Fehler bei einem Instrument beendet den Lauf nicht.

        Returns:
            Anzahl erfolgreich aktualisierter Instrumente.
        """
        instruments = self._repository.list_instruments()
        refreshed = 0
        for instrument in instruments:
            try:
                fresh = self._fetch_live(instrument)
                self._repository.save_quote(fresh)
                refreshed += 1
            except Exception as exc:
                logger.warning(
                    "refresh_failed",
                    isin=instrument.get("isin"),
                    symbol=instrument.get("symbol"),
                    error=str(exc),
                )
        logger.info("refresh_completed", total=len(instruments), refreshed=refreshed)
        return refreshed

    def refresh_one(self, isin: str) -> QuoteResponse:
        """Aktualisiert ein einzelnes Instrument per ISIN live und speichert es.

        Umgeht die TTL bewusst.

        Raises:
            InstrumentNotFoundError: ISIN nicht auflösbar.
            QuoteUnavailableError: Kein Kurs beschaffbar.
        """
        fresh = self._quote_service.get_quote_by_isin(isin)
        self._repository.save_quote(fresh)
        return fresh

    def refresh_one_by_symbol(self, symbol: str) -> QuoteResponse:
        """Aktualisiert ein Instrument per Symbol live (für Papiere ohne ISIN).

        Raises:
            QuoteUnavailableError: Kein Kurs beschaffbar.
        """
        fresh = self._quote_service.get_quote_by_symbol(symbol)
        self._repository.save_quote(fresh)
        return fresh

    def list_instruments(self) -> list[dict]:
        """Gibt alle Instrumente inkl. letztem Kurs zurück (für das Dashboard)."""
        return self._repository.list_instruments_with_latest()

    def count_instruments(self) -> int:
        """Gibt die Anzahl bekannter Instrumente zurück."""
        return self._repository.count_instruments()

    def delete_instrument(self, isin: str) -> bool:
        """Löscht ein Instrument samt Historie per ISIN; True bei Erfolg."""
        return self._repository.delete_instrument(isin)

    def delete_by_symbol(self, symbol: str) -> bool:
        """Löscht ein Instrument samt Historie per Symbol; True bei Erfolg."""
        return self._repository.delete_by_symbol(symbol)

    def _fetch_live(self, instrument: dict) -> QuoteResponse:
        """Beschafft einen frischen Kurs für ein bekanntes Instrument (ohne Cache)."""
        isin = instrument.get("isin")
        if isin:
            return self._quote_service.get_quote_by_isin(isin)
        return self._quote_service.get_quote_by_symbol(instrument["symbol"])

    def _get(self, instrument: dict | None, fetch) -> QuoteResponse:
        """Gemeinsame Cache-Logik: frischer Cache → nutzen, sonst neu beschaffen.

        Args:
            instrument: Bereits bekanntes Instrument-Dict (oder None).
            fetch: Callable, das den Kurs live beschafft.

        Returns:
            Kurs-Antwort (aus Cache, frisch oder stale bei Fehler).
        """
        latest = (
            self._repository.get_latest_quote(instrument["id"]) if instrument else None
        )
        if instrument and latest and self._is_fresh(latest["fetched_at"]):
            return self._from_cache(instrument, latest, stale=False)

        try:
            fresh = fetch()
        except QuoteUnavailableError:
            if instrument and latest:
                logger.warning("serving_stale_quote", isin=instrument.get("isin"))
                return self._from_cache(instrument, latest, stale=True)
            raise

        self._repository.save_quote(fresh)
        return fresh

    def _is_fresh(self, fetched_at: str) -> bool:
        """Prüft, ob ein Zeitstempel jünger als die TTL ist."""
        try:
            timestamp = datetime.fromisoformat(fetched_at)
        except ValueError:
            return False
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        age_seconds = (datetime.now(timezone.utc) - timestamp).total_seconds()
        return age_seconds < self._ttl_hours * 3600

    @staticmethod
    def _from_cache(instrument: dict, quote: dict, stale: bool) -> QuoteResponse:
        """Baut eine QuoteResponse aus gespeichertem Instrument + Kurspunkt."""
        return QuoteResponse(
            isin=instrument["isin"],
            symbol=instrument["symbol"],
            exchange=instrument["exchange"],
            name=instrument["name"],
            type=instrument["type"],
            currency=quote["currency"] or instrument["currency"],
            price=quote["price"],
            quote_time=quote["quote_time"],
            volume=quote["volume"],
            ter=instrument["ter"],
            provider=instrument["provider"],
            replication=instrument["replication"],
            fund_size=instrument["fund_size"],
            source="cache",
            cached=True,
            stale=stale,
            fetched_at=quote["fetched_at"],
        )

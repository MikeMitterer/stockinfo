"""Cachende Kurs-Beschaffung — Lazy-TTL über dem QuoteService.

Bei einer Anfrage wird der Cache genutzt, solange der letzte Kurs jünger als
die TTL ist; sonst wird frisch beschafft und gespeichert. Schlägt eine frische
Beschaffung fehl, aber es liegt ein alter Wert vor, wird dieser als ``stale``
zurückgegeben statt eines Fehlers.
"""

import threading
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import structlog

from app.models import OVERRIDE_FIELDS, QuotePoint, QuoteResponse
from app.repository import QuoteRepository
from app.services.daily_sync import DailyCloseSync
from app.services.freshness import is_fresh
from app.services.quote_service import (
    InstrumentNotFoundError,
    QuoteService,
    QuoteUnavailableError,
    annualized_volatility,
)

logger = structlog.get_logger()


def _as_bool(value: object) -> bool | None:
    """Wandelt einen gespeicherten Integer/None in ``bool | None`` um."""
    return None if value is None else bool(value)


def apply_overrides(row: dict) -> dict:
    """Legt die manuellen Kennzahlen über die der Quelle — **nur in Lücken**.

    Die Regel in einem Satz: *Was die Quelle liefert, gewinnt; ein manueller
    Wert füllt nur, was leer bleibt.* Damit kann eine spätere Lieferung von
    justETF/extraETF eine Eingabe nie dauerhaft ersetzen — sie verdeckt sie nur,
    solange sie etwas zu sagen hat.

    Verdecken darf aber nicht stillschweigend passieren: Wer einen Wert
    eingetragen hat und plötzlich einen anderen sieht, muss erfahren, warum.
    Deshalb zwei Listen statt eines stillen Ergebnisses:

    * ``manual_fields`` — hier kommt der angezeigte Wert gerade von Hand.
    * ``shadowed_fields`` — hier liegt ein manueller Wert, den die Quelle
      gerade überstimmt. Der rohe Wert steht in ``manual_<feld>``, damit die
      Oberfläche ihn im Hinweis nennen kann.

    Der Sonderfall ``accumulating``: Es ist ein Wahrheitswert, und ``False``
    („ausschüttend") ist eine Aussage, keine Lücke. Geprüft wird deshalb auf
    ``None``, nicht auf Falschheit — sonst hätte „ausschüttend" nie Bestand.

    Args:
        row: Zeile aus ``list_instruments_with_latest`` samt ``manual_*``.

    Returns:
        Dieselbe Zeile mit wirksamen Werten und den beiden Listen.
    """
    result = dict(row)
    manual_fields: list[str] = []
    shadowed_fields: list[str] = []

    for feld in OVERRIDE_FIELDS:
        manuell = result.get(f"manual_{feld}")
        if feld == "accumulating":
            manuell = _as_bool(manuell)
            result["manual_accumulating"] = manuell
        if manuell is None:
            continue

        if result.get(feld) is None:
            result[feld] = manuell
            manual_fields.append(feld)
        else:
            shadowed_fields.append(feld)

    result["manual_fields"] = manual_fields
    result["shadowed_fields"] = shadowed_fields
    return result


class IsinConflictError(Exception):
    """Die ISIN ist bereits einem anderen Instrument zugeordnet."""


class RefreshInProgressError(Exception):
    """Ein ``refresh_all``-Lauf ist bereits aktiv (Scheduler oder Request)."""


class CachedQuoteService:
    """Legt einen TTL-Cache (SQLite) vor die Live-Kursbeschaffung."""

    def __init__(
        self,
        quote_service: QuoteService,
        repository: QuoteRepository,
        ttl_hours: int,
        daily_sync: DailyCloseSync,
    ) -> None:
        """
        Args:
            quote_service: Live-Beschaffung (yfinance + justETF).
            repository: SQLite-Persistenz für Cache und Historie.
            ttl_hours: Maximales Alter eines Kurses, bevor neu beschafft wird.
            daily_sync: Inkrementelle EOD-Synchronisation für den akkumulierenden
                Tages-Cache, aus dem die Volatilität berechnet wird.
        """
        self._quote_service = quote_service
        self._repository = repository
        self._ttl_hours = ttl_hours
        self._daily_sync = daily_sync
        self._refresh_lock = threading.Lock()

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
        instrument = self.ensure_instrument(isin=isin)
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
        instrument = self.ensure_instrument(symbol=symbol)
        rows = self._repository.get_history(instrument["id"], date_from, date_to, limit)
        return self._to_points(rows)

    def ensure_instrument(
        self, *, isin: str | None = None, symbol: str | None = None
    ) -> dict:
        """Holt das Instrument aus der DB oder legt es einmalig per Live-Fetch an.

        Args:
            isin: ISIN des Wertpapiers (bevorzugt).
            symbol: Yahoo-Symbol (für Papiere ohne ISIN).

        Returns:
            Das Instrument-Dict aus der Datenbank.

        Raises:
            InstrumentNotFoundError: ISIN nicht auflösbar.
            QuoteUnavailableError: Instrument unbekannt und nicht beschaffbar.
        """
        if isin:
            instrument = self._repository.get_instrument_by_isin(isin)
            if instrument is None:
                self.get_by_isin(isin)  # legt Instrument + ersten Punkt an
                instrument = self._repository.get_instrument_by_isin(isin)
        elif symbol:
            instrument = self._repository.get_instrument_by_symbol(symbol)
            if instrument is None:
                self.get_by_symbol(symbol)  # legt Instrument + ersten Punkt an
                instrument = self._repository.get_instrument_by_symbol(symbol)
        else:
            instrument = None
        if instrument is None:
            raise QuoteUnavailableError(isin or symbol or "")
        return instrument

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

        Wird vom Hintergrund-Scheduler und vom Dashboard aufgerufen. Umgeht die
        TTL bewusst. Ein Fehler bei einem Instrument beendet den Lauf nicht.
        Es läuft immer nur ein Lauf gleichzeitig.

        Returns:
            Anzahl erfolgreich aktualisierter Instrumente.

        Raises:
            RefreshInProgressError: Ein anderer Lauf ist bereits aktiv.
        """
        if not self._refresh_lock.acquire(blocking=False):
            raise RefreshInProgressError()
        try:
            return self._refresh_all_locked()
        finally:
            self._refresh_lock.release()

    def _refresh_all_locked(self) -> int:
        """Führt den eigentlichen Refresh-Lauf aus (Lock wird vom Aufrufer gehalten)."""
        instruments = self._repository.list_instruments()
        refreshed = 0
        for instrument in instruments:
            try:
                self._save_fresh_with_volatility(self._fetch_live(instrument))
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
        return self._save_fresh_with_volatility(self._quote_service.get_quote_by_isin(isin))

    def refresh_one_by_symbol(self, symbol: str) -> QuoteResponse:
        """Aktualisiert ein Instrument per Symbol live (für Papiere ohne ISIN).

        Raises:
            QuoteUnavailableError: Kein Kurs beschaffbar.
        """
        return self._save_fresh_with_volatility(
            self._quote_service.get_quote_by_symbol(symbol)
        )

    def _with_overrides(
        self, response: QuoteResponse, instrument_id: int | None = None
    ) -> QuoteResponse:
        """Legt die von Hand gepflegten Kennzahlen über eine Kurs-Antwort.

        Die Vorrang-Regel galt bis dahin nur in der Instrumentenliste. Wer
        dieselbe Kennzahl über ``/quote`` abfragte — das JSON-Fenster der
        Oberfläche, Excel über Power Query, jedes Skript — bekam den rohen Wert
        der Quelle und damit ein „nicht gesetzt", obwohl etwas eingetragen war.

        Gerechnet wird mit :func:`apply_overrides` und nicht mit einer zweiten
        Fassung derselben Regel: Zwei Stellen liefen sonst früher oder später
        auseinander, und die Antwort widerspräche der Liste daneben.

        Geschrieben wird dabei nichts — die Instrumentenzeile bleibt roh, damit
        der nächste Refresh weiterhin nichts zu überschreiben findet.

        Args:
            response: Antwort mit den Werten der Quelle.
            instrument_id: Bereits bekannte Id; sonst wird sie nachgeschlagen.

        Returns:
            Dieselbe Antwort, in deren Lücken die manuellen Werte stehen.
        """
        if instrument_id is None:
            instrument = (
                self._repository.get_instrument_by_isin(response.isin)
                if response.isin
                else self._repository.get_instrument_by_symbol(response.symbol)
            )
            if instrument is None:
                return response
            instrument_id = instrument["id"]

        overrides = self._repository.get_overrides(instrument_id)
        if overrides is None:
            return response

        zeile = apply_overrides(
            {
                **{feld: getattr(response, feld) for feld in OVERRIDE_FIELDS},
                **{f"manual_{feld}": overrides[feld] for feld in OVERRIDE_FIELDS},
            }
        )
        for feld in OVERRIDE_FIELDS:
            setattr(response, feld, zeile[feld])
        return response

    def _save_fresh(self, fresh: QuoteResponse) -> QuoteResponse:
        """Persistiert einen frisch beschafften Kurs und reicht ihn durch."""
        self._repository.save_quote(fresh)
        return self._with_overrides(fresh)

    def _save_fresh_with_volatility(self, fresh: QuoteResponse) -> QuoteResponse:
        """Persistiert einen frischen Kurs und ergänzt die Volatilität aus dem Cache.

        Nur wenn der Kurs selbst keine Volatilität mitbringt (justETF liefert für
        ETFs bereits eine — die bleibt bevorzugt). Wird ausschließlich im
        Refresh-Pfad aufgerufen, damit der lesende Request-Pfad schlank bleibt.

        Schlägt die Neuberechnung fehl (leerer EOD-Cache und toter Delta-Fetch),
        wird der zuvor gespeicherte Wert wiederhergestellt statt ihn mit ``None``
        zu überschreiben — behält den letzten bekannten Wert.
        """
        previous_volatility = self._stored_volatility(fresh)
        instrument_id = self._repository.save_quote(fresh)
        if fresh.volatility is None:
            volatility = self._volatility_from_cache(instrument_id, fresh.symbol)
            if volatility is not None:
                fresh.volatility = volatility
                self._repository.set_volatility(instrument_id, volatility)
            elif previous_volatility is not None:
                fresh.volatility = previous_volatility
                self._repository.set_volatility(instrument_id, previous_volatility)
        return self._with_overrides(fresh, instrument_id)

    def _stored_volatility(self, fresh: QuoteResponse) -> float | None:
        """Liest die aktuell gespeicherte Volatilität, bevor ``save_quote`` sie überschreibt."""
        instrument = (
            self._repository.get_instrument_by_isin(fresh.isin)
            if fresh.isin
            else self._repository.get_instrument_by_symbol(fresh.symbol)
        )
        return instrument["volatility"] if instrument else None

    def _volatility_from_cache(self, instrument_id: int, symbol: str) -> float | None:
        """Berechnet die 1-Jahres-Volatilität aus dem akkumulierenden EOD-Cache.

        Zieht zunächst das Delta nach (nur fehlende Tage) und rechnet dann über
        die letzten ~370 Tage. Best-effort: fehlende/zu wenige Daten → ``None``.
        """
        start = (datetime.now(timezone.utc).date() - timedelta(days=370)).isoformat()
        self._daily_sync.sync(instrument_id, symbol, start)
        rows = self._repository.get_daily_closes(instrument_id, start)
        closes = [row["close"] for row in rows if row.get("close") is not None]
        return annualized_volatility(closes)

    def list_instruments(self) -> list[dict]:
        """Gibt alle Instrumente inkl. letztem Kurs und wirksamer Kennzahlen zurück."""
        return [apply_overrides(row) for row in self._repository.list_instruments_with_latest()]

    def get_overrides(self, symbol: str) -> dict:
        """Gibt die von Hand gepflegten Kennzahlen eines Instruments zurück.

        Raises:
            InstrumentNotFoundError: Symbol unbekannt.
        """
        instrument = self._require_instrument(symbol)
        stored = self._repository.get_overrides(instrument["id"]) or {}
        return {
            "ter": stored.get("ter"),
            "volatility": stored.get("volatility"),
            "accumulating": _as_bool(stored.get("accumulating")),
        }

    def set_overrides(
        self,
        symbol: str,
        ter: float | None,
        volatility: float | None,
        accumulating: bool | None,
    ) -> dict:
        """Schreibt die manuellen Kennzahlen eines Instruments und gibt sie zurück.

        Alle drei Werte auf einmal — ``None`` löscht. Die Vorrang-Regel wird
        hier **nicht** angewandt: Gespeichert wird, was der Nutzer eingetragen
        hat, auch wenn die Quelle den Wert gerade verdeckt. Sonst verschwände
        seine Eingabe in dem Moment, in dem die Quelle wieder etwas liefert —
        und käme nicht zurück, wenn sie es später wieder vergisst.

        Raises:
            InstrumentNotFoundError: Symbol unbekannt.
        """
        instrument = self._require_instrument(symbol)
        self._repository.set_overrides(
            instrument["id"],
            ter,
            volatility,
            accumulating,
            datetime.now(timezone.utc).isoformat(),
        )
        return self.get_overrides(symbol)

    def _require_instrument(self, symbol: str) -> dict:
        """Holt ein Instrument per Symbol oder wirft."""
        instrument = self._repository.get_instrument_by_symbol(symbol)
        if instrument is None:
            raise InstrumentNotFoundError(symbol)
        return instrument

    def count_instruments(self) -> int:
        """Gibt die Anzahl bekannter Instrumente zurück."""
        return self._repository.count_instruments()

    def delete_instrument(self, isin: str) -> bool:
        """Löscht ein Instrument samt Historie per ISIN; True bei Erfolg."""
        return self._repository.delete_instrument(isin)

    def delete_by_symbol(self, symbol: str) -> bool:
        """Löscht ein Instrument samt Historie per Symbol; True bei Erfolg."""
        return self._repository.delete_by_symbol(symbol)

    def set_isin(self, symbol: str, isin: str) -> None:
        """Trägt die ISIN eines Instruments nach (per Symbol).

        Raises:
            InstrumentNotFoundError: Symbol unbekannt.
            IsinConflictError: ISIN bereits einem anderen Instrument zugeordnet.
        """
        if self._repository.get_instrument_by_symbol(symbol) is None:
            raise InstrumentNotFoundError(symbol)
        existing = self._repository.get_instrument_by_isin(isin)
        if existing is not None and existing["symbol"] != symbol:
            raise IsinConflictError(isin)
        self._repository.set_isin(symbol, isin)

    def _fetch_live(self, instrument: dict) -> QuoteResponse:
        """Beschafft einen frischen Kurs für ein bekanntes Instrument (ohne Cache)."""
        isin = instrument.get("isin")
        if isin:
            return self._quote_service.get_quote_by_isin(isin)
        return self._quote_service.get_quote_by_symbol(instrument["symbol"])

    def _get(
        self, instrument: dict | None, fetch: Callable[[], QuoteResponse]
    ) -> QuoteResponse:
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
        if instrument and latest and is_fresh(latest["fetched_at"], self._ttl_hours):
            return self._with_overrides(
                self._from_cache(instrument, latest, stale=False), instrument["id"]
            )

        try:
            fresh = fetch()
        except (QuoteUnavailableError, InstrumentNotFoundError):
            # Auch ein Resolver-Ausfall (InstrumentNotFoundError) darf einen
            # vorhandenen Cache-Wert nicht in einen Fehler verwandeln.
            if instrument and latest:
                logger.warning("serving_stale_quote", isin=instrument.get("isin"))
                return self._with_overrides(
                    self._from_cache(instrument, latest, stale=True), instrument["id"]
                )
            raise

        return self._save_fresh(fresh)

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
            volatility=instrument["volatility"],
            accumulating=_as_bool(instrument["accumulating"]),
            source="cache",
            cached=True,
            stale=stale,
            fetched_at=quote["fetched_at"],
        )

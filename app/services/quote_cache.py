"""Cachende Kurs-Beschaffung — Lazy-TTL über dem QuoteService.

Bei einer Anfrage wird der Cache genutzt, solange der letzte Kurs jünger als
die TTL ist; sonst wird frisch beschafft und gespeichert. Schlägt eine frische
Beschaffung fehl, aber es liegt ein alter Wert vor, wird dieser als ``stale``
zurückgegeben statt eines Fehlers.
"""

import threading

from app.details import CANONICAL, merge_value, validate_input
from app.detail_models import DetailInput, DetailValue
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import structlog

from app.models import (
    OVERRIDE_FIELDS,
    ListedIdentityOut,
    QuotePoint,
    QuoteResponse,
    identity_columns,
    identity_from_columns,
    with_identity,
)
from app.providers.base import identity_from_row
from app.repository import PROTECTED_META_FIELDS, QuoteRepository
from app.services.daily_sync import DailyCloseSync
from app.services.freshness import is_fresh
from app.services.quote_service import (
    InstrumentNotFoundError,
    PrecheckedCoreValues,
    QuoteService,
    QuoteUnavailableError,
    annualized_volatility,
    ensure_core_complete,
    require_core_values,
)

logger = structlog.get_logger()


@dataclass(frozen=True)
class StoredQuote:
    """Eine Kurs-Antwort und ob das Instrument dabei **entstanden** ist.

    Der Aufnahmeweg (T-21 Teil 3) muss `201` von `200` unterscheiden, und die
    Antwort darauf entsteht in der schreibenden Transaktion des Repositories —
    nicht in einer Vorabfrage, die ein konkurrierender Insert überholen kann.
    Damit sie oben ankommt, reicht dieser Typ sie durch die Cache-Schicht.

    `created` ist **falsch**, wenn der Cache die Antwort bedient hat: Dann gab
    es das Papier schon, und geschrieben wurde gar nichts.

    Die `instrument_id` reist mit, weil der Aufnahmeweg danach die gespeicherte
    Zeile ausliefert. Sie über `isin` oder `symbol` erneut zu suchen wäre eine
    zweite Abfrage auf eine Zeile, die gerade eben in der Hand lag — und bei
    einem Papier ohne ISIN sogar eine mehrdeutige.
    """

    quote: QuoteResponse | None
    created: bool
    instrument_id: int


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

    for field in OVERRIDE_FIELDS:
        manual = result.get(f'manual_{field}')
        provider = result.get(field)
        if field == 'accumulating':
            manual = _as_bool(manual)
            provider = _as_bool(provider)
        merged = merge_value({'value': provider}, {'value': manual}, CANONICAL[field][1])
        result[field] = merged.value
        result[f'manual_{field}'] = merged.manual_value
        if merged.origin == 'manual':
            manual_fields.append(field)
        if merged.shadowed:
            shadowed_fields.append(field)

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
        metadata_ttl_days: int = 7,
    ) -> None:
        """
        Args:
            quote_service: Live-Beschaffung (yfinance + justETF).
            repository: SQLite-Persistenz für Cache und Historie.
            ttl_hours: Maximales Alter eines Kurses, bevor neu beschafft wird.
            daily_sync: Inkrementelle EOD-Synchronisation für den akkumulierenden
                Tages-Cache, aus dem die Volatilität berechnet wird.
            metadata_ttl_days: Maximales Alter der ETF-Kennzahlen, bevor justETF
                erneut gefragt wird. Kurse und Kennzahlen altern verschieden
                schnell: Ein Kurs ist nach Stunden veraltet, ein Fondsdomizil
                ändert sich in Jahren nicht. Der Vorgabewert entspricht
                `Settings.metadata_ttl_days`.
        """
        self._quote_service = quote_service
        self._repository = repository
        self._ttl_hours = ttl_hours
        self._metadata_ttl_days = metadata_ttl_days
        self._daily_sync = daily_sync
        self._refresh_lock = threading.Lock()

    def get_by_isin(self, isin: str) -> QuoteResponse:
        """Liefert den Kurs zu einer ISIN aus Cache oder frisch beschafft.

        Ein bekanntes Papier wird über sein gespeichertes Listing aufgefrischt
        (`_fetch_live`), nicht neu aufgelöst — sonst wandert es beim schlichten
        Nachschlagen die Börse, und weil `_get` das Ergebnis speichert, bleibt
        die falsche stehen. Das ist derselbe Schutz wie in `refresh_one`, nur
        auf dem meistgenutzten Endpunkt.

        Raises:
            InstrumentNotFoundError: ISIN nicht auflösbar.
            QuoteUnavailableError: Kein Kurs beschaffbar und kein Cache vorhanden.
        """
        return self.store_by_isin(isin).quote

    def store_by_isin(self, isin: str) -> StoredQuote:
        """Wie `get_by_isin`, sagt aber zusätzlich, ob das Papier entstanden ist.

        **Ein Weg, zwei Sichten** — kein Zwilling: `get_by_isin` ist die
        schmale Antwort für den Kursendpunkt, der die Unterscheidung nicht
        braucht; der Aufnahmeweg braucht sie, weil `201` und `200`
        auseinandergehalten werden müssen. Beide laufen durch **diesen** Rumpf.
        """
        instrument = self._repository.get_instrument_by_isin(isin)
        if instrument:
            return self._get(instrument, lambda: self._fetch_live(instrument))
        return self._get(
            None, lambda: self._quote_service.get_quote_by_isin(isin, enrich_etf=True)
        )

    def get_by_symbol(self, symbol: str) -> QuoteResponse:
        """Liefert den Kurs zu einem Yahoo-Symbol aus Cache oder frisch beschafft.

        Bekanntes Papier ohne erneute Auflösung — die Begründung steht bei
        `get_by_isin`.

        Raises:
            QuoteUnavailableError: Kein Kurs beschaffbar und kein Cache vorhanden.
        """
        return self.store_by_symbol(symbol).quote

    def store_by_identity(self, ticker: str, mic: str) -> StoredQuote:
        """Der Weg des Aufnahmewegs — über die **kanonische Identität**.

        Nicht über das Symbol, und das ist der ganze Punkt: `AAPL.XNAS` und
        `AAPL.XNYS` tragen denselben Abrufalias `AAPL`, weil die US-Plätze
        keinen Suffix führen. Ein Nachschlagen über `symbol` fände deshalb
        entweder die falsche Börse — dieselbe Eingabe antwortete dann mit dem
        anderen Handelsplatz, als der Benutzer genannt hat — oder auf leerem
        Bestand gar nichts, und der mehrdeutige Auflösungsweg übernähme.

        Die genannte Börse bleibt deshalb bis zur Speicherung erhalten: Das
        Nachschlagen läuft über `(ticker, mic)`, und der frische Abruf über
        `get_quote_by_identity`, dem beide Werte ausdrücklich mitgegeben werden.
        Dieser Neuaufnahmeweg beschafft auch Name und Gattung; ein vorhandenes
        Listing wird weiterhin über den bekannten Bestand aufgefrischt.

        Args:
            ticker: Kanonischer Ticker aus der Eingabe.
            mic: MIC aus der Eingabe, in beiden Schreibweisen dieselbe Börse.

        Returns:
            Kurs und ob das Papier in diesem Aufruf entstanden ist.
        """
        instrument = self._repository.get_instrument_by_identity(
            ListedIdentityOut(ticker=ticker, mic=mic)
        )
        if instrument:
            return self._get(instrument, lambda: self._fetch_live(instrument))

        return self._get(
            None,
            lambda: self._quote_service.get_quote_by_identity(ticker, mic),
        )

    def store_by_symbol(self, symbol: str) -> StoredQuote:
        """Wie `get_by_symbol`, sagt aber zusätzlich, ob das Papier entstanden ist.

        Die Begründung für das Paar steht bei `store_by_isin`.
        """
        instrument = self._repository.get_instrument_by_symbol(symbol)
        if instrument:
            return self._get(instrument, lambda: self._fetch_live(instrument))
        return self._get(
            None,
            lambda: self._quote_service.get_quote_by_symbol(symbol, enrich_etf=True),
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
        return self._to_points(rows, instrument)

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
        return self._to_points(rows, instrument)

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
    def _to_points(rows: list[dict], instrument: dict) -> list[QuotePoint]:
        """Wandelt Quote-Zeilen in QuotePoint-Modelle um.

        Die Währung ist im Vertrag Pflicht (`core.history.currency`), ältere
        Zeilen können sie aber leer haben — vor der Währungspflicht ging eine
        Antwort ohne sie durch. Ausgeliefert wird dann die Währung des
        Listings: Dieselbe Notiz, dieselbe Währung.

        Raises:
            QuoteUnavailableError: Auch das Instrument kennt keine Währung.
        """
        currency = instrument.get("currency")
        points = []
        for row in rows:
            effective = row["currency"] or currency
            if effective is None:
                raise QuoteUnavailableError(
                    f"{instrument['symbol']}: Kurspunkt {row['quote_time']} ohne Währung"
                )
            points.append(
                QuotePoint(
                    price=row["price"],
                    quote_time=row["quote_time"],
                    volume=row["volume"],
                    currency=effective,
                    fetched_at=row["fetched_at"],
                )
            )
        return points

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

        Umgeht die TTL bewusst. Ist das Papier bekannt, wird es über sein
        gespeichertes Listing aufgefrischt statt neu aufgelöst — sonst wechselt
        es bei jedem Refresh womöglich Börse und Währung
        (siehe `get_quote_for_known`). Eine unbekannte ISIN muss dagegen
        aufgelöst werden, sonst ließe sich nie ein neues Papier aufnehmen.

        Raises:
            InstrumentNotFoundError: ISIN nicht auflösbar.
            QuoteUnavailableError: Kein Kurs beschaffbar.
        """
        instrument = self._repository.get_instrument_by_isin(isin)
        symbol = instrument.get("symbol") if instrument else None
        if instrument and symbol:
            # `enrich_etf=True` und nicht über `_fetch_live`: Der Griff zum
            # einzelnen Papier ist die ausdrückliche Ansage, jetzt nachzusehen —
            # die Metadaten-TTL gilt hier nicht.
            return self._save_fresh_with_volatility(
                self._quote_service.get_quote_for_known(
                    symbol,
                    isin=instrument.get("isin"),
                    exchange=instrument.get("exchange"),
                    instrument_type=instrument.get("type"),
                    name=instrument.get("name"),
                    identity=identity_from_columns(instrument),
                    enrich_etf=True,
                )
            )
        return self._save_fresh_with_volatility(self._quote_service.get_quote_by_isin(isin))

    def refresh_one_by_symbol(self, symbol: str) -> QuoteResponse:
        """Aktualisiert ein Instrument per Symbol live (für Papiere ohne ISIN).

        Reicht ISIN, Börse und Gattung der gespeicherten Zeile mit, genau wie
        `refresh_one`. Ohne ISIN läuft die justETF-Anreicherung gar nicht erst
        an (`enrich_etf and isin` in `_build`) — der Knopf an der Zeile ließe
        TER, Anbieter und Domizil dann für immer stehen, obwohl er das
        Gegenteil verspricht.

        Raises:
            QuoteUnavailableError: Kein Kurs beschaffbar.
        """
        instrument = self._repository.get_instrument_by_symbol(symbol)
        if instrument:
            return self._save_fresh_with_volatility(
                self._quote_service.get_quote_for_known(
                    symbol,
                    isin=instrument.get("isin"),
                    exchange=instrument.get("exchange"),
                    instrument_type=instrument.get("type"),
                    name=instrument.get("name"),
                    identity=identity_from_columns(instrument),
                    # Der Griff zum einzelnen Papier übergeht die Metadaten-TTL
                    # bewusst — siehe `refresh_one`.
                    enrich_etf=True,
                )
            )
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
            # **Über die Identität, nicht über das Symbol.** Die Antwort weiß,
            # welches Listing sie meint; `symbol` ist seit T-21 nur der
            # Anzeigename und trifft bei `AAPL/XNAS` neben `AAPL/XNYS` die
            # ältere Zeile. Das ist keine Mehrdeutigkeit, die den Aufrufer
            # etwas anginge — er hat kein Symbol genannt —, sondern eine
            # Buchführung, die schlicht die falsche Zeile las.
            isin = getattr(response.identity, "isin", None)
            instrument = (
                self._repository.get_instrument_by_isin(isin)
                if isin
                else self._repository.get_instrument_by_identity(
                    response.identity
                )
            )
            if instrument is None:
                return response
            instrument_id = instrument["id"]

        stored = self._repository.get_instrument_with_latest(instrument_id)
        if stored is not None:
            row = apply_overrides(stored)
            for field in OVERRIDE_FIELDS:
                setattr(response, field, row[field])
            response.details = {key: DetailValue.model_validate(value) for key, value in row['details'].items()}
        return response

    def _save_fresh(self, fresh: QuoteResponse) -> StoredQuote:
        """Persistiert einen frisch beschafften Kurs und reicht ihn durch."""
        stored = self._stored_metadata(fresh)
        saved = self._repository.save_quote(fresh)
        return StoredQuote(
            self._with_overrides(self._keep_stored_metadata(fresh, stored)),
            created=saved.created,
            instrument_id=saved.instrument_id,
        )

    @staticmethod
    def _keep_stored_metadata(
        fresh: QuoteResponse, stored: dict | None
    ) -> QuoteResponse:
        """Füllt die Lücken einer unvollständigen Antwort aus dem gespeicherten Stand.

        Das Repository schützt seine ETF-Spalten, wenn eine Antwort über sie
        nichts weiß (``metadata_complete=False``) — die Antwort an den Client
        ging aber unverändert hinaus. Ergebnis: Kurs-TTL abgelaufen,
        Metadaten-TTL frisch, justETF zu Recht nicht gefragt — und ``/quote``
        meldete `ter: null`, während in der Datenbank `0.2` stand. Dieselbe
        Kennzahl, zwei Antworten.

        Überlagert wird **genau dann und genau das**, was auch nicht
        geschrieben werden darf: dieselbe Bedingung, dieselbe Feldmenge wie in
        `QuoteRepository._writable_fields`. Eine vollständige Antwort bleibt
        unangetastet — sagt die Quelle zu einem Feld nichts mehr, ist das eine
        Aussage, und die muss durchkommen.

        Gefüllt werden nur **Lücken**; geprüft wird auf ``None`` und nicht auf
        Falschheit, sonst verlöre „ausschüttend" (`accumulating=False`) seinen
        Sinn. Einzige Ausnahme ist `source`: Es beschriftet die überlagerten
        Felder, steht bei einer frischen Antwort aber nie auf ``None`` — bliebe
        es stehen, hieße die Anzeige „yfinance" über Werten, die von justETF
        stammen.

        Args:
            fresh: Frisch beschaffte Antwort.
            stored: Instrumentenzeile vor dem Speichern, oder ``None`` für ein
                bis dahin unbekanntes Papier.

        Returns:
            Dieselbe Antwort, in deren Lücken der gespeicherte Stand steht.
        """
        if fresh.metadata_complete or stored is None:
            return fresh
        for field in PROTECTED_META_FIELDS:
            value = stored.get(field)
            if value is None:
                continue
            if field == "accumulating":
                value = _as_bool(value)
            if field == "source" or getattr(fresh, field) is None:
                setattr(fresh, field, value)
        return fresh

    def _stored_metadata(self, fresh: QuoteResponse) -> dict | None:
        """Liest die Instrumentenzeile, bevor ``save_quote`` sie fortschreibt.

        Ohne ISIN über die **kanonische Identität** — dieselbe Begründung wie
        in `_with_overrides`: Die frische Antwort weiß, welches Listing sie
        meint, und `symbol` weiß es seit T-21 nicht mehr.
        """
        isin = getattr(fresh.identity, "isin", None)
        if isin:
            return self._repository.get_instrument_by_isin(isin)
        return self._repository.get_instrument_by_identity(fresh.identity)

    def _save_fresh_with_volatility(self, fresh: QuoteResponse) -> QuoteResponse:
        """Persistiert einen frischen Kurs und ergänzt die Volatilität aus dem Cache.

        Nur wenn der Kurs selbst keine Volatilität mitbringt (justETF liefert für
        ETFs bereits eine — die bleibt bevorzugt). Wird ausschließlich im
        Refresh-Pfad aufgerufen, damit der lesende Request-Pfad schlank bleibt.

        Schlägt die Neuberechnung fehl (leerer EOD-Cache und toter Delta-Fetch),
        wird der zuvor gespeicherte Wert wiederhergestellt statt ihn mit ``None``
        zu überschreiben — behält den letzten bekannten Wert.
        """
        stored = self._stored_metadata(fresh)
        previous_volatility = stored["volatility"] if stored else None
        instrument_id = self._repository.save_quote(fresh).instrument_id
        if fresh.volatility is None:
            volatility = self._volatility_from_cache(instrument_id, fresh)
            if volatility is not None:
                fresh.volatility = volatility
                self._repository.set_volatility(instrument_id, volatility)
            elif previous_volatility is not None:
                fresh.volatility = previous_volatility
                self._repository.set_volatility(instrument_id, previous_volatility)
        return self._with_overrides(
            self._keep_stored_metadata(fresh, stored), instrument_id
        )

    def _volatility_from_cache(self, instrument_id: int, quote) -> float | None:
        """Berechnet die 1-Jahres-Volatilität aus dem akkumulierenden EOD-Cache.

        Zieht zunächst das Delta nach (nur fehlende Tage) und rechnet dann über
        die letzten ~370 Tage. Best-effort: fehlende/zu wenige Daten → ``None``.
        """
        start = (datetime.now(timezone.utc).date() - timedelta(days=370)).isoformat()
        self._daily_sync.sync(
            instrument_id,
            quote.symbol,
            start,
            # Zwei Darstellungen derselben Sache: `QuoteResponse.identity`
            # ist die REST-Form, der Vertrag will seine eigene. Der Weg
            # ueber die Spaltenbelegung benutzt beide vorhandenen
            # Umrechnungen, statt eine dritte zu erfinden.
            identity=identity_from_row(identity_columns(quote.identity)),
            instrument_type=quote.type,
        )
        rows = self._repository.get_daily_closes(instrument_id, start)
        closes = [row["close"] for row in rows if row.get("close") is not None]
        return annualized_volatility(closes)

    def list_instruments(self) -> list[dict]:
        """Gibt alle Instrumente inkl. letztem Kurs und wirksamer Kennzahlen zurück."""
        return [
            with_identity(apply_overrides(row))
            for row in self._repository.list_instruments_with_latest()
        ]

    def store_resolved(self, resolved: object) -> StoredQuote:
        """Speichert ein aufgelöstes Papier **ohne Kurs**.

        Der Weg für Gattungen, die keine Kursquelle haben (T-31). Er läuft
        bewusst nicht über `_get`: Dort ginge es um Cache und TTL, und beides
        setzt einen Kurs voraus, den es hier nicht gibt.

        Args:
            resolved: Das aufgelöste Papier.

        Returns:
            Dasselbe Paar wie die Kurswege — nur ohne Kurs in der Antwort.
        """
        saved = self._repository.save_instrument(
            resolved, datetime.now(timezone.utc).isoformat()
        )
        return StoredQuote(
            quote=None, created=saved.created, instrument_id=saved.instrument_id
        )

    def get_instrument_summary(self, instrument_id: int) -> dict | None:
        """Eine einzelne Zeile der Übersicht — für den Aufnahmeweg.

        **Warum der Aufnahmedienst sie hier holt und nicht aus einem eigenen
        Repository:** Zwei Repositories in einem Request sind zwei Wahrheiten.
        Der erste Entwurf baute im `IntakeService` eines aus den Settings —
        und im Test schrieb der Aufnahmeweg in die Testdatenbank, während er
        die Antwortzeile aus der **echten** las. Aufgefallen ist es nur, weil
        in der Antwort plötzlich ein Papier mit gepflegten Kennzahlen stand,
        das die Vorrichtung nie angelegt hatte.

        Args:
            instrument_id: Die lokale ID aus der Speicherung.

        Returns:
            Die Zeile mit wirksamen Kennzahlen, oder ``None``.
        """
        row = self._repository.get_instrument_with_latest(instrument_id)
        return with_identity(apply_overrides(row)) if row else None

    def get_overrides(self, symbol: str) -> dict:
        """Gibt die von Hand gepflegten Kennzahlen eines Instruments zurück.

        Raises:
            InstrumentNotFoundError: Symbol unbekannt.
        """
        instrument = self._require_instrument(symbol)
        stored = self._repository.get_overrides(instrument["id"]) or {}
        result = {field: stored.get(field) for field in OVERRIDE_FIELDS}
        result["accumulating"] = _as_bool(result["accumulating"])
        return result

    def set_overrides(self, symbol: str, values: dict[str, object]) -> dict:
        """Schreibt die manuellen Kennzahlen eines Instruments und liest sie zurück.

        Alle acht Werte auf einmal — ``None`` (bzw. ein fehlendes Feld) löscht.
        Die Vorrang-Regel wird hier **nicht** angewandt: Gespeichert wird, was
        der Nutzer eingetragen hat, auch wenn die Quelle den Wert gerade
        verdeckt. Sonst verschwände seine Eingabe in dem Moment, in dem die
        Quelle wieder etwas liefert — und käme nicht zurück, wenn sie es später
        wieder vergisst.

        Args:
            symbol: Yahoo-Symbol des Instruments.
            values: Werte je Feld aus ``OVERRIDE_FIELDS``; fehlende gelten als
                ``None`` und löschen damit.

        Raises:
            InstrumentNotFoundError: Symbol unbekannt.
        """
        instrument = self._require_instrument(symbol)
        definitions, _ = self._repository.detail_catalog()
        by_name = {definition.name: definition for definition in definitions}
        currency = (values.get('fund_currency')
                    or instrument.get('details', {}).get('fund_size', {}).get('manual_currency')
                    or instrument.get('manual_fund_currency')
                    or instrument.get('fund_currency'))
        if definitions or self._repository.has_detail_catalog():
            for field, value in values.items():
                if value is None:
                    continue
                definition = by_name.get(field)
                if definition is None or not definition.applies(instrument['type'], instrument['kind']) or not definition.overridable:
                    raise ValueError(f'Feld nicht bearbeitbar: {field}')
                validate_input(definition, DetailInput(value=value,
                    currency=currency if definition.currency_required else None))
        self._repository.set_overrides(
            instrument["id"],
            values=values,
            updated_at=datetime.now(timezone.utc).isoformat(),
            currency=currency,
        )
        return self.get_overrides(symbol)

    def set_detail_overrides(self, listing_id: str, values: dict[str, DetailInput]) -> dict:
        """Prüft den vollständigen Patch vor dem atomaren Schreiben."""
        instrument = self._repository.get_instrument_by_listing_id(listing_id)
        if instrument is None:
            raise InstrumentNotFoundError(listing_id)
        definitions, _ = self._repository.detail_catalog()
        by_name = {definition.name: definition for definition in definitions}
        for field, entry in values.items():
            definition = by_name.get(field)
            if definition is None or not definition.applies(instrument['type'], instrument['kind']):
                raise ValueError(f'Feld für dieses Instrument nicht deklariert: {field}')
            if not definition.overridable:
                raise ValueError(f'Feld nicht bearbeitbar: {field}')
            validate_input(definition, entry)
        self._repository.set_detail_overrides(instrument['id'], values, datetime.now(timezone.utc).isoformat())
        return self.get_instrument_summary(instrument['id'])['details']

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
        """Beschafft einen frischen Kurs für ein bekanntes Instrument (ohne Cache).

        justETF wird nur gefragt, wenn die gespeicherten Kennzahlen älter sind
        als `metadata_ttl_days`. Das ist der Pfad des Sammelrefresh: Ohne die
        Grenze kostet jede Runde einen Scrape je ETF, obwohl sich Anbieter,
        Domizil und Replikationsart praktisch nie ändern.

        **Ohne erneute Auflösung.** Das Papier ist bekannt, sein Listing steht
        fest — die ISIN noch einmal aufzulösen hieße, bei jedem Refresh neu zu
        würfeln, welche Börse man trifft (siehe `get_quote_for_known`). Ein
        einmal falsch aufgelöstes Instrument heilt damit nicht mehr von selbst;
        der Weg dafür ist `DELETE /instruments/{isin}`, danach löst der nächste
        Abruf neu auf.
        """
        enrich = self._etf_metadata_is_stale(instrument)
        symbol = instrument.get("symbol")
        if symbol:
            return self._quote_service.get_quote_for_known(
                symbol,
                isin=instrument.get("isin"),
                exchange=instrument.get("exchange"),
                instrument_type=instrument.get("type"),
                name=instrument.get("name"),
                identity=identity_from_columns(instrument),
                enrich_etf=enrich,
            )
        # Ohne Symbol bleibt nur die Auflösung — das kann nur ein Datensatz
        # sein, der vor dem ersten erfolgreichen Abruf angelegt wurde.
        return self._quote_service.get_quote_by_isin(instrument["isin"], enrich)

    def _etf_metadata_is_stale(self, instrument: dict | None) -> bool:
        """Ist der gespeicherte ETF-Metadatenstand alt genug für eine neue Abfrage?

        Args:
            instrument: Bekanntes Instrument, oder ``None`` für ein noch
                unbekanntes Papier.

        Returns:
            ``True`` wenn justETF gefragt werden soll. Ein unbekanntes Papier
            und eines ohne Zeitstempel gelten als alt — sonst bekäme ein neu
            hinzugefügter ETF seine Kennzahlen nie.
        """
        if instrument is None:
            return True
        fetched_at = instrument.get("meta_fetched_at")
        if not fetched_at:
            return True
        return not is_fresh(fetched_at, self._metadata_ttl_days * 24)

    def _get(
        self, instrument: dict | None, fetch: Callable[[], QuoteResponse]
    ) -> StoredQuote:
        """Gemeinsame Cache-Logik: frischer Cache → nutzen, sonst neu beschaffen.

        Args:
            instrument: Bereits bekanntes Instrument-Dict (oder None).
            fetch: Callable, das den Kurs live beschafft.

        Returns:
            Kurs-Antwort (aus Cache, frisch oder stale bei Fehler) samt der
            Auskunft, ob das Instrument in diesem Aufruf entstanden ist. Beide
            Cache-Wege beantworten das mit `False` — sie haben nichts
            geschrieben, und das Papier lag bereits vor.
        """
        latest = (
            self._repository.get_latest_quote(instrument["id"]) if instrument else None
        )
        # **Eine lokale Quelle kennt keine Frist.** Gefragt wird **je Papier**:
        # Steht die Dateiquelle hinter einer Online-Quelle, bleibt ein von der
        # vorderen bedienter Wert zwischengespeichert.
        asks = getattr(self._quote_service, "cacheable_for", None)
        cached_allowed = True if asks is None or not instrument else asks(instrument)
        if (
            instrument
            and latest
            and cached_allowed
            and is_fresh(latest["fetched_at"], self._ttl_hours)
        ):
            return StoredQuote(
                self._with_overrides(
                    self._from_cache(instrument, latest, stale=False), instrument["id"]
                ),
                created=False,
                instrument_id=instrument["id"],
            )

        try:
            fresh = fetch()
        except (QuoteUnavailableError, InstrumentNotFoundError):
            # Auch ein Resolver-Ausfall (InstrumentNotFoundError) darf einen
            # vorhandenen Cache-Wert nicht in einen Fehler verwandeln.
            if instrument and latest:
                logger.warning("serving_stale_quote", isin=instrument.get("isin"))
                return StoredQuote(
                    self._with_overrides(
                        self._from_cache(instrument, latest, stale=True),
                        instrument["id"],
                    ),
                    created=False,
                    instrument_id=instrument["id"],
                )
            raise

        return self._save_fresh(fresh)

    @staticmethod
    def _from_cache(instrument: dict, quote: dict, stale: bool) -> QuoteResponse:
        """Baut eine QuoteResponse aus gespeichertem Instrument + Kurspunkt.

        Die Währung kommt aus dem Kurspunkt, ersatzweise vom Instrument — sie
        gehört zum Listing, nicht zum einzelnen Punkt.

        Am Ende steht dieselbe Core-Prüfung wie im Live-Pfad, und zwar aus
        einem gemessenen Grund: Der Cache-Pfad hatte sie nicht, und über den
        läuft der Normalfall. Eine Antwort ohne Währung ist auch dann
        unverwertbar, wenn sie aus dem eigenen Bestand kommt.

        Raises:
            QuoteUnavailableError: Ein Pflichtfeld des Core fehlt. Betrifft
                auch den ``stale``-Fall: Der alte Wert ist der Notnagel, nicht
                die Ausnahme von der Regel.
        """
        # Dieselbe Prüfung wie auf dem frischen Weg, und aus demselben Grund:
        # Seit die zugesagten Felder nicht-nullbar sind, entstünde sonst ein
        # `ValidationError` statt der Aussage, was fehlt. Der `stale`-Fall ist
        # ausdrücklich mitgemeint — der alte Wert ist der Notnagel, nicht die
        # Ausnahme von der Regel.
        identity = identity_from_columns(instrument)
        require_core_values(
            instrument["symbol"],
            PrecheckedCoreValues(
                identity=identity,
                currency=quote["currency"] or instrument["currency"],
                name=instrument["name"],
                type=instrument["type"],
            ),
        )
        response = QuoteResponse(
            symbol=instrument["symbol"],
            # Seit T-21 Übergabe 3 zugesagt, und `ensure_core_complete` liest
            # die Pflichtliste aus dem Vertragsartefakt — ohne diese Zeile
            # antwortete ausgerechnet der Cache-Weg mit `502`. Der Wert steht
            # in der Zeile: seit T-31 bindet ihn dort der `CHECK`.
            identity=identity,
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
            fund_domicile=instrument["fund_domicile"],
            fund_currency=instrument["fund_currency"],
            volatility=instrument["volatility"],
            accumulating=_as_bool(instrument["accumulating"]),
            source="cache",
            cached=True,
            stale=stale,
            fetched_at=quote["fetched_at"],
        )
        ensure_core_complete(response)
        return response

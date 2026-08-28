"""Die Brücke zwischen Plugin-Vertrag und Core — und warum es sie geben muss.

Beide Seiten beschreiben dasselbe und sprechen verschieden:

    Core     handles(isin: str)          resolve_isin(isin) -> ResolvedInstrument
    Vertrag  handles(ResolveRequest)     resolve(ResolveRequest) -> Resolved

Ohne eine Brücke dazwischen bleibt der Plugin-Vertrag eine Hülle: Ein Plugin
kann geladen, geprüft und in `GET /sources` angezeigt werden — und beantwortet
trotzdem keine einzige Anfrage der App. Genau dieser Zustand war der schwerste
Befund aus Runde 1: Die Registry fand Plugins, der Core baute daneben weiter
seine nativen Klassen, und mein eigener „Auswahltest" hat die Lücke als
Eigenschaft festgeschrieben.

**Übersetzt wird an einer Stelle, und die Fachlogik wandert nicht mit.** Der
Adapter formt Anfragen und Antworten um; er entscheidet nichts über Börsen,
Symbole oder Zuständigkeit. Was er dafür braucht — die Bildung des
Anbieter-Symbols aus `ticker` und `mic` —, holt er aus `app.exchanges`, wo es
ohnehin steht.

**Warum die eingebauten Quellen denselben Weg nehmen.** Ein zweiter, direkter
Pfad für „unsere" Quellen wäre genau die Sonderbehandlung, die T-23 auflösen
soll: Wo der Vertrag zwickt, fiele es dann zuerst einem Fremden auf und nicht
uns.
"""

from __future__ import annotations

from dataclasses import fields
from datetime import date

import structlog

from stockinfo_plugin.types import (
    DailyRequest,
    DailySeries,
    FxRate,
    FxRequest,
    NotFound,
    NotResponsible,
    Quote,
    QuoteRequest,
    Resolved,
    ResolveRequest,
    Unavailable,
)

from app.exchanges import EXCHANGES, provider_alias
from app.providers.base import EtfDetails, RawQuote, Resolution, ResolvedInstrument

logger = structlog.get_logger()


def unwrap(source: object) -> object:
    """Die Quelle unter Adapter und Kapsel — **eine** Stelle, die hindurchsieht.

    Eine gebaute Kette trägt seit T-23 bis zu zwei Schichten: die Kapsel für
    fremden Code und den Adapter in die Sprache des Core. Wer wissen will,
    *was* dort eigentlich steht — eine Diagnose, ein Test, ein Protokoll —,
    fragt hier und nicht mit `._source` an drei Stellen.

    Die Alternative wäre gewesen, jeder Aufrufer schält selbst. Genau das
    stand nach Runde 1 in zwei Testdateien, jeweils leicht verschieden.
    """
    seen = source
    while True:
        inner = getattr(seen, "source", None)
        if inner is None or inner is seen:
            return seen
        seen = inner


class QuoteAdapter:
    """Ein Plugin der Kursrolle, in der Sprache des Core.

    **Der Core reicht seit T-23 die aufgelöste Identität herein, nicht mehr nur
    das Symbol.** Das ist die einzige Änderung an einer Core-Schnittstelle in
    diesem Ticket, und sie hat einen zwingenden Grund: Der Vertrag fragt mit
    `ticker` **und** `mic`, das Anbieter-Symbol entsteht erst daraus. Aus
    ``EUNL.DE`` wieder `('EUNL', 'XETR')` zu machen ginge nur über eine
    Rückwärtssuche in der Alias-Tabelle — und die ist nicht eindeutig: Ein
    Symbol ohne Suffix kann jeder US-Handelsplatz sein.

    Eine Umkehrung zu bauen, die in einem von sechs Fällen rät, wäre die
    schlechtere Wahl gewesen als eine Zeile im Aufrufer. Der Aufrufer **hat**
    die Identität; sie wegzuwerfen und danach zu erraten ist der Umweg.
    """

    def __init__(self, source: object, default_exchange: str) -> None:
        """
        Args:
            source: Das Plugin der Rolle `quotes`.
            default_exchange: Unbenutzt — die Signatur ist für alle Adapter
                dieselbe, damit `build_chain` sie ohne Fallunterscheidung
                aufrufen kann. Eine Kursanfrage trägt ihre Börse selbst.
        """
        self._source = source
        self._default_exchange = default_exchange

    @property
    def source(self) -> object:
        """Das gekapselte Plugin — für Diagnose und Tests."""
        return self._source

    @property
    def name(self) -> str:
        """Der Name des Plugins, für Protokoll und Anzeige."""
        return getattr(self._source, "name", type(self._source).__name__)

    def fetch_quote(self, instrument: ResolvedInstrument) -> RawQuote | None:
        """Holt den Kurs zu einer aufgelösten Identität.

        Returns:
            `RawQuote`, oder ``None`` wenn es keinen gibt. **`None` heißt für
            den Core „kein Kurs"** — die feinere Unterscheidung des Vertrags
            zwischen `NotFound` und `Unavailable` steht im Protokoll, damit sie
            nicht verlorengeht, aber der Core kennt an dieser Stelle nur zwei
            Ausgänge.

            Name, Gattung und Börse setzt der Adapter **nicht**: Sie sind
            Eigenschaften des Papiers und kommen aus der Auflösung. Der Service
            setzt sie mit ``raw.name or resolved.name`` zusammen; sie hier
            zusätzlich zu füllen hieße, dieselbe Angabe an zwei Stellen zu
            behaupten.
        """
        if not instrument.ticker or not instrument.mic:
            logger.info("quote_without_identity", symbol=instrument.symbol)
            return None

        answer = self._source.fetch_quote(
            QuoteRequest(
                ticker=instrument.ticker, mic=instrument.mic, isin=instrument.isin
            )
        )

        if isinstance(answer, Quote):
            return RawQuote(
                symbol=instrument.symbol,
                price=answer.price,
                quote_time=answer.as_of.isoformat(),
                currency=answer.currency,
                volume=answer.volume,
                isin=instrument.isin,
            )

        logger.info(
            "quote_not_available",
            source=self.name,
            symbol=instrument.symbol,
            outcome=type(answer).__name__,
        )
        return None


class DailyAdapter:
    """Ein Plugin der Historienrolle, in der Sprache des Core.

    **Diese Klasse fehlte, und das war kein Schönheitsfehler.** Runde 2 setzte
    `contract=True` an der yfinance-Quelle, ohne für `daily` und `fx` einen
    Adapter zu haben — der Core bekam damit das nackte Plugin und rief darauf
    `fetch_daily_closes`, das es nicht gibt. Ein `AttributeError` im Betrieb,
    und kein Test hat ihn gesehen, weil keiner diese beiden Rollen durch den
    Container geführt hat.
    """

    def __init__(self, source: object, default_exchange: str) -> None:
        self._source = source
        self._default_exchange = default_exchange

    @property
    def source(self) -> object:
        """Das gekapselte Plugin — für Diagnose und Tests."""
        return self._source

    def fetch_daily_closes(
        self, symbol: str, start: str | None = None
    ) -> list[dict] | None:
        """Die Tagesreihe in der Form, die der Core liest.

        Args:
            symbol: Das Anbieter-Symbol. Der Vertrag fragt mit `ticker` und
                `mic`; hier ist die Rückwärtsrichtung nötig und **eindeutig
                lösbar**, weil `EXCHANGES` die Aliase kennt. Wo sie es nicht
                ist, gibt es keine Antwort statt einer geratenen.
            start: Frühester Tag als ISO-Datum.

        Returns:
            Zeilen mit ``date``, ``close`` und ``currency``; ``None`` bei einer
            Störung, ``[]`` wenn es nichts gibt. Die Unterscheidung stammt aus
            dem Vertrag und wird hier nicht eingeebnet.
        """
        identity = _identity_from(symbol)
        if identity is None:
            logger.info("daily_symbol_not_resolvable", symbol=symbol)
            return None
        ticker, mic = identity

        answer = self._source.fetch_daily(
            DailyRequest(
                ticker=ticker,
                mic=mic,
                start=date.fromisoformat(start) if start else None,
            )
        )
        if isinstance(answer, DailySeries):
            return [
                {
                    "date": bar.day.isoformat(),
                    "close": bar.close,
                    "currency": answer.currency,
                }
                for bar in answer.bars
            ]
        if isinstance(answer, NotFound):
            return []
        return None


class FxAdapter:
    """Ein Plugin der Devisenrolle, in der Sprache des Core."""

    def __init__(self, source: object, default_exchange: str) -> None:
        self._source = source
        self._default_exchange = default_exchange

    @property
    def source(self) -> object:
        """Das gekapselte Plugin — für Diagnose und Tests."""
        return self._source

    def fetch_fx_rate(self, base: str, quote: str) -> float | None:
        """Der Kurs als nackte Zahl — mehr liest der Core hier nicht."""
        answer = self._source.fetch_rate(FxRequest(base=base, quote=quote))
        return answer.rate if isinstance(answer, FxRate) else None


class MetadataAdapter:
    """Ein Plugin der Metadatenrolle, in der Sprache des Core.

    Hier ist die Übersetzung am größten, und das ist kein Zufall: Die beiden
    Seiten schneiden die Daten verschieden. Der Core kennt einen Datensatz mit
    festen Feldern (`EtfDetails`), der Vertrag eine Liste von Messwerten
    (`Reading`) — Letzteres, damit ein Feld ankommen kann, das die App noch
    nicht kennt.

    Der Adapter füllt deshalb nur, was `EtfDetails` hat. **Ein unbekanntes Feld
    geht hier verloren**, und das ist der ehrliche Stand: Es aufzuheben ist
    T-26, nicht dieses Ticket.
    """

    def __init__(self, source: object, default_exchange: str) -> None:
        self._source = source
        self._default_exchange = default_exchange

    @property
    def source(self) -> object:
        """Das gekapselte Plugin — für Diagnose und Tests."""
        return self._source

    def is_responsible(self, isin: str | None = None, **_: object) -> bool:
        """Fühlt sich diese Quelle für das Papier zuständig?"""
        return bool(self._source.handles(ResolveRequest(isin=isin)))

    def fetch_etf(self, isin: str) -> EtfDetails | None:
        """Die Messwerte als Datensatz.

        Returns:
            `EtfDetails` mit den Feldern, die die App kennt. ``None``, wenn die
            Quelle nichts liefert **oder** nicht zuständig ist — der Core
            unterscheidet an dieser Stelle nicht, und ihm eine Unterscheidung
            vorzuspielen, die er nicht auswertet, wäre eine leere Zusage.
        """
        readings = self._source.fetch(ResolveRequest(isin=isin))
        if not readings:
            return None

        known = {field.name for field in fields(EtfDetails)}
        values = {
            reading.field: reading.value
            for reading in readings
            if reading.field in known
        }
        return EtfDetails(**values) if values else None


def _identity_from(symbol: str) -> tuple[str, str] | None:
    """Aus dem Anbieter-Symbol wieder Ticker und MIC — oder ``None``.

    **Die Gegenrichtung von `provider_alias`, und sie ist nur teilweise
    eindeutig.** ``EUNL.DE`` → `('EUNL', 'XETR')` geht, weil genau eine Börse
    den Alias ``DE`` führt. Ein Symbol **ohne** Suffix kann dagegen jeder
    US-Handelsplatz sein; dort gibt es keine Antwort statt einer geratenen.

    Genau deshalb bekommt `QuoteAdapter.fetch_quote` die Identität vom Core
    hereingereicht, statt sie hier zu rekonstruieren. Bei der Tagesreihe ist
    das (noch) nicht so — der Core reicht dort ein Symbol —, und das ist der
    Grund, warum diese Funktion überhaupt existiert.
    """
    if "." not in symbol:
        return None
    ticker, _, alias = symbol.rpartition(".")
    for mic, definition in EXCHANGES.items():
        if getattr(definition, "alias", None) == alias:
            return ticker, mic
    return None


class ResolverAdapter:
    """Ein Plugin der Resolver-Rolle, in der Sprache des Core.

    Die Übersetzung ist hier verlustfrei, und das ist der Grund, warum diese
    Rolle die erste ist: Der Core fragt mit einer ISIN, der Vertrag mit einer
    `ResolveRequest` — die trägt dieselbe ISIN plus die bevorzugte Börse, und
    die kommt aus den Einstellungen.

    Zurück ist es ebenso gerade: `Resolved` trägt `ticker` und `mic`, und das
    Anbieter-Symbol entsteht daraus über `provider_alias` — dieselbe Funktion,
    die der Core-Resolver benutzt. Sie hier nachzubauen hieße, dieselbe Regel
    zweimal zu pflegen.
    """

    def __init__(self, source: object, default_exchange: str) -> None:
        """
        Args:
            source: Das Plugin — alles, was `handles` und `resolve` nach dem
                Vertrag beantwortet.
            default_exchange: Die bevorzugte Börse aus den Einstellungen. Der
                Core fragt nur mit einer ISIN; welche Börse gemeint ist, weiß
                die App und nicht der Anrufer.
        """
        self._source = source
        self._default_exchange = default_exchange

    @property
    def source(self) -> object:
        """Das gekapselte Plugin — für Diagnose und Tests."""
        return self._source

    @property
    def name(self) -> str:
        """Der Name des Plugins, für Protokoll und Anzeige."""
        return getattr(self._source, "name", type(self._source).__name__)

    def _request(self, isin: str) -> ResolveRequest:
        """Die ISIN als Anfrage des Vertrags."""
        return ResolveRequest(isin=isin, preferred_mic=self._default_exchange)

    def handles(self, isin: str) -> bool:
        """Fühlt sich dieses Plugin für die ISIN zuständig?"""
        return bool(self._source.handles(self._request(isin)))

    def resolve_isin(self, isin: str) -> Resolution:
        """Löst auf und übersetzt die Antwort.

        Returns:
            `ResolvedInstrument` bei einem Treffer. Die Fehlfälle werden
            **unverändert durchgereicht**: `app.providers.base.Resolution`
            benutzt für sie bereits `stockinfo_plugin.types`, der Vertrag ist
            an dieser Stelle also schon gemeinsam.

        Ein Treffer **ohne vollständige Identität** wird zu `NotFound`. Der
        Core baut aus `ticker` und `mic` das Symbol, mit dem er später den Kurs
        holt; fehlt eines von beiden, entstünde ein Symbol, das auf ein anderes
        Listing zeigt. Lieber keine Antwort als die falsche.
        """
        answer = self._source.resolve(self._request(isin))

        if isinstance(answer, (NotResponsible, NotFound, Unavailable)):
            return answer
        if not isinstance(answer, Resolved):
            # Ein Plugin, das etwas anderes zurückgibt, verletzt den Vertrag.
            # Das ist ein Befund und kein Absturz: Die Kette geht zur nächsten
            # Quelle, und im Protokoll steht, wer sich nicht daran hält.
            logger.warning(
                "plugin_returned_unknown_type",
                source=self.name,
                got=type(answer).__name__,
            )
            return Unavailable(error=f"{self.name}: unerwartete Antwort")

        if not answer.ticker or not answer.mic:
            logger.info("resolve_without_identity", isin=isin, source=self.name)
            return NotFound()

        definition = EXCHANGES.get(answer.mic)
        return ResolvedInstrument(
            symbol=provider_alias(answer.ticker, answer.mic),
            isin=answer.isin or isin,
            exchange=definition.name if definition else None,
            name=answer.name,
            type=answer.instrument_type,
            ticker=answer.ticker,
            mic=answer.mic,
        )

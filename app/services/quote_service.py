"""Orchestriert die Kursbeschaffung — Auflösung, Abfrage, ETF-Anreicherung.

Kennt keine HTTP-Belange. Fehler werden als Domain-Exceptions signalisiert und
in der Router-Schicht auf HTTP-Statuscodes abgebildet.
"""

import math
import statistics
from dataclasses import dataclass, fields, replace
from datetime import datetime, timezone

import structlog

from stockinfo_plugin.types import Unavailable, Unsupported

from app.contract import required_fields
from app.exchanges import EXCHANGES, split_symbol
from app.models import (
    identity_columns,
    IdentityOut,
    ListedIdentityOut,
    PairIdentityOut,
    QuoteResponse,
    identity_from_columns,
)
from app.providers.base import (
    INSTRUMENT_TYPES,
    EtfEnricher,
    InstrumentResolver,
    QuoteProvider,
    RawQuote,
    ResolvedInstrument,
    declared_name,
    identity_from_row,
)

logger = structlog.get_logger()

# Handelstage pro Jahr — Standardfaktor zur Annualisierung der Tagesvolatilität.
_TRADING_DAYS_PER_YEAR = 252


def annualized_volatility(closes: list[float]) -> float | None:
    """Berechnet die annualisierte Volatilität aus Tages-Schlusskursen.

    Volatilität = Standardabweichung der täglichen Renditen × √252, in Prozent.

    Args:
        closes: Chronologisch geordnete Tages-Schlusskurse.

    Returns:
        Annualisierte Volatilität in Prozent (gerundet), oder ``None`` bei zu
        wenigen Datenpunkten.
    """
    if len(closes) < 5:
        return None
    returns = [
        closes[day] / closes[day - 1] - 1.0
        for day in range(1, len(closes))
        if closes[day - 1]
    ]
    if len(returns) < 2:
        return None
    daily_sd = statistics.stdev(returns)
    return round(daily_sd * math.sqrt(_TRADING_DAYS_PER_YEAR) * 100.0, 2)


class InstrumentNotFoundError(Exception):
    """Zu ISIN/Symbol konnte kein Wertpapier aufgelöst werden."""


class QuoteUnavailableError(Exception):
    """Es konnte kein aktueller Kurs beschafft werden.

    **`resolved` reist mit, seit es Papiere ohne Kursquelle gibt** (T-31).
    Eine OTC-Anleihe wird von OpenFIGI erkannt — Name, Gattung und Identität
    stehen fest —, und trotzdem liefert keine Quelle einen Preis. Das ist
    kein Fehlschlag der Aufnahme, sondern ihr Normalfall: Das Papier gehört
    in den Bestand, sein Preis ist eine andere Frage.

    Ohne dieses Feld ginge die Auflösung verloren, und der Aufnahmeweg müsste
    sie ein zweites Mal beschaffen — dieselbe Frage an dieselben Quellen, nur
    teurer.

    ``None`` heißt, dass es gar nicht bis zur Auflösung kam.
    """

    def __init__(self, *args: object, resolved: object = None) -> None:
        super().__init__(*args)
        self.resolved = resolved


def _as_resolved(row: object) -> ResolvedInstrument:
    """Eine gespeicherte Zeile als aufgelöstes Papier — für die Cachefrage.

    Sie braucht Identität und Gattung, sonst nichts.
    """
    get = row.get if isinstance(row, dict) else lambda key, default=None: getattr(row, key, default)
    return ResolvedInstrument(
        symbol=str(get("symbol") or ""),
        isin=get("isin"),
        kind=str(get("kind") or "listed"),
        ticker=get("ticker"),
        mic=get("mic"),
        base=get("base"),
        quote_currency=get("quote_currency"),
        type=get("type"),
    )


class QuoteCurrencyMismatchError(Exception):
    """Der gelieferte Kurs steht in einer anderen Währung als das Paar (`#7`).

    **Bei einem Paar gehört die Währung zur Identität.** Sie beantwortet die
    Frage, die bei einer Aktie der Handelsplatz beantwortet: *wo gilt dieser
    Preis?* `BTC-EUR` und `BTC-USD` sind zwei Instrumente, so verschieden wie
    zwei Listings derselben Aktie.

    Ein Kurs in fremder Währung gehört damit zu einem **anderen** Papier. Ihn
    still umzurechnen wäre die gefährlichere von zwei falschen Antworten: Der
    Wert sähe richtig aus und wäre es nicht, und niemand hätte einen Anlass
    nachzusehen. Ein Umrechnen bräuchte außerdem einen Stichtagskurs — eine
    zweite Quelle für eine Zahl, die niemand angefordert hat.
    """

    def __init__(self, symbol: str, expected: str, delivered: str) -> None:
        super().__init__(
            f"'{symbol}' notiert in {expected}, die Quelle lieferte "
            f"{delivered} — das ist ein anderes Instrument"
        )
        self.symbol = symbol
        self.expected = expected
        self.delivered = delivered


class UnsupportedInstrumentTypeError(Exception):
    """Diese Gattung nimmt die App **bewusst** nicht auf (T-31, Matrix `#6`).

    Der Unterschied zu `UnresolvableSymbolError` ist der ganze Punkt. Ein
    Index scheitert nicht daran, dass sein Symbol keinen Handelsplatz nennt —
    er scheitert daran, dass Indizes nicht im Gattungskatalog stehen. Fiele er
    in die Symbolform-Ablehnung, läse der Benutzer eine Begründung, die mit
    dem Grund nichts zu tun hat, und probierte Schreibweisen durch, die nie
    helfen können.

    Die Kennung sagt außerdem, dass es eine **Entscheidung** war und keine
    Grenze der Technik: Eine spätere Aufnahme des Typs ändert genau hier
    etwas.
    """

    def __init__(self, symbol: str, instrument_type: str) -> None:
        super().__init__(
            f"'{symbol}' ist ein {instrument_type!r} — diese Gattung nimmt "
            "StockInfo derzeit nicht auf"
        )
        self.symbol = symbol
        self.instrument_type = instrument_type


class UnresolvableSymbolError(Exception):
    """Aus diesem Symbol lässt sich keine kanonische Identität gewinnen.

    **Ein Eingabefehler, kein Ausfall.** Der Aufrufer hat ein Symbol genannt,
    das seine Börse nicht nennt (`AAPL`) oder eine fremde Schreibweise trägt
    (`BRK-B.DE`). Beides ist behebbar, und die Meldung sagt wie — deshalb
    nennt sie **beide** zulässigen Formen und nicht nur, dass etwas fehlt.
    """

    def __init__(self, symbol: str) -> None:
        super().__init__(
            f"'{symbol}' nennt keinen eindeutigen Handelsplatz. "
            "Zulässig sind das Provider-Suffix (z.B. 'EUNL.DE') oder der "
            "echte MIC (z.B. 'EUNL.XETR'); am zuverlässigsten ist die ISIN."
        )
        self.symbol = symbol


def _resolved_from(
    identity: IdentityOut,
    symbol: str,
    exchange: str | None,
    instrument_type: str | None,
) -> ResolvedInstrument:
    """Ein `ResolvedInstrument` aus einer Identität, die nicht `listed` ist.

    Für ein Paar und eine ISIN-only-Anleihe gibt es aus dem Symbol nichts
    abzuleiten — die Identität *ist* die Angabe, und sie kommt aus der
    gespeicherten Zeile.
    """
    if isinstance(identity, PairIdentityOut):
        return ResolvedInstrument(
            symbol=symbol,
            exchange=exchange,
            type=instrument_type,
            kind="pair",
            base=identity.base,
            quote_currency=identity.quote_currency,
        )
    return ResolvedInstrument(
        symbol=symbol,
        isin=identity.isin,
        exchange=exchange,
        type=instrument_type,
        kind="isin_only",
    )


@dataclass(frozen=True)
class PrecheckedCoreValues:
    """Die Pflichtfelder, die **erst beim Bauen** zusammenkommen.

    Sie stammen aus verschiedenen Quellen — Auflösung, Anbieterantwort,
    gespeicherte Zeile — und können dabei leer bleiben. Die übrigen erzwingt
    schon der Typ.

    **`identity` ist seit T-31 ein Feld statt zweier.** Sie ist entweder
    vollständig in ihrer Form oder ``None``; ein halb gefülltes Paar aus
    Ticker und MIC, wie es hier bis T-31 stand, gibt es nicht mehr — die
    Zusammensetzung passiert eine Ebene früher und kennt die Form.

    **Name und Wert stehen hier zusammen, und das ist der ganze Zweck.** Bis
    Runde 43 lagen die Namen in einer Tupelkonstante, die Werte positional
    daneben und ein drittes Mal in der Signatur der Prüffunktion. Der
    Kommentar behauptete, ein viertes Feld werde an genau einer Stelle
    ergänzt; die Gegenprobe von Codex zeigte das Gegenteil: Ein Name mehr in
    der Konstante ließ den Wächtertest grün und die Prüfung selbst an
    `zip(..., strict=True)` abstürzen. Ein Feld mehr **hier** wandert dagegen
    von selbst in die Namensliste, in die Prüfung und — weil kein Feld einen
    Vorgabewert hat — sichtbar in beide Aufrufer.
    """

    identity: IdentityOut | None
    currency: str | None
    # **Seit T-38, und der Weg hierher war der Beweis für den Absatz darüber.**
    # `quote.name` und `quote.type` wurden im Artefakt zu Pflichtfeldern, das
    # Modell wurde nicht-nullbar — und diese Vorabprüfung kannte beide nicht.
    # Ergebnis: Pydantic warf zwei Zeilen später einen `ValidationError`, also
    # ein 500 ohne Auskunft, an vierzehn Stellen zugleich.
    #
    # Genau das sollte die Struktur hier verhindern: Ein Feld mehr **in dieser
    # Klasse** wandert von selbst in `missing()`, in `PRECHECKED_CORE_FIELDS`
    # und — weil kein Feld einen Vorgabewert hat — sichtbar in beide Aufrufer.
    # Sie hat gehalten, was sie verspricht; nur hatte niemand sie ergänzt.
    name: str | None
    type: str | None

    def missing(self) -> list[str]:
        """Die Namen der Felder ohne Wert, in Deklarationsreihenfolge.

        **Reiner Leerraum zählt als fehlend.** Ein Pflichtfeld verhindert, dass
        ein Wert weggelassen wird — nicht, dass er nichts enthält. ``"   "`` ist
        eine nichtleere Zeichenkette und damit wahr; ohne diese Regel verließe
        ein Name aus drei Leerzeichen den Kursweg als gültige Antwort und
        stünde danach in der Oberfläche.

        Returns:
            Leere Liste, wenn alles da ist.
        """
        missing: list[str] = []
        for entry in fields(self):
            value = getattr(self, entry.name)
            if not value or isinstance(value, str) and not value.strip():
                missing.append(entry.name)
        return missing


# Abgeleitet statt danebengeschrieben — sonst wäre es wieder eine zweite
# Wahrheit. Die Namen wandern nach außen, weil der Vertragswächter prüft, dass
# die Vorabprüfung nichts verlangt, was das Artefakt nicht zusagt.
PRECHECKED_CORE_FIELDS = tuple(entry.name for entry in fields(PrecheckedCoreValues))


def require_core_values(symbol: str, values: PrecheckedCoreValues) -> None:
    """Die **eine** Vorabprüfung, bevor eine `QuoteResponse` entsteht.

    Das Gegenstück zu `ensure_core_complete`, eine Zeile früher. Seit die
    zugesagten Pflichtfelder auch im Modell nicht-nullbar sind, käme ein
    fehlender Wert dort als `ValidationError` an — ein `500`, der dem Aufrufer
    nichts über die Ursache sagt.

    **Zwei Aufrufer, eine Struktur.** Der frische Weg (`QuoteService._build`)
    und der Cache-Weg (`CachedQuoteService._from_cache`) beschaffen dieselben
    Werte aus verschiedenen Quellen. Bis Runde 42 zählte jeder sie selbst auf;
    ein viertes Pflichtfeld wäre an genau einem von beiden vorbeigegangen.

    Args:
        symbol: Für die Meldung.
        values: Die beschafften Pflichtwerte.

    Raises:
        QuoteUnavailableError: Mindestens ein Wert ist leer.
    """
    missing = values.missing()
    if not missing:
        return
    logger.warning("core_incomplete", symbol=symbol, missing=missing)
    raise QuoteUnavailableError(f"{symbol}: Pflichtfelder fehlen — {', '.join(missing)}")


def ensure_core_complete(response: QuoteResponse) -> None:
    """Wirft, wenn ein Pflichtfeld des Core-Vertrags leer ist.

    Der praktische Fall ist die fehlende Währung: Ein Preis ohne sie ist für
    eine Depotrechnung wertlos, und die naheliegende Vermutung — „wird schon
    Euro sein" — ist bei einem Londoner Listing in Pence falsch. Bisher ging
    so eine Antwort durch und wurde gespeichert.

    Die Feldliste kommt aus `contract/core-contract.json`, nicht aus einer
    zweiten Aufzählung hier: Sonst verspräche `GET /fields` etwas anderes, als
    der Code durchlässt. Pydantic deckt die übrigen Pflichtfelder schon beim
    Bauen ab; übrig bleiben die, die zwar Pflicht sind, aber ``None`` sein
    könnten.

    Args:
        response: Die fertig gebaute Antwort.

    Raises:
        QuoteUnavailableError: Ein Pflichtfeld ist ``None``. Der Router bildet
            das auf 502 ab — „nicht verwertbar" ist näher an „Quelle
            unbrauchbar" als an „nicht gefunden".
    """
    missing = [
        field
        for field in required_fields("quote")
        if getattr(response, field, None) is None
    ]
    if not missing:
        return
    logger.warning("core_incomplete", symbol=response.symbol, missing=missing)
    raise QuoteUnavailableError(
        f"{response.symbol}: Pflichtfelder fehlen — {', '.join(missing)}"
    )


class QuoteService:
    """Beschafft einen vollständigen, angereicherten Kurs für ein Wertpapier."""

    def __init__(
        self,
        quote_provider: QuoteProvider,
        etf_provider: EtfEnricher,
        resolver: InstrumentResolver,
    ) -> None:
        """
        Args:
            quote_provider: Liefert den Rohkurs zu einem Symbol.
            etf_provider: Reichert ETFs anhand der ISIN an.
            resolver: Löst ISINs zu Symbolen auf.
        """
        self._quote_provider = quote_provider
        self._etf_provider = etf_provider
        self._resolver = resolver

    def cacheable_for(self, row: object) -> bool:
        """Darf ein Kurs zu diesem Papier zwischengespeichert werden?

        Die Frage geht an die Kette: Sie weiß, welche Quelle für dieses Papier
        zuerst infrage kommt. Ohne diese Auskunft gilt zwischenspeicherbar.

        Args:
            row: Eine Instrumentenzeile mit den Identitätsspalten.
        """
        answer = getattr(self._quote_provider, "cacheable_for", None)
        if answer is None:
            return True
        return bool(answer(_as_resolved(row)))

    def _metadata_source(self, raw: RawQuote) -> str | None:
        """Woher der Metadatenstand dieser Antwort kommt — oder ``None``.

        **`source` ist die Herkunft der Metadaten, nicht die des Kurses.** So
        sagt es der Vertrag (`contract/core-contract.json`, `quote.source`:
        „Woher der jüngste Metadatenstand kommt"), und genau daran sind zwei
        Anläufe nacheinander gescheitert:

        * Bis T-37 stand hier fest ``"yfinance"``. Im Online-Profil fiel das
          nicht auf — dort lieferte yfinance beides.
        * In T-37 habe ich es durch den Namen der **Kursquelle** ersetzt. Das
          machte die Zeile im CSV-Profil zwar plausibel, war aber dasselbe
          Missverständnis: Eine reine Kursquelle liefert überhaupt keine
          Metadaten, und ihr Name gehört deshalb nicht in dieses Feld.

        **Gemessen, und es entscheidet die Sache:** Seit T-23 setzt
        `QuoteAdapter` auf der `RawQuote` weder `name` noch `type` noch
        `exchange` — der Vertragstyp `Quote` hat diese Felder nicht. Der
        Kursweg trägt also in **keinem** Profil etwas zum Metadatenstand bei.
        Ihn hier zu nennen wäre immer falsch, nicht nur manchmal.

        Deshalb steht hier eine **Bedingung** und keine Konstante: Die
        Kursquelle wird genannt, *wenn* ihre Antwort Metadaten trug — und sonst
        nicht. Heute trägt sie keine, die Antwort ist also ``None`` und die
        Metadatenquelle setzt sie in `_enrich`. Liefert eine Anbindung später
        wieder Name oder Gattung, folgt die Herkunft von selbst, ohne dass
        jemand daran denken muss.

        **Gefragt wird die Antwort, nicht der Anbieter.** In einer Kaskade
        sind das zwei verschiedene Dinge: Fällt die erste Quelle durch,
        stammen die Metadaten von der zweiten, während `declared_name` am
        Anbieter weiterhin die erste nennt. Wer sich hier auf den Anbieter
        verlässt, schreibt einen Namen auf, der nichts geliefert hat.

        Der Rückfall auf den Anbieter bleibt für den Normalfall einer
        einzelnen Quelle: Sie beschriftet ihre Antwort nicht, und ihr Name ist
        dort ohne Zweideutigkeit der richtige.

        Args:
            raw: Die Antwort der Kursquelle.

        Returns:
            Der Name der Quelle, die geantwortet hat, falls sie Metadaten
            beigesteuert hat; sonst ``None``.
        """
        contributed = any((raw.name, raw.type, raw.exchange))
        if not contributed:
            return None
        return raw.source or declared_name(self._quote_provider)


    def get_quote_by_isin(self, isin: str, enrich_etf: bool = True) -> QuoteResponse:
        """Beschafft den Kurs zu einer ISIN.

        Args:
            isin: ISIN des Wertpapiers.
            enrich_etf: Ob justETF gefragt wird. ``False`` heißt „der
                gespeicherte Metadatenstand ist jung genug" — die Antwort
                trägt die ETF-Extras dann nicht und ist als unvollständig
                markiert, damit sie den Bestand nicht überschreibt.

        Returns:
            Vollständige, ggf. angereicherte Kurs-Antwort.

        Raises:
            InstrumentNotFoundError: Die Quellen haben nachgesehen und kennen
                das Papier nicht — oder keine war zuständig. Führt zu 404.
            QuoteUnavailableError: Mindestens eine zuständige Quelle konnte
                gar nicht nachsehen. Führt zu **502**, und der Antwortkörper
                nennt die ausgefallenen Quellen. Vorher lief dieser Fall über
                dasselbe ``None`` wie „kenne ich nicht" und wurde zu 404 — ein
                Konsument gab das Papier daraufhin auf, obwohl nur das Netz
                weg war.
        """
        resolution = self._resolver.resolve_isin(isin)
        if isinstance(resolution, Unsupported):
            # **Derselbe Grund wie im Symbolweg** (T-31, Matrix `#6`). Hier
            # fiel er bis Runde 6 in das `InstrumentNotFoundError` darunter,
            # und ein erkannter Index wurde am ISIN-Eingang zu einem 404. Für
            # den Benutzer war das dieselbe Auskunft wie bei einer erfundenen
            # ISIN — er hätte die Kennung nachgeschlagen, die längst stimmte.
            raise UnsupportedInstrumentTypeError(isin, resolution.instrument_type)
        if isinstance(resolution, Unavailable):
            raise QuoteUnavailableError(
                f"{isin}: keine Quelle konnte nachsehen — {resolution.error}"
            )
        if not isinstance(resolution, ResolvedInstrument):
            raise InstrumentNotFoundError(isin)
        return self._build(resolution, enrich_etf)

    def get_quote_by_symbol(self, symbol: str, enrich_etf: bool = True) -> QuoteResponse:
        """Beschafft den Kurs zu einem vollständigen Yahoo-Symbol.

        Args:
            symbol: Vollständiges Yahoo-Symbol inkl. Börsen-Suffix, z.B.
                'VGWL.DE' (Xetra) oder 'AAPL' (US). Das Suffix wählt die Börse.
            enrich_etf: Ob justETF gefragt wird — siehe `get_quote_by_isin`.

        Returns:
            Kurs-Antwort.

        Raises:
            QuoteUnavailableError: Kein Kurs beschaffbar.
        """
        # Die Identität kann hier nicht aus einer Auflösung kommen — es gibt
        # keine ISIN zu fragen. Sie entsteht aus dem Symbol selbst, mit
        # derselben Rechnung, mit der der Umzug den Bestand zerlegt.
        #
        # **Bleibt das Symbol unzerlegbar, wird abgelehnt.** Hier stand bis
        # T-21 Teil 3 das Gegenteil: Die Zeile entstand „sichtbar offen", mit
        # dem Argument, der Aufrufer nenne das Listing ja selbst. Das Argument
        # hielt nicht — dieser Weg war die Quelle, die dauerhaft offene Zeilen
        # nachlieferte, und `get_quote_for_known` schloss sie nie, weil es
        # nicht auflöst, sondern Kurse holt. Seit eine halbe Identität nirgends
        # mehr weiterleben darf, ist Ablehnen der einzige ehrliche Ausgang.
        #
        # Geraten wird weiterhin nicht: `AAPL` bekommt keinen erfundenen MIC.
        ticker, mic = split_symbol(symbol)
        if ticker and mic:
            return self._build(self._described(symbol, ticker, mic), enrich_etf)

        # **Erst jetzt wird gefragt** (T-31, Matrix `#5`). Ein Symbol ohne
        # Börsensuffix ist nicht zwangsläufig unbrauchbar — es kann ein Papier
        # sein, das gar keinen Handelsplatz hat. Welche Form und welche Gattung
        # dahintersteckt, weiß nur eine Quelle; abgeleitet wird sie **nicht**.
        #
        # Der Bindestrich in `BTC-EUR` ist dabei kein Argument. Ein `^GDAXI`
        # trägt gar keins, und trotzdem verlangt Matrix `#6` für ihn eine
        # eigene Ablehnung statt des Zufallsbefunds „kein Börsensuffix" —
        # genau daran ist die Ableitung aus der Symbolform gescheitert.
        resolution = self._resolver.resolve_symbol(symbol)
        if isinstance(resolution, Unsupported):
            # **Der eigentliche Ausgang für Matrix `#6`.** Die Quelle hat das
            # Papier erkannt und seine Gattung genannt; abgelehnt wird es
            # wegen dieser Gattung und nicht wegen seiner Schreibweise. Dass
            # die Prüfung unten dieselbe Ausnahme wirft, ist kein doppelter
            # Weg: Dort ist die Gattung an einem *Treffer* aufgefallen, hier
            # ist sie die ganze Antwort.
            raise UnsupportedInstrumentTypeError(symbol, resolution.instrument_type)
        if isinstance(resolution, Unavailable):
            # **Ein Ausfall ist kein Eingabefehler** (Codex, Runde 5). Vorher
            # wurde daraus `UnresolvableSymbolError` und damit ein 400 mit dem
            # Rat, das Symbol anders zu schreiben — bei einem Netzausfall ein
            # Rat, der nicht helfen kann und den Benutzer an der falschen
            # Stelle suchen lässt. `BTC-EUR` ist gültig; die Quelle war es
            # gerade nicht.
            raise QuoteUnavailableError(f"{symbol}: {resolution.error}")
        if not isinstance(resolution, ResolvedInstrument):
            raise UnresolvableSymbolError(symbol)
        if resolution.type is not None and resolution.type not in INSTRUMENT_TYPES:
            raise UnsupportedInstrumentTypeError(symbol, resolution.type)
        return self._build(resolution, enrich_etf)

    def _described(self, symbol: str, ticker: str, mic: str) -> ResolvedInstrument:
        """Die Identität aus dem Symbol, Name und Gattung aus der Quelle.

        **Die genannte Börse gewinnt:** `ticker`, `mic` und der Anzeigename
        kommen aus dem Symbol — wer `GOLD.SG` tippt, meint Stuttgart. Die
        Quelle steuert bei, was die Identität nicht sagt; ihre ISIN reist mit,
        denn die sagt etwas über das Papier, nicht über den Handelsplatz.

        **Ablehnung und Ausfall reisen weiter**, sonst käme ein Index als
        „Pflichtfelder fehlen" heraus und ein Netzausfall als Aussage über das
        Papier. Die Ablehnung hat **zwei Gestalten** — ein verpacktes
        `Unsupported` und einen Treffer mit fremder Gattung; der eingebaute
        Yahoo-Resolver liefert die zweite. `NotFound` bricht nicht ab.

        Args:
            symbol: Das genannte Symbol samt Suffix.
            ticker: Kanonischer Ticker daraus.
            mic: Börse daraus — die des Benutzers.

        Returns:
            Das aufgelöste Instrument mit der Identität aus dem Symbol.

        Raises:
            UnsupportedInstrumentTypeError: Gattung, die StockInfo nicht führt.
            QuoteUnavailableError: Die Quelle ist ausgefallen.
        """
        described = self._resolver.resolve_symbol(symbol)
        if isinstance(described, Unsupported):
            raise UnsupportedInstrumentTypeError(symbol, described.instrument_type)
        if isinstance(described, Unavailable):
            raise QuoteUnavailableError(f"{symbol}: {described.error}")

        definition = EXCHANGES.get(mic)
        bare = ResolvedInstrument(
            symbol=symbol,
            ticker=ticker,
            mic=mic,
            exchange=definition.name if definition else None,
        )
        if not isinstance(described, ResolvedInstrument):
            return bare
        if described.type is not None and described.type not in INSTRUMENT_TYPES:
            raise UnsupportedInstrumentTypeError(symbol, described.type)
        return replace(
            bare, name=described.name, type=described.type, isin=described.isin
        )

    def get_quote_for_known(
        self,
        symbol: str,
        isin: str | None = None,
        exchange: str | None = None,
        instrument_type: str | None = None,
        identity: IdentityOut | None = None,
        enrich_etf: bool = True,
        name: str | None = None,
    ) -> QuoteResponse:
        """Beschafft den Kurs für ein **bereits aufgelöstes** Instrument.

        Der Unterschied zu `get_quote_by_isin` ist der fehlende Resolver-Lauf,
        und der ist der ganze Zweck: Die Auflösung ist nicht stabil. Findet
        OpenFIGI kein Listing an der bevorzugten Börse — Zeitüberschreitung,
        Rate-Limit, leere Antwort —, springt der Yahoo-Fallback ein und liefert
        das primäre Listing, bei einem iShares-Papier also die Londoner oder
        US-Notierung. Wer ein bekanntes Papier über die ISIN auffrischt,
        bekommt so mal Xetra in EUR und mal London in GBP, und das Ergebnis
        wird gespeichert. Im Depot fällt die Position damit aus der
        Währungsrechnung, und Gesamtwert wie Anteile stimmen nicht mehr.

        ISIN und Gattung werden trotzdem mitgegeben, und beide aus gutem Grund:
        `_build` braucht die ISIN für die justETF-Anreicherung, und die Gattung
        entscheidet, ob der ETF-Zweig überhaupt betreten wird. Fiele sie auf
        ``None``, bliebe `metadata_complete` auf seiner Vorgabe ``True``, und das
        Repository dürfte die gepflegten justETF-Felder mit nichts überschreiben.
        Der Resolver war bisher der zweite Lieferant der Gattung — wer ihn
        überspringt, muss sie aus der gespeicherten Zeile mitbringen.

        Args:
            symbol: Gespeichertes Yahoo-Symbol inkl. Börsen-Suffix.
            isin: Gespeicherte ISIN, für die ETF-Anreicherung.
            exchange: Gespeicherte Börse — sie bleibt, was sie war.
            instrument_type: Gespeicherte Gattung ('etf', 'stock', …).
            ticker: Gespeicherter kanonischer Ticker. Er greift nur, wenn das
                Symbol selbst keinen hergibt — bei Börsen **ohne** Alias.
            mic: Gespeicherter MIC, mit derselben Regel.
            enrich_etf: Ob justETF gefragt wird — siehe `get_quote_by_isin`.

        Returns:
            Kurs-Antwort für genau dieses Listing.

        Raises:
            QuoteUnavailableError: Kein Kurs beschaffbar.
        """
        # **Das Symbol entscheidet, wo es das kann — sonst die gespeicherte
        # Zeile.** Die Reihenfolge trägt zwei Zusagen, und beide sind geprüft:
        #
        # * **Nachtragen und korrigieren.** Ein zerlegbares Symbol *ist* die
        #   Auskunft über den Handelsplatz: In `EUNL.DE` benennt der Alias
        #   genau eine Börse. Steht in der Zeile etwas anderes — etwa `XMIL`,
        #   nachdem jemand die Vorzugsbörse umgestellt hat —, zieht der nächste
        #   Kurs sie gerade. Gewänne stattdessen der gespeicherte Wert, bliebe
        #   die überholte Zuordnung für immer stehen.
        # * **Aliaslose Börsen.** Ein US-Papier heißt gespeichert schlicht
        #   `AAPL`, und `split_symbol` gibt darauf `(None, None)` — richtig,
        #   denn dem nackten Symbol sieht niemand an, ob `XNAS` oder `XNYS`
        #   gemeint ist. Dort weiß es nur die Zeile. Ohne diesen Rückfall wäre
        #   die Auffrischung jedes US-Papiers ein `502`, seit `ticker` und
        #   `mic` zugesagte Pflichtfelder sind.
        #
        # Überschrieben wird nichts: Das Repository nimmt eine vollständige
        # Zuordnung nur an, wenn sie vollständig **ist**, und eine leere
        # ersetzt nie eine gespeicherte.
        # **Die gespeicherte Identität hat Vorrang vor der aus dem Symbol
        # abgeleiteten** — nur umgekehrt bei `listed`, wo das Symbol den
        # aktuellen Handelsplatz trägt und die Zeile einen überholten tragen
        # könnte. Für ein Paar und eine ISIN-only-Anleihe gibt es aus dem
        # Symbol ohnehin nichts abzuleiten.
        derived_ticker, derived_mic = split_symbol(symbol)
        # **Der Name reist seit T-38 mit, und ohne ihn wäre jeder Refresh ein
        # 502.** Dieser Weg löst bewusst *nicht* auf — er kennt das Papier ja
        # schon. Damit gibt es hier niemanden mehr, der einen Namen liefern
        # könnte: Die Kursquelle trägt ihn nach dem Vertrag nicht, und
        # `require_core_values` verlangt ihn seit T-38.
        #
        # Er kommt deshalb von dort, wo er steht: aus der gespeicherten Zeile,
        # genau wie `instrument_type` daneben. Das ist keine neue Quelle,
        # sondern dieselbe, die die Gattung schon immer geliefert hat.
        if identity is not None and not isinstance(identity, ListedIdentityOut):
            resolved = _resolved_from(identity, symbol, exchange, instrument_type)
            resolved = replace(resolved, name=name)
        else:
            resolved = ResolvedInstrument(
                symbol=symbol,
                isin=isin,
                exchange=exchange,
                name=name,
                type=instrument_type,
                kind="listed",
                ticker=derived_ticker
                or (identity.ticker if isinstance(identity, ListedIdentityOut) else None),
                mic=derived_mic
                or (identity.mic if isinstance(identity, ListedIdentityOut) else None),
            )
        return self._build(resolved, enrich_etf)

    def _build(
        self, resolved: ResolvedInstrument, enrich_etf: bool = True
    ) -> QuoteResponse:
        """Fragt den Kurs ab, baut die Antwort und reichert ETFs an.

        Args:
            resolved: Aufgelöstes Instrument (Symbol, ggf. ISIN und Typ).
            enrich_etf: Ob justETF gefragt wird.

        Returns:
            Kurs-Antwort; ``metadata_complete`` sagt, ob ihre ETF-Felder
            belastbar sind.
        """
        raw = self._quote_provider.fetch_quote(resolved)
        if raw is None:
            # Die Auflösung reist mit: Wer sie hat, kann das Papier aufnehmen,
            # auch wenn niemand einen Preis kennt.
            raise QuoteUnavailableError(resolved.symbol, resolved=resolved)

        isin = self._isin_of(resolved, raw)
        identity = identity_from_columns(
            {
                "kind": resolved.kind,
                "ticker": resolved.ticker,
                "mic": resolved.mic,
                "base": resolved.base,
                "quote_currency": resolved.quote_currency,
                "isin": isin,
            }
        )
        currency = raw.currency or resolved.currency
        require_core_values(
            resolved.symbol,
            PrecheckedCoreValues(
                identity=identity,
                currency=currency,
                name=raw.name or resolved.name,
                type=raw.type or resolved.type,
            ),
        )

        # **Matrix `#7`.** Bei einem Paar ist die Quote-Währung Teil der
        # Identität; ein Kurs in einer anderen gehört zu einem anderen
        # Instrument. Geprüft wird hier und nicht im Adapter: Erst hier stehen
        # Identität und gelieferte Währung nebeneinander.
        #
        # **Nach** der Vollständigkeitsprüfung: Ohne Währung ist „passt nicht"
        # keine belastbare Aussage, und der Aufrufer braucht dann die andere
        # Meldung.
        if isinstance(identity, PairIdentityOut) and currency != identity.quote_currency:
            raise QuoteCurrencyMismatchError(
                resolved.symbol, identity.quote_currency, str(currency)
            )

        instrument_type = raw.type or resolved.type
        response = QuoteResponse(
            symbol=resolved.symbol,
            # Die kanonische Identität aus der Auflösung (T-21), seit T-31 in
            # ihrer Form — am REST-Rand seit `core_version 2.0.0` zugesagt.
            identity=identity,
            exchange=resolved.exchange or raw.exchange,
            name=raw.name or resolved.name,
            type=instrument_type,
            currency=currency,
            price=raw.price,
            quote_time=raw.quote_time,
            volume=raw.volume,
            source=self._metadata_source(raw),
            cached=False,
            stale=False,
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )

        ensure_core_complete(response)

        if instrument_type is not None:
            # Ohne ISIN beantworten Börse und Währung die Zuständigkeit mit —
            # für `XIC.TO` nennt yfinance keine ISIN, und `.TO` in CAD sagt
            # bereits, dass justETF dieses Papier nicht führt. Vorher fiel
            # jedes solche Papier in den konservativen Zweig und blieb ohne
            # Anbieter (T-18).
            # Dass die Frage überhaupt beantwortbar ist, garantiert die
            # Core-Prüfung oben: Ohne Währung kommt eine Antwort gar nicht bis
            # hierher. Der Fall „niemand weiß etwas" ist damit an dieser Stelle
            # unerreichbar — die Quellen behandeln ihn trotzdem konservativ,
            # weil sie auch von anderswo aufgerufen werden.
            if not self._etf_provider.is_responsible(
                isin, exchange=response.exchange, currency=response.currency
            ):
                # Die Quelle führt dieses Papier gar nicht — ein US- oder
                # kanadischer ETF steht nicht bei justETF. Dann gibt es nichts
                # zu holen und damit auch keinen gepflegten Stand, den ein
                # `False` schützen müsste. Bliebe es dabei, hätte ein Nutzer
                # außerhalb Europas bei **jedem** ETF dauerhaft ein leeres
                # `source` in der Tabelle: Das Feld gehört zu
                # `_ETF_META_FIELDS` und würde nie geschrieben.
                response.metadata_complete = True
            elif enrich_etf:
                # Die Antwort weiß nur dann über die ETF-Extras Bescheid, wenn
                # die Anreicherung gelaufen ist **und** geliefert hat. Sonst
                # darf sie den gespeicherten Stand nicht ersetzen — siehe
                # `QuoteResponse.metadata_complete`.
                #
                # Die ISIN ist dafür keine Bedingung mehr: Yahoo arbeitet über
                # das Symbol, und die zuständige Quelle steht schon fest.
                response.metadata_complete = self._enrich_etf(response, isin)
            else:
                # Übersprungen, weil die Metadaten-TTL noch frisch ist. Was
                # hier steht, sagt nichts über die ETF-Felder — also darf es
                # den gespeicherten Stand nicht ersetzen.
                response.metadata_complete = False
        elif instrument_type is None:
            # Ohne Gattung lief der ETF-Zweig gar nicht — `metadata_complete`
            # blieb dann auf seiner Vorgabe `True`, und das Repository durfte
            # provider, ter, replication, Fondsgröße, -domizil, -währung und
            # source mit nichts überschreiben. yfinance liefert nicht immer
            # einen `quote_type`, und der Resolver ist nicht auf jedem Weg
            # dabei; „ich weiß nichts über die ETF-Felder" ist dann die
            # ehrlichere Aussage als „vollständig".
            #
            # Bei bekannter Gattung bestimmen die Plugin-Deklarationen oben,
            # welche Felder abgefragt werden; auch Aktien und Krypto sind möglich.
            response.metadata_complete = False
        return response

    @staticmethod
    def _isin_of(resolved: ResolvedInstrument, raw: RawQuote) -> str | None:
        """Wählt die ISIN der Antwort — die bekannte schlägt die gemeldete.

        `resolved.isin` ist entweder die Eingabe des Nutzers oder der
        gespeicherte Stand; `raw.isin` ist, was der Kursanbieter zum Symbol
        sagt. Bisher gewann der Anbieter, und das ist nachweislich falsch:
        yfinance meldet zu `MC.PA` die kanadische Zweitnotierung
        `CA50244Q1037` statt `FR0000121014`, zu `7203.T` entsprechend
        `CA89238H1091` statt `JP3633400001`. Der Name stimmt dabei jedes Mal,
        die Gattung nicht — beim Draufschauen fällt nichts auf, gespeichert
        wird trotzdem ein anderes Papier.

        Eine Abweichung wird protokolliert statt still verworfen: Sie sagt
        etwas über die Quelle, und das gehört gesehen.

        Args:
            resolved: Aufgelöstes oder gespeichertes Instrument.
            raw: Rohkurs des Anbieters.

        Returns:
            Die maßgebliche ISIN, oder ``None`` wenn keine Seite eine kennt.
        """
        if resolved.isin and raw.isin and raw.isin != resolved.isin:
            logger.warning(
                "isin_mismatch",
                requested=resolved.isin,
                reported=raw.isin,
                symbol=resolved.symbol,
            )
        return resolved.isin or raw.isin

    def _enrich_etf(self, response: QuoteResponse, isin: str | None) -> bool:
        """Ergänzt ETF-Details (TER, Anbieter, …) aus der ETF-Quelle, best-effort.

        Args:
            response: Antwort, die ergänzt wird.
            isin: ISIN für die Abfrage.

        Returns:
            ``True`` wenn die Quelle geantwortet hat — nur dann sind die
            ETF-Felder dieser Antwort belastbar. ``False`` heißt „nicht
            erreichbar", **nicht** „hat nichts". Der Unterschied entscheidet,
            ob der gespeicherte Stand überschrieben werden darf.
        """
        details = self._etf_provider.fetch_etf(
            isin,
            symbol=response.symbol,
            exchange=response.exchange,
            currency=response.currency,
            identity=identity_from_row(identity_columns(response.identity)),
            instrument_type=response.type,
        )
        if details is None:
            logger.debug("etf_enrichment_skipped", isin=isin)
            return False
        response.detail_readings = details.detail_readings
        response.ter = details.ter
        response.provider = details.provider
        response.replication = details.replication
        response.fund_size = details.fund_size
        response.name = response.name or details.name
        # Kein Rückfall auf die Handelswährung: Zwei Begriffe, zwei Felder.
        response.fund_currency = details.fund_currency
        response.fund_domicile = details.fund_domicile
        response.volatility = details.volatility
        response.accumulating = details.accumulating
        # Die Quelle beschriftet sich selbst — seit es mehr als eine gibt, wäre
        # ein festes "yfinance+justetf" für die Hälfte der Papiere falsch.
        response.source = details.source or response.source
        return True

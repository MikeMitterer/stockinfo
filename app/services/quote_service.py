"""Orchestriert die Kursbeschaffung — Auflösung, Abfrage, ETF-Anreicherung.

Kennt keine HTTP-Belange. Fehler werden als Domain-Exceptions signalisiert und
in der Router-Schicht auf HTTP-Statuscodes abgebildet.
"""

import math
import statistics
from datetime import datetime, timezone

import structlog

from stockinfo_plugin.types import Unavailable

from app.contract import required_fields
from app.exchanges import split_symbol
from app.models import QuoteResponse
from app.providers.base import (
    EtfEnricher,
    InstrumentResolver,
    QuoteProvider,
    RawQuote,
    ResolvedInstrument,
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
        closes[i] / closes[i - 1] - 1.0
        for i in range(1, len(closes))
        if closes[i - 1]
    ]
    if len(returns) < 2:
        return None
    daily_sd = statistics.stdev(returns)
    return round(daily_sd * math.sqrt(_TRADING_DAYS_PER_YEAR) * 100.0, 2)


class InstrumentNotFoundError(Exception):
    """Zu ISIN/Symbol konnte kein Wertpapier aufgelöst werden."""


class QuoteUnavailableError(Exception):
    """Es konnte kein aktueller Kurs beschafft werden."""


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


def require_core_values(symbol: str, **values: object) -> None:
    """Wirft, wenn einer der übergebenen Werte fehlt — **vor** dem Bauen.

    Das Gegenstück zu `ensure_core_complete`, eine Zeile früher. Seit die
    zugesagten Pflichtfelder auch im Modell nicht-nullbar sind, käme ein
    fehlender Wert dort als `ValidationError` an — ein `500`, der dem Aufrufer
    nichts über die Ursache sagt. Geprüft wird deshalb, bevor die Antwort
    entsteht, und die Aussage ist dieselbe wie die des späteren Prüfers.

    Args:
        symbol: Für die Meldung.
        values: Feldname auf Wert, in der Reihenfolge des Vertrags.

    Raises:
        QuoteUnavailableError: Mindestens ein Wert ist leer.
    """
    missing = [name for name, value in values.items() if not value]
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
        if not ticker or not mic:
            raise UnresolvableSymbolError(symbol)

        resolved = ResolvedInstrument(symbol=symbol, ticker=ticker, mic=mic)
        return self._build(resolved, enrich_etf)

    def get_quote_for_known(
        self,
        symbol: str,
        isin: str | None = None,
        exchange: str | None = None,
        instrument_type: str | None = None,
        ticker: str | None = None,
        mic: str | None = None,
        enrich_etf: bool = True,
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
        derived_ticker, derived_mic = split_symbol(symbol)
        resolved = ResolvedInstrument(
            symbol=symbol,
            isin=isin,
            exchange=exchange,
            type=instrument_type,
            ticker=derived_ticker or ticker,
            mic=derived_mic or mic,
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
        raw = self._quote_provider.fetch_quote(resolved.symbol)
        if raw is None:
            raise QuoteUnavailableError(resolved.symbol)

        require_core_values(
            resolved.symbol,
            ticker=resolved.ticker,
            mic=resolved.mic,
            currency=raw.currency or resolved.currency,
        )

        isin = self._isin_of(resolved, raw)
        instrument_type = raw.type or resolved.type
        response = QuoteResponse(
            isin=isin,
            symbol=resolved.symbol,
            # Die kanonische Identität aus der Auflösung (T-21) — seit
            # `core_version 2.0.0` auch am REST-Rand zugesagt.
            ticker=resolved.ticker,
            mic=resolved.mic,
            exchange=resolved.exchange or raw.exchange,
            name=raw.name or resolved.name,
            type=instrument_type,
            currency=raw.currency or resolved.currency,
            price=raw.price,
            quote_time=raw.quote_time,
            volume=raw.volume,
            source="yfinance",
            cached=False,
            stale=False,
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )

        ensure_core_complete(response)

        if instrument_type == "etf":
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
            # Eine bekannte Gattung außer `etf` bleibt bewusst vollständig: Da
            # gibt es nichts anzureichern und also nichts zu schützen — sonst
            # bekäme eine Aktie ihre Metadaten nie wieder aktualisiert.
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
        )
        if details is None:
            logger.debug("etf_enrichment_skipped", isin=isin)
            return False
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

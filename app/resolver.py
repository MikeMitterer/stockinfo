"""ISIN → Symbol/Börse-Auflösung.

Primär über OpenFIGI (bevorzugte Börse, z.B. Xetra → Suffix ``.DE``), Fallback
über die Yahoo-Finance-Suche (fängt US-Aktien u.a. ohne Xetra-Listing).

Das Yahoo-Suffix wählt die *Börse* — die *Währung* wird NICHT daraus abgeleitet,
sondern stammt immer aus dem Live-Quote (siehe yfinance_provider).
"""


import structlog
import yfinance as yf
from stockinfo_plugin.types import (
    NotFound,
    NotResponsible,
    Unavailable,
    Unsupported,
)

from app.exchanges import (
    DEFAULT_EXCHANGE,
    EXCHANGES,
    home_exchange,
    is_canonical_ticker,
    is_real_mic,
    mic_for_alias,
    preferred_mics,
    provider_alias,
)
from app.providers.base import (
    QUOTE_TYPE_MAP,
    InstrumentResolver,
    Resolution,
    ResolvedInstrument,
    SourceUnavailableError,
)
from app.providers.openfigi_provider import OpenFigiClient

logger = structlog.get_logger()


# Yahoos Börsencodes → echter MIC. **Bewusst kurz.**
#
# Gebraucht wird die Tabelle nur dort, wo die eigene Börsentabelle nichts
# hergibt: bei **suffixlosen** Symbolen. Für `EUNL.DE` liefert `mic_for_alias`
# den MIC aus der eigenen Konvention — Yahoos `GER` steht hier deshalb nicht,
# und jede Zeile, die dort schon beantwortet wird, gehört auch nicht her.
#
# Die Rangfolge steht an genau einer Stelle: `_exchange_of`.
#
# Suffixlos notieren bei Yahoo US-Listings. Welcher konkrete Handelsplatz
# gemeint ist, steht im Treffer; das Länderpräfix `US` ist kein MIC.
#
# Alle sechs Codes sind am 2026-08-23 über `yf.Search` **gemessen**, nicht aus
# der Erinnerung notiert (`AAPL`/`MSFT` → NMS, `QQQ` → NGM, `NAKDX` → NAS,
# `IBM`/`GME`/`BRK-B` → NYQ, `SPY`/`VTI` → PCX, `NAK`/`IMO` → ASE, `PBUS` →
# BTS). Die drei NASDAQ-Segmente (Global Select, Global Market, Capital
# Market) bekommen denselben MIC `XNAS`: Das ist der Betreiber-MIC, und die
# Segment-MICs (`XNGS`, `XNMS`, `XNCM`) sagen über den Handelsplatz nichts,
# was eine Kursquelle bräuchte.
YAHOO_EXCHANGE_MICS: dict[str, str] = {
    "NYQ": "XNYS",  # NYSE
    "NMS": "XNAS",  # NASDAQ Global Select
    "NGM": "XNAS",  # NASDAQ Global Market
    "NAS": "XNAS",  # NASDAQ Capital Market
    "PCX": "ARCX",  # NYSE Arca
    "ASE": "XASE",  # NYSE American
    "BTS": "BATS",  # Cboe BZX
}


def _exchange_of(symbol: str, exchange_code: str | None) -> str | None:
    """An welcher Börse liegt dieser Yahoo-Treffer?

    **Die eine Ableitung**, aus der Auswahl *und* Identitätsbildung ihren MIC
    beziehen. Getrennt formuliert liefen die beiden auseinander: Die Auswahl
    zog Yahoos Code auch bei einem suffigierten Symbol heran, und ein
    `WRONG.DE`-Treffer mit dem Code `NMS` galt ihr als NASDAQ-Notierung,
    während `_identity` ihm gleich darauf `XETR` gab. Anzeige, gewählte
    Präferenz und gespeicherter MIC widersprachen einander.

    Die Rangfolge ist **nicht** „erst probieren, dann das andere":

    1. **Das Symbol trägt ein Suffix.** Dann entscheidet allein die eigene
       Börsentabelle. Kennt sie das Suffix nicht (`FOO.ZZ`), ist die Antwort
       ``None`` — Yahoos Code darauf anzuwenden wäre falsch: Der Ticker vor
       dem Punkt gehört zu einer Börse, die StockInfo nicht führt, und das
       Symbol ließe sich danach nicht mehr zusammensetzen.
    2. **Das Symbol trägt keines.** Erst dann hilft `YAHOO_EXCHANGE_MICS`.
       Suffixlos notiert bei Yahoo genau ein Markt, die USA — und dort trägt
       nur der Code die Auskunft, welcher der fünf Plätze gemeint ist.

    Args:
        symbol: Das Symbol aus der Yahoo-Suche.
        exchange_code: Yahoos Feld ``exchange``, falls vorhanden.

    Returns:
        Der MIC, oder ``None`` wenn sich die Börse nicht bestimmen lässt.
    """
    if "." in symbol:
        return mic_for_alias(symbol.partition(".")[2])
    return YAHOO_EXCHANGE_MICS.get((exchange_code or "").upper())


def _identity(symbol: str, exchange_code: str | None) -> tuple[str | None, str | None]:
    """Bestimmt `(ticker, mic)` zu einem Yahoo-Treffer — oder gibt auf.

    Die Börse kommt aus `_exchange_of`; hier kommt allein die Frage dazu, ob
    der **Ticker** taugt. Er muss kanonisch sein: `BRK-B` scheitert daran,
    obwohl sein MIC feststeht — die Schreibweise ist Yahoos, nicht die der
    Börse. Dieselbe Regel misst die Erzeugung neuer Papiere, sonst gälte für
    gewachsene Zeilen eine andere Wahrheit als für neue.

    Args:
        symbol: Das Symbol aus der Yahoo-Suche.
        exchange_code: Yahoos Feld ``exchange``, falls vorhanden.

    Returns:
        `(ticker, mic)` bei eindeutiger Zuordnung, sonst ``(None, None)``.
    """
    mic = _exchange_of(symbol, exchange_code)
    if mic is None:
        return None, None

    ticker = symbol.partition(".")[0]
    return (ticker, mic) if is_canonical_ticker(ticker) else (None, None)


def _quote_name(quote: dict) -> str | None:
    """Bevorzugt den Langnamen; der Kurzname ist nur der Rückfall."""
    return quote.get("longname") or quote.get("shortname")


def _quote_type(quote: dict) -> str:
    """Liest den ``quoteType`` eines Yahoo-Treffers normalisiert aus.

    Args:
        quote: Ein Treffer der Yahoo-Suche.

    Returns:
        Die Gattung in Großbuchstaben, oder ``''`` wenn Yahoo keine nennt.
    """
    return (quote.get("quoteType") or "").upper()


class OpenFigiResolver:
    """Löst ISINs über OpenFIGI zum Listing einer bevorzugten Börse auf."""

    def __init__(
        self,
        client: OpenFigiClient,
        default_exchange: str = DEFAULT_EXCHANGE,
        home_fallback: bool = True,
    ) -> None:
        """
        Args:
            client: OpenFIGI-Client für das ISIN→Ticker-Mapping.
            default_exchange: MIC der bevorzugten Börse (z.B. 'XETR').
            home_fallback: Ob bei erfolglosem Versuch die Heimatbörse aus dem
                ISIN-Präfix gefragt wird. ``False`` bei `STRICT_EXCHANGE` —
                wer diese Einstellung wählt, will keine Überraschung in
                fremder Währung.
        """
        self._client = client
        self._default_exchange = default_exchange
        self._home_fallback = home_fallback

    def handles(self, isin: str) -> bool:
        """OpenFIGI deckt alle Märkte ab — hier gibt es nichts abzulehnen."""
        return True

    def resolve_isin(self, isin: str) -> Resolution:
        """Löst eine ISIN zum Yahoo-Symbol auf — bevorzugte Börse, dann Heimat.

        Die Kaskade ist der Kern von T-18: `CA7800871021` hat an Xetra kein
        Listing, an Toronto schon. Bisher fiel das Papier durch, weil nur die
        Vorgabebörse gefragt wurde. Das Emissionsland steckt im ISIN-Präfix —
        niemand muss es konfigurieren.

        Die Reihenfolge ist keine Feinheit: Die **bevorzugte** Börse gewinnt
        immer, wenn sie ein Listing hat. Sonst kippte ein europäischer ETF auf
        sein Domizil, und `IE00B4L5Y983` notierte plötzlich in Dublin statt an
        Xetra.

        Args:
            isin: ISIN des Wertpapiers.

        Returns:
            `ResolvedInstrument` bei einem Treffer, `NotFound` wenn OpenFIGI
            das Papier an keiner der gefragten Börsen kennt, `Unavailable`
            wenn der Dienst nicht antwortet. Die Unterscheidung ist der Zweck
            von T-20: Vorher war beides ``None``, und ein Ausfall wurde zu
            einem 404.
        """
        preferred = preferred_mics(self._default_exchange)[0]

        try:
            resolved = self._try_exchange(isin, preferred)
            if resolved is not None:
                return resolved

            home = home_exchange(isin) if self._home_fallback else None
            if home is None or home == preferred or home not in EXCHANGES:
                logger.warning("openfigi_resolve_empty", isin=isin, exchange=preferred)
                return NotFound()

            resolved = self._try_exchange(isin, home)
        except SourceUnavailableError as exc:
            return Unavailable(error=str(exc))

        if resolved is None:
            logger.warning("openfigi_resolve_empty", isin=isin, exchange=home)
            return NotFound()

        # Sichtbar machen, was passiert ist: Wer sein Papier plötzlich in CAD
        # sieht, muss den Grund im Protokoll finden.
        logger.info(
            "resolve_home_exchange",
            isin=isin,
            preferred=preferred,
            home=home,
            symbol=resolved.symbol,
        )
        return resolved

    def _try_exchange(self, isin: str, mic: str) -> ResolvedInstrument | None:
        """Fragt OpenFIGI nach dem Listing an genau einer Börse."""
        if not is_real_mic(mic):
            # Ohne gültige MIC-Schreibweise kann kein Listing entstehen.
            logger.info("resolve_without_identity", isin=isin, source="openfigi", mic=mic)
            return None

        exch = EXCHANGES[mic]
        match = self._client.map_isin(isin, mic, id_type="micCode")
        if not match:
            return None
        ticker = match.ticker
        if not is_canonical_ticker(ticker):
            # OpenFIGI schreibt Anteilsklassen mit Schrägstrich (`BRK/B`) —
            # das ist die Schreibweise des Anbieters, nicht die der Börse.
            logger.info(
                "resolve_without_identity",
                isin=isin,
                source="openfigi",
                ticker=ticker,
                mic=mic,
            )
            return None
        return ResolvedInstrument(
            symbol=provider_alias(ticker, mic),
            isin=isin,
            exchange=exch.name,
            # **Name und Gattung kommen aus derselben Antwort** und wurden bis
            # T-35 verworfen. Ohne die Gattung hielt die App jeden ETF für eine
            # Aktie und fragte justETF nie — TER, Anbieter und Domizil blieben
            # dauerhaft leer, ohne dass irgendwo ein Fehler stand.
            name=match.name,
            type=match.instrument_type,
            ticker=ticker,
            mic=mic,
        )


class YFinanceResolver:
    """Löst ISINs über die Yahoo-Finance-Suche auf (Fallback, v.a. US-Titel)."""

    def __init__(self, default_exchange: str = DEFAULT_EXCHANGE) -> None:
        """
        Args:
            default_exchange: MIC der bevorzugten Börse — dieselbe Vorgabe wie
                beim `OpenFigiResolver`. Sie entscheidet, welches Listing aus
                der Trefferliste genommen wird.
        """
        self._default_exchange = default_exchange

    def handles(self, isin: str) -> bool:
        """Yahoos Suche kennt keine Marktgrenze — hier gibt es nichts abzulehnen."""
        return True

    def resolve_symbol(self, symbol: str) -> Resolution:
        """Fragt Yahoo, **was** dieses Symbol ist (T-31, Matrix `#5`).

        Der Einstieg für Papiere ohne ISIN. Yahoo führt `BTC-EUR` nativ und
        meldet `quoteType: CRYPTOCURRENCY`; aus diesem **Befund** entsteht die
        Paar-Identität — nicht aus dem Bindestrich im Symbol.

        Der Unterschied ist nicht akademisch. Ein `^GDAXI` trägt kein Merkmal,
        an dem sich eine Gattung ablesen ließe, und ein `BRK-B.DE` trägt einen
        Bindestrich, ohne ein Paar zu sein. Wer aus der Symbolform schließt,
        bekommt bei beiden die falsche Antwort; wer fragt, bekommt bei beiden
        die richtige.

        Args:
            symbol: Das vom Nutzer genannte Symbol.

        Returns:
            `ResolvedInstrument` mit der Form, die zur gemeldeten Gattung
            passt. `NotFound`, wenn Yahoo das Symbol nicht kennt;
            `Unavailable`, wenn die Suche nicht antwortet — ein Netzfehler ist
            kein „gibt es nicht".
        """
        try:
            quotes = yf.Search(symbol).quotes
        except Exception as exc:
            logger.warning("resolve_symbol_failed", symbol=symbol, error=str(exc))
            return Unavailable(error=f"yahoo: {exc}")

        exact = next(
            (quote for quote in quotes if quote.get("symbol") == symbol), None
        )
        if exact is None:
            logger.info("resolve_symbol_unknown", symbol=symbol)
            return NotFound()

        # **Ein unbekannter `quoteType` wird durchgereicht, nicht zu `None`.**
        # Der Unterschied trägt Matrix `#6`: `None` heißt „die Quelle hat
        # nichts gesagt", `index` heißt „sie hat etwas gesagt, das wir nicht
        # führen". Nur im zweiten Fall gibt es einen Grund, der den Benutzer
        # weiterbringt — und das Ticket verlangt ihn ausdrücklich, statt auf
        # `stock` zu runden.
        reported = _quote_type(exact)
        instrument_type = QUOTE_TYPE_MAP.get(reported) or (reported.lower() or None)
        if instrument_type == "crypto":
            # `{base}-{quote}` ist Yahoos Schreibweise für ein Paar. Zerlegt
            # wird sie **erst jetzt** — nachdem die Gattung feststeht.
            base, _, quote_currency = symbol.partition("-")
            if not base or not quote_currency:
                return NotFound()
            return ResolvedInstrument(
                symbol=symbol,
                name=_quote_name(exact),
                type=instrument_type,
                kind="pair",
                base=base.upper(),
                quote_currency=quote_currency.upper(),
            )

        ticker, mic = _identity(symbol, exact.get("exchange"))
        if not ticker or not mic:
            # Kein erfundener Handelsplatz — dieselbe Regel wie im ISIN-Weg.
            # Die Gattung reist trotzdem mit: Der Aufrufer entscheidet damit,
            # ob er ablehnt, weil er die Gattung nicht führt, oder weil das
            # Symbol seine Börse nicht nennt. Zwei verschiedene Antworten.
            logger.info(
                "resolve_symbol_without_venue",
                symbol=symbol,
                instrument_type=instrument_type,
            )
            return ResolvedInstrument(symbol=symbol, type=instrument_type)

        return ResolvedInstrument(
            symbol=symbol,
            name=_quote_name(exact),
            type=instrument_type,
            kind="listed",
            ticker=ticker,
            mic=mic,
        )

    def resolve_isin(self, isin: str) -> Resolution:
        """Sucht das Listing der bevorzugten Börse zu einer ISIN über Yahoo.

        Args:
            isin: ISIN des Wertpapiers.

        Returns:
            `ResolvedInstrument` bei einem Treffer, `NotFound` wenn die Suche
            leer bleibt, `Unavailable` wenn sie gar nicht erst antwortet. Ein
            Netzfehler ist kein „gibt es nicht".
        """
        try:
            quotes = yf.Search(isin).quotes
        except Exception as exc:
            # Netz oder Parsing — nachgesehen hat hier niemand.
            logger.warning("resolve_isin_failed", isin=isin, error=str(exc))
            return Unavailable(error=f"yahoo: {exc}")

        if not quotes:
            logger.warning("resolve_isin_empty", isin=isin)
            return NotFound()

        top = self._best_match(quotes, isin)
        if top is None:
            logger.warning("resolve_isin_no_symbol", isin=isin)
            return NotFound()
        symbol = top["symbol"]
        exchange_code = top.get("exchange")
        ticker, mic = _identity(symbol, exchange_code)
        if not ticker or not mic:
            # **Ablehnen statt halb anlegen** (Ticket T-21, entschieden mit
            # Codex am 2026-08-20). Die Alternative — übernehmen und als „nicht
            # zerlegbar" markieren — macht die gerade eingeführte kanonische
            # Identität wieder optional und belastet jedes spätere Plugin mit
            # einem Yahoo-Sonderfall.
            #
            # `Unavailable`, nicht `NotFound`: Das Papier **gibt es**, nur ist
            # seine Zuordnung offen. Der Unterschied ist für den Aufrufer der
            # zwischen „falsche ISIN" und „hier muss jemand nachhelfen".
            logger.warning(
                "resolve_isin_ambiguous",
                isin=isin,
                symbol=symbol,
                exchange_code=exchange_code,
            )
            return Unavailable(
                error=(
                    f"yahoo: Treffer '{symbol}' ist nicht eindeutig zuzuordnen "
                    f"(Börsencode {exchange_code or '—'}); "
                    "Ticker und MIC müssen von Hand gesetzt werden"
                )
            )

        return ResolvedInstrument(
            symbol=symbol,
            isin=isin,
            exchange=top.get("exchDisp") or exchange_code,
            ticker=ticker,
            mic=mic,
            name=_quote_name(top),
            type=QUOTE_TYPE_MAP.get(_quote_type(top)),
            currency=None,  # Währung kommt aus dem Live-Quote, nicht aus der Suche
        )

    def _best_match(self, quotes: list[dict], isin: str) -> dict | None:
        """Wählt aus der Trefferliste das Listing der bevorzugten Börse.

        Yahoo sortiert nach eigenem Gutdünken, und der erste Treffer ist für ein
        europäisches Papier oft die Londoner oder US-Notierung. Wer den nimmt,
        holt sich GBP oder USD ins Haus, obwohl dasselbe Papier zwei Zeilen
        weiter in Euro an Xetra steht — im Depot fällt die Position damit aus
        der Währungsrechnung.

        Erkannt wird die Börse über `_exchange_of` — dieselbe Ableitung, die
        dem gewählten Treffer gleich darauf seinen MIC gibt. Am **Suffix des
        Symbols** (``.DE``, ``.MI``, …), und nur wo es keines gibt, an
        **Yahoos Börsencode** (`NMS`, `PCX`). Das Feld ``exchDisp`` daneben
        wäre der naheliegende Weg, ist aber Freitext von Yahoo („XETRA",
        „Frankfurt", „Milan") und taugt nicht als Schlüssel.

        Ein Treffer, dessen Börse sich so nicht bestimmen lässt, gehört zu
        keiner Präferenz. Er kann weiterhin gewinnen — aber nur über den
        Fremdbörsen-Fallback unten, wenn kein Treffer der bevorzugten Börse
        dasteht.

        Steht an der bevorzugten Börse mehr als ein Listing, entscheidet die
        **Gattung des bestplatzierten Treffers**. Yahoos Suche ist unscharf und
        mischt Zertifikate, Fonds und Optionsscheine desselben Basiswerts unter
        die Treffer; ohne diese Feinauswahl gewinnt der erste Suffix-Treffer,
        auch wenn er ein ``MUTUALFUND`` neben dem gesuchten ETF ist. Die
        Gattung ist dabei die Feinauswahl, nicht die Bedingung: Nennt kein
        Treffer der bevorzugten Börse dieselbe, gewinnt weiterhin die Börse —
        sonst kippte die Regel bei jeder unsauberen ``quoteType``-Angabe auf
        die auswärtige Notierung zurück.

        Findet sich das bevorzugte Listing nicht, gewinnt der erste brauchbare
        Treffer — ein US-Papier ohne deutsche Notierung muss weiterhin
        durchgehen, dafür gibt es diesen Resolver überhaupt.

        Args:
            quotes: Trefferliste der Yahoo-Suche.
            isin: Nur fürs Protokoll.

        Returns:
            Der gewählte Treffer oder ``None``, wenn keiner ein Symbol trägt.
        """
        with_symbol = [quote for quote in quotes if quote.get("symbol")]
        if not with_symbol:
            return None

        mics = frozenset(preferred_mics(self._default_exchange))
        at_exchange = [
            quote
            for quote in with_symbol
            if _exchange_of(str(quote["symbol"]), quote.get("exchange")) in mics
        ]

        if at_exchange:
            quote_type = _quote_type(with_symbol[0])
            return next(
                (
                    quote
                    for quote in at_exchange
                    if _quote_type(quote) == quote_type
                ),
                at_exchange[0],
            )

        logger.info(
            "resolve_foreign_exchange",
            isin=isin,
            chosen=with_symbol[0]["symbol"],
            expected=self._default_exchange,
        )
        return with_symbol[0]


def _resolve_symbol_of(resolver: object, symbol: str) -> Resolution:
    """Fragt eine Quelle über das Symbol — oder stellt fest, dass sie es nicht kann.

    Nicht jede Quelle beantwortet die Frage. Eine, die den Einstieg nicht
    hat, ist für dieses Symbol **unzuständig** — das ist eine ehrliche
    Aussage und etwas anderes als „kenne ich nicht". Der Unterschied
    entscheidet in der Kette über 404 gegen 502.
    """
    ask = getattr(resolver, "resolve_symbol", None)
    if ask is None:
        return NotResponsible(reason=f"{type(resolver).__name__} sucht nicht per Symbol")
    return ask(symbol)


class CompositeResolver:
    """Probiert mehrere Resolver der Reihe nach — erster Treffer gewinnt."""

    def __init__(self, *resolvers: InstrumentResolver) -> None:
        """
        Args:
            *resolvers: Resolver in Prioritätsreihenfolge.
        """
        self._resolvers = resolvers

    def handles(self, isin: str) -> bool:
        """Zuständig, sobald irgendeine Quelle der Kette es ist."""
        return any(resolver.handles(isin) for resolver in self._resolvers)

    def resolve_isin(self, isin: str) -> Resolution:
        """Fragt die Kette der Reihe nach und fasst die Antwortarten zusammen.

        Die Zusammenfassung ist der Kern von T-20 — sie entscheidet, ob am
        Ende ein 404 oder ein 502 steht:

        Die Tabelle steht bei `_ask`, wo die Regel liegt.

        **Ein Ausfall schlägt ein „kenne ich nicht".** Hat eine Quelle gar
        nicht nachsehen können, ist „gibt es nicht" keine belegte Aussage —
        auch dann nicht, wenn eine andere Quelle das Papier tatsächlich nicht
        kennt. Ein 404 würde einen Konsumenten dazu bringen, das Papier
        aufzugeben.

        Unzuständige Quellen werden **vor** der Anfrage übersprungen; sie
        kosten damit weder Netz noch Kontingent.

        Args:
            isin: ISIN des Wertpapiers.

        Returns:
            Die zusammengefasste Antwort der Kette.
        """
        return self._ask(
            lambda resolver: resolver.resolve_isin(isin),
            skip=lambda resolver: not resolver.handles(isin),
            subject=isin,
        )

    def resolve_symbol(self, symbol: str) -> Resolution:
        """Dasselbe über das Symbol — der Einstieg für Papiere ohne ISIN.

        **Warum es ihn braucht** (T-31, Matrix `#5`/`#6`): Die Identitätsform
        und die Gattung sind der *Befund der Quelle*, nicht eine Ableitung aus
        dem Symbol. Über den By-Symbol-Weg gab es bisher niemanden zu fragen —
        `QuoteRequest` verlangt eine fertige Identität, also genau das, was
        erst entstehen soll.

        **Ohne Vorfilter.** `handles` beantwortet die Zuständigkeit für eine
        *ISIN*; auf ein Symbol lässt sie sich nicht anwenden. Gefragt werden
        deshalb alle, und wer nichts damit anfangen kann, sagt
        `NotResponsible` — das kostet keine Anfrage nach außen, weil eine
        Quelle ohne Symbolsuche gar nicht erst hinausgeht.

        Args:
            symbol: Das vom Nutzer genannte Symbol.

        Returns:
            Die zusammengefasste Antwort der Kette, nach denselben Regeln wie
            bei `resolve_isin`.
        """
        return self._ask(
            lambda resolver: _resolve_symbol_of(resolver, symbol),
            skip=lambda resolver: False,
            subject=symbol,
        )

    def _ask(self, ask, skip, subject: str) -> Resolution:
        """Die Kettenregel aus T-20 — **einmal**, für beide Einstiege.

        Sie entscheidet, ob am Ende ein 404 oder ein 502 steht, und das ist
        zu viel Bedeutung für zwei Fassungen:

        | Unterwegs gesehen | Gesamtantwort | HTTP |
        |---|---|---|
        | ein Treffer | `ResolvedInstrument` | 200 |
        | sonst „erkannt, nicht geführt" | `Unsupported` | **400** |
        | sonst mindestens ein Ausfall | `Unavailable` | **502** |
        | sonst mindestens ein „kenne ich nicht" | `NotFound` | 404 |
        | nur Unzuständige | `NotResponsible` | 404 |

        **Warum `Unsupported` über dem Ausfall steht** (T-31, Matrix `#6`).
        Die bisherige Reihenfolge hatte einen Grund: „Ein Ausfall schlägt ein
        ‚kenne ich nicht'", weil eine Abwesenheit nichts beweist, solange
        jemand gar nicht nachsehen konnte. `Unsupported` ist aber keine
        Abwesenheit, sondern ein **Befund über das Papier**: Eine Quelle hat
        ``^GDAXI`` erkannt und die Gattung genannt. Dass eine andere Quelle
        währenddessen ausfiel, ändert daran nichts — sie hätte dasselbe Papier
        allenfalls als etwas anderes erkannt, und das wäre ein Widerspruch,
        keine Ergänzung. Ein 502 hieße hier „versuch es später nochmal" über
        eine Antwort, die auch morgen dieselbe ist.

        **Die Kette bricht trotzdem nicht ab.** „Ich führe keine Anleihen"
        heißt nicht „niemand führt Anleihen"; eine spätere Quelle darf
        dasselbe Papier auflösen und gewinnt mit ihrem Treffer.

        Args:
            ask: Was die einzelne Quelle gefragt wird.
            skip: Ob sie vorab übersprungen wird — beim ISIN-Weg die
                Zuständigkeitsfrage, beim Symbolweg nie.
            subject: ISIN oder Symbol, nur für das Protokoll.

        Returns:
            Die zusammengefasste Antwort.
        """
        failures: list[str] = []
        someone_looked = False
        unsupported: Unsupported | None = None

        for resolver in self._resolvers:
            if skip(resolver):
                continue
            result = ask(resolver)
            if isinstance(result, ResolvedInstrument):
                return result
            if isinstance(result, Unsupported):
                # Die **erste** Ablehnung gewinnt. Zwei Quellen, die dasselbe
                # Papier verschieden einordnen, sind ein Fall für das
                # Protokoll und nicht für eine Mehrheitsentscheidung.
                unsupported = unsupported or result
            elif isinstance(result, Unavailable):
                failures.append(result.error)
            elif isinstance(result, NotFound):
                someone_looked = True

        if unsupported is not None:
            logger.info(
                "resolve_chain_unsupported",
                subject=subject,
                instrument_type=unsupported.instrument_type,
            )
            return unsupported
        if failures:
            logger.warning(
                "resolve_chain_unavailable", subject=subject, sources=failures
            )
            return Unavailable(error="; ".join(failures))
        if someone_looked:
            return NotFound()
        return NotResponsible(reason="keine zuständige Quelle in der Kette")

"""ISIN → Symbol/Börse-Auflösung.

Primär über OpenFIGI (bevorzugte Börse, z.B. Xetra → Suffix ``.DE``), Fallback
über die Yahoo-Finance-Suche (fängt US-Aktien u.a. ohne Xetra-Listing).

Das Yahoo-Suffix wählt die *Börse* — die *Währung* wird NICHT daraus abgeleitet,
sondern stammt immer aus dem Live-Quote (siehe yfinance_provider).
"""


import structlog
import yfinance as yf

from stockinfo_plugin.types import NotFound, NotResponsible, Unavailable

from app.exchanges import (
    DEFAULT_EXCHANGE,
    EXCHANGES,
    home_exchange,
    is_canonical_ticker,
    is_real_mic,
    preference_kind,
    preferred_aliases,
    provider_alias,
    split_symbol,
)

from app.providers.base import (
    QUOTE_TYPE_MAP,
    InstrumentResolver,
    Resolution,
    ResolvedInstrument,
    SourceUnavailableError,
)
from app.providers.openfigi_provider import OpenFigiClient, figi_lookup

logger = structlog.get_logger()


# Yahoos Börsencodes → echter MIC. **Bewusst kurz.**
#
# Gebraucht wird die Tabelle nur dort, wo die eigene Börsentabelle nichts
# hergibt: bei **suffixlosen** Symbolen. Für `EUNL.DE` liefert `split_symbol`
# den MIC aus der eigenen Konvention — Yahoos `GER` steht hier deshalb nicht,
# und jede Zeile, die dort schon beantwortet wird, gehört auch nicht her.
#
# Suffixlos notiert bei Yahoo genau ein Markt: die USA. Die Börsentabelle führt
# ihn als Sammelcode `US` zusammen, weil OpenFIGI so sucht — welcher der sechs
# Handelsplätze gemeint ist, weiß erst der Treffer.
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


def _identity(symbol: str, exchange_code: str | None) -> tuple[str | None, str | None]:
    """Bestimmt `(ticker, mic)` zu einem Yahoo-Treffer — oder gibt auf.

    Zwei Wege, in dieser Reihenfolge:

    1. **Das Suffix** über die eigene Börsentabelle (`EUNL.DE` → `XETR`). Das
       ist StockInfos eigene Konvention und braucht Yahoo nicht.
    2. **Yahoos Börsencode** für suffixlose Symbole (`AAPL` bei `NMS` →
       `XNAS`). Nur hier ist die Zuordnungstabelle nötig.

    Der Ticker muss in beiden Fällen kanonisch sein. `BRK-B` scheitert daran,
    obwohl sein MIC feststeht — die Schreibweise ist Yahoos, nicht die der
    Börse.

    Args:
        symbol: Das Symbol aus der Yahoo-Suche.
        exchange_code: Yahoos Feld ``exchange``, falls vorhanden.

    Returns:
        `(ticker, mic)` bei eindeutiger Zuordnung, sonst ``(None, None)``.
    """
    ticker, mic = split_symbol(symbol)
    if ticker and mic:
        return ticker, mic

    if "." in symbol:
        # Ein Suffix, das die Tabelle nicht kennt (`GOLD.SG`). Yahoos Code
        # darauf anzuwenden wäre falsch: Der Ticker vor dem Punkt gehört zu
        # einer Börse, die StockInfo nicht führt — und `.SG` an einen MIC zu
        # binden, ohne die Börse in die eigene Tabelle aufzunehmen, hinge in
        # der Luft (das Symbol liesse sich danach nicht mehr zusammensetzen).
        return None, None

    mic = YAHOO_EXCHANGE_MICS.get((exchange_code or "").upper())
    if mic and is_canonical_ticker(symbol):
        return symbol, mic
    return None, None


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
        preferred = self._default_exchange
        if preference_kind(preferred) is None:
            # Seit T-21 Teil 3 liegen Börsen und Sammelcodes in getrennten
            # Tabellen. Geprüft wird deshalb die **Präferenz**, nicht die
            # Mitgliedschaft in `EXCHANGES` — sonst gälte der zulässige
            # Vorgabewert `US` plötzlich als unbekannt und fiele still auf
            # Xetra zurück.
            logger.warning("unknown_default_exchange", configured=preferred)
            preferred = DEFAULT_EXCHANGE

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
            # Der Sammelcode `US` fasst sechs Handelsplätze zusammen. OpenFIGI
            # beantwortet darauf die Frage „welcher Ticker", nicht „welche
            # Börse" — und ohne echten MIC ist die Identität unvollständig.
            #
            # Deshalb wird hier **gar nicht erst gefragt**: Die Antwort wäre
            # ohnehin nicht verwendbar, und jede Anfrage zählt gegen OpenFIGIs
            # Kontingent. Auflösen kann den Fall der Yahoo-Fallback, der den
            # Handelsplatz benennt (`NMS` → `XNAS`).
            logger.info("resolve_without_identity", isin=isin, source="openfigi", mic=mic)
            return None

        exch = EXCHANGES[mic]
        id_type, id_value = figi_lookup(mic)
        ticker = self._client.map_isin(isin, id_value, id_type=id_type)
        if not ticker:
            return None
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
            name=top.get("shortname") or top.get("longname"),
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

        Erkannt wird die Börse am **Suffix des Symbols** (``.DE``, ``.MI``, …).
        Das Feld ``exchDisp`` daneben wäre der naheliegende Weg, ist aber
        Freitext von Yahoo („XETRA", „Frankfurt", „Milan") und taugt nicht als
        Schlüssel.

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

        aliases = preferred_aliases(self._default_exchange)

        if aliases:
            at_exchange = [
                quote
                for quote in with_symbol
                if any(
                    str(quote["symbol"]).endswith(f".{alias}") for alias in aliases
                )
            ]
        else:
            # Keine der in Frage kommenden Börsen führt einen Alias — beim
            # Sammelcode `US` sind das seine fünf Mitglieder. Dort ist das
            # punktlose Symbol die Notierung. Ohne diesen Zweig liefe die
            # Regel leer, weil es kein Suffix zum Vergleichen gibt.
            at_exchange = [
                quote for quote in with_symbol if "." not in str(quote["symbol"])
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

        | Unterwegs gesehen | Gesamtantwort | HTTP |
        |---|---|---|
        | ein Treffer | `ResolvedInstrument` | 200 |
        | mindestens ein Ausfall | `Unavailable` | **502** |
        | sonst mindestens ein „kenne ich nicht" | `NotFound` | 404 |
        | nur Unzuständige | `NotResponsible` | 404 |

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
        failures: list[str] = []
        someone_looked = False

        for resolver in self._resolvers:
            if not resolver.handles(isin):
                continue
            result = resolver.resolve_isin(isin)
            if isinstance(result, ResolvedInstrument):
                return result
            if isinstance(result, Unavailable):
                failures.append(result.error)
            elif isinstance(result, NotFound):
                someone_looked = True

        if failures:
            logger.warning("resolve_chain_unavailable", isin=isin, sources=failures)
            return Unavailable(error="; ".join(failures))
        if someone_looked:
            return NotFound()
        return NotResponsible(reason="keine zuständige Quelle in der Kette")

"""ISIN → Symbol/Börse-Auflösung.

Primär über OpenFIGI (bevorzugte Börse, z.B. Xetra → Suffix ``.DE``), Fallback
über die Yahoo-Finance-Suche (fängt US-Aktien u.a. ohne Xetra-Listing).

Das Yahoo-Suffix wählt die *Börse* — die *Währung* wird NICHT daraus abgeleitet,
sondern stammt immer aus dem Live-Quote (siehe yfinance_provider).
"""

from dataclasses import dataclass

import structlog
import yfinance as yf

from app.providers.base import QUOTE_TYPE_MAP, InstrumentResolver, ResolvedInstrument
from app.providers.openfigi_provider import OpenFigiClient

logger = structlog.get_logger()


@dataclass(frozen=True)
class ExchangeDef:
    """Definition einer Börse: Anzeige, Yahoo-Suffix, OpenFIGI-Auflösung.

    ``currency`` ist nur Anzeige — die reale Kurswährung stammt aus dem Live-Quote.
    ``figi_value`` leer ⇒ der Dict-Key (MIC) wird als Auflösungswert verwendet.
    """

    suffix: str
    name: str
    region: str  # "germany" | "usa" | "europe" | "global"
    currency: str
    figi_id_type: str = "micCode"
    figi_value: str = ""


# Weltweite Börsentabelle: Key = MIC (bzw. 'US'). Erweiterbar per Zeile.
EXCHANGES: dict[str, ExchangeDef] = {
    # Amerika
    "US": ExchangeDef("", "NYSE / NASDAQ", "usa", "USD", "exchCode", "US"),
    "XTSE": ExchangeDef(".TO", "Toronto", "global", "CAD"),
    "XTSX": ExchangeDef(".V", "TSX Venture", "global", "CAD"),
    "BVMF": ExchangeDef(".SA", "São Paulo (B3)", "global", "BRL"),
    "XMEX": ExchangeDef(".MX", "Mexiko", "global", "MXN"),
    # Europa
    "XETR": ExchangeDef(".DE", "Xetra", "germany", "EUR"),
    "XFRA": ExchangeDef(".F", "Frankfurt", "germany", "EUR"),
    "XLON": ExchangeDef(".L", "London LSE", "europe", "GBp"),
    "XMIL": ExchangeDef(".MI", "Mailand", "europe", "EUR"),
    "XPAR": ExchangeDef(".PA", "Paris (Euronext)", "europe", "EUR"),
    "XAMS": ExchangeDef(".AS", "Amsterdam", "europe", "EUR"),
    "XBRU": ExchangeDef(".BR", "Brüssel", "europe", "EUR"),
    "XLIS": ExchangeDef(".LS", "Lissabon", "europe", "EUR"),
    "XMAD": ExchangeDef(".MC", "Madrid", "europe", "EUR"),
    "XWBO": ExchangeDef(".VI", "Wien", "europe", "EUR"),
    "XSWX": ExchangeDef(".SW", "SIX Swiss", "europe", "CHF"),
    "XSTO": ExchangeDef(".ST", "Stockholm", "europe", "SEK"),
    "XCSE": ExchangeDef(".CO", "Kopenhagen", "europe", "DKK"),
    "XOSL": ExchangeDef(".OL", "Oslo", "europe", "NOK"),
    "XHEL": ExchangeDef(".HE", "Helsinki", "europe", "EUR"),
    "XWAR": ExchangeDef(".WA", "Warschau", "europe", "PLN"),
    # Asien-Pazifik
    "XTKS": ExchangeDef(".T", "Tokio", "global", "JPY"),
    "XHKG": ExchangeDef(".HK", "Hongkong", "global", "HKD"),
    "XSHG": ExchangeDef(".SS", "Shanghai", "global", "CNY"),
    "XSHE": ExchangeDef(".SZ", "Shenzhen", "global", "CNY"),
    "XASX": ExchangeDef(".AX", "Sydney (ASX)", "global", "AUD"),
    "XSES": ExchangeDef(".SI", "Singapur", "global", "SGD"),
    "XNSE": ExchangeDef(".NS", "Indien NSE", "global", "INR"),
    "XBOM": ExchangeDef(".BO", "Indien BSE", "global", "INR"),
    "XKRX": ExchangeDef(".KS", "Korea (KRX)", "global", "KRW"),
    "XTAI": ExchangeDef(".TW", "Taiwan", "global", "TWD"),
    # Afrika / Nahost
    "XJSE": ExchangeDef(".JO", "Johannesburg", "global", "ZAR"),
    "XTAE": ExchangeDef(".TA", "Tel Aviv", "global", "ILS"),
}
DEFAULT_EXCHANGE = "XETR"


class OpenFigiResolver:
    """Löst ISINs über OpenFIGI zum Listing einer bevorzugten Börse auf."""

    def __init__(
        self, client: OpenFigiClient, default_exchange: str = DEFAULT_EXCHANGE
    ) -> None:
        """
        Args:
            client: OpenFIGI-Client für das ISIN→Ticker-Mapping.
            default_exchange: MIC der bevorzugten Börse (z.B. 'XETR').
        """
        self._client = client
        self._default_exchange = default_exchange

    def resolve_isin(self, isin: str) -> ResolvedInstrument | None:
        """Löst eine ISIN zum Yahoo-Symbol der konfigurierten Börse auf.

        Args:
            isin: ISIN des Wertpapiers.

        Returns:
            Aufgelöstes Instrument oder ``None``, wenn OpenFIGI kein Listing an
            der konfigurierten Börse kennt.
        """
        key = self._default_exchange
        exch = EXCHANGES.get(key)
        if exch is None:
            logger.warning("unknown_default_exchange", configured=key)
            key = DEFAULT_EXCHANGE
            exch = EXCHANGES[key]
        id_value = exch.figi_value or key
        ticker = self._client.map_isin(isin, id_value, id_type=exch.figi_id_type)
        if not ticker:
            logger.warning(
                "openfigi_resolve_empty", isin=isin, exchange=self._default_exchange
            )
            return None
        return ResolvedInstrument(
            symbol=f"{ticker}{exch.suffix}", isin=isin, exchange=exch.name
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

    def resolve_isin(self, isin: str) -> ResolvedInstrument | None:
        """Sucht das Listing der bevorzugten Börse zu einer ISIN über Yahoo.

        Args:
            isin: ISIN des Wertpapiers.

        Returns:
            Aufgelöstes Instrument oder ``None``, wenn nichts gefunden wurde.
        """
        try:
            quotes = yf.Search(isin).quotes
        except Exception as exc:
            # Netzwerk/Parsing kann fehlschlagen — defensiv behandeln.
            logger.warning("resolve_isin_failed", isin=isin, error=str(exc))
            return None

        if not quotes:
            logger.warning("resolve_isin_empty", isin=isin)
            return None

        top = self._passendster(quotes, isin)
        if top is None:
            logger.warning("resolve_isin_no_symbol", isin=isin)
            return None
        symbol = top["symbol"]

        quote_type = (top.get("quoteType") or "").upper()
        return ResolvedInstrument(
            symbol=symbol,
            isin=isin,
            exchange=top.get("exchDisp") or top.get("exchange"),
            name=top.get("shortname") or top.get("longname"),
            type=QUOTE_TYPE_MAP.get(quote_type),
            currency=None,  # Währung kommt aus dem Live-Quote, nicht aus der Suche
        )

    def _passendster(self, quotes: list[dict], isin: str) -> dict | None:
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

        Findet sich das bevorzugte Listing nicht, gewinnt der erste brauchbare
        Treffer — ein US-Papier ohne deutsche Notierung muss weiterhin
        durchgehen, dafür gibt es diesen Resolver überhaupt.

        Args:
            quotes: Trefferliste der Yahoo-Suche.
            isin: Nur fürs Protokoll.

        Returns:
            Der gewählte Treffer oder ``None``, wenn keiner ein Symbol trägt.
        """
        mit_symbol = [q for q in quotes if q.get("symbol")]
        if not mit_symbol:
            return None

        exchange = EXCHANGES.get(self._default_exchange) or EXCHANGES[DEFAULT_EXCHANGE]
        suffix = exchange.suffix

        if suffix:
            passend = next(
                (q for q in mit_symbol if str(q["symbol"]).endswith(suffix)), None
            )
        else:
            # Börse ohne Suffix (`US`): Dort ist das punktlose Symbol die
            # Notierung. Ohne diesen Zweig liefe die Regel leer, weil jedes
            # Symbol auf `''` endet.
            passend = next((q for q in mit_symbol if "." not in str(q["symbol"])), None)

        if passend is not None:
            return passend

        logger.info(
            "resolve_isin_andere_boerse",
            isin=isin,
            gewaehlt=mit_symbol[0]["symbol"],
            erwartet=self._default_exchange,
        )
        return mit_symbol[0]


class CompositeResolver:
    """Probiert mehrere Resolver der Reihe nach — erster Treffer gewinnt."""

    def __init__(self, *resolvers: InstrumentResolver) -> None:
        """
        Args:
            *resolvers: Resolver in Prioritätsreihenfolge.
        """
        self._resolvers = resolvers

    def resolve_isin(self, isin: str) -> ResolvedInstrument | None:
        """Gibt das erste erfolgreiche Auflösungsergebnis zurück."""
        for resolver in self._resolvers:
            result = resolver.resolve_isin(isin)
            if result is not None:
                return result
        return None

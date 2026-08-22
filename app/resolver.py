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


def _gattung(quote: dict) -> str:
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
        if preferred not in EXCHANGES:
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
        exch = EXCHANGES[mic]
        ticker = self._client.map_isin(
            isin, exch.figi_value or mic, id_type=exch.figi_id_type
        )
        if not ticker:
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

        top = self._passendster(quotes, isin)
        if top is None:
            logger.warning("resolve_isin_no_symbol", isin=isin)
            return NotFound()
        symbol = top["symbol"]

        return ResolvedInstrument(
            symbol=symbol,
            isin=isin,
            exchange=top.get("exchDisp") or top.get("exchange"),
            name=top.get("shortname") or top.get("longname"),
            type=QUOTE_TYPE_MAP.get(_gattung(top)),
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
        mit_symbol = [q for q in quotes if q.get("symbol")]
        if not mit_symbol:
            return None

        exchange = EXCHANGES.get(self._default_exchange) or EXCHANGES[DEFAULT_EXCHANGE]
        suffix = exchange.suffix

        if suffix:
            an_der_boerse = [q for q in mit_symbol if str(q["symbol"]).endswith(suffix)]
        else:
            # Börse ohne Suffix (`US`): Dort ist das punktlose Symbol die
            # Notierung. Ohne diesen Zweig liefe die Regel leer, weil jedes
            # Symbol auf `''` endet.
            an_der_boerse = [q for q in mit_symbol if "." not in str(q["symbol"])]

        if an_der_boerse:
            gattung = _gattung(mit_symbol[0])
            return next(
                (q for q in an_der_boerse if _gattung(q) == gattung),
                an_der_boerse[0],
            )

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
        ausfaelle: list[str] = []
        jemand_hat_nachgesehen = False

        for resolver in self._resolvers:
            if not resolver.handles(isin):
                continue
            result = resolver.resolve_isin(isin)
            if isinstance(result, ResolvedInstrument):
                return result
            if isinstance(result, Unavailable):
                ausfaelle.append(result.error)
            elif isinstance(result, NotFound):
                jemand_hat_nachgesehen = True

        if ausfaelle:
            logger.warning("resolve_chain_unavailable", isin=isin, quellen=ausfaelle)
            return Unavailable(error="; ".join(ausfaelle))
        if jemand_hat_nachgesehen:
            return NotFound()
        return NotResponsible(reason="keine zuständige Quelle in der Kette")

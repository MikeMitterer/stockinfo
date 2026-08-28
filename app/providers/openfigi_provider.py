"""ISIN→Ticker-Mapping über die OpenFIGI-API (gratis).

Findet zu einer ISIN gezielt den Ticker einer bevorzugten Börse (z.B. Xetra).
Yahoos eigene ISIN-Suche liefert diese Notiz nicht — daher OpenFIGI davor.
"""

import re
from dataclasses import dataclass
from typing import Any

import httpx
import structlog

from app.providers.base import SourceUnavailableError

logger = structlog.get_logger()

_ENDPOINT = "https://api.openfigi.com/v3/mapping"

# Börsen, die OpenFIGI **nicht** über ihren MIC adressiert. Nur Ausnahmen.
#
# Der Regelfall braucht keinen Eintrag: `micCode` mit dem MIC selbst. Hier
# steht, wo OpenFIGI davon abweicht — `US` ist sein Composite für NYSE und
# NASDAQ und wird über ein anderes Feld gesucht.
#
# Bis T-21 trugen diese beiden Angaben als Spalten in `ExchangeDef` mit, also
# in der Börsentabelle der App. Dort waren sie am falschen Ort: Sie sagen
# nichts über die Börse, sondern über **einen Anbieter**. Die nächste
# Kursquelle hätte ihre eigenen zwei Spalten danebengestellt.
_FIGI_EXCEPTIONS: dict[str, tuple[str, str]] = {
    "US": ("exchCode", "US"),
}


def figi_lookup(mic: str) -> tuple[str, str]:
    """Wie OpenFIGI nach dieser Börse zu fragen ist.

    Args:
        mic: MIC der Börse — oder ein Sammelcode der eigenen Tabelle.

    Returns:
        `(id_type, id_value)` für die Anfrage: im Regelfall
        ``("micCode", mic)``.
    """
    return _FIGI_EXCEPTIONS.get(mic, ("micCode", mic))

# Zeichen, die ein Yahoo-Symbol tragen kann: Buchstaben, Ziffern, Punkt,
# Bindestrich, Zirkumflex (Indizes) und Gleichheitszeichen (Devisen/Futures).
_YAHOO_SYMBOL_PATTERN = re.compile(r"^[A-Za-z0-9.^=-]+$")


@dataclass(frozen=True)
class FigiMatch:
    """Ein OpenFIGI-Treffer, so weit die App ihn braucht.

    Warum ein Datensatz und keine drei Rückgabewerte: `map_isin` wird an einer
    Stelle gerufen und in fünf Tests nachgestellt. Ein Tupel hätte dort überall
    eine Stellenordnung eingeführt, die niemand liest.
    """

    ticker: str
    name: str | None = None
    instrument_type: str | None = None
    """``"etf"``, ``"stock"`` oder ``None`` — das Vokabular der App."""


# OpenFIGIs Gattungen in die zwei Begriffe der App. Die Liste ist bewusst
# **kurz und wörtlich**: Was hier nicht steht, wird zu ``None`` und nicht
# geraten. Ein falsch geratenes „stock" wäre schlimmer als kein Wert — es
# schaltete die ETF-Anreicherung stillschweigend ab, und genau dieser Fehler
# ist der Anlass des Tickets.
#
# Gemessen: `IE00B4L5Y983` liefert `securityType: "ETP"`, `securityType2:
# "Mutual Fund"`. Beide Felder werden geprüft, weil OpenFIGI die Gattung je
# nach Papier im einen oder anderen führt.
_FIGI_TYPES: dict[str, str] = {
    "ETP": "etf",
    "MUTUAL FUND": "etf",
    "OPEN-END FUND": "etf",
    "COMMON STOCK": "stock",
    "EQUITY": "stock",
    "DEPOSITARY RECEIPT": "stock",
    "REIT": "stock",
}


def _instrument_type(entry: dict[str, Any]) -> str | None:
    """Die Gattung eines Treffers, oder ``None`` wenn OpenFIGI keine nennt."""
    for field in ("securityType", "securityType2"):
        value = entry.get(field)
        if isinstance(value, str):
            mapped = _FIGI_TYPES.get(value.strip().upper())
            if mapped:
                return mapped
    return None


def _is_yahoo_compatible_symbol(ticker: str) -> bool:
    """Könnte dieser FIGI-Ticker ein Yahoo-Symbol sein?

    OpenFIGI liefert Bloomberg-Bezeichner, und die sind nicht durchweg
    Symbole. Zur Vorzugsaktie `CA78012H5675` kommt `RY V3.65 PERP BB` zurück;
    mit Börsensuffix wird daraus `RY V3.65 PERP BB.TO`, und yfinance antwortet
    darauf 404. Schlimmer als der Fehlschlag ist seine Nebenwirkung: Der
    `CompositeResolver` prüft auf ``None``, nicht auf Brauchbarkeit — ein
    solcher „Treffer" verdeckt also den Yahoo-Fallback, der das Papier
    vielleicht gefunden hätte.

    **Das ist eine Plausibilitätsprüfung, keine Zusage.** Sie sortiert aus, was
    als Symbol nicht funktionieren *kann*; ob Yahoo den Rest kennt, sagt sie
    nicht. `RY.PR.H` — die TSX-Schreibweise derselben Vorzugsaktie — käme
    durch, und Yahoo führt sie trotzdem nicht. Wer mehr will, braucht einen
    Abgleich gegen eine Symbolliste, nicht einen strengeren Ausdruck.

    Geprüft wird die Zeichenmenge und nicht die Gattung. `marketSector`
    auszuwerten wäre naheliegend, ginge aber zu weit: Vorzugsaktien und
    Anleihen sind handelbare Papiere, die jemand aufnehmen können soll, sobald
    ein brauchbares Symbol dafür vorliegt.

    Der Filter ist ein Schutz, keine Lösung. OpenFIGI ordnet Kennungen zu —
    ISIN, FIGI, Gattung, Handelsplatz — und ist kein Yahoo-Symbol-Resolver;
    das blinde Anhängen eines Börsensuffixes bleibt bis auf Weiteres eine
    Annahme. Die Trennung von Instrument-, Listing- und Anbieter-Identität
    gehört in die Identitäts- und Plugin-Tickets (T-21 ff.), nicht hierher.

    Args:
        ticker: Ticker aus der OpenFIGI-Antwort.

    Returns:
        ``True`` wenn der Ticker als Yahoo-Symbol taugen kann.
    """
    return bool(_YAHOO_SYMBOL_PATTERN.match(ticker))


class OpenFigiClient:
    """Mappt ISINs über OpenFIGI auf den Ticker einer bestimmten Börse.

    Auflösung entweder über ``micCode`` (einzelne Börse, z.B. Xetra) oder
    ``exchCode`` (z.B. das US-Composite über alle US-Börsen hinweg).
    """

    def __init__(self, api_key: str = "", timeout: float = 15.0) -> None:
        """
        Args:
            api_key: Optionaler OpenFIGI-API-Key (höheres Rate-Limit).
            timeout: HTTP-Timeout in Sekunden.
        """
        self._api_key = api_key
        self._timeout = timeout

    def map_isin(
        self, isin: str, id_value: str, id_type: str = "micCode"
    ) -> FigiMatch | None:
        """Liefert den Treffer zu einer ISIN an einer Börse.

        Args:
            isin: ISIN des Wertpapiers.
            id_value: Wert des Auflösungsmerkmals (z.B. 'XETR' für micCode,
                'US' für exchCode).
            id_type: OpenFIGI-Feld — 'micCode' (einzelne Börse) oder 'exchCode'
                (z.B. das US-Composite).

        Returns:
            `FigiMatch` mit Ticker (z.B. 'VGWL'), Name und Gattung — oder
            ``None``, wenn OpenFIGI das Papier an dieser Börse **nicht
            kennt**. Bis T-35 kam hier nur der Ticker zurück; Name und
            Gattung standen in derselben Antwort und wurden verworfen.

        Raises:
            SourceUnavailableError: Der Dienst war nicht erreichbar oder hat
                mit einem Fehler geantwortet. Früher kam auch dieser Fall als
                ``None`` zurück — ununterscheidbar von „kenne ich nicht", und
                damit wurde aus einem Ausfall ein 404.
        """
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["X-OPENFIGI-APIKEY"] = self._api_key
        payload = [{"idType": "ID_ISIN", "idValue": isin, id_type: id_value}]
        try:
            response = httpx.post(
                _ENDPOINT, json=payload, headers=headers, timeout=self._timeout
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.warning(
                "openfigi_failed",
                isin=isin,
                id_type=id_type,
                id_value=id_value,
                error=str(exc),
            )
            raise SourceUnavailableError(f"openfigi: {exc}") from exc
        return self._extract_match(data)

    @staticmethod
    def _extract_ticker(data: Any) -> str | None:
        """Extrahiert den ersten brauchbaren Ticker aus der OpenFIGI-Antwort.

        Returns:
            Der Ticker, oder ``None`` wenn die Antwort keinen enthält oder er
            als Yahoo-Symbol nicht taugt (siehe `_is_yahoo_compatible_symbol`).
        """
        match = OpenFigiClient._extract_match(data)
        return match.ticker if match else None

    @staticmethod
    def _extract_match(data: Any) -> FigiMatch | None:
        """Der erste brauchbare Treffer — Ticker **samt Name und Gattung**.

        **Bis T-35 hat diese Antwort nur den Ticker überlebt.** OpenFIGI
        schickt in derselben Antwort auch `name` und `securityType`; sie
        wurden hier weggeworfen. Gemessen am 2026-08-28 für `IE00B4L5Y983`:

            {"ticker": "EUNL", "name": "ISHARES CORE MSCI WORLD",
             "securityType": "ETP", "securityType2": "Mutual Fund", …}

        Die Folge war doppelt sichtbar: Die Oberfläche zeigte keinen Namen,
        und weil `type` leer blieb, hielt sie den ETF für eine Aktie — womit
        justETF **gar nicht erst gefragt** wurde. TER, Anbieter, Domizil und
        Fondsvolumen blieben für jedes Papier dauerhaft leer.
        """
        if not isinstance(data, list) or not data:
            return None
        entry = data[0]
        results = entry.get("data") if isinstance(entry, dict) else None
        if not results:
            return None
        first = results[0]
        ticker = first.get("ticker")
        if ticker and not _is_yahoo_compatible_symbol(ticker):
            logger.info("openfigi_ticker_unusable", ticker=ticker)
            return None
        if not ticker:
            return None
        return FigiMatch(
            ticker=ticker,
            name=first.get("name") or None,
            instrument_type=_instrument_type(first),
        )

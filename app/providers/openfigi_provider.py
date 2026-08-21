"""ISIN→Ticker-Mapping über die OpenFIGI-API (gratis).

Findet zu einer ISIN gezielt den Ticker einer bevorzugten Börse (z.B. Xetra).
Yahoos eigene ISIN-Suche liefert diese Notiz nicht — daher OpenFIGI davor.
"""

import re
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()

_ENDPOINT = "https://api.openfigi.com/v3/mapping"

# Zeichen, die ein Yahoo-Symbol tragen kann: Buchstaben, Ziffern, Punkt,
# Bindestrich, Zirkumflex (Indizes) und Gleichheitszeichen (Devisen/Futures).
_YAHOO_SYMBOL_PATTERN = re.compile(r"^[A-Za-z0-9.^=-]+$")


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
    ) -> str | None:
        """Liefert den Ticker einer ISIN an einer Börse.

        Args:
            isin: ISIN des Wertpapiers.
            id_value: Wert des Auflösungsmerkmals (z.B. 'XETR' für micCode,
                'US' für exchCode).
            id_type: OpenFIGI-Feld — 'micCode' (einzelne Börse) oder 'exchCode'
                (z.B. das US-Composite).

        Returns:
            Ticker (z.B. 'VGWL') oder ``None``, wenn kein Mapping gefunden wird.
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
            return None
        return self._extract_ticker(data)

    @staticmethod
    def _extract_ticker(data: Any) -> str | None:
        """Extrahiert den ersten brauchbaren Ticker aus der OpenFIGI-Antwort.

        Returns:
            Der Ticker, oder ``None`` wenn die Antwort keinen enthält oder er
            als Yahoo-Symbol nicht taugt (siehe `_ist_symbolfaehig`).
        """
        if not isinstance(data, list) or not data:
            return None
        entry = data[0]
        results = entry.get("data") if isinstance(entry, dict) else None
        if not results:
            return None
        ticker = results[0].get("ticker")
        if ticker and not _is_yahoo_compatible_symbol(ticker):
            logger.info("openfigi_ticker_unbrauchbar", ticker=ticker)
            return None
        return ticker

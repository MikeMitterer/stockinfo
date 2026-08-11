"""ISIN→Ticker-Mapping über die OpenFIGI-API (gratis).

Findet zu einer ISIN gezielt den Ticker einer bevorzugten Börse (z.B. Xetra).
Yahoos eigene ISIN-Suche liefert diese Notiz nicht — daher OpenFIGI davor.
"""

from typing import Any

import httpx
import structlog

logger = structlog.get_logger()

_ENDPOINT = "https://api.openfigi.com/v3/mapping"


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
        """Extrahiert den ersten Ticker aus der OpenFIGI-Antwortstruktur."""
        if not isinstance(data, list) or not data:
            return None
        entry = data[0]
        results = entry.get("data") if isinstance(entry, dict) else None
        if not results:
            return None
        return results[0].get("ticker")

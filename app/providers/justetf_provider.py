"""ETF-Anreicherung (TER, Anbieter, Replikation, Fondsgröße) über justETF.

justETF wird gescraped — die Abfrage ist langsamer und fragiler als yfinance.
Daher strikt best-effort: bei jedem Fehler ``None`` und Weiterarbeit ohne
ETF-Extras.
"""

from typing import Any

import justetf_scraping
import structlog

from app.providers.base import EtfDetails

logger = structlog.get_logger()

# justETF listet ausschließlich europäische UCITS-ETFs. Deren Fonds-Domizil ist am
# ISIN-Länderpräfix erkennbar (EU + EEA + CH/UK). Für andere ISINs (US, CA, JP …) hat
# justETF keine Daten — dort wird gar nicht erst gescraped (spart einen langsamen,
# sicher fehlschlagenden Netz-Aufruf pro Refresh). Bewusst großzügige Allow-List, damit
# kein echter europäischer ETF verloren geht.
_EUROPEAN_DOMICILES = frozenset(
    {
        # EU
        "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
        "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
        "SI", "ES", "SE",
        # EEA
        "IS", "LI", "NO",
        # Schweiz, UK
        "CH", "GB",
    }
)


def is_european_isin(isin: str) -> bool:
    """Prüft anhand des ISIN-Länderpräfix, ob ein europäisches UCITS-Domizil vorliegt.

    Args:
        isin: ISIN des Wertpapiers.

    Returns:
        ``True`` bei europäischem Domizil (EU/EEA/CH/UK), sonst ``False``.
    """
    return len(isin) >= 2 and isin[:2].upper() in _EUROPEAN_DOMICILES


class JustEtfProvider:
    """Reichert ETF-Daten anhand der ISIN über justETF (Scraping) an."""

    def fetch_etf(self, isin: str) -> EtfDetails | None:
        """Holt ETF-Zusatzdaten zu einer ISIN.

        Args:
            isin: ISIN des ETFs.

        Returns:
            EtfDetails oder ``None``, wenn justETF nichts liefert bzw.
            fehlschlägt.
        """
        if not is_european_isin(isin):
            # Nicht-europäische ISIN → justETF hat garantiert nichts, kein Scrape.
            logger.debug("justetf_skipped_non_european", isin=isin)
            return None

        try:
            overview = justetf_scraping.get_etf_overview(isin)
        except Exception as exc:
            logger.warning("justetf_fetch_failed", isin=isin, error=str(exc))
            return None

        if not overview:
            return None

        # get_etf_overview liefert ein TypedDict → Zugriff per dict.get().
        return EtfDetails(
            ter=self._as_float(overview.get("ter")),
            provider=overview.get("fund_provider"),
            replication=overview.get("replication"),
            fund_size=self._as_float(overview.get("fund_size_eur")),
            currency=overview.get("fund_currency"),
            name=overview.get("name"),
            volatility=self._as_float(overview.get("volatility_1y")),
            accumulating=self._as_accumulating(overview.get("distribution_policy")),
        )

    @staticmethod
    def _as_accumulating(policy: Any) -> bool | None:
        """Leitet aus der Ausschüttungspolitik ab, ob der ETF thesauriert.

        Args:
            policy: justETF-Feld ``distribution_policy`` (z.B. 'Accumulating',
                'Distributing').

        Returns:
            ``True`` bei thesaurierend, ``False`` bei ausschüttend, ``None``
            wenn unbekannt.
        """
        if not isinstance(policy, str) or not policy.strip():
            return None
        return policy.strip().lower().startswith("accumul")

    @staticmethod
    def _as_float(value: Any) -> float | None:
        """Konvertiert einen Wert defensiv nach float; ``None`` bei Fehler."""
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

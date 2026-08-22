"""Mehrere ETF-Quellen hintereinander — die erste zuständige gewinnt.

Das Gegenstück zu `CompositeResolver` auf der Metadaten-Seite: Welche Quelle ein
Papier führt, hängt an seinem Domizil, und keine einzelne deckt alle ab.
"""

import structlog

from app.providers.base import EtfDetails, EtfEnricher

logger = structlog.get_logger()


class CompositeEtfEnricher:
    """Fragt die ETF-Quellen der Reihe nach, überspringt die unzuständigen."""

    def __init__(self, *enrichers: EtfEnricher) -> None:
        """
        Args:
            enrichers: Quellen in der Reihenfolge ihres Vorrangs. Für ein
                Papier, das mehrere führen, gewinnt die erste.
        """
        self._enrichers = enrichers

    def is_responsible(
        self,
        isin: str | None,
        *,
        exchange: str | None = None,
        currency: str | None = None,
    ) -> bool:
        """Führt **irgendeine** der Quellen dieses Papier?

        Das ``False`` ist die wichtigere Antwort: Es sagt dem QuoteService, dass
        es hier nichts zu holen und damit auch keinen gepflegten Stand zu
        schützen gibt — siehe `QuoteService._build`.

        Args:
            isin: ISIN des Wertpapiers, sofern bekannt.
            exchange: Anzeigename des Handelsplatzes — beantwortet die Frage
                zusammen mit der Währung auch ohne ISIN.
            currency: Handelswährung des Kurses.

        Returns:
            ``True``, sobald eine Quelle zuständig ist.
        """
        return any(
            enricher.is_responsible(isin, exchange=exchange, currency=currency)
            for enricher in self._enrichers
        )

    def fetch_etf(
        self,
        isin: str | None,
        symbol: str | None = None,
        *,
        exchange: str | None = None,
        currency: str | None = None,
    ) -> EtfDetails | None:
        """Holt die ETF-Details von der ersten zuständigen Quelle, die liefert.

        Eine unzuständige Quelle wird gar nicht erst gefragt — sonst kostete
        jeder US-ETF einen justETF-Scrape, der garantiert nichts findet. Fällt
        eine zuständige Quelle aus, kommt die nächste zuständige dran; erst
        wenn keine etwas liefert, ist die Antwort ``None`` und der gespeicherte
        Stand bleibt geschützt.

        Args:
            isin: ISIN des ETFs, sofern bekannt.
            symbol: Yahoo-Symbol, für Quellen die damit arbeiten.
            exchange: Anzeigename des Handelsplatzes — entscheidet ohne ISIN
                mit über die Zuständigkeit.
            currency: Handelswährung des Kurses.

        Returns:
            Die erste nicht-leere Antwort, sonst ``None``.
        """
        for enricher in self._enrichers:
            if not enricher.is_responsible(isin, exchange=exchange, currency=currency):
                continue
            details = enricher.fetch_etf(isin, symbol=symbol)
            if details is not None:
                return details
        return None

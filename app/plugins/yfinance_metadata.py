"""Die vorhandene yfinance-ETF-Anbindung in der Metadata-Rolle.

Der letzte eingebaute Sonderweg. Bis Runde 3 baute die Registry für
`etf_meta` noch direkt einen `YFinanceEtfEnricher` — eine eingebaute Quelle,
die an der Rollenschicht vorbeilief, während alle anderen hindurchgingen. Genau
die Sonderbehandlung, die T-23 auflösen soll.

Wie bei justETF steht hier **keine** Fachlogik: Welche Papiere Yahoo für ETFs
führt und wann es sich heraushält, entscheidet `YFinanceEtfEnricher`.

**Und wie bei justETF stößt der Vertrag hier an eine Grenze.** Die
Zuständigkeitsregel braucht Börse und Währung — `ResolveRequest` kennt beides
nicht. Die vollständige Regel steht deshalb in `is_responsible` neben
`handles`; der Adapter benutzt sie, wenn der Core die Angaben hat. Ob
`ResolveRequest` dafür wächst, ist eine Entscheidung am Vertrag und gehört
nicht in dieses Ticket.
"""

from typing import Any

from stockinfo_plugin import FieldSpec, MetadataSource, Reading, ResolveRequest

from app.providers.yfinance_etf_provider import YFinanceEtfEnricher

FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec(
        "provider", kind="text", label_en="Fund provider", label_de="Anbieter"
    ),
    FieldSpec("name", kind="text", label_en="Name", label_de="Name"),
)
"""Was Yahoo für ETFs liefert — deutlich weniger als justETF.

Genau deshalb steht justETF in der Vorgabekette **vorn**: Für europäische
UCITS-Papiere hat es ungleich mehr. Yahoo ist der Weg für alles andere.
"""

_BY_NAME = {spec.name: spec for spec in FIELDS}


class YFinanceMetadataPlugin(MetadataSource):
    """ETF-Anbieter und Name von Yahoo, in der Metadata-Rolle."""

    name = "yfinance"
    cost = "free"

    FIELDS = FIELDS

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        *,
        enricher: YFinanceEtfEnricher | None = None,
    ) -> None:
        """
        Args:
            config: Der eigene Abschnitt aus der Quellen-Konfiguration.
            enricher: Die vorhandene Anbindung; im Test wird eine
                hereingereicht.
        """
        super().__init__(config)
        self._enricher = enricher or YFinanceEtfEnricher()

    def handles(self, request: ResolveRequest) -> bool:
        """Die gröbere Auskunft — ohne Börse und Währung (siehe Modul-Docstring)."""
        return self.is_responsible(request.isin)

    def is_responsible(
        self,
        isin: str | None,
        *,
        exchange: str | None = None,
        currency: str | None = None,
    ) -> bool:
        """Die **vollständige** Regel — geholt, nicht nachgebaut."""
        return self._enricher.is_responsible(
            isin, exchange=exchange, currency=currency
        )

    def fetch(self, request: ResolveRequest) -> list[Reading] | None:
        """Holt Anbieter und Namen.

        Returns:
            ``[]`` bei Unzuständigkeit, ``None`` wenn Yahoo nichts liefert,
            sonst die Messwerte. Die drei Ausgänge bedeuten Verschiedenes —
            siehe `JustEtfMetadataPlugin.fetch`.
        """
        if not self.is_responsible(request.isin):
            return []

        details = self._enricher.fetch_etf(request.isin, request.symbol)
        if details is None:
            return None

        readings = [
            Reading(field=spec.name, value=getattr(details, spec.name), source=self.name)
            for spec in FIELDS
            if getattr(details, spec.name, None) is not None
        ]
        return readings or None

    def declared(self, name: str) -> FieldSpec | None:
        """Wie ein Feld zu lesen ist — oder ``None``, wenn es nicht von hier stammt."""
        return _BY_NAME.get(name)

    def configuration_problem(self) -> str:
        """Yahoo braucht keinen Schlüssel — und sagt das."""
        return ""

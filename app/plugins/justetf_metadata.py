"""Die vorhandene justETF-Anbindung in der Metadata-Rolle des Plugin-Vertrags.

Wie beim OpenFIGI-Resolver ist der Punkt, was **nicht** hier steht: das
Abrufen, das Auslesen der Felder, die Erkennung thesaurierender Fonds, die
Zuständigkeitsregel für europäische Listings. Das alles steht in
`app/providers/justetf_provider.py` und wird von hier benutzt.

Übersetzt wird nur in die Sprache des Vertrags — und das ist hier mehr Arbeit
als beim Resolver, weil die beiden Seiten die Daten verschieden schneiden:

    EtfDetails (ein Datensatz mit festen Feldern)
        →  list[Reading] (je Feld ein Messwert mit Einheit und Herkunft)

Der Grund für den Unterschied ist der interessantere Teil. `EtfDetails` ist ein
Datensatz **dieser App**: Wer ein Feld hinzufügt, ändert die Klasse. `Reading`
ist die Form für Werte, die eine **fremde** Quelle liefert — sie trägt ihre
Einheit und ihre Herkunft mit sich, damit ein Feld, das die App nicht kennt,
trotzdem ankommen kann. Genau deshalb ist die Metadata-Rolle so geschnitten.
"""

from typing import Any

from stockinfo_plugin import FieldSpec, MetadataSource, Reading, ResolveRequest, Unit

from app.providers.base import EtfDetails
from app.providers.justetf_provider import JustEtfProvider, is_european_isin

# Was justETF liefert, in der Form des Vertrags. Die Deklaration ist **nicht**
# Zierde: Sie sagt der App, wie ein Wert zu lesen ist (Prozent, Betrag, Text)
# und wie er heißt, wenn sie ihn anzeigt.
DECLARED: tuple[FieldSpec, ...] = (
    FieldSpec(
        "ter",
        kind="number",
        unit=Unit.PERCENT,
        plausible=(0.0, 5.0),
        label_en="Total expense ratio",
        label_de="Gesamtkostenquote",
    ),
    FieldSpec("provider", kind="text", label_en="Fund provider", label_de="Anbieter"),
    FieldSpec("replication", kind="text", label_en="Replication", label_de="Replikation"),
    FieldSpec(
        "fund_size",
        kind="number",
        unit=Unit.ABSOLUTE,
        label_en="Fund size",
        label_de="Fondsvolumen",
    ),
    FieldSpec(
        "fund_currency",
        kind="text",
        label_en="Fund currency",
        label_de="Fondswährung",
    ),
    FieldSpec(
        "fund_domicile", kind="text", label_en="Fund domicile", label_de="Fondsdomizil"
    ),
    FieldSpec(
        "volatility",
        kind="number",
        unit=Unit.PERCENT,
        plausible=(0.0, 200.0),
        label_en="Volatility (1y)",
        label_de="Volatilität (1 Jahr)",
    ),
    FieldSpec(
        "accumulating",
        kind="bool",
        label_en="Accumulating",
        label_de="Thesaurierend",
    ),
)

_BY_NAME = {spec.name: spec for spec in DECLARED}


class JustEtfMetadataPlugin(MetadataSource):
    """ETF-Kennzahlen von justETF, in der Metadata-Rolle."""

    name = "justetf"
    cost = "free"

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        *,
        provider: JustEtfProvider | None = None,
    ) -> None:
        """
        Args:
            config: Der eigene Abschnitt aus der Quellen-Konfiguration.
            provider: Die vorhandene Anbindung. Ohne Angabe eine neue — im Test
                wird hier eine hereingereicht, ohne dass dieses Modul dafür
                etwas vorsehen müsste.
        """
        super().__init__(config)
        self._provider = provider or JustEtfProvider()

    def handles(self, request: ResolveRequest) -> bool:
        """justETF kennt europäische Fonds.

        Die Regel steht in `is_european_isin` und wird von dort geholt. Sie hier
        noch einmal zu formulieren hieße, sie beim ersten Sonderfall zweimal zu
        pflegen — und der Sonderfall wäre dann in genau einer der beiden
        Fassungen berücksichtigt.
        """
        return bool(request.isin) and is_european_isin(request.isin)

    def fetch(self, request: ResolveRequest) -> list[Reading] | None:
        """Holt die Kennzahlen und macht daraus Messwerte.

        Returns:
            Je gefülltem Feld ein `Reading`. ``None``, wenn justETF nichts
            liefert — **nicht** eine leere Liste: „nichts gefunden" und „ein
            Fonds ohne jede Kennzahl" sind zwei verschiedene Aussagen, und nur
            die zweite ist ein Ergebnis.
        """
        if not self.handles(request):
            return None

        details = self._provider.fetch_etf(request.isin or "")
        if details is None:
            return None

        return as_readings(details, self.name) or None

    def declared(self, name: str) -> FieldSpec | None:
        """Wie ein Feld zu lesen ist — oder ``None``, wenn es nicht von hier stammt."""
        return _BY_NAME.get(name)

    def configuration_problem(self) -> str:
        """justETF braucht keinen Schlüssel — und sagt das."""
        return ""


def as_readings(details: EtfDetails, source: str = "justetf") -> list[Reading]:
    """`EtfDetails` → Messwerte. Die **einzige** Stelle, an der das passiert.

    `fetch` ruft sie auf; ein Test kann sie ohne Netz aufrufen. Sie zweimal zu
    schreiben — einmal im Abrufweg, einmal für die Prüfung — hätte bedeutet,
    dass eine Prüfung ihre eigene Übersetzung mitbringt und damit sich selbst
    bestätigt.

    Leere Felder fallen weg: Ein `Reading` mit ``None`` wäre die Aussage „dieser
    Wert ist None", und das ist etwas anderes als „justETF nennt ihn nicht".
    """
    return [
        Reading(
            field=spec.name,
            value=getattr(details, spec.name),
            unit=spec.unit,
            source=source,
        )
        for spec in DECLARED
        if getattr(details, spec.name, None) is not None
    ]

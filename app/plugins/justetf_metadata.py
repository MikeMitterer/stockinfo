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
from app.exchanges import EXCHANGES
from app.providers.justetf_provider import JustEtfProvider

FUND_SIZE_CURRENCY = "EUR"
"""Die Währung des Fondsvolumens — **fest, weil die Anbindung es so liest.**

`JustEtfProvider` nimmt `overview["fund_size_eur"]`. Der Wert ist also schon
umgerechnet, und `fund_currency` beschreibt etwas anderes: die Währung des
Fonds selbst. Beides zu verwechseln verfälscht den Betrag um den Wechselkurs.

Sollte die Anbindung eines Tages den Originalbetrag lesen, gehört diese
Konstante mit ihr zusammen geändert — deshalb steht sie hier und nicht als
Zeichenkette mitten im Code.
"""

# Was justETF liefert, in der Form des Vertrags. Die Deklaration ist **nicht**
# Zierde: Sie sagt der App, wie ein Wert zu lesen ist (Prozent, Betrag, Text)
# und wie er heißt, wenn sie ihn anzeigt.
FIELDS: tuple[FieldSpec, ...] = (
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

_BY_NAME = {spec.name: spec for spec in FIELDS}


class JustEtfMetadataPlugin(MetadataSource):
    """ETF-Kennzahlen von justETF, in der Metadata-Rolle."""

    name = "justetf"
    cost = "free"
    api_version = 2
    SUPPORTED_KINDS = frozenset({"listed"})
    SUPPORTED_TYPES = frozenset({"etf", "etc"})

    FIELDS = FIELDS
    """Was diese Quelle liefert — **der Vertrag fragt danach.**

    Ohne diese Deklaration weiß die App nicht, wie sie einen Wert behandeln
    soll: ob er Prozent ist, ein Betrag oder Text, und wie er heißt, wenn er
    angezeigt wird. `MetadataContract.test_felder_sind_deklariert` hat genau
    das gefunden — die erste Fassung ließ die Angabe leer.
    """

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

        **Die vollständige Regel, ausgedrückt im Vertrag.** Ohne ISIN
        entscheidet das Listing: `JustEtfProvider.is_responsible` nimmt dafür
        Handelswährung und Börsenname. Die Währung trägt `ResolveRequest` seit
        T-23; den Börsennamen holt diese Methode aus `EXCHANGES` zum
        `preferred_mic`.

        Bis Runde 4 stand hier ein zusätzliches `is_responsible` neben
        `handles` — ein Sondervertrag, den nur die eingebauten Quellen hatten.
        Ein fremdes Plugin konnte die Regel damit gar nicht formulieren, und
        die „einheitliche Schnittstelle" war eine Behauptung.
        """
        definition = EXCHANGES.get(request.preferred_mic)
        return self._provider.is_responsible(
            request.isin,
            exchange=definition.name if definition else None,
            currency=request.currency,
        )

    def fetch(self, request: ResolveRequest) -> list[Reading] | None:
        """Holt die Kennzahlen und macht daraus Messwerte.

        Returns:
            Je gefülltem Feld ein `Reading`. **Drei Ausgänge, drei Bedeutungen:**

            * ``[]`` — nicht zuständig. Der Aufrufer fragt die nächste Quelle.
            * ``None`` — zuständig, aber justETF kennt das Papier nicht. Der
              Aufrufer hört auf zu suchen.
            * eine gefüllte Liste — Kennzahlen.

            Die ersten beiden zu vertauschen ist der Fehler, den der Vertrag
            gefunden hat: Er sieht von außen gleich aus und ändert, wie weit die
            Kette läuft.
        """
        if not self.handles(request):
            # **Leere Liste, nicht `None`** — Befund des Vertrags. „Nicht
            # zuständig" und „zuständig, nichts gefunden" sind zwei Aussagen,
            # und der Aufrufer darf sie nicht verwechseln: Beim ersten fragt er
            # die nächste Quelle, beim zweiten hört er auf.
            return []

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
            # **Ein absoluter Betrag ohne Währung ist bedeutungslos** — dieselbe
            # Regel, die für Kurse gilt, und ein Befund des Vertrags.
            #
            # Die Währung ist **EUR und nicht `fund_currency`.** Der Provider
            # liest `overview["fund_size_eur"]`; das Volumen ist also bereits
            # umgerechnet. `fund_currency` ist die Währung des **Fonds** — bei
            # `IE00B4L5Y983` USD —, und den EUR-Betrag damit zu beschriften
            # hätte ihn um den Wechselkurs verfälscht, ohne dass irgendwo ein
            # Fehler entstünde. Zweiter Befund derselben Sorte in diesem
            # Ticket: Der Wert stimmte, seine Bedeutung nicht.
            currency=FUND_SIZE_CURRENCY if spec.unit is Unit.ABSOLUTE else None,
        )
        for spec in FIELDS
        if getattr(details, spec.name, None) is not None
    ]

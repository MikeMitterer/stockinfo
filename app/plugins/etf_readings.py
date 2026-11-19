"""`EtfDetails` → Messwerte des Plugin-Vertrags, für die eigenen Metadaten-Plugins."""

from stockinfo_plugin import FieldSpec, Reading
from stockinfo_plugin.types import MONEY_UNITS

from app.providers.base import EtfDetails


def etf_readings(
    details: EtfDetails,
    source: str,
    fields: tuple[FieldSpec, ...],
    money_currency: str | None,
) -> list[Reading]:
    """`EtfDetails` → Messwerte. Die **einzige** Stelle, an der das passiert.

    justETF und Yahoo rufen sie mit ihrer Feldliste; ein Test kann sie ohne
    Netz aufrufen. Sie zweimal zu schreiben — einmal im Abrufweg, einmal für
    die Prüfung — hätte bedeutet, dass eine Prüfung ihre eigene Übersetzung
    mitbringt und damit sich selbst bestätigt.

    Leere Felder fallen weg: Ein `Reading` mit ``None`` wäre die Aussage „dieser
    Wert ist None", und das ist etwas anderes als „die Quelle nennt ihn nicht".

    Args:
        details: Die Antwort des Providers.
        source: Name der Quelle im `Reading`.
        fields: Die Felder, die diese Quelle deklariert.
        money_currency: Währung eines Betrags (Einheit aus `MONEY_UNITS`);
            **ein Betrag ohne Währung ist bedeutungslos**, auch in Millionen.
    """
    return [
        Reading(
            field=spec.name,
            value=getattr(details, spec.name),
            unit=spec.unit,
            source=source,
            currency=money_currency if spec.unit in MONEY_UNITS else None,
        )
        for spec in fields
        if getattr(details, spec.name, None) is not None
    ]

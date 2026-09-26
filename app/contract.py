"""Zugriff auf das Vertragsartefakt `contract/core-contract.json`.

Eine Datei, zwei Leser: Die Fixtures werden beim Bauen dagegen geprüft
(`tests/test_contract.py`), `GET /fields` beantwortet sie im Betrieb. Zwei
getrennte Listen liefen früher oder später auseinander, und ein Konsument
bekäme je nach Weg eine andere Zusage.
"""

import json
import os
from functools import lru_cache
from pathlib import Path

import structlog

logger = structlog.get_logger()

# Neben `app/` — im Repository wie im Image, weil das Dockerfile `contract/`
# an dieselbe Stelle kopiert. `CONTRACT_PATH` überschreibt den Weg für Fälle,
# in denen die App woanders liegt als ihr Artefakt.
CONTRACT_FILE = Path(
    os.environ.get(
        "CONTRACT_PATH",
        Path(__file__).resolve().parent.parent / "contract" / "core-contract.json",
    )
)


class ContractUnavailableError(Exception):
    """Das Vertragsartefakt fehlt oder ist unlesbar."""


@lru_cache(maxsize=1)
def core_contract() -> dict:
    """Liest das Vertragsartefakt — einmal, danach aus dem Cache.

    Returns:
        Das Artefakt als Dict.

    Raises:
        ContractUnavailableError: Datei fehlt oder ist kein gültiges JSON. Der
            Fehler wird nicht verschluckt: Eine App, die ihren eigenen Vertrag
            nicht kennt, soll das sagen und nicht eine leere Feldliste
            ausliefern, die wie eine Zusage aussieht.
    """
    try:
        return json.loads(CONTRACT_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("contract_unreadable", path=str(CONTRACT_FILE), error=str(exc))
        raise ContractUnavailableError(str(CONTRACT_FILE)) from exc


def core_version() -> str:
    """Die Vertragsversion, an der ein Konsument einen Prüfbedarf erkennt."""
    return core_contract()["core_version"]


def required_fields(model: str) -> tuple[str, ...]:
    """Die Pflichtfelder eines Antworttyps.

    Args:
        model: Name des Core-Modells, z.B. ``'quote'``.

    Returns:
        Die Namen der Pflichtfelder in der Reihenfolge des Artefakts.
    """
    return tuple(
        field["name"] for field in core_contract()["core"][model] if field["required"]
    )


# ─── Der Plugin-Vertrag, aus den Typen abgeleitet (T-38) ──────────────────────

_PLUGIN_FIELD_MEANINGS: dict[tuple[str, str], str] = {
    ("resolved", "identity"): (
        "The identity in its applicable form: 'listed' (ticker + mic), 'pair' "
        "(base + quote_currency) or 'isin_only' (isin). The 'kind' field "
        "identifies the form."
    ),
    ("resolved", "name"): (
        "Display name of the instrument. Required: resolving an instrument "
        "without a name produces a row the user cannot recognize."
    ),
    ("resolved", "instrument_type"): (
        "Instrument type from the open catalog: stock, etf, etc, fund, crypto, "
        "bond. Required: it determines which metadata sources are queried. "
        "Without it, the fallback chain silently does not run."
    ),
    ("quote", "price"): "The price. Positive and finite; zero is not a valid price.",
    ("quote", "currency"): (
        "ISO 4217 code. Prices quoted in subunits (pence in London) "
        "must be converted first."
    ),
    ("quote", "as_of"): "Time when this price applied, with a time zone.",
    ("quote", "volume"): "Daily volume, if known to the provider.",
    ("daily_bar", "day"): "Trading day of the closing price.",
    ("daily_bar", "close"): "Closing price for this day. Positive and finite.",
    ("daily_series", "bars"): (
        "Daily bars in ascending date order, without duplicates."
    ),
    ("daily_series", "currency"): (
        "ISO 4217 code for the entire series. The currency must be "
        "the same throughout the series."
    ),
    ("daily_series", "adjusted"): (
        "Whether prices are adjusted for splits and distributions. Required: "
        "adjusted and unadjusted series are not comparable, and the values "
        "alone do not reveal which kind of series they belong to."
    ),
    ("fx_rate", "base"): "Base currency as an ISO 4217 code.",
    ("fx_rate", "quote"): "Quote currency as an ISO 4217 code.",
    ("fx_rate", "rate"): "Amount of quote currency per unit of base currency.",
    ("fx_rate", "as_of"): "Time when this rate applied, with a time zone.",
    ("reading", "field"): "Metric name as declared by the source.",
    ("reading", "value"): (
        "The value: a number, string or boolean, as appropriate for the metric."
    ),
    ("reading", "unit"): (
        "Unit of the value. Without it, an expense ratio of 0.19 cannot "
        "be distinguished from one of 0.0019."
    ),
    ("reading", "source"): "Source of the value.",
    ("reading", "currency"): "Currency, if the value is a monetary amount.",
}
"""Die Bedeutung je Feld — der einzige Teil, den kein Typ hergibt.

Alles andere (Name, Art, Pflicht) wird aus der Dataclass **gelesen**. Eine
zweite, von Hand gepflegte Liste wäre genau die Kopie, die in diesem Projekt
schon einmal auseinandergelaufen ist: Der Vertrag stünde dann im Typ und in
der Auskunft, und die Auskunft veraltete zuerst.
"""


def _field_kind(annotation: object) -> str:
    """Die Art eines Feldes, wie `FieldSpec` sie benennt.

    Die Reihenfolge der Prüfungen ist die Aussage: Ein zusammengesetzter Typ
    wird als solcher erkannt, bevor der Name eines seiner Bestandteile
    zuschlägt. ``tuple[DailyBar, ...]`` enthält den Text ``bar`` und wäre sonst
    keine Liste, und ``bool`` enthält kein ``int``, wird aber gern dafür
    gehalten.

    Ein Wert mit mehreren möglichen Skalartypen — `Reading.value` trägt Zahl,
    Text oder Wahrheitswert — heißt ``object``: Es ist die einzige Angabe, die
    stimmt, und eine willkürlich gewählte davon wäre eine Zusage, auf die sich
    jemand verlässt.
    """
    text = str(annotation)
    if text.startswith(("tuple", "list")):
        return "array"
    scalars = {
        "boolean": "bool" in text,
        "string": "str" in text or "date" in text or "Unit" in text,
        "number": "float" in text,
        "integer": "int" in text and "bool" not in text,
    }
    named = [kind for kind, present in scalars.items() if present]
    if len(named) == 1:
        return named[0]
    if not named:
        return "object"
    # Mehrere Skalartypen in einem Feld: `int` neben `float` ist dabei kein
    # echter Widerspruch — eine Zahl bleibt eine Zahl.
    if set(named) == {"number", "integer"}:
        return "number"
    return "object"


def plugin_contract() -> dict[str, list[dict]]:
    """Die Pflicht- und Optionalfelder des **Plugin**-Vertrags (T-38, `#6`).

    **Abgeleitet, nicht gepflegt.** `required` kommt daher, ob die Dataclass
    einen Vorgabewert führt — dieselbe Tatsache, die den Vertrag ausmacht.
    Eine gepflegte Liste könnte behaupten, `name` sei Pflicht, während der Typ
    ihn optional lässt; genau dieser Widerspruch stand vor T-38 im Produkt, nur
    andersherum: Die Auskunft sagte `required: false` über ein Feld, das Mike
    längst als Pflicht entschieden hatte.

    Warum das hier steht und nicht im JSON-Artefakt: Das Artefakt beschreibt
    den **REST**-Vertrag gegenüber einem Konsumenten. Der Plugin-Vertrag
    richtet sich an einen Autor und lebt in `stockinfo_plugin.types`. Zwei
    Verträge, zwei Quellen — aber jeder nur eine.

    Returns:
        Je Antworttyp die Felder mit Art, Pflicht und Bedeutung.
    """
    from dataclasses import MISSING, fields as dataclass_fields

    from stockinfo_plugin.types import (
        DailyBar,
        DailySeries,
        FxRate,
        Quote,
        Reading,
        Resolved,
    )

    described: dict[str, list[dict]] = {}
    for label, dataclass_type in (
        ("resolved", Resolved),
        ("quote", Quote),
        ("daily_bar", DailyBar),
        ("daily_series", DailySeries),
        ("fx_rate", FxRate),
        ("reading", Reading),
    ):
        described[label] = [
            {
                "name": field.name,
                "kind": _field_kind(field.type),
                "required": (
                    field.default is MISSING and field.default_factory is MISSING
                ),
                "meaning": _PLUGIN_FIELD_MEANINGS.get((label, field.name), "—"),
            }
            for field in dataclass_fields(dataclass_type)
        ]
    return described

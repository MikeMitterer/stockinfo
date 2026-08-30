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
        field["name"]
        for field in core_contract()["core"][model]
        if field["required"]
    )


# ─── Der Plugin-Vertrag, aus den Typen abgeleitet (T-38) ──────────────────────

_PLUGIN_FIELD_MEANINGS: dict[tuple[str, str], str] = {
    ("resolved", "identity"): (
        "Die Identität in ihrer Form — 'listed' (ticker + mic), 'pair' "
        "(base + quote_currency) oder 'isin_only' (isin). Welche Form gilt, "
        "sagt das Feld 'kind'."
    ),
    ("resolved", "name"): (
        "Anzeigename des Papiers. Pflicht: Eine Auflösung ohne Namen erzeugt "
        "eine Zeile, die der Benutzer nicht wiedererkennt."
    ),
    ("resolved", "instrument_type"): (
        "Gattung aus dem offenen Katalog — stock, etf, etc, fund, crypto, "
        "bond. Pflicht: An ihr hängt, welche Metadatenquellen überhaupt "
        "gefragt werden. Fehlt sie, läuft die Kaskade stillschweigend nicht."
    ),
    ("quote", "price"): "Der Kurs. Positiv und endlich; 0 ist keine Angabe.",
    ("quote", "currency"): (
        "ISO-4217-Code. Wer in Untereinheiten notiert (London in Pence), "
        "rechnet vorher um."
    ),
    ("quote", "as_of"): "Wann dieser Kurs galt, mit Zeitzone.",
    ("quote", "volume"): "Tagesvolumen, falls der Anbieter es kennt.",
    ("daily_bar", "day"): "Handelstag des Schlusskurses.",
    ("daily_bar", "close"): "Schlusskurs dieses Tages. Positiv und endlich.",
    ("daily_series", "bars"): (
        "Die Tagesbalken, aufsteigend nach Datum und ohne Duplikate."
    ),
    ("daily_series", "currency"): (
        "ISO-4217-Code der ganzen Reihe. Eine Reihe mit wechselnder Währung "
        "ist keine Reihe."
    ),
    ("daily_series", "adjusted"): (
        "Ob die Kurse um Splits und Ausschüttungen bereinigt sind. Pflicht, "
        "weil sich bereinigte und unbereinigte Reihen nicht vergleichen "
        "lassen und man es ihnen nicht ansieht."
    ),
    ("fx_rate", "base"): "Ausgangswährung als ISO-4217-Code.",
    ("fx_rate", "quote"): "Zielwährung als ISO-4217-Code.",
    ("fx_rate", "rate"): "Wieviel Zielwährung eine Einheit Ausgangswährung kostet.",
    ("fx_rate", "as_of"): "Wann dieser Kurs galt, mit Zeitzone.",
    ("reading", "field"): "Name der Kennzahl, wie die Quelle sie deklariert.",
    ("reading", "value"): (
        "Der Wert. Zahl, Text oder Wahrheitswert — was die Kennzahl hergibt."
    ),
    ("reading", "unit"): (
        "Die Einheit, in der der Wert steht. Ohne sie ist eine Kostenquote "
        "von 0.19 nicht von einer von 0.0019 zu unterscheiden."
    ),
    ("reading", "source"): "Woher der Wert stammt.",
    ("reading", "currency"): "Währung, falls der Wert ein Betrag ist.",
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
                "meaning": _PLUGIN_FIELD_MEANINGS.get(
                    (label, field.name), "—"
                ),
            }
            for field in dataclass_fields(dataclass_type)
        ]
    return described

"""Schlägt an, wenn sich der Core unbemerkt ändert (T-24 `#7`, `#7c`).

Der Schnappschuss unter `contract/openapi-core-snapshot.json` hält fest, wie
die Core-Endpunkte und ihre Modelle heute aussehen. Weicht die App davon ab,
gibt es genau zwei richtige Antworten: die Änderung zurücknehmen, oder sie
wollen — dann steigt `core_version`, und der Schnappschuss wird erneuert.

Der Unterschied zu `tests/test_contract.py`: Dort wird das Artefakt gegen die
Fixtures geprüft, ohne die App. Hier wird die App gegen ihren eigenen
Vergangenheitsstand geprüft. Beides zusammen deckt die Frage „hat sich etwas
geändert, ohne dass es jemand gesagt hat?" ab.

Erneuern:

    UPDATE_CORE_SNAPSHOT=1 .venv/bin/pytest tests/test_contract_openapi.py -q
"""

import json
import os
from pathlib import Path

import pytest

from app.contract import core_contract, required_fields
from app.main import app

SNAPSHOT_FILE = Path(__file__).resolve().parent.parent / "contract" / "openapi-core-snapshot.json"

_REFRESH_HINT = (
    "Ist die Änderung gewollt? Dann `core_version` im Artefakt erhöhen "
    "(Major bei entferntem oder unverträglich geändertem Pflichtfeld, Minor "
    "bei additiver Erweiterung) und danach\n"
    "    UPDATE_CORE_SNAPSHOT=1 .venv/bin/pytest tests/test_contract_openapi.py -q"
)


def _schema_names(node: object, found: set[str]) -> set[str]:
    """Sammelt alle `#/components/schemas/…`-Verweise unterhalb eines Knotens."""
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
            found.add(ref.rsplit("/", 1)[-1])
        for value in node.values():
            _schema_names(value, found)
    elif isinstance(node, list):
        for entry in node:
            _schema_names(entry, found)
    return found


def _promised_paths() -> set[str]:
    """Alle Pfade, für die der Vertrag eine Form zusagt.

    Die Core-Endpunkte **und** die, die den Vertrag selbst ausliefern: Ein
    Konsument hängt auch an der Form von `/fields`. Nicht dabei sind die
    Diagnose- und Schreibendpunkte — ein Schnappschuss über alles wäre
    ständig grundlos rot.
    """
    contract = core_contract()
    paths = {
        spec["path"]
        for specs in contract["endpoints"].values()
        for spec in specs
    }
    return paths | {spec["path"] for spec in contract["contract_endpoints"]}


def _core_excerpt() -> dict:
    """Der Teil der OpenAPI, den der Vertrag zusagt — Pfade und ihre Modelle.

    Bewusst ein Ausschnitt: Ein Schnappschuss über das ganze Dokument schlüge
    bei jeder Änderung an einem Diagnoseendpunkt an, und niemand liest einen
    Test, der ständig grundlos rot ist.
    """
    document = app.openapi()
    promised = _promised_paths()

    paths: dict[str, dict] = {}
    schemas: set[str] = set()
    for path, operations in document["paths"].items():
        if path not in promised:
            continue
        paths[path] = {}
        for method, operation in operations.items():
            paths[path][method] = {
                "parameters": sorted(
                    parameter["name"] for parameter in operation.get("parameters", [])
                ),
                "responses": {
                    code: response.get("content", {})
                    for code, response in operation.get("responses", {}).items()
                },
            }
            _schema_names(operation, schemas)

    available = document["components"]["schemas"]
    return {
        "core_version": core_contract()["core_version"],
        "paths": paths,
        "schemas": {
            name: available[name] for name in sorted(_closure(schemas, available))
        },
    }


def _closure(names: set[str], available: dict) -> set[str]:
    """Erweitert eine Schemamenge um alles, worauf sie verweist.

    Ein Modell schützt nichts, wenn seine Bestandteile fehlen: `FieldsResponse`
    verweist auf `FieldSpec` und `EndpointSpec`, und ohne die beiden konnte
    `FieldSpec.meaning` von `string` auf `integer` wandern, ohne dass der
    Schnappschuss anschlägt.

    Args:
        names: Die direkt in den Operationen genannten Schemas.
        available: Alle Schemas des OpenAPI-Dokuments.

    Returns:
        Die transitive Hülle — jedes erreichbare Schema genau einmal.
    """
    found = set(names)
    pending = list(found)
    while pending:
        name = pending.pop()
        for referenced in _schema_names(available.get(name, {}), set()):
            if referenced not in found:
                found.add(referenced)
                pending.append(referenced)
    return found


def test_der_schnappschuss_folgt_verweisen_bis_zum_ende() -> None:
    """Ein Modell schützt nichts, wenn seine Bestandteile fehlen.

    `FieldsResponse` verweist auf `FieldSpec` und `EndpointSpec`. Wurden nur
    die direkt in den Operationen genannten Schemas aufgenommen, konnte
    `FieldSpec.meaning` von `string` auf `integer` wandern, ohne dass der
    Wächter anschlägt — die veröffentlichte Form von `/fields` war damit nur
    eine Ebene tief geschützt (Codex, T-24 Runde 3).
    """
    schemas = _core_excerpt()["schemas"]

    assert "FieldsResponse" in schemas
    assert "FieldSpec" in schemas, "verwiesenes Modell fehlt im Schnappschuss"
    assert "EndpointSpec" in schemas, "verwiesenes Modell fehlt im Schnappschuss"


def test_alle_vertragspfade_existieren_in_der_app() -> None:
    """Ein Vertrag über einen Pfad, den es nicht gibt, ist keiner."""
    published = set(app.openapi()["paths"])
    promised = _promised_paths()

    assert promised <= published, f"fehlende Pfade: {sorted(promised - published)}"


def test_der_core_entspricht_dem_schnappschuss() -> None:
    """Der eigentliche Wächter: unbemerkte Änderungen am Core gibt es nicht."""
    current =_core_excerpt()

    if os.environ.get("UPDATE_CORE_SNAPSHOT"):
        SNAPSHOT_FILE.write_text(
            json.dumps(current, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        pytest.skip(f"Schnappschuss erneuert: {SNAPSHOT_FILE.name}")

    assert SNAPSHOT_FILE.is_file(), (
        f"{SNAPSHOT_FILE} fehlt. Einmalig anlegen mit\n"
        "    UPDATE_CORE_SNAPSHOT=1 .venv/bin/pytest tests/test_contract_openapi.py -q"
    )
    stored = json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))

    assert current["core_version"] == stored["core_version"], (
        "Die Vertragsversion hat sich geändert, ohne dass der Schnappschuss "
        f"erneuert wurde.\n{_REFRESH_HINT}"
    )
    assert current["paths"] == stored["paths"], (
        f"Die Core-Pfade haben sich geändert.\n{_REFRESH_HINT}"
    )
    assert current["schemas"] == stored["schemas"], (
        f"Ein Core-Modell hat sich geändert.\n{_REFRESH_HINT}"
    )


# Welches Antwortmodell trägt welchen Vertragstyp. Ausgeschrieben und nicht
# geraten: Der Name im Artefakt ist eine Vertragsvokabel, der Klassenname eine
# Implementierungssache, und sie müssen nicht gleich heißen.
_CONTRACT_MODELS = {
    "quote": "QuoteResponse",
    "instrument": "InstrumentSummary",
}


def _is_nullable(schema: dict) -> bool:
    """Lässt dieses Feldschema ``null`` zu?

    Pydantic schreibt ein optionales Feld als `anyOf` mit einem
    `{"type": "null"}`-Zweig. Genau der ist die Zusage, um die es geht: Ein
    generierter Client darf `null` erwarten und dafür einen Zweig bauen.
    """
    return any(branch.get("type") == "null" for branch in schema.get("anyOf", ()))


@pytest.mark.parametrize("model", sorted(_CONTRACT_MODELS))
def test_jedes_pflichtfeld_des_artefakts_ist_im_schema_auch_zugesagt(model: str) -> None:
    """**Der Befund aus Runde 39** — zwei Zusagen, die sich widersprachen.

    Das Artefakt erklärte `quote.ticker` und `quote.mic` zu Pflichtfeldern,
    während das veröffentlichte OpenAPI-Schema beide als optional **und**
    nullable führte. Ein generierter Client durfte damit genau den Zustand
    annehmen, den `core_version 2.0.0` abschafft — und ein bloß neu erzeugter
    Schnappschuss hätte beide Seiten in ihrem eigenen Widerspruch bestätigt.
    Dasselbe galt seit T-24 unbemerkt für `currency`.

    Geprüft wird deshalb quer über die beiden Quellen: Das Feld **existiert**
    im Schema, und es ist **nicht nullable**. Das ist die Zusage, die zählt —
    sie sagt dem Konsumenten, dass er keinen `null`-Zweig braucht.

    **Die `required`-Liste wird bewusst nicht geprüft**, und das ist keine
    Bequemlichkeit: Bei einem *Antwort*modell sagt sie nichts aus. Pydantic
    bindet sie an die Eingabe, und ein Feld mit Vorgabewert — `cached`,
    `history_count`, das per `default_factory` gefüllte `manual_fields` — steht
    nicht darin, wird aber in jeder Antwort serialisiert. Eine Prüfung
    darüber sähe strenger aus, als sie ist, und würde bei jedem Feld mit
    Vorgabewert falsch anschlagen.
    """
    schema = app.openapi()["components"]["schemas"][_CONTRACT_MODELS[model]]
    properties = schema["properties"]

    for field in required_fields(model):
        assert field in properties, f"{model}.{field} fehlt im Schema ganz"
        assert not _is_nullable(properties[field]), (
            f"{model}.{field} ist laut Artefakt Pflicht, im Schema aber nullable"
        )

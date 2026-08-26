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

import ast
import json
import os
from dataclasses import MISSING, fields
from pathlib import Path

import pytest

from app.contract import core_contract, required_fields
from app.main import app
from app.services.quote_service import (
    PRECHECKED_CORE_FIELDS,
    PrecheckedCoreValues,
    QuoteUnavailableError,
    require_core_values,
)

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
    "daily": "DailyPoint",
    "history": "QuotePoint",
    "fx": "FxRate",
}


def _is_nullable(schema: dict) -> bool:
    """Lässt dieses Feldschema ``null`` zu?

    Pydantic schreibt ein optionales Feld als `anyOf` mit einem
    `{"type": "null"}`-Zweig. Genau der ist die Zusage, um die es geht: Ein
    generierter Client darf `null` erwarten und dafür einen Zweig bauen.
    """
    return any(branch.get("type") == "null" for branch in schema.get("anyOf", ()))


def test_die_vorabpruefung_deckt_nur_pflichtfelder_ab() -> None:
    """Die Vorabprüfung darf nichts verlangen, was der Vertrag nicht zusagt.

    `PRECHECKED_CORE_FIELDS` ist die eine Liste der Werte, die erst beim Bauen
    zusammenkommen und deshalb vorher geprüft werden. Stünde dort ein Feld,
    das das Artefakt gar nicht verlangt, wiese der Core Antworten ab, die
    vertragsgemäß in Ordnung sind — eine Verschärfung, die niemand zugesagt
    hat und die kein anderer Test bemerkt.

    Umgekehrt gilt der Satz **nicht**: Nicht jedes Pflichtfeld muss hier
    stehen. `price` oder `quote_time` erzwingt schon der Typ beim Bauen.
    """
    assert set(PRECHECKED_CORE_FIELDS) <= set(required_fields("quote")), (
        "die Vorabprüfung verlangt ein Feld, das der Vertrag nicht zusagt"
    )


def test_jeder_geprüfte_name_hat_auch_einen_wert() -> None:
    """**Befund 2 aus Runde 43** — der Wächter prüfte nur die halbe Zusage.

    Bis dahin standen die Feldnamen in einer Tupelkonstante und die Werte
    positional daneben. Der Test verglich allein die Namen mit dem Artefakt;
    Codex' Gegenprobe ergänzte das zulässige Pflichtfeld `price` an der
    behaupteten „einen Stelle" und bekam beides: einen **grünen** Wächter und
    eine Prüfung, die an `zip(..., strict=True)` abstürzte.

    Geprüft wird deshalb die Bindung selbst, und zwar über die abgeleitete
    Namensliste statt über eine zweite Aufzählung: Für **jedes** Feld wird
    genau dieses leer gesetzt und alle anderen gefüllt. Die Prüfung muss
    anschlagen und den leeren Namen nennen. Ein Name ohne Wert lässt die
    Konstruktion scheitern, ein Wert ohne Prüfung bleibt unbemerkt — beides
    ist hier rot.

    Ein neu aufgenommenes Feld wandert automatisch in diesen Test. Genau das
    war die Zusage, die vorher keine war.
    """
    for missing_field in PRECHECKED_CORE_FIELDS:
        values = PrecheckedCoreValues(
            **{
                name: "" if name == missing_field else "gesetzt"
                for name in PRECHECKED_CORE_FIELDS
            }
        )

        assert values.missing() == [missing_field], (
            f"{missing_field} ist leer, wird aber nicht als fehlend gemeldet"
        )

        with pytest.raises(QuoteUnavailableError) as rejected:
            require_core_values("AAPL", values)
        assert missing_field in str(rejected.value), (
            "die Meldung muss sagen, welches Feld fehlt"
        )


def test_jede_bindungsstelle_liefert_alle_werte() -> None:
    """Der Kern des Befunds: Namen **und** Bindung müssen zusammen wachsen.

    Codex' Gegenprobe ergänzte das zulässige Pflichtfeld `price` an der
    behaupteten Source of Truth. Vorher blieb der Wächter grün, weil er nur
    Namen mit dem Artefakt verglich — die Bindung sah er nie an.

    Er sieht sie jetzt, und zwar über ein **Inventar statt einer Textsuche**:
    Jede Konstruktion von `PrecheckedCoreValues` in `app/` wird aus dem
    Syntaxbaum geholt und muss jedes Feld benennen. Ein Feld mehr in der
    Struktur macht damit genau hier rot, an der Stelle, die den einen Ort
    behauptet — und nicht erst irgendwo tief in einem Kursabruf.

    Positionale Bindung ist ausgeschlossen: Sie war die ursprüngliche Ursache.
    Ein Tupel in der falschen Reihenfolge ist ein Fehler, den keine Prüfung
    mehr sieht, weil beide Seiten dann ja „vollständig" sind.
    """
    app_dir = Path(__file__).resolve().parent.parent / "app"
    bindings = []
    for source in sorted(app_dir.rglob("*.py")):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == PrecheckedCoreValues.__name__
            ):
                bindings.append((source.name, node))

    assert len(bindings) >= 2, (
        "erwartet werden mindestens der frische Weg und der Cache-Weg; "
        f"gefunden: {[name for name, _ in bindings]}"
    )
    for name, call in bindings:
        assert not call.args, (
            f"{name} bindet positional — dann sagt die Reihenfolge, was der "
            "Name sagen soll"
        )
        assert {keyword.arg for keyword in call.keywords} == set(
            PRECHECKED_CORE_FIELDS
        ), f"{name} liefert nicht jeden geprüften Wert"


def test_kein_pflichtwert_darf_einen_vorgabewert_haben() -> None:
    """Der zweite Teil der Synchronität — die Seite der **Aufrufer**.

    Die Schleife darüber prüft, dass jeder Name geprüft wird. Sie sagt nichts
    darüber, ob die beiden Wege den Wert auch liefern. Genau da lag der alte
    Fehler: Ein vierter Name kam ohne vierten Wert durch.

    Ein Feld ohne Vorgabewert kann das nicht. Wächst die Struktur, bricht die
    Konstruktion in `QuoteService._build` und `CachedQuoteService._from_cache`
    laut und sofort — ein Vorgabewert wäre wieder das Schlupfloch, durch das
    ein ungeprüfter Wert lautlos schlüpft.
    """
    for entry in fields(PrecheckedCoreValues):
        assert entry.default is MISSING, (
            f"{entry.name} hat einen Vorgabewert — ein Aufrufer darf ihn dann "
            "weglassen, ohne dass es jemand merkt"
        )
        assert entry.default_factory is MISSING, (
            f"{entry.name} hat eine Vorgabefabrik — dieselbe Lücke"
        )


def test_die_vorabpruefung_laesst_vollstaendige_werte_durch() -> None:
    """Das Gegenstück — sonst bestünde auch ein „wirft immer" den Test oben.

    Ohne diesen Fall wäre das Orakel selbstbestätigend: Eine Prüfung, die
    jeden Aufruf ablehnt, erfüllte jede einzelne Erwartung der Schleife.
    """
    values = PrecheckedCoreValues(
        **{name: "gesetzt" for name in PRECHECKED_CORE_FIELDS}
    )

    assert values.missing() == []
    require_core_values("AAPL", values)


@pytest.mark.parametrize("model", sorted(_CONTRACT_MODELS))
def test_jedes_pflichtfeld_des_artefakts_ist_im_schema_auch_zugesagt(model: str) -> None:
    """**Der Befund aus Runde 39** — zwei Zusagen, die sich widersprachen.

    Das Artefakt erklärte `quote.ticker` und `quote.mic` zu Pflichtfeldern,
    während das veröffentlichte OpenAPI-Schema beide als optional **und**
    nullable führte. Ein generierter Client durfte damit genau den Zustand
    annehmen, den `core_version 2.0.0` abschafft — und ein bloß neu erzeugter
    Schnappschuss hätte beide Seiten in ihrem eigenen Widerspruch bestätigt.
    Dasselbe galt seit T-24 unbemerkt für `currency`.

    Geprüft wird deshalb quer über die beiden Quellen, in **drei** Punkten:
    Das Feld existiert im Schema, es steht in dessen `required`-Liste, und es
    ist nicht nullable.

    **Die erste Fassung ließ `required` aus, mit einer falschen Begründung.**
    Sie behauptete, die Liste sage bei Antwortmodellen nichts aus, weil ein
    Feld mit Vorgabewert ohnehin serialisiert werde. Das verwechselt Erzeuger
    und Zusage: Die Liste ist die JSON-Schema-Aussage an einen **generierten
    Konsumenten**, ob eine Property fehlen darf. Steht sie nicht drin, muss er
    einen Zweig für ihr Fehlen bauen — unabhängig davon, was dieser Server
    gerade schreibt. Codex hat das in Runde 42 richtiggestellt.

    Der Vorgabewert bleibt; das Schema sagt die Anwesenheit trotzdem zu
    (`always_present` in `app/models.py`). Nullability wird dagegen **nie**
    über das Schema geglättet — dort ändert sich der Typ.

    Geprüft werden **alle fünf** Core-Modelle. Die erste Fassung nahm nur
    `quote` und `instrument`, obwohl ihr Name jedes Pflichtfeld behauptete —
    und `daily.currency` sowie `history.currency` waren genau deshalb bis
    Runde 42 nullable geblieben.
    """
    schema = app.openapi()["components"]["schemas"][_CONTRACT_MODELS[model]]
    properties = schema["properties"]
    required = set(schema.get("required", ()))

    for field in required_fields(model):
        assert field in properties, f"{model}.{field} fehlt im Schema ganz"
        assert field in required, (
            f"{model}.{field} ist laut Artefakt Pflicht, steht im Schema aber "
            "nicht in `required` — ein Konsument dürfte es für optional halten"
        )
        assert not _is_nullable(properties[field]), (
            f"{model}.{field} ist laut Artefakt Pflicht, im Schema aber nullable"
        )

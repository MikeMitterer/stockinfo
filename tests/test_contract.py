"""Statische Prüfung des REST-Core-Vertrags — **ohne laufende App**.

Geprüft wird, ob das Vertragsartefakt (`contract/core-contract.json`) und die
HTTP-Fixtures daneben zusammenpassen: dieselben Endpunkte samt Methode und
zulässigen Query-Namen, derselbe Headername, und jede Fixture erfüllt das
Schema, das der Vertrag für ihren Antworttyp festschreibt.

Bewusst ohne Import der FastAPI-App (T-24 `#7i`): Der Vertrag muss prüfbar
sein, bevor die Routen existieren, die T-25 baut. Dass die **laufende** App
diesem Artefakt entspricht, nimmt T-25 `#7j` ab.

**Negativ heißt hier nachweislich negativ.** Eine Fixture, die sich als
vertragswidrig ausgibt, muss die benannte Verletzung auch tragen — sonst
veröffentlicht dieses Repo einen Fehlerfall, der keiner ist, und ein Konsument
prüft gegen ein Beispiel, das ihm nichts beibringt.
"""

import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

CONTRACT_DIR = Path(__file__).resolve().parent.parent / "contract"
CONTRACT_FILE = CONTRACT_DIR / "core-contract.json"
FIXTURE_DIR = CONTRACT_DIR / "fixtures"

_KIND_TO_TYPES: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "number": (int, float),
    "integer": (int,),
    "boolean": (bool,),
    "array": (list,),
    "object": (dict,),
}


def _generation_header(fixture: dict, contract: dict) -> str | None:
    """Der Generationsheader dieser Antwort, oder ``None``."""
    return fixture["response"]["headers"].get(contract["generation"]["header"])


def _header_missing(fixture: dict, contract: dict) -> bool:
    """Trägt die Antwort den Generationsheader **nicht**?"""
    return _generation_header(fixture, contract) is None


def _header_contradicts_body(fixture: dict, contract: dict) -> bool:
    """Nennen Header und Rumpf **verschiedene** Generationen?"""
    body = fixture["response"]["body"]
    if not isinstance(body, dict) or "generation_id" not in body:
        return False
    return _generation_header(fixture, contract) != body["generation_id"]


# Jede Regel, auf die sich eine Fixture berufen darf, samt der Prüfung, die
# ihre Verletzung tatsächlich nachweist.
#
# Ohne diese Zuordnung war `violates` nur ein Textfeld: Der Test fragte, ob
# *irgendetwas* dasteht, nicht ob es zutrifft. Eine Fixture konnte damit
# aufhören, negativ zu sein — Header ergänzt, Widerspruch beseitigt —, und
# blieb grün (Codex, T-24 Runde 1).
_VIOLATION_CHECKS = {
    "generation.required_on_every_response": _header_missing,
    "generation.rule": _header_contradicts_body,
}

# Die Negativfälle, die T-24 `#7h` ausdrücklich verlangt. Verschwindet einer,
# schlägt der Test an — sonst könnte man die Prüfung durch Löschen bestehen.
_REQUIRED_VIOLATIONS = {
    "generation.required_on_every_response",
    "generation.rule",
}


@pytest.fixture(scope="module")
def contract() -> dict:
    """Das Vertragsartefakt als Dict."""
    return json.loads(CONTRACT_FILE.read_text(encoding="utf-8"))


def _fixture_files() -> list[Path]:
    """Alle Fixture-Dateien, alphabetisch — leer, solange keine existieren."""
    return sorted(FIXTURE_DIR.glob("*.json")) if FIXTURE_DIR.is_dir() else []


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _endpoint_specs(contract: dict) -> dict[str, dict]:
    """Alle Endpunkte des Vertrags als ``pfad → spec``, inklusive /generation."""
    specs = {
        spec["path"]: {**spec, "model": model}
        for model, specifications in contract["endpoints"].items()
        for spec in specifications
    }
    generation = contract["generation"]
    specs[generation["endpoint"]] = {
        "path": generation["endpoint"],
        "method": "GET",
        "query": [],
        "model": None,
    }
    return specs


def _matches_template(route: str, template: str) -> bool:
    """Deckt sich ein konkreter Pfad mit einer Endpunktvorlage?

    ``/quote/IE00B4L5Y983/daily`` passt auf ``/quote/{isin}/daily``; die
    geschweiften Segmente nehmen jeden Wert an, die übrigen müssen wörtlich
    stimmen. Ohne den Segmentvergleich ginge `/quote/by-symbol/{symbol}/daily`
    als `/quote/{isin}/daily` durch.
    """
    parts, template_parts = route.strip("/").split("/"), template.strip("/").split("/")
    if len(parts) != len(template_parts):
        return False
    return all(
        template_part.startswith("{") or template_part == part
        for part, template_part in zip(parts, template_parts)
    )


def test_vertragsartefakt_existiert_und_nennt_seine_version(contract: dict) -> None:
    """Ohne Versionsnummer kann ein Konsument nicht erkennen, dass er prüfen muss."""
    assert contract["core_version"].count(".") == 2  # Major.Minor.Patch
    assert isinstance(contract["details_version"], int)


def test_jeder_antworttyp_hat_felder_mit_art_und_pflicht(contract: dict) -> None:
    """Eine Feldliste ohne Nullability ist ungenauer als das OpenAPI-Dokument."""
    assert set(contract["core"]) >= {"quote", "instrument", "daily", "fx"}
    for model, fields in contract["core"].items():
        assert fields, f"{model} hat keine Felder"
        for field in fields:
            assert field["kind"] in _KIND_TO_TYPES, f"{model}.{field['name']}"
            assert isinstance(field["required"], bool)
            assert field["meaning"].strip(), f"{model}.{field['name']} ohne Bedeutung"


def test_jeder_endpunkt_nennt_methode_und_zulaessige_query_namen(
    contract: dict,
) -> None:
    """Ein Endpunkt ohne Query-Liste lässt jedes erfundene Beispiel durchgehen."""
    for model, specifications in contract["endpoints"].items():
        assert specifications, f"{model} hat keine Endpunkte"
        for spec in specifications:
            assert spec["path"].startswith("/")
            assert spec["method"] in {"GET", "POST", "PUT", "DELETE"}
            assert isinstance(spec["query"], list)


def test_es_gibt_fixtures() -> None:
    """Ein Vertrag ohne Beispiele ist für den Konsumenten nicht nachvollziehbar."""
    assert _fixture_files(), f"keine Fixtures unter {FIXTURE_DIR}"


@pytest.mark.parametrize("path", _fixture_files(), ids=lambda p: p.name)
def test_fixture_nennt_endpunkt_und_erwartung(path: Path, contract: dict) -> None:
    """Jede Fixture sagt, welchen Endpunkt sie zeigt und ob sie vertragstreu ist."""
    fixture = _load(path)
    specs = _endpoint_specs(contract)

    assert fixture["endpoint"] in specs, (
        f"{path.name} zeigt auf '{fixture['endpoint']}', "
        f"der Vertrag kennt nur {sorted(specs)}"
    )
    assert isinstance(fixture["contract_compliant"], bool)
    assert fixture["note"].strip(), f"{path.name} erklärt nicht, was sie zeigt"

    # Eine Fehlerantwort trägt einen Fehlerrumpf, kein Core-Modell — deshalb
    # hängt die Erwartung am Status. Ohne diese Unterscheidung wäre entweder
    # `quote-404.json` falsch beanstandet oder ein `200` ohne Modell erlaubt,
    # und dann liefe die Schemaprüfung darunter ins Leere.
    expected = specs[fixture["endpoint"]]["model"]
    if fixture["response"]["status"] >= 400:
        assert fixture["model"] is None, (
            f"{path.name}: Fehlerantworten tragen kein Core-Modell"
        )
    else:
        assert fixture["model"] == expected, (
            f"{path.name}: model '{fixture['model']}' passt nicht zu "
            f"{fixture['endpoint']} (erwartet {expected})"
        )


@pytest.mark.parametrize("path", _fixture_files(), ids=lambda p: p.name)
def test_fixture_ruft_ihren_endpunkt_so_auf_wie_er_existiert(
    path: Path, contract: dict
) -> None:
    """Pfad, Methode und Query-Namen müssen zum Endpunkt passen.

    Die Fixtures werden veröffentlicht und von Konsumenten gelesen. Ein
    Beispielaufruf mit einem Parameter, den es nicht gibt, sieht aus wie eine
    zugesagte Funktion — FastAPI ignoriert Unbekanntes still, und niemand
    merkt es. Genau so stand `?limit=3` an einem Endpunkt, der nur `period`
    kennt (Codex, T-24 Runde 1).
    """
    fixture = _load(path)
    spec = _endpoint_specs(contract)[fixture["endpoint"]]
    parsed = urlsplit(fixture["request"]["path"])

    assert fixture["request"]["method"] == spec["method"], (
        f"{path.name}: Methode {fixture['request']['method']} passt nicht zu "
        f"{spec['path']} ({spec['method']})"
    )
    assert _matches_template(parsed.path, spec["path"]), (
        f"{path.name}: '{parsed.path}' passt nicht auf '{spec['path']}'"
    )
    unknown = set(parse_qs(parsed.query)) - set(spec["query"])
    assert not unknown, (
        f"{path.name}: {sorted(unknown)} gibt es an {spec['path']} nicht — "
        f"zulässig sind {spec['query'] or 'keine'}"
    )


@pytest.mark.parametrize("path", _fixture_files(), ids=lambda p: p.name)
def test_vertragstreue_fixture_traegt_den_generationsheader(
    path: Path, contract: dict
) -> None:
    """Der Header ist Pflicht auf **jeder** Antwort — auch auf Fehlern."""
    fixture = _load(path)
    if not fixture["contract_compliant"]:
        pytest.skip("absichtlich vertragswidrig")

    assert not _header_missing(fixture, contract), (
        f"{path.name} ist als vertragstreu markiert, trägt aber keinen "
        f"{contract['generation']['header']}"
    )


@pytest.mark.parametrize("path", _fixture_files(), ids=lambda p: p.name)
def test_vertragswidrige_fixture_traegt_ihre_verletzung_wirklich(
    path: Path, contract: dict
) -> None:
    """Eine behauptete Verletzung muss nachweisbar vorliegen.

    Vorher genügte irgendein Text in `violates`. Damit hätte eine Fixture
    stillschweigend aufhören können, ein Negativfall zu sein — und
    StockPortfolio bekäme ein Beispiel, das den bezeichneten Vertragsfehler
    gar nicht enthält.
    """
    fixture = _load(path)
    if fixture["contract_compliant"]:
        assert fixture["violates"] is None, (
            f"{path.name} ist vertragstreu und darf keine Verletzung nennen"
        )
        pytest.skip("vertragstreu")

    rule = fixture["violates"]
    assert rule in _VIOLATION_CHECKS, (
        f"{path.name} beruft sich auf '{rule}' — bekannt sind nur "
        f"{sorted(_VIOLATION_CHECKS)}"
    )
    assert _VIOLATION_CHECKS[rule](fixture, contract), (
        f"{path.name} behauptet die Verletzung '{rule}', erfüllt den Vertrag "
        f"an dieser Stelle aber — die Fixture ist kein Negativfall mehr"
    )


def test_die_geforderten_negativfaelle_sind_vorhanden(contract: dict) -> None:
    """T-24 `#7h` nennt sie ausdrücklich — Löschen darf kein Weg zum Grün sein."""
    existing = {
        _load(path)["violates"]
        for path in _fixture_files()
        if not _load(path)["contract_compliant"]
    }
    assert _REQUIRED_VIOLATIONS <= existing, (
        f"fehlende Negativfälle: {sorted(_REQUIRED_VIOLATIONS - existing)}"
    )


def test_die_pruefung_erkennt_eine_luegende_negativfixture(contract: dict) -> None:
    """Die Gegenprobe zur Prüfung selbst — sonst prüft sie sich nie.

    Konstruiert wird genau der Fall, den Codex als `MUTANT_UNERKANNT` gemeldet
    hat: Eine Fixture behauptet `generation.rule`, trägt in Header und Rumpf
    aber dieselbe UUID. Der Prüfer muss das ablehnen.
    """
    same_uuid = "550e8400-e29b-41d4-a716-446655440000"
    liar = {
        "endpoint": "/generation",
        "model": None,
        "contract_compliant": False,
        "violates": "generation.rule",
        "note": "nur für diesen Test",
        "request": {"method": "GET", "path": "/generation"},
        "response": {
            "status": 200,
            "headers": {
                "Cache-Control": "no-store",
                contract["generation"]["header"]: same_uuid,
            },
            "body": {"generation_id": same_uuid},
        },
    }

    assert not _VIOLATION_CHECKS["generation.rule"](liar, contract)

    liar_without_conflict = dict(liar, violates="generation.required_on_every_response")
    assert not _VIOLATION_CHECKS["generation.required_on_every_response"](
        liar_without_conflict, contract
    )


@pytest.mark.parametrize("path", _fixture_files(), ids=lambda p: p.name)
def test_erfolgsfixture_erfuellt_das_schema_ihres_modells(
    path: Path, contract: dict
) -> None:
    """Pflichtfelder sind da und haben die zugesagte Art.

    Nur für vertragstreue Erfolgsantworten: Eine `404` trägt einen Fehlerrumpf,
    kein Kursmodell, und eine bewusst kaputte Fixture soll ja abweichen.
    """
    fixture = _load(path)
    if not fixture["contract_compliant"] or fixture["response"]["status"] >= 400:
        pytest.skip("kein Erfolgsfall")

    model = fixture["model"]
    if model is None:
        pytest.skip("Fixture ohne Core-Modell (z.B. /generation)")

    fields = contract["core"][model]
    body = fixture["response"]["body"]
    entries = body if isinstance(body, list) else [body]

    for entry in entries:
        for field in fields:
            name, kind = field["name"], field["kind"]
            if field["required"]:
                assert name in entry, f"{path.name}: '{name}' fehlt"
                assert entry[name] is not None, f"{path.name}: '{name}' ist null"
            if entry.get(name) is not None:
                assert isinstance(entry[name], _KIND_TO_TYPES[kind]), (
                    f"{path.name}: '{name}' ist {type(entry[name]).__name__}, "
                    f"erwartet {kind}"
                )


@pytest.mark.parametrize("path", _fixture_files(), ids=lambda p: p.name)
def test_generationsfixture_haelt_header_und_rumpf_zusammen(
    path: Path, contract: dict
) -> None:
    """„Header und Rumpf stammen aus derselben Generation" — die zentrale Regel.

    Ohne sie könnte ein Konsument eine Antwort aus Profil A für eine aus B
    halten.
    """
    fixture = _load(path)
    if fixture["endpoint"] != contract["generation"]["endpoint"]:
        pytest.skip("keine /generation-Fixture")
    if not fixture["contract_compliant"]:
        pytest.skip("Negativfall — geprüft in der Verletzungsprüfung")

    assert not _header_contradicts_body(fixture, contract), (
        f"{path.name}: Header und Rumpf widersprechen sich"
    )
    assert (
        fixture["response"]["headers"].get("Cache-Control")
        == contract["generation"]["cache_control"]
    )


def test_aufnahmevertrag_benennt_entscheidung_vor_dem_speichern(contract: dict) -> None:
    """Die optionale Prüfung liefert noch kein gespeichertes Instrument."""
    intake = next(spec for spec in contract["endpoints"]["instrument"] if spec["method"] == "POST")
    assert intake["request_optional"] == ["check_exchange", "confirmed_listing"]
    assert intake["responses"]["202"] == "IntakeConfirmation"

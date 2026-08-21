"""Statische Prüfung des REST-Core-Vertrags — **ohne laufende App**.

Geprüft wird, ob das Vertragsartefakt (`contract/core-contract.json`) und die
HTTP-Fixtures daneben zusammenpassen: dieselben Endpunktpfade, derselbe
Headername, und jede Fixture erfüllt das Schema, das der Vertrag für ihren
Antworttyp festschreibt.

Bewusst ohne Import der FastAPI-App (T-24 `#7i`): Der Vertrag muss prüfbar
sein, bevor die Routen existieren, die T-25 baut. Dass die **laufende** App
diesem Artefakt entspricht, nimmt T-25 `#7j` ab.
"""

import json
from pathlib import Path

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


@pytest.fixture(scope="module")
def contract() -> dict:
    """Das Vertragsartefakt als Dict."""
    return json.loads(CONTRACT_FILE.read_text(encoding="utf-8"))


def _fixture_files() -> list[Path]:
    """Alle Fixture-Dateien, alphabetisch — leer, solange keine existieren."""
    return sorted(FIXTURE_DIR.glob("*.json")) if FIXTURE_DIR.is_dir() else []


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_vertragsartefakt_existiert_und_nennt_seine_version(contract: dict) -> None:
    """Ohne Versionsnummer kann ein Konsument nicht erkennen, dass er prüfen muss."""
    assert contract["core_version"].count(".") == 2  # Major.Minor.Patch
    assert isinstance(contract["details_version"], int)


def test_jeder_antworttyp_hat_felder_mit_art_und_pflicht(contract: dict) -> None:
    """Eine Feldliste ohne Nullability ist ungenauer als das OpenAPI-Dokument."""
    assert set(contract["core"]) >= {"quote", "instrument", "daily", "fx"}
    for modell, felder in contract["core"].items():
        assert felder, f"{modell} hat keine Felder"
        for feld in felder:
            assert feld["kind"] in _KIND_TO_TYPES, f"{modell}.{feld['name']}"
            assert isinstance(feld["required"], bool)
            assert feld["meaning"].strip(), f"{modell}.{feld['name']} ohne Bedeutung"


def test_es_gibt_fixtures() -> None:
    """Ein Vertrag ohne Beispiele ist für den Konsumenten nicht nachvollziehbar."""
    assert _fixture_files(), f"keine Fixtures unter {FIXTURE_DIR}"


@pytest.mark.parametrize("path", _fixture_files(), ids=lambda p: p.name)
def test_fixture_nennt_endpunkt_und_erwartung(path: Path, contract: dict) -> None:
    """Jede Fixture sagt, welchen Endpunkt sie zeigt und ob sie vertragstreu ist."""
    fixture = _load(path)
    endpoints = {
        endpoint
        for modell in contract["endpoints"].values()
        for endpoint in modell
    } | {contract["generation"]["endpoint"]}

    assert fixture["endpoint"] in endpoints, (
        f"{path.name} zeigt auf '{fixture['endpoint']}', "
        f"der Vertrag kennt nur {sorted(endpoints)}"
    )
    assert isinstance(fixture["contract_compliant"], bool)
    assert fixture["note"].strip(), f"{path.name} erklärt nicht, was sie zeigt"


@pytest.mark.parametrize("path", _fixture_files(), ids=lambda p: p.name)
def test_fixture_traegt_den_generationsheader(path: Path, contract: dict) -> None:
    """Der Header ist Pflicht auf **jeder** Antwort — auch auf Fehlern.

    Genau dafür gibt es die als vertragswidrig markierten Fixtures: Ein
    Konsument muss auch prüfen können, dass er den Fehlerfall erkennt.
    """
    fixture = _load(path)
    header = contract["generation"]["header"]
    vorhanden = header in fixture["response"]["headers"]

    if fixture["contract_compliant"]:
        assert vorhanden, f"{path.name} ist als vertragstreu markiert, Header fehlt"
    else:
        # Nicht jede vertragswidrige Fixture zeigt den fehlenden Header —
        # aber sie muss sagen, welche Regel sie verletzt.
        assert fixture["violates"], f"{path.name} nennt die verletzte Regel nicht"


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

    modell = fixture["model"]
    if modell is None:
        pytest.skip("Fixture ohne Core-Modell (z.B. /generation)")

    felder = contract["core"][modell]
    rumpf = fixture["response"]["body"]
    eintraege = rumpf if isinstance(rumpf, list) else [rumpf]

    for eintrag in eintraege:
        for feld in felder:
            name, kind = feld["name"], feld["kind"]
            if feld["required"]:
                assert name in eintrag, f"{path.name}: '{name}' fehlt"
                assert eintrag[name] is not None, f"{path.name}: '{name}' ist null"
            if eintrag.get(name) is not None:
                assert isinstance(eintrag[name], _KIND_TO_TYPES[kind]), (
                    f"{path.name}: '{name}' ist {type(eintrag[name]).__name__}, "
                    f"erwartet {kind}"
                )


@pytest.mark.parametrize("path", _fixture_files(), ids=lambda p: p.name)
def test_generationsfixture_haelt_header_und_rumpf_zusammen(
    path: Path, contract: dict
) -> None:
    """„Header und Rumpf stammen aus derselben Generation" — die zentrale Regel.

    Ohne sie könnte ein Konsument eine Antwort aus Profil A für eine aus B
    halten. Die absichtlich widersprüchliche Fixture belegt, dass ein
    Konsument den Fall erkennen kann.
    """
    fixture = _load(path)
    if fixture["endpoint"] != contract["generation"]["endpoint"]:
        pytest.skip("keine /generation-Fixture")

    header = fixture["response"]["headers"].get(contract["generation"]["header"])
    rumpf = fixture["response"]["body"].get("generation_id")

    if fixture["contract_compliant"]:
        assert header == rumpf, f"{path.name}: Header und Rumpf widersprechen sich"
        assert (
            fixture["response"]["headers"].get("Cache-Control")
            == contract["generation"]["cache_control"]
        )
    else:
        assert header != rumpf or fixture["violates"]
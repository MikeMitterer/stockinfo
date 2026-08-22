"""Tests für `GET /fields` — der Vertrag zur Laufzeit abfragbar.

Ein Dokument, das niemand zur Laufzeit lesen kann, hilft einem Konsumenten
nicht: Er müsste raten, ob seine gecachte Feldliste noch stimmt. `/fields`
beantwortet das aus derselben Quelle, gegen die auch die Fixtures geprüft
werden (`contract/core-contract.json`) — eine zweite Wahrheit gäbe es sonst
sofort.
"""

import json

import pytest
from fastapi.testclient import TestClient

from app.contract import CONTRACT_FILE, core_contract
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_fields_nennt_die_vertragsversion(client: TestClient) -> None:
    """Ohne Nummer müsste ein Konsument die ganze Feldliste vergleichen."""
    antwort = client.get("/fields")

    assert antwort.status_code == 200
    daten = antwort.json()
    assert daten["core_version"] == core_contract()["core_version"]
    assert isinstance(daten["details_version"], int)


def test_fields_ist_nach_antworttyp_gegliedert(client: TestClient) -> None:
    """Ein flaches Array sagt nicht, in welcher Antwort ein Feld Pflicht ist.

    `price` und `currency` sind im Kurs Pflicht, in der Instrumentenzeile
    nicht. Eine flache Liste wäre damit ungenauer als das vorhandene
    OpenAPI-Dokument.
    """
    daten = client.get("/fields").json()

    assert set(daten["core"]) >= {"quote", "instrument", "daily", "fx"}
    kurs = {feld["name"]: feld for feld in daten["core"]["quote"]}
    instrument = {feld["name"]: feld for feld in daten["core"]["instrument"]}

    assert kurs["currency"]["required"] is True
    assert instrument["currency"]["required"] is False


def test_fields_liefert_art_und_bedeutung_je_feld(client: TestClient) -> None:
    """Die Bedeutung ist der Teil, den ein Konsument nirgends sonst bekommt."""
    kurs = {feld["name"]: feld for feld in client.get("/fields").json()["core"]["quote"]}

    assert kurs["price"]["kind"] == "number"
    assert kurs["stale"]["kind"] == "boolean"
    assert "TTL" in kurs["stale"]["meaning"]


def test_fields_stimmt_mit_dem_artefakt_ueberein(client: TestClient) -> None:
    """Die Antwort wird aus der Datei bedient, nicht aus einer zweiten Liste.

    Liefe die Laufzeitantwort aus einer eigenen Quelle, könnten Fixtures und
    Endpunkt auseinanderlaufen — und der Konsument bekäme je nach Weg eine
    andere Zusage.
    """
    artefakt = json.loads(CONTRACT_FILE.read_text(encoding="utf-8"))
    daten = client.get("/fields").json()

    assert daten["core"] == artefakt["core"]
    assert daten["core_version"] == artefakt["core_version"]


def test_fields_traegt_die_endpunkte_je_modell(client: TestClient) -> None:
    """Welches Modell an welchem Pfad hängt, muss ohne Ratespiel erkennbar sein."""
    daten = client.get("/fields").json()

    pfade = [eintrag["path"] for eintrag in daten["endpoints"]["quote"]]
    assert "/quote/{isin}" in pfade

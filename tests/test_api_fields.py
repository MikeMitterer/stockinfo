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
from tests import test_yaml_profile as yaml_profile


client = yaml_profile.client
volume = yaml_profile.volume


@pytest.mark.parametrize("language", [None, "en", "de"])
@pytest.mark.parametrize(
    ("section", "expected"),
    [
        (
            "core",
            "Latest known price in the trading currency. Never guessed or converted.",
        ),
        (
            "plugin_contract",
            "The price. Positive and finite; zero is not a valid price.",
        ),
    ],
)
def test_fields_beschreibungen_bleiben_englisch(
    client: TestClient, language: str | None, section: str, expected: str
) -> None:
    """Beide Vertragsquellen liefern Englisch unabhängig vom Sprachheader."""
    headers = {"Accept-Language": language} if language else {}
    response = client.get("/fields", headers=headers)

    assert response.status_code == 200
    quote = {field["name"]: field for field in response.json()[section]["quote"]}
    assert quote["price"]["meaning"] == expected


def test_fields_nennt_die_vertragsversion(client: TestClient) -> None:
    """Ohne Nummer müsste ein Konsument die ganze Feldliste vergleichen."""
    response = client.get("/fields")

    assert response.status_code == 200
    data = response.json()
    assert data["core_version"] == core_contract()["core_version"]
    assert isinstance(data["details_version"], int)


def test_fields_ist_nach_antworttyp_gegliedert(client: TestClient) -> None:
    """Ein flaches Array sagt nicht, in welcher Antwort ein Feld Pflicht ist.

    `price` und `currency` sind im Kurs Pflicht, in der Instrumentenzeile
    nicht. Eine flache Liste wäre damit ungenauer als das vorhandene
    OpenAPI-Dokument.
    """
    data = client.get("/fields").json()

    assert set(data["core"]) >= {"quote", "instrument", "daily", "fx"}
    quote = {field["name"]: field for field in data["core"]["quote"]}
    instrument = {field["name"]: field for field in data["core"]["instrument"]}

    assert quote["currency"]["required"] is True
    assert instrument["currency"]["required"] is False


def test_fields_liefert_art_und_bedeutung_je_feld(client: TestClient) -> None:
    """Die Bedeutung ist der Teil, den ein Konsument nirgends sonst bekommt."""
    quote = {
        field["name"]: field for field in client.get("/fields").json()["core"]["quote"]
    }

    assert quote["price"]["kind"] == "number"
    assert quote["stale"]["kind"] == "boolean"
    assert "TTL" in quote["stale"]["meaning"]


def test_fields_stimmt_mit_dem_artefakt_ueberein(client: TestClient) -> None:
    """Die Antwort wird aus der Datei bedient, nicht aus einer zweiten Liste.

    Liefe die Laufzeitantwort aus einer eigenen Quelle, könnten Fixtures und
    Endpunkt auseinanderlaufen — und der Konsument bekäme je nach Weg eine
    andere Zusage.
    """
    artifact = json.loads(CONTRACT_FILE.read_text(encoding="utf-8"))
    data = client.get("/fields").json()

    assert data["core"] == artifact["core"]
    assert data["core_version"] == artifact["core_version"]


def test_fields_traegt_die_endpunkte_je_modell(client: TestClient) -> None:
    """Welches Modell an welchem Pfad hängt, muss ohne Ratespiel erkennbar sein."""
    data = client.get("/fields").json()

    paths = [entry["path"] for entry in data["endpoints"]["quote"]]
    assert "/quote/{isin}" in paths

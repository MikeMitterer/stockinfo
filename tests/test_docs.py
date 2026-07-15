"""Tests für die eigene /docs-Route (Dark-Swagger); ReDoc ist entfernt."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_docs_liefert_swagger_ui_mit_dark_styling() -> None:
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text
    # Marker des Dark-Stylings (Invert-Filter) muss im HTML eingebettet sein.
    assert "hue-rotate(180deg)" in response.text


def test_redoc_ist_entfernt() -> None:
    assert client.get("/redoc").status_code == 404


def test_openapi_schema_bleibt_erreichbar() -> None:
    assert client.get("/openapi.json").status_code == 200

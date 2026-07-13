"""Tests für den konditionalen StaticFiles-Mount des Dashboards."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import mount_dashboard


def test_mount_wird_uebersprungen_wenn_verzeichnis_fehlt(tmp_path) -> None:
    app = FastAPI()
    mounted = mount_dashboard(app, str(tmp_path / "gibt-es-nicht"))
    assert mounted is False


def test_mount_serviert_index_wenn_vorhanden(tmp_path) -> None:
    (tmp_path / "index.html").write_text("<h1>StockInfo Dashboard</h1>")
    app = FastAPI()
    mounted = mount_dashboard(app, str(tmp_path))
    assert mounted is True

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "StockInfo Dashboard" in response.text

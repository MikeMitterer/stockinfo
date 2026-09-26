"""Plugin-Datei und aktive Konfiguration bestimmen den REST-Typkatalog."""

import json
from pathlib import Path
from uuid import UUID

import pytest
import yaml
from fastapi.testclient import TestClient

from app.config import get_settings
from app.container import get_sources_config
from app.main import app
from app.repository import QuoteRepository
from app.sources_config import ROLES


PLUGIN = """
from pathlib import Path
from stockinfo_plugin import QuoteSource, MetadataSource

class CatalogQuote(QuoteSource):
    name = "catalog-quote"
    api_version = 2
    SUPPORTED_TYPES = frozenset({"stock", "future-type"})

    def __init__(self, config):
        super().__init__(config)
        path = Path(config["builds"])
        path.write_text(path.read_text() + "built\\n" if path.exists() else "built\\n")

    def configuration_problem(self):
        return "Temporarily unavailable" if Path(self._config["failure"]).exists() else ""

    def handles(self, request):
        Path(self._config["fetches"]).touch()
        raise AssertionError("Der Katalog darf keine Fachabfrage auslösen")

class BrokenQuote(QuoteSource):
    name = "catalog-broken"
    api_version = 2
    SUPPORTED_TYPES = frozenset({"crypto"})

    def __init__(self, config):
        raise RuntimeError("Konstruktor defekt")

class InvalidQuote(QuoteSource):
    name = "catalog-invalid"
    api_version = 2
    SUPPORTED_TYPES = "stock"

class CatalogMetadata(MetadataSource):
    name = "catalog-meta"
    api_version = 2
    SUPPORTED_TYPES = frozenset({"metadata-type", "stock"})

SOURCES = [CatalogQuote, BrokenQuote, InvalidQuote, CatalogMetadata]
"""


@pytest.fixture
def volume(tmp_path: Path) -> Path:
    """Eigene Plugin-Datei, ohne Instrumente oder externe Datenquellen."""
    (tmp_path / "plugins").mkdir()
    (tmp_path / "plugins" / "catalog.py").write_text(PLUGIN)
    return tmp_path


def configure(volume: Path, **chains: list[str]) -> None:
    """Schreibt alle Rollen ausdrücklich; ungenannte Rollen bleiben leer."""
    config = {role: chains.get(role, []) for role in ROLES}
    config["providers"] = {
        "catalog-quote": {
            "builds": str(volume / "builds"),
            "failure": str(volume / "failure"),
            "fetches": str(volume / "fetches"),
        }
    }
    (volume / "sources.yaml").write_text(yaml.safe_dump(config))


def restart() -> TestClient:
    """Liest Konfiguration beim nächsten echten App-Start erneut."""
    get_settings.cache_clear()
    get_sources_config.cache_clear()
    return TestClient(app)


def test_typen_kommen_aus_plugins_ohne_instrumente(volume: Path) -> None:
    """Unbekannter Typ erscheint ohne Asset; inaktive Plugins tragen nichts bei."""
    configure(volume, quotes=["catalog-quote"], etf_meta=["catalog-meta"])
    with restart() as client:
        assert QuoteRepository(str(volume / "stockinfo.db")).list_instruments() == []
        builds = (volume / "builds").read_text()
        response = client.get("/instrument-types")
        assert response.status_code == 200
        assert response.json()["instrument_types"] == [
            "future-type",
            "metadata-type",
            "stock",
        ]
        assert response.json()["complete"] is True
        assert all(
            source["status"] == "available" for source in response.json()["sources"]
        )
        assert response.headers["Cache-Control"] == "no-store"
        assert response.headers["StockInfo-Generation"]
        assert client.get("/instrument-types").json() == response.json()
        assert (volume / "builds").read_text() == builds
        assert not (volume / "fetches").exists()
        assert QuoteRepository(str(volume / "stockinfo.db")).list_instruments() == []


def test_laufende_konfiguration_bis_zum_neustart(volume: Path) -> None:
    """Dateiedit allein verändert den laufenden Katalog nicht; Neustart schon."""
    configure(volume, quotes=["catalog-quote"])
    with restart() as client:
        before = client.get("/instrument-types").json()
        configure(volume)
        assert client.get("/instrument-types").json() == before
    with restart() as client:
        assert client.get("/instrument-types").json() == {
            "instrument_types": [],
            "complete": True,
            "sources": [],
        }


def test_entferntes_plugin_bleibt_als_luecke_sichtbar(volume: Path) -> None:
    """Ein konfigurierter Name ohne ladbares Plugin ist keine vollständige Leermenge."""
    configure(volume, quotes=["missing"])
    with restart() as client:
        response = client.get("/instrument-types")
        assert response.status_code == 200
        assert response.json() == {
            "instrument_types": [],
            "complete": False,
            "sources": [
                {
                    "name": "missing",
                    "role": "quotes",
                    "instrument_types": [],
                    "status": "unknown_source",
                }
            ],
        }


def test_betriebsstoerung_entfernt_keine_deklarierten_typen(volume: Path) -> None:
    """Bekannte Deklarationen bleiben auch bei Baufehler und späterem Ausfall lesbar."""
    configure(volume, quotes=["catalog-quote", "catalog-broken"])
    with restart() as client:
        before = client.get("/instrument-types").json()
        assert before["instrument_types"] == ["crypto", "future-type", "stock"]
        assert before["complete"] is True
        assert [source["status"] for source in before["sources"]] == [
            "available",
            "unavailable",
        ]
        (volume / "failure").touch()
        failed = client.get("/instrument-types").json()
        assert failed["instrument_types"] == before["instrument_types"]
        assert failed["complete"] is True
        assert [source["status"] for source in failed["sources"]] == [
            "unavailable",
            "unavailable",
        ]
        (volume / "failure").unlink()
        assert client.get("/instrument-types").json() == before


def test_falsche_rolle_und_deklaration_verdecken_gesunde_quelle_nicht(
    volume: Path,
) -> None:
    """Fehler werden einzeln benannt, ohne eine feste Ersatzliste zu erfinden."""
    configure(
        volume, quotes=["catalog-quote", "catalog-invalid"], daily=["catalog-quote"]
    )
    with restart() as client:
        body = client.get("/instrument-types").json()
        assert body["instrument_types"] == ["future-type", "stock"]
        assert body["complete"] is False
        assert [source["status"] for source in body["sources"]] == [
            "available",
            "invalid_declaration",
            "unsupported_role",
        ]


@pytest.mark.parametrize(
    "role, expected",
    [
        ("etf_meta", ["etc", "etf", "fund"]),
        ("fx", []),
        ("quotes", ["bond", "crypto", "etc", "etf", "fund", "stock"]),
    ],
)
def test_nur_die_konfigurierte_rollenklasse_zaehlt(
    volume: Path, role: str, expected: list[str]
) -> None:
    """Yfinance-Metadaten versprechen keine Aktien; FX allein keine Asset-Typen."""
    configure(volume, **{role: ["yfinance"]})
    with restart() as client:
        body = client.get("/instrument-types").json()
        assert body["complete"] is True
        assert body["instrument_types"] == expected


@pytest.mark.parametrize(
    "declaration, expected_status",
    [
        ("frozenset()", "available"),
        ("frozenset({'', 'stock'})", "invalid_declaration"),
        ("frozenset({2})", "invalid_declaration"),
        ("frozenset({' stock'})", "invalid_declaration"),
    ],
)
def test_leere_und_ungueltige_typdeklarationen(
    volume: Path, declaration: str, expected_status: str
) -> None:
    """Leere Zusage ist gültig; fehlerhafte Einträge machen die Auskunft unvollständig."""
    path = volume / "plugins" / "catalog.py"
    path.write_text(
        PLUGIN.replace('SUPPORTED_TYPES = "stock"', f"SUPPORTED_TYPES = {declaration}")
    )
    configure(volume, quotes=["catalog-invalid"])
    with restart() as client:
        body = client.get("/instrument-types").json()
        assert body["instrument_types"] == []
        assert body["complete"] is (expected_status == "available")
        assert body["sources"][0]["status"] == expected_status


@pytest.mark.parametrize(
    "variant, names",
    [("200", ["catalog-quote"]), ("200-empty", []), ("200-incomplete", ["missing"])],
)
def test_http_fixture_entspricht_der_laufenden_api(
    volume: Path, variant: str, names: list[str]
) -> None:
    """Veröffentlichte Konsumentenbeispiele entsprechen den echten HTTP-Antworten."""
    fixture = json.loads(
        (
            Path(__file__).parents[1]
            / "contract"
            / "fixtures"
            / f"instrument-types-{variant}.json"
        ).read_text()
    )
    configure(volume, quotes=names)
    with restart() as client:
        response = client.request(
            fixture["request"]["method"], fixture["request"]["path"]
        )
        assert response.status_code == fixture["response"]["status"]
        assert response.json() == fixture["response"]["body"]
        for name in ("Content-Type", "Cache-Control"):
            assert response.headers[name] == fixture["response"]["headers"][name]
        assert UUID(response.headers["StockInfo-Generation"])
        assert UUID(fixture["response"]["headers"]["StockInfo-Generation"])

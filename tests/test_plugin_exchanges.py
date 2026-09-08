"""Deklarierte Handelsplätze durch normalen Start, Aufnahme und REST."""

from pathlib import Path
import shutil
import sqlite3
from importlib.metadata import EntryPoint

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.sources_registry import register_loaded


@pytest.mark.parametrize("declared", [False, True])
@pytest.mark.parametrize("load_path", ["directory", "entry_point"])
def test_neuer_mic_ist_ueber_den_normalen_aufnahmeweg_verwendbar(
    tmp_path, monkeypatch, declared, load_path
):
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    source = plugins / "local.py"
    shutil.copy(Path("plugin_api/examples/yaml_file.py"), source)
    with source.open("a") as stream:
        if declared:
            stream.write("\nfrom stockinfo_plugin import ExchangeSpec, MicCoverage\n")
        stream.write("\nfrom dataclasses import replace\n")
        stream.write("\nclass RegionalSource(YamlFileSource):\n")
        stream.write('    name = "regional"\n    api_version = 2\n')
        if declared:
            stream.write(
                '    EXCHANGES = (ExchangeSpec("XBUD", "Budapest", "europe", "HUF"),)\n'
            )
            stream.write(
                '    MIC_SUPPORT = {"quotes": MicCoverage(("XBUD",), "inventory")}\n'
            )
        stream.write("""    def handles(self, request):
        return True
    def resolve(self, request):
        if request.symbol == 'DEMO.XBUD':
            request = replace(request, symbol='DEMO')
        return super().resolve(request)

SOURCES = [RegionalSource]
""")
    if load_path == "entry_point":
        module = tmp_path / "regional_test_plugin.py"
        source.rename(module)
        monkeypatch.syspath_prepend(str(tmp_path))
        import sys

        monkeypatch.delitem(sys.modules, "regional_test_plugin", raising=False)
        monkeypatch.setattr(
            "app.plugin_loader.entry_points",
            lambda **_: [
                EntryPoint(
                    name="regional",
                    value="regional_test_plugin:RegionalSource",
                    group="stockinfo.sources",
                )
            ],
        )
    (tmp_path / "assets.yaml").write_text("""version: 1
instruments:
  - id: demo
    identity: {kind: listed, ticker: DEMO, mic: XBUD}
    name: Regional Demo
    instrument_type: stock
    price: {value: 42, currency: HUF, as_of: "2026-01-03T21:00:00+00:00"}
""")
    (tmp_path / "sources.yaml").write_text(f"""resolvers: [regional]
quotes: [regional]
daily: [regional]
etf_meta: [regional]
fx: []
providers:
  regional:
    path: {tmp_path / "assets.yaml"}
""")
    database = Path(get_settings().database_path)
    assert not database.exists()
    try:
        with TestClient(app) as client:
            response = client.post(
                "/instruments/intake", json={"identifier": "DEMO.XBUD"}
            )
            if not declared:
                assert response.status_code == 400
                return
            assert response.status_code == 201, response.text
            assert response.json()["identity"]["mic"] == "XBUD"
            assert response.json()["symbol"] == "DEMO.XBUD"
            catalog = client.get("/exchanges").json()["catalog"]
            entry = next(item for item in catalog if item.get("mic") == "XBUD")
            assert entry["declared_by"] == ["regional"]
            assert entry["support"] == [
                {
                    "source": "regional",
                    "role": "quotes",
                    "scope": "inventory",
                    "usable": True,
                }
            ]
            with sqlite3.connect(database) as connection:
                assert connection.execute(
                    "SELECT symbol, ticker, mic FROM instruments"
                ).fetchall() == [("DEMO.XBUD", "DEMO", "XBUD")]
            register_loaded(())
            assert not any(
                item.get("mic") == "XBUD"
                for item in client.get("/exchanges").json()["catalog"]
            )
            with sqlite3.connect(database) as connection:
                assert connection.execute(
                    "SELECT symbol FROM instruments"
                ).fetchall() == [("DEMO.XBUD",)]
    finally:
        register_loaded(())

"""Aktive Profile liefern echte Online- und Dateiabdeckung über REST."""

from pathlib import Path
import shutil

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.sources_registry import register_loaded


def _write_inventory(path, mic="XETR"):
    path.write_text(f'''version: 1
instruments:
  - id: price
    identity: {{kind: listed, ticker: PRICE, mic: {mic}}}
    name: Price fixture
    instrument_type: stock
    price: {{value: 42, currency: EUR, as_of: "2026-01-03T21:00:00+00:00"}}
  - id: history
    identity: {{kind: listed, ticker: HISTORY, mic: XNAS}}
    name: History fixture
    instrument_type: etf
    history:
      currency: USD
      closes: [{{date: "2026-01-02", value: 12}}]
    metadata: {{ter_bps: 20}}
  - id: identity
    identity: {{kind: listed, ticker: IDENTITY, mic: XTSE}}
    name: Identity fixture
    instrument_type: stock
  - id: pair
    identity: {{kind: pair, base: BTC, quote_currency: EUR}}
    name: Bitcoin
    instrument_type: crypto
''')


@pytest.mark.parametrize("online", [False, True], ids=["nur-datei", "online-mit-datei"])
def test_aktive_abdeckung_folgt_profil_und_datei(tmp_path, online):
    from app.config import get_settings

    assert not Path(get_settings().database_path).exists()
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    shutil.copy(Path("plugin_api/examples/yaml_file.py"), plugins / "local.py")
    with (plugins / "local.py").open("a") as stream:
        stream.write('\nfrom stockinfo_plugin import ExchangeSpec\nYamlFileSource.EXCHANGES = (ExchangeSpec("XBUD", "Budapest", "europe", "HUF"),)\n')
    inventory = tmp_path / "assets.yaml"
    _write_inventory(inventory)
    chains = {
        "resolvers": ["openfigi", "yahoo-search"] if online else [],
        "quotes": ["yfinance"] if online else [],
        "daily": ["yfinance"] if online else [],
        "etf_meta": ["justetf", "yfinance"] if online else [],
        "fx": [],
    }
    (tmp_path / "sources.yaml").write_text(
        "\n".join(f"{role}: {names + ['yaml-file']}" for role, names in chains.items())
        + "\nproviders:\n  yaml-file:\n    path: assets.yaml\n"
    )
    try:
        with TestClient(app) as client:
            def coverage():
                response = client.get("/exchanges")
                assert response.status_code == 200
                body = response.json()
                assert body["unspecified_support"] == []
                return {row["mic"]: row["support"] for row in body["catalog"] if row["kind"] == "exchange"}

            def file_roles(rows, mic):
                entries = [row for row in rows[mic] if row["source"] == "yaml-file"]
                assert all(row["scope"] == "inventory" and row["usable"] for row in entries)
                return {row["role"] for row in entries}

            rows = coverage()
            assert rows["XBUD"] == []
            assert file_roles(rows, "XETR") == {"resolvers", "quotes"}
            assert file_roles(rows, "XNAS") == {"resolvers", "quotes", "daily", "etf_meta"}
            assert file_roles(rows, "XTSE") == {"resolvers"}
            assert file_roles(rows, "XNYS") == set()
            market = {(row["source"], row["role"]) for row in rows["XETR"] if row["scope"] == "market"}
            assert market == ({("openfigi", "resolvers"), ("yahoo-search", "resolvers"),
                               ("yfinance", "quotes"), ("yfinance", "daily"),
                               ("yfinance", "etf_meta"), ("justetf", "etf_meta")} if online else set())
            assert not any(row["role"] == "fx" for entries in rows.values() for row in entries)
            _write_inventory(inventory, "XPAR")
            rows = coverage()
            assert file_roles(rows, "XETR") == set()
            assert file_roles(rows, "XPAR") == {"resolvers", "quotes"}
            inventory.write_text("broken: [")
            body = client.get("/exchanges").json()
            assert not any(row["source"] == "yaml-file" for item in body["catalog"] if item["kind"] == "exchange" for row in item["support"])
            _write_inventory(inventory)
            assert file_roles(coverage(), "XETR") == {"resolvers", "quotes"}
            register_loaded(())
            body = client.get("/exchanges").json()
            assert not any(item.get("mic") == "XBUD" for item in body["catalog"])
            assert not any(row["source"] == "yaml-file" for item in body["catalog"] if item["kind"] == "exchange" for row in item["support"])
    finally:
        register_loaded(())


@pytest.mark.parametrize("answer", ["exception", "bad-mic", "unknown-mic", "bad-scope", "bad-shape"])
def test_fehlerhafte_aktuelle_zusage_erfindet_keine_abdeckung(answer):
    from stockinfo_plugin import MicCoverage, QuoteSource
    from app.config import get_settings
    from app.exchange_catalog import catalog_annotations
    from app.plugin_loader import spec_from_class
    from app.sources_config import ROLES, SourcesConfig
    from app.sources_registry import build_chain, describe_chain

    class BrokenSource(QuoteSource):
        name = "broken"
        api_version = 2
        MIC_SUPPORT = {"quotes": MicCoverage(("XETR",))}

        @classmethod
        def get_mic_support(cls, config):
            if answer == "exception":
                raise OSError("unreadable inventory")
            if answer == "bad-shape":
                return []
            return {"quotes": MicCoverage(
                ("US" if answer == "bad-mic" else "XXXX" if answer == "unknown-mic" else "XETR",),
                "invalid" if answer == "bad-scope" else "inventory",
            )}

    config = SourcesConfig(chains={role: ("broken",) if role == "quotes" else () for role in ROLES})
    register_loaded((spec_from_class(BrokenSource),))
    try:
        build_chain("quotes", config, get_settings())
        entries, unspecified = catalog_annotations(describe_chain("quotes", config))
        assert all(row["support"] == [] for row in entries.values())
        assert unspecified == [{"source": "broken", "role": "quotes", "usable": False}]
    finally:
        register_loaded(())

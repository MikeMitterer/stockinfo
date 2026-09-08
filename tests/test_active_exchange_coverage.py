"""Aktive Profile liefern echte Online- und Dateiabdeckung über REST."""

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.sources_registry import register_loaded


def _write_inventory(path, mic="XETR"):
    path.write_text(f"""version: 1
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
""")


@pytest.fixture(params=[False, True], ids=["nur-datei", "online-mit-datei"])
def active_profile(tmp_path, request):
    online = request.param
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
            yield client, inventory, online
    finally:
        register_loaded(())


def test_aktive_abdeckung_folgt_profil_und_datei(active_profile):
    client, inventory, online = active_profile
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


@pytest.fixture
def intake_profile(active_profile, monkeypatch):
    from stockinfo_plugin import NotFound

    from app.plugins.openfigi_resolver import OpenFigiResolverPlugin
    from app.plugins.yahoo_search_resolver import YahooSearchResolverPlugin
    from app.plugins.yfinance_quotes import YFinancePlugin
    from app.sources_registry import specs_by_name

    client, inventory, online = active_profile
    calls = []
    resolutions = []

    def no_online_hit(self, request):
        resolutions.append(request)
        return NotFound()

    def no_online_quote(self, request):
        calls.append("online")
        return NotFound()

    monkeypatch.setattr(OpenFigiResolverPlugin, "resolve", no_online_hit)
    monkeypatch.setattr(YahooSearchResolverPlugin, "resolve", no_online_hit)
    monkeypatch.setattr(YFinancePlugin, "fetch_quote", no_online_quote)
    source = specs_by_name()["yaml-file"].declaration
    fetch_quote = source.fetch_quote
    resolve = source.resolve

    def file_resolution(self, request):
        resolutions.append(request)
        return resolve(self, request)

    monkeypatch.setattr(source, "resolve", file_resolution)

    def file_quote(self, request):
        calls.append("file")
        return fetch_quote(self, request)

    monkeypatch.setattr(source, "fetch_quote", file_quote)
    original = inventory.read_text() + """
  - id: uncovered
    identity: {kind: listed, ticker: BLOCKED, mic: XBUD, isin: US0378331005}
    name: Uncovered fixture
    instrument_type: stock
    metadata: {ter_bps: 10}
  - id: bond
    identity: {kind: isin_only, isin: DE0001102531}
    name: Bond fixture
    instrument_type: bond
"""
    inventory.write_text(original)

    return client, inventory, online, calls, source, original, resolutions


@pytest.mark.parametrize("first_identifier", ["BLOCKED.XBUD", "US0378331005"])
def test_aufnahme_prueft_dieselbe_aktuelle_abdeckung(intake_profile, monkeypatch, first_identifier):
    client, inventory, online, calls, source, original, resolutions = intake_profile

    def add(identifier):
        return client.post("/instruments/intake", json={"identifier": identifier})

    def covered(mic):
        row = next(row for row in client.get("/exchanges").json()["catalog"] if row.get("mic") == mic)
        return any(item["role"] == "quotes" and item["usable"] for item in row["support"])

    def rejected(identifier, mic):
        before = client.get("/instruments").json()
        count = len(calls)
        resolution_count = len(resolutions)
        response = add(identifier)
        assert response.status_code == 400, response.text
        assert response.json() == {"code": "exchange_not_covered", "params": {"mic": mic}}
        assert len(calls) == count, "Ein abgelehnter Handelsplatz wurde trotzdem bepreist"
        if "." in identifier:
            assert len(resolutions) == resolution_count, "Der Symbolweg hat trotzdem eine Quelle gefragt"
        assert client.get("/instruments").json() == before

    assert not covered("XBUD")
    rejected(first_identifier, "XBUD")
    rejected("BLOCKED.XBUD", "XBUD")
    rejected("US0378331005", "XBUD")
    assert covered("XETR")
    assert add("PRICE.DE").status_code == 201
    assert add("PRICE.XETR").status_code == 200
    assert add("DE0001102531").status_code == 201
    if not online:
        assert not covered("XTSE")
        rejected("IDENTITY.TO", "XTSE")
        rejected("IDENTITY.XTSE", "XTSE")

    # Ergänzung gilt sofort, auch für die ISIN-Aufnahme und die Kursanzeige.
    inventory.write_text(original.replace("name: Uncovered fixture", 'price: {value: 50, currency: HUF, as_of: "2026-01-03T21:00:00+00:00"}\n    name: Uncovered fixture'))
    assert covered("XBUD")
    assert add("US0378331005").status_code == 201
    inventory.write_text(original)
    assert not covered("XBUD")
    rejected("US0378331005", "XBUD")
    rejected("BLOCKED.XBUD", "XBUD")

    inventory.write_text("broken: [")
    assert not covered("XBUD")
    rejected("BLOCKED.XBUD", "XBUD")
    inventory.write_text(original)

    # Ungültige/fehlende Selbstauskunft darf keinen funktionierenden Abruf legitimieren.
    for declaration in ({}, {"quotes": "invalid"}):
        monkeypatch.setattr(source, "get_mic_support", classmethod(lambda cls, config: declaration))
        assert not covered("XBUD")
        rejected("BLOCKED.XBUD", "XBUD")


def test_ticker_rueckfall_uebernimmt_keine_fremde_boerse(intake_profile):
    client, inventory, _, _, _, original, _ = intake_profile
    inventory.write_text(original + """
  - id: paris
    identity: {kind: listed, ticker: PARIS, mic: XPAR}
    name: Paris fixture
    instrument_type: stock
    price: {value: 2, currency: EUR, as_of: "2026-01-03T21:00:00+00:00"}
""")
    response = client.post("/instruments/intake", json={"identifier": "PRICE.PA"})
    assert response.status_code == 502
    assert client.get("/instruments").json() == []


def test_aufnahme_kennt_paare_ohne_einen_handelsplatz_zu_erfinden(intake_profile):
    client, inventory, _, _, _, original, _ = intake_profile
    inventory.write_text(original.replace("name: Bitcoin", 'price: {value: 50000, currency: EUR, as_of: "2026-01-03T21:00:00+00:00"}\n    name: Bitcoin'))
    response = client.post("/instruments/intake", json={"identifier": "BTC-EUR"})
    assert response.status_code == 201, response.text
    assert response.json()["identity"] == {"kind": "pair", "base": "BTC", "quote_currency": "EUR"}
    response = client.post("/instruments/intake", json={"identifier": "MISSING"})
    assert response.status_code == 400
    assert response.json()["code"] == "symbol_without_exchange_suffix"
    response = client.post("/instruments/intake", json={"identifier": "PRICE"})
    assert response.status_code == 400
    assert response.json()["code"] == "symbol_without_exchange_suffix"


@pytest.mark.parametrize("failure", ["unsupported", "currency", "unavailable"])
def test_aufnahme_erhaelt_die_strukturierten_quellenfehler(intake_profile, monkeypatch, failure):
    from datetime import datetime, timezone

    from stockinfo_plugin import Quote, Unavailable, Unsupported

    client, _, _, _, source, _, _ = intake_profile
    if failure == "unsupported":
        monkeypatch.setattr(source, "resolve", lambda self, request: Unsupported("index"))
    else:
        answer = (Quote(price=1, currency="USD", as_of=datetime.now(timezone.utc))
                  if failure == "currency" else Unavailable("test failure"))
        monkeypatch.setattr(source, "fetch_quote", lambda self, request: answer)
    response = client.post("/instruments/intake", json={"identifier": "BTC-EUR"})
    assert response.status_code == (400 if failure == "unsupported" else 502)
    assert response.json()["code"] == {
        "unsupported": "unsupported_instrument_type",
        "currency": "quote_currency_mismatch",
        "unavailable": "quote_unavailable",
    }[failure]
    assert client.get("/instruments").json() == []

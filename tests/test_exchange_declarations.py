"""Konflikte und Lebenszyklus des deklarierten Katalogs."""

from dataclasses import replace

import pytest
from stockinfo_plugin import DailyCloseSource, ExchangeSpec, MicCoverage, QuoteSource

from app.config import get_settings
from app.exchange_catalog import catalog_annotations, prepare_catalog
from app.exchanges import EXCHANGES, identity_from_input
from app.plugin_loader import spec_from_class
from app.sources_config import ROLES, SourcesConfig
from app.sources_registry import (
    build_chain,
    describe_chain,
    register_loaded,
    specs_by_name,
)

EXCHANGE = ExchangeSpec("XBUD", "Budapest", "europe", "HUF")


class RegionalSource(QuoteSource, DailyCloseSource):
    name = "regional"
    api_version = 2
    EXCHANGES = (EXCHANGE,)
    MIC_SUPPORT = {"quotes": MicCoverage(("XBUD",)), "daily": MicCoverage(())}


@pytest.fixture(autouse=True)
def clean_catalog():
    register_loaded(())
    yield
    register_loaded(())


def configure(*sources):
    register_loaded(tuple(spec_from_class(source) for source in sources))
    config = SourcesConfig(
        chains={
            role: tuple(source.name for source in sources)
            if role in ("quotes", "daily")
            else ()
            for role in ROLES
        }
    )
    for role in ("quotes", "daily"):
        build_chain(role, config, get_settings())
    return config


@pytest.mark.parametrize("reverse", [False, True])
def test_widerspruch_verwirft_beide_quellen_unabhaengig_von_der_reihenfolge(reverse):
    class OtherSource(RegionalSource):
        name = "other"
        EXCHANGES = (replace(EXCHANGE, name="Different"),)

    sources = [RegionalSource, OtherSource]
    config = configure(*reversed(sources) if reverse else sources)
    assert "XBUD" not in EXCHANGES
    assert all(
        not entry.usable and "Conflicting" in entry.reason
        for entry in describe_chain("quotes", config)
    )


def test_identische_deklarationen_bleiben_nach_entfernen_einer_quelle_erhalten():
    class OtherSource(RegionalSource):
        name = "other"

    config = configure(RegionalSource, OtherSource)
    annotations, _ = catalog_annotations(describe_chain("quotes", config))
    assert annotations["XBUD"]["declared_by"] == ["other", "regional"]
    config = configure(RegionalSource)
    annotations, _ = catalog_annotations(describe_chain("quotes", config))
    assert annotations["XBUD"]["declared_by"] == ["regional"]
    configure()
    assert identity_from_input("DEMO.XBUD") is None


def test_core_definition_und_alias_bleiben_bei_ueberschreibversuch_erhalten():
    original = EXCHANGES["XETR"]

    class OtherSource(RegionalSource):
        EXCHANGES = (ExchangeSpec("XETR", "Different", "europe", "HUF"),)
        MIC_SUPPORT = {"quotes": MicCoverage(("XETR",))}

    config = configure(OtherSource)
    assert EXCHANGES["XETR"] == original
    assert identity_from_input("SAP.DE") == ("SAP", "XETR")
    assert not describe_chain("quotes", config)[0].usable


def test_identische_referenz_ersetzt_den_core_eintrag_nicht():
    original = EXCHANGES["XETR"]

    class ReferencingSource(RegionalSource):
        EXCHANGES = (
            ExchangeSpec("XETR", original.name, original.region, original.currency),
        )
        MIC_SUPPORT = {"quotes": MicCoverage(("XETR",))}

    config = configure(ReferencingSource)
    assert prepare_catalog(specs_by_name(), config) == {}
    assert describe_chain("quotes", config)[0].usable
    assert EXCHANGES["XETR"] == original
    assert EXCHANGES["XETR"].alias == "DE"
    assert identity_from_input("EUNL.DE") == ("EUNL", "XETR")


def test_vorhandener_mic_darf_ohne_neudefinition_unterstuetzt_werden():
    class ExistingSource(RegionalSource):
        EXCHANGES = ()
        MIC_SUPPORT = {"quotes": MicCoverage(("XETR",))}

    config = configure(ExistingSource)
    annotations, unspecified = catalog_annotations(
        [
            entry
            for role in ("quotes", "daily")
            for entry in describe_chain(role, config)
        ]
    )
    assert annotations["XETR"]["support"][0]["usable"]
    assert annotations["XETR"]["provenance"] == {"kind": "core"}
    assert unspecified == [{"source": "regional", "role": "daily", "usable": True}]


def test_ausfall_ist_keine_aktive_unterstuetzung_und_leere_rolle_ist_nicht_unbekannt():
    class OfflineSource(RegionalSource):
        def configuration_problem(self):
            return "Unavailable"

    config = configure(OfflineSource)
    annotations, unspecified = catalog_annotations(
        [
            entry
            for role in ("quotes", "daily")
            for entry in describe_chain(role, config)
        ]
    )
    assert annotations["XBUD"]["support"] == [
        {"source": "regional", "role": "quotes", "scope": "market", "usable": False}
    ]
    assert unspecified == []


@pytest.mark.parametrize(
    "declarations,support",
    [
        ((replace(EXCHANGE, mic="US"),), {}),
        ((replace(EXCHANGE, name=""),), {}),
        ((replace(EXCHANGE, currency="ZZZ"),), {}),
        ((EXCHANGE, EXCHANGE), {}),
        ((), {"quotes": MicCoverage(("ZZZZ",))}),
        ((), {"fx": MicCoverage(("XETR",))}),
        ((), {"quotes": MicCoverage(("XETR", "XETR"))}),
        ((), {"quotes": MicCoverage(("XETR",), "unknown")}),
    ],
)
def test_ungueltige_angaben_werden_diagnostiziert(declarations, support):
    class InvalidSource(RegionalSource):
        EXCHANGES = declarations
        MIC_SUPPORT = support

    config = configure(InvalidSource)
    entry = describe_chain("quotes", config)[0]
    assert not entry.usable
    assert entry.reason
    assert "XBUD" not in EXCHANGES


def test_installation_allein_erweitert_den_katalog_nicht():
    register_loaded((spec_from_class(RegionalSource),))
    config = SourcesConfig(chains={role: () for role in ROLES})
    assert prepare_catalog(specs_by_name(), config) == {}
    assert "XBUD" not in EXCHANGES

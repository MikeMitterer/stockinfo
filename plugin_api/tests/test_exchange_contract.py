"""Der geerbte Autor-Vertrag prüft Deklarationen ohne Host-Katalog."""

from types import MappingProxyType

import pytest

from stockinfo_plugin import ExchangeSpec, MicCoverage, QuoteSource
from stockinfo_plugin.testing import FakeQuoteSource, QuoteContract


@pytest.mark.parametrize("invalid", ["mic", "role", "scope", "currency", "duplicate"])
def test_autor_vertrag_weist_ungueltige_deklaration_ab(invalid):
    class DeclaredSource(FakeQuoteSource):
        EXCHANGES = (ExchangeSpec("XBUD", "Budapest", "europe", "HUF"),)
        MIC_SUPPORT = MappingProxyType({"quotes": MicCoverage(("XBUD",))})

    if invalid == "mic":
        DeclaredSource.MIC_SUPPORT = {"quotes": MicCoverage(("US",))}
    elif invalid == "role":
        DeclaredSource.MIC_SUPPORT = {"resolvers": MicCoverage(("XBUD",))}
    elif invalid == "scope":
        DeclaredSource.MIC_SUPPORT = {"quotes": MicCoverage(("XBUD",), "unknown")}
    elif invalid == "currency":
        DeclaredSource.EXCHANGES = (ExchangeSpec("XBUD", "Budapest", "europe", "bad"),)
    else:
        DeclaredSource.EXCHANGES *= 2
    contract = QuoteContract()
    contract.make_source = DeclaredSource
    with pytest.raises(ValueError):
        contract.test_boersendeklarationen_sind_gueltig()


def test_optionale_und_neue_deklarationen_brauchen_keinen_host():
    contract = QuoteContract()
    contract.make_source = FakeQuoteSource
    contract.test_boersendeklarationen_sind_gueltig()

    class DeclaredSource(FakeQuoteSource):
        EXCHANGES = (ExchangeSpec("XBUD", "Budapest", "europe", "HUF"),)
        MIC_SUPPORT = MappingProxyType({"quotes": MicCoverage(("XBUD",), "inventory")})

    contract.make_source = DeclaredSource
    contract.test_boersendeklarationen_sind_gueltig()
    contract.test_kein_veraenderlicher_zustand_an_der_klasse()


def test_autor_vertrag_prueft_auch_die_aktuelle_bestandszusage():
    class InventorySource(QuoteSource):
        @classmethod
        def get_mic_support(cls, config):
            return {"quotes": MicCoverage((config["mic"],), "inventory")}

    contract = QuoteContract()
    contract.make_source = lambda: InventorySource({"mic": "US"})
    with pytest.raises(ValueError, match="canonical"):
        contract.test_boersendeklarationen_sind_gueltig()
    contract.make_source = lambda: InventorySource({"mic": "XETR"})
    contract.test_boersendeklarationen_sind_gueltig()

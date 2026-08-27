"""Das Testkit: Verträge, Szenarien und Doubles.

Bis T-27a war das eine einzelne `testing.py` mit zwei Verträgen. Mit fünf
Rollen, dem Szenarioformat und den Doubles wären daraus rund achthundert Zeilen
in einer Datei geworden, die drei verschiedene Fragen beantwortet — deshalb ein
Paket. Der Importweg bleibt derselbe::

    from stockinfo_plugin.testing import ResolverContract, FakeResolver

===================== =========================================================
`contracts`           Was eine Quelle je Rolle erfüllen muss
`scenarios`           Ein Fall, einmal beschrieben, in zwei Betriebsarten
`doubles`             Quellen auf Ansage, mit Aufrufprotokoll und Fake-Uhr
===================== =========================================================
"""

from stockinfo_plugin.testing.contracts import (
    DailyContract,
    FxContract,
    MetadataContract,
    QuoteContract,
    ResolverContract,
    SourceContract,
)
from stockinfo_plugin.testing.doubles import (
    EPOCH,
    Call,
    CallLog,
    FakeClock,
    FakeDailySource,
    FakeFxSource,
    FakeMetadataSource,
    FakeQuoteSource,
    FakeResolver,
    FakeSource,
)
from stockinfo_plugin.testing.scenarios import (
    HIT_TYPES,
    MISS_TYPES,
    DirectRunner,
    Scenario,
    ScenarioRunner,
    check_scenario,
    run_scenarios,
    validate_scenarios,
)

__all__ = [
    "EPOCH",
    "HIT_TYPES",
    "MISS_TYPES",
    "Call",
    "CallLog",
    "DailyContract",
    "DirectRunner",
    "FakeClock",
    "FakeDailySource",
    "FakeFxSource",
    "FakeMetadataSource",
    "FakeQuoteSource",
    "FakeResolver",
    "FakeSource",
    "FxContract",
    "MetadataContract",
    "QuoteContract",
    "ResolverContract",
    "Scenario",
    "ScenarioRunner",
    "SourceContract",
    "check_scenario",
    "run_scenarios",
    "validate_scenarios",
]

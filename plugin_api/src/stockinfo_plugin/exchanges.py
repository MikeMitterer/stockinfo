"""Optionale Handelsplatzdeklarationen ohne Abhängigkeit vom Host."""

from dataclasses import dataclass
from collections.abc import Mapping
from typing import Literal

from stockinfo_plugin.invariants import currency_is_valid, mic_is_wellformed


@dataclass(frozen=True)
class ExchangeSpec:
    """Neue Börse; die Anbieter-Schreibweise bleibt im Plugin."""

    mic: str
    name: str
    region: str
    currency: str


@dataclass(frozen=True)
class MicCoverage:
    """Deklarierte Unterstützung, gegebenenfalls nur für den Dateibestand."""

    mics: tuple[str, ...]
    scope: Literal["market", "inventory"] = "market"


def validate_exchanges(declaration: object, roles: frozenset[str]) -> None:
    """Prüft Struktur und Werte; Katalogkonflikte prüft der Host separat."""
    exchanges = getattr(declaration, "EXCHANGES", ())
    support = getattr(declaration, "MIC_SUPPORT", {})
    if not isinstance(exchanges, tuple) or not isinstance(support, Mapping):
        raise ValueError("EXCHANGES must be a tuple and MIC_SUPPORT a mapping")
    seen = set()
    for exchange in exchanges:
        if not isinstance(exchange, ExchangeSpec):
            raise ValueError("EXCHANGES requires ExchangeSpec entries")
        if not mic_is_wellformed(exchange.mic) or exchange.mic in seen:
            raise ValueError("Exchange MIC must be canonical and unique")
        if not isinstance(exchange.name, str) or not exchange.name.strip():
            raise ValueError("Exchange name must not be empty")
        if exchange.region not in ("germany", "usa", "europe", "global"):
            raise ValueError("Unknown exchange region")
        if not currency_is_valid(exchange.currency):
            raise ValueError("Invalid exchange currency")
        seen.add(exchange.mic)
    for role, coverage in support.items():
        if role not in roles or role == "fx":
            raise ValueError("MIC_SUPPORT requires an implemented listing role")
        if not isinstance(coverage, MicCoverage) or not isinstance(
            coverage.mics, tuple
        ):
            raise ValueError("MIC_SUPPORT requires MicCoverage with a MIC tuple")
        if coverage.scope not in ("market", "inventory"):
            raise ValueError("Unknown MIC coverage scope")
        if any(not mic_is_wellformed(mic) for mic in coverage.mics):
            raise ValueError("Coverage MIC must be canonical")
        if len(set(coverage.mics)) != len(coverage.mics):
            raise ValueError("Coverage MICs must be unique")

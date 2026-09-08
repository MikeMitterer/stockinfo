"""Profilabhängiger Katalog: erst vollständig prüfen, dann veröffentlichen."""

from collections import defaultdict

from stockinfo_plugin.exchanges import validate_exchanges

from app.exchanges import EXCHANGES, ExchangeDef
from app.sources_config import ROLES

_CORE = dict(EXCHANGES)
_CONFIG = None
_DECLARATIONS: dict[str, object] = {}
_ORIGINS: dict[str, list[str]] = {}
_PROBLEMS: dict[str, str] = {}
_SPECS: dict[str, object] = {}


def reset_catalog() -> None:
    """Entfernte Quellen dürfen keine Deklarationen hinterlassen."""
    global _CONFIG
    _CONFIG = None
    _DECLARATIONS.clear()
    _ORIGINS.clear()
    _PROBLEMS.clear()
    _SPECS.clear()
    EXCHANGES.clear()
    EXCHANGES.update(_CORE)


def prepare_catalog(specs: dict, config) -> dict[str, str]:
    """Validiert alle konfigurierten Klassen vor dem ersten Quellenbau."""
    global _CONFIG
    if _CONFIG is config:
        return _PROBLEMS
    reset_catalog()
    candidates = {}
    for role in ROLES:
        for name in config.chain(role):
            spec = specs.get(name)
            if spec is not None and role in spec.roles and spec.declaration is not None:
                candidates[name] = spec
    for name, spec in candidates.items():
        try:
            declaration = spec.exchange_declaration()
            validate_exchanges(declaration, spec.roles)
            _DECLARATIONS[name] = declaration
            _SPECS[name] = spec
        except Exception as error:  # noqa: BLE001 — fremde Klassenmetadaten
            _PROBLEMS[name] = f"Invalid exchange declaration: {error}"

    # Jeder Konflikt entfernt alle beteiligten Quellen, nie einen Ladegewinner.
    definitions = defaultdict(list)
    for name, declaration in _DECLARATIONS.items():
        for exchange in getattr(declaration, "EXCHANGES", ()):
            definitions[exchange.mic].append((name, exchange))
    aliases = {value.alias: mic for mic, value in _CORE.items() if value.alias}
    for mic, entries in definitions.items():
        core = _CORE.get(mic)
        conflict = aliases.get(mic, mic) != mic
        conflict |= len({value for _, value in entries}) > 1
        if core:
            conflict |= any(
                (value.name, value.region, value.currency)
                != (core.name, core.region, core.currency)
                for _, value in entries
            )
        if conflict:
            for name, _ in entries:
                _PROBLEMS[name] = f"Conflicting exchange declaration: {mic}"

    # Wenn eine Quelle entfällt, können Referenzen auf ihre MICs ungültig werden.
    while True:
        remaining = {
            mic
            for mic, entries in definitions.items()
            if any(name not in _PROBLEMS for name, _ in entries)
        } | set(_CORE)
        rejected = {
            name
            for name, declaration in _DECLARATIONS.items()
            if name not in _PROBLEMS
            and any(
                mic not in remaining
                for coverage in getattr(declaration, "MIC_SUPPORT", {}).values()
                for mic in coverage.mics
            )
        }
        if not rejected:
            break
        for name in rejected:
            _PROBLEMS[name] = "MIC_SUPPORT references an unknown exchange"

    for mic, entries in definitions.items():
        accepted = [(name, value) for name, value in entries if name not in _PROBLEMS]
        if not accepted:
            continue
        _ORIGINS[mic] = sorted(name for name, _ in accepted)
        if mic not in _CORE:
            value = accepted[0][1]
            EXCHANGES[mic] = ExchangeDef(mic, value.name, value.region, value.currency)
    _CONFIG = config
    return _PROBLEMS


def catalog_annotations(chains: list) -> tuple[dict, list]:
    """Deklaration und heutige Betriebsfähigkeit, ohne Handles-Scheinanfragen."""
    annotations = {
        mic: {
            "declared_by": _ORIGINS.get(mic, []),
            "provenance": {"kind": "core"}
            if mic in _CORE
            else {"kind": "plugin", "id": _ORIGINS[mic][0]},
            "support": [],
        }
        for mic in EXCHANGES
    }
    # Einmal je Quelle lesen, damit Rollen denselben Dateistand zeigen.
    current = {}
    for name, spec in _SPECS.items():
        if name in _PROBLEMS:
            continue
        try:
            declaration = spec.exchange_declaration(_CONFIG.config_for(name))
            validate_exchanges(declaration, spec.roles)
            if any(mic not in EXCHANGES for coverage in declaration.MIC_SUPPORT.values() for mic in coverage.mics):
                raise ValueError("Unknown exchange in current coverage")
            current[name] = declaration.MIC_SUPPORT
        except Exception:  # noqa: BLE001 — fremde Selbstauskunft, keine erfundene Abdeckung
            current[name] = None
    unspecified = []
    for entry in chains:
        if entry.role == "fx" or not entry.known or not entry.role_ok:
            continue
        declaration = _DECLARATIONS.get(entry.name)
        if declaration is None or entry.name in _PROBLEMS:
            continue
        coverage = (current.get(entry.name) or {}).get(entry.role)
        if coverage is None:
            unspecified.append(
                {"source": entry.name, "role": entry.role, "usable": entry.usable and current.get(entry.name) is not None}
            )
            continue
        for mic in coverage.mics:
            annotations[mic]["support"].append(
                {
                    "source": entry.name,
                    "role": entry.role,
                    "scope": coverage.scope,
                    "usable": entry.usable,
                }
            )
    return annotations, unspecified

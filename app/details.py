"""Feldkatalog, Validierung und die einzige Merge-Regel für Detailwerte."""

import math
import re
from collections.abc import Iterable

from stockinfo_plugin import Unit
from stockinfo_plugin.types import convert

from app.detail_models import DetailDefinition, DetailInput, DetailScope, DetailValue

# Der geschlossene Kompatibilitätskatalog legt Zieleinheiten und Grenzen fest.
# Welche Felder bei einem Instrument gelten, deklarieren ausschließlich Quellen.
CANONICAL = {
    'ter': ('number', 'percent', 0, 5),
    'volatility': ('number', 'percent', 0, 500),
    'fund_size': ('number', 'absolute', 0, 2_000_000),
    'accumulating': ('boolean', None, None, None),
    'provider': ('text', None, None, None),
    'replication': ('text', None, None, None),
    'fund_domicile': ('text', None, None, None),
    'fund_currency': ('text', None, None, None),
}


def definitions_for(source: object) -> list[DetailDefinition]:
    """Normalisiert und validiert die Deklarationen eines Plugins beim Laden."""
    result = []
    names = set()
    for spec in getattr(source, 'FIELDS', ()):
        if spec.name == 'name':
            # Der Core-Name bleibt T-62; keine zweite editierbare Identität.
            continue
        if not re.fullmatch(r'[a-z][a-z0-9_]*', spec.name):
            raise ValueError(f'Ungültiger lokaler Feldname: {spec.name}')
        if spec.name in names:
            raise ValueError(f'Doppeltes Feld: {spec.name}')
        names.add(spec.name)
        kind = 'boolean' if spec.kind == 'bool' else spec.kind
        unit = spec.unit.value if spec.unit else None
        minimum, maximum = spec.plausible or (None, None)
        name = spec.name if spec.name in CANONICAL else f'{source.name}.{spec.name}'
        if spec.name in CANONICAL:
            expected_kind, expected_unit, minimum, maximum = CANONICAL[spec.name]
            if kind != expected_kind:
                raise ValueError(f'Unverträglicher Typ für {spec.name}')
            if unit != expected_unit and (
                unit is None or expected_unit is None
                or convert(1.0, spec.unit, Unit(expected_unit)) is None
            ):
                raise ValueError(f'Unverträgliche Einheit für {spec.name}')
            unit = expected_unit
        elif not spec.label_en.strip():
            raise ValueError(f'Englische Beschriftung fehlt: {name}')
        types = spec.instrument_types
        supported = getattr(source, 'SUPPORTED_TYPES', frozenset())
        if types is not None and not types.issubset(supported):
            raise ValueError(f'Feld {name} deklariert nicht unterstützte Gattungen')
        result.append(DetailDefinition(
            name=name, kind=kind, unit=unit, minimum=minimum, maximum=maximum,
            label_en=spec.label_en or spec.name, label_de=spec.label_de,
            overridable=spec.overridable, sources=[source.name],
            currency_required=unit == 'absolute',
            scopes=[DetailScope(source=source.name,
                instrument_types=sorted(supported if types is None else types),
                identity_kinds=sorted(getattr(source, 'SUPPORTED_KINDS', ())))],
        ))
    return result


def merge_definitions(groups: Iterable[list[DetailDefinition]]) -> list[DetailDefinition]:
    """Führt Quellen in Vorrangfolge zusammen; Konflikte bleiben Fehler."""
    merged: dict[str, DetailDefinition] = {}
    for definitions in groups:
        for definition in definitions:
            previous = merged.get(definition.name)
            if previous is None:
                merged[definition.name] = definition.model_copy(deep=True)
                continue
            keys = ('kind', 'unit', 'overridable', 'currency_required')
            if any(getattr(previous, key) != getattr(definition, key) for key in keys):
                raise ValueError(f'Widersprüchliche Deklaration: {definition.name}')
            if definition.name not in CANONICAL and (
                previous.label_en != definition.label_en or previous.label_de != definition.label_de
            ):
                raise ValueError(f'Widersprüchliche Bedeutung: {definition.name}')
            for scope in definition.scopes:
                if scope not in previous.scopes:
                    previous.scopes.append(scope)
            for source in definition.sources:
                if source not in previous.sources:
                    previous.sources.append(source)
    return list(merged.values())


def validate_input(definition: DetailDefinition, entry: DetailInput) -> DetailInput:
    """Prüft manuelle Werte und normalisierte Quellenwerte ohne Typkoercion."""
    value = entry.value
    if value is None:
        return DetailInput(value=None)
    if definition.kind == 'number':
        try:
            finite = type(value) in (int, float) and math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite:
            raise ValueError(f'{definition.name}: endliche Zahl erforderlich')
        if definition.minimum is not None and value < definition.minimum:
            raise ValueError(f'{definition.name}: Wert unter Minimum')
        if definition.maximum is not None and value > definition.maximum:
            raise ValueError(f'{definition.name}: Wert über Maximum')
    elif definition.kind == 'boolean':
        if type(value) is not bool:
            raise ValueError(f'{definition.name}: Wahrheitswert erforderlich')
    elif not isinstance(value, str) or not value.strip() or len(value) > 1000:
        raise ValueError(f'{definition.name}: nichtleerer Text erforderlich')
    if definition.name == 'fund_currency' and not re.fullmatch('[A-Z]{3}', str(value)):
        raise ValueError('fund_currency: dreistelliger Währungscode erforderlich')
    if definition.currency_required and not re.fullmatch('[A-Z]{3}', entry.currency or ''):
        raise ValueError(f'{definition.name}: Währung erforderlich')
    if not definition.currency_required and entry.currency is not None:
        raise ValueError(f'{definition.name}: keine Betragswährung zulässig')
    return entry


def merge_value(provider: dict | None, manual: dict | None, unit: str | None) -> DetailValue:
    """Quellenwert gewinnt; False und 0 sind Werte, keine Lücken."""
    provider = provider or {}
    manual = manual or {}
    has_provider = provider.get('value') is not None
    has_manual = manual.get('value') is not None
    effective = provider if has_provider else manual
    return DetailValue(
        value=effective.get('value'), currency=effective.get('currency'), unit=unit,
        origin='provider' if has_provider else 'manual' if has_manual else None,
        source=provider.get('source') if has_provider else None,
        as_of=effective.get('as_of'), shadowed=has_provider and has_manual,
        manual_value=manual.get('value'), manual_currency=manual.get('currency'),
    )

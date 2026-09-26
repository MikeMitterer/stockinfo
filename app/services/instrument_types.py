"""Asset-Typen aus den Deklarationen der laufenden Quellenkonfiguration."""

import structlog

from app.models import InstrumentTypeSource, InstrumentTypesResponse
from app.plugin_loader import roles_of
from app.sources_config import ROLES, SourcesConfig
from app.sources_registry import ChainEntry, SourceSpec, describe_chain, specs_by_name

logger = structlog.get_logger()


def instrument_type_catalog(config: SourcesConfig) -> InstrumentTypesResponse:
    """Liest deklarierte Typen und Betriebszustand ohne Fachabfragen.

    Args:
        config: Die gecachte Konfiguration der laufenden App.

    Returns:
        Sortierte Typmenge und Deklarationsstatus je ausgewählter Asset-Rolle.
        Betriebsstörungen entfernen keine bekannten Typen aus der Menge.
    """
    specs = specs_by_name()
    sources = [
        _describe_types(entry, specs.get(entry.name))
        for role in ROLES
        if role != "fx"
        for entry in describe_chain(role, config)
    ]
    return InstrumentTypesResponse(
        instrument_types=sorted(
            {kind for source in sources for kind in source.instrument_types}
        ),
        complete=all(
            source.status in {"available", "unavailable"} for source in sources
        ),
        sources=sources,
    )


def _describe_types(entry: ChainEntry, spec: SourceSpec | None) -> InstrumentTypeSource:
    """Ordnet eine laufende Quellenrolle ihrer lesbaren Typdeklaration zu."""
    kinds: list[str] = []
    if spec is None:
        status = "unknown_source"
    elif not entry.role_ok:
        status = "unsupported_role"
    else:
        try:
            kinds = _declared_types(spec, entry.role)
            status = "available" if entry.usable else "unavailable"
        except Exception as error:  # noqa: BLE001 — fremde Klassenmetadaten
            logger.warning(
                "source_types_invalid",
                source=entry.name,
                role=entry.role,
                error=str(error),
            )
            status = "invalid_declaration"
    return InstrumentTypeSource(
        name=entry.name, role=entry.role, instrument_types=kinds, status=status
    )


def _declared_types(spec: SourceSpec, role: str) -> list[str]:
    """Liest nur die Klassen der ausgewählten Rolle; weist ungültige Mengen ab."""
    declarations = [
        declaration
        for declaration in (spec.declaration, *spec.additional_declarations)
        if declaration is not None and role in roles_of(declaration)
    ]
    if not declarations:
        raise ValueError("No declaration for this role")
    kinds: set[str] = set()
    for declaration in declarations:
        declared = declaration.SUPPORTED_TYPES
        if not isinstance(declared, (set, frozenset)) or any(
            not isinstance(kind, str) or not kind or kind.strip() != kind
            for kind in declared
        ):
            raise ValueError("SUPPORTED_TYPES must contain non-empty type identifiers")
        kinds.update(declared)
    return sorted(kinds)

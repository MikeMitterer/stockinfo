"""Offene Felddefinitionen und Werte für REST und Persistenz."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictInt, StrictStr

Scalar = StrictBool | StrictInt | StrictFloat | StrictStr


class DetailScope(BaseModel):
    """Die deklarierte Anwendbarkeit einer Quelle, unabhängig von ihrer Gesundheit."""

    source: str
    instrument_types: list[str]
    identity_kinds: list[str]


class DetailDefinition(BaseModel):
    """Kanonische Feldbeschreibung für generische Konsumenten."""

    name: str
    kind: Literal['number', 'text', 'boolean']
    unit: str | None = None
    label_en: str
    label_de: str = ''
    overridable: bool = True
    sources: list[str] = Field(default_factory=list)
    scopes: list[DetailScope] = Field(default_factory=list)
    minimum: float | None = None
    maximum: float | None = None
    currency_required: bool = False

    def applies(self, instrument_type: str, identity_kind: str) -> bool:
        """Mindestens eine Quelle deklariert diese Kombination."""
        return any(
            instrument_type in scope.instrument_types and identity_kind in scope.identity_kinds
            for scope in self.scopes
        )


class DetailValue(BaseModel):
    """Wirksamer Wert samt Herkunft und separat erhaltener manueller Eingabe."""

    value: Scalar | None = None
    unit: str | None = None
    currency: str | None = None
    origin: Literal['provider', 'manual'] | None = None
    source: str | None = None
    as_of: str | None = None
    shadowed: bool = False
    manual_value: Scalar | None = None
    manual_currency: str | None = None


class DetailInput(BaseModel):
    """Eine manuelle Eingabe; null entfernt nur diesen manuellen Wert."""

    model_config = ConfigDict(extra='forbid')
    value: Scalar | None
    currency: str | None = None

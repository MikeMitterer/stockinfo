"""Kennzahlen, die StockInfo selbst berechnet, als Detailfeld-Deklaration.

Die Volatilität entsteht aus den gespeicherten Tageskursen, für jedes
Instrument mit Kursen (`quote_cache._save_fresh_with_volatility`). Ein
Detailwert erscheint aber nur, wenn eine Deklaration ihn für Gattung und
Identitätsart freigibt. Diese Deklaration gehört zur Quelle der Berechnung,
nicht zu einem Plugin. `sources_registry.detail_definitions` hängt sie nach
den Plugins an; bei mehreren Werten gilt deshalb zuerst der Plugin-Wert
(justETF bei ETFs), sonst der berechnete.
"""

from stockinfo_plugin import FieldSpec, Unit

from app.providers.base import INSTRUMENT_TYPES

CALCULATED_SOURCE = "calculated"
"""Quellname gespeicherter berechneter Werte; muss zur Deklaration passen."""


class CalculatedMetrics:
    """Deklariert die selbst berechneten Kennzahlen im Detailkatalog."""

    name = CALCULATED_SOURCE
    SUPPORTED_TYPES = frozenset(INSTRUMENT_TYPES)
    SUPPORTED_KINDS = frozenset({"listed", "pair"})
    FIELDS = (
        FieldSpec(
            "volatility",
            kind="number",
            unit=Unit.PERCENT,
            label_en="Volatility (1y)",
            label_de="Volatilität (1 Jahr)",
        ),
    )

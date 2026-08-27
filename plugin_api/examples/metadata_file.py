"""Beispiel-Plugin: Kennzahlen aus einer gepflegten Tabelle.

Zeigt die zwei Punkte, an denen Metadaten-Quellen typischerweise auseinander-
laufen:

* **Variable Feldmenge** — nicht jede Zeile führt jede Kennzahl. Was fehlt,
  wird nicht geliefert, statt als ``None`` den gespeicherten Stand zu ersetzen.
* **Eigene Einheit** — die Kostenquote steht hier in **Basispunkten**, weil
  Datenblätter sie oft so führen (``19`` statt ``0.19``). Die Quelle deklariert
  das, die App rechnet um. Ohne Deklaration wäre der Wert um den Faktor 100
  daneben — genau der Fehler, der bei zwei echten Quellen gemessen wurde.

Format (Semikolon, Kopfzeile erforderlich, leere Zellen erlaubt)::

    isin;ter_bps;provider;fund_domicile
    CA78012H5675;6;BlackRock Canada;Canada
    CA9861913023;;Yorbeau;
"""

import csv
from pathlib import Path
from types import MappingProxyType
from typing import Any

from stockinfo_plugin import (
    FieldSpec,
    MetadataSource,
    Reading,
    ResolveRequest,
    Unit,
)


class MetadataFileSource(MetadataSource):
    """Liest ETF-Kennzahlen aus einer CSV-Datei."""

    name = "metadata-file"
    cost = "free"

    FIELDS = (
        FieldSpec(
            "ter",
            kind="number",
            unit=Unit.BASIS_POINTS,
            plausible=(0.5, 500.0),
            label_en="Total expense ratio",
            label_de="Gesamtkostenquote",
        ),
        FieldSpec("provider", kind="text", label_en="Fund provider", label_de="Anbieter"),
        FieldSpec(
            "fund_domicile", kind="text", label_en="Fund domicile", label_de="Fondsdomizil"
        ),
    )

    # Spalte in der Datei → Feldname im Vertrag. Die Namen unterscheiden sich
    # bewusst: `ter_bps` sagt in der Datei, in welcher Einheit die Zahl steht.
    #
    # `MappingProxyType` und kein rohes Dict: Ein Dict an der Klasse gehört
    # allen Instanzen gemeinsam, und ein einziges `self._COLUMNS[...] = ...`
    # irgendwo änderte still das Verhalten jeder anderen. Dass hier niemand
    # schreibt, ist heute wahr und morgen eine Annahme —
    # `SourceContract.test_kein_veraenderlicher_zustand_an_der_klasse` hat
    # genau diese Zeile gefunden, und sie hatte recht.
    _COLUMNS = MappingProxyType(
        {"ter_bps": "ter", "provider": "provider", "fund_domicile": "fund_domicile"}
    )

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """
        Args:
            config: ``path`` — Pfad zur CSV-Datei. ``prefixes`` — ISIN-Präfixe,
                für die diese Quelle zuständig ist.
        """
        super().__init__(config)
        self._path = Path(self._config.get("path", "/data/manual-metadata.csv"))
        self._prefixes = tuple(self._config.get("prefixes", ("CA",)))

    def is_configured(self) -> bool:
        return self._path.is_file()

    def handles(self, request: ResolveRequest) -> bool:
        return bool(request.isin) and request.isin.upper().startswith(self._prefixes)

    def fetch(self, request: ResolveRequest) -> list[Reading] | None:
        """Liest die Zeile zur ISIN und gibt die gefüllten Felder zurück."""
        if not self.handles(request):
            return []
        try:
            row = self._lookup(request.isin.upper())
        except OSError:
            # Konnte nicht nachsehen — der gespeicherte Stand bleibt geschützt.
            return None
        if row is None:
            return []

        readings: list[Reading] = []
        for column, field in self._COLUMNS.items():
            raw = (row.get(column) or "").strip()
            if not raw:
                continue  # leere Zelle heißt „nicht geführt", nicht „ist leer"
            spec = self.declared(field)
            value: float | str = raw
            if spec is not None and spec.kind == "number":
                try:
                    value = float(raw)
                except ValueError:
                    continue  # unbrauchbare Zahl lieber weglassen als raten
            readings.append(
                Reading(
                    field=field,
                    value=value,
                    unit=spec.unit if spec else None,
                    source=self.name,
                )
            )
        return readings

    def _lookup(self, isin: str) -> dict[str, str] | None:
        """Sucht die Zeile zur ISIN. ``None``, wenn es keine gibt."""
        with self._path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle, delimiter=";"):
                if (row.get("isin") or "").strip().upper() == isin:
                    return row
        return None


SOURCES = [MetadataFileSource]

"""Beispiel-Plugin: löst ISINs über eine von Hand gepflegte Tabelle auf.

Der Anlass ist ein gemessener Fall — für kanadische Papiere liefert weder
OpenFIGI ein Listing an der bevorzugten Börse noch Yahoos ISIN-Suche einen
Treffer. Wo keine automatische Quelle etwas weiß, trägt der Nutzer drei Werte
von Hand ein, statt auf eine Quelle zu warten, die es vielleicht nie gibt.

Dasselbe Prinzip wie bei den manuell gepflegten Kennzahlen, eine Ebene höher:
*Wo die Quelle nichts hat, springt der Mensch ein.*

Format der Datei (Semikolon, Kopfzeile erforderlich)::

    isin;ticker;mic;name;type
    CA78012H5675;RY;XTSE;Royal Bank of Canada;stock

``type`` ist seit T-37 dabei und **optional** — Tabellen ohne die Spalte
bleiben gültig. Sie fehlte, und der UI-Lauf hat gezeigt, was das kostet: Ohne
Gattung hält die App jedes Papier für eine Aktie und fragt die
Metadatenquelle gar nicht erst. Mit T-38 wird die Angabe zur Pflicht.
"""

import csv
from pathlib import Path
from typing import Any

from stockinfo_plugin import (
    ListedIdentity,
    NotFound,
    NotResponsible,
    Resolution,
    Resolved,
    ResolveRequest,
    Resolver,
    Unavailable,
)


class CanadaFileResolver(Resolver):
    """Liest ISIN → Ticker + MIC aus einer CSV-Datei."""

    name = "canada-file"
    cost = "free"
    api_version = 2
    SUPPORTED_KINDS = frozenset({"listed"})
    SUPPORTED_TYPES = frozenset({"stock", "etf", "etc", "fund", "bond"})

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """
        Args:
            config: ``path`` — Pfad zur CSV-Datei. ``prefixes`` — Liste der
                ISIN-Länderpräfixe, für die diese Quelle zuständig ist.
        """
        super().__init__(config)
        self._path = Path(self._config.get("path", "/data/manual-isins.csv"))
        self._prefixes = tuple(self._config.get("prefixes", ("CA",)))

    def configuration_problem(self) -> str:
        """Ohne Datei gibt es nichts nachzuschlagen — und der Pfad gehört dazu.

        `is_configured()` leitet sich daraus ab. Den Pfad zu nennen ist der
        ganze Punkt: „nicht konfiguriert" schickt den Betreiber auf die Suche,
        der Pfad beendet sie — meistens ist ein Mount weggefallen oder die
        Datei liegt eine Ebene daneben.
        """
        if self._path.is_file():
            return ""
        return f"Tabelle {self._path} nicht gefunden — Pfad in der Konfiguration prüfen"

    def handles(self, request: ResolveRequest) -> bool:
        """Zuständig für die konfigurierten Länderpräfixe."""
        return bool(request.isin) and request.isin.upper().startswith(self._prefixes)

    def resolve(self, request: ResolveRequest) -> Resolution:
        """Schlägt die ISIN in der Tabelle nach."""
        if not self.handles(request):
            return NotResponsible(f"nur {'/'.join(self._prefixes)}-ISINs")
        try:
            entry = self._lookup(request.isin.upper())
        except OSError as exc:
            # Die Datei kann verschwinden, während die App läuft — das ist
            # „konnte nicht nachsehen", nicht „gibt es nicht".
            return Unavailable(f"{self._path} nicht lesbar: {exc}")
        if entry is None:
            return NotFound()
        # **Die Gattung kommt aus der Tabelle, seit T-37.** Sie fehlte, und
        # der UI-Lauf hat gezeigt, was das kostet: Ohne `type` hält die App das
        # Papier für eine Aktie und fragt die Metadatenquelle **gar nicht
        # erst** — TER und Anbieter bleiben dauerhaft leer, ohne Meldung.
        #
        # **Die Spalte war optional, und diese Zeile hat vorhergesagt, wann
        # sie es nicht mehr ist.** Mit T-38 sind `name` und `instrument_type`
        # Pflichtfelder. Eine Tabellenzeile ohne sie ist damit kein Treffer
        # mehr, sondern `NotFound`: Die Datei kennt die ISIN, aber nicht
        # genug, um sie zu beantworten.
        #
        # Für einen Plugin-Autor ist **das** der lehrreiche Teil dieses
        # Beispiels: Wer ein Pflichtfeld nicht füllen kann, antwortet ehrlich
        # nichts, statt eine halbe Zeile zu liefern. Die nächste Quelle in der
        # Kette darf es besser wissen.
        name = (entry.get("name") or "").strip()
        instrument_type = (entry.get("type") or "").strip()
        if not name or not instrument_type:
            return NotFound()

        return Resolved(
            identity=ListedIdentity(
                ticker=entry["ticker"],
                mic=entry["mic"],
                isin=request.isin.upper(),
            ),
            name=name,
            instrument_type=instrument_type,
        )

    def _lookup(self, isin: str) -> dict[str, str] | None:
        """Sucht die Zeile zur ISIN. Gibt ``None`` zurück, wenn es keine gibt."""
        with self._path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle, delimiter=";"):
                if (row.get("isin") or "").strip().upper() == isin:
                    return {key: (value or "").strip() for key, value in row.items()}
        return None


SOURCES = [CanadaFileResolver]
"""Was die Registry lädt, wenn diese Datei als Einzeldatei-Plugin liegt."""

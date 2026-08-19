"""Der ganze Vertrag, geprüft an einem echten Plugin — sechs gesetzte Zeilen.

Das ist der Punkt der Übung: Der Autor nennt drei Anfragen, den Rest prüft
`ResolverContract`. Was hier grün ist, läuft auch in einer App, die dieses
Papier nie gesehen hat.
"""

from pathlib import Path

import pytest

from stockinfo_plugin import ResolveRequest
from stockinfo_plugin.testing import ResolverContract

from examples.canada_file import CanadaFileResolver

FIXTURE = Path(__file__).parent / "fixtures" / "manual-isins.csv"


class TestCanadaFile(ResolverContract):
    """Der komplette Vertrag — geerbt, nicht geschrieben."""

    responsible = ResolveRequest(isin="CA78012H5675")
    not_responsible = ResolveRequest(isin="IE00B4L5Y983")
    unknown = ResolveRequest(isin="CA00000000000")

    def make_source(self) -> CanadaFileResolver:
        return CanadaFileResolver({"path": str(FIXTURE)})


# ─── Was über den Vertrag hinausgeht, prüft der Autor selbst ──────────────────


def test_liefert_ticker_und_boerse_getrennt() -> None:
    """Kein Yahoo-Suffix im Ticker — das Zusammensetzen ist Sache der Kurs-Quelle."""
    resolver = CanadaFileResolver({"path": str(FIXTURE)})

    treffer = resolver.resolve(ResolveRequest(isin="CA78012H5675"))

    assert treffer.ticker == "RY"
    assert treffer.mic == "XTSE"
    assert treffer.name == "Royal Bank of Canada"


def test_fehlende_datei_ist_nicht_konfiguriert() -> None:
    """Eine Quelle ohne Datei kommt gar nicht erst in die Kette."""
    assert CanadaFileResolver({"path": "/gibt/es/nicht.csv"}).is_configured() is False


def test_verschwundene_datei_meldet_unavailable_statt_notfound() -> None:
    """Der Unterschied entscheidet über 502 gegen 404.

    Die Datei kann verschwinden, während die App läuft — ein gemounteter
    Ordner, der wegfällt. „Konnte nicht nachsehen" ist dann die ehrliche
    Aussage, nicht „gibt es nicht".
    """
    resolver = CanadaFileResolver({"path": "/gibt/es/nicht.csv"})

    antwort = resolver.resolve(ResolveRequest(isin="CA78012H5675"))

    assert type(antwort).__name__ == "Unavailable"


@pytest.mark.parametrize("prefixes", [("JP",), ("US", "CA")])
def test_zustaendigkeit_ist_konfigurierbar(prefixes: tuple[str, ...]) -> None:
    """Dasselbe Plugin trägt jeden Markt — die Tabelle entscheidet, nicht der Code."""
    resolver = CanadaFileResolver({"path": str(FIXTURE), "prefixes": list(prefixes)})

    assert resolver.handles(ResolveRequest(isin=f"{prefixes[0]}0000000000"))

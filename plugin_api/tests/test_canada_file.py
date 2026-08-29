"""Der ganze Vertrag, geprüft an einem echten Plugin — sechs gesetzte Zeilen.

Das ist der Punkt der Übung: Der Autor nennt drei Anfragen, den Rest prüft
`ResolverContract`. Was hier grün ist, läuft auch in einer App, die dieses
Papier nie gesehen hat.
"""

from pathlib import Path

import pytest

from stockinfo_plugin import ListedIdentity, NotFound, ResolveRequest
from stockinfo_plugin.testing import ResolverContract

from examples.canada_file import CanadaFileResolver

FIXTURE = Path(__file__).parent / "fixtures" / "manual-isins.csv"


class TestCanadaFile(ResolverContract):
    """Der komplette Vertrag — geerbt, nicht geschrieben."""

    responsible = ResolveRequest(isin="CA78012H5675")
    not_responsible = ResolveRequest(isin="IE00B4L5Y983")
    # Barrick Gold — eine **gültige** kanadische ISIN, die in der Tabelle nicht
    # steht. Hier stand bis T-27a `CA00000000000`: dreizehn Zeichen, falsche
    # Prüfziffer, also gar keine ISIN. Der Test maß damit die Formprüfung des
    # Plugins statt seines Verhaltens bei einem echten, aber nicht geführten
    # Papier — zwei verschiedene Fälle, und nur der zweite war gemeint.
    # Gefunden hat das nicht ein Mensch, sondern die neue Vertragsregel
    # `test_die_eigenen_pruefdaten_sind_gueltige_isins`.
    unknown = ResolveRequest(isin="CA0679011084")

    def make_source(self) -> CanadaFileResolver:
        return CanadaFileResolver({"path": str(FIXTURE)})


# ─── Was über den Vertrag hinausgeht, prüft der Autor selbst ──────────────────


def test_liefert_ticker_und_boerse_getrennt() -> None:
    """Kein Yahoo-Suffix im Ticker — das Zusammensetzen ist Sache der Kurs-Quelle."""
    resolver = CanadaFileResolver({"path": str(FIXTURE)})

    hit = resolver.resolve(ResolveRequest(isin="CA78012H5675"))

    assert hit.identity == ListedIdentity(
        ticker="RY", mic="XTSE", isin="CA78012H5675"
    )
    assert hit.name == "Royal Bank of Canada"


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

    answer = resolver.resolve(ResolveRequest(isin="CA78012H5675"))

    assert type(answer).__name__ == "Unavailable"


@pytest.mark.parametrize("prefixes", [("JP",), ("US", "CA")])
def test_zustaendigkeit_ist_konfigurierbar(prefixes: tuple[str, ...]) -> None:
    """Dasselbe Plugin trägt jeden Markt — die Tabelle entscheidet, nicht der Code."""
    resolver = CanadaFileResolver({"path": str(FIXTURE), "prefixes": list(prefixes)})

    assert resolver.handles(ResolveRequest(isin=f"{prefixes[0]}0000000000"))


def test_die_gattung_kommt_aus_der_tabelle() -> None:
    """**Die Spalte, deren Fehlen T-35 im Browser sichtbar gemacht hat.**

    Ohne `instrument_type` hält die App das Papier für eine Aktie und fragt
    die Metadatenquelle **gar nicht erst** — TER, Anbieter und Domizil bleiben
    dauerhaft leer, ohne Fehlermeldung und ohne Protokolleintrag. Genau dieser
    Weg lief monatelang so, bis der erste Browserlauf ihn zeigte.
    """
    resolver = CanadaFileResolver({"path": str(FIXTURE)})

    hit = resolver.resolve(ResolveRequest(isin="CA78012H5675"))

    assert hit.instrument_type == "stock"


def test_eine_tabelle_ohne_gattungsspalte_loest_nicht_mehr_auf(tmp_path: Path) -> None:
    """**Diese Zusage hat sich mit T-38 umgedreht — und das gehört hierher.**

    Bis T-38 stand hier das Gegenteil: *„Die Spalte ist additiv — alte Dateien
    dürfen nicht kaputtgehen."* Das Argument war gut und ist es noch: Ein
    Betreiber pflegt seine Tabelle von Hand, und ein Format, das nach einem
    Update eine neue Pflichtspalte verlangt, kostet ihn seine Quelle, während
    er nichts geändert hat.

    **Es hat trotzdem verloren, und zwar gegen eine Messung.** Im UI-Lauf vom
    2026-08-28 kam genau so eine Zeile durch: Identität vollständig, Gattung
    leer. Die App hat sie angenommen, gespeichert, angezeigt — und die
    Metadatenkaskade nie angeworfen, weil die Gattung fehlte. Ohne Meldung,
    ohne Protokolleintrag, monatelang. Der Betreiber hat seine Quelle also
    auch vorher verloren, nur ohne es zu erfahren.

    Der Unterschied ist damit nicht „streng gegen tolerant", sondern
    **„sichtbar gegen still"**. Die alte Zeile fällt jetzt als `NotFound` auf,
    und der Betreiber kann eine Spalte ergänzen.

    Geprüft werden weiterhin **beide** Formen der Abwesenheit: die Spalte fehlt
    ganz, und sie ist da, aber leer.
    """
    legacy_file = tmp_path / "ohne-spalte.csv"
    legacy_file.write_text(
        "isin;ticker;mic;name\nCA78012H5675;RY;XTSE;Royal Bank of Canada\n",
        encoding="utf-8",
    )

    without_column = CanadaFileResolver({"path": str(legacy_file)}).resolve(
        ResolveRequest(isin="CA78012H5675")
    )
    assert isinstance(without_column, NotFound), (
        "eine Zeile ohne Gattung ist kein Treffer mehr — sie war es vorher, "
        f"und genau das war der Fehler. Bekommen: {without_column}"
    )

    empty_cell = CanadaFileResolver({"path": str(FIXTURE)}).resolve(
        ResolveRequest(isin="CA9861913023")
    )
    assert isinstance(empty_cell, NotFound), (
        "eine leere Zelle ist keine Gattung — und seit T-38 auch kein Treffer"
    )

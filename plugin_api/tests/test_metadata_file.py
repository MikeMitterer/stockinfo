"""Vertrag und Eigenheiten einer Metadaten-Quelle."""

from pathlib import Path

from stockinfo_plugin import ResolveRequest, Unit, convert
from stockinfo_plugin.testing import MetadataContract

from examples.metadata_file import MetadataFileSource

FIXTURE = Path(__file__).parent / "fixtures" / "manual-metadata.csv"


class TestMetadataFile(MetadataContract):
    """Der komplette Vertrag — zwei gesetzte Zeilen."""

    responsible = ResolveRequest(isin="CA78012H5675")
    not_responsible = ResolveRequest(isin="IE00B4L5Y983")

    def make_source(self) -> MetadataFileSource:
        return MetadataFileSource({"path": str(FIXTURE)})


# ─── Was über den Vertrag hinausgeht ──────────────────────────────────────────


def _readings(isin: str) -> dict[str, object]:
    """Liest die Felder zu einer ISIN als Zuordnung Feld → Wert."""
    source = MetadataFileSource({"path": str(FIXTURE)})
    return {r.field: r.value for r in source.fetch(ResolveRequest(isin=isin)) or []}


def test_leere_zellen_werden_nicht_geliefert() -> None:
    """Nicht geführt ist etwas anderes als leer.

    Die zweite Zeile der Testdatei hat weder TER noch Domizil. Käme beides als
    ``None`` zurück, dürfte das Repository einen gepflegten Stand damit
    überschreiben — genau der Fehler, gegen den `metadata_complete` gebaut ist.
    """
    readings = _readings("CA9861913023")

    assert "provider" in readings
    assert "ter" not in readings
    assert "fund_domicile" not in readings


def test_volle_zeile_liefert_alle_drei_felder() -> None:
    readings = _readings("CA78012H5675")

    assert set(readings) == {"ter", "provider", "fund_domicile"}
    assert readings["provider"] == "BlackRock Asset Management Canada"


def test_basispunkte_werden_zu_prozent() -> None:
    """Der eigentliche Zweck der Einheiten-Angabe.

    Die Quelle führt 6 Basispunkte. Ohne Umrechnung stünde in der Tabelle ein
    TER von 6 % statt 0,06 % — Faktor 100, und niemand sieht es der Zahl an.
    """
    raw = _readings("CA78012H5675")["ter"]

    assert raw == 6.0
    assert convert(raw, Unit.BASIS_POINTS, Unit.PERCENT) == 0.06


def test_unplausible_werte_gelten_als_kein_wert() -> None:
    """Eine stille Null tarnt sich als gültige Angabe.

    Gemessen an einem echten Fonds: Die Quelle meldete 0,0000 als Kostenquote,
    real sind es rund 0,06 %. Der erklärte Wertebereich fängt das ab.
    """
    spec = MetadataFileSource().declared("ter")

    assert spec.is_plausible(6.0) is True
    assert spec.is_plausible(0.0) is False       # stille Null
    assert spec.is_plausible(9999.0) is False    # vermutlich falsche Einheit


def test_beschriftungen_liegen_zweisprachig_vor() -> None:
    """Ein Feld ohne Beschriftung erscheint als roher Feldname."""
    spec = MetadataFileSource().declared("fund_domicile")

    assert spec.label_en == "Fund domicile"
    assert spec.label_de == "Fondsdomizil"

"""Das justETF-Plugin gegen den **echten** Dienst.

Er fehlte bis Runde 1 — die Kette hatte einen Online-Nachweis für OpenFIGI und
yfinance, aber keinen für justETF. Eine Rolle ohne Online-Fall ist genau die,
bei der zuerst niemand merkt, dass sich die Gegenseite geändert hat.

    pytest tests/test_plugin_justetf_integration.py   # fragt justETF
    pytest -m "not integration"                       # ohne fremde Dienste

**Keine festgenagelten Kennzahlen.** Ein Fondsvolumen ändert sich täglich, eine
Kostenquote gelegentlich. Festgenagelt wird, was sich nicht ändert: dass die
Antwort überhaupt Felder trägt, dass jedes davon **deklariert** ist, und dass
ein absoluter Betrag seine Währung mitbringt. Genau die drei Zusagen hat der
Vertrag an den Doubles gefunden — hier stehen sie gegen die Wirklichkeit.
"""

import pytest

from stockinfo_plugin import ResolveRequest, Unit
from stockinfo_plugin.invariants import currency_problem

from app.plugins.justetf_metadata import JustEtfMetadataPlugin

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def plugin() -> JustEtfMetadataPlugin:
    """Das Plugin mit der echten Anbindung."""
    return JustEtfMetadataPlugin()


def test_ein_bekannter_ucits_fonds_liefert_deklarierte_felder(
    plugin: JustEtfMetadataPlugin,
) -> None:
    """iShares Core MSCI World — der Regelfall.

    Geprüft wird die **Deklaration**, nicht der Wert: Jedes gelieferte Feld
    muss in `FIELDS` stehen. Driftete die Anbindung, käme ein Feld an, das die
    App nicht einordnen kann — und sie zeigte es als rohen Feldnamen an, ohne
    zu wissen, ob es Prozent oder ein Betrag ist.
    """
    readings = plugin.fetch(ResolveRequest(isin="IE00B4L5Y983"))

    assert readings, "justETF kennt diesen Fonds — eine leere Antwort wäre neu"
    for reading in readings:
        assert plugin.declared(reading.field) is not None, (
            f"'{reading.field}' kommt an, ist aber nicht deklariert"
        )


def test_ein_absoluter_betrag_traegt_seine_waehrung(
    plugin: JustEtfMetadataPlugin,
) -> None:
    """Ein Betrag ohne Währung ist bedeutungslos — dieselbe Regel wie beim Kurs.

    Der Vertrag hat das an einem Double gefunden; hier steht es gegen den
    echten Dienst. Liefert justETF eines Tages ein Volumen ohne Fondswährung,
    schlägt dieser Test an, statt eine nackte Zahl in die Datenbank zu lassen.
    """
    readings = plugin.fetch(ResolveRequest(isin="IE00B4L5Y983"))

    absolute = [
        reading
        for reading in readings or []
        if (reading.unit or getattr(plugin.declared(reading.field), "unit", None))
        is Unit.ABSOLUTE
    ]

    assert absolute, "ohne einen absoluten Betrag prüft dieser Test nichts"
    for reading in absolute:
        assert not currency_problem(reading.currency), (
            f"'{reading.field}' = {reading.value!r} ohne brauchbare Währung "
            f"({reading.currency!r})"
        )


def test_ein_us_papier_ist_nicht_zustaendig(plugin: JustEtfMetadataPlugin) -> None:
    """justETF führt europäische Fonds — und sagt das, statt zu raten.

    Die leere Liste ist die Aussage „nicht zuständig"; sie unterscheidet sich
    von ``None`` („zuständig, nichts gefunden"). Der Unterschied entscheidet,
    ob die Kette weiterfragt.
    """
    assert plugin.fetch(ResolveRequest(isin="US0378331005")) == []

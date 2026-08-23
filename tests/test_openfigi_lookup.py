"""Wie OpenFIGI eine Börse adressiert — Wissen des Anbieters (T-21, Teil 2b).

Bis hierher stand es in `ExchangeDef`: Jede Börse der eigenen Tabelle trug zwei
Spalten mit, die **nur** OpenFIGI etwas angehen. Damit hätte jede weitere
Kursquelle ihre eigenen zwei Spalten dazugelegt, und die Börsentabelle wäre zur
Sammelstelle für Anbieter-Eigenheiten geworden.

Die Tabelle beschreibt jetzt nur noch die Börse selbst: Suffix, Name, Region,
Währung.
"""

import pytest

from app.exchanges import COLLECTOR_CODES, EXCHANGES, ExchangeDef, is_real_mic
from app.providers.openfigi_provider import figi_lookup


def test_eine_gewoehnliche_boerse_wird_ueber_ihren_mic_gesucht() -> None:
    """Der Regelfall braucht keinen Eintrag — der MIC ist die Antwort."""
    assert figi_lookup("XETR") == ("micCode", "XETR")


def test_der_sammelcode_us_ist_die_ausnahme() -> None:
    """`US` ist kein MIC, sondern OpenFIGIs Composite für NYSE und NASDAQ.

    Es wird über ein **anderes Feld** gesucht (`exchCode`), und genau diese
    Ausnahme ist der einzige Grund, warum es die Zuordnung überhaupt gibt.
    """
    assert figi_lookup("US") == ("exchCode", "US")


def test_eine_unbekannte_boerse_wird_wie_ein_mic_behandelt() -> None:
    """`XNAS` steht nicht in der eigenen Tabelle und ist trotzdem ein MIC.

    Die Tabelle ist eine Auswahl der Börsen, die StockInfo auflösen kann —
    kein Verzeichnis aller MICs. Eine manuelle Zuordnung darf einen Wert
    setzen, den sie nicht kennt.
    """
    assert figi_lookup("XNAS") == ("micCode", "XNAS")


def test_die_boersentabelle_traegt_kein_anbieterwissen_mehr() -> None:
    """Der eigentliche Punkt dieses Umbaus — festgehalten, damit er hält.

    Ohne diese Zeile wanderte die nächste Anbieter-Eigenheit wieder in
    `ExchangeDef`: Es ist der bequemste Ort, weil dort schon alle Börsen
    stehen.
    """
    fields = set(ExchangeDef.__dataclass_fields__)

    assert fields == {"suffix", "name", "region", "currency"}


def test_der_sammelcode_ist_ausdruecklich_benannt() -> None:
    """`is_real_mic` erkennt ihn jetzt an einer Liste, nicht am Suchverfahren.

    Vorher war das Merkmal indirekt: „wird über `exchCode` gesucht" hieß „ist
    kein echter MIC". Diese Kopplung verschwindet mit den Spalten — und ein
    Sammelcode bleibt einer, auch wenn ihn nie jemand bei OpenFIGI sucht.
    """
    assert "US" in COLLECTOR_CODES
    assert is_real_mic("US") is False


@pytest.mark.parametrize("code", sorted(COLLECTOR_CODES))
def test_jeder_sammelcode_steht_auch_in_der_boersentabelle(code: str) -> None:
    """Sonst wäre die Liste ein toter Buchstabe.

    Ein Sammelcode, den `EXCHANGES` nicht führt, kann nirgends auftauchen —
    dann fehlt entweder die Zeile oder der Eintrag ist übrig geblieben.
    """
    assert code in EXCHANGES

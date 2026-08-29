"""Das yfinance-Plugin gegen den **echten** Anbieter.

Das Gegenstück zu `test_plugin_selection.py`: Dort entscheidet die
Konfiguration zwischen CSV und Anbieter, ohne dass jemand ins Netz greift.
Hier greift jemand ins Netz — und nur das steht hier drin.

    pytest tests/test_plugin_yfinance_integration.py   # fragt Yahoo
    pytest -m "not integration"                        # ohne fremde Dienste

Was ein Integrationstest belegt und kein Double belegen kann: dass die
Symbolbildung noch trifft, dass Yahoo weiterhin Währung und Zeitstempel
liefert, und dass die Übersetzung in `Quote` und `FxRate` trägt.

**Nur Netzfälle.** Der Identitätsfall `EUR→EUR` stand hier bis Runde 2 und
berührte keinen Anbieter — er fiel damit unter `-m "not integration"` heraus,
obwohl er ohne Netz läuft. Derselbe Fehler war kurz zuvor in T-27b korrigiert
worden; er steht jetzt in `test_app_plugins_contract.py`.

**Kein Golden-Kurs.** Ein Kurs ändert sich täglich; ihn festzunageln hieße,
einen Test zu schreiben, der morgen rot ist, ohne dass etwas kaputt wäre.
Festgenagelt wird, was sich **nicht** ändert: Währung und Handelsplatz. Der
Kurs bekommt einen Bereich — er schlägt an, wenn eine Quelle Pence für Pfund
hält, und schweigt bei normaler Bewegung.
"""

from datetime import date, timedelta

import pytest

from stockinfo_plugin import (
    DailyRequest,
    DailySeries,
    FxRate,
    FxRequest,
    ListedIdentity,
    Quote,
    QuoteRequest,
)
from stockinfo_plugin.invariants import days_are_ordered, has_timezone

from app.plugins.yfinance_quotes import YFinancePlugin

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def plugin() -> YFinancePlugin:
    """Das Plugin mit der echten Anbindung."""
    return YFinancePlugin()


def test_ein_kurs_kommt_mit_waehrung_und_zeitpunkt(plugin: YFinancePlugin) -> None:
    """iShares Core MSCI World an Xetra — der Regelfall.

    Geprüft wird die **Währung** als feste Zusage: Sie ist eine Eigenschaft des
    Listings und ändert sich nicht von Tag zu Tag, während der Kurs es tut.
    """
    answer = plugin.fetch_quote(QuoteRequest(ListedIdentity(ticker="EUNL", mic="XETR")))

    assert isinstance(answer, Quote), answer
    assert answer.currency == "EUR"
    assert 1.0 < answer.price < 10_000.0, "Bereich statt Golden Case — ein Kurs bewegt sich"
    assert has_timezone(answer.as_of), (
        "ein Zeitpunkt ohne Zone stürzt beim ersten Vergleich mit TypeError ab"
    )


def test_eine_tagesreihe_ist_aufsteigend_und_traegt_ihre_waehrung(
    plugin: YFinancePlugin,
) -> None:
    """Sortierung und Währung — beides Zusagen des Vertrags, hier am echten Anbieter.

    Die Reihenfolge wird **geprüft und nicht hergestellt**: Sie hier zu
    sortieren hieße, einen Fehler des Anbieters zu verdecken, statt ihn zu
    melden.
    """
    end = date.today()
    answer = plugin.fetch_daily(
        DailyRequest(ListedIdentity(ticker="EUNL", mic="XETR"), start=end - timedelta(days=30), end=end)
    )

    assert isinstance(answer, DailySeries), answer
    assert answer.currency == "EUR"
    assert answer.bars, "eine leere Reihe ist kein Ergebnis"
    assert days_are_ordered([bar.day for bar in answer.bars]), (
        "streng aufsteigend — zwei Einträge für denselben Tag zählt der "
        "Verbraucher doppelt"
    )


def test_ein_wechselkurs(plugin: YFinancePlugin) -> None:
    """EUR/CHF — plausibler Bereich statt festgenagelter Zahl."""
    answer = plugin.fetch_rate(FxRequest(base="EUR", quote="CHF"))

    assert isinstance(answer, FxRate), answer
    assert (answer.base, answer.quote) == ("EUR", "CHF")
    assert 0.5 < answer.rate < 2.0

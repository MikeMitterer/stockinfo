"""Das yfinance-Plugin gegen den **echten** Anbieter.

Das Gegenstück zu `test_plugin_selection.py`: Dort entscheidet die
Konfiguration zwischen CSV und Anbieter, ohne dass jemand ins Netz greift.
Hier greift jemand ins Netz — und nur das steht hier drin.

    pytest tests/test_plugin_yfinance_integration.py   # fragt Yahoo
    pytest -m "not integration"                        # ohne fremde Dienste

Was ein Integrationstest belegt und kein Double belegen kann: dass die
Symbolbildung noch trifft, dass Yahoo weiterhin Währung und Zeitstempel
liefert, und dass die Übersetzung in `Quote` und `FxRate` trägt.

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
    answer = plugin.fetch_quote(QuoteRequest(ticker="EUNL", mic="XETR"))

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
    ende = date.today()
    antwort = plugin.fetch_daily(
        DailyRequest(ticker="EUNL", mic="XETR", start=ende - timedelta(days=30), end=ende)
    )

    assert isinstance(antwort, DailySeries), antwort
    assert antwort.currency == "EUR"
    assert antwort.bars, "eine leere Reihe ist kein Ergebnis"
    assert days_are_ordered([bar.day for bar in antwort.bars]), (
        "streng aufsteigend — zwei Einträge für denselben Tag zählt der "
        "Verbraucher doppelt"
    )


def test_ein_wechselkurs(plugin: YFinancePlugin) -> None:
    """EUR/CHF — plausibler Bereich statt festgenagelter Zahl."""
    answer = plugin.fetch_rate(FxRequest(base="EUR", quote="CHF"))

    assert isinstance(answer, FxRate), answer
    assert (answer.base, answer.quote) == ("EUR", "CHF")
    assert 0.5 < answer.rate < 2.0


def test_der_identitaetsfall_braucht_keinen_anbieter(plugin: YFinancePlugin) -> None:
    """Eine Einheit einer Währung kostet **genau** eine Einheit derselben.

    Über einen Anbieter gerechnet käme 0,9999… heraus. Der Test steht hier und
    nicht bei den Unit-Tests, weil er belegt, dass der Abkürzungsweg auch dann
    greift, wenn eine echte Anbindung daneben steht.
    """
    answer = plugin.fetch_rate(FxRequest(base="EUR", quote="EUR"))

    assert isinstance(answer, FxRate), answer
    assert answer.rate == 1.0

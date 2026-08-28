"""Die App-Plugins gegen die geerbten Verträge aus T-27a.

**Der Grund, warum das hier steht und nicht als handgeschriebene Teilprüfung:**
Die Verträge existieren, sind selbst geprüft (23 Mutanten in `plugin_api`) und
stellen Fragen, auf die man von allein nicht kommt. Eigene Teilprüfungen daneben
zu schreiben hieße, sich die Fragen auszusuchen — und ausgerechnet die
unbequeme wegzulassen.

Genau das ist in Runde 1 passiert: Die drei neuen Klassen unter `app/plugins/`
hatten keinen einzigen Vertrag geerbt. Was die Verträge danach gefunden haben,
steht in den Docstrings der Suiten unten.

Die Doubles sind **testlokal und klein** — keine wiederverwendbare
Fake-Infrastruktur. Deren Aufbau war der Fehler, den `P-09` beschreibt.
"""

from datetime import date, datetime, timezone
from typing import Any

from stockinfo_plugin import (
    DailyRequest,
    FxRequest,
    QuoteRequest,
    ResolveRequest,
)
from stockinfo_plugin.testing import (
    DailyContract,
    FxContract,
    MetadataContract,
    QuoteContract,
)

from app.plugins.justetf_metadata import JustEtfMetadataPlugin
from app.plugins.yfinance_quotes import YFinancePlugin
from app.providers.base import EtfDetails, RawQuote


class FakeJustEtf:
    """Antwortet für **ein** Papier — der Rest ist unbekannt."""

    def fetch_etf(self, isin: str) -> EtfDetails | None:
        if isin != "IE00B4L5Y983":
            return None
        return EtfDetails(
            ter=0.2,
            provider="iShares",
            replication="Physisch",
            fund_size=1_200_000_000.0,
            fund_currency="USD",
            fund_domicile="Irland",
            name="iShares Core MSCI World",
            volatility=12.5,
            accumulating=True,
        )


class FakeYFinance:
    """Kennt genau ein Listing, in einer Währung."""

    def fetch_quote(self, symbol: str) -> RawQuote | None:
        if symbol != "EUNL.DE":
            return None
        return RawQuote(
            symbol=symbol,
            price=95.8,
            quote_time=datetime(2026, 1, 3, 17, 30, tzinfo=timezone.utc).isoformat(),
            currency="EUR",
            volume=1234,
        )

    def fetch_daily_closes(self, symbol: str, start: str | None = None) -> list[dict] | None:
        if symbol != "EUNL.DE":
            return []
        return [
            {"date": "2026-01-02", "close": 95.1, "currency": "EUR"},
            {"date": "2026-01-03", "close": 95.8, "currency": "EUR"},
        ]

    def fetch_fx_rate(self, base: str, quote: str) -> float | None:
        return 0.9376 if (base, quote) == ("EUR", "CHF") else None


class TestJustEtfMetadata(MetadataContract):
    """Der vollständige Metadaten-Vertrag — geerbt, nicht nachgeschrieben.

    **Drei Verstöße hat er gefunden**, und keiner davon wäre mir aufgefallen:

    * `FIELDS` war leer — die Suite verlangt, dass eine Quelle ihre Felder
      **deklariert**, sonst weiß die App nicht, wie sie einen Wert behandelt.
    * Bei Unzuständigkeit kam `None` statt einer leeren Liste zurück. Das ist
      ein Unterschied: „nicht zuständig" und „zuständig, nichts gefunden" darf
      der Aufrufer nicht verwechseln.
    * `fund_size` trägt `Unit.ABSOLUTE` und kam **ohne Währung**. Ein Betrag
      ohne Währung ist bedeutungslos — dieselbe Regel, die für Kurse gilt.
    """

    responsible = ResolveRequest(isin="IE00B4L5Y983")
    not_responsible = ResolveRequest(isin="US0378331005")

    def make_source(self) -> JustEtfMetadataPlugin:
        return JustEtfMetadataPlugin(provider=FakeJustEtf())


class TestYFinanceQuotes(QuoteContract):
    """Der Kursvertrag am yfinance-Plugin."""

    responsible = QuoteRequest(ticker="EUNL", mic="XETR")
    not_responsible = QuoteRequest(ticker="EUNL", mic="ZZZZ")
    unknown = QuoteRequest(ticker="GIBTESNICHT", mic="XETR")

    def make_source(self) -> YFinancePlugin:
        return YFinancePlugin(provider=FakeYFinance())


class TestYFinanceDaily(DailyContract):
    """Der Historienvertrag am yfinance-Plugin."""

    responsible = DailyRequest(ticker="EUNL", mic="XETR", start=date(2026, 1, 1))
    not_responsible = DailyRequest(ticker="EUNL", mic="ZZZZ")
    unknown = DailyRequest(ticker="GIBTESNICHT", mic="XETR")

    def make_source(self) -> YFinancePlugin:
        return YFinancePlugin(provider=FakeYFinance())


class TestYFinanceFx(FxContract):
    """Der Devisenvertrag am yfinance-Plugin.

    **Ein Verstoß, den ich selbst gebaut hatte:** `fetch_rate` fragte den
    Anbieter auch dann, wenn `handles` die Anfrage abgelehnt hatte — und ließ
    dessen Ausnahme durch. Eine Quelle, die bei Unzuständigkeit trotzdem
    zugreift, verbraucht Kontingent für eine Frage, die sie nicht beantworten
    will.
    """

    responsible = FxRequest(base="EUR", quote="CHF")
    not_responsible = FxRequest(base="EUR", quote="ZZZ")

    def make_source(self) -> YFinancePlugin:
        return YFinancePlugin(provider=FakeYFinance())


def test_der_identitaetsfall_braucht_keinen_anbieter() -> None:
    """Eine Einheit einer Währung kostet **genau** eine Einheit derselben.

    **Dieser Test stand bis Runde 1 unter dem `integration`-Marker** und wurde
    damit mit `-m "not integration"` abgewählt — obwohl er kein Netz berührt.
    Derselbe Fehler war kurz zuvor in T-27b korrigiert worden; hier steht er
    jetzt richtig, mit einem Anbieter, dessen Benutzung ein Fehler wäre.
    """

    class VerbotenerProvider:
        def fetch_fx_rate(self, base: str, quote: str) -> float:
            raise AssertionError("der Identitätsfall darf nicht fragen")

    plugin = YFinancePlugin(provider=VerbotenerProvider())

    answer = plugin.fetch_rate(FxRequest(base="EUR", quote="EUR"))

    assert answer.rate == 1.0
    assert (answer.base, answer.quote) == ("EUR", "EUR")


def test_eine_reihe_meldet_sich_als_bereinigt() -> None:
    """`auto_adjust=True` in der Anbindung heißt `adjusted=True` im Vertrag.

    Der Wert stimmte auch vorher; seine **Bedeutung** nicht. Ein Verbraucher,
    der unbereinigte Kurse erwartet, rechnete mit einer Rendite, die es so nie
    gab — und nichts hätte ihn gewarnt.
    """
    plugin = YFinancePlugin(provider=FakeYFinance())

    series: Any = plugin.fetch_daily(DailyRequest(ticker="EUNL", mic="XETR"))

    assert series.adjusted is True

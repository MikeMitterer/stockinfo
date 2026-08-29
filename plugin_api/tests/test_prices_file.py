"""Kurs, Historie und Devisen — die drei neuen Verträge an einem echten Plugin.

Derselbe Punkt wie bei `test_canada_file`: Der Autor nennt drei Anfragen, den
Rest prüft der Vertrag. Neu ist, dass es jetzt für **jede** der fünf Rollen
einen gibt — vor T-27a wäre eine Kursquelle nur dadurch abgesichert gewesen,
dass jemand sie sich angesehen hat.
"""

import shutil
from datetime import date
from pathlib import Path

import pytest

from stockinfo_plugin import (
    DailyRequest,
    FxRate,
    FxRequest,
    ListedIdentity,
    NotFound,
    Quote,
    QuoteRequest,
    Unavailable,
)
from stockinfo_plugin.testing import (
    DailyContract,
    DirectRunner,
    FxContract,
    QuoteContract,
    Scenario,
    run_scenarios,
)

from examples.prices_file import (
    FxFileSource,
    PricesFileDailySource,
    PricesFileQuoteSource,
)

FIXTURES = Path(__file__).parent / "fixtures"
CLOSES = FIXTURES / "closes.csv"
FX = FIXTURES / "fx.csv"


# ─── Die Verträge ─────────────────────────────────────────────────────────────


class TestPricesFileQuote(QuoteContract):
    """Der Kursvertrag — geerbt, nicht geschrieben."""

    responsible = QuoteRequest(ListedIdentity(ticker="RY", mic="XTSE"))
    not_responsible = QuoteRequest(ListedIdentity(ticker="", mic=""))
    unknown = QuoteRequest(ListedIdentity(ticker="ZZZZ", mic="XTSE"))

    def make_source(self) -> PricesFileQuoteSource:
        return PricesFileQuoteSource({"path": str(CLOSES)})


class TestPricesFileDaily(DailyContract):
    """Der Historienvertrag.

    ``start`` ist gesetzt, damit
    `test_der_angefragte_zeitraum_wird_eingehalten` etwas zu prüfen hat. Ohne
    Grenze wäre die Zeile ein leerer Durchlauf — sie liefe grün, ohne je eine
    Aussage zu treffen.
    """

    responsible = DailyRequest(ListedIdentity(ticker="RY", mic="XTSE"), start=date(2025, 12, 30))
    not_responsible = DailyRequest(ListedIdentity(ticker="", mic=""))
    unknown = DailyRequest(ListedIdentity(ticker="ZZZZ", mic="XTSE"))

    def make_source(self) -> PricesFileDailySource:
        return PricesFileDailySource({"path": str(CLOSES)})


class TestFxFile(FxContract):
    """Der Devisenvertrag — der Identitätsfall kommt aus `responsible.base`."""

    responsible = FxRequest(base="CAD", quote="EUR")
    not_responsible = FxRequest(base="CA", quote="EU")

    def make_source(self) -> FxFileSource:
        return FxFileSource({"path": str(FX)})


# ─── Was über den Vertrag hinausgeht, prüft der Autor selbst ──────────────────


def test_die_reihe_wird_sortiert_obwohl_die_datei_es_nicht_ist() -> None:
    """Wer von Hand pflegt, hängt neue Zeilen unten an — auch rückwirkende.

    Die Fixture steht deshalb absichtlich in der Reihenfolge 31., 29., 30. Der
    Vertrag verlangt streng aufsteigend; die Quelle sortiert, statt sich auf
    die Datei zu verlassen.
    """
    series = PricesFileDailySource({"path": str(CLOSES)}).fetch_daily(
        DailyRequest(ListedIdentity(ticker="RY", mic="XTSE"))
    )

    assert [bar.day for bar in series.bars] == [
        date(2025, 12, 29),
        date(2025, 12, 30),
        date(2025, 12, 31),
    ]


def test_der_aktuelle_kurs_ist_der_juengste_eintrag() -> None:
    """Eine Datei kennt keinen Intraday-Stand — einen zu behaupten wäre schlimmer."""
    quote = PricesFileQuoteSource({"path": str(CLOSES)}).fetch_quote(
        QuoteRequest(ListedIdentity(ticker="RY", mic="XTSE"))
    )

    assert isinstance(quote, Quote)
    assert quote.price == 141.55
    assert quote.as_of.date() == date(2025, 12, 31)


def test_der_bereinigungsstand_wird_deklariert_nicht_geraten() -> None:
    """Vorgabe ``False``: Eine von Hand gepflegte Tabelle ist fast nie bereinigt.

    Die freundlichere Annahme wäre hier die gefährlichere — bereinigte und
    unbereinigte Reihen unterscheiden sich um zweistellige Prozentwerte, und
    beide sehen für sich plausibel aus.
    """
    default = PricesFileDailySource({"path": str(CLOSES)})
    declared = PricesFileDailySource({"path": str(CLOSES), "adjusted": True})
    request = DailyRequest(ListedIdentity(ticker="RY", mic="XTSE"))

    assert default.fetch_daily(request).adjusted is False
    assert declared.fetch_daily(request).adjusted is True


def test_der_identitaetskurs_kommt_ohne_datei_aus() -> None:
    """Eine Währung in sich selbst ist ``1.0`` — das muss keine Tabelle sagen.

    Stünde dort versehentlich ``0.9998``, wäre der Fehler durch die ganze App
    gewandert. Deshalb steht der Fall **vor** dem Dateizugriff, und der Test
    weist das nach, indem er die Datei wegnimmt.
    """
    source = FxFileSource({"path": "/gibt/es/nicht.csv"})

    answer = source.fetch_rate(FxRequest(base="EUR", quote="EUR"))

    assert answer.rate == 1.0
    assert isinstance(source.fetch_rate(FxRequest(base="EUR", quote="USD")), Unavailable)


def test_eine_kaputte_zeile_ist_unavailable_und_nicht_notfound() -> None:
    """Ein Fehler der **Datei** ist keine Aussage über das Papier.

    `NotFound` behauptete, das Papier gebe es nicht — und der Betreiber suchte
    an der falschen Stelle, während in Wahrheit seine Tabelle einen Tippfehler
    hat.
    """
    broken = FIXTURES / "closes-broken.csv"
    broken.write_text(
        "ticker;mic;day;close;currency\nRY;XTSE;2025-13-45;141.55;CAD\n",
        encoding="utf-8",
    )
    try:
        answer = PricesFileDailySource({"path": str(broken)}).fetch_daily(
            DailyRequest(ListedIdentity(ticker="RY", mic="XTSE"))
        )
    finally:
        broken.unlink()

    assert isinstance(answer, Unavailable)
    assert "unlesbare Zeile" in answer.error


def test_eine_gemischte_waehrung_wird_nicht_stillschweigend_vereinheitlicht(
    tmp_path: Path,
) -> None:
    """**Gegenprüfung von Codex aus Runde 1.**

    Vorher übernahm die Quelle die Währung der **ersten** gefundenen Zeile und
    fragte nicht, ob die späteren dieselbe tragen. Eine von Hand gepflegte
    Tabelle bekommt über die Jahre Zeilen von verschiedenen Leuten — schreibt
    einer CAD und ein anderer USD für dasselbe Listing, entstand eine
    „einheitliche" Reihe mit gemischten Beträgen. Der Kurs darüber trug dann
    eine Währung, die von der Sortierreihenfolge abhing.

    Das schlimme daran ist die Lautlosigkeit: Beide Zahlen sind plausibel, die
    Reihe ist sortiert, der Vertrag ist grün.
    """
    mixed = tmp_path / "closes.csv"
    mixed.write_text(
        "ticker;mic;day;close;currency\n"
        "RY;XTSE;2025-12-30;140.10;CAD\n"
        "RY;XTSE;2025-12-31;103.90;USD\n",
        encoding="utf-8",
    )

    answer = PricesFileDailySource({"path": str(mixed)}).fetch_daily(
        DailyRequest(ListedIdentity(ticker="RY", mic="XTSE"))
    )

    assert isinstance(answer, Unavailable), (
        "gemischte Währungen wurden stillschweigend zu einer Reihe vereinheitlicht"
    )
    assert "CAD" in answer.error and "USD" in answer.error, (
        "die Meldung nennt beide Währungen — sonst muss der Betreiber suchen"
    )


def test_der_kurs_erbt_den_ausfall_der_reihe(tmp_path: Path) -> None:
    """Die Kursquelle liest über die Historienquelle — also erbt sie deren Urteil.

    Ohne diese Zeile bliebe offen, ob die Kursquelle die gemischte Datei
    trotzdem beantwortet: Sie nimmt den **letzten** Eintrag, und der hat für
    sich genommen eine eindeutige Währung.
    """
    mixed = tmp_path / "closes.csv"
    mixed.write_text(
        "ticker;mic;day;close;currency\n"
        "RY;XTSE;2025-12-30;140.10;CAD\n"
        "RY;XTSE;2025-12-31;103.90;USD\n",
        encoding="utf-8",
    )

    answer = PricesFileQuoteSource({"path": str(mixed)}).fetch_quote(
        QuoteRequest(ListedIdentity(ticker="RY", mic="XTSE"))
    )

    assert isinstance(answer, Unavailable)


def test_ein_nicht_gefuehrtes_papier_ist_notfound() -> None:
    """Nicht `Unavailable`: Es wurde nachgesehen, und die Tabelle führt es nicht."""
    answer = PricesFileDailySource({"path": str(CLOSES)}).fetch_daily(
        DailyRequest(ListedIdentity(ticker="ZZZZ", mic="XTSE"))
    )

    assert isinstance(answer, NotFound)


# ─── Golden Cases ─────────────────────────────────────────────────────────────
#
# Die Werte hier sind **nicht** aus der Fixture abgelesen. Sie stehen in der
# `note` je Fall mit ihrer Herkunft, und die Gegenprobe darunter beweist die
# Trennung: Wenn die Eingabedatei lügt, wird der Fall rot.

GOLDEN = (
    Scenario(
        case_id="rbc-tsx-quote",
        request=QuoteRequest(ListedIdentity(ticker="RY", mic="XTSE")),
        expect=Quote,
        golden={"currency": "CAD"},
        plausible={"price": (20.0, 500.0)},
        note=(
            "Die Royal Bank of Canada notiert an der TSX in kanadischen Dollar — "
            "eine Eigenschaft des Listings, nicht des Tages. Der Kurs selbst "
            "bewegt sich und steht deshalb als Bereich da, nicht als Wert."
        ),
    ),
    Scenario(
        case_id="cad-eur",
        request=FxRequest(base="CAD", quote="EUR"),
        expect=FxRate,
        golden={"base": "CAD", "quote": "EUR"},
        plausible={"rate": (0.4, 1.0)},
        note=(
            "Richtung und Größenordnung: Ein kanadischer Dollar war in den "
            "letzten zwanzig Jahren nie mehr als ein Euro wert. Der Bereich "
            "schlägt an, wenn eine Quelle das Paar vertauscht."
        ),
    ),
)


def test_die_golden_cases_laufen_durch_den_runner() -> None:
    """Format, Validierung und Vergleich in einem Durchgang.

    `DirectRunner` ruft die Quelle im selben Prozess auf; der Fall beschreibt,
    *was* gefragt wird, nicht *wie* die Quelle heißt.
    """
    quotes = DirectRunner(PricesFileQuoteSource({"path": str(CLOSES)}))
    rates = DirectRunner(FxFileSource({"path": str(FX)}))

    assert run_scenarios(quotes, [GOLDEN[0]]) == []
    assert run_scenarios(rates, [GOLDEN[1]]) == []


def test_eine_luegende_eingabedatei_macht_den_fall_rot(tmp_path: Path) -> None:
    """**Die Gegenprobe zum wichtigsten Fallstrick des Kits.**

    Golden-Werte dürfen nicht aus der Datei stammen, die die Quelle liest —
    sonst prüft der Fall nur noch, ob ein möglicherweise falscher Treffer
    *reproduzierbar* falsch ist. Behaupten lässt sich das leicht; hier wird es
    gemessen.

    Der Test verfälscht die Tabelle so, dass die Royal Bank angeblich in Euro
    notiert. Käme die Erwartung aus der Datei, zöge sie mit und der Fall bliebe
    grün. Er wird rot — also kommt sie woanders her.
    """
    lying = tmp_path / "closes.csv"
    shutil.copy(CLOSES, lying)
    lying.write_text(
        lying.read_text(encoding="utf-8").replace("CAD", "EUR"), encoding="utf-8"
    )

    findings = run_scenarios(
        DirectRunner(PricesFileQuoteSource({"path": str(lying)})), [GOLDEN[0]]
    )

    assert len(findings) == 1
    assert "'EUR'" in findings[0] and "'CAD'" in findings[0], (
        "die Erwartung ist mitgezogen — dann stammt sie aus der Eingabedatei"
    )


@pytest.mark.parametrize("scenario", GOLDEN, ids=lambda s: s.case_id)
def test_jeder_golden_case_nennt_seine_herkunft(scenario: Scenario) -> None:
    """In zwei Jahren ist „RY/XTSE" ohne Herkunft nicht mehr überprüfbar.

    Wer den Wert dann anzweifelt, hätte nur noch die geprüfte Quelle selbst —
    also genau die, aus der er nicht stammen durfte. Die `note` ist deshalb
    keine Zierde.
    """
    assert len(scenario.note) > 40, f"{scenario.case_id} nennt keine Herkunft"

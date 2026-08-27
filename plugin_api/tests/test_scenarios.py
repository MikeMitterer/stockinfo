"""Das Szenarioformat — und vor allem seine Validierung.

Die Validierung ist die Stufe, die es sonst nirgends gibt. Ein falsch
beschriebener Fall läuft grün, **weil** er nichts prüft: Ein Tippfehler im
Feldnamen vergleicht ein Feld, das es nicht gibt, und eine naive Prüfschleife
übergeht ihn stillschweigend. Deshalb prüft dieses Modul zuerst die
Beschreibungen und erst danach die Antworten.
"""

from datetime import datetime, timezone

from stockinfo_plugin import (
    FxRate,
    FxRequest,
    NotFound,
    NotResponsible,
    Quote,
    QuoteRequest,
    Resolved,
    ResolveRequest,
    Unavailable,
)
from stockinfo_plugin.testing import (
    DirectRunner,
    FakeQuoteSource,
    FakeResolver,
    Scenario,
    ScenarioRunner,
    check_scenario,
    run_scenarios,
    validate_scenarios,
)

GOOD = Scenario(
    case_id="rbc-tsx",
    request=ResolveRequest(isin="CA78012H5675"),
    expect=Resolved,
    golden={"ticker": "RY", "mic": "XTSE"},
    note="TMX-Listing der Royal Bank of Canada, von Hand nachgeschlagen",
)


# ─── Die Beschreibungen ───────────────────────────────────────────────────────


def test_ein_sauberer_fall_wird_nicht_beanstandet() -> None:
    assert validate_scenarios([GOOD]) == []


def test_ein_tippfehler_im_feldnamen_faellt_auf() -> None:
    """Der Fehler, der sonst nie auffällt — weil er grün ist.

    ``golden={"tikcer": "RY"}`` vergleicht ein Feld, das es an `Resolved` nicht
    gibt. Ohne diese Prüfung liefe der Fall durch, und der Autor glaubte, sein
    Ticker sei abgesichert.
    """
    broken = Scenario(
        case_id="tippfehler",
        request=ResolveRequest(isin="CA78012H5675"),
        expect=Resolved,
        golden={"tikcer": "RY", "mic": "XTSE"},
    )

    problems = validate_scenarios([broken])

    assert any("tikcer" in line for line in problems)
    assert any("ticker" in line for line in problems), "die Meldung nennt die echten"


def test_zwei_faelle_mit_derselben_kennung() -> None:
    """Danach trifft eine Aufzeichnung den falschen Fall — und niemand merkt es."""
    problems = validate_scenarios([GOOD, GOOD])

    assert any("doppelte case_id" in line for line in problems)


def test_ein_treffer_ohne_kernwerte_beweist_nichts() -> None:
    """„Irgendein `Resolved` kam zurück" ist keine Aussage über ein Wertpapier.

    Das ist die maschinelle Hälfte des Golden-Case-Gedankens: Ob die Werte
    **von Hand** gepflegt sind, kann kein Test sehen — dass sie überhaupt da
    sind, schon.
    """
    hollow = Scenario(
        case_id="ohne-kern",
        request=ResolveRequest(isin="CA78012H5675"),
        expect=Resolved,
    )

    problems = validate_scenarios([hollow])

    assert any("ticker" in line and "mic" in line for line in problems)


def test_ein_leerer_kernwert_ist_keine_erwartung() -> None:
    """``golden={"ticker": ""}`` sieht aus wie eine Zusage und ist eine Auslassung."""
    hollow = Scenario(
        case_id="leerer-kern",
        request=ResolveRequest(isin="CA78012H5675"),
        expect=Resolved,
        golden={"ticker": "", "mic": "XTSE"},
    )

    assert any("ist leer" in line for line in validate_scenarios([hollow]))


def test_eine_antwort_ohne_ergebnis_traegt_keine_werte() -> None:
    """`NotFound` hat keine Felder — wer dort Werte nennt, hat sich vertan."""
    confused = Scenario(
        case_id="verwirrt",
        request=ResolveRequest(isin="CA0679011084"),
        expect=NotFound,
        golden={"ticker": "RY"},
    )

    assert any("trägt keine Felder" in line for line in validate_scenarios([confused]))


def test_vertauschte_grenzen_schlagen_nie_an() -> None:
    """Ein leerer Bereich ist schlimmer als keiner — er meldet nie etwas.

    ``(10000, 1)`` sieht aus wie eine Plausibilitätsregel und ist eine Zusage,
    die niemals greift. Ohne diese Prüfung stünde sie jahrelang im Fall.
    """
    swapped = Scenario(
        case_id="vertauscht",
        request=QuoteRequest(ticker="RY", mic="XTSE"),
        expect=Quote,
        plausible={"price": (10000.0, 1.0)},
    )

    assert any("vertauschte Grenzen" in line for line in validate_scenarios([swapped]))


def test_ein_ausfall_laesst_sich_von_aussen_nicht_bestellen() -> None:
    """`real_ok` bei erwartetem `Unavailable` ist eine Erwartung an das Wetter."""
    impossible = Scenario(
        case_id="ausfall-real",
        request=ResolveRequest(isin="CA78012H5675"),
        expect=Unavailable,
        real_ok=True,
    )

    assert any("real_ok" in line for line in validate_scenarios([impossible]))


def test_alle_beanstandungen_kommen_auf_einmal() -> None:
    """Wer beim ersten Fehler abbricht, läuft zehnmal für zehn Fehler."""
    broken = [
        Scenario(case_id="", request=ResolveRequest(), expect=Resolved),
        Scenario(
            case_id="zweiter",
            request=ResolveRequest(isin="CA78012H5675"),
            expect=Resolved,
        ),
    ]

    assert len(validate_scenarios(broken)) >= 2


# ─── Der Vergleich ────────────────────────────────────────────────────────────


def test_die_falsche_ergebnisart_wird_benannt() -> None:
    """Die Meldung trägt den Grund mit, wenn die Antwort einen hat.

    „Erwartet Resolved, bekommen Unavailable" allein schickt den Autor auf die
    Suche. „(Netz weg)" beendet sie.
    """
    deviations = check_scenario(GOOD, Unavailable("Netz weg"))

    assert len(deviations) == 1
    assert "Resolved" in deviations[0] and "Unavailable" in deviations[0]
    assert "Netz weg" in deviations[0]


def test_ein_abweichender_kernwert_wird_gemeldet() -> None:
    deviations = check_scenario(GOOD, Resolved(ticker="RX", mic="XTSE"))

    assert len(deviations) == 1
    assert "'RX'" in deviations[0] and "'RY'" in deviations[0]


def test_ein_wert_ausserhalb_des_bereichs() -> None:
    """Der Pence-Fehler, wie ihn eine Plausibilitätsregel sieht."""
    scenario = Scenario(
        case_id="kurs",
        request=QuoteRequest(ticker="RY", mic="XTSE"),
        expect=Quote,
        plausible={"price": (1.0, 1000.0)},
    )
    in_pence = Quote(
        price=14155.0, currency="CAD", as_of=datetime(2026, 1, 2, tzinfo=timezone.utc)
    )

    deviations = check_scenario(scenario, in_pence)

    assert any("außerhalb" in line for line in deviations)


def test_ein_bereich_auf_etwas_das_keine_zahl_ist() -> None:
    """Sonst vergliche ``None <= wert`` — und das wirft, statt zu melden."""
    scenario = Scenario(
        case_id="kein-wert",
        request=FxRequest(base="CAD", quote="EUR"),
        expect=FxRate,
        golden={"base": "CAD", "quote": "EUR"},
        plausible={"as_of": (1.0, 2.0)},
    )
    answer = FxRate(
        base="CAD", quote="EUR", rate=0.64, as_of=datetime(2026, 1, 2, tzinfo=timezone.utc)
    )

    assert any("keine Zahl" in line for line in check_scenario(scenario, answer))


# ─── Der Runner ───────────────────────────────────────────────────────────────


def test_der_direkte_runner_erfuellt_den_runner_vertrag() -> None:
    """Ein Vertrag ohne eine einzige Umsetzung wäre eine Behauptung."""
    assert isinstance(DirectRunner(FakeResolver()), ScenarioRunner)


def test_der_runner_waehlt_die_methode_nach_dem_anfragetyp() -> None:
    """Ein Fall beschreibt, *was* gefragt wird — nicht, wie die Methode heißt."""
    source = FakeQuoteSource(
        Quote(price=141.55, currency="CAD", as_of=datetime(2026, 1, 2, tzinfo=timezone.utc))
    )
    scenario = Scenario(
        case_id="kurs",
        request=QuoteRequest(ticker="RY", mic="XTSE"),
        expect=Quote,
        plausible={"price": (1.0, 1000.0)},
    )

    assert run_scenarios(DirectRunner(source), [scenario]) == []


def test_eine_ausnahme_der_quelle_beendet_nicht_den_lauf() -> None:
    """Ein Verstoß gegen „wirft nicht" ist ein Befund, kein Testabbruch.

    Bräche der Runner ab, liefen die übrigen Fälle nicht mehr — obwohl sie es
    könnten, und obwohl der Autor gerade jetzt wissen will, welche davon noch
    tragen.
    """
    source = FakeResolver(RuntimeError("kaputt"))

    findings = run_scenarios(DirectRunner(source), [GOOD])

    assert len(findings) == 1
    assert "RuntimeError" in findings[0] and "kaputt" in findings[0]


def test_beschreibungsfehler_stehen_vor_den_laufergebnissen() -> None:
    """Ein falsch beschriebener Fall macht jede Abweichung darunter unglaubwürdig."""
    broken = Scenario(
        case_id="ohne-kern",
        request=ResolveRequest(isin="CA78012H5675"),
        expect=Resolved,
    )

    findings = run_scenarios(DirectRunner(FakeResolver(NotResponsible())), [broken])

    assert len(findings) == 1, "der Lauf hat gar nicht erst stattgefunden"
    assert "ticker" in findings[0]


def test_die_reale_betriebsart_waehlt_nur_freigegebene_faelle() -> None:
    """Derselbe Satz Fälle, zwei Betriebsarten — das ist der ganze Punkt.

    Welcher Runner hinter `only_real` steht, weiß dieses Modul nicht; T-27b
    stellt den HTTP-Runner daneben, ohne dass ein Fall neu geschrieben wird.
    """
    offline_only = Scenario(
        case_id="nur-offline",
        request=ResolveRequest(isin="CA0679011084"),
        expect=NotFound,
    )
    source = FakeResolver(keyed={GOOD.request: Resolved(ticker="RX", mic="XTSE")})

    findings = run_scenarios(DirectRunner(source), [GOOD, offline_only], only_real=True)

    assert findings == [], "kein Fall ist für den Realbetrieb freigegeben"

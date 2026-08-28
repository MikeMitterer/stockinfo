"""Ein Fall wird **einmal** beschrieben — und läuft in zwei Betriebsarten.

Ein Plugin-Autor hat zwei Bedürfnisse, die sich widersprechen. Er will bei
jedem Commit prüfen, ob sein Plugin noch tut, was es soll — schnell, ohne Netz,
reproduzierbar. Und er will vor einem Release wissen, ob der echte Anbieter
noch dasselbe liefert. Wer beides getrennt beschreibt, pflegt zwei Wahrheiten,
und die auseinanderlaufende ist immer die, die seltener läuft.

Deshalb: **ein** `Scenario` je Fall, zwei Runner. Was der Runner mit der
Anfrage macht, weiß dieses Modul nicht — es kennt weder HTTP noch Aufzeichnung.
`ScenarioRunner` ist genau eine Methode.

**Was hier abgenommen wird und was nicht.** Format, Validierung, Prüfung und
der transportneutrale Runner-Vertrag stehen hier, ausgeführt vom `DirectRunner`
gegen eine Quelle im selben Prozess. Dass derselbe Fall auch als Aufzeichnung
und gegen den echten Anbieter läuft, baut **T-27b** — dort gehört der
HTTP-Runner hin, und er hängt an diesem Format.

Der wichtigste Fallstrick steht in `Scenario.golden`.
"""

from dataclasses import dataclass, field, fields, is_dataclass
from typing import Protocol, runtime_checkable

from stockinfo_plugin.invariants import is_finite_number
from stockinfo_plugin.types import (
    DailyRequest,
    DailySeries,
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

HIT_TYPES: tuple[type, ...] = (Resolved, Quote, DailySeries, FxRate)
"""Die Ergebnisarten, bei denen es überhaupt etwas zu vergleichen gibt."""

MISS_TYPES: tuple[type, ...] = (NotResponsible, NotFound, Unavailable)
"""Die Ergebnisarten, die kein Ergebnis tragen."""

# Welche Kernwerte einen Treffer eindeutig machen. Ohne sie beweist ein Fall
# nichts: „irgendein Resolved kam zurück" ist keine Aussage über das Papier.
#
# **Alle vier Trefferarten, nicht nur zwei** — Befund aus Runde 1. `Quote` und
# `DailySeries` durften vorher ohne einen einzigen Erwartungswert dastehen und
# prüften damit nur, dass überhaupt geantwortet wurde. Der Kern ist bei ihnen
# die **Währung**: Sie ist eine Eigenschaft des Listings und ändert sich nicht
# von Tag zu Tag, während der Kurs es tut. Genau deshalb taugt sie als Golden
# Case und der Kurs nur als Bereich.
REQUIRED_GOLDEN: dict[type, tuple[str, ...]] = {
    Resolved: ("ticker", "mic"),
    Quote: ("currency",),
    DailySeries: ("currency",),
    FxRate: ("base", "quote"),
}

# Welche Trefferart zu welcher Anfrage gehört. Eine `QuoteRequest`, die ein
# `Resolved` erwartet, ist keine Erwartung, sondern ein Denkfehler — und er lief
# vorher grün, weil ein Double bereitwillig alles zurückgibt, was man ihm sagt.
ROLE_RESULTS: dict[type, type] = {
    ResolveRequest: Resolved,
    QuoteRequest: Quote,
    DailyRequest: DailySeries,
    FxRequest: FxRate,
}


@dataclass(frozen=True)
class Scenario:
    """Ein Prüffall — einmal beschrieben, in jeder Betriebsart derselbe.

    Attributes:
        case_id: Stabile Kennung. Sie taucht in jeder Meldung auf und darf sich
            **nicht** ändern, wenn der Fall umformuliert wird — sonst verliert
            eine Aufzeichnung ihren Fall, und niemand merkt es.
        request: Die Anfrage, im Typ ihrer Rolle.
        expect: Die erwartete **Ergebnisart** als Klasse, nicht als Zeichenkette.
            ``expect=NotFound`` statt ``expect="not_found"``: Ein Katalog von
            Kennungen müsste gepflegt werden und liefe gegen die Typen aus; eine
            Klasse ist ihre eigene Wahrheit, und ein Tippfehler ist ein
            ``NameError`` statt eines stillen Nichtvergleichs.
        golden: Erwartete Kernwerte, Feld für Feld.

            **Der wichtigste Fallstrick des ganzen Kits.** Diese Werte dürfen
            nicht aus der Aufzeichnung erzeugt werden. Wer sie aus dem
            mitgeschnittenen Anbieter-Antwortpaket ableitet, prüft nur noch, ob
            ein möglicherweise falscher Treffer *reproduzierbar* falsch ist —
            und je länger der Test grün bleibt, desto sicherer fühlt sich der
            Irrtum an.

            Golden-Erwartungen sind kleine, bewusst geprüfte Daten: Jemand hat
            nachgesehen, dass die Royal Bank of Canada an der TSX als ``RY``
            läuft, und hat es hingeschrieben. Sie werden getrennt von den
            Aufzeichnungen gepflegt, und `validate_scenarios` verlangt sie für
            jede Ergebnisart, bei der ein Treffer ohne sie nichts aussagt.
        plausible: Bereiche für Werte, die sich ändern — je Feld
            ``(untere, obere)`` Grenze, beide einschließlich. Ein Kurs lässt
            sich nicht festnageln, aber „zwischen 1 und 10000" schlägt an, wenn
            eine Quelle Pence für Pfund hält.
        real_ok: Ob der Fall gegen den echten Anbieter laufen darf. ``False``
            für alles, was von außen nicht herstellbar ist.
        note: Woher die Golden-Werte stammen. Freitext, aber nicht Zierde: In
            zwei Jahren ist „RY/XTSE" ohne Herkunft nicht mehr überprüfbar,
            und wer es dann anzweifelt, hat nur die Aufzeichnung — also genau
            die Quelle, die es nicht sein durfte.
    """

    case_id: str
    request: ResolveRequest | QuoteRequest | DailyRequest | FxRequest
    expect: type
    golden: dict[str, object] = field(default_factory=dict)
    plausible: dict[str, tuple[float, float]] = field(default_factory=dict)
    real_ok: bool = False
    note: str = ""


@runtime_checkable
class ScenarioRunner(Protocol):
    """Wie ein Szenario zu einer Antwort kommt — **eine** Methode.

    Transportneutral heißt wörtlich: Dieses Modul weiß nicht, ob die Antwort
    aus dem Prozess, aus einer Aufzeichnung oder aus dem Netz kommt. Alles, was
    ein Runner verspricht, ist eine Antwort auf ein Szenario.

    Der Vertrag hat eine einzige harte Regel, und sie ist dieselbe wie bei den
    Quellen: **Er wirft nicht.** Ein Runner, der bei Netzfehlern eine Ausnahme
    durchlässt, macht aus einem Anbieterausfall einen Testabbruch — und dann
    laufen die restlichen Fälle nicht mehr, obwohl sie es könnten.
    """

    def run(self, scenario: Scenario) -> object:
        """Beantwortet ein Szenario."""
        ...


class DirectRunner:
    """Der Runner ohne Transport: ruft die Quelle im selben Prozess auf.

    Er ist die Existenzberechtigung des Formats. Ein Runner-Vertrag ohne eine
    einzige Umsetzung wäre eine Behauptung — hier läuft jeder Fall dieses
    Pakets tatsächlich durch ihn hindurch, und `check_scenario` sieht echte
    Antworten statt gedachter.

    Die Zuordnung Anfragetyp → Methode steht hier und nicht im Szenario: Ein
    Fall beschreibt, *was* gefragt wird, nicht *wie* die Quelle heißt, die das
    beantwortet.
    """

    def __init__(self, source: object) -> None:
        """
        Args:
            source: Die zu befragende Quelle. Sie muss die Methode der Rolle
                haben, zu der die Anfragen gehören.
        """
        self._source = source

    def run(self, scenario: Scenario) -> object:
        """Ruft die zur Anfrage passende Methode auf.

        Returns:
            Die Antwort der Quelle. Wirft die Quelle entgegen dem Vertrag doch,
            wird daraus `Unavailable` — der Lauf soll bei den übrigen Fällen
            weitergehen, und der Verstoß steht danach als Abweichung da statt
            als abgebrochener Testlauf.
        """
        request = scenario.request
        methods = {
            ResolveRequest: "resolve",
            QuoteRequest: "fetch_quote",
            DailyRequest: "fetch_daily",
            FxRequest: "fetch_rate",
        }
        name = methods.get(type(request))
        if name is None:
            return Unavailable(f"unbekannter Anfragetyp {type(request).__name__}")
        try:
            return getattr(self._source, name)(request)
        except Exception as exc:  # noqa: BLE001 — der Verstoß ist der Befund
            return Unavailable(f"{type(exc).__name__}: {exc}")


def validate_scenarios(scenarios: list[Scenario] | tuple[Scenario, ...]) -> list[str]:
    """Prüft die **Fallbeschreibungen**, bevor irgendetwas läuft.

    Das ist die Stufe, die es sonst nirgends gibt: Ein falsch beschriebener Fall
    läuft grün, weil er nichts prüft. Ein `golden={"tikcer": "RY"}` mit Tippfehler
    vergleicht ein Feld, das es nicht gibt — und jede naive Prüfschleife
    übergeht es stillschweigend.

    Args:
        scenarios: Die zu prüfenden Fälle.

    Returns:
        Die Beanstandungen, je eine Zeile. Leere Liste heißt: Die Beschreibungen
        taugen. Bewusst **keine** Ausnahme — ein Aufrufer soll alle Fehler auf
        einmal sehen und nicht einen nach dem anderen reparieren.
    """
    problems: list[str] = []
    seen: set[str] = set()

    for scenario in scenarios:
        case_id = scenario.case_id
        if not case_id or not case_id.strip():
            problems.append("ein Fall hat keine case_id")
            continue
        if case_id in seen:
            problems.append(
                f"{case_id}: doppelte case_id — zwei Fälle mit derselben "
                "Kennung, und eine Aufzeichnung trifft danach den falschen"
            )
        seen.add(case_id)

        if scenario.expect not in (*HIT_TYPES, *MISS_TYPES):
            problems.append(
                f"{case_id}: expect={scenario.expect!r} ist keine Ergebnisart"
            )
            continue

        is_hit = scenario.expect in HIT_TYPES
        if not is_hit and (scenario.golden or scenario.plausible):
            problems.append(
                f"{case_id}: erwartet {scenario.expect.__name__}, nennt aber "
                "Werte — eine Antwort ohne Ergebnis trägt keine Felder"
            )
        if not is_hit and scenario.real_ok and scenario.expect is Unavailable:
            problems.append(
                f"{case_id}: real_ok bei erwartetem Unavailable — ein Ausfall "
                "des Anbieters lässt sich von außen nicht herstellen"
            )

        problems.extend(_check_role_match(scenario))
        problems.extend(_check_field_names(scenario))
        problems.extend(_check_ranges(scenario))
        if is_hit:
            problems.extend(_check_required_golden(scenario))
            problems.extend(_check_provenance(scenario))

    return problems


def _check_role_match(scenario: Scenario) -> list[str]:
    """Passt die erwartete Trefferart zur Rolle der Anfrage?

    **Befund aus Runde 1.** ``QuoteRequest`` mit ``expect=Resolved`` lief grün
    — ein Double gibt bereitwillig zurück, was man ihm sagt, und niemand hat
    gefragt, ob das überhaupt zusammenpasst. Der Fall prüfte danach eine
    Zusage, die es in dieser Rolle gar nicht gibt.

    Die Fehlfälle bleiben frei: `NotFound` und `Unavailable` sind für jede
    Rolle dieselbe Aussage.

    **Befund aus Runde 2 — an der Reihenfolge dieser beiden Prüfungen hängt
    alles.** Der Ausstieg für Fehlfälle stand vorher **vor** der Frage, ob der
    Anfragetyp überhaupt zu einer Rolle gehört. Ein Fall mit einem unbekannten
    Request und ``expect=Unavailable`` kam dadurch zweimal durch: Die
    Beschreibung wurde nicht beanstandet, und `DirectRunner` erfindet für einen
    unbekannten Anfragetyp genau das `Unavailable`, das der Fall erwartet. Die
    Quelle wurde nie gefragt — der Prüfstand hat sich selbst bestätigt.

    Deshalb gilt jetzt: Der **Anfragetyp** wird immer geprüft, die
    **Trefferart** nur dort, wo es überhaupt eine gibt.
    """
    expected = ROLE_RESULTS.get(type(scenario.request))
    if expected is None:
        known = ", ".join(sorted(role.__name__ for role in ROLE_RESULTS))
        return [
            f"{scenario.case_id}: {type(scenario.request).__name__} gehört zu "
            f"keiner bekannten Rolle — bekannt sind {known}"
        ]
    if scenario.expect not in HIT_TYPES:
        return []
    if scenario.expect is expected:
        return []
    return [
        f"{scenario.case_id}: {type(scenario.request).__name__} kann nur "
        f"{expected.__name__} liefern, erwartet wird aber "
        f"{scenario.expect.__name__} — die Rollen passen nicht zusammen"
    ]


def _check_provenance(scenario: Scenario) -> list[str]:
    """Trägt der Golden Case seine Herkunft?

    **Befund aus Runde 1: Das stand als Zusage im Ticket und wurde nur in einem
    App-eigenen Test geprüft** — also gerade nicht dort, wo ein fremder
    Plugin-Autor davon profitiert.

    In zwei Jahren ist ``RY/XTSE`` ohne Herkunft nicht mehr überprüfbar. Wer
    den Wert dann anzweifelt, hat nur die Aufzeichnung — also genau die Quelle,
    die es nicht sein durfte. Die Länge ist eine Untergrenze gegen ``"ok"``:
    kein Beweis für eine gute Begründung, aber die Grenze, unterhalb derer
    keine stehen kann.
    """
    if len(scenario.note.strip()) >= 20:
        return []
    return [
        f"{scenario.case_id}: note ist {scenario.note.strip()!r} — ein Golden "
        "Case ohne Herkunft ist in zwei Jahren nicht mehr überprüfbar, und "
        "nachschlagen ließe er sich dann nur in der Aufzeichnung"
    ]


def _known_fields(result_type: type) -> set[str]:
    """Die Feldnamen einer Ergebnisart."""
    if not is_dataclass(result_type):
        return set()
    return {spec.name for spec in fields(result_type)}


def _check_field_names(scenario: Scenario) -> list[str]:
    """Jeder genannte Feldname muss es an der Ergebnisart geben."""
    known_fields = _known_fields(scenario.expect)
    if not known_fields:
        return []
    return [
        f"{scenario.case_id}: Feld '{name}' gibt es an "
        f"{scenario.expect.__name__} nicht — bekannt: {', '.join(sorted(known_fields))}"
        for name in (*scenario.golden, *scenario.plausible)
        if name not in known_fields
    ]


def _check_ranges(scenario: Scenario) -> list[str]:
    """Taugen die Bereichsgrenzen — und schließen sie überhaupt etwas ein?

    **Befund aus Runde 2.** Geprüft wurde nur die Anzahl der Grenzen und ihre
    Reihenfolge, nicht ihre Art. ``plausible={"price": ("a", "z")}`` galt
    damit als gültige Beschreibung; erst `check_scenario` verglich später
    Zeichenkette gegen Zahl und warf `TypeError`. Das verletzt gleich zwei
    Zusagen dieses Moduls: `validate_scenarios` **sammelt** Beschreibungsfehler,
    statt beim ersten auszusteigen, und `run_scenarios` bricht nicht ab,
    solange noch Fälle laufen könnten. Ein falsch beschriebener Fall riss so
    alle übrigen mit.

    ``NaN`` und ``inf`` gehören zur selben Klasse: Sie sind formal Zahlen, und
    ein Vergleich gegen sie ist entweder immer wahr oder nie — beides schweigt
    genauso wie ein leerer Bereich.
    """
    problems = []
    for name, bounds in scenario.plausible.items():
        if not isinstance(bounds, (tuple, list)) or len(bounds) != 2:
            problems.append(
                f"{scenario.case_id}: '{name}' braucht zwei Grenzen als "
                f"(untere, obere), bekommen: {bounds!r}"
            )
            continue
        low, high = bounds
        unusable = [
            f"{edge} Grenze {value!r}"
            for edge, value in (("untere", low), ("obere", high))
            if not is_finite_number(value)
        ]
        if unusable:
            problems.append(
                f"{scenario.case_id}: '{name}' hat {' und '.join(unusable)} — "
                "eine Grenze muss eine endliche Zahl sein, sonst wirft der "
                "Vergleich später TypeError oder trifft immer beziehungsweise "
                "nie zu"
            )
            continue
        if low > high:
            problems.append(
                f"{scenario.case_id}: '{name}' hat vertauschte Grenzen "
                f"({low} > {high}) — der Bereich ist leer und schlägt nie an"
            )
    return problems


def _check_required_golden(scenario: Scenario) -> list[str]:
    """Ein Treffer ohne Kernwerte beweist nichts.

    Siehe `Scenario.golden`: „irgendein `Resolved` kam zurück" ist keine
    Aussage über ein Wertpapier. Für Ergebnisarten, deren Kern in
    `REQUIRED_GOLDEN` steht, sind die Werte deshalb Pflicht.
    """
    required = REQUIRED_GOLDEN.get(scenario.expect, ())
    missing = [name for name in required if name not in scenario.golden]
    empty = [
        name
        for name in required
        if name in scenario.golden and scenario.golden[name] in (None, "")
    ]
    problems = []
    if missing:
        problems.append(
            f"{scenario.case_id}: {scenario.expect.__name__} ohne "
            f"{', '.join(missing)} — der Fall prüft nur, dass irgendein "
            "Treffer kam, nicht welcher"
        )
    if empty:
        problems.append(
            f"{scenario.case_id}: {', '.join(empty)} ist leer — das ist keine "
            "Erwartung, sondern eine ausgelassene"
        )
    return problems


def check_scenario(scenario: Scenario, result: object) -> list[str]:
    """Hält die Antwort, was der Fall verlangt?

    Args:
        scenario: Der Fall.
        result: Was der Runner geliefert hat.

    Returns:
        Die Abweichungen, je eine Zeile. Leere Liste heißt bestanden.
    """
    if not isinstance(result, scenario.expect):
        reason = getattr(result, "error", "") or getattr(result, "reason", "")
        return [
            f"{scenario.case_id}: erwartet {scenario.expect.__name__}, bekommen "
            f"{type(result).__name__}" + (f" ({reason})" if reason else "")
        ]

    deviations = []
    for name, expected in scenario.golden.items():
        actual = getattr(result, name, None)
        if actual != expected:
            deviations.append(
                f"{scenario.case_id}: {name} ist {actual!r}, erwartet "
                f"{expected!r}"
            )
    for name, (low, high) in scenario.plausible.items():
        value = getattr(result, name, None)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            deviations.append(
                f"{scenario.case_id}: {name} ist {value!r} — keine Zahl, der "
                "Bereich lässt sich nicht prüfen"
            )
        elif not low <= value <= high:
            deviations.append(
                f"{scenario.case_id}: {name} = {value} liegt außerhalb "
                f"[{low}, {high}]"
            )
    return deviations


def run_scenarios(
    runner: ScenarioRunner,
    scenarios: list[Scenario] | tuple[Scenario, ...],
    *,
    only_real: bool = False,
) -> list[str]:
    """Lässt alle Fälle laufen und sammelt, was nicht stimmt.

    **Alle** — nicht bis zum ersten Fehler. Wer zehn Fälle beschreibt und beim
    ersten abbricht, repariert zehnmal hintereinander je einen und läuft
    zehnmal.

    Args:
        runner: Wie die Antworten beschafft werden.
        scenarios: Die Fälle.
        only_real: Nur Fälle mit ``real_ok``. Das ist die Betriebsart „gegen den
            echten Anbieter" — welcher Runner dahintersteht, bleibt offen.

    Returns:
        Erst die Beanstandungen an den Beschreibungen, dann die Abweichungen der
        Läufe. Beschreibungsfehler stehen zuerst, weil ein falsch beschriebener
        Fall jede Abweichung darunter unglaubwürdig macht.

        **Ein Lauf ohne einen einzigen Fall ist eine Beanstandung, kein
        Erfolg.** Das war ein Befund aus Runde 1 und es ist dasselbe Muster wie
        `P-05`: Die leere Liste sah aus wie „alles in Ordnung" und hieß in
        Wahrheit „nichts geprüft". Bei ``only_real`` ist der Fall besonders
        heimtückisch — vergisst ein Autor überall `real_ok`, meldet sein
        Release-Lauf jahrelang Erfolg, ohne je den echten Anbieter zu fragen.
    """
    findings = validate_scenarios(scenarios)
    if findings:
        return findings
    selected = [s for s in scenarios if s.real_ok] if only_real else list(scenarios)
    if not selected:
        return [
            "kein einziger Fall gelaufen — bei only_real=True heißt das, dass "
            "keiner real_ok trägt; sonst, dass die Liste leer war. Ein leeres "
            "Ergebnis sieht wie Erfolg aus und ist keiner."
            if only_real
            else "kein einziger Fall gelaufen — die Liste war leer. Ein leeres "
            "Ergebnis sieht wie Erfolg aus und ist keiner."
        ]
    for scenario in selected:
        findings.extend(check_scenario(scenario, runner.run(scenario)))
    return findings

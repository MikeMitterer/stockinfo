"""Alle fünf Rollenverträge an einer Quelle — der Sinn des Contract-Kits.

`yaml-file` ist das einzige mitgelieferte Beispiel und bedient jede Rolle. Ein
Beispiel, das den Vertrag **nicht** maschinell erfüllt, ist eine Behauptung:
Der Autor eines fremden Plugins liest es als Vorlage, und was hier
durchrutscht, rutscht dort auch durch.

Der Autor setzt je Rolle zwei bis drei Anfragen; alles andere prüft die
geerbte Suite. Sechs Zeilen je Rolle, und der Vertrag ist gemessen statt
zugesagt.
"""

from datetime import date
from pathlib import Path

import pytest

from stockinfo_plugin import (
    DailyRequest,
    FxRequest,
    IsinOnlyIdentity,
    ListedIdentity,
    QuoteRequest,
    ResolveRequest,
)
from stockinfo_plugin.testing import (
    DailyContract,
    FxContract,
    MetadataContract,
    QuoteContract,
    ResolverContract,
)

from examples.yaml_file import YamlFileSource

FIXTURE = Path(__file__).parent / "fixtures" / "assets.yaml"

# Die Papiere aus der Prüfdatei. Sie sind **von Hand nachgeschlagen** und nicht
# aus der Antwort abgeleitet — ein Erwartungswert, der aus dem Prüfling
# stammt, bestätigt nur, dass er reproduzierbar antwortet.
_ETF = "IE00B4L5Y983"  # iShares Core MSCI World, Xetra, Ticker EUNL
_BOND = "DE0001102531"  # Bundesanleihe, kein Handelsplatz
_ABSENT = "CA0679011084"  # Barrick Gold — gültige ISIN, steht nicht in der Datei


def _source() -> YamlFileSource:
    return YamlFileSource({"path": str(FIXTURE)})


class TestYamlFileResolver(ResolverContract):
    """Auflösung: Identität, Name und Gattung aus der Datei."""

    responsible = ResolveRequest(isin=_ETF)
    # **Unzuständig heißt hier „ohne Schlüssel", nicht „nicht in der Datei".**
    # Eine ISIN, die die Datei nicht führt, ist eine beantwortbare Frage mit
    # der Antwort „kenne ich nicht" — das ist `NotFound`. Eine Anfrage ohne
    # ISIN und ohne Symbol lässt sich gar nicht erst nachschlagen.
    not_responsible = ResolveRequest()
    unknown = ResolveRequest(isin=_ABSENT)

    def make_source(self) -> YamlFileSource:
        return _source()


class TestYamlFileMetadata(MetadataContract):
    """Metadaten: die optionalen Kennzahlen eines Eintrags."""

    responsible = ResolveRequest(isin=_ETF)
    not_responsible = ResolveRequest(isin=_ABSENT)

    def make_source(self) -> YamlFileSource:
        return _source()


class TestYamlFileQuote(QuoteContract):
    """Kurs: der gepflegte `price` oder der jüngste Schlusskurs."""

    responsible = QuoteRequest(
        identity=ListedIdentity(ticker="EUNL", mic="XETR", isin=_ETF)
    )
    not_responsible = QuoteRequest(identity=ListedIdentity(ticker="", mic=""))
    unknown = QuoteRequest(identity=IsinOnlyIdentity(isin=_ABSENT))

    def make_source(self) -> YamlFileSource:
        return _source()


class TestYamlFileDaily(DailyContract):
    """Historie: die manuell gepflegte Reihe der Anleihe."""

    responsible = DailyRequest(
        identity=IsinOnlyIdentity(isin=_BOND),
        start=date(2026, 8, 1),
        end=date(2026, 8, 31),
    )
    not_responsible = DailyRequest(
        identity=ListedIdentity(ticker="", mic=""),
        start=date(2026, 8, 1),
        end=date(2026, 8, 31),
    )
    unknown = DailyRequest(
        identity=IsinOnlyIdentity(isin=_ABSENT),
        start=date(2026, 8, 1),
        end=date(2026, 8, 31),
    )

    def make_source(self) -> YamlFileSource:
        return _source()


class TestYamlFileFx(FxContract):
    """Devisen: die Einträge aus `fx_rates`."""

    responsible = FxRequest(base="CAD", quote="EUR")
    not_responsible = FxRequest(base="JPY", quote="CHF")

    def make_source(self) -> YamlFileSource:
        return _source()


# ─── Was über die Verträge hinausgeht, prüft der Autor selbst ─────────────────


def test_die_history_wird_auf_das_fenster_beschnitten() -> None:
    """Eine Anfrage bekommt **ihr** Fenster, nicht die ganze Datei.

    Der Vertrag nennt `start` und `end`, und wer sie ignoriert, liefert für
    jede Anfrage dieselbe Reihe. Für den Aufrufer sieht das aus wie eine
    Antwort auf seine Frage — und ist die Antwort auf eine andere.
    """
    source = _source()

    outside = source.fetch_daily(
        DailyRequest(
            identity=IsinOnlyIdentity(isin=_BOND),
            start=date(2030, 1, 1),
            end=date(2030, 12, 31),
        )
    )

    # **Leer, nicht unbekannt.** Das Papier ist geführt und hat einen Verlauf —
    # nur nicht in diesem Fenster. `NotFound` hieße „kenne ich nicht" und
    # schickte den Aufrufer eine Quelle weiter, die es auch nicht besser weiß.
    assert outside.bars == (), f"das Fenster wurde ignoriert: {outside}"
    assert outside.currency == "EUR"
    assert outside.adjusted is False


def test_derselbe_wechselkurs_auf_sich_selbst_ist_eins() -> None:
    """`CAD/CAD` ist 1.0 — und keine Frage an eine Quelle.

    Der Identitätskurs steht in keiner Datei, weil ihn niemand pflegt. Ihn als
    „kenne ich nicht" abzuweisen zwänge den Host, dieselbe Rechnung selbst
    anzustellen — für eine Zahl, die feststeht.
    """
    source = _source()

    assert source.fetch_rate(FxRequest(base="CAD", quote="CAD")).rate == 1.0

    # **Nur für eine echte Währung.** `ZZZ` vergibt ISO 4217 nicht; ihm 1.0 zu
    # antworten hieße, einen Tippfehler zu bestätigen.
    invented = FxRequest(base="ZZZ", quote="ZZZ")
    assert source.handles(invented) is False
    assert getattr(source.fetch_rate(invented), "rate", None) is None


def test_zustaendig_ist_wer_die_zeile_hat() -> None:
    """`handles` beantwortet die Frage der **jeweiligen** Rolle.

    Bis hierher fragte jede Rolle denselben Instrumentenindex — auch die
    Devisenrolle, die dort nie etwas findet. Ergebnis: `handles(CAD/EUR)` war
    `False`, während `fetch_rate` denselben Kurs lieferte. Eine Quelle, die
    ihre Zuständigkeit verneint und dann doch antwortet, macht den Vorfilter
    des Hosts wertlos.
    """
    source = _source()

    assert source.handles(FxRequest(base="CAD", quote="EUR")) is True
    assert source.handles(FxRequest(base="JPY", quote="CHF")) is False
    assert source.handles(ResolveRequest(isin=_ETF)) is True
    assert source.handles(ResolveRequest(isin=_ABSENT)) is False


# Der Rumpf, an dem jede Grenze einzeln verbogen wird. Ein Mutant, der zwei
# Fehler trägt, belegt nicht, welcher gefunden wurde.
_SHELL = """version: 1
instruments:
  - id: a
    identity: {kind: isin_only, isin: DE0001102531}
    name: Bundesanleihe
    instrument_type: bond
"""


@pytest.mark.parametrize(
    ("broken", "expected"),
    [
        # ─── die Wurzel ──────────────────────────────────────────────────────
        pytest.param("version: 1\ninstruments: {}\n", "liste", id="instruments-objekt"),
        pytest.param("version: 999\ninstruments: []\n", "version", id="version-unbekannt"),
        pytest.param("version: true\ninstruments: []\n", "version", id="version-boolean"),
        pytest.param("version: 1.0\ninstruments: []\n", "version", id="version-gleitkomma"),
        pytest.param("instruments: []\n", "version", id="version-fehlt"),
        pytest.param(
            "version: 1\ninstruments: []\nfx_rates: {}\n", "liste", id="fx-objekt"
        ),
        pytest.param(
            "version: 1\ninstruments: []\nfx_rates: [7]\n", "objekt", id="fx-punkt-skalar"
        ),
        pytest.param("version: 1\ninstruments: [7]\n", "objekt", id="instrument-skalar"),
        # ─── ein Instrument ──────────────────────────────────────────────────
        pytest.param(
            _SHELL.replace("id: a", "id: 7"), "zeichenkette", id="id-zahl"
        ),
        pytest.param(
            _SHELL.replace("name: Bundesanleihe", "name: 7"),
            "zeichenkette",
            id="name-zahl",
        ),
        pytest.param(
            _SHELL.replace("instrument_type: bond", "instrument_type: 7"),
            "zeichenkette",
            id="gattung-zahl",
        ),
        pytest.param(
            _SHELL.replace("instrument_type: bond", "instrument_type: spaceship"),
            "spaceship",
            id="gattung-ausserhalb-des-katalogs",
        ),
        pytest.param(
            _SHELL.replace(
                "identity: {kind: isin_only, isin: DE0001102531}", "identity: nope"
            ),
            "objekt",
            id="identity-skalar",
        ),
        # ─── die Unterblöcke ─────────────────────────────────────────────────
        pytest.param(_SHELL + "    price: []\n", "objekt", id="price-liste"),
        pytest.param(_SHELL + "    metadata: []\n", "objekt", id="metadata-liste"),
        pytest.param(_SHELL + "    history: []\n", "objekt", id="history-liste"),
        pytest.param(
            _SHELL + "    history: {currency: EUR, closes: 7}\n",
            "liste",
            id="closes-skalar",
        ),
        pytest.param(
            _SHELL + "    history: {currency: EUR, closes: [7]}\n",
            "objekt",
            id="close-punkt-skalar",
        ),
        pytest.param(
            _SHELL + "    history: {currency: 7, closes: []}\n",
            "zeichenkette",
            id="history-waehrung-zahl",
        ),
        pytest.param(
            _SHELL
            + '    price: {value: 1.0, currency: 7, as_of: "2026-08-27T17:30:00+02:00"}\n',
            "zeichenkette",
            id="price-waehrung-zahl",
        ),
        # ─── die Kennzahlen ──────────────────────────────────────────────────
        pytest.param(
            _SHELL + "    metadata: {ter_bps: nope}\n", "ter_bps", id="kennzahl-text"
        ),
        pytest.param(
            _SHELL + "    metadata: {ter_bps: 5000}\n",
            "bereich",
            id="kennzahl-ausserhalb-des-bereichs",
        ),
        pytest.param(
            _SHELL + "    metadata: {provider: 7}\n",
            "zeichenkette",
            id="kennzahl-text-ist-zahl",
        ),
        # ─── die Devisen ─────────────────────────────────────────────────────
        pytest.param(
            "version: 1\ninstruments: []\nfx_rates:\n  - {base: 7, quote: EUR, rate: 1.0,"
            ' as_of: "2026-08-27T17:30:00+02:00"}\n',
            "zeichenkette",
            id="fx-basis-zahl",
        ),
    ],
)
def test_jede_grenze_meldet_ihre_form(
    tmp_path: Path, broken: str, expected: str
) -> None:
    """**Die Formgrenze, einmal vollständig.**

    Bis hierher wurde sie mit Einzelfällen nachgezogen, und die Übergabe
    behauptete danach, es entkomme nichts mehr. Das stimmte nicht: `identity:
    nope`, eine Zahl in `name`, ein skalarer Listenpunkt und leere Listen an
    `price`/`metadata`/`history` kamen weiterhin durch — die letzten drei, weil
    `or {}` jeden falsey Wert in ein „fehlt" verwandelt.

    Jeder Fall verbiegt **eine** Grenze an einem sonst tadellosen Rumpf. Zwei
    Fehler in einem Mutanten belegten nicht, welcher gefunden wurde.

    Zwei Fälle sind dabei Fallen der Sprache selbst: ``version: true`` und
    ``version: 1.0`` galten als Fassung 1, weil ``True == 1`` und ``1.0 == 1``
    in einer Menge von Ganzzahlen gefunden werden.
    """
    path = tmp_path / "kaputt.yaml"
    path.write_text(broken, encoding="utf-8")

    problem = YamlFileSource({"path": str(path)}).configuration_problem()

    assert problem, "die Quelle meldet keinen Grund"
    assert expected in problem.lower(), problem


# ─── Die inneren Werte: Identitätsfelder und Zahlen ───────────────────────────

_HUGE = "9" * 1000
"""Eine Ganzzahl, die keine Gleitkommazahl mehr ist.

`float(10**1000)` wirft `OverflowError`. Bis hierher warf sie bei Metadaten im
Konstruktor und bei Kurs, Historie und Devisen erst **beim Abruf** — also dort,
wo niemand mehr an die Datei denkt.
"""


@pytest.mark.parametrize(
    ("field", "line"),
    [
        ("kind", "identity: {kind: 7, isin: DE0001102531}"),
        ("ticker", "identity: {kind: listed, ticker: 7, mic: XETR}"),
        ("mic", "identity: {kind: listed, ticker: EUNL, mic: 7}"),
        ("isin", "identity: {kind: listed, ticker: EUNL, mic: XETR, isin: 7}"),
        ("base", "identity: {kind: pair, base: 7, quote_currency: EUR}"),
        ("quote_currency", "identity: {kind: pair, base: BTC, quote_currency: 7}"),
        ("isin_only", "identity: {kind: isin_only, isin: 7}"),
    ],
)
def test_ein_identitaetsfeld_ist_text(tmp_path: Path, field: str, line: str) -> None:
    """Jedes Identitätsfeld läuft durch die Textprüfung.

    Eine Zahl in `ticker` warf aus dem Konstruktor, weil dort jemand `.strip()`
    ruft — der Betreiber las einen `AttributeError` statt der Zeile, die er
    ändern muss. Die Prüfung steht deshalb **vor** `identity_problem` und nicht
    daneben.
    """
    path = tmp_path / "kaputt.yaml"
    path.write_text(
        f"""version: 1
instruments:
  - id: a
    {line}
    name: Papier
    instrument_type: bond
""",
        encoding="utf-8",
    )

    problem = YamlFileSource({"path": str(path)}).configuration_problem()

    assert "zeichenkette" in problem.lower(), problem


@pytest.mark.parametrize(
    ("where", "document"),
    [
        pytest.param(
            "price",
            _SHELL + '    price: {value: VALUE, currency: EUR,'
            ' as_of: "2026-08-27T17:30:00+02:00"}\n',
            id="price",
        ),
        pytest.param(
            "close",
            _SHELL + '    history: {currency: EUR, closes: [{date: "2026-08-27",'
            " value: VALUE}]}\n",
            id="close",
        ),
        pytest.param(
            "metadata",
            _SHELL + "    metadata: {ter_bps: VALUE}\n",
            id="metadata",
        ),
        pytest.param(
            "fx",
            "version: 1\ninstruments: []\nfx_rates:\n  - {base: CAD, quote: EUR,"
            ' rate: VALUE, as_of: "2026-08-27T17:30:00+02:00"}\n',
            id="fx-rate",
        ),
    ],
)
@pytest.mark.parametrize(
    "value", [_HUGE, "true", '"20"'], ids=["riesig", "wahrheitswert", "text"]
)
def test_jeder_zahlenverbraucher_prueft_den_rohen_wert(
    tmp_path: Path, where: str, document: str, value: str
) -> None:
    """**Vier Verbraucher, drei Sorten Nichtzahl** — und alle beim Laden.

    ``true`` ist in Python eine Ganzzahl und käme sonst als ``1.0`` durch.
    ``"20"`` ist Text; ihn umzuwandeln hieße zu raten, was der Benutzer
    meinte. Und eine tausendstellige Ganzzahl ist zwar eine Zahl, aber keine,
    die sich als Gleitkommazahl ausdrücken lässt.

    Geprüft wird je **Verbraucher**, nicht nur am Helfer: Ein Helfer, den nur
    drei von vier Stellen benutzen, ist an der vierten wirkungslos.
    """
    path = tmp_path / "kaputt.yaml"
    path.write_text(document.replace("VALUE", value), encoding="utf-8")

    problem = YamlFileSource({"path": str(path)}).configuration_problem()

    assert problem, f"{where} nimmt {value} an"
    assert "zahl" in problem.lower() or "groß" in problem.lower(), problem


def test_ein_unlesbarer_wert_beim_lesen_ist_ein_befund(tmp_path: Path) -> None:
    """Auch der Leseschritt endet in einem Grund, nicht in einem Stacktrace.

    Python bricht das Umwandeln sehr langer Ganzzahlen ab — Grenze 4300
    Stellen. Das ist ein Wert in der Datei und kein Fehler der App; er gehört
    in dieselbe Meldung wie ein Syntaxfehler.
    """
    path = tmp_path / "riesig.yaml"
    path.write_text(f"version: 1\ninstruments: []\nx: {'9' * 5000}\n", encoding="utf-8")

    problem = YamlFileSource({"path": str(path)}).configuration_problem()

    assert problem, "der Lesefehler kommt als Ausnahme statt als Grund"
    assert "unlesbar" in problem.lower() or "wert" in problem.lower(), problem

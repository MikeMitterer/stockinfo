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

    assert type(outside).__name__ == "NotFound", (
        f"ein Fenster ohne gepflegte Tage liefert Werte: {outside}"
    )


def test_derselbe_wechselkurs_auf_sich_selbst_ist_eins() -> None:
    """`CAD/CAD` ist 1.0 — und keine Frage an eine Quelle.

    Der Identitätskurs steht in keiner Datei, weil ihn niemand pflegt. Ihn als
    „kenne ich nicht" abzuweisen zwänge den Host, dieselbe Rechnung selbst
    anzustellen — für eine Zahl, die feststeht.
    """
    answer = _source().fetch_rate(FxRequest(base="CAD", quote="CAD"))

    assert getattr(answer, "rate", None) == 1.0, answer


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


@pytest.mark.parametrize(
    ("broken", "expected"),
    [
        pytest.param("version: 1\ninstruments: {}\n", "liste", id="instruments-objekt"),
        pytest.param(
            "version: 999\ninstruments: []\n", "version", id="unbekannte-version"
        ),
        pytest.param(
            """version: 1
instruments:
  - id: a
    identity: {kind: isin_only, isin: DE0001102531}
    name: Raumschiff
    instrument_type: spaceship
""",
            "spaceship",
            id="gattung-ausserhalb-des-katalogs",
        ),
        pytest.param(
            """version: 1
instruments:
  - id: a
    identity: {kind: isin_only, isin: DE0001102531}
    name: Anleihe
    instrument_type: bond
    metadata: {ter_bps: nope}
""",
            "ter_bps",
            id="kennzahl-ist-keine-zahl",
        ),
    ],
)
def test_ein_formfehler_entkommt_dem_konstruktor_nicht(
    tmp_path: Path, broken: str, expected: str
) -> None:
    """**Vier Wege, auf denen ein Benutzerwert bisher entkam.**

    Zwei davon warfen erst später — `instruments: {}` im Konstruktor, eine
    unlesbare Kennzahl beim Abruf. Ein Fehler, der die Quelle nicht sauber
    abschaltet, kostet den Betreiber die Meldung: Er sieht einen Stacktrace
    oder eine Rolle, die stumm nichts liefert.

    Die beiden anderen wurden **angenommen**: eine unbekannte Formatversion
    und eine Gattung außerhalb des Katalogs. Beides sieht aus wie eine Datei,
    die funktioniert, und ist eine, die stillschweigend etwas anderes bedeutet.
    """
    path = tmp_path / "kaputt.yaml"
    path.write_text(broken, encoding="utf-8")

    problem = YamlFileSource({"path": str(path)}).configuration_problem()

    assert problem, "die Quelle meldet keinen Grund"
    assert expected in problem.lower(), problem

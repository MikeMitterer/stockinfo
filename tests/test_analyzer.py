"""Die Diagnose misst die **konfigurierte Kette**, nicht feste Anbieter.

Bis T-46 baute der Analyzer `yf.Ticker` und `JustEtfProvider` selbst und
beschriftete seine Stufen mit deren Namen. Eine Instanz ohne Online-Quelle
bekam damit Zahlen zu einer Kette, die sie nicht führt — und ging beim
Analysieren ins Netz, obwohl sie bewusst offline lief.

Geprüft wird deshalb dreierlei:

============ ================================================================
Zuordnung    Je konfigurierte Quelle **und** Rolle eine Zeile, in der
             Reihenfolge der Konfiguration
Nichtfragen  Eine Quelle, die die Kaskade nach einem Treffer nicht mehr
             gebraucht hat, meldet `skipped` — nicht `0 ms, ok`
Ausgänge     `ok`, `empty` und `error` unterscheiden sich, und keiner davon
             bricht die übrigen Rollen ab
============ ================================================================
"""

import ast
from pathlib import Path

from stockinfo_plugin.types import NotFound, Unavailable

from app.providers.base import EtfDetails, ResolvedInstrument, SourceAnswer
from app.services.analyzer import QuoteAnalyzer

_APP = Path(__file__).resolve().parent.parent / "app"

_ETF = ResolvedInstrument(
    symbol="EUNL.DE", isin="IE00B4L5Y983", ticker="EUNL", mic="XETR", type="etf"
)


class _Resolver:
    """Eine Auflösungsquelle mit fester Antwort."""

    def __init__(self, name: str, answer=None) -> None:
        self.name = name
        self._answer = _ETF if answer is None else answer
        self.calls = 0

    def handles(self, isin: str) -> bool:
        return True

    def resolve_isin(self, isin: str):
        self.calls += 1
        return self._answer

    def resolve_symbol(self, symbol: str):
        self.calls += 1
        return self._answer


class _Quotes:
    def __init__(self, name: str, quote=None) -> None:
        self.name = name
        self._quote = quote
        self.calls = 0

    def fetch_quote(self, instrument):
        self.calls += 1
        return self._quote


class _Daily:
    def __init__(self, name: str, rows=None) -> None:
        self.name = name
        self._rows = rows
        self.calls = 0

    def fetch_daily_closes(self, symbol, start=None, *, identity=None, instrument_type=None):
        self.calls += 1
        return SourceAnswer(self._rows)


class _Meta:
    def __init__(self, name: str, details=None) -> None:
        self.name = name
        self._details = details
        self.calls = 0

    def is_responsible(self, isin, **kwargs) -> bool:
        return True

    def fetch_etf(self, isin, symbol=None, **kwargs):
        self.calls += 1
        return self._details


def _rows(count: int) -> list[dict]:
    return [
        {"date": f"2026-08-{day + 1:02d}", "close": 100.0 + day, "currency": "EUR"}
        for day in range(count)
    ]


def _stages(result) -> dict[tuple[str, str], object]:
    return {(stage.role, stage.source): stage for stage in result.stages}


# ─── Keine eigene Quelle ──────────────────────────────────────────────────────


def _imported_modules(path: Path) -> set[str]:
    """Jedes importierte Modul einer Datei — auch die in Funktionen.

    Ein Inventar, keine Textsuche: `ast` zählt `Import` und `ImportFrom`
    überall auf, ein `grep` nach `yfinance` hätte einen Import in einer
    Funktion oder unter anderem Namen verfehlt.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return {name.split(".")[0] for name in modules} | modules


def test_die_diagnose_kennt_keine_einzige_konkrete_quelle() -> None:
    """**Das Pflichtorakel „kein Netz" — als Inventar, nicht als Steckdose.**

    Der naheliegende Weg wäre, im Dateiprofil die Steckdose zuzuhalten und zu
    zählen, ob jemand hinausgeht. Er trägt hier nicht: `yfinance` telefoniert
    über `curl_cffi`, also über libcurl, und nicht über Pythons `socket`. Ein
    eingebauter Mutant, der mitten in der Diagnose `yf.Ticker(...).history()`
    rief, ließ genau dieses Orakel grün — gemessen wurde eine Leitung, die die
    Quelle gar nicht benutzt.

    Was tragfähig ist, ist die Abhängigkeit selbst: Wer keine konkrete Quelle
    kennt, kann keine anrufen. Die verbotene Liste wird dabei **aufgezählt**
    (jedes Modul in `app/providers/`, das keine Kaskade und keine Basis ist)
    und nicht geraten — ein neuer Anbieter steht damit von selbst darin.
    """
    infrastructure = {"__init__", "base", "composite_etf", "composite_market"}
    concrete_providers = {
        f"app.providers.{path.stem}"
        for path in (_APP / "providers").glob("*.py")
        if path.stem not in infrastructure
    }
    assert concrete_providers, "das Inventar der Anbieter ist leer — es misst nichts"

    forbidden = concrete_providers | {
        "yfinance",
        "curl_cffi",
        "requests",
        "httpx",
        "urllib",
        "urllib3",
        "aiohttp",
        "socket",
    }

    found = _imported_modules(_APP / "services" / "analyzer.py") & forbidden

    assert not found, f"die Diagnose kennt eine konkrete Quelle: {sorted(found)}"


# ─── Zuordnung ────────────────────────────────────────────────────────────────


def test_jede_konfigurierte_quelle_bekommt_eine_zeile() -> None:
    """**Die Rolle sagt, wonach gefragt wurde; die Quelle, wer geantwortet hat.**

    Ein fester Anbietername konnte beides nicht: Er behauptete eine Quelle, die
    im Profil vielleicht gar nicht steht.
    """
    analyzer = QuoteAnalyzer(
        {
            "resolvers": [_Resolver("yaml-file")],
            "quotes": [_Quotes("yaml-file", object())],
            "daily": [_Daily("yaml-file", _rows(3))],
            "etf_meta": [_Meta("yaml-file", EtfDetails(ter=0.2))],
        }
    )

    result = analyzer.analyze(isin="IE00B4L5Y983")

    assert [(stage.role, stage.source) for stage in result.stages] == [
        ("resolvers", "yaml-file"),
        ("quotes", "yaml-file"),
        ("daily", "yaml-file"),
        ("etf_meta", "yaml-file"),
    ]
    assert result.symbol == "EUNL.DE"


def test_die_reihenfolge_ist_die_der_konfiguration() -> None:
    """Ein Betreiber liest hier seine eigene Kette und soll sie wiedererkennen.

    Ohne diese Zusage stünde die Reihenfolge der **Messung** da — und die
    kippt, sobald eine Quelle schneller antwortet als eine frühere.
    """
    analyzer = QuoteAnalyzer(
        {
            "resolvers": [_Resolver("yaml-file")],
            "quotes": [_Quotes("online", None), _Quotes("yaml-file", object())],
        }
    )

    result = analyzer.analyze(symbol="EUNL.DE")

    assert [stage.source for stage in result.stages] == [
        "yaml-file",  # resolvers
        "online",
        "yaml-file",
    ]


# ─── Nicht gefragt ────────────────────────────────────────────────────────────


def test_eine_nicht_gefragte_quelle_meldet_das_auch() -> None:
    """**Der Unterschied, um den es geht.** Eine Kaskade hört beim Treffer auf.

    Die zweite Quelle mit `0 ms, ok` zu melden wäre richtig gemessen und falsch
    verstanden: Sie hat nicht schnell geantwortet, sie wurde nicht gefragt.
    """
    first = _Quotes("online", object())
    second = _Quotes("yaml-file", object())
    analyzer = QuoteAnalyzer(
        {"resolvers": [_Resolver("yaml-file")], "quotes": [first, second]}
    )

    stages = _stages(analyzer.analyze(symbol="EUNL.DE"))

    assert stages[("quotes", "online")].status == "ok"
    assert stages[("quotes", "yaml-file")].status == "skipped"
    assert second.calls == 0, "die zweite Quelle wurde trotz Treffer gefragt"


def test_ohne_treffer_kommt_die_zweite_quelle_dran() -> None:
    """Die Gegenprobe: Ohne sie wäre `skipped` auch grün, wenn nie jemand fällt."""
    analyzer = QuoteAnalyzer(
        {
            "resolvers": [_Resolver("yaml-file")],
            "quotes": [_Quotes("online", None), _Quotes("yaml-file", object())],
        }
    )

    stages = _stages(analyzer.analyze(symbol="EUNL.DE"))

    assert stages[("quotes", "online")].status == "empty"
    assert stages[("quotes", "yaml-file")].status == "ok"


# ─── Ausgänge ─────────────────────────────────────────────────────────────────


def test_ein_fehler_beendet_die_uebrigen_rollen_nicht() -> None:
    class _Boom(_Quotes):
        def fetch_quote(self, instrument):
            raise RuntimeError("boom")

    analyzer = QuoteAnalyzer(
        {
            "resolvers": [_Resolver("yaml-file")],
            "quotes": [_Boom("online")],
            "daily": [_Daily("yaml-file", _rows(2))],
        }
    )

    stages = _stages(analyzer.analyze(isin="IE00B4L5Y983"))

    assert stages[("quotes", "online")].status == "error"
    assert stages[("quotes", "online")].detail == "RuntimeError"
    assert stages[("daily", "yaml-file")].status == "ok", "die Analyse brach ab"


def test_ein_papier_ohne_boersensymbol_bricht_nicht_ab() -> None:
    """**Der Absturz aus dem Befund.** Eine `isin_only`-Identität ist kein Fehler.

    Vorher baute der Analyzer daraus einen `yf.Ticker` und bekam ein
    `ValueError` — die Route endete im `500`. Ohne festen Anbieter gibt es
    diesen Schritt nicht mehr.
    """
    bond = ResolvedInstrument(symbol="DE0001102531", isin="DE0001102531", kind="isin_only", type="bond")
    analyzer = QuoteAnalyzer(
        {"resolvers": [_Resolver("yaml-file", bond)], "quotes": [_Quotes("yaml-file", object())]}
    )

    result = analyzer.analyze(isin="DE0001102531")

    assert result.symbol == "DE0001102531"
    assert _stages(result)[("quotes", "yaml-file")].status == "ok"


def test_ein_nicht_gefundenes_papier_liefert_ein_teilergebnis() -> None:
    """Die Auflösung meldet `empty`, die übrigen Rollen bleiben ungefragt."""
    analyzer = QuoteAnalyzer(
        {
            "resolvers": [_Resolver("yaml-file", NotFound())],
            "quotes": [_Quotes("yaml-file", object())],
        }
    )

    result = analyzer.analyze(isin="XX0000000000")
    stages = _stages(result)

    assert stages[("resolvers", "yaml-file")].status == "empty"
    assert stages[("resolvers", "yaml-file")].detail == "NotFound"
    assert stages[("quotes", "yaml-file")].status == "skipped"
    assert result.symbol == "XX0000000000"


def test_ein_quellenausfall_ist_kein_leeres_ergebnis() -> None:
    """`Unavailable` sagt etwas anderes als „nichts gefunden".

    Wer die Diagnose aufruft, will genau das unterscheiden — und seit T-44 tut
    es der Rest der App auch.
    """
    analyzer = QuoteAnalyzer(
        {"resolvers": [_Resolver("openfigi", Unavailable(error="down"))]}
    )

    stage = _stages(analyzer.analyze(isin="IE00B4L5Y983"))[("resolvers", "openfigi")]

    assert stage.detail == "Unavailable"


def test_eine_leere_rolle_erzeugt_keine_zeile() -> None:
    """Was nicht konfiguriert ist, wird auch nicht behauptet.

    Eine Instanz ohne ETF-Metadaten bekommt keine `etf_meta`-Zeile mit
    `skipped` — sie hat diese Rolle nicht, und eine leere Zeile dafür wäre eine
    Aussage über eine Kette, die es nicht gibt.
    """
    analyzer = QuoteAnalyzer(
        {"resolvers": [_Resolver("yaml-file")], "quotes": [_Quotes("yaml-file", object())]}
    )

    result = analyzer.analyze(symbol="EUNL.DE")

    assert [stage.role for stage in result.stages] == ["resolvers", "quotes"]

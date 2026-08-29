"""Tests für den QuoteAnalyzer (externe Calls über Fakes)."""

from stockinfo_plugin.types import (
    NotFound,
    NotResponsible,
    Unavailable,
    Unsupported,
)

from app.providers.base import EtfDetails, ResolvedInstrument
from app.services.analyzer import QuoteAnalyzer


class _FakeResolver:
    """Liefert eine vorgegebene Resolution — auch die negativen Arten.

    ``None`` bleibt als Kurzschreibweise für „kenne ich nicht" erlaubt, damit
    die älteren Tests lesbar bleiben.
    """

    def __init__(self, resolved) -> None:
        self._resolved = NotFound() if resolved is None else resolved

    def handles(self, isin: str) -> bool:
        return True

    def resolve_isin(self, isin: str):
        return self._resolved


class _FakeEtf:
    def __init__(self, details: EtfDetails | None) -> None:
        self._details = details

    def is_responsible(self, isin: str) -> bool:
        return True

    def fetch_etf(self, isin: str, symbol: str | None = None) -> EtfDetails | None:
        return self._details


class _FakeFastInfo:
    last_price = 128.6
    currency = "EUR"


class _FakeTicker:
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self.fast_info = _FakeFastInfo()
        self.isin = "IE00B4L5Y983"

    def get_info(self) -> dict:
        return {"longName": "Test ETF"}

    def history(self, **kwargs):
        return [1, 2, 3]  # len() = "3 rows"


def _analyzer(resolved=None, details=None) -> QuoteAnalyzer:
    return QuoteAnalyzer(
        _FakeResolver(resolved or ResolvedInstrument(symbol="EUNL.DE", type="etf")),
        _FakeEtf(details or EtfDetails(ter=0.2)),
        ticker_factory=_FakeTicker,
    )


def test_analyze_per_isin_liefert_alle_stages() -> None:
    result = _analyzer().analyze(isin="IE00B4L5Y983")
    stages = {s.stage: s for s in result.stages}
    assert set(stages) >= {"openfigi", "fast_info", "get_info", "isin", "history", "justetf"}
    assert stages["openfigi"].status == "ok"
    assert stages["history"].detail == "3 rows"
    assert result.symbol == "EUNL.DE"
    assert result.total >= 0.0


def test_analyze_per_symbol_ueberspringt_openfigi() -> None:
    result = _analyzer().analyze(symbol="AAPL")
    stages = {s.stage: s for s in result.stages}
    assert stages["openfigi"].status == "skipped"
    assert stages["fast_info"].status == "ok"


def test_stage_fehler_bricht_kette_nicht_ab() -> None:
    class _BoomTicker(_FakeTicker):
        def get_info(self) -> dict:
            raise RuntimeError("boom")

    analyzer = QuoteAnalyzer(
        _FakeResolver(ResolvedInstrument(symbol="EUNL.DE", type="etf")),
        _FakeEtf(None),
        ticker_factory=_BoomTicker,
    )
    result = analyzer.analyze(isin="IE00B4L5Y983")
    stages = {s.stage: s for s in result.stages}
    assert stages["get_info"].status == "error"
    assert stages["get_info"].detail == "RuntimeError"
    assert stages["isin"].status == "ok"  # Kette läuft weiter


def test_nicht_aufloesbare_isin_liefert_teilergebnis() -> None:
    analyzer = QuoteAnalyzer(_FakeResolver(None), _FakeEtf(None), ticker_factory=_FakeTicker)
    result = analyzer.analyze(isin="XX0000000000")
    stages = {s.stage: s for s in result.stages}
    assert stages["openfigi"].status == "empty"
    assert stages["fast_info"].status == "skipped"


def test_analyse_ueberlebt_ein_unbekanntes_papier() -> None:
    """Der Diagnose-Endpunkt darf an einer negativen Antwort nicht zerbrechen.

    Seit T-20 liefert der Resolver `NotFound` statt ``None``. Der Analyzer
    prüfte weiter auf ``None`` und griff danach auf `.symbol` zu — für ein
    unbekanntes Papier endete `/analyze` damit in einem 500, obwohl er gerade
    dann ein Teilergebnis liefern soll.
    """
    analyzer = QuoteAnalyzer(_FakeResolver(NotFound()), _FakeEtf(None))

    ergebnis = analyzer.analyze(isin="XX0000000000")

    stages = {stage.stage: stage for stage in ergebnis.stages}
    assert stages["openfigi"].status == "empty"
    # Der Analyzer fällt auf die ISIN als Anzeigenamen zurück — er liefert ein
    # Teilergebnis, statt abzubrechen. Genau das ist sein Zweck.
    assert ergebnis.symbol == "XX0000000000"
    assert stages["fast_info"].status == "skipped"


def test_analyse_meldet_einen_quellenausfall_als_fehler() -> None:
    """`Unavailable` ist kein leeres Ergebnis — es ist ein Fehler.

    Wer die Diagnose aufruft, will genau das sehen: nicht „nichts gefunden",
    sondern „die Quelle war nicht erreichbar".
    """
    analyzer = QuoteAnalyzer(
        _FakeResolver(Unavailable(error="openfigi: down")), _FakeEtf(None)
    )

    ergebnis = analyzer.analyze(isin="IE00B4L5Y983")

    stages = {stage.stage: stage for stage in ergebnis.stages}
    assert stages["openfigi"].status == "error"
    assert "openfigi" in (stages["openfigi"].detail or "")


def test_analyse_meldet_eine_unzustaendige_kette_als_leer() -> None:
    """Niemand war zuständig — nachgesehen hat auch niemand, aber kaputt ist nichts."""
    analyzer = QuoteAnalyzer(
        _FakeResolver(NotResponsible(reason="keine zuständige Quelle")), _FakeEtf(None)
    )

    stages = {s.stage: s for s in analyzer.analyze(isin="XX0000000000").stages}

    assert stages["openfigi"].status == "empty"


def test_analyse_nennt_die_nicht_gefuehrte_gattung() -> None:
    """Die fünfte Antwortart, in dem Endpunkt, dessen Zweck der Grund ist.

    **Zwei Aussagen, und beide sind nötig.** `empty` und nicht `error`: Die
    Kette hat einwandfrei gearbeitet, sie hat das Papier sogar erkannt — ein
    `error` schickte den Betreiber auf die Suche nach einer Störung, die es
    nicht gibt. Und das Detail nennt die **Gattung**: Ohne eigene Zeile fiele
    der Fall in das leere `empty` ganz unten, richtig in der Farbe und stumm
    im Grund.
    """
    analyzer = QuoteAnalyzer(
        _FakeResolver(Unsupported(instrument_type="index")), _FakeEtf(None)
    )

    stages = {s.stage: s for s in analyzer.analyze(isin="DE0008469008").stages}

    assert stages["openfigi"].status == "empty", "kein Ausfall — die Kette lief"
    assert "index" in (stages["openfigi"].detail or ""), (
        "ohne die Gattung im Detail ist die Diagnose an dieser Stelle stumm"
    )

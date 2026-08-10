"""Tests für den QuoteAnalyzer (externe Calls über Fakes)."""

from app.providers.base import EtfDetails, ResolvedInstrument
from app.services.analyzer import QuoteAnalyzer


class _FakeResolver:
    def __init__(self, resolved: ResolvedInstrument | None) -> None:
        self._resolved = resolved

    def resolve_isin(self, isin: str) -> ResolvedInstrument | None:
        return self._resolved


class _FakeEtf:
    def __init__(self, details: EtfDetails | None) -> None:
        self._details = details

    def fetch_etf(self, isin: str) -> EtfDetails | None:
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

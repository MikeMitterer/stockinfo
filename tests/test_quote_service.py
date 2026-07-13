"""Tests für die Orchestrierung im QuoteService (Provider gemockt)."""

import pytest

from app.providers.base import EtfDetails, RawQuote, ResolvedInstrument
from app.services.quote_service import (
    InstrumentNotFoundError,
    QuoteService,
    QuoteUnavailableError,
    annualized_volatility,
)


class FakeQuoteProvider:
    """Liefert einen vorgegebenen RawQuote (oder None)."""

    def __init__(self, raw: RawQuote | None) -> None:
        self._raw = raw

    def fetch_quote(self, symbol: str) -> RawQuote | None:
        return self._raw


class FakeEtfProvider:
    """Liefert vorgegebene ETF-Details (oder None)."""

    def __init__(self, details: EtfDetails | None) -> None:
        self._details = details

    def fetch_etf(self, isin: str) -> EtfDetails | None:
        return self._details


class FakeDailyQuoteProvider:
    """Wie FakeQuoteProvider, liefert zusätzlich Tages-Schlusskurse."""

    def __init__(self, raw: RawQuote | None, closes: list[float]) -> None:
        self._raw = raw
        self._closes = closes

    def fetch_quote(self, symbol: str) -> RawQuote | None:
        return self._raw

    def fetch_daily_closes(self, symbol: str, start: str | None = None) -> list[dict]:
        return [{"date": f"d{i}", "close": c, "currency": "EUR"} for i, c in enumerate(self._closes)]


class FakeResolver:
    """Liefert ein vorgegebenes ResolvedInstrument (oder None)."""

    def __init__(self, resolved: ResolvedInstrument | None) -> None:
        self._resolved = resolved

    def resolve_isin(self, isin: str) -> ResolvedInstrument | None:
        return self._resolved


def _etf_quote() -> RawQuote:
    return RawQuote(
        symbol="VGWL.DE",
        price=160.98,
        quote_time="2026-07-12T17:35:00+00:00",
        currency="EUR",
        volume=1000,
        type="etf",
    )


def test_etf_wird_mit_justetf_angereichert() -> None:
    details = EtfDetails(ter=0.19, provider="Vanguard", replication="Physical")
    service = QuoteService(
        FakeQuoteProvider(_etf_quote()),
        FakeEtfProvider(details),
        FakeResolver(
            ResolvedInstrument(symbol="VGWL.DE", isin="IE00B3RBWM25", type="etf")
        ),
    )

    result = service.get_quote_by_isin("IE00B3RBWM25")

    assert result.type == "etf"
    assert result.ter == 0.19
    assert result.provider == "Vanguard"
    assert result.currency == "EUR"
    assert result.source == "yfinance+justetf"


def test_aktie_wird_nicht_angereichert() -> None:
    stock = RawQuote(
        symbol="BRYN.DE",
        price=430.05,
        quote_time="2026-07-12T17:35:00+00:00",
        currency="EUR",
        type="stock",
    )
    service = QuoteService(
        FakeQuoteProvider(stock),
        FakeEtfProvider(EtfDetails(ter=0.99)),  # würde ignoriert
        FakeResolver(
            ResolvedInstrument(symbol="BRYN.DE", isin="US0846707026", type="stock")
        ),
    )

    result = service.get_quote_by_isin("US0846707026")

    assert result.type == "stock"
    assert result.ter is None
    assert result.source == "yfinance"


def test_unbekannte_isin_wirft_not_found() -> None:
    service = QuoteService(
        FakeQuoteProvider(_etf_quote()),
        FakeEtfProvider(None),
        FakeResolver(None),
    )

    with pytest.raises(InstrumentNotFoundError):
        service.get_quote_by_isin("XX0000000000")


def test_kein_kurs_wirft_unavailable() -> None:
    service = QuoteService(
        FakeQuoteProvider(None),
        FakeEtfProvider(None),
        FakeResolver(ResolvedInstrument(symbol="NOPE.DE")),
    )

    with pytest.raises(QuoteUnavailableError):
        service.get_quote_by_symbol("NOPE.DE")


def test_gbp_pence_wird_originalgetreu_uebernommen() -> None:
    pence = RawQuote(
        symbol="EQQQ.L",
        price=54211.0,
        quote_time="2026-07-12T17:35:00+00:00",
        currency="GBp",
        type="etf",
    )
    service = QuoteService(
        FakeQuoteProvider(pence),
        FakeEtfProvider(None),
        FakeResolver(ResolvedInstrument(symbol="EQQQ.L")),
    )

    result = service.get_quote_by_symbol("EQQQ.L")

    assert result.currency == "GBp"
    assert result.price == 54211.0


def test_etf_uebernimmt_volatilitaet_und_thesaurierend_von_justetf() -> None:
    details = EtfDetails(ter=0.19, volatility=9.95, accumulating=True)
    service = QuoteService(
        FakeQuoteProvider(_etf_quote()),
        FakeEtfProvider(details),
        FakeResolver(
            ResolvedInstrument(symbol="VGWL.DE", isin="IE00B3RBWM25", type="etf")
        ),
    )

    result = service.get_quote_by_isin("IE00B3RBWM25")

    assert result.volatility == 9.95
    assert result.accumulating is True


def test_volatilitaet_wird_aus_tageskursen_berechnet_wenn_justetf_fehlt() -> None:
    stock = RawQuote(
        symbol="AAPL",
        price=300.0,
        quote_time="2026-07-12T17:35:00+00:00",
        currency="USD",
        type="stock",
    )
    closes = [100.0, 101.0, 99.5, 102.0, 100.5, 103.0, 101.5]
    service = QuoteService(
        FakeDailyQuoteProvider(stock, closes),
        FakeEtfProvider(None),
        FakeResolver(ResolvedInstrument(symbol="AAPL", type="stock")),
    )

    result = service.get_quote_by_symbol("AAPL")

    assert result.volatility == annualized_volatility(closes)
    assert result.volatility is not None
    assert result.accumulating is None  # Aktie → keine Ausschüttungspolitik


def test_annualized_volatility_zu_wenig_daten_ist_none() -> None:
    assert annualized_volatility([100.0, 101.0]) is None
    assert annualized_volatility([]) is None

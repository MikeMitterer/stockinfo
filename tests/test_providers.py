"""Tests der Provider-Parsing-Logik (externe Aufrufe gemockt, kein Netz)."""

import app.providers.justetf_provider as justetf_module
import app.providers.yfinance_provider as yfinance_module
from app.providers.justetf_provider import JustEtfProvider
from app.providers.openfigi_provider import OpenFigiClient
from app.providers.yfinance_provider import YFinanceProvider


# ─── OpenFIGI ─────────────────────────────────────────────────────────────────


def test_openfigi_extract_ticker() -> None:
    data = [{"data": [{"ticker": "VGWL", "exchCode": "GT"}]}]
    assert OpenFigiClient._extract_ticker(data) == "VGWL"


def test_openfigi_extract_ticker_leer() -> None:
    assert OpenFigiClient._extract_ticker([{"warning": "No identifier found."}]) is None
    assert OpenFigiClient._extract_ticker([]) is None
    assert OpenFigiClient._extract_ticker({}) is None


# ─── justETF ──────────────────────────────────────────────────────────────────


def test_justetf_mappt_dict_felder(monkeypatch) -> None:
    overview = {
        "name": "Vanguard FTSE All-World",
        "ter": 0.19,
        "fund_provider": "Vanguard",
        "replication": "Physical(Optimized sampling)",
        "fund_size_eur": 22638.0,
        "fund_currency": "USD",
        "volatility_1y": 9.95,
        "distribution_policy": "Distributing",
    }
    monkeypatch.setattr(
        justetf_module.justetf_scraping, "get_etf_overview", lambda isin: overview
    )

    details = JustEtfProvider().fetch_etf("IE00B3RBWM25")

    assert details is not None
    assert details.ter == 0.19
    assert details.provider == "Vanguard"
    assert details.fund_size == 22638.0
    assert details.volatility == 9.95
    assert details.accumulating is False


def test_justetf_thesaurierend_wird_erkannt(monkeypatch) -> None:
    overview = {"name": "iShares Core MSCI World", "distribution_policy": "Accumulating"}
    monkeypatch.setattr(
        justetf_module.justetf_scraping, "get_etf_overview", lambda isin: overview
    )

    details = JustEtfProvider().fetch_etf("IE00B4L5Y983")

    assert details is not None
    assert details.accumulating is True


def test_justetf_fehler_gibt_none(monkeypatch) -> None:
    def boom(isin: str) -> dict:
        raise RuntimeError("scrape failed")

    monkeypatch.setattr(justetf_module.justetf_scraping, "get_etf_overview", boom)
    assert JustEtfProvider().fetch_etf("IE00B3RBWM25") is None


def test_justetf_ueberspringt_nicht_europaeische_isin(monkeypatch) -> None:
    """US-/nicht-europäische ISINs werden gar nicht erst gescraped."""
    calls: list[str] = []

    def spy(isin: str) -> dict:
        calls.append(isin)
        return {"name": "sollte nicht passieren"}

    monkeypatch.setattr(justetf_module.justetf_scraping, "get_etf_overview", spy)

    assert JustEtfProvider().fetch_etf("US78462F1030") is None  # SPY (US)
    assert calls == []  # kein Scrape-Aufruf


def test_justetf_versucht_europaeische_isin(monkeypatch) -> None:
    """Europäische UCITS-ISIN (IE/LU/…) wird gescraped."""
    calls: list[str] = []

    def overview(isin: str) -> dict:
        calls.append(isin)
        return {"name": "iShares", "ter": 0.2}

    monkeypatch.setattr(justetf_module.justetf_scraping, "get_etf_overview", overview)

    details = JustEtfProvider().fetch_etf("IE00B4L5Y983")
    assert details is not None
    assert calls == ["IE00B4L5Y983"]


def test_is_european_isin() -> None:
    from app.providers.justetf_provider import is_european_isin

    assert is_european_isin("IE00B4L5Y983") is True
    assert is_european_isin("LU0274208692") is True
    assert is_european_isin("ie00b4l5y983") is True  # case-insensitive
    assert is_european_isin("US78462F1030") is False
    assert is_european_isin("CA0679011084") is False
    assert is_european_isin("") is False


# ─── yfinance ─────────────────────────────────────────────────────────────────


class FakeFastInfo:
    """Imitiert yfinance FastInfo (nur Attribut-Zugriff)."""

    last_price = 160.98
    currency = "EUR"
    exchange = "GER"
    last_volume = 14403
    quote_type = "ETF"


class FakeTicker:
    """Imitiert yfinance Ticker."""

    fast_info = FakeFastInfo()
    isin = "IE00B3RBWM25"

    def get_info(self) -> dict:
        return {"longName": "Vanguard FTSE All-World UCITS ETF"}


def test_yfinance_fetch_quote(monkeypatch) -> None:
    monkeypatch.setattr(yfinance_module.yf, "Ticker", lambda symbol: FakeTicker())

    quote = YFinanceProvider().fetch_quote("VGWL.DE")

    assert quote is not None
    assert quote.price == 160.98
    assert quote.currency == "EUR"
    assert quote.type == "etf"
    assert quote.volume == 14403
    assert quote.name == "Vanguard FTSE All-World UCITS ETF"
    assert quote.isin == "IE00B3RBWM25"


def test_yfinance_ohne_preis_gibt_none(monkeypatch) -> None:
    class NoPrice(FakeTicker):
        fast_info = type("F", (), {"last_price": None})()

    monkeypatch.setattr(yfinance_module.yf, "Ticker", lambda symbol: NoPrice())
    assert YFinanceProvider().fetch_quote("VGWL.DE") is None


def test_yfinance_helfer() -> None:
    provider = YFinanceProvider()
    assert provider._as_int("42") == 42
    assert provider._as_int(None) is None
    assert provider._as_int("x") is None
    assert provider._quote_time({"regularMarketTime": 0}).startswith("1970-01-01")
    assert provider._safe_isin(FakeTicker()) == "IE00B3RBWM25"


def test_yfinance_fetch_fx_rate(monkeypatch) -> None:
    class _FxFast:
        last_price = 1.1538

    class _FxTicker:
        fast_info = _FxFast()

    captured = {}

    def fake_ticker(symbol):
        captured["symbol"] = symbol
        return _FxTicker()

    monkeypatch.setattr(yfinance_module.yf, "Ticker", fake_ticker)

    rate = YFinanceProvider().fetch_fx_rate("EUR", "USD")

    assert rate == 1.1538
    assert captured["symbol"] == "EURUSD=X"


def test_yfinance_fetch_fx_rate_ohne_wert_gibt_none(monkeypatch) -> None:
    class _NoRate:
        fast_info = type("F", (), {"last_price": None})()

    monkeypatch.setattr(yfinance_module.yf, "Ticker", lambda s: _NoRate())
    assert YFinanceProvider().fetch_fx_rate("EUR", "USD") is None

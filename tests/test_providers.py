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
    }
    monkeypatch.setattr(
        justetf_module.justetf_scraping, "get_etf_overview", lambda isin: overview
    )

    details = JustEtfProvider().fetch_etf("IE00B3RBWM25")

    assert details is not None
    assert details.ter == 0.19
    assert details.provider == "Vanguard"
    assert details.fund_size == 22638.0


def test_justetf_fehler_gibt_none(monkeypatch) -> None:
    def boom(isin: str) -> dict:
        raise RuntimeError("scrape failed")

    monkeypatch.setattr(justetf_module.justetf_scraping, "get_etf_overview", boom)
    assert JustEtfProvider().fetch_etf("IE00B3RBWM25") is None


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

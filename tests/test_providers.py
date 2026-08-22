"""Tests der Provider-Parsing-Logik (externe Aufrufe gemockt, kein Netz)."""

import pytest

import app.providers.justetf_provider as justetf_module
import app.providers.yfinance_etf_provider as yfinance_etf_module
import app.providers.yfinance_provider as yfinance_module
from app.providers.base import EtfDetails
from app.providers.composite_etf import CompositeEtfEnricher
from app.providers.justetf_provider import JustEtfProvider
from app.providers.openfigi_provider import OpenFigiClient
from app.providers.yfinance_etf_provider import YFinanceEtfEnricher
from app.providers.yfinance_provider import YFinanceProvider


# ─── OpenFIGI ─────────────────────────────────────────────────────────────────


def test_openfigi_extract_ticker() -> None:
    data = [{"data": [{"ticker": "VGWL", "exchCode": "GT"}]}]
    assert OpenFigiClient._extract_ticker(data) == "VGWL"


def test_openfigi_extract_ticker_leer() -> None:
    assert OpenFigiClient._extract_ticker([{"warning": "No identifier found."}]) is None
    assert OpenFigiClient._extract_ticker([]) is None
    assert OpenFigiClient._extract_ticker({}) is None


def test_zustaendigkeit_ohne_isin_haengt_an_boerse_und_waehrung() -> None:
    """Ohne ISIN muss die Zuständigkeit trotzdem beantwortbar sein.

    Für `XIC.TO` nennt yfinance keine ISIN. Bisher griff dann der
    konservative Pfad, und der Anbieter blieb leer — obwohl `.TO` in CAD
    ersichtlich nicht europäisch ist und justETF dieses Papier gar nicht
    führt. Die Frage „führt diese Quelle das Papier?" braucht die ISIN nicht,
    wenn Börse und Währung sie schon beantworten.
    """
    justetf = JustEtfProvider()
    yahoo = YFinanceEtfEnricher()

    assert justetf.is_responsible(None, exchange="Toronto", currency="CAD") is False
    assert yahoo.is_responsible(None, exchange="Toronto", currency="CAD") is True

    assert justetf.is_responsible(None, exchange="Xetra", currency="EUR") is True
    assert yahoo.is_responsible(None, exchange="Xetra", currency="EUR") is False


def test_zustaendigkeit_ohne_jeden_hinweis_bleibt_konservativ() -> None:
    """Weder ISIN noch Börse noch Währung: dann weiß niemand etwas.

    Der Schutz des gespeicherten Standes gewinnt im Zweifel — ein
    europäischer ETF, dessen ISIN gerade fehlt, darf seine Kennzahlen nicht
    verlieren.
    """
    assert JustEtfProvider().is_responsible(None) is False
    assert YFinanceEtfEnricher().is_responsible(None) is False


def test_die_isin_schlaegt_boerse_und_waehrung() -> None:
    """Ist die ISIN da, entscheidet sie — sie ist die genauere Angabe.

    Ein irischer UCITS-ETF an der Londoner Börse in GBp bleibt ein Fall für
    justETF, auch wenn die Börse nach etwas anderem aussieht.
    """
    assert (
        JustEtfProvider().is_responsible(
            "IE00B4L5Y983", exchange="London LSE", currency="GBp"
        )
        is True
    )
    assert (
        JustEtfProvider().is_responsible(
            "US9229087690", exchange="Xetra", currency="EUR"
        )
        is False
    )


def test_openfigi_verwirft_einen_bloomberg_bezeichner() -> None:
    """Ein FIGI-Ticker ist nicht immer ein Symbol.

    Gemessen am 2026-08-21: `CA78012H5675` (Vorzugsaktie der Royal Bank) liefert
    an `XTSE` genau einen Treffer, `RY V3.65 PERP BB`. Mit Börsensuffix wird
    daraus `RY V3.65 PERP BB.TO`, und yfinance antwortet 404. Weil OpenFIGI
    „getroffen" hatte, kam der Yahoo-Fallback nie an die Reihe.
    """
    data = [{"data": [{"ticker": "RY V3.65 PERP BB", "exchCode": "TORONTO"}]}]
    assert OpenFigiClient._extract_ticker(data) is None


def test_openfigi_behaelt_uebliche_symbolzeichen() -> None:
    """Punkt, Bindestrich und Ziffern kommen in echten Symbolen vor.

    `BRK-B` (US), `RY.PR.J` (Toronto), `7203` (Tokio) — der Filter darf nur
    aussortieren, was als Yahoo-Symbol nicht taugt.
    """
    for ticker in ("BRK-B", "RY.PR.J", "7203", "VGWL"):
        data = [{"data": [{"ticker": ticker}]}]
        assert OpenFigiClient._extract_ticker(data) == ticker


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
        justetf_module.justetf_scraping, "get_etf_overview", lambda isin, **kw: overview
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
        justetf_module.justetf_scraping, "get_etf_overview", lambda isin, **kw: overview
    )

    details = JustEtfProvider().fetch_etf("IE00B4L5Y983")

    assert details is not None
    assert details.accumulating is True


def test_justetf_fehler_gibt_none(monkeypatch) -> None:
    def boom(isin: str, **kw: object) -> dict:
        raise RuntimeError("scrape failed")

    monkeypatch.setattr(justetf_module.justetf_scraping, "get_etf_overview", boom)
    assert JustEtfProvider().fetch_etf("IE00B3RBWM25") is None


def test_justetf_liefert_domizil_und_fondswaehrung(monkeypatch) -> None:
    overview = {
        "name": "iShares Core MSCI World",
        "fund_domicile": "Ireland",
        "fund_currency": "USD",
    }
    monkeypatch.setattr(
        justetf_module.justetf_scraping, "get_etf_overview", lambda isin, **kw: overview
    )

    details = JustEtfProvider().fetch_etf("IE00B4L5Y983")

    assert details is not None
    assert details.fund_domicile == "Ireland"
    assert details.fund_currency == "USD"


def test_justetf_ueberspringt_nicht_europaeische_isin(monkeypatch) -> None:
    """US-/nicht-europäische ISINs werden gar nicht erst gescraped."""
    calls: list[str] = []

    def spy(isin: str, **kw: object) -> dict:
        calls.append(isin)
        return {"name": "sollte nicht passieren"}

    monkeypatch.setattr(justetf_module.justetf_scraping, "get_etf_overview", spy)

    assert JustEtfProvider().fetch_etf("US78462F1030") is None  # SPY (US)
    assert calls == []  # kein Scrape-Aufruf


def test_justetf_holt_den_gettex_kurs_nicht_mit(monkeypatch) -> None:
    """Der Gettex-Kurs kommt sonst per Extra-Request mit und wird verworfen.

    Der Kurs stammt von yfinance; justETF wird nur für die ETF-Extras befragt.
    Gemessen an `IE00B4L5Y983` kostete der ungenutzte Abruf rund die Hälfte der
    Scrape-Zeit — Median 0,99 s mit, 0,53 s ohne — und das bei jedem Refresh
    und jedem Papier.
    """
    aufrufe: list[dict] = []

    def spion(isin: str, **kw: object) -> dict:
        aufrufe.append(dict(kw))
        return {"name": "iShares Core MSCI World", "ter": 0.2}

    monkeypatch.setattr(justetf_module.justetf_scraping, "get_etf_overview", spion)

    JustEtfProvider().fetch_etf("IE00B4L5Y983")

    assert aufrufe == [{"include_gettex": False}]


def test_justetf_versucht_europaeische_isin(monkeypatch) -> None:
    """Europäische UCITS-ISIN (IE/LU/…) wird gescraped."""
    calls: list[str] = []

    def overview(isin: str, **kw: object) -> dict:
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


def test_unbekannte_ausschuettungspolitik_bleibt_unbekannt(monkeypatch) -> None:
    """Was justETF nicht als bekannt meldet, darf keine Aussage werden.

    Die Regel lautete „beginnt mit accumul → thesaurierend, sonst
    ausschüttend". Damit wurde jeder neue oder unerwartete Providerwert — eine
    Umbenennung, eine Übersetzung, ein leeres Feld mit Leerzeichen — als
    belastbares „ausschüttend" gespeichert. Die Dokumentation der Methode
    versprach an dieser Stelle bereits `None`; nur der Code hielt sich nicht
    daran.

    `None` heißt „nicht gepflegt" und lässt sich von Hand nachtragen; ein
    falsches `False` sieht wie eine gesicherte Angabe aus.
    """
    for politik in ("Thesaurierend", "unbekannt", "n/a", "Acc.", "-", "   "):
        monkeypatch.setattr(
            justetf_module.justetf_scraping,
            "get_etf_overview",
            lambda isin, **kw: {"distribution_policy": politik},
        )

        details = JustEtfProvider().fetch_etf("IE00B3RBWM25")

        assert details is not None
        assert details.accumulating is None, f"'{politik}' ist keine Aussage"


def test_bekannte_ausschuettungspolitik_wird_unabhaengig_von_schreibweise_erkannt(
    monkeypatch,
) -> None:
    """Gross-/Kleinschreibung und Leerraum sind Formatierung, keine Bedeutung."""
    faelle = {
        "Accumulating": True,
        "accumulating": True,
        "  ACCUMULATING ": True,
        "Distributing": False,
        "distributing": False,
        "  DISTRIBUTING ": False,
    }
    for politik, erwartet in faelle.items():
        monkeypatch.setattr(
            justetf_module.justetf_scraping,
            "get_etf_overview",
            lambda isin, **kw: {"distribution_policy": politik},
        )

        details = JustEtfProvider().fetch_etf("IE00B3RBWM25")

        assert details is not None
        assert details.accumulating is erwartet, politik


class _FakeTicker(FakeTicker):
    """Wie `FakeTicker`, nur mit frei wählbarem Kurs."""

    def __init__(self, price: float) -> None:
        self.fast_info = type(
            "F", (), {"last_price": price, "currency": "EUR", "last_volume": 1,
                      "exchange": "GER", "quote_type": "ETF"}
        )()


@pytest.mark.parametrize("kaputt", [float("nan"), float("inf"), float("-inf"), 0.0, -1.5])
def test_unbrauchbare_kurse_werden_verworfen(monkeypatch, kaputt) -> None:
    """Nicht jeder Zahlenwert ist ein Kurs.

    Geprüft wurde bisher nur gegen `None`. `NaN` und `Infinity` überstehen
    Pydantic als float, landen in SQLite und brechen spätestens bei strikter
    JSON-Serialisierung mit einem 500. Ein Kurs von 0 oder darunter ist
    fachlich ebenso wenig ein Kurs — er würde Renditen und Volatilität
    verfälschen, statt sie als fehlend auszuweisen.
    """
    monkeypatch.setattr(
        yfinance_module.yf, "Ticker", lambda symbol: _FakeTicker(price=kaputt)
    )

    assert YFinanceProvider().fetch_quote("VGWL.DE") is None


@pytest.mark.parametrize("kaputt", [float("nan"), float("inf"), 0.0, -1.0])
def test_unbrauchbare_wechselkurse_werden_verworfen(monkeypatch, kaputt) -> None:
    monkeypatch.setattr(
        yfinance_module.yf, "Ticker", lambda symbol: _FakeTicker(price=kaputt)
    )

    assert YFinanceProvider().fetch_fx_rate("EUR", "USD") is None


def test_brauchbarer_kurs_kommt_durch(monkeypatch) -> None:
    """Die Gegenrichtung — sonst wäre die Prüfung ein stiller Totalausfall."""
    monkeypatch.setattr(
        yfinance_module.yf, "Ticker", lambda symbol: _FakeTicker(price=160.98)
    )

    quote = YFinanceProvider().fetch_quote("VGWL.DE")

    assert quote is not None
    assert quote.price == 160.98
    assert YFinanceProvider().fetch_fx_rate("EUR", "USD") == 160.98


# ─── yfinance als ETF-Quelle (nicht-europäische Papiere) ──────────────────────


class _FakeFundsTicker:
    """Ersetzt ``yf.Ticker`` für den ETF-Enricher."""

    def __init__(self, family: str | None = "Vanguard", boom: bool = False) -> None:
        self._family = family
        self._boom = boom

    @property
    def info(self) -> dict:
        if self._boom:
            raise RuntimeError("Yahoo antwortet nicht")
        return {"fundFamily": self._family, "quoteType": "ETF", "currency": "USD"}


def test_yfinance_etf_ist_fuer_europaeische_isins_nicht_zustaendig() -> None:
    """Dort führt justETF das Papier — zwei Quellen für dasselbe Feld wären eine zu viel."""
    enricher = YFinanceEtfEnricher()

    assert enricher.is_responsible("IE00B4L5Y983") is False
    assert enricher.is_responsible("DE0007164600") is False


def test_yfinance_etf_ist_fuer_us_und_kanada_zustaendig() -> None:
    enricher = YFinanceEtfEnricher()

    assert enricher.is_responsible("US9229087690") is True
    assert enricher.is_responsible("CA46434V6817") is True


def test_yfinance_etf_liefert_den_anbieter(monkeypatch) -> None:
    """Der Anbieter kommt verlässlich — mehr wird bewusst nicht übernommen.

    `ter` und `fund_size` bleiben leer: yfinance nennt die Kostenquote je nach
    Feld als Prozent (0.03) oder als Anteil (0.0003), und das Fondsvolumen in
    Landeswährung, während das Modell Mio. EUR erwartet. Ein falscher Wert wäre
    hier schlimmer als keiner — er verdeckt einen von Hand nachgetragenen,
    statt die Lücke offen zu lassen (siehe `apply_overrides`).
    """
    monkeypatch.setattr(
        yfinance_etf_module.yf, "Ticker", lambda symbol: _FakeFundsTicker("Vanguard")
    )

    details = YFinanceEtfEnricher().fetch_etf("US9229087690", symbol="VTI")

    assert details is not None
    assert details.provider == "Vanguard"
    assert details.ter is None
    assert details.fund_size is None
    assert details.source == "yfinance"


def test_yfinance_etf_ohne_anbieter_ist_trotzdem_eine_antwort(monkeypatch) -> None:
    """„Abgefragt, nichts gefunden" ist eine Aussage — „nicht erreichbar" nicht.

    Nur der Unterschied zwischen beiden entscheidet, ob `metadata_complete`
    trägt. Käme hier ``None`` zurück, bliebe ein US-ETF ohne Anbieterangabe
    dauerhaft unvollständig und damit ohne `source`.
    """
    monkeypatch.setattr(
        yfinance_etf_module.yf, "Ticker", lambda symbol: _FakeFundsTicker(None)
    )

    details = YFinanceEtfEnricher().fetch_etf("US9229087690", symbol="VTI")

    assert details is not None
    assert details.provider is None


def test_yfinance_etf_fehler_liefert_none(monkeypatch) -> None:
    monkeypatch.setattr(
        yfinance_etf_module.yf, "Ticker", lambda symbol: _FakeFundsTicker(boom=True)
    )

    assert YFinanceEtfEnricher().fetch_etf("US9229087690", symbol="VTI") is None


def test_yfinance_etf_ohne_symbol_liefert_nichts(monkeypatch) -> None:
    """Yahoo kennt keine ISINs — ohne Symbol ist nichts abzufragen."""
    monkeypatch.setattr(
        yfinance_etf_module.yf, "Ticker", lambda symbol: _FakeFundsTicker("Vanguard")
    )

    assert YFinanceEtfEnricher().fetch_etf("US9229087690") is None


# ─── Zusammenspiel der ETF-Quellen ────────────────────────────────────────────


class _StubEnricher:
    """Zuständigkeit und Antwort getrennt vorgebbar."""

    def __init__(self, responsible: bool, details: EtfDetails | None) -> None:
        self._responsible = responsible
        self._details = details
        self.gefragt = 0

    def is_responsible(
        self,
        isin: str | None,
        *,
        exchange: str | None = None,
        currency: str | None = None,
    ) -> bool:
        return self._responsible

    def fetch_etf(
        self,
        isin: str | None,
        symbol: str | None = None,
        *,
        exchange: str | None = None,
        currency: str | None = None,
    ) -> EtfDetails | None:
        self.gefragt += 1
        return self._details


def test_composite_fragt_nur_die_zustaendige_quelle() -> None:
    europaeisch = _StubEnricher(True, EtfDetails(provider="iShares"))
    uebersee = _StubEnricher(False, EtfDetails(provider="Vanguard"))
    composite = CompositeEtfEnricher(europaeisch, uebersee)

    details = composite.fetch_etf("IE00B4L5Y983")

    assert details is not None
    assert details.provider == "iShares"
    assert uebersee.gefragt == 0  # nicht zuständig, also gar nicht erst gefragt


def test_composite_ist_zustaendig_wenn_eine_quelle_es_ist() -> None:
    composite = CompositeEtfEnricher(
        _StubEnricher(False, None), _StubEnricher(True, EtfDetails())
    )

    assert composite.is_responsible("US9229087690") is True


def test_composite_ohne_zustaendige_quelle_meldet_das_ehrlich() -> None:
    """Damit `_build` weiß: Hier gibt es nichts zu holen und nichts zu schützen."""
    composite = CompositeEtfEnricher(
        _StubEnricher(False, None), _StubEnricher(False, None)
    )

    assert composite.is_responsible("JP3633400001") is False
    assert composite.fetch_etf("JP3633400001") is None


def test_composite_geht_bei_ausfall_zur_naechsten_zustaendigen_quelle() -> None:
    """Ein Ausfall der ersten Quelle darf eine zweite nicht verhindern."""
    ausgefallen = _StubEnricher(True, None)
    ersatz = _StubEnricher(True, EtfDetails(provider="Vanguard"))
    composite = CompositeEtfEnricher(ausgefallen, ersatz)

    details = composite.fetch_etf("US9229087690")

    assert details is not None
    assert details.provider == "Vanguard"
    assert ausgefallen.gefragt == 1

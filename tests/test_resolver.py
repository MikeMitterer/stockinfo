"""Tests für die ISIN-Auflösung (OpenFIGI-Client gemockt)."""

from app.resolver import (
    EXCHANGES,
    CompositeResolver,
    OpenFigiResolver,
    YFinanceResolver,
)
from app.providers.base import ResolvedInstrument
from app.providers.openfigi_provider import OpenFigiClient


class FakeFigiClient:
    """Liefert einen vorgegebenen Ticker und merkt sich den letzten Aufruf."""

    def __init__(self, ticker: str | None) -> None:
        self._ticker = ticker
        self.last_id_value: str | None = None
        self.last_id_type: str | None = None

    def map_isin(
        self, isin: str, id_value: str, id_type: str = "micCode"
    ) -> str | None:
        self.last_id_value = id_value
        self.last_id_type = id_type
        return self._ticker


def test_openfigi_baut_xetra_symbol() -> None:
    client = FakeFigiClient("VGWL")
    resolver = OpenFigiResolver(client, default_exchange="XETR")

    resolved = resolver.resolve_isin("IE00B3RBWM25")

    assert resolved is not None
    assert resolved.symbol == "VGWL.DE"
    assert resolved.isin == "IE00B3RBWM25"
    assert client.last_id_value == "XETR"
    assert client.last_id_type == "micCode"


def test_openfigi_ohne_treffer_gibt_none() -> None:
    resolver = OpenFigiResolver(FakeFigiClient(None), default_exchange="XETR")

    assert resolver.resolve_isin("DE000A0S9GB0") is None


def test_openfigi_respektiert_andere_boerse() -> None:
    client = FakeFigiClient("EQQQ")
    resolver = OpenFigiResolver(client, default_exchange="XMIL")

    resolved = resolver.resolve_isin("IE0032077012")

    assert resolved is not None
    assert resolved.symbol == "EQQQ.MI"
    assert client.last_id_value == "XMIL"
    assert client.last_id_type == "micCode"


class _FakeFigi:
    """Zeichnet den letzten map_isin-Aufruf auf und liefert einen festen Ticker."""

    def __init__(self, ticker: str | None) -> None:
        self.ticker = ticker
        self.calls: list[tuple] = []

    def map_isin(
        self, isin: str, id_value: str, id_type: str = "micCode"
    ) -> str | None:
        self.calls.append((isin, id_value, id_type))
        return self.ticker


def test_tsx_bildet_punkt_to_symbol() -> None:
    figi = _FakeFigi("RY")
    resolved = OpenFigiResolver(figi, "XTSE").resolve_isin("CA7800871021")
    assert resolved is not None
    assert resolved.symbol == "RY.TO"
    assert figi.calls == [("CA7800871021", "XTSE", "micCode")]


def test_us_nutzt_exchcode_und_leeres_suffix() -> None:
    figi = _FakeFigi("AAPL")
    resolved = OpenFigiResolver(figi, "US").resolve_isin("US0378331005")
    assert resolved is not None
    assert resolved.symbol == "AAPL"  # kein Suffix
    assert figi.calls == [("US0378331005", "US", "exchCode")]


def test_unbekannte_boerse_faellt_auf_xetr_zurueck() -> None:
    figi = _FakeFigi("EUNL")
    resolved = OpenFigiResolver(figi, "NOPE").resolve_isin("IE00B4L5Y983")
    assert resolved is not None
    assert resolved.symbol == "EUNL.DE"
    assert figi.calls == [("IE00B4L5Y983", "XETR", "micCode")]


def test_us_ist_in_tabelle_mit_exchcode() -> None:
    assert EXCHANGES["US"].figi_id_type == "exchCode"
    assert EXCHANGES["US"].suffix == ""


class StubResolver:
    """Resolver-Stub für den CompositeResolver-Test."""

    def __init__(self, result: ResolvedInstrument | None) -> None:
        self._result = result

    def resolve_isin(self, isin: str) -> ResolvedInstrument | None:
        return self._result


def test_composite_nimmt_ersten_treffer() -> None:
    primary = StubResolver(None)
    fallback = StubResolver(ResolvedInstrument(symbol="BRK-B", isin="US0846707026"))
    resolver = CompositeResolver(primary, fallback)

    resolved = resolver.resolve_isin("US0846707026")

    assert resolved is not None
    assert resolved.symbol == "BRK-B"


def test_composite_gibt_none_wenn_alle_leer() -> None:
    resolver = CompositeResolver(StubResolver(None), StubResolver(None))

    assert resolver.resolve_isin("XX0000000000") is None


class CountingResolver:
    """Zählt seine Aufrufe — beantwortet die Frage, ob er überhaupt drankam."""

    def __init__(self, result: ResolvedInstrument | None) -> None:
        self._result = result
        self.calls: list[str] = []

    def resolve_isin(self, isin: str) -> ResolvedInstrument | None:
        self.calls.append(isin)
        return self._result


class _FakeResponse:
    """Antwortobjekt für den gemockten OpenFIGI-Aufruf."""

    def __init__(self, payload: object) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


def _mit_openfigi_antwort(monkeypatch, payload: object) -> None:
    """Legt die OpenFIGI-Antwort fest, ohne den Dienst zu fragen."""
    import app.providers.openfigi_provider as openfigi_module

    monkeypatch.setattr(
        openfigi_module.httpx,
        "post",
        lambda *args, **kwargs: _FakeResponse(payload),
    )


def test_bloomberg_bezeichner_laesst_den_fallback_ans_werk(monkeypatch) -> None:
    """Die ganze Kette, nicht nur der Filter: Kommt der zweite Resolver dran?

    Gemessen am 2026-08-21: OpenFIGI liefert zu `CA78012H5675` (Vorzugsaktie
    der Royal Bank) den Bloomberg-Bezeichner `RY V3.65 PERP BB`. Daraus wurde
    das Symbol `RY V3.65 PERP BB.TO`, auf das yfinance mit 404 antwortet — und
    weil der `CompositeResolver` nur auf ``None`` prüft, galt das als Treffer.
    Der Yahoo-Fallback kam nie an die Reihe.

    Der Test geht durch den echten Antwort-Parser des Clients; gemockt ist
    allein der HTTP-Aufruf.
    """
    _mit_openfigi_antwort(
        monkeypatch,
        [{"data": [{"ticker": "RY V3.65 PERP BB", "exchCode": "TORONTO"}]}],
    )
    fallback = CountingResolver(
        ResolvedInstrument(symbol="RY-PH.TO", isin="CA78012H5675")
    )
    resolver = CompositeResolver(
        OpenFigiResolver(OpenFigiClient(), default_exchange="XTSE"), fallback
    )

    resolved = resolver.resolve_isin("CA78012H5675")

    assert fallback.calls == ["CA78012H5675"]
    assert resolved is not None
    assert resolved.symbol == "RY-PH.TO"


def test_brauchbarer_ticker_laesst_den_fallback_in_ruhe(monkeypatch) -> None:
    """Die Gegenprobe: Ein echtes Symbol beendet die Kette wie bisher."""
    _mit_openfigi_antwort(monkeypatch, [{"data": [{"ticker": "RY"}]}])
    fallback = CountingResolver(ResolvedInstrument(symbol="RY", isin="CA7800871021"))
    resolver = CompositeResolver(
        OpenFigiResolver(OpenFigiClient(), default_exchange="XTSE"), fallback
    )

    resolved = resolver.resolve_isin("CA7800871021")

    assert fallback.calls == []
    assert resolved is not None
    assert resolved.symbol == "RY.TO"


def test_unbrauchbarer_ticker_ohne_fallback_ist_nicht_aufloesbar(monkeypatch) -> None:
    """Findet auch die zweite Quelle nichts, bleibt es beim sauberen Fehlschlag.

    Der Filter macht dieses Papier nicht auflösbar — Yahoos ISIN-Suche kennt
    `CA78012H5675` ebenfalls nicht. Er sorgt allein dafür, dass die Kette
    weiterläuft und am Ende 404 steht statt eines Symbols, das es nicht gibt.
    """
    _mit_openfigi_antwort(
        monkeypatch, [{"data": [{"ticker": "RY V3.65 PERP BB"}]}]
    )
    fallback = CountingResolver(None)
    resolver = CompositeResolver(
        OpenFigiResolver(OpenFigiClient(), default_exchange="XTSE"), fallback
    )

    assert resolver.resolve_isin("CA78012H5675") is None
    assert fallback.calls == ["CA78012H5675"]


class _FakeSearch:
    """Ersetzt ``yf.Search`` — liefert eine je Test gesetzte Trefferliste."""

    treffer: list[dict] = []

    def __init__(self, isin: str) -> None:
        self.quotes = list(self.treffer)


def _mit_suche(monkeypatch, treffer: list[dict]) -> None:
    """Hängt die Fake-Suche an die Stelle, an der der Resolver sie holt."""
    from app import resolver as resolver_modul

    _FakeSearch.treffer = treffer
    monkeypatch.setattr(resolver_modul.yf, "Search", _FakeSearch)


def test_yahoo_nimmt_das_listing_der_bevorzugten_boerse(monkeypatch) -> None:
    """Nicht der erste Treffer gewinnt, sondern der passende.

    Der Anlass steht in DATA-03: Die Yahoo-Suche liefert für ein iShares-Papier
    zuerst die Londoner Notierung. Wer sie nimmt, bekommt GBP statt EUR — und
    im Depot fällt die Position aus der Währungsrechnung.
    """
    _mit_suche(
        monkeypatch,
        [
            {"symbol": "IS3M.L", "exchDisp": "LSE", "quoteType": "ETF"},
            {"symbol": "IS3M.DE", "exchDisp": "XETRA", "quoteType": "ETF"},
        ],
    )
    resolver = YFinanceResolver(default_exchange="XETR")

    resolved = resolver.resolve_isin("IE00BCRY6557")

    assert resolved is not None
    assert resolved.symbol == "IS3M.DE"


def test_yahoo_nimmt_den_ersten_treffer_wenn_die_boerse_fehlt(monkeypatch) -> None:
    """Ein US-Papier ohne deutsches Listing muss weiterhin durchgehen.

    Genau dafür gibt es den Fallback — er darf nicht zum Nichts-Finden werden.
    """
    _mit_suche(
        monkeypatch,
        [
            {"symbol": "AAPL", "exchDisp": "NasdaqGS", "quoteType": "EQUITY"},
            {"symbol": "AAPL.MX", "exchDisp": "Mexico", "quoteType": "EQUITY"},
        ],
    )
    resolver = YFinanceResolver(default_exchange="XETR")

    resolved = resolver.resolve_isin("US0378331005")

    assert resolved is not None
    assert resolved.symbol == "AAPL"


def test_yahoo_folgt_der_konfigurierten_boerse(monkeypatch) -> None:
    _mit_suche(
        monkeypatch,
        [
            {"symbol": "EQQQ.DE", "exchDisp": "XETRA", "quoteType": "ETF"},
            {"symbol": "EQQQ.MI", "exchDisp": "Milan", "quoteType": "ETF"},
        ],
    )
    resolver = YFinanceResolver(default_exchange="XMIL")

    resolved = resolver.resolve_isin("IE0032077012")

    assert resolved is not None
    assert resolved.symbol == "EQQQ.MI"


def test_yahoo_bevorzugt_bei_boerse_ohne_suffix_das_symbol_ohne_punkt(
    monkeypatch,
) -> None:
    """`US` hat kein Suffix — dort ist das punktlose Symbol die Notierung.

    Ohne diesen Zweig liefe die Regel leer: Jedes Symbol „endet auf ''".
    """
    _mit_suche(
        monkeypatch,
        [
            {"symbol": "AAPL.DE", "exchDisp": "XETRA", "quoteType": "EQUITY"},
            {"symbol": "AAPL", "exchDisp": "NasdaqGS", "quoteType": "EQUITY"},
        ],
    )
    resolver = YFinanceResolver(default_exchange="US")

    resolved = resolver.resolve_isin("US0378331005")

    assert resolved is not None
    assert resolved.symbol == "AAPL"


def test_yahoo_ueberspringt_treffer_ohne_symbol(monkeypatch) -> None:
    _mit_suche(
        monkeypatch,
        [
            {"exchDisp": "XETRA", "quoteType": "ETF"},
            {"symbol": "VGWL.DE", "exchDisp": "XETRA", "quoteType": "ETF"},
        ],
    )
    resolver = YFinanceResolver(default_exchange="XETR")

    resolved = resolver.resolve_isin("IE00B3RBWM25")

    assert resolved is not None
    assert resolved.symbol == "VGWL.DE"


def test_yahoo_ohne_treffer_gibt_none(monkeypatch) -> None:
    _mit_suche(monkeypatch, [])
    resolver = YFinanceResolver(default_exchange="XETR")

    assert resolver.resolve_isin("IE00B3RBWM25") is None


def test_yahoo_bevorzugt_die_gattung_des_bestplatzierten_treffers(monkeypatch) -> None:
    """Das Börsen-Suffix allein reicht nicht — die Trefferliste mischt Gattungen.

    Yahoos ISIN-Suche ist unscharf: Neben dem gesuchten ETF stehen dort
    Zertifikate, Fonds und Optionsscheine desselben Basiswerts. Wer schlicht
    den ersten Suffix-Treffer nimmt, holt sich einen davon ins Haus, obwohl
    der bestplatzierte Treffer die richtige Gattung nennt.
    """
    _mit_suche(
        monkeypatch,
        [
            {"symbol": "IS3M.L", "exchDisp": "LSE", "quoteType": "ETF"},
            {"symbol": "XYZ.DE", "exchDisp": "XETRA", "quoteType": "MUTUALFUND"},
            {"symbol": "IS3M.DE", "exchDisp": "XETRA", "quoteType": "ETF"},
        ],
    )
    resolver = YFinanceResolver(default_exchange="XETR")

    resolved = resolver.resolve_isin("IE00BCRY6557")

    assert resolved is not None
    assert resolved.symbol == "IS3M.DE"
    assert resolved.type == "etf"


def test_yahoo_nimmt_die_boerse_auch_bei_abweichender_gattung(monkeypatch) -> None:
    """Die Gattung ist die Feinauswahl, nicht die Bedingung.

    Nennt kein Treffer der bevorzugten Börse dieselbe Gattung wie der
    bestplatzierte, gewinnt weiterhin die Börse — sonst kippte die Regel bei
    jeder unsauberen `quoteType`-Angabe auf die Londoner Notierung zurück.
    """
    _mit_suche(
        monkeypatch,
        [
            {"symbol": "IS3M.L", "exchDisp": "LSE", "quoteType": "ETF"},
            {"symbol": "IS3M.DE", "exchDisp": "XETRA", "quoteType": ""},
        ],
    )
    resolver = YFinanceResolver(default_exchange="XETR")

    resolved = resolver.resolve_isin("IE00BCRY6557")

    assert resolved is not None
    assert resolved.symbol == "IS3M.DE"

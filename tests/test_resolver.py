"""Tests für die ISIN-Auflösung (OpenFIGI-Client gemockt)."""

from app.resolver import EXCHANGES, CompositeResolver, OpenFigiResolver
from app.providers.base import ResolvedInstrument


class FakeFigiClient:
    """Liefert einen vorgegebenen Ticker und merkt sich den letzten Aufruf."""

    def __init__(self, ticker: str | None) -> None:
        self._ticker = ticker
        self.last_id_value: str | None = None
        self.last_id_type: str | None = None

    def map_isin(self, isin: str, id_value: str, id_type: str = "micCode") -> str | None:
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

    def map_isin(self, isin: str, id_value: str, id_type: str = "micCode") -> str | None:
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

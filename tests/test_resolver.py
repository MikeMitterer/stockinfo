"""Tests für die ISIN-Auflösung (OpenFIGI-Client gemockt)."""

from app.resolver import CompositeResolver, OpenFigiResolver
from app.providers.base import ResolvedInstrument


class FakeFigiClient:
    """Liefert einen vorgegebenen Ticker und merkt sich den MIC."""

    def __init__(self, ticker: str | None) -> None:
        self._ticker = ticker
        self.last_mic: str | None = None

    def map_isin(self, isin: str, mic_code: str) -> str | None:
        self.last_mic = mic_code
        return self._ticker


def test_openfigi_baut_xetra_symbol() -> None:
    client = FakeFigiClient("VGWL")
    resolver = OpenFigiResolver(client, default_exchange="XETR")

    resolved = resolver.resolve_isin("IE00B3RBWM25")

    assert resolved is not None
    assert resolved.symbol == "VGWL.DE"
    assert resolved.isin == "IE00B3RBWM25"
    assert client.last_mic == "XETR"


def test_openfigi_ohne_treffer_gibt_none() -> None:
    resolver = OpenFigiResolver(FakeFigiClient(None), default_exchange="XETR")

    assert resolver.resolve_isin("DE000A0S9GB0") is None


def test_openfigi_respektiert_andere_boerse() -> None:
    client = FakeFigiClient("EQQQ")
    resolver = OpenFigiResolver(client, default_exchange="XMIL")

    resolved = resolver.resolve_isin("IE0032077012")

    assert resolved is not None
    assert resolved.symbol == "EQQQ.MI"
    assert client.last_mic == "XMIL"


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

"""Yahoo-Langnamen haben beim Auflösen Vorrang vor gepolsterten Kurznamen."""

from types import SimpleNamespace

import pytest

from app.providers.base import ResolvedInstrument
from app.resolver import YFinanceResolver


@pytest.mark.parametrize("entry", ["symbol", "isin", "crypto"])
@pytest.mark.parametrize("long_name", ["SAP SE", None, ""])
def test_langname_hat_vorrang_mit_kurzname_als_rueckfall(
    monkeypatch: pytest.MonkeyPatch, entry: str, long_name: str | None
) -> None:
    symbol = "BTC-EUR" if entry == "crypto" else "SAP.DE"
    hit = {
        "symbol": symbol,
        "exchange": "GER",
        "quoteType": "CRYPTOCURRENCY" if entry == "crypto" else "EQUITY",
        "shortname": "SAP SE                        I",
    }
    if long_name is not None:
        hit["longname"] = long_name
    monkeypatch.setattr(
        "app.resolver.yf.Search", lambda query: SimpleNamespace(quotes=[hit])
    )
    resolver = YFinanceResolver()
    result = (
        resolver.resolve_isin("DE0007164600")
        if entry == "isin"
        else resolver.resolve_symbol(symbol)
    )
    assert isinstance(result, ResolvedInstrument)
    assert result.name == ("SAP SE" if long_name else "SAP SE                        I")

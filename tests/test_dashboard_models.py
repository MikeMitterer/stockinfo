import pytest
from pydantic import ValidationError

from app.models import (
    IsinOnlyIdentityOut,
    PairIdentityOut,
    EnvInfo,
    InstrumentSummary,
    ListedIdentityOut,
    RefreshResult,
)


def test_instrument_summary_defaults() -> None:
    # Die Identität ist seit T-21 Übergabe 3 Pflicht — sie hat keinen
    # Vorgabewert, weil es die halbe Identität nicht mehr geben darf.
    summary = InstrumentSummary(
        symbol="VGWL.DE",
        identity=ListedIdentityOut(ticker="VGWL", mic="XETR"),
        listing_id="018f3a2c-7b41-7c9e-a3d2-5f1b9c4e2a10",
        history_count=3,
    )
    assert summary.symbol == "VGWL.DE"
    assert summary.identity.isin is None
    assert summary.latest_price is None
    assert summary.history_count == 3


def test_env_info_und_refresh_result() -> None:
    env = EnvInfo(
        version="0.1.0",
        database_path="data/stockinfo.db",
        cache_ttl_hours=6,
        refresh_interval_hours=6,
        metadata_ttl_days=7,
        default_exchange="XETR",
        strict_exchange=False,
        host="0.0.0.0",
        port=8000,
        openfigi_key_set=True,
    )
    assert env.openfigi_key_set is True
    assert RefreshResult(total=5, refreshed=4).refreshed == 4


@pytest.mark.parametrize(
    ("form", "extra"),
    [
        (PairIdentityOut(base="BTC", quote_currency="EUR"), {"isin": "DE0001102531"}),
        (PairIdentityOut(base="BTC", quote_currency="EUR"), {"ticker": "BTC"}),
        (IsinOnlyIdentityOut(isin="DE0001102531"), {"mic": "XETR"}),
        (ListedIdentityOut(ticker="EUNL", mic="XETR"), {"base": "EUNL"}),
    ],
    ids=["pair_mit_isin", "pair_mit_ticker", "isin_only_mit_mic", "listed_mit_base"],
)
def test_eine_identitaetsform_nimmt_keine_fremden_felder(form, extra: dict) -> None:
    """**Die Gegenprobe zu `extra="forbid"`** (Codex `#5`, Runde 5).

    Ohne sie wären die fremden Felder still verworfen worden — und genau
    dieser stille Verlust hat den Umbau in Runde 4 zwei Schichten später zum
    Absturz gebracht: Ein übriggebliebenes `isin=` verschwand kommentarlos,
    die Zeile ging ohne ISIN in die Datenbank, und der Fehler tauchte an einer
    Stelle ohne Bezug zur Ursache auf.

    Jede Kombination hier ist fachlich unmöglich: Ein Paar hat keine ISIN und
    keinen Ticker, eine ISIN-only-Form keinen Handelsplatz, ein Listing keinen
    Basiswert. Wer sie trotzdem schickt, hat einen Rest aus einem Umbau — und
    das gehört gemeldet, nicht weggeworfen.
    """
    with pytest.raises(ValidationError):
        type(form)(**{**form.model_dump(), **extra})

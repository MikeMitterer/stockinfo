from app.models import (
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

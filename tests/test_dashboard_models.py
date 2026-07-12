from app.models import EnvInfo, InstrumentSummary, RefreshResult


def test_instrument_summary_defaults() -> None:
    summary = InstrumentSummary(symbol="VGWL.DE", history_count=3)
    assert summary.symbol == "VGWL.DE"
    assert summary.isin is None
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
        host="0.0.0.0",
        port=8000,
        api_key_set=False,
        openfigi_key_set=True,
    )
    assert env.api_key_set is False
    assert RefreshResult(total=5, refreshed=4).refreshed == 4

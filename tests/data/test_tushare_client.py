from types import SimpleNamespace

import pandas as pd

from data.ingestion.tushare_client import ResilientTushareFetcher, TushareDataFetcher


class DummyLimiter:
    def __init__(self):
        self.wait_calls = 0
        self.error_calls = 0
        self.empty_calls = 0
        self.success_calls = 0

    def wait(self):
        self.wait_calls += 1

    def record_error(self):
        self.error_calls += 1

    def record_empty(self):
        self.empty_calls += 1

    def record_success(self):
        self.success_calls += 1


def test_fetch_historical_data_returns_cached_frame_without_api(tmp_path):
    fetcher = object.__new__(TushareDataFetcher)
    fetcher.symbol = "000001.SZ"
    fetcher.monitor = SimpleNamespace(
        log_error=lambda *args, **kwargs: None,
        log_warning=lambda *args, **kwargs: None,
        log_success=lambda *args, **kwargs: None,
    )
    fetcher.cache_manager = None
    fetcher.stocks_dir = tmp_path

    cache_file = fetcher._get_stock_cache_path(fetcher.symbol)
    cached = pd.DataFrame(
        {"Close": [10.0, 10.5], "Symbol": [fetcher.symbol, fetcher.symbol]},
        index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
    )
    cached.to_parquet(cache_file)

    fetcher._fetch_from_api = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("API should not be called")
    )

    result = fetcher.fetch_historical_data("2024-01-01", "2024-01-31", use_cache=True)

    pd.testing.assert_frame_equal(result, cached)


def test_fetch_daily_with_retry_records_failure_once_for_invalid_payload(monkeypatch):
    payload = pd.DataFrame({"ts_code": ["000001.SZ"], "trade_date": ["20240101"]})
    pro = SimpleNamespace(daily=lambda **kwargs: payload)
    fetcher = ResilientTushareFetcher(pro_api=pro, max_attempts=1)
    limiter = DummyLimiter()
    fetcher.rate_limiter = limiter

    monkeypatch.setattr("data.ingestion.tushare_client.time.sleep", lambda *_args, **_kwargs: None)

    result = fetcher.fetch_daily_with_retry("000001.SZ", "2024-01-01", "2024-01-31")

    assert result is None
    assert limiter.error_calls == 1
    assert limiter.empty_calls == 0
    assert limiter.success_calls == 0


def test_retry_delay_grows_but_is_bounded(monkeypatch):
    pro = SimpleNamespace(daily=lambda **kwargs: pd.DataFrame())
    fetcher = ResilientTushareFetcher(pro_api=pro, base_delay=2.0)

    monkeypatch.setattr("data.ingestion.tushare_client.random.uniform", lambda _a, _b: 0.5)

    first_delay = fetcher._get_retry_delay(0)
    later_delay = fetcher._get_retry_delay(3)
    capped_delay = fetcher._get_retry_delay(10)

    assert later_delay > first_delay
    assert capped_delay <= 30.0

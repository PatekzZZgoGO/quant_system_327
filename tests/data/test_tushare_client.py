from types import SimpleNamespace

import pandas as pd

import data.ingestion.tushare_client as tushare_client
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


class FakeCachePath:
    def __init__(self, exists=True):
        self._exists = exists
        self.parent = SimpleNamespace(mkdir=lambda **kwargs: None)

    def exists(self):
        return self._exists


def make_fetcher(symbol="000001.SZ"):
    fetcher = object.__new__(TushareDataFetcher)
    fetcher.symbol = symbol
    fetcher.monitor = SimpleNamespace(
        log_error=lambda *args, **kwargs: None,
        log_warning=lambda *args, **kwargs: None,
        log_success=lambda *args, **kwargs: None,
    )
    fetcher.cache_manager = SimpleNamespace(update_meta=lambda *args, **kwargs: None)
    return fetcher


def test_fetch_historical_data_returns_cached_frame_without_api(monkeypatch):
    fetcher = make_fetcher()
    cached = pd.DataFrame(
        {"Close": [10.0, 10.5], "Symbol": [fetcher.symbol, fetcher.symbol]},
        index=pd.to_datetime(["2024-01-30", "2024-02-01"]),
    )

    fetcher._get_stock_cache_path = lambda _symbol: FakeCachePath()
    monkeypatch.setattr(tushare_client.pd, "read_parquet", lambda *_args, **_kwargs: cached.copy())
    fetcher._fetch_from_api = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("API should not be called"))

    result = fetcher.fetch_historical_data("2024-01-01", "2024-01-31", use_cache=True)

    pd.testing.assert_frame_equal(result, cached)


def test_resolve_effective_end_date_rolls_weekend_back_to_friday():
    fetcher = make_fetcher()

    assert fetcher._resolve_effective_end_date("20260329") == "20260327"


def test_fetch_historical_data_skips_weekend_incremental_fetch(monkeypatch):
    fetcher = make_fetcher()
    cached = pd.DataFrame(
        {"Close": [10.0], "Symbol": [fetcher.symbol]},
        index=pd.to_datetime(["2026-03-28"]),
    )

    fetcher._get_stock_cache_path = lambda _symbol: FakeCachePath()
    monkeypatch.setattr(tushare_client.pd, "read_parquet", lambda *_args, **_kwargs: cached.copy())
    fetcher._fetch_from_api = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("API should not be called"))

    result = fetcher.fetch_historical_data("2026-01-01", "2026-03-29", use_cache=True)

    pd.testing.assert_frame_equal(result, cached)


def test_fetch_historical_data_merges_incremental_data(monkeypatch):
    fetcher = make_fetcher()
    cached = pd.DataFrame(
        {"Close": [10.0, 10.5], "Symbol": [fetcher.symbol, fetcher.symbol]},
        index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
    )
    fresh = pd.DataFrame(
        {"Close": [11.0, 11.5], "Symbol": [fetcher.symbol, fetcher.symbol]},
        index=pd.to_datetime(["2024-01-04", "2024-01-05"]),
    )
    saved = {}
    meta = {}

    fetcher._get_stock_cache_path = lambda _symbol: FakeCachePath()
    monkeypatch.setattr(tushare_client.pd, "read_parquet", lambda *_args, **_kwargs: cached.copy())
    def fake_fetch_from_api(symbol, start, end):
        saved["api_args"] = (symbol, start, end)
        return fresh.copy()

    fetcher._fetch_from_api = fake_fetch_from_api
    fetcher._save_to_cache = lambda df, _path: saved.setdefault("df", df.copy())
    fetcher.cache_manager = SimpleNamespace(update_meta=lambda *args: meta.setdefault("args", args))

    result = fetcher.fetch_historical_data("2024-01-01", "2024-01-04", use_cache=True)

    assert saved["api_args"] == ("000001.SZ", "20240103", "20240104")
    assert len(result) == 4
    assert result.index.max() == pd.Timestamp("2024-01-05")
    assert meta["args"] == ("000001.SZ", "20240104", 4)


def test_fetch_daily_basic_merges_incremental_data(monkeypatch):
    fetcher = make_fetcher()
    cached = pd.DataFrame(
        {"TotalMV": [1000.0], "Symbol": [fetcher.symbol]},
        index=pd.to_datetime(["2024-01-03"]),
    )
    raw_incremental = pd.DataFrame(
        {
            "ts_code": [fetcher.symbol],
            "trade_date": ["20240103"],
            "total_mv": [2.0],
            "circ_mv": [1.0],
            "turnover_rate": [0.5],
            "pe": [10.0],
        }
    )
    saved = {}

    fetcher._get_basic_cache_path = lambda _symbol: FakeCachePath()
    monkeypatch.setattr(tushare_client.pd, "read_parquet", lambda *_args, **_kwargs: cached.copy())
    def fake_fetch_daily_basic_with_retry(**kwargs):
        saved["api_kwargs"] = kwargs
        return raw_incremental.copy()

    fetcher.fetcher = SimpleNamespace(fetch_daily_basic_with_retry=fake_fetch_daily_basic_with_retry)

    result = fetcher.fetch_daily_basic("2024-01-01", "2024-01-03", use_cache=True)

    assert saved["api_kwargs"] == {
        "ts_code": "000001.SZ",
        "start_date": "20240103",
        "end_date": "20240103",
    }
    assert len(result) == 2
    assert result.index.max() == pd.Timestamp("2024-01-04")
    assert result.loc[pd.Timestamp("2024-01-04"), "TotalMV"] == 20000.0


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

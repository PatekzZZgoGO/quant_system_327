import pandas as pd

from application.shared.data_app import get_cache_status, run_update_stock, run_update_stocks


class StubFetcher:
    def __init__(self, symbol=None, stock_list=None, failures=None):
        self.symbol = symbol
        self._stock_list = stock_list or []
        self._failures = failures or set()

    def fetch_historical_data(self, start_date, end_date=None, force_refresh=False):
        if self.symbol in self._failures:
            raise RuntimeError(f"boom:{self.symbol}")
        return pd.DataFrame({"close": [1, 2]})

    def fetch_daily_basic(self, start_date, end_date=None, force_refresh=False):
        if self.symbol in self._failures:
            raise RuntimeError(f"boom:{self.symbol}")
        return pd.DataFrame({"mv": [3]})

    def get_stock_list(self):
        return list(self._stock_list)

    def check_cache_status(self):
        return {"total": 3, "cached": 2, "missing": 1}


def test_run_update_stock_returns_summary_payload():
    payload = run_update_stock(
        code="000001.SZ",
        start_date="2024-01-01",
        end_date="2024-01-31",
        force_refresh=True,
        fetcher=StubFetcher(symbol="000001.SZ"),
    )

    assert payload["code"] == "000001.SZ"
    assert payload["price_rows"] == 2
    assert payload["basic_rows"] == 1
    assert payload["success"] is True


def test_run_update_stocks_collects_success_and_failure():
    payload = run_update_stocks(
        start_date="2024-01-01",
        end_date="2024-01-31",
        limit=2,
        fetcher=StubFetcher(stock_list=["000001.SZ", "000002.SZ"], failures={"000002.SZ"}),
    )

    assert payload["requested_count"] == 2
    assert payload["success_count"] == 1
    assert payload["failure_count"] == 1
    assert payload["results"][1]["error"] == "boom:000002.SZ"


def test_get_cache_status_returns_stats_payload():
    payload = get_cache_status(fetcher=StubFetcher())

    assert payload["stats"] == {"total": 3, "cached": 2, "missing": 1}

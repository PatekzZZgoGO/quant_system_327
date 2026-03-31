import warnings
from types import SimpleNamespace

import pandas as pd

from application.shared.factor_app import _load_factor_panel
from application.shared.ic_app import _load_ic_panel
from data.services.data_service import DataService


class StubBoundaryDataService:
    def __init__(self):
        self.lookback_days = 20
        self.calls = []

    def get_analysis_panel(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(panel=pd.DataFrame({"Date": [], "Symbol": []}))

    def get_analysis_factor_panel(self, *args, **kwargs):  # pragma: no cover
        raise AssertionError("legacy factor interface should not be used")

    def get_analysis_backtest_panel(self, *args, **kwargs):  # pragma: no cover
        raise AssertionError("legacy backtest interface should not be used")

    def get_analysis_ic_panel(self, *args, **kwargs):  # pragma: no cover
        raise AssertionError("legacy IC interface should not be used")


def test_factor_app_loads_panel_via_shared_analysis_entry():
    data_service = StubBoundaryDataService()

    _load_factor_panel(
        data_service,
        ["000001.SZ"],
        date="2024-01-05",
        use_cache=True,
    )

    assert data_service.calls[0]["cache_extras"] == {"lookback_days": 20}


def test_ic_app_loads_panel_via_shared_analysis_entry():
    data_service = StubBoundaryDataService()

    _load_ic_panel(
        data_service,
        ["000001.SZ"],
        start="2024-01-01",
        end="2024-01-05",
        horizon=3,
        use_cache=True,
    )

    assert data_service.calls[0]["cache_extras"] == {"lookback_buffer_days": 9}
    assert pd.to_datetime(data_service.calls[0]["end"]) == pd.Timestamp("2024-01-14")


def test_legacy_factor_interface_emits_deprecation_warning():
    service = object.__new__(DataService)
    service.lookback_days = 20
    service.get_analysis_panel = lambda **kwargs: kwargs

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        service.get_analysis_factor_panel(["000001.SZ"], "2024-01-05", use_cache=True)

    assert any("get_analysis_factor_panel" in str(item.message) for item in caught)


def test_legacy_backtest_alias_emits_deprecation_warning():
    service = object.__new__(DataService)
    service.get_analysis_backtest_panel = lambda *args, **kwargs: None

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        service.get_backtest_panel(["000001.SZ"], "2024-01-01", "2024-01-05", execution_delay=1, use_cache=True)

    assert any("get_backtest_panel" in str(item.message) for item in caught)

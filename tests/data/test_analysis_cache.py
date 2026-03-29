from pathlib import Path

import pandas as pd

from core.common.config import APP_CONFIG
from data.cache.analysis_cache import AnalysisCache
from data.loaders.universe_loader import UniverseLoader
from data.providers.universe_provider import UniverseProvider
from data.services.data_service import DataService


def test_data_service_uses_config_stock_dir_by_default():
    service = DataService()
    assert service.data_dir == APP_CONFIG.stock_dir
    assert APP_CONFIG.cache_dir == APP_CONFIG.root_dir / "data" / "cache"


def _test_cache_dir(name: str) -> Path:
    path = APP_CONFIG.cache_dir / "test_artifacts" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_analysis_cache_round_trip_factor_and_ic():
    cache = AnalysisCache(base_dir=_test_cache_dir("factor_ic"))
    scored = pd.DataFrame({"Symbol": ["000001.SZ"], "score": [1.23]})
    ic_df = pd.DataFrame({"factor": ["alpha"], "ic": [0.12]})
    summary = pd.DataFrame({"factor": ["alpha"], "mean": [0.12]})

    factor_key = {"kind": "factor", "date": "2024-01-05", "model": "simple_alpha"}
    ic_key = {"kind": "ic", "start": "2024-01-01", "end": "2024-01-05"}

    cache.save_factor_result(factor_key, scored, {"rank_corr": {"alpha": 0.88}})
    cache.save_ic_result(ic_key, ic_df, summary, {"source": "test"})

    factor_result = cache.load_factor_result(factor_key)
    ic_result = cache.load_ic_result(ic_key)

    pd.testing.assert_frame_equal(factor_result["scored"], scored)
    assert factor_result["metadata"] == {"rank_corr": {"alpha": 0.88}}
    pd.testing.assert_frame_equal(ic_result["ic_df"], ic_df)
    pd.testing.assert_frame_equal(ic_result["summary"], summary)
    assert ic_result["metadata"] == {"source": "test"}


def test_analysis_cache_round_trip_panel():
    cache = AnalysisCache(base_dir=_test_cache_dir("panel"))
    panel = pd.DataFrame({"Date": ["2024-01-01"], "Symbol": ["000001.SZ"], "Close": [10.0]})
    key = {"kind": "panel", "symbols": ["000001.SZ"], "start": "2024-01-01", "end": "2024-01-05"}

    cache.save_panel(key, panel)
    loaded = cache.load_panel(key)

    pd.testing.assert_frame_equal(loaded, panel)


def test_analysis_cache_round_trip_universe():
    cache = AnalysisCache(base_dir=_test_cache_dir("universe"))
    key = {"kind": "universe", "limit": 2}
    symbols = ["000001.SZ", "000002.SZ"]

    cache.save_universe(key, symbols, {"count": 2, "limit": 2})
    loaded = cache.load_universe(key)

    assert loaded["symbols"] == symbols
    assert loaded["metadata"] == {"count": 2, "limit": 2}


def test_universe_provider_uses_cache():
    cache = AnalysisCache(base_dir=_test_cache_dir("universe_provider"))
    loader = UniverseLoader(APP_CONFIG.stock_dir)
    provider = UniverseProvider(loader, cache=cache)

    uncached = provider.get_universe(limit=3, use_cache=True)
    loader.get_universe = lambda limit=None: (_ for _ in ()).throw(AssertionError("loader should not be called"))
    cached = provider.get_universe(limit=3, use_cache=True)

    assert uncached == cached
    assert len(cached) == 3

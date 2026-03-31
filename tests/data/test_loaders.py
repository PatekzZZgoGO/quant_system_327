from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pandas as pd

from core.common.config import APP_CONFIG
from data.loaders.panel_loader import PanelLoader
from data.loaders.universe_loader import UniverseLoader


def test_panel_loader_merges_price_and_basic_rows():
    price_df = pd.DataFrame(
        {
            "Date": ["2024-01-02", "2024-01-03"],
            "Symbol": ["000001.SZ", "000001.SZ"],
            "Close": [10.0, 10.5],
        }
    )
    basic_df = pd.DataFrame(
        {
            "Date": ["2024-01-01"],
            "Symbol": ["000001.SZ"],
            "pe_ttm": [12.3],
        }
    )
    price_loader = SimpleNamespace(load=lambda symbol, start, end: price_df.copy())
    basic_loader = SimpleNamespace(load=lambda symbol: basic_df.copy())
    loader = PanelLoader(price_loader, basic_loader)

    panel = loader.load_panel(["000001.SZ"], "2024-01-01", "2024-01-03", max_workers=1)

    assert list(panel["Symbol"].unique()) == ["000001.SZ"]
    assert panel["pe_ttm"].tolist() == [12.3, 12.3]


def _test_universe_dir() -> Path:
    path = APP_CONFIG.cache_dir / "test_artifacts" / "universe_loader" / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_universe_loader_ignores_basic_files_and_applies_limit():
    data_dir = _test_universe_dir()
    (data_dir / "000001_sz.parquet").touch()
    (data_dir / "000002_sh.parquet").touch()
    (data_dir / "000001_sz_basic.parquet").touch()

    loader = UniverseLoader(data_dir)

    assert loader.get_universe(limit=1) == ["000001.SZ"]
    assert loader.get_universe() == ["000001.SZ", "000002.SH"]

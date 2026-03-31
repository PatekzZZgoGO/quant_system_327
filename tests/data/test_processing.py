import pandas as pd

from data.processors.aligner_processor import align_price_basic
from data.processors.returns_processor import compute_future_returns


def test_align_price_basic_backfills_latest_basic_row_by_symbol():
    price_df = pd.DataFrame(
        {
            "Date": ["2024-01-02", "2024-01-03"],
            "Symbol": ["000001.SZ", "000001.SZ"],
            "Close": [10.0, 10.5],
        }
    )
    basic_df = pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-03"],
            "Symbol": ["000001.SZ", "000001.SZ"],
            "pb": [1.2, 1.5],
        }
    )

    aligned = align_price_basic(price_df, basic_df)

    assert aligned["pb"].tolist() == [1.2, 1.5]


def test_compute_future_returns_adds_horizon_return_column():
    panel = pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "Symbol": ["000001.SZ", "000001.SZ", "000001.SZ"],
            "Close": [10.0, 11.0, 12.0],
            "factor_a": [1.0, 2.0, 3.0],
        }
    )

    result = compute_future_returns(panel, horizon=1)

    assert "ret_1d" in result.columns
    assert result["ret_1d"].round(4).tolist() == [0.1, 0.0909]
    assert "factor_a" in result.columns

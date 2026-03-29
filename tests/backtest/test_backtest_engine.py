import pandas as pd

from backtest.engine import BacktestEngine
from backtest.simulation import ExecutionModel
from data.domains.market_domain import Market
from data.domains.universe_domain import Universe
from features.engine.factor_engine import FactorEngine
from features.engine.scoring_engine import ScoringEngine


class StubDataService:
    """最小化 DataService 替身，用于验证回测闭环。"""

    def __init__(self, panel: pd.DataFrame):
        self._panel = panel.copy()

    def get_analysis_universe(self, limit=None, use_cache=True):
        symbols = sorted(self._panel["Symbol"].unique().tolist())
        if limit is not None:
            symbols = symbols[:limit]
        return Universe(symbols)

    def get_analysis_backtest_panel(self, symbols, start, end, execution_delay=1, use_cache=True):
        panel = self._panel[self._panel["Symbol"].isin(symbols)].copy()
        return Market(panel)


def _sample_panel():
    dates = pd.to_datetime(
        [
            "2024-01-01",
            "2024-01-02",
            "2024-01-03",
            "2024-01-04",
            "2024-01-05",
        ]
    )
    rows = []
    close_a = [10.0, 11.0, 12.0, 13.0, 14.0]
    close_b = [10.0, 10.0, 10.0, 10.0, 10.0]

    for idx, date in enumerate(dates):
        rows.append({"Date": date, "Symbol": "AAA", "Close": close_a[idx], "alpha": 1.0})
        rows.append({"Date": date, "Symbol": "BBB", "Close": close_b[idx], "alpha": 0.0})

    return pd.DataFrame(rows)


def test_backtest_engine_builds_factor_to_pnl_loop():
    panel = _sample_panel()
    engine = BacktestEngine(
        data_service=StubDataService(panel),
        factor_engine=FactorEngine(None),
        scoring_engine=ScoringEngine(),
        execution_model=ExecutionModel(commission_rate=0.0, slippage_rate=0.0),
    )

    result = engine.run(
        start="2024-01-01",
        end="2024-01-04",
        weights={"alpha": 1.0},
        model_name="test_model",
        top_n=1,
        rebalance_every=1,
        execution_delay=1,
        use_cache=False,
    )

    daily_pnl = result["daily_pnl"]
    assert list(daily_pnl["date"].dt.strftime("%Y-%m-%d")) == [
        "2024-01-02",
        "2024-01-03",
        "2024-01-04",
        "2024-01-05",
    ]
    assert daily_pnl.loc[0, "net_return"] == 0.0
    assert daily_pnl.loc[1, "net_return"] > 0
    assert daily_pnl.loc[2, "net_return"] > 0
    assert daily_pnl.loc[3, "net_return"] > 0
    assert result["summary"].loc[0, "total_return"] > 0
    assert len(result["trades"]) >= 1
    assert set(result["positions"]["symbol"]) == {"AAA"}


def test_backtest_engine_applies_turnover_costs():
    panel = _sample_panel()
    panel.loc[(panel["Symbol"] == "AAA") & (panel["Date"] >= pd.Timestamp("2024-01-03")), "alpha"] = 0.0
    panel.loc[(panel["Symbol"] == "BBB") & (panel["Date"] >= pd.Timestamp("2024-01-03")), "alpha"] = 1.0

    engine = BacktestEngine(
        data_service=StubDataService(panel),
        factor_engine=FactorEngine(None),
        scoring_engine=ScoringEngine(),
        execution_model=ExecutionModel(commission_rate=0.001, slippage_rate=0.0),
    )

    result = engine.run(
        start="2024-01-01",
        end="2024-01-04",
        weights={"alpha": 1.0},
        model_name="switch_model",
        top_n=1,
        rebalance_every=1,
        execution_delay=1,
        use_cache=False,
    )

    assert result["trades"]["total_cost"].sum() > 0
    assert result["daily_pnl"]["trading_cost"].sum() > 0

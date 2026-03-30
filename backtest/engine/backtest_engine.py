from typing import Dict, Optional

import pandas as pd

from backtest.analysis.result_analyzer import ResultAnalyzer
from backtest.simulation.execution_model import ExecutionModel
from backtest.simulation.pnl_calculator import PnLCalculator
from backtest.simulation.portfolio_manager import PortfolioManager
from backtest.simulation.signal_generator import SignalGenerator
from data.services.data_service import DataService
from exceptions.pipeline import PipelineExecutionError
from features.engine.factor_engine import FactorEngine
from features.engine.scoring_engine import ScoringEngine


class BacktestEngine:
    """与现有 DataService 无缝对齐的回测主控。"""

    def __init__(
        self,
        data_service: DataService,
        factor_engine: Optional[FactorEngine] = None,
        scoring_engine: Optional[ScoringEngine] = None,
        execution_model: Optional[ExecutionModel] = None,
        pnl_calculator: Optional[PnLCalculator] = None,
        result_analyzer: Optional[ResultAnalyzer] = None,
    ):
        self.data_service = data_service
        self.factor_engine = factor_engine or FactorEngine(None)
        self.scoring_engine = scoring_engine or ScoringEngine()
        self.signal_generator = SignalGenerator(self.scoring_engine)
        self.execution_model = execution_model or ExecutionModel()
        self.pnl_calculator = pnl_calculator or PnLCalculator()
        self.result_analyzer = result_analyzer or ResultAnalyzer()

    def _prepare_panel(self, symbols, start, end, execution_delay: int, use_cache: bool) -> pd.DataFrame:
        """取回测所需 panel，并统一整理日期字段。"""
        market = self.data_service.get_analysis_backtest_panel(
            symbols=symbols,
            start=start,
            end=end,
            execution_delay=execution_delay,
            use_cache=use_cache,
        )
        panel = market.panel.copy()
        if panel is None or panel.empty:
            return pd.DataFrame()

        panel["Date"] = pd.to_datetime(panel["Date"])
        panel = panel.sort_values(["Date", "Symbol"]).reset_index(drop=True)
        return panel

    def _compute_factor_panel(self, panel: pd.DataFrame, weights: Dict[str, float]) -> pd.DataFrame:
        """整段区间一次性完成因子计算。"""
        factors = list(weights.keys())
        enriched = self.factor_engine.pipeline.run(panel.set_index("Date"), factors=factors).reset_index()
        enriched = self.factor_engine.handle_missing(enriched, factors=factors)
        enriched["Date"] = pd.to_datetime(enriched["Date"])
        return enriched.sort_values(["Date", "Symbol"]).reset_index(drop=True)

    def run(
        self,
        start,
        end,
        weights: Dict[str, float],
        model_name: str = "custom",
        top_n: int = 20,
        limit: Optional[int] = None,
        rebalance_every: int = 1,
        execution_delay: int = 1,
        use_cache: bool = True,
    ):
        """执行完整回测。"""
        if not weights:
            raise ValueError("[BacktestEngine] weights is empty")
        if top_n <= 0:
            raise ValueError("[BacktestEngine] top_n must be positive")
        if rebalance_every <= 0:
            raise ValueError("[BacktestEngine] rebalance_every must be positive")
        if execution_delay <= 0:
            raise ValueError("[BacktestEngine] execution_delay must be positive")

        universe = self.data_service.get_analysis_universe(limit=limit, use_cache=use_cache)
        symbols = universe.symbols
        if not symbols:
            raise PipelineExecutionError("[BacktestEngine] universe is empty")

        panel = self._prepare_panel(symbols, start, end, execution_delay=execution_delay, use_cache=use_cache)
        if panel.empty:
            raise PipelineExecutionError("[BacktestEngine] panel is empty")

        factor_panel = self._compute_factor_panel(panel, weights)
        all_dates = sorted(factor_panel["Date"].drop_duplicates())
        signal_start = pd.to_datetime(start)
        signal_end = pd.to_datetime(end)
        signal_dates = [date for date in all_dates if signal_start <= date <= signal_end]
        signal_rank = {date: idx for idx, date in enumerate(signal_dates)}
        panel_by_date = {date: df for date, df in factor_panel.groupby("Date", sort=True)}

        portfolio_manager = PortfolioManager()
        daily_records = []
        trade_records = []
        signal_records = []
        position_records = []

        for idx, current_date in enumerate(all_dates):
            if idx > 0:
                prev_date = all_dates[idx - 1]
                period_record = self.pnl_calculator.compute_period_return(
                    panel_by_date=panel_by_date,
                    positions=portfolio_manager.positions,
                    start_date=prev_date,
                    end_date=current_date,
                )
                daily_records.append(
                    {
                        "date": current_date,
                        "gross_return": period_record["gross_return"],
                        "net_return": period_record["net_return"],
                        "turnover": 0.0,
                        "trading_cost": 0.0,
                        "covered_weight": period_record["covered_weight"],
                        "missing_symbols": period_record["missing_symbols"],
                        "position_count": len(portfolio_manager.positions),
                    }
                )

            execution_result = portfolio_manager.execute_due_rebalance(current_date, self.execution_model)
            if execution_result is not None:
                trade_records.append(
                    {
                        "signal_date": execution_result.signal_date,
                        "execution_date": execution_result.execution_date,
                        "turnover": execution_result.turnover,
                        "commission_cost": execution_result.commission_cost,
                        "slippage_cost": execution_result.slippage_cost,
                        "total_cost": execution_result.total_cost,
                        "position_count": len(execution_result.new_positions),
                    }
                )

                if daily_records and daily_records[-1]["date"] == current_date:
                    daily_records[-1]["turnover"] += execution_result.turnover
                    daily_records[-1]["trading_cost"] += execution_result.total_cost
                    daily_records[-1]["net_return"] = daily_records[-1]["gross_return"] - daily_records[-1]["trading_cost"]
                    daily_records[-1]["position_count"] = len(execution_result.new_positions)
                else:
                    daily_records.append(
                        {
                            "date": current_date,
                            "gross_return": 0.0,
                            "net_return": -execution_result.total_cost,
                            "turnover": execution_result.turnover,
                            "trading_cost": execution_result.total_cost,
                            "covered_weight": 0.0,
                            "missing_symbols": 0,
                            "position_count": len(execution_result.new_positions),
                        }
                    )

                position_records.extend(portfolio_manager.get_position_snapshot(current_date))

            if current_date not in signal_rank:
                continue
            if signal_rank[current_date] % rebalance_every != 0:
                continue
            if idx + execution_delay >= len(all_dates):
                continue

            snapshot = panel_by_date[current_date]
            signal_output = self.signal_generator.generate(snapshot=snapshot, weights=weights, top_n=top_n)
            if signal_output["selected"].empty:
                continue

            execution_date = all_dates[idx + execution_delay]
            portfolio_manager.schedule_rebalance(
                signal_date=current_date,
                execution_date=execution_date,
                target_positions=signal_output["target_positions"],
            )
            signal_records.append(
                {
                    "signal_date": current_date,
                    "execution_date": execution_date,
                    "model": model_name,
                    "selected_count": len(signal_output["selected"]),
                    "top_symbol": signal_output["selected"].iloc[0]["Symbol"],
                    "top_score": float(signal_output["selected"].iloc[0]["score"]),
                }
            )

        daily_pnl = pd.DataFrame(daily_records).sort_values("date").reset_index(drop=True)
        if not daily_pnl.empty:
            daily_pnl["date"] = pd.to_datetime(daily_pnl["date"])
            daily_pnl["nav"] = (1.0 + daily_pnl["net_return"].fillna(0.0)).cumprod()

        trades = pd.DataFrame(trade_records)
        signals = pd.DataFrame(signal_records)
        positions = pd.DataFrame(position_records)
        summary = self.result_analyzer.analyze(daily_pnl, trades)

        return {
            "daily_pnl": daily_pnl,
            "summary": summary,
            "trades": trades,
            "signals": signals,
            "positions": positions,
            "factor_panel": factor_panel,
        }

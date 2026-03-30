import importlib
from datetime import datetime

import pandas as pd

from backtest.engine import BacktestEngine
from backtest.simulation import ExecutionModel
from core.common.config import APP_CONFIG
from data.services.data_service import DataService
from features.engine.factor_engine import FactorEngine
from features.engine.scoring_engine import ScoringEngine


def load_model(name: str):
    """加载因子模型模块。"""
    return importlib.import_module(f"models.alpha.{name}")


def resolve_weights(model, date=None):
    """从模型中解析权重定义。"""
    if hasattr(model, "get_weights"):
        return model.get_weights(date)
    if hasattr(model, "WEIGHTS"):
        return model.WEIGHTS
    raise ValueError("[Backtest] model has no weights")


def print_backtest_result(summary: pd.DataFrame, daily_pnl: pd.DataFrame, trades: pd.DataFrame):
    """打印核心回测结果。"""
    print("\n=== Backtest Summary ===")
    print(summary.to_string(index=False))

    if not daily_pnl.empty:
        print("\n=== Daily PnL Tail ===")
        print(daily_pnl.tail().to_string(index=False))

    if not trades.empty:
        print("\n=== Trades Tail ===")
        print(trades.tail().to_string(index=False))


def save_backtest_result(result, model_name: str):
    """把回测结果保存到 backtest/results/runs。

    兼容性说明：
    - 当前阶段仍沿用现有 `backtest/results/runs` 路径；
    - 未来若逐步推进存储分区，目标落位应为 `storage/trading_system/backtests/`；
    - 本函数当前不改变现有路径逻辑，只补充边界说明。
    """
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = APP_CONFIG.backtest_runs_dir / f"{run_id}_{model_name}"
    output_dir.mkdir(parents=True, exist_ok=True)

    result["summary"].to_csv(output_dir / "summary.csv", index=False)
    result["daily_pnl"].to_csv(output_dir / "daily_pnl.csv", index=False)
    result["trades"].to_csv(output_dir / "trades.csv", index=False)
    result["signals"].to_csv(output_dir / "signals.csv", index=False)
    result["positions"].to_csv(output_dir / "positions.csv", index=False)

    return output_dir


def run_backtest(args):
    """执行回测命令。"""
    data_service = DataService()
    factor_engine = FactorEngine(None)
    scoring_engine = ScoringEngine()
    execution_model = ExecutionModel(
        commission_rate=args.commission_rate,
        slippage_rate=args.slippage_rate,
    )
    engine = BacktestEngine(
        data_service=data_service,
        factor_engine=factor_engine,
        scoring_engine=scoring_engine,
        execution_model=execution_model,
    )

    model = load_model(args.model)
    weights = resolve_weights(model, args.start)

    result = engine.run(
        start=args.start,
        end=args.end,
        weights=weights,
        model_name=args.model,
        top_n=args.top_n,
        limit=args.limit,
        rebalance_every=args.rebalance_every,
        execution_delay=args.execution_delay,
        use_cache=not args.no_cache,
    )

    print_backtest_result(result["summary"], result["daily_pnl"], result["trades"])

    if args.save:
        output_dir = save_backtest_result(result, args.model)
        print(f"\nSaved to: {output_dir}")


def register(subparsers):
    backtest_parser = subparsers.add_parser("backtest", help="backtest module")
    subparsers_backtest = backtest_parser.add_subparsers(dest="action", required=True)

    run_parser = subparsers_backtest.add_parser("run", help="run factor backtest")
    run_parser.add_argument("--start", required=True)
    run_parser.add_argument("--end", required=True)
    run_parser.add_argument("--model", required=True)
    run_parser.add_argument("--top-n", type=int, default=20)
    run_parser.add_argument("--limit", type=int, default=None)
    run_parser.add_argument("--rebalance-every", type=int, default=1)
    run_parser.add_argument("--execution-delay", type=int, default=1)
    run_parser.add_argument("--commission-rate", type=float, default=0.001)
    run_parser.add_argument("--slippage-rate", type=float, default=0.0)
    run_parser.add_argument("--save", action="store_true")
    run_parser.add_argument("--no-cache", action="store_true")
    run_parser.set_defaults(func=run_backtest)

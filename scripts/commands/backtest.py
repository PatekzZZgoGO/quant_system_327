import pandas as pd

from pipelines.backtest_pipeline import run_backtest_pipeline


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


def run_backtest(args):
    """执行回测命令。"""
    payload = run_backtest_pipeline(
        start=args.start,
        end=args.end,
        model_name=args.model,
        top_n=args.top_n,
        limit=args.limit,
        rebalance_every=args.rebalance_every,
        execution_delay=args.execution_delay,
        commission_rate=args.commission_rate,
        slippage_rate=args.slippage_rate,
        use_cache=not args.no_cache,
        save=args.save,
    )
    result = payload["result"]

    print_backtest_result(result["summary"], result["daily_pnl"], result["trades"])

    if payload["output_dir"] is not None:
        print(f"\nSaved to: {payload['output_dir']}")


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

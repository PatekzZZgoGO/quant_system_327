import pandas as pd
import logging
from pathlib import Path
import time
import importlib

from joblib import Parallel, delayed
import os

from features.engine.factor_engine import FactorEngine
from data.loaders.market_loader import MarketDataLoader
from data.loaders.universe_loader import UniverseLoader

from features.analysis.ic_temp import (
    summarize_ic,
    compute_snapshot_ic
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# =========================
# 🧠 model / factor解析
# =========================
def load_model(name: str):
    return importlib.import_module(f"models.alpha.{name}")


def resolve_factors(args, factor_engine):

    if args.factors:
        return args.factors, "user"

    if args.model:
        model = load_model(args.model)

        if hasattr(model, "get_weights"):
            return list(model.get_weights().keys()), "model"
        elif hasattr(model, "WEIGHTS"):
            return list(model.WEIGHTS.keys()), "model"

    return factor_engine.pipeline.registry.list_factors(), "registry"


# =========================
# 🚀 并行 worker（优化版）
# =========================
def _ic_worker(
    date,
    panel_grouped,
    future_grouped,
    factors,
    horizon
):
    """
    单日 IC 计算（无 slice / 无 merge 优化版）
    """

    try:
        # =========================
        # 🚀 O(1) 直接取
        # =========================
        snapshot = panel_grouped.get(date)
        future_ret = future_grouped.get(date)

        if snapshot is None or future_ret is None:
            return []

        if snapshot.empty or future_ret.empty:
            return []

        # =========================
        # 🚀 merge（已经是最小开销）
        # =========================
        merged = snapshot.merge(
            future_ret,
            on=["Date", "Symbol"],
            how="inner"
        )

        if len(merged) < 5:
            return []

        # =========================
        # 因子列
        # =========================
        factor_cols = [
            f"{f}_z" if f"{f}_z" in merged.columns else f
            for f in factors
        ]

        # =========================
        # IC 计算
        # =========================
        ic_dict = compute_snapshot_ic(
            merged,
            factor_cols=factor_cols,
            ret_col=f"ret_{horizon}d",
            method="spearman"
        )

        return [
            {
                "date": date,
                "factor": f.replace("_z", ""),
                "ic": ic
            }
            for f, ic in ic_dict.items()
        ]

    except Exception as e:
        logger.warning(f"[IC][Worker] {date} failed: {e}")
        return []


# =========================
# 🚀 IC 主函数
# =========================
def run_factor_ic(args):
    logger.info("=" * 50)
    logger.info("[Factor IC] Start")

    total_start_time = time.time()

    data_loader = MarketDataLoader()
    factor_engine = FactorEngine(data_loader)

    logger.info("[IC] Initialized data loader and engine")

    # =========================
    # 股票池
    # =========================
    universe_loader = UniverseLoader()
    stock_list = universe_loader.get_universe(limit=args.limit)
    logger.info(f"[IC] Loaded universe: {len(stock_list)} stocks")

    # =========================
    # 🚀 加载 panel
    # =========================
    buffer_days = args.horizon * 3

    logger.info(f"[IC] Loading panel with buffer_days={buffer_days}")

    panel = data_loader.load_panel(
        args.start,
        pd.to_datetime(args.end) + pd.Timedelta(days=buffer_days),
        stock_list
    )

    if panel.empty:
        logger.error("[IC] Panel is empty")
        return

    panel["Date"] = pd.to_datetime(panel["Date"])
    panel = panel.sort_values(["Symbol", "Date"])

    # =========================
    # 🚀 提取交易日
    # =========================
    all_dates = sorted(panel["Date"].unique())
    all_dates = pd.to_datetime(all_dates)

    start_dt = pd.to_datetime(args.start)
    end_dt = pd.to_datetime(args.end)

    dates = [d for d in all_dates if start_dt <= d <= end_dt]

    logger.info(f"[IC] Trade dates count (from panel): {len(dates)}")

    # =========================
    # 因子解析
    # =========================
    factors, source = resolve_factors(args, factor_engine)
    logger.info(f"[IC] Factors: {factors}")
    logger.info(f"[IC] Source: {source}")

    # =========================
    # 🚀 一次性算全因子
    # =========================
    logger.info("[IC] Computing ALL factors on full panel (ONCE)")

    panel = factor_engine.pipeline.run(
        panel.set_index("Date"),
        factors=factors
    ).reset_index()

    logger.info(f"[IC] Factor panel shape: {panel.shape}")

    # =========================
    # 🚀 ✅ 全局 missing（关键优化）
    # =========================
    logger.info("[IC] Handling missing data ONCE (global)")

    panel = factor_engine.handle_missing(panel, factors)

    # =========================
    # 🚀 未来收益
    # =========================
    logger.info(f"[IC] Computing future returns (horizon={args.horizon})")

    future_returns_df = data_loader.get_future_returns(
        panel=panel,
        horizon=args.horizon
    )

    future_returns_df["Date"] = pd.to_datetime(future_returns_df["Date"])

    logger.info(f"[IC] Future returns shape: {future_returns_df.shape}")

    # =========================
    # 🚀 🚀 分组缓存（核心优化）
    # =========================
    logger.info("[IC] Building grouped cache (panel / future)")

    panel_grouped = dict(tuple(panel.groupby("Date")))
    future_grouped = dict(tuple(future_returns_df.groupby("Date")))

    # =========================
    # 🚀 并行 IC
    # =========================
    logger.info("[IC] Running parallel IC computation...")

    n_jobs = max(1, os.cpu_count() - 1)

    results = Parallel(
        n_jobs=n_jobs,
        backend="loky"
    )(
        delayed(_ic_worker)(
            date,
            panel_grouped,
            future_grouped,
            factors,
            args.horizon
        )
        for date in dates
    )

    # =========================
    # flatten
    # =========================
    all_ic = [item for sublist in results for item in sublist]

    # =========================
    # 汇总
    # =========================
    ic_df = pd.DataFrame(all_ic)

    if ic_df.empty:
        logger.error("[IC] No results")
        return

    print("\n=== IC Time Series (tail) ===")
    print(ic_df.tail())

    summary = summarize_ic(ic_df)

    print("\n=== IC Summary ===")
    print(summary)

    logger.info(f"[Factor IC] Done | total time: {time.time() - total_start_time:.4f}s")
    logger.info("=" * 50)


# =========================
# CLI 注册
# =========================
def register(subparsers):
    ic_parser = subparsers.add_parser("ic")

    ic_parser.add_argument("--start", required=True)
    ic_parser.add_argument("--end", required=True)
    ic_parser.add_argument("--model", required=False)
    ic_parser.add_argument("--factors", nargs="+")
    ic_parser.add_argument("--horizon", type=int, default=5)
    ic_parser.add_argument("--limit", type=int)

    ic_parser.set_defaults(func=run_factor_ic)
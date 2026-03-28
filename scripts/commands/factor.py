import pandas as pd
import logging
from typing import Dict, List, Tuple
from pathlib import Path
import importlib
import time

# ✅ 替换旧 engine
from features.engine.factor_engine import FactorEngine
from features.engine.scoring_engine import ScoringEngine

from data.loaders.market_loader import MarketDataLoader
from data.loaders.universe_loader import UniverseLoader

# 👉 IC 模块
from features.analysis.ic_temp import (
    summarize_ic,
    compute_snapshot_ic,
    compute_rank_corr
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# =========================
# 🧠 model
# =========================
def load_model(name: str):
    try:
        logger.info(f"[load_model] Loading model: {name}")
        return importlib.import_module(f"models.alpha.{name}")
    except ModuleNotFoundError:
        logger.error(f"[ERROR] model not found: {name}")
        raise ValueError(f"[ERROR] model not found: {name}")

# =========================
# 🧠 factor 解析（核心）
# =========================
def resolve_factors(args, factor_engine):

    # 1️⃣ 用户指定
    if args.factors:
        logger.info(f"[resolve_factors] Using user specified factors: {args.factors}")
        return args.factors, "user"

    # 2️⃣ model
    if args.model:
        logger.info(f"[resolve_factors] Resolving factors from model: {args.model}")
        model = load_model(args.model)

        if hasattr(model, "get_weights"):
            factors = list(model.get_weights().keys())
        elif hasattr(model, "WEIGHTS"):
            factors = list(model.WEIGHTS.keys())
        else:
            logger.error("[resolve_factors] model has no weights")
            raise ValueError("model has no weights")

        return factors, "model"

    # 3️⃣ 全量（正确）
    logger.info("[resolve_factors] Using all available factors from registry")
    return factor_engine.pipeline.registry.list_factors(), "registry"

# =========================
# 🚀 主执行函数
# =========================
def run_factor(args):
    logger.info("=" * 50)
    logger.info("[Factor] Start running factor pipeline")

    # =========================
    # 1️⃣ 初始化（只负责读 parquet）
    # =========================
    data_loader = MarketDataLoader()
    factor_engine = FactorEngine(data_loader)
    scoring_engine = ScoringEngine()

    # =========================
    # 2️⃣ 加载模型
    # =========================
    logger.info(f"[Factor] Loading model: {args.model}")
    model = load_model(args.model)

    # 权重
    if args.weights:
        logger.info(f"[Factor] Using user-specified weights: {args.weights}")
        weights = dict(
            (k.strip(), float(v))
            for k, v in (
                item.split("=") for item in args.weights.split(",")
            )
        )
    else:
        if hasattr(model, "get_weights"):
            logger.info("[Factor] Fetching weights from model")
            weights = model.get_weights(args.date)
        elif hasattr(model, "WEIGHTS"):
            logger.info("[Factor] Fetching weights from model (WEIGHTS)")
            weights = model.WEIGHTS
        else:
            logger.error("[ERROR] model has no weights")
            raise ValueError("[ERROR] model has no weights")

    logger.info(f"[Factor] model = {args.model}")
    logger.info(f"[Factor] weights = {weights}")

    # =========================
    # 3️⃣ 日期
    # =========================
    date = pd.to_datetime(args.date)
    logger.info(f"[Factor] Date = {date}")

    # =========================
    # 4️⃣ 股票池
    # =========================
    logger.info("[Factor] Fetching stock list")
    universe_loader = UniverseLoader()
    stock_list = universe_loader.get_universe(limit=args.limit)

    if not stock_list:
        logger.error("[Factor] stock list is empty")
        return

    logger.info(f"[Factor] universe size = {len(stock_list)}")

    # =========================
    # 5️⃣ 数据加载（替代 engine 内部加载）
    # =========================
    logger.info(f"[Factor] Loading panel data")
    panel = data_loader.load_panel(
        start_date="2000-01-01",
        end_date=date,
        symbols=stock_list
    )

    if panel is None or panel.empty:
        logger.warning("[Factor] empty panel")
        return

    panel["Date"] = pd.to_datetime(panel["Date"])
    panel = panel.sort_values(["Date", "Symbol"])
    panel = panel.set_index("Date")

    # =========================
    # 6️⃣ 因子计算（替代 engine.run）
    # =========================
    snapshot = factor_engine.run_factor_pipeline(
        df=panel,
        date=date,
        factors=list(weights.keys())
    )

    # =========================
    # 7️⃣ 防空
    # =========================
    if snapshot is None or snapshot.empty:
        logger.warning("[Factor] no stocks selected")
        return

    # =========================
    # 8️⃣ 打分（拆出来）
    # =========================
    scored = scoring_engine.score(snapshot, weights)
    selected = scoring_engine.select(scored, args.top_n)

    # =========================
    # 7️⃣ 输出结果
    # =========================
    print("\n=== Top Stocks ===")

    cols = ["Symbol", "score"]
    cols = [c for c in cols if c in selected.columns]

    print(
        selected[cols]
        .head(args.top_n)
        .sort_values("score", ascending=False)
        .to_string(index=False)
    )

    # =========================
    # 因子贡献
    # =========================
    contrib_cols = [
        f"{f}_contrib"
        for f in weights.keys()
        if f"{f}_contrib" in selected.columns
    ]

    print("\n=== Factor Contribution ===")
    print(
        selected[["Symbol", "score"] + contrib_cols]
        .sort_values("score", ascending=False)
        .head(args.top_n)
        .to_string(index=False)
    )

    # =========================
    # 8️⃣ Debug 信息
    # =========================
    print("\n=== Debug Info ===")
    print(f"Total candidates: {len(scored)}")
    print(f"Selected: {len(selected)}")

    if "score" in scored.columns:
        print(
            f"Score range: {scored['score'].min():.4f} ~ {scored['score'].max():.4f}"
        )

    print("\n=== Factor Stats ===")
    for c in contrib_cols:
        print(f"{c}:")
        print(f"  mean     = {selected[c].mean():.4f}")
        print(f"  abs_mean = {selected[c].abs().mean():.4f}")
        print(f"  std      = {selected[c].std():.4f}")

    # =========================
    # Rank Corr
    # =========================
    rank_corr = compute_rank_corr(
        scored,
        target_col="score",
        factors=list(weights.keys())
    )

    print("\n=== Rank Corr ===")
    for k, v in rank_corr.items():
        print(f"{k}: {v:.4f}")

    logger.info("[Factor] Done")
    logger.info("=" * 50)

# =========================
# 🚀 IC
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
    # 🚀 交易日（改为从 panel 提取）
    # =========================
    logger.info("[IC] Extracting trade dates from panel (NO get_trade_dates)")
    dates = None  # 占位，后面从 panel 生成

    # =========================
    # 🚀 加载 panel（带 buffer）
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
    # 🚀 从 panel 提取交易日（替代 get_trade_dates）
    # =========================
    all_dates = sorted(panel["Date"].unique())
    all_dates = pd.to_datetime(all_dates)

    start_dt = pd.to_datetime(args.start)
    end_dt = pd.to_datetime(args.end)

    # 只保留目标区间
    dates = [d for d in all_dates if start_dt <= d <= end_dt]

    if not dates:
        logger.error("[IC] No trade dates in panel range")
        return

    logger.info(f"[IC] Trade dates count (from panel): {len(dates)}")

    # =========================
    # 因子解析
    # =========================
    factors, source = resolve_factors(args, factor_engine)
    logger.info(f"[IC] Factors: {factors}")
    logger.info(f"[IC] Source: {source}")

    # =========================
    # 🚀 一次性计算所有因子（核心优化）
    # =========================
    logger.info("[IC] Computing ALL factors on full panel (ONCE)")

    panel = factor_engine.pipeline.run(
        panel.set_index("Date"),
        factors=factors
    ).reset_index()

    logger.info(f"[IC] Factor panel shape: {panel.shape}")

    # =========================
    # 🚀 未来收益（一次性）
    # =========================
    logger.info(f"[IC] Computing future returns (horizon={args.horizon})")

    future_returns_df = data_loader.get_future_returns(
        panel=panel,
        horizon=args.horizon
    )

    if future_returns_df.empty:
        logger.error("[IC] Future returns is empty")
        return

    future_returns_df["Date"] = pd.to_datetime(future_returns_df["Date"])

    logger.info(f"[IC] Future returns shape: {future_returns_df.shape}")

    # =========================
    # IC 主循环（🔥不再重复算因子）
    # =========================
    all_ic = []

    for date_str in dates:
        date = pd.to_datetime(date_str)
        logger.info(f"[IC] Processing {date_str}")

        try:
            # =========================
            # 🚀 直接取当天截面（不再算因子）
            # =========================
            snapshot = panel[panel["Date"] == date].copy()

            if snapshot is None or snapshot.empty:
                continue

            # =========================
            # 缺失处理（保留）
            # =========================
            snapshot = factor_engine.handle_missing(snapshot, factors)

            # =========================
            # 未来收益截面
            # =========================
            future_ret = future_returns_df[
                future_returns_df["Date"] == date
            ]

            if future_ret.empty:
                continue

            # =========================
            # merge（必须 Date + Symbol）
            # =========================
            merged = snapshot.merge(
                future_ret,
                on=["Date", "Symbol"],
                how="inner"
            )

            if len(merged) < 5:
                continue

            # =========================
            # 因子列
            # =========================
            factor_cols = []
            for f in factors:
                if f"{f}_z" in merged.columns:
                    factor_cols.append(f"{f}_z")
                elif f in merged.columns:
                    factor_cols.append(f)

            # =========================
            # IC 计算
            # =========================
            ic_dict = compute_snapshot_ic(
                merged,
                factor_cols=factor_cols,
                ret_col=f"ret_{args.horizon}d",
                method="spearman"
            )

            for f, ic in ic_dict.items():
                all_ic.append({
                    "date": date_str,
                    "factor": f.replace("_z", ""),
                    "ic": ic
                })

        except Exception as e:
            logger.warning(f"[IC] {date_str} failed: {e}")
            logger.exception(f"[IC] {date_str} failed")
            continue

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

    # =========================
    # 保存
    # =========================
    if args.save:
        Path("outputs").mkdir(exist_ok=True)

        ic_df.to_csv(f"outputs/ic_{args.start}_{args.end}.csv", index=False)
        summary.to_csv(f"outputs/ic_summary_{args.start}_{args.end}.csv", index=False)

        logger.info("[IC] Results saved")

    logger.info(f"[Factor IC] Done | total time: {time.time() - total_start_time:.4f}s")
    logger.info("=" * 50)
    
# =========================
# 🧩 CLI 注册
# =========================
def register(subparsers):
    factor_parser = subparsers.add_parser("factor", help="因子模块")

    subparsers_factor = factor_parser.add_subparsers(
        dest="action",
        required=True
    )

    # =========================
    # factor run
    # =========================
    run_parser = subparsers_factor.add_parser(
        "run",
        help="运行因子选股"
    )

    run_parser.add_argument(
        "--date",
        type=str,
        required=True,
        help="交易日期 YYYYMMDD",
    )

    run_parser.add_argument(
        "--top-n",
        type=int,
        default=50,
        help="选股数量",
    )

    run_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="限制股票池数量（用于测试）",
    )

    run_parser.add_argument(
        "--weights",
        type=str,
        help="因子权重，如 momentum=0.6,volatility=-0.2",
    )

    run_parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="策略模型名称，如 simple_alpha",
    )

    run_parser.add_argument(
        "--save",
        action="store_true",
        help="保存结果到 CSV",
    )

    run_parser.set_defaults(func=run_factor)

    # IC
    ic_parser = subparsers_factor.add_parser("ic")

    ic_parser.add_argument("--start", required=True)
    ic_parser.add_argument("--end", required=True)

    ic_parser.add_argument("--model", required=False)
    ic_parser.add_argument("--factors", nargs="+")
    ic_parser.add_argument("--horizon", type=int, default=5)
    ic_parser.add_argument("--limit", type=int)
    ic_parser.add_argument("--save", action="store_true")

    ic_parser.set_defaults(func=run_factor_ic)
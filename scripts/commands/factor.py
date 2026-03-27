import pandas as pd
import logging
from typing import Dict, List, Tuple
from pathlib import Path
import importlib
import time


from features.engine.cross_sectional_engine import CrossSectionalEngine
from data.loaders.market_loader import MarketDataLoader
from data.loaders.universe_loader import UniverseLoader

# 👉 IC 模块
from features.analysis.ic import (
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
def resolve_factors(args, engine):

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
    return engine.pipeline.registry.list_factors(), "registry"

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
    engine = CrossSectionalEngine(data_loader)

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
    # 5️⃣ 运行引擎
    # =========================
    logger.info(f"[Factor] Running engine with {len(stock_list)} stocks")
    selected, df = engine.run(
        date=date,
        universe=stock_list,
        model=model,
        top_n=args.top_n,
    )

    # =========================
    # 6️⃣ 防空
    # =========================
    if selected is None or selected.empty:
        logger.warning("[Factor] no stocks selected")
        return

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
    print(f"Total candidates: {len(df)}")
    print(f"Selected: {len(selected)}")

    if "score" in df.columns:
        print(
            f"Score range: {df['score'].min():.4f} ~ {df['score'].max():.4f}"
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
        df,
        target_col="score",
        factors=list(weights.keys())
    )

    print("\n=== Rank Corr ===")
    for k, v in rank_corr.items():
        print(f"{k}: {v:.4f}")

    logger.info("[Factor] Done")
    logger.info("=" * 50)

# =========================
# 🚀 IC（重构版）
# =========================
def run_factor_ic(args):
    logger.info("=" * 50)
    logger.info("[Factor IC] Start")

    data_loader = MarketDataLoader()
    engine = CrossSectionalEngine(data_loader)

    # 获取股票池
    universe_loader = UniverseLoader()
    stock_list = universe_loader.get_universe(limit=args.limit)

    # 获取交易日列表
    dates = data_loader.get_trade_dates(args.start, args.end)
    if not dates:
        logger.error("[IC] No trade dates in range")
        return

    # =========================
    # 🚀 关键优化：一次性加载整个区间的面板数据
    # =========================
    logger.info(f"[IC] Preloading panel from {args.start} to {args.end} for {len(stock_list)} stocks")
    
    start_time = time.time()
    
    panel = data_loader.load_panel(args.start, args.end, stock_list)
    if panel.empty:
        logger.error("[IC] Panel is empty")
        return

    end_time = time.time()
    logger.info(f"Loading panel took {end_time - start_time:.4f} seconds")

    # 确定因子列表
    factors, source = resolve_factors(args, engine)
    logger.info(f"[IC] factors = {factors}")
    logger.info(f"[IC] source = {source}")

    all_ic = []

    for date_str in dates:
        date = pd.to_datetime(date_str)
        logger.info(f"[IC] {date_str}")

        # =========================
        # 从预加载面板中提取截至当前日期的历史数据
        # =========================
        hist_df = panel[panel.index <= date].copy()

        if hist_df.empty:
            continue

        start_time = time.time()

        # 调用 engine.run，传入预加载的数据
        try:
            _, df = engine.run(
                date=date,
                universe=stock_list,
                model=None,
                factors=factors,
                top_n=None,
                df=hist_df  # 关键：传入预加载数据
            )

            if df is None or df.empty:
                continue

            # 获取未来收益（也需要预加载优化，但先保持原样）
            future_ret = data_loader.get_future_returns(date_str, horizon=args.horizon)

            if future_ret.empty:
                continue

            merged = df.merge(future_ret, on="Symbol", how="inner")

            if len(merged) < 5:
                continue

            factor_cols = []
            for f in factors:
                if f"{f}_z" in merged.columns:
                    factor_cols.append(f"{f}_z")
                elif f in merged.columns:
                    factor_cols.append(f)

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

    end_time = time.time()
    logger.info(f"Factor calculation took {end_time - start_time:.4f} seconds")

    ic_df = pd.DataFrame(all_ic)

    if ic_df.empty:
        logger.error("[IC] No results")
        return

    print("\n=== IC Time Series (tail) ===")
    print(ic_df.tail())

    summary = summarize_ic(ic_df)

    print("\n=== IC Summary ===")
    print(summary)

    if args.save:
        Path("outputs").mkdir(exist_ok=True)
        ic_df.to_csv(f"outputs/ic_{args.start}_{args.end}.csv", index=False)
        summary.to_csv(f"outputs/ic_summary_{args.start}_{args.end}.csv", index=False)

    logger.info("[Factor IC] Done")
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
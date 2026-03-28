import pandas as pd
import logging
from typing import Dict, List, Tuple
from pathlib import Path
import importlib
import time

# ✅ engine
from features.engine.factor_engine import FactorEngine
from features.engine.scoring_engine import ScoringEngine

from data.loaders.market_loader import MarketDataLoader
from data.loaders.universe_loader import UniverseLoader

# 👉 只保留 rank_corr（用于调试）
from features.analysis.ic_temp import compute_rank_corr

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
# 🚀 Panel Cache（新增核心）
# =========================
def load_panel_with_cache(
    data_loader,
    stock_list,
    date,
    lookback_days=252 * 2
):
    """
    🚀 工业级 panel 加载：

    优化点：
    - 限制历史窗口（避免 24 年数据）
    - 本地缓存 parquet
    """

    cache_dir = Path("cache/panel")
    cache_dir.mkdir(parents=True, exist_ok=True)

    start_date = pd.to_datetime(date) - pd.Timedelta(days=lookback_days)
    end_date = pd.to_datetime(date)

    cache_file = cache_dir / f"panel_{start_date.date()}_{end_date.date()}_{len(stock_list)}.parquet"

    # =========================
    # ✅ cache 命中
    # =========================
    if cache_file.exists():
        logger.info(f"[Factor] Loading panel from cache: {cache_file}")
        panel = pd.read_parquet(cache_file)
        return panel

    # =========================
    # ❌ cache miss → 加载
    # =========================
    logger.info("[Factor] Cache miss → loading panel from disk")

    panel = data_loader.load_panel(
        start_date=start_date,
        end_date=end_date,
        symbols=stock_list
    )

    if panel is None or panel.empty:
        return panel

    # =========================
    # ✅ 写 cache
    # =========================
    panel.to_parquet(cache_file)

    logger.info(f"[Factor] Panel cached → {cache_file}")

    return panel


# =========================
# 🚀 主执行函数（选股）
# =========================
def run_factor(args):
    logger.info("=" * 50)
    logger.info("[Factor] Start running factor pipeline")

    total_start_time = time.time()

    # =========================
    # 1️⃣ 初始化
    # =========================
    data_loader = MarketDataLoader()
    factor_engine = FactorEngine(data_loader)
    scoring_engine = ScoringEngine()

    # =========================
    # 2️⃣ 加载模型
    # =========================
    logger.info(f"[Factor] Loading model: {args.model}")
    model = load_model(args.model)

    # =========================
    # 权重
    # =========================
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
    # 5️⃣ 🚀 数据加载（核心优化）
    # =========================
    logger.info(f"[Factor] Loading panel data (optimized)")

    panel = load_panel_with_cache(
        data_loader=data_loader,
        stock_list=stock_list,
        date=date
    )

    if panel is None or panel.empty:
        logger.warning("[Factor] empty panel")
        return

    panel["Date"] = pd.to_datetime(panel["Date"])
    panel = panel.sort_values(["Symbol", "Date"])

    logger.info(f"[Factor] Panel shape = {panel.shape}")

    # =========================
    # 6️⃣ 🚀 一次性计算所有因子（核心优化）
    # =========================
    logger.info("[Factor] Computing ALL factors on full panel (ONCE)")

    panel = factor_engine.pipeline.run(
        panel.set_index("Date"),
        factors=list(weights.keys())
    ).reset_index()

    logger.info(f"[Factor] Factor panel shape = {panel.shape}")

    # =========================
    # 7️⃣ 🚀 全局 missing 处理（和 IC 一致）
    # =========================
    logger.info("[Factor] Handling missing data (global)")

    panel = factor_engine.handle_missing(
        panel,
        factors=list(weights.keys())
    )

    # =========================
    # 8️⃣ 🚀 snapshot（只在最后切片）
    # =========================
    logger.info(f"[Factor] Extracting snapshot @ {date}")

    snapshot = panel[panel["Date"] == date]

    if snapshot.empty:
        logger.warning("[Factor] snapshot is empty")
        return

    logger.info(f"[Factor] Snapshot size = {len(snapshot)}")

    # =========================
    # 9️⃣ 打分
    # =========================
    scored = scoring_engine.score(snapshot, weights)
    selected = scoring_engine.select(scored, args.top_n)

    # =========================
    # 输出结果
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
    # Debug 信息
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
    # Rank Corr（调试用）
    # =========================
    rank_corr = compute_rank_corr(
        scored,
        target_col="score",
        factors=list(weights.keys())
    )

    print("\n=== Rank Corr ===")
    for k, v in rank_corr.items():
        print(f"{k}: {v:.4f}")

    logger.info(
        f"[Factor] Done | total time: {time.time() - total_start_time:.4f}s"
    )
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

    run_parser = subparsers_factor.add_parser(
        "run",
        help="运行因子选股"
    )

    run_parser.add_argument("--date", type=str, required=True)
    run_parser.add_argument("--top-n", type=int, default=50)
    run_parser.add_argument("--limit", type=int, default=None)
    run_parser.add_argument("--weights", type=str)
    run_parser.add_argument("--model", type=str, required=True)
    run_parser.add_argument("--save", action="store_true")

    run_parser.set_defaults(func=run_factor)
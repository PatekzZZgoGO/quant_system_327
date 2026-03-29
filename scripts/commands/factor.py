import pandas as pd
import logging
import importlib
import time
from pathlib import Path

# ✅ 新架构入口
from data.services.data_service import DataService

# ✅ engine
from features.engine.factor_engine import FactorEngine
from features.engine.scoring_engine import ScoringEngine

# 👉 调试
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
# 🚀 Panel Cache（保留你的优化）
# =========================
def load_panel_with_cache(
    data_service,
    stock_list,
    date,
    lookback_days=252 * 2
):
    """
    工业级 panel 加载（带缓存）

    优化点：
    - 限制历史窗口
    - parquet 本地缓存
    - 统一走 DataService
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
        return pd.read_parquet(cache_file)

    # =========================
    # ❌ cache miss → DataService
    # =========================
    logger.info("[Factor] Cache miss → loading panel via DataService")

    market = data_service.get_panel(
        stock_list,
        start_date,
        end_date
    )

    panel = market.panel

    if panel is None or panel.empty:
        return panel

    # =========================
    # 写 cache
    # =========================
    panel.to_parquet(cache_file)

    logger.info(f"[Factor] Panel cached → {cache_file}")

    return panel


# =========================
# 🚀 主执行函数
# =========================
def run_factor(args):

    logger.info("=" * 50)
    logger.info("[Factor] Start running factor pipeline")

    total_start_time = time.time()

    # =========================
    # 🧠 初始化（新架构）
    # =========================
    data_service = DataService("data/datasets/processed/stocks")

    factor_engine = FactorEngine(None)  # ⚠️ 已不依赖 data_loader
    scoring_engine = ScoringEngine()

    # =========================
    # 📦 Universe（Domain）
    # =========================
    universe = data_service.get_universe(limit=args.limit)

    stock_list = universe.symbols

    if not stock_list:
        logger.error("[Factor] stock list is empty")
        return

    logger.info(f"[Factor] Universe size = {universe.size()}")

    # =========================
    # 🧠 加载模型
    # =========================
    logger.info(f"[Factor] Loading model: {args.model}")
    model = load_model(args.model)

    # =========================
    # 权重解析
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
            weights = model.get_weights(args.date)
        elif hasattr(model, "WEIGHTS"):
            weights = model.WEIGHTS
        else:
            raise ValueError("[ERROR] model has no weights")

    logger.info(f"[Factor] weights = {weights}")

    # =========================
    # 日期
    # =========================
    date = pd.to_datetime(args.date)

    # =========================
    # 🚀 Panel（通过 DataService）
    # =========================
    panel = load_panel_with_cache(
        data_service=data_service,
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
    # 🚀 一次性计算因子（核心）
    # =========================
    logger.info("[Factor] Computing ALL factors (ONCE)")

    panel = factor_engine.pipeline.run(
        panel.set_index("Date"),
        factors=list(weights.keys())
    ).reset_index()

    logger.info(f"[Factor] Factor panel shape = {panel.shape}")

    # =========================
    # 🚀 missing 统一处理
    # =========================
    panel = factor_engine.handle_missing(
        panel,
        factors=list(weights.keys())
    )

    # =========================
    # 🚀 snapshot（最后才 slice）
    # =========================
    snapshot = panel[panel["Date"] == date]

    if snapshot.empty:
        logger.warning("[Factor] snapshot is empty")
        return

    logger.info(f"[Factor] Snapshot size = {len(snapshot)}")

    # =========================
    # 🏆 打分
    # =========================
    scored = scoring_engine.score(snapshot, weights)
    selected = scoring_engine.select(scored, args.top_n)

    # =========================
    # 输出
    # =========================
    print("\n=== Top Stocks ===")

    print(
        selected[["Symbol", "score"]]
        .sort_values("score", ascending=False)
        .head(args.top_n)
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
    # Debug
    # =========================
    print("\n=== Debug Info ===")
    print(f"Total candidates: {len(scored)}")
    print(f"Selected: {len(selected)}")

    if "score" in scored.columns:
        print(
            f"Score range: {scored['score'].min():.4f} ~ {scored['score'].max():.4f}"
        )

    # =========================
    # Rank Corr（调试）
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
# CLI 注册
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
import pandas as pd
import logging
import time
import importlib

from data.services.data_service import DataService
from data.domains.returns_domain import Returns

from features.engine.factor_engine import FactorEngine
from features.analysis.ic_temp import summarize_ic

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# =========================
# 模型加载
# =========================
def load_model(name: str):
    return importlib.import_module(f"models.alpha.{name}")


# =========================
# 因子解析
# =========================
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
# 🚀 IC 主函数
# =========================
def run_factor_ic(args):

    logger.info("=" * 50)
    logger.info("[Factor IC] Start")

    total_start_time = time.time()

    # =========================
    # 🧠 初始化 DataService
    # =========================
    data_service = DataService("data/datasets/processed/stocks")

    factor_engine = FactorEngine(None)

    logger.info("[IC] Initialized DataService & FactorEngine")

    # =========================
    # 🧾 Universe（Domain）
    # =========================
    universe = data_service.get_universe(limit=args.limit)

    logger.info(f"[IC] Universe size: {universe.size()} | head: {universe.head()}")

    stock_list = universe.symbols

    # =========================
    # 📊 Panel（Domain）
    # =========================
    buffer_days = args.horizon * 3

    logger.info(f"[IC] Loading panel with buffer_days={buffer_days}")

    market = data_service.get_panel(
        stock_list,
        args.start,
        pd.to_datetime(args.end) + pd.Timedelta(days=buffer_days)
    )

    panel = market.panel

    if panel.empty:
        logger.error("[IC] Panel is empty")
        return

    logger.info(f"[IC] Panel shape: {panel.shape}")

    # =========================
    # 因子解析
    # =========================
    factors, source = resolve_factors(args, factor_engine)

    logger.info(f"[IC] Factors: {factors}")
    logger.info(f"[IC] Source: {source}")

    # =========================
    # 🚀 全量因子计算（一次性）
    # =========================
    logger.info("[IC] Computing ALL factors on full panel")

    panel = factor_engine.pipeline.run(
        panel.set_index("Date"),
        factors=factors
    ).reset_index()

    logger.info(f"[IC] Factor panel shape: {panel.shape}")

    # =========================
    # 缺失处理
    # =========================
    logger.info("[IC] Handling missing data")

    panel = factor_engine.handle_missing(panel, factors)

    # =========================
    # 🚀 Future Return（Domain）
    # =========================
    logger.info(f"[IC] Computing future returns (horizon={args.horizon})")

    ret = Returns(panel)
    panel = ret.forward(horizon=args.horizon)

    ret_col = f"ret_{args.horizon}d"

    logger.info("[IC] Future return computed")

    # =========================
    # 🚀 IC（vectorized）
    # =========================
    logger.info("[IC] Computing IC (vectorized)")

    factor_cols = [
        f"{f}_z" if f"{f}_z" in panel.columns else f
        for f in factors
    ]

    use_cols = ["Date", ret_col] + factor_cols

    df_ic = panel[use_cols].dropna()

    if df_ic.empty:
        logger.error("[IC] No valid data after dropna")
        return

    logger.info(f"[IC] IC input shape: {df_ic.shape}")

    # =========================
    # 核心：groupby IC
    # =========================
    def compute_ic_block(x):

        if len(x) < 5:
            return pd.Series([None] * len(factor_cols), index=factor_cols)

        return x[factor_cols].corrwith(x[ret_col], method="spearman")

    ic_matrix = df_ic.groupby("Date").apply(compute_ic_block)

    # =========================
    # 转长表
    # =========================
    ic_df = (
        ic_matrix
        .stack()
        .reset_index()
        .rename(columns={
            "level_1": "factor",
            0: "ic"
        })
    )

    ic_df["factor"] = ic_df["factor"].str.replace("_z", "")

    if ic_df.empty:
        logger.error("[IC] No IC results")
        return

    print("\n=== IC Time Series (tail) ===")
    print(ic_df.tail())

    # =========================
    # 汇总
    # =========================
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
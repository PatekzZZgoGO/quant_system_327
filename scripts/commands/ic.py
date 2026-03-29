import pandas as pd
import logging
import time
import importlib

# ✅ Data Layer
from data.services.data_service import DataService
from data.domains.returns_domain import Returns
from data.domains.ic_domain import IC

# ✅ Factor
from features.engine.factor_engine import FactorEngine

# ✅ 分析
from features.analysis.ic_temp import summarize_ic

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# =========================
# 🧠 model
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
# 🚀 主函数
# =========================
def run_factor_ic(args):

    logger.info("=" * 50)
    logger.info("[Factor IC] Start")

    total_start_time = time.time()

    # =========================
    # 初始化
    # =========================
    data_service = DataService("data/datasets/processed/stocks")
    factor_engine = FactorEngine(None)

    logger.info("[IC] Initialized DataService & FactorEngine")

    # =========================
    # Universe
    # =========================
    universe = data_service.get_universe(limit=args.limit)
    stock_list = universe.symbols

    logger.info(f"[IC] Universe size: {universe.size()}")

    # =========================
    # Panel
    # =========================
    buffer_days = args.horizon * 3

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

    logger.info(f"[IC] Factors: {factors} | Source: {source}")

    # =========================
    # 🚀 因子计算（一次性）
    # =========================
    panel = factor_engine.pipeline.run(
        panel.set_index("Date"),
        factors=factors
    ).reset_index()

    logger.info(f"[IC] Factor panel shape: {panel.shape}")

    # =========================
    # 缺失处理
    # =========================
    panel = factor_engine.handle_missing(panel, factors)

    # =========================
    # 🚀 Future Return
    # =========================
    ret = Returns(panel)
    panel = ret.forward(horizon=args.horizon)

    ret_col = f"ret_{args.horizon}d"

    logger.info("[IC] Future return computed")
    
    print("\n=== DEBUG: AFTER RETURNS ===")
    print(panel.columns.tolist())

    # =========================
    # 🚀 IC Domain
    # =========================
    ic_engine = IC(panel)

    ic_df = ic_engine.compute(
        factors=factors,
        ret_col=ret_col,
        method="spearman"
    )

    if ic_df.empty:
        logger.error("[IC] No IC results")
        return

    # =========================
    # 输出
    # =========================
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
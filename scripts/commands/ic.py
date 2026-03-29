import importlib
import logging
import time

import pandas as pd

from data.domains.ic_domain import IC
from data.domains.returns_domain import Returns
from data.services.data_service import DataService
from features.analysis.ic_temp import summarize_ic
from features.engine.factor_engine import FactorEngine

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def load_model(name: str):
    return importlib.import_module(f"models.alpha.{name}")


def resolve_factors(args, factor_engine):
    if args.factors:
        return args.factors, "user"

    if args.model:
        model = load_model(args.model)
        if hasattr(model, "get_weights"):
            return list(model.get_weights().keys()), "model"
        if hasattr(model, "WEIGHTS"):
            return list(model.WEIGHTS.keys()), "model"

    return factor_engine.pipeline.registry.list_factors(), "registry"


def print_ic_result(ic_df, summary):
    print("\n=== IC Time Series (tail) ===")
    print(ic_df.tail())

    print("\n=== IC Summary ===")
    print(summary)


def run_factor_ic(args):
    logger.info("=" * 50)
    logger.info("[Factor IC] Start")
    total_start_time = time.time()

    data_service = DataService()
    factor_engine = FactorEngine(None)

    universe = data_service.get_analysis_universe(limit=args.limit)
    stock_list = universe.symbols
    logger.info(f"[IC] Universe size: {universe.size()}")

    factors, source = resolve_factors(args, factor_engine)
    logger.info(f"[IC] Factors: {factors} | Source: {source}")

    cached_result = data_service.load_ic_analysis(
        start=args.start,
        end=args.end,
        horizon=args.horizon,
        limit=args.limit,
        model=args.model,
        factors=factors,
    )
    if cached_result is not None:
        logger.info("[IC] IC cache hit")
        print_ic_result(cached_result["ic_df"], cached_result["summary"])
        return

    panel = data_service.get_analysis_ic_panel(
        symbols=stock_list,
        start=args.start,
        end=args.end,
        horizon=args.horizon,
        use_cache=True,
    ).panel
    if panel.empty:
        logger.error("[IC] Panel is empty")
        return

    logger.info(f"[IC] Panel shape: {panel.shape}")
    panel = factor_engine.pipeline.run(panel.set_index("Date"), factors=factors).reset_index()
    panel = factor_engine.handle_missing(panel, factors)

    ret = Returns(panel)
    panel = ret.forward(horizon=args.horizon)
    ret_col = f"ret_{args.horizon}d"

    ic_engine = IC(panel)
    ic_df = ic_engine.compute(factors=factors, ret_col=ret_col, method="spearman")
    if ic_df.empty:
        logger.error("[IC] No IC results")
        return

    summary = summarize_ic(ic_df)
    data_service.save_ic_analysis(
        start=args.start,
        end=args.end,
        horizon=args.horizon,
        limit=args.limit,
        model=args.model,
        factors=factors,
        ic_df=ic_df,
        summary_df=summary,
        metadata={
            "factors": factors,
            "source": source,
            "start": args.start,
            "end": args.end,
            "horizon": args.horizon,
        },
    )
    print_ic_result(ic_df, summary)

    logger.info(f"[Factor IC] Done | total time: {time.time() - total_start_time:.4f}s")
    logger.info("=" * 50)


def register(subparsers):
    ic_parser = subparsers.add_parser("ic")
    ic_parser.add_argument("--start", required=True)
    ic_parser.add_argument("--end", required=True)
    ic_parser.add_argument("--model", required=False)
    ic_parser.add_argument("--factors", nargs="+")
    ic_parser.add_argument("--horizon", type=int, default=5)
    ic_parser.add_argument("--limit", type=int)
    ic_parser.set_defaults(func=run_factor_ic)

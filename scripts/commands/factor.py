import importlib
import logging
import time

import pandas as pd

from data.services.data_service import DataService
from features.analysis.ic_temp import compute_rank_corr
from features.engine.factor_engine import FactorEngine
from features.engine.scoring_engine import ScoringEngine

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def load_model(name: str):
    try:
        logger.info(f"[load_model] Loading model: {name}")
        return importlib.import_module(f"models.alpha.{name}")
    except ModuleNotFoundError:
        logger.error(f"[ERROR] model not found: {name}")
        raise ValueError(f"[ERROR] model not found: {name}")


def resolve_weights(args, model):
    if args.weights:
        logger.info(f"[Factor] Using user weights: {args.weights}")
        return dict((k.strip(), float(v)) for k, v in (item.split("=") for item in args.weights.split(",")))

    if hasattr(model, "get_weights"):
        return model.get_weights(args.date)
    if hasattr(model, "WEIGHTS"):
        return model.WEIGHTS
    raise ValueError("[ERROR] model has no weights")


def print_factor_result(scored, weights, top_n, rank_corr):
    selected = scored.sort_values("score", ascending=False).head(top_n)

    print("\n=== Top Stocks ===")
    print(selected[["Symbol", "score"]].to_string(index=False))

    contrib_cols = [f"{factor}_contrib" for factor in weights.keys() if f"{factor}_contrib" in selected.columns]
    print("\n=== Factor Contribution ===")
    print(selected[["Symbol", "score"] + contrib_cols].to_string(index=False))

    print("\n=== Debug Info ===")
    print(f"Total candidates: {len(scored)}")
    print(f"Selected: {len(selected)}")
    if "score" in scored.columns:
        print(f"Score range: {scored['score'].min():.4f} ~ {scored['score'].max():.4f}")

    print("\n=== Rank Corr ===")
    for key, value in rank_corr.items():
        print(f"{key}: {value:.4f}")


def run_factor(args):
    logger.info("=" * 50)
    logger.info("[Factor] Start running factor pipeline")
    total_start_time = time.time()

    data_service = DataService()
    factor_engine = FactorEngine(None)
    scoring_engine = ScoringEngine()

    universe = data_service.get_analysis_universe(limit=args.limit)
    stock_list = universe.symbols
    if not stock_list:
        logger.error("[Factor] stock list is empty")
        return

    logger.info(f"[Factor] Universe size = {universe.size()}")
    model = load_model(args.model)
    weights = resolve_weights(args, model)
    logger.info(f"[Factor] weights = {weights}")

    date = pd.to_datetime(args.date)
    cached_result = data_service.load_factor_analysis(
        date=date,
        model=args.model,
        weights=weights,
        top_n=args.top_n,
        limit=args.limit,
    )
    if cached_result is not None:
        logger.info("[Factor] Factor cache hit")
        print_factor_result(cached_result["scored"], weights, args.top_n, cached_result["metadata"]["rank_corr"])
        return

    panel = data_service.get_analysis_factor_panel(stock_list, date, use_cache=True).panel
    if panel is None or panel.empty:
        logger.warning("[Factor] empty panel")
        return

    logger.info(f"[Factor] Panel shape = {panel.shape}")
    panel = factor_engine.pipeline.run(panel.set_index("Date"), factors=list(weights.keys())).reset_index()
    panel = factor_engine.handle_missing(panel, factors=list(weights.keys()))

    snapshot = panel[panel["Date"] == date]
    if snapshot.empty:
        logger.warning("[Factor] snapshot is empty")
        return

    scored = scoring_engine.score(snapshot, weights)
    rank_corr = compute_rank_corr(scored, target_col="score", factors=list(weights.keys()))
    data_service.save_factor_analysis(
        date=date,
        model=args.model,
        weights=weights,
        top_n=args.top_n,
        limit=args.limit,
        scored=scored,
        metadata={
            "rank_corr": rank_corr,
            "weights": weights,
            "date": date.strftime("%Y-%m-%d"),
            "model": args.model,
        },
    )
    print_factor_result(scored, weights, args.top_n, rank_corr)

    logger.info(f"[Factor] Done | total time: {time.time() - total_start_time:.4f}s")
    logger.info("=" * 50)


def register(subparsers):
    factor_parser = subparsers.add_parser("factor", help="factor module")
    subparsers_factor = factor_parser.add_subparsers(dest="action", required=True)

    run_parser = subparsers_factor.add_parser("run", help="run factor selection")
    run_parser.add_argument("--date", type=str, required=True)
    run_parser.add_argument("--top-n", type=int, default=50)
    run_parser.add_argument("--limit", type=int, default=None)
    run_parser.add_argument("--weights", type=str)
    run_parser.add_argument("--model", type=str, required=True)
    run_parser.add_argument("--save", action="store_true")
    run_parser.set_defaults(func=run_factor)

import logging

from pipelines.factor_pipeline import run_factor_pipeline

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


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
    try:
        result = run_factor_pipeline(
            date=args.date,
            model_name=args.model,
            top_n=args.top_n,
            limit=args.limit,
            user_weights=args.weights,
        )
    except ValueError as exc:
        logger.error(str(exc))
        return

    logger.info("[Factor] Universe size = %s", result["universe_size"])
    logger.info("[Factor] weights = %s", result["weights"])
    if result["from_cache"]:
        logger.info("[Factor] Factor cache hit")

    print_factor_result(result["scored"], result["weights"], args.top_n, result["rank_corr"])


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

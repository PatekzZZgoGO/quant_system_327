import logging

from application.shared.ic_app import run_ic_analysis

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def print_ic_result(ic_df, summary):
    print("\n=== IC Time Series (tail) ===")
    print(ic_df.tail())

    print("\n=== IC Summary ===")
    print(summary)


def run_factor_ic(args):
    try:
        result = run_ic_analysis(
            start=args.start,
            end=args.end,
            horizon=args.horizon,
            limit=args.limit,
            model_name=args.model,
            user_factors=args.factors,
        )
    except ValueError as exc:
        logger.error(str(exc))
        return

    logger.info("[IC] Universe size: %s", result["universe_size"])
    logger.info("[IC] Factors: %s | Source: %s", result["factors"], result["source"])
    if result["from_cache"]:
        logger.info("[IC] IC cache hit")

    print_ic_result(result["ic_df"], result["summary"])


def register(subparsers):
    ic_parser = subparsers.add_parser("ic")
    ic_parser.add_argument("--start", required=True)
    ic_parser.add_argument("--end", required=True)
    ic_parser.add_argument("--model", required=False)
    ic_parser.add_argument("--factors", nargs="+")
    ic_parser.add_argument("--horizon", type=int, default=5)
    ic_parser.add_argument("--limit", type=int)
    ic_parser.set_defaults(func=run_factor_ic)

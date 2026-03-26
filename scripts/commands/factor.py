import pandas as pd
import logging
from typing import Dict
from pathlib import Path

from features.engine.cross_sectional_engine import CrossSectionalEngine
from data.loaders.market_loader import MarketDataLoader

logger = logging.getLogger(__name__)


# =========================
# 📂 本地股票池读取（关键）
# =========================
def load_stock_list():
    path = Path("data/datasets/processed/stock_list.csv")

    if not path.exists():
        raise FileNotFoundError(
            "❌ stock_list.csv 不存在，请先运行:\n"
            "python run.py data update stocks"
        )

    df = pd.read_csv(path)

    if "symbol" not in df.columns:
        raise ValueError("❌ stock_list.csv 缺少 symbol 列")

    stock_list = df["symbol"].dropna().astype(str).tolist()

    return stock_list


# =========================
# 🧠 权重解析
# =========================
def parse_weights(w_str: str) -> Dict[str, float]:
    try:
        return dict(
            (k.strip(), float(v))
            for k, v in (
                item.split("=") for item in w_str.split(",")
            )
        )
    except Exception:
        raise ValueError(
            f"[ERROR] Invalid weights format: {w_str}\n"
            f"Example: momentum=0.6,volatility=-0.2"
        )


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
    # 2️⃣ 权重
    # =========================
    if args.weights:
        weights = parse_weights(args.weights)
    else:
        weights = {
            "momentum": 0.6,
            "volatility": -0.2,
            "liquidity": 0.2,
        }

    logger.info(f"[Factor] weights = {weights}")

    # =========================
    # 3️⃣ 日期
    # =========================
    date = pd.to_datetime(args.date)

    # =========================
    # 4️⃣ 股票池（🔥 改这里）
    # =========================
    stock_list = load_stock_list()

    if not stock_list:
        logger.error("[Factor] stock list is empty")
        return

# 🚀 测试模式：限制股票数量
    if args.limit:
        stock_list = stock_list[:args.limit]
        logger.info(f"[Factor] TEST MODE: limit = {args.limit}")

    logger.info(f"[Factor] universe size = {len(stock_list)}")

    logger.info(f"[Factor] universe size = {len(stock_list)}")

    # =========================
    # 5️⃣ 运行引擎
    # =========================
    selected, df = engine.run(
        date=date,
        universe=stock_list,
        weights=weights,
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
    # 8️⃣ Debug 信息
    # =========================
    print("\n=== Debug Info ===")
    print(f"Total candidates: {len(df)}")
    print(f"Selected: {len(selected)}")

    if "score" in df.columns:
        print(
            f"Score range: {df['score'].min():.4f} ~ {df['score'].max():.4f}"
        )

    # =========================
    # 9️⃣ 保存结果
    # =========================
    if args.save:
        output_path = f"outputs/top_{args.top_n}_{args.date}.csv"

        try:
            Path("outputs").mkdir(exist_ok=True)
            selected.to_csv(output_path, index=False)
            logger.info(f"[Factor] saved to {output_path}")
        except Exception as e:
            logger.warning(f"[Factor] save failed: {e}")

    logger.info("[Factor] Done")
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
        "--save",
        action="store_true",
        help="保存结果到 CSV",
    )

    run_parser.set_defaults(func=run_factor)
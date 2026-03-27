import pandas as pd
import logging
from typing import Dict
from pathlib import Path
import importlib

from features.engine.cross_sectional_engine import CrossSectionalEngine
from data.loaders.market_loader import MarketDataLoader

# 👉 IC 模块
from features.analysis.ic import (
    summarize_ic,
    compute_rank_corr
)

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

def load_model(name: str):
    try:
        module = importlib.import_module(f"models.alpha.{name}")
        return module
    except ModuleNotFoundError:
        raise ValueError(f"[ERROR] model not found: {name}")

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
    model = load_model(args.model)

    # 权重
    if args.weights:
        weights = parse_weights(args.weights)
        logger.info("[Factor] Using CLI weights override")
    else:
        if hasattr(model, "get_weights"):
            weights = model.get_weights(args.date)
        elif hasattr(model, "WEIGHTS"):
            weights = model.WEIGHTS
        else:
            raise ValueError("[ERROR] model has no weights")

    logger.info(f"[Factor] model = {args.model}")
    logger.info(f"[Factor] weights = {weights}")

    # =========================
    # 3️⃣ 日期
    # =========================
    date = pd.to_datetime(args.date)

    # =========================
    # 4️⃣ 股票池
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


    # =========================
    # 5️⃣ 运行引擎
    # =========================
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

    print("\n=== Rank Corr (vs score) ===")
    for k, v in rank_corr.items():
        print(f"{k}: {v:.4f}")

    # =========================
    # 9️⃣ 保存结果
    # =========================
    if args.save:
        Path("outputs").mkdir(exist_ok=True)
        output_path = f"outputs/top_{args.top_n}_{args.date}.csv"
        selected.to_csv(output_path, index=False)
        logger.info(f"[Factor] saved to {output_path}")

    logger.info("[Factor] Done")
    logger.info("=" * 50)


# =========================
# 🚀 IC Time Series（独立命令）
# =========================
def run_factor_ic(args):
    logger.info("=" * 50)
    logger.info("[Factor IC] Start")

    data_loader = MarketDataLoader()
    engine = CrossSectionalEngine(data_loader)

    model = load_model(args.model)

    dates = data_loader.get_trade_dates(args.start, args.end)
    stock_list = load_stock_list()

    if args.limit:
        stock_list = stock_list[:args.limit]
        logger.info(f"[IC] TEST MODE limit = {args.limit}")

    all_ic = []

    for date in dates:
        logger.info(f"[IC] {date}")

        try:
            _, df = engine.run(
                date=pd.to_datetime(date),
                universe=stock_list,
                model=model,
                top_n=None  # ⚠️必须
            )

            if df is None or df.empty:
                continue

            future_ret = data_loader.get_future_returns(
                date=date,
                horizon=args.horizon
            )

            merged = df.merge(future_ret, on="Symbol", how="inner")

            if merged.empty:
                continue

            if hasattr(model, "get_weights"):
                weights = model.get_weights(date)
            elif hasattr(model, "WEIGHTS"):
                weights = model.WEIGHTS
            else:
                raise ValueError("model has no weights")

            for f in weights.keys():

                col = f"{f}_z" if f"{f}_z" in merged.columns else f

                if col not in merged.columns:
                    continue

                ic = merged[col].corr(
                    merged[f"ret_{args.horizon}d"]
                )

                all_ic.append({
                    "date": date,
                    "factor": f,
                    "ic": ic
                })

        except Exception as e:
            logger.warning(f"[IC] {date} failed: {e}")
            continue

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

    # ic
    ic_parser = subparsers_factor.add_parser("ic", help="IC 分析")
    ic_parser.add_argument("--start", type=str, required=True)
    ic_parser.add_argument("--end", type=str, required=True)
    ic_parser.add_argument("--model", type=str, required=True)
    ic_parser.add_argument("--horizon", type=int, default=5)
    ic_parser.add_argument("--limit", type=int, default=None) 
    ic_parser.add_argument("--save", action="store_true")
    ic_parser.set_defaults(func=run_factor_ic)
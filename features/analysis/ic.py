import pandas as pd
import numpy as np
from typing import List, Dict


# =========================
# 📊 单日 IC（通用版）
# =========================
def compute_snapshot_ic(
    df: pd.DataFrame,
    factor_cols: List[str],
    ret_col: str,
    method: str = "spearman"
) -> Dict[str, float]:
    """
    df 必须包含：
        Symbol, factor_cols, ret_col
    """

    results = {}

    if ret_col not in df.columns:
        return results

    for f in factor_cols:
        if f not in df.columns:
            continue

        sub = df[[f, ret_col]].dropna()

        if len(sub) < 5:
            continue

        ic = sub[f].corr(sub[ret_col], method=method)

        results[f] = ic

    return results


# =========================
# 📈 IC Time Series（新版推荐）
# =========================
def compute_ic_time_series(
    engine,
    data_loader,
    model,
    dates: List[str],
    factors: List[str],
    horizon: int = 5,
    universe: List[str] = None,
) -> pd.DataFrame:
    """
    🚀 正确版本（无未来函数）

    因子来自：
        engine.run(date)

    收益来自：
        data_loader.get_future_returns(date, horizon)
    """

    all_ic = []

    for date in dates:

        try:
            # =========================
            # 1️⃣ 因子（t）
            # =========================
            _, df = engine.run(
                date=date,
                universe=universe,
                model=model,
                top_n=None
            )

            if df is None or df.empty:
                continue

            # =========================
            # 2️⃣ 未来收益（t+N）
            # =========================
            future_ret = data_loader.get_future_returns(
                date=date,
                horizon=horizon
            )

            if future_ret is None or future_ret.empty:
                continue

            # =========================
            # 3️⃣ merge
            # =========================
            merged = df.merge(
                future_ret,
                on="Symbol",
                how="inner"
            )

            if len(merged) < 5:
                continue

            # =========================
            # 4️⃣ 权重 → 因子列表
            # =========================
            if hasattr(model, "get_weights"):
                weights = model.get_weights(date)
            elif hasattr(model, "WEIGHTS"):
                weights = model.WEIGHTS
            else:
                continue

            factor_cols = []
            for f in weights.keys():
                if f"{f}_z" in merged.columns:
                    factor_cols.append(f"{f}_z")
                elif f in merged.columns:
                    factor_cols.append(f)

            # =========================
            # 5️⃣ IC
            # =========================
            ic_dict = compute_snapshot_ic(
                merged,
                factor_cols=factor_cols,
                ret_col=f"ret_{horizon}d"
            )

            for f, ic in ic_dict.items():
                all_ic.append({
                    "date": date,
                    "factor": f,
                    "ic": ic
                })

        except Exception as e:
            print(f"[IC ERROR] {date}: {e}")
            continue

    ic_df = pd.DataFrame(all_ic)

    return ic_df


# =========================
# 📊 IC统计（修复版）
# =========================
def summarize_ic(ic_df: pd.DataFrame) -> pd.DataFrame:
    """
    输出：
        factor, mean, std, ir
    """

    if ic_df is None or ic_df.empty:
        return pd.DataFrame()

    results = []

    for factor, group in ic_df.groupby("factor"):

        s = group["ic"].dropna()

        if len(s) == 0:
            continue

        mean = s.mean()
        std = s.std()
        ir = mean / std if std != 0 else np.nan

        results.append({
            "factor": factor,
            "mean": mean,
            "std": std,
            "ir": ir
        })

    return pd.DataFrame(results).sort_values("ir", ascending=False)


# =========================
# 📊 Rank Corr（保持不变）
# =========================
def compute_rank_corr(
    df: pd.DataFrame,
    target_col: str,
    factors: List[str]
) -> Dict[str, float]:

    results = {}

    if target_col not in df.columns:
        return results

    target_rank = df[target_col].rank()

    for f in factors:
        if f not in df.columns:
            continue

        corr = target_rank.corr(df[f].rank())
        results[f] = corr

    return results
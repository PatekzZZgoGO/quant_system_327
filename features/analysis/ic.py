import pandas as pd
import numpy as np
from typing import List, Dict


def compute_snapshot_ic(
    df: pd.DataFrame,
    factor_cols: List[str],
    ret_col: str,
    method: str = "spearman"
) -> Dict[str, float]:

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


def summarize_ic(ic_df: pd.DataFrame) -> pd.DataFrame:

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
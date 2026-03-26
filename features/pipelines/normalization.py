# 因子标准化
import pandas as pd
import numpy as np


# =========================
# 📊 Z-Score 标准化（横截面）
# =========================
def zscore(series: pd.Series) -> pd.Series:
    """
    标准化（横截面）

    ⚠️ 注意：
    - 只能用于“同一时点”的数据（snapshot）
    - 不用于时间序列
    """
    std = series.std()

    if std == 0 or np.isnan(std):
        return pd.Series(0, index=series.index)

    return (series - series.mean()) / std


# =========================
# 📉 Winsorize（分位数去极值）
# =========================
def winsorize(series: pd.Series, lower=0.01, upper=0.99) -> pd.Series:
    """
    分位数去极值（简单版）

    参数：
    - lower: 下分位（默认1%）
    - upper: 上分位（默认99%）
    """
    if series.empty:
        return series

    low = series.quantile(lower)
    high = series.quantile(upper)

    return series.clip(low, high)


# =========================
# 👻 MAD 去极值（机构常用）
# =========================
def mad_winsorize(series: pd.Series, n=3) -> pd.Series:
    """
    MAD（Median Absolute Deviation）去极值

    比 quantile 更稳健，机构常用
    """
    median = series.median()
    mad = (series - median).abs().median()

    if mad == 0 or np.isnan(mad):
        return series

    lower = median - n * mad
    upper = median + n * mad

    return series.clip(lower, upper)


# =========================
# 🧠 标准化 Pipeline（可选）
# =========================
def normalize_factor(
    series: pd.Series,
    method: str = "zscore",
    winsor: bool = False
) -> pd.Series:
    """
    因子标准化统一入口

    参数：
    - method: zscore / rank（预留）
    - winsor: 是否先去极值
    """

    s = series.copy()

    # =========================
    # 1️⃣ 去极值
    # =========================
    if winsor:
        s = mad_winsorize(s)

    # =========================
    # 2️⃣ 标准化
    # =========================
    if method == "zscore":
        return zscore(s)

    elif method == "rank":
        return s.rank(pct=True)

    else:
        raise ValueError(f"Unknown normalize method: {method}")
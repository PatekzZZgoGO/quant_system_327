import pandas as pd


def clean_market_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    🚀 市场数据统一清洗（唯一入口）

    做的事情：
    ✔ Date 标准化
    ✔ 排序（极关键）
    ✔ 去重
    ✔ 基础缺失处理
    """

    if df is None or df.empty:
        return df

    df = df.copy()

    # =========================
    # 日期标准化
    # =========================
    df["Date"] = pd.to_datetime(df["Date"])

    # =========================
    # 排序（核心）
    # =========================
    df = df.sort_values(["Symbol", "Date"])

    # =========================
    # 去重
    # =========================
    df = df.drop_duplicates(subset=["Date", "Symbol"])

    # =========================
    # 基础清洗
    # =========================
    if "Close" in df.columns:
        df = df.dropna(subset=["Close"])

    return df.reset_index(drop=True)
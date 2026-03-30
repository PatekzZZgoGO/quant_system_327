import pandas as pd

from exceptions.data import SchemaValidationError


def align_price_basic(price_df: pd.DataFrame, basic_df: pd.DataFrame) -> pd.DataFrame:
    """
    🚀 price + basic 对齐（防未来函数版本）

    核心方法：
        pandas.merge_asof

    关键点：
        ✔ 按 Date 对齐
        ✔ 使用 direction="backward"（只看过去）
        ✔ 按 Symbol 分组（避免跨股票污染）

    参数:
        price_df: 行情数据（必须包含 Date, Symbol）
        basic_df: 基本面数据（必须包含 Date, Symbol）

    返回:
        对齐后的 DataFrame
    """

    if price_df is None or price_df.empty:
        return price_df

    if basic_df is None or basic_df.empty:
        return price_df

    # =========================
    # 🛡️ 防御式检查
    # =========================
    required_cols = {"Date", "Symbol"}

    if not required_cols.issubset(price_df.columns):
        raise SchemaValidationError(
            f"price_df 缺少必要列: {required_cols - set(price_df.columns)}"
        )

    if not required_cols.issubset(basic_df.columns):
        raise SchemaValidationError(
            f"basic_df 缺少必要列: {required_cols - set(basic_df.columns)}"
        )

    # =========================
    # 📅 时间标准化
    # =========================
    price_df = price_df.copy()
    basic_df = basic_df.copy()

    price_df["Date"] = pd.to_datetime(price_df["Date"])
    basic_df["Date"] = pd.to_datetime(basic_df["Date"])

    # =========================
    # 🚀 merge_asof（核心）
    # =========================
    merged = pd.merge_asof(
        price_df.sort_values(["Symbol", "Date"]),
        basic_df.sort_values(["Symbol", "Date"]),
        on="Date",
        by="Symbol",               # 🚀 关键：按股票分组
        direction="backward"       # 🚀 防未来函数
    )

    return merged

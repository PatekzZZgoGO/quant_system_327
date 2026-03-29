import pandas as pd

def compute_future_returns(panel: pd.DataFrame, horizon: int = 5):
    """
    向量化 future return（无副作用）
    """

    df = panel.sort_values(["Symbol", "Date"]).copy()

    df["future_close"] = (
        df.groupby("Symbol")["Close"]
        .shift(-horizon)
    )

    ret_col = f"ret_{horizon}d"

    df[ret_col] = df["future_close"] / df["Close"] - 1

    return df
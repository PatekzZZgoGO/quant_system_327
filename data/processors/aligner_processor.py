import pandas as pd

def align_price_basic(price_df, basic_df):
    """
    防未来函数的 asof merge
    """

    return pd.merge_asof(
        price_df.sort_values("Date"),
        basic_df.sort_values("Date"),
        on="Date",
        direction="backward"
    )
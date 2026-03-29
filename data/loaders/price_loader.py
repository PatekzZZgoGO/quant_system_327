import pandas as pd
from pathlib import Path

class PriceLoader:
    """
    只负责读取 price 数据（无任何计算逻辑）
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def load(self, symbol: str, start: str, end: str) -> pd.DataFrame:

        path = self.data_dir / f"{symbol.replace('.', '_')}.parquet"

        if not path.exists():
            return pd.DataFrame()

        df = pd.read_parquet(path)

        if "Date" not in df.columns:
            df = df.reset_index()

        df["Date"] = pd.to_datetime(df["Date"])

        df = df.sort_values("Date")

        return df[
            (df["Date"] >= pd.to_datetime(start)) &
            (df["Date"] <= pd.to_datetime(end))
        ]
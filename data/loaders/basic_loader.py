import pandas as pd
from pathlib import Path

class BasicLoader:

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def load(self, symbol: str) -> pd.DataFrame:

        path = self.data_dir / f"{symbol.replace('.', '_')}_basic.parquet"

        if not path.exists():
            return pd.DataFrame()

        df = pd.read_parquet(path)

        if "Date" not in df.columns:
            df = df.reset_index()

        df["Date"] = pd.to_datetime(df["Date"])

        return df.sort_values("Date")
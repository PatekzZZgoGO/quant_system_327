# data/loaders/market_loader.py

import pandas as pd
from pathlib import Path
from infra.config import config


class MarketDataLoader:
    """
    市场数据加载器（无未来函数版本）

    🔥 特点：
    - 只读本地 parquet
    - merge_asof 防未来函数
    - 时间严格对齐
    """

    def __init__(self):
        self.data_dir = Path(config.get("data.path", "data/datasets/processed/stocks"))

    # =========================
    # 单只股票
    # =========================
    def load_one(self, symbol, start_date=None, end_date=None):
        price_path = self.data_dir / f"{symbol.replace('.', '_')}.parquet"
        basic_path = self.data_dir / f"{symbol.replace('.', '_')}_basic.parquet"

        if not price_path.exists():
            print(f"❌ 缺少 price 数据: {symbol}")
            return pd.DataFrame()

        price_df = pd.read_parquet(price_path)

        if not isinstance(price_df.index, pd.DatetimeIndex):
            price_df.index = pd.to_datetime(price_df.index)

        price_df = price_df.sort_index()

        # =========================
        # 时间过滤（先做）
        # =========================
        if start_date:
            price_df = price_df[price_df.index >= pd.to_datetime(start_date)]
        if end_date:
            price_df = price_df[price_df.index <= pd.to_datetime(end_date)]

        # =========================
        # basic（关键：防未来函数）
        # =========================
        if basic_path.exists():
            basic_df = pd.read_parquet(basic_path)

            if not isinstance(basic_df.index, pd.DatetimeIndex):
                basic_df.index = pd.to_datetime(basic_df.index)

            basic_df = basic_df.sort_index()

            # 👉 reset index 做 asof merge
            price_reset = price_df.reset_index().rename(columns={"index": "Date"})
            basic_reset = basic_df.reset_index().rename(columns={"index": "Date"})

            # 🔥 核心：只用过去数据
            df = pd.merge_asof(
                price_reset.sort_values("Date"),
                basic_reset.sort_values("Date"),
                on="Date",
                direction="backward"   # ← 关键！！只看过去
            )

            df.set_index("Date", inplace=True)

        else:
            df = price_df

        # =========================
        # 清洗
        # =========================
        df = df.sort_index()

        # 👉 不再盲目 ffill（已经由 asof 保证）
        df = df.dropna(subset=["Close"])

        return df

    # =========================
    # 多股票
    # =========================
    def load_multiple(self, symbols, start_date=None, end_date=None):
        data = []

        for symbol in symbols:
            df = self.load_one(symbol, start_date, end_date)

            if not df.empty:
                df["Symbol"] = symbol
                data.append(df)

        if not data:
            return pd.DataFrame()

        return pd.concat(data)
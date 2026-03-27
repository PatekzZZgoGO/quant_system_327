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
                df["Symbol"] = symbol.upper()  # ✅ 统一大写（关键）
                data.append(df)

        if not data:
            return pd.DataFrame()

        return pd.concat(data)

    # =========================================================
    # 🆕 以下是新增（IC 必需功能）
    # =========================================================

    # =========================
    # 📅 获取所有股票代码
    # =========================
    def get_all_symbols(self):
        symbols = []

        for file in self.data_dir.glob("*.parquet"):
            name = file.stem

            # 跳过 basic 文件
            if name.endswith("_basic"):
                continue

            symbol = name.replace("_", ".").upper()
            symbols.append(symbol)

        return list(set(symbols))

    # =========================
    # 📅 获取交易日
    # =========================
    def get_trade_dates(self, start: str, end: str):
        """
        从本地 parquet 推断交易日（无未来函数）
        """

        all_dates = set()

        for file in self.data_dir.glob("*.parquet"):
            try:
                df = pd.read_parquet(file)

                if isinstance(df.index, pd.DatetimeIndex):
                    all_dates.update(df.index)

            except Exception:
                continue

        dates = sorted(all_dates)

        # 转字符串过滤
        dates = [
            d for d in dates
            if start <= d.strftime("%Y%m%d") <= end
        ]

        return [d.strftime("%Y%m%d") for d in dates]

    # =========================
    # 📅 向后移动交易日
    # =========================
    def shift_trading_date(self, date: str, n: int):
        dates = self.get_trade_dates("20000101", "20990101")

        if date not in dates:
            return None

        idx = dates.index(date)

        if idx + n >= len(dates):
            return None

        return dates[idx + n]

    # =========================
    # 📈 获取未来收益（IC核心）
    # =========================
    def get_future_returns(self, date: str, horizon: int = 5):
        """
        返回：
        Symbol, ret_Nd
        """

        future_date = self.shift_trading_date(date, horizon)

        if future_date is None:
            return pd.DataFrame()

        symbols = self.get_all_symbols()

        df_t = self.load_multiple(symbols, end_date=date)
        df_t1 = self.load_multiple(symbols, end_date=future_date)

        snap_t = df_t[df_t.index == pd.to_datetime(date)][["Symbol", "Close"]]
        snap_t1 = df_t1[df_t1.index == pd.to_datetime(future_date)][["Symbol", "Close"]]

        merged = snap_t.merge(
            snap_t1,
            on="Symbol",
            suffixes=("_t", "_t1")
        )

        merged[f"ret_{horizon}d"] = (
            merged["Close_t1"] / merged["Close_t"] - 1
        )

        return merged[["Symbol", f"ret_{horizon}d"]]
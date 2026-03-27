import hashlib
import pickle
import pandas as pd
from pathlib import Path
from infra.config import config
import logging
from typing import List

logger = logging.getLogger(__name__)

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
        self._panel_cache = {}  # 新增：缓存面板数据

    def load_panel(self, start_date: str, end_date: str, symbols: List[str]) -> pd.DataFrame:
        """
        加载指定日期范围和股票列表的面板数据（所有原始字段）。
        返回 DataFrame，索引为日期，列包含 Symbol 和所有字段。
        结果会被缓存。
        """
        # 生成缓存键
        cache_key = (start_date, end_date, tuple(sorted(symbols)))
        
        # 检查缓存命中情况
        logger.debug(f"Checking cache for: {cache_key}")
        if cache_key in self._panel_cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self._panel_cache[cache_key]

        logger.info(f"Loading panel for {len(symbols)} symbols from {start_date} to {end_date}")

        # 收集每个股票的数据
        all_data = []
        for symbol in symbols:
            df = self.load_one(symbol, start_date=start_date, end_date=end_date)
            if not df.empty:
                df['Symbol'] = symbol.upper()
                all_data.append(df)

        if not all_data:
            return pd.DataFrame()

        # 合并所有股票数据
        panel = pd.concat(all_data)
        # 确保索引是 DatetimeIndex
        if not isinstance(panel.index, pd.DatetimeIndex):
            panel.index = pd.to_datetime(panel.index)

        # 按日期和符号排序
        panel = panel.sort_index()

        # 缓存
        self._panel_cache[cache_key] = panel
        logger.info(f"Panel loaded, shape: {panel.shape}")

        return panel

    # =========================
    # 单只股票
    # =========================
    def load_one(self, symbol, start_date=None, end_date=None):
        """
        加载单只股票的历史数据，并进行时间对齐。
        """
        price_path = self.data_dir / f"{symbol.replace('.', '_')}.parquet"
        basic_path = self.data_dir / f"{symbol.replace('.', '_')}_basic.parquet"

        if not price_path.exists():
            logger.warning(f"❌ 缺少 price 数据: {symbol}")
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
        """
        加载多个股票的数据并合并为一个面板数据。
        """
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
        """
        获取所有的股票符号。
        """
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
        获取指定日期范围内的交易日。
        """
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)
        all_dates = set()
        for file in self.data_dir.glob("*.parquet"):
            try:
                df = pd.read_parquet(file)
                if isinstance(df.index, pd.DatetimeIndex):
                    all_dates.update(df.index)
            except Exception:
                continue
        dates = sorted(all_dates)
        # 过滤
        dates = [d for d in dates if start_dt <= d <= end_dt]
        return [d.strftime("%Y%m%d") for d in dates]

    # =========================
    # 📅 向后移动交易日
    # =========================
    def shift_trading_date(self, date: str, n: int):
        """
        向后移动交易日。
        """
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
        获取指定日期的未来收益。
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
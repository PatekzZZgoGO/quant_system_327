import hashlib
import pickle
import pandas as pd
from pathlib import Path
from infra.config import config
import time
import logging
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

    # =========================
    # 加载面板数据
    # =========================
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

        # 使用多线程加速加载过程
        all_data = []
        with ThreadPoolExecutor() as executor:
            future_to_symbol = {executor.submit(self.load_one, symbol, start_date, end_date): symbol for symbol in symbols}
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    df = future.result()
                    if not df.empty:
                        df['Symbol'] = symbol.upper()
                        all_data.append(df)
                except Exception as e:
                    logger.warning(f"Failed to load data for symbol {symbol}: {e}")

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
    # 单只股票数据
    # =========================
    def load_one(self, symbol, start_date=None, end_date=None, load_columns=None):
        """
        加载单只股票的历史数据（仅加载指定列），并进行时间对齐。
        - load_columns 为 None 或空列表时，加载所有列；否则，只加载指定列。
        """
        price_path = self.data_dir / f"{symbol.replace('.', '_')}.parquet"
        basic_path = self.data_dir / f"{symbol.replace('.', '_')}_basic.parquet"

        if not price_path.exists():
            logger.warning(f"❌ 缺少 price 数据: {symbol}")
            return pd.DataFrame()

        # 如果 load_columns 为空或 None，加载所有列；否则，只加载指定列
        price_df = pd.read_parquet(price_path, columns=load_columns if load_columns else None)

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
    # 多股票数据
    # =========================
    def load_multiple(self, symbols, start_date=None, end_date=None, load_columns=None):
        """
        加载多个股票的数据并合并为一个面板数据（仅加载指定列），并行加载提高性能。
        - load_columns 为 None 或空列表时，加载所有列；否则，只加载指定列。
        """
        data = []

        # 使用线程池并行加载每个股票的数据
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self.load_one, symbol, start_date, end_date, load_columns): symbol
                for symbol in symbols
            }

            # 获取并处理每个未来的加载任务的结果
            for future in futures:
                symbol = futures[future]
                try:
                    df = future.result()
                    if not df.empty:
                        df["Symbol"] = symbol.upper()  # 统一大写
                        data.append(df)
                except Exception as e:
                    logger.warning(f"Failed to load data for {symbol}: {e}")

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
        start_time = time.time()
        logger.info(f"[get_trade_dates] Start retrieving trade dates for range {start} to {end}")

        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)

        all_dates = set()

        # Start reading data files
        logger.info(f"[get_trade_dates] Start reading Parquet files from {self.data_dir}")
        read_start_time = time.time()

        for file in self.data_dir.glob("*.parquet"):
            try:
                df = pd.read_parquet(file)
                if isinstance(df.index, pd.DatetimeIndex):
                    all_dates.update(df.index)
            except Exception as e:
                logger.warning(f"[get_trade_dates] Failed to read {file}: {e}")
                continue

        read_end_time = time.time()
        logger.info(f"[get_trade_dates] Finished reading Parquet files in {read_end_time - read_start_time:.4f} seconds")

        # Sorting and filtering dates
        dates = sorted(all_dates)
        logger.info(f"[get_trade_dates] Sorting dates took {time.time() - read_end_time:.4f} seconds")

        # Filter dates within range
        dates = [d for d in dates if start_dt <= d <= end_dt]
        logger.info(f"[get_trade_dates] Filtered dates in the range {start_dt} to {end_dt}")

        # Converting dates to desired format
        formatted_dates = [d.strftime("%Y%m%d") for d in dates]

        # End of the function
        end_time = time.time()
        logger.info(f"[get_trade_dates] Completed in {end_time - start_time:.4f} seconds")

        return formatted_dates

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
        获取指定日期的未来收益，只加载 Close 数据并计算未来收益。
        """
        start_time = time.time()  # 记录函数总的开始时间
        logger.info(f"开始获取未来收益 - {pd.to_datetime(date)} | Horizon: {horizon}天")

        # 步骤 1: 获取未来日期
        step_start = time.time()
        future_date = self.shift_trading_date(date, horizon)
        if future_date is None:
            logger.warning(f"未找到有效的未来日期，返回空的DataFrame。")
            return pd.DataFrame()
        step_end = time.time()
        logger.info(f"获取未来日期耗时：{step_end - step_start:.4f}秒")

        # 步骤 2: 获取所有股票代码
        step_start = time.time()
        symbols = self.get_all_symbols()
        logger.info(f"股票池加载完成，股票数量：{len(symbols)}")
        step_end = time.time()
        logger.info(f"获取股票池耗时：{step_end - step_start:.4f}秒")

        # 步骤 3: 加载历史数据（仅加载 Close 列）
        step_start = time.time()
        logger.info(f"开始加载历史数据：{pd.to_datetime(date)}")
        df_t = self.load_multiple(symbols, start_date=date, end_date=date, load_columns=["Close"])
        step_end = time.time()
        logger.info(f"历史数据加载完成，数据条数：{len(df_t)}，耗时：{step_end - step_start:.4f}秒")

        # 步骤 4: 加载未来数据（仅加载 Close 列）
        step_start = time.time()
        logger.info(f"开始加载未来数据：{pd.to_datetime(future_date)}")
        df_t1 = self.load_multiple(symbols, start_date=future_date, end_date=future_date, load_columns=["Close"])
        step_end = time.time()
        logger.info(f"未来数据加载完成，数据条数：{len(df_t1)}，耗时：{step_end - step_start:.4f}秒")

        # 步骤 5: 合并数据
        step_start = time.time()
        logger.info(f"开始合并数据：历史与未来数据按 Symbol 合并")
        merged = df_t.merge(
            df_t1,
            on="Symbol",
            suffixes=("_t", "_t1")
        )
        step_end = time.time()
        logger.info(f"数据合并耗时：{step_end - step_start:.4f}秒")

        # 步骤 6: 计算未来收益
        step_start = time.time()
        logger.info(f"开始计算未来收益：{horizon}天")
        merged[f"ret_{horizon}d"] = (
            merged["Close_t1"] / merged["Close_t"] - 1
        )
        step_end = time.time()
        logger.info(f"计算未来收益耗时：{step_end - step_start:.4f}秒")

        # 总结：返回结果并记录总耗时
        end_time = time.time()
        logger.info(f"返回结果，包含未来收益数据：{len(merged)}")
        logger.info(f"函数执行总耗时：{end_time - start_time:.4f}秒")
        
        return merged[["Symbol", f"ret_{horizon}d"]]
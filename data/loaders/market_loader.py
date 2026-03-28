import hashlib
import pickle
import pandas as pd
from pathlib import Path
from infra.config import config
import time
import logging
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from data.ingestion.tushare_client import TushareDataFetcher


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
    
    def load_single_symbol(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        加载单只股票 + 合并 basic 数据（机构级标准版）
        """

        base_dir = Path("data/datasets/processed/stocks").resolve()

        market_file = base_dir / f"{symbol.replace('.', '_')}.parquet"
        basic_file = base_dir / f"{symbol.replace('.', '_')}_basic.parquet"

        if not market_file.exists():
            return pd.DataFrame()

        # =========================
        # 1️⃣ 读取 market 数据
        # =========================
        df_market = pd.read_parquet(market_file)

        if "Date" not in df_market.columns:
            df_market = df_market.reset_index()

        df_market["Date"] = pd.to_datetime(df_market["Date"])

        # ⚠️🔥【关键修复】必须升序（否则 shift 全错）
        df_market = df_market.sort_values("Date")

        # 时间过滤
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        df_market = df_market[
            (df_market["Date"] >= start_date) &
            (df_market["Date"] <= end_date)
        ]

        if df_market.empty:
            return pd.DataFrame()

        # Symbol 标准化
        if "Symbol" not in df_market.columns:
            df_market["Symbol"] = symbol

        # =========================
        # 2️⃣ 读取 basic 数据
        # =========================
        if basic_file.exists():
            df_basic = pd.read_parquet(basic_file)

            if "Date" not in df_basic.columns:
                df_basic = df_basic.reset_index()

            df_basic["Date"] = pd.to_datetime(df_basic["Date"])

            # 同样必须升序
            df_basic = df_basic.sort_values("Date")

            if "Symbol" not in df_basic.columns:
                df_basic["Symbol"] = symbol

            # merge（不会产生 Symbol_x）
            df = pd.merge(
                df_market,
                df_basic,
                on=["Date", "Symbol"],
                how="left",
                suffixes=("", "_basic")
            )
        else:
            df = df_market

        return df
    

    def load_panel(self, start_date: str, end_date: str, symbols: list, max_workers: int = 8):
        """
        标准 Panel：

        Date | Symbol | Open | High | Low | Close | Volume | ...

        每一行 = (Date, Symbol)
        """

        logger.info(f"Loading panel for {len(symbols)} symbols from {start_date} to {end_date}")

        results = []

        def load_one(symbol: str):
            try:
                df = self.load_single_symbol(symbol, start_date, end_date)

                if df is None or df.empty:
                    return None

                df = df.copy()

                # 确保 Date 存在
                if "Date" not in df.columns:
                    df = df.reset_index()

                # Symbol 标准化
                if "ts_code" in df.columns and "Symbol" not in df.columns:
                    df["Symbol"] = df["ts_code"]

                if "Symbol" not in df.columns:
                    df["Symbol"] = symbol

                # 清理多余 Symbol 列
                symbol_cols = [c for c in df.columns if "Symbol" in c and c != "Symbol"]
                df = df.drop(columns=symbol_cols, errors="ignore")

                return df

            except Exception as e:
                logger.warning(f"Failed to load {symbol}: {e}")
                return None

        # =========================
        # 🚀 并行加载
        # =========================
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(load_one, sym): sym for sym in symbols}

            for future in as_completed(futures):
                df = future.result()
                if df is not None and not df.empty:
                    results.append(df)

        if not results:
            logger.warning("Panel load failed: no data")
            return pd.DataFrame()

        # =========================
        # 合并
        # =========================
        panel = pd.concat(results, ignore_index=True)

        # =========================
        # 类型标准化
        # =========================
        panel["Date"] = pd.to_datetime(panel["Date"])

        # ⚠️🔥【关键】全局排序（影响 future return）
        panel = panel.sort_values(["Symbol", "Date"]).reset_index(drop=True)

        # =========================
        # 去重
        # =========================
        panel = panel.drop_duplicates(subset=["Date", "Symbol"])

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

    def shift_trading_date(self, date: str, n: int):
        """
        向后移动 n 个交易日（基于本地数据）
        """
        import pandas as pd

        # 获取全量交易日（建议缓存，但先不优化）
        dates = self.get_trade_dates(start="2000-01-01", end=None)

        if not dates:
            return None

        # 转 datetime
        dates = pd.to_datetime(dates)

        target_date = pd.to_datetime(date)

        # 找到位置
        try:
            idx = list(dates).index(target_date)
        except ValueError:
            return None

        # 越界判断
        if idx + n >= len(dates):
            return None

        return dates[idx + n].strftime("%Y-%m-%d")

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
    # 📈 获取未来收益（IC核心）
    # =========================

    def get_future_returns(
        self,
        panel: pd.DataFrame,
        horizon: int = 5
    ) -> pd.DataFrame:
        """
        基于已加载的 panel 计算未来收益（高性能向量化版本）

        输入 panel 必须包含：
            Date | Symbol | Close

        返回：
            Date | Symbol | ret_{horizon}d
        """

        import time
        start_time = time.time()

        logger.info(f"开始计算未来收益 | horizon={horizon}")

        if panel is None or panel.empty:
            logger.warning("输入 panel 为空")
            return pd.DataFrame()

        required_cols = {"Date", "Symbol", "Close"}
        if not required_cols.issubset(panel.columns):
            raise ValueError(f"panel 缺少必要列: {required_cols - set(panel.columns)}")

        # =========================
        # 0️⃣ 标准化
        # =========================
        df = panel.copy()

        df["Date"] = pd.to_datetime(df["Date"])

        # 排序（非常关键）
        df = df.sort_values(["Symbol", "Date"])

        # 去重（防止重复数据影响 shift）
        df = df.drop_duplicates(subset=["Date", "Symbol"])

        # =========================
        # 1️⃣ groupby + shift（核心优化）
        # =========================
        df["future_close"] = (
            df.groupby("Symbol")["Close"]
            .shift(-horizon)
        )

        # =========================
        # 2️⃣ 计算收益
        # =========================
        ret_col = f"ret_{horizon}d"

        df[ret_col] = df["future_close"] / df["Close"] - 1

        # =========================
        # 3️⃣ 清理数据
        # =========================
        df = df.dropna(subset=[ret_col])

        # =========================
        # 4️⃣ 只保留必要列
        # =========================
        result = df[["Date", "Symbol", ret_col]].copy()

        # 再排序一次（保证 merge 稳定）
        result = result.sort_values(["Date", "Symbol"]).reset_index(drop=True)

        end_time = time.time()
        logger.info(
            f"未来收益计算完成 | 耗时: {end_time - start_time:.4f}s | shape={result.shape}"
        )

        return result
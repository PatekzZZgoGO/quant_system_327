# 因子统一加载器
import pandas as pd
import logging
from typing import List
from pathlib import Path

logger = logging.getLogger(__name__)


class DataLoader:
    """
    批量数据加载器（连接 tushare_client 与 engine）

    功能：
    - 批量加载 parquet
    - 自动合并 price + basic
    - 标准化字段
    - 输出统一结构
    """

    def __init__(self, data_dir: str):
        """
        data_dir:
            data/datasets/processed/stocks
        """
        self.data_dir = Path(data_dir)

    # =========================
    # 单股票加载
    # =========================
    def load_single(self, symbol: str) -> pd.DataFrame:
        """
        加载单个股票（price + basic）
        """

        try:
            safe_symbol = symbol.replace('.', '_')

            price_path = self.data_dir / f"{safe_symbol}.parquet"
            basic_path = self.data_dir / f"{safe_symbol}_basic.parquet"

            if not price_path.exists():
                return pd.DataFrame()

            # --- price
            price_df = pd.read_parquet(price_path)

            # --- basic（可能不存在）
            if basic_path.exists():
                basic_df = pd.read_parquet(basic_path)

                # join
                df = price_df.join(basic_df, how='left')

                # ⚠️ 注意：不能 forward fill（会引入未来函数）
                # 👉 这里只做轻量处理
                # df['TotalMV'] = df['TotalMV'].ffill() ❌ 不要

            else:
                df = price_df

            # --- 加 Symbol（统一字段）
            df['Symbol'] = symbol

            return df

        except Exception as e:
            logger.warning(f"[Loader] failed: {symbol} | {e}")
            return pd.DataFrame()

    # =========================
    # 批量加载（核心）
    # =========================
    def load_multiple(self, symbols: List[str]) -> pd.DataFrame:
        """
        批量加载（给 engine 用）
        """

        all_df = []

        for s in symbols:
            df = self.load_single(s)

            if df is not None and not df.empty:
                all_df.append(df)

        if not all_df:
            return pd.DataFrame()

        df = pd.concat(all_df)

        # =========================
        # 标准化字段（关键）
        # =========================
        df = self._normalize_columns(df)

        return df

    # =========================
    # 字段统一（核心）
    # =========================
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        统一字段命名（适配 engine）
        """

        rename_map = {
            'close': 'Close',
            'total_mv': 'TotalMV',
            'turnover_rate': 'TurnoverRate'
        }

        df = df.rename(columns=rename_map)

        # 保证 index 是 datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        return df.sort_index()
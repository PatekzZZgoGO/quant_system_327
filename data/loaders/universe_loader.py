import logging
from pathlib import Path
import pandas as pd
from typing import List, Optional
from exceptions.data import DataUnavailableError, SchemaValidationError

logger = logging.getLogger(__name__)

class UniverseLoader:
    """
    UniverseLoader 加载股票池的管理类，提供股票代码解析、加载和缓存功能。
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化 UniverseLoader。

        参数:
            data_dir: 股票数据的文件夹路径。如果为 None，将使用默认路径 'data/datasets/processed/stocks'。
        """
        self.data_dir = Path(data_dir) if data_dir else Path("data/datasets/processed/stocks")
        self._cached_symbols = None  # 缓存股票符号列表
        logger.debug(f"UniverseLoader initialized with data_dir: {self.data_dir}")

    def _get_all_symbols_from_files(self) -> List[str]:
        """
        从 parquet 文件中解析所有股票符号，并进行去重和规范化处理。
        """
        symbols = set()

        # 遍历文件目录，获取所有股票符号
        for file in self.data_dir.glob("*.parquet"):
            # 排除 _basic 文件，因为这些不是实际的股票数据文件
            if file.stem.endswith("_basic"):
                continue

            symbol = file.stem.replace("_", ".").upper()

            # 只考虑包含一个 '.' 的文件名（确保是股票代码）
            if symbol.count('.') == 1:
                symbols.add(symbol)

        logger.debug(f"Found {len(symbols)} unique symbols from parquet files")
        return sorted(symbols)

    def get_universe(self, limit: Optional[int] = None) -> List[str]:
        """
        获取股票池列表。返回最多 `limit` 个股票代码，或者如果未设置 `limit`，则返回所有股票。

        参数:
            limit: 可选，限制返回的股票数量。

        返回:
            股票代码列表。
        """
        # 如果缓存已经存在，直接返回
        if self._cached_symbols is not None:
            logger.debug("Using cached symbols list.")
            symbols = self._cached_symbols
        else:
            if not self.data_dir.exists():
                raise DataUnavailableError(
                    f"❌ 数据目录不存在: {self.data_dir}\n"
                    "请先运行:\n"
                    "python run.py data update stocks"
                )

            parquet_files = list(self.data_dir.glob("*.parquet"))
            if not parquet_files:
                raise DataUnavailableError(
                    f"❌ 数据目录中无 parquet 文件: {self.data_dir}\n"
                    "请先运行:\n"
                    "python run.py data update stocks"
                )

            # 从文件中解析符号并缓存
            symbols = self._get_all_symbols_from_files()
            if not symbols:
                raise SchemaValidationError("❌ 未能从 parquet 文件中解析出股票代码")

            # 缓存符号
            self._cached_symbols = symbols

        # 根据 limit 限制股票数量
        if limit is not None and limit > 0:
            symbols = symbols[:limit]
            logger.info(f"Universe limited to {limit} stocks: {symbols[:5]}... (showing first 5)")
        else:
            logger.info(f"Full universe: {len(symbols)} stocks (showing first 5): {symbols[:5]}...")

        return symbols

import pandas as pd
import numpy as np
import logging
from typing import List
import time

from features.pipelines.factor_pipeline import FactorPipeline

logger = logging.getLogger(__name__)


class FactorEngine:
    """
    🎯 纯因子引擎（解耦版）

    只负责：
    ✔ 因子计算（pipeline）
    ✔ snapshot 提取
    ✔ 不涉及 score / 权重 / 选股

    用途：
    - IC 分析
    - 因子研究
    """

    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.pipeline = FactorPipeline()

    # =========================
    # 🧪 数据校验（保留原逻辑）
    # =========================
    def validate_data(self, df: pd.DataFrame):
        required_cols = ['Symbol', 'Close']

        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"[FactorEngine] Missing column: {col}")

        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("[FactorEngine] index must be DatetimeIndex")

    # =========================
    # 🧠 因子计算（核心拆分）
    # =========================
    def compute_factors(
        self,
        df: pd.DataFrame,
        factors: List[str]
    ) -> pd.DataFrame:
        start_time = time.time()
        logger.info(f"[FactorEngine] Computing factors: {factors}")

        df = df.copy()

        self.validate_data(df)

        if not factors:
            logger.warning("[FactorEngine] no factors to compute")
            return df

        # ⚠️ 必须排序（非常关键）
        df = df.sort_values(["Symbol", "Date"])

        df = self.pipeline.run(df, factors=factors)

        logger.info(f"[FactorEngine] Factor computation done in {time.time() - start_time:.4f}s")

        return df

    # =========================
    # 📊 横截面提取（保留原逻辑）
    # =========================
    def get_snapshot(self, df: pd.DataFrame, date: pd.Timestamp) -> pd.DataFrame:
        logger.info(f"[FactorEngine] Extracting snapshot for {date}")
        snapshot = df[df.index == date].copy()
        return snapshot

    # =========================
    # 🧠 缺失处理（原封不动搬过来）
    # =========================
    def handle_missing(self, df: pd.DataFrame, factors: List[str]) -> pd.DataFrame:
        start_time = time.time()
        logger.info(f"[FactorEngine] Start missing data handling")

        df = df.copy()

        for col in factors:
            if col not in df.columns:
                continue

            if df[col].isna().all():
                df = df.drop(columns=[col])
                continue

            median = df[col].median()
            df[col] = df[col].fillna(median)

        logger.info(f"[FactorEngine] Missing handling done in {time.time() - start_time:.4f}s")

        return df

    # =========================
    # 🎯 IC / research 专用接口
    # =========================
    def run_factor_pipeline(
        self,
        df: pd.DataFrame,
        date: pd.Timestamp,
        factors: List[str]
    ) -> pd.DataFrame:
        """
        👉 给 IC 用的“干净接口”

        流程：
        1. 防未来函数
        2. 因子计算
        3. snapshot
        4. 缺失处理
        """

        logger.info("=" * 50)
        logger.info(f"[FactorEngine] RUN date={date}")

        df = df.copy()

        self.validate_data(df)

        # =========================
        # 防未来函数（保留原逻辑）
        # =========================
        df = df[df.index <= date]

        if df.empty:
            logger.warning("[FactorEngine] no history")
            return pd.DataFrame()

        # =========================
        # 因子计算
        # =========================
        df = self.compute_factors(df, factors)

        # =========================
        # snapshot
        # =========================
        snapshot = self.get_snapshot(df, date)

        if snapshot.empty:
            logger.warning(f"[FactorEngine] no snapshot for {date}")
            return pd.DataFrame()

        # =========================
        # 缺失处理
        # =========================
        snapshot = self.handle_missing(snapshot, factors)

        logger.info(f"[FactorEngine] snapshot size={len(snapshot)}")

        return snapshot
import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Tuple

from features.pipelines.factor_pipeline import FactorPipeline
from features.pipelines.normalization import zscore

logger = logging.getLogger(__name__)


class CrossSectionalEngine:
    """
    👻 横截面多因子引擎（机构级版本）

    核心理念：
    ----------
    1. 时间序列计算 → 因子产生 alpha
    2. 横截面排序 → 决定资金分配
    3. 严禁未来函数（no leakage）
    4. 因子必须解耦（pipeline 化）

    数据要求：
    ----------
    index: DatetimeIndex
    columns:
        Symbol, Close, TotalMV, TurnoverRate
    """

    def __init__(self, data_loader):
        """
        data_loader:
            必须实现:
                load_multiple(symbols) -> DataFrame
        """
        self.data_loader = data_loader
        self.pipeline = FactorPipeline()

    # =========================
    # 🧰 工具函数
    # =========================
    @staticmethod
    def safe_log(series: pd.Series) -> pd.Series:
        return np.log(series.replace(0, np.nan))

    # =========================
    # 🧠 横截面缺失处理（升级版）
    # =========================
    def handle_missing(self, df: pd.DataFrame, factors: List[str]) -> pd.DataFrame:
        """
        👻 不使用简单 median，而是：
        1. 优先删除极端缺失
        2. 再做截面内填充
        3. 保证不引入未来信息
        """

        df = df.copy()

        for col in factors:

            if col not in df.columns:
                continue

            # 👻 Step 1: 删除全空列（避免污染）
            if df[col].isna().all():
                df = df.drop(columns=[col])
                continue

            # 👻 Step 2: 横截面填充（仅当前日期）
            median = df[col].median()

            # ⚠️ 注意：这是“当日截面 median”，不是时间序列
            df[col] = df[col].fillna(median)

        return df

    # =========================
    # 📊 横截面提取
    # =========================
    def get_snapshot(self, df: pd.DataFrame, date: pd.Timestamp) -> pd.DataFrame:
        """
        👻 核心原则：
        横截面 = 同一天所有股票

        ⚠️ 严禁：
        - 使用未来数据
        - 使用时间序列 fillna
        """

        snapshot = df[df.index == date].copy()

        return snapshot

    # =========================
    # 📈 因子标准化 + 打分
    # =========================
    def score(self, df: pd.DataFrame, weights: Dict[str, float]) -> pd.DataFrame:
        df = df.copy()

        # =========================
        # 1️⃣ zscore
        # =========================
        for f in weights.keys():

            if f not in df.columns:
                df[f + "_z"] = 0
                continue

            df[f + "_z"] = zscore(df[f])

        # =========================
        # 2️⃣ score + 因子贡献
        # =========================
        df['score'] = 0.0

        for f, w in weights.items():
            contrib_col = f"{f}_contrib"

            df[contrib_col] = df[f + "_z"] * w
            df['score'] += df[contrib_col]

        return df

    # =========================
    # 🧪 数据校验
    # =========================
    def validate_data(self, df: pd.DataFrame):
        required_cols = ['Symbol', 'Close']

        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"[Engine] Missing column: {col}")

        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("[Engine] index must be DatetimeIndex")

    # =========================
    # 🎯 主流程
    # =========================
    def run(
        self,
        date: str,
        universe: List[str],
        weights: Dict[str, float] = None,
        model=None,
        top_n: int = 50
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:

        logger.info("=" * 60)
        logger.info(f"[Engine] RUN date={date}")
        logger.info(f"[Engine] universe size={len(universe)}")

        # =========================
        # 🧠 从 model 获取 weights（新增）
        # =========================
        if weights is None:
            if model is None:
                raise ValueError("[Engine] weights or model must be provided")

            if hasattr(model, "get_weights"):
                weights = model.get_weights(date)
            elif hasattr(model, "WEIGHTS"):
                weights = model.WEIGHTS
            else:
                raise ValueError("[Engine] model has no weights")

        logger.info(f"[Engine] weights = {weights}")

        # =========================
        # 1️⃣ 数据加载
        # =========================
        df = self.data_loader.load_multiple(universe)

        if df is None or df.empty:
            logger.warning("[Engine] empty data")
            return pd.DataFrame(), pd.DataFrame()

        self.validate_data(df)

        # =========================
        # 2️⃣ 防未来函数
        # =========================
        date = pd.to_datetime(date)

        # 👻 关键：只保留历史数据
        df = df[df.index <= date]

        if df.empty:
            logger.warning("[Engine] no history")
            return pd.DataFrame(), pd.DataFrame()

        # =========================
        # 3️⃣ 因子计算（pipeline）
        # =========================
        df = self.pipeline.run(df, factors=list(weights.keys()))
        # =========================
        # 4️⃣ 横截面提取
        # =========================
        snapshot = self.get_snapshot(df, date)

        if snapshot.empty:
            logger.warning(f"[Engine] no snapshot for {date}")
            return pd.DataFrame(), pd.DataFrame()

        # =========================
        # 5️⃣ 缺失处理（关键升级点）
        # =========================
        snapshot = self.handle_missing(snapshot, list(weights.keys()))

        # =========================
        # 6️⃣ 打分
        # =========================
        snapshot = self.score(snapshot, weights)

        # =========================
        # 7️⃣ 排序 + 选股
        # =========================
        snapshot = snapshot.sort_values('score', ascending=False)

        if top_n is None:
            selected = snapshot
        else:
            selected = snapshot.head(top_n)

        # =========================
        # 8️⃣ 日志
        # =========================
        logger.info(f"[Engine] valid stocks={len(snapshot)}")
        logger.info(f"[Engine] selected={len(selected)}")

        if not snapshot.empty:
            logger.info(
                f"[Engine] score range=({snapshot['score'].min():.4f}, {snapshot['score'].max():.4f})"
            )

        logger.info("=" * 60)

        return selected, snapshot
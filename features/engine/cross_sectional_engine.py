import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Tuple
import time

from features.pipelines.factor_pipeline import FactorPipeline
from features.pipelines.normalization import zscore

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',  # 包含时间戳
)

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
        start_time = time.time()
        logger.info(f"[Engine] Start missing data handling at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
        
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

        elapsed_time = time.time() - start_time
        logger.info(f"[Engine] Missing data handling completed in {elapsed_time:.2f} seconds.")
        return df

    # =========================
    # 📊 横截面提取
    # =========================
    def get_snapshot(self, df: pd.DataFrame, date: pd.Timestamp) -> pd.DataFrame:
        logger.info(f"[Engine] Extracting snapshot for {date} at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
        snapshot = df[df.index == date].copy()
        return snapshot

    # =========================
    # 📈 因子标准化 + 打分
    # =========================
    def score(self, df: pd.DataFrame, weights: Dict[str, float]) -> pd.DataFrame:
        logger.info(f"[Engine] Scoring with weights {weights} at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
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

        logger.info(f"[Engine] Scoring completed at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
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
        factors: List[str] = None,
        top_n: int = 50,
        df: pd.DataFrame = None  # 新增：外部预加载的数据
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        logger.info("=" * 60)
        logger.info(f"[Engine] RUN date={date}")
        logger.info(f"[Engine] universe size={len(universe)}")
        logger.info(f"[DEBUG] run called: weights={weights}, model={model}, factors={factors}, df_shape={df.shape if df is not None else None}")

        # =========================
        # 1️⃣ 数据加载（如果有预加载数据则跳过）
        # =========================
        if df is None:
            logger.info(f"[Engine] Loading data for {len(universe)} stocks at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
            df = self.data_loader.load_multiple(universe)
        else:
            df = df.copy()

        if df is None or df.empty:
            logger.warning("[Engine] empty data")
            return pd.DataFrame(), pd.DataFrame()

        self.validate_data(df)

        # =========================
        # 2️⃣ 防未来函数
        # =========================
        date = pd.to_datetime(date)
        df = df[df.index <= date]

        if df.empty:
            logger.warning("[Engine] no history")
            return pd.DataFrame(), pd.DataFrame()

        # =========================
        # 3️⃣ 因子计算（pipeline）
        # =========================
        if factors is not None:
            factor_list = factors
        else:
            if weights is None:
                factor_list = []
            else:
                factor_list = list(weights.keys())

        if not factor_list:
            logger.warning("[Engine] no factors to compute")
            return pd.DataFrame(), pd.DataFrame()

        # 计算因子
        logger.info(f"[Engine] Computing factors at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
        df = self.pipeline.run(df, factors=factor_list)

        # =========================
        # 4️⃣ 横截面提取
        # =========================
        snapshot = self.get_snapshot(df, date)

        if snapshot.empty:
            logger.warning(f"[Engine] no snapshot for {date}")
            return pd.DataFrame(), pd.DataFrame()

        # =========================
        # 5️⃣ 缺失处理
        # =========================
        snapshot = self.handle_missing(snapshot, factor_list)

        # =========================
        # 6️⃣ 确定权重（用于打分）
        # =========================
        if weights is None:
            if model is not None:
                if hasattr(model, "get_weights"):
                    weights = model.get_weights(date)
                elif hasattr(model, "WEIGHTS"):
                    weights = model.WEIGHTS
                else:
                    raise ValueError("[Engine] model has no weights")
            elif factors is not None:
                weights = {f: 0.0 for f in factors}
            else:
                raise ValueError("[Engine] need weights or model or factors")

        if not weights:
            logger.warning("[Engine] weights is empty")
            return pd.DataFrame(), pd.DataFrame()

        # =========================
        # 7️⃣ 打分
        # =========================
        snapshot = self.score(snapshot, weights)

        # =========================
        # 8️⃣ 排序 + 选股
        # =========================
        snapshot = snapshot.sort_values('score', ascending=False)

        if top_n is None:
            selected = snapshot
        else:
            selected = snapshot.head(top_n)

        # =========================
        # 9️⃣ 日志
        # =========================
        logger.info(f"[Engine] valid stocks={len(snapshot)}")
        logger.info(f"[Engine] selected={len(selected)}")
        if not snapshot.empty:
            logger.info(
                f"[Engine] score range=({snapshot['score'].min():.4f}, {snapshot['score'].max():.4f})"
            )
        logger.info("=" * 60)

        return selected, snapshot
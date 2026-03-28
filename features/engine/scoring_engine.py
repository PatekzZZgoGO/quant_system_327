import pandas as pd
import logging
from typing import Dict
import time

from features.pipelines.normalization import zscore

logger = logging.getLogger(__name__)


class ScoringEngine:
    """
    🎯 打分引擎（从原 engine 拆出）

    只负责：
    ✔ zscore
    ✔ 权重加权
    ✔ 排序
    """

    # =========================
    # 📈 打分（原封不动）
    # =========================
    def score(self, df: pd.DataFrame, weights: Dict[str, float]) -> pd.DataFrame:
        logger.info(f"[ScoringEngine] Scoring with weights {weights}")
        df = df.copy()

        # 1️⃣ zscore
        for f in weights.keys():
            if f not in df.columns:
                df[f + "_z"] = 0
                continue

            df[f + "_z"] = zscore(df[f])

        # 2️⃣ score
        df['score'] = 0.0

        for f, w in weights.items():
            contrib_col = f"{f}_contrib"

            df[contrib_col] = df[f + "_z"] * w
            df['score'] += df[contrib_col]

        return df

    # =========================
    # 🎯 排序 + 选股
    # =========================
    def select(self, df: pd.DataFrame, top_n: int = 50) -> pd.DataFrame:
        start_time = time.time()

        df = df.sort_values('score', ascending=False)

        if top_n is None:
            selected = df
        else:
            selected = df.head(top_n)

        logger.info(f"[ScoringEngine] Selected {len(selected)} stocks")

        return selected
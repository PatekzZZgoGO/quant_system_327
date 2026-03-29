from typing import Dict

import pandas as pd

from features.engine.scoring_engine import ScoringEngine


class SignalGenerator:
    """信号生成器。

    职责非常单一：
    1. 接收某个交易日的横截面 snapshot；
    2. 用 ScoringEngine 把因子值转成可排序的 score；
    3. 选出目标股票，并转换成目标权重。
    """

    def __init__(self, scoring_engine: ScoringEngine):
        self.scoring_engine = scoring_engine

    def _to_equal_weight_positions(self, selected: pd.DataFrame) -> Dict[str, float]:
        """把选股结果转成等权目标仓位。"""
        if selected is None or selected.empty:
            return {}

        symbols = selected["Symbol"].tolist()
        weight = 1.0 / len(symbols)
        return {symbol: weight for symbol in symbols}

    def generate(self, snapshot: pd.DataFrame, weights: Dict[str, float], top_n: int):
        """生成单日调仓信号。"""
        if snapshot is None or snapshot.empty:
            return {
                "scored": pd.DataFrame(),
                "selected": pd.DataFrame(),
                "target_positions": {},
            }

        scored = self.scoring_engine.score(snapshot, weights)
        selected = self.scoring_engine.select(scored, top_n=top_n)

        return {
            "scored": scored,
            "selected": selected,
            "target_positions": self._to_equal_weight_positions(selected),
        }

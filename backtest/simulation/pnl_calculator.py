from typing import Dict

import pandas as pd


class PnLCalculator:
    """收益计算器。"""

    def __init__(self, price_col: str = "Close"):
        self.price_col = price_col

    def compute_period_return(self, panel_by_date: Dict[pd.Timestamp, pd.DataFrame], positions, start_date, end_date):
        """计算一个持仓周期的组合收益。"""
        if not positions:
            return {
                "gross_return": 0.0,
                "net_return": 0.0,
                "covered_weight": 0.0,
                "missing_symbols": 0,
            }

        df_start = panel_by_date.get(start_date)
        df_end = panel_by_date.get(end_date)
        if df_start is None or df_end is None or df_start.empty or df_end.empty:
            return {
                "gross_return": 0.0,
                "net_return": 0.0,
                "covered_weight": 0.0,
                "missing_symbols": len(positions),
            }

        start_index = df_start.set_index("Symbol")
        end_index = df_end.set_index("Symbol")

        gross_return = 0.0
        covered_weight = 0.0
        missing_symbols = 0

        for symbol, weight in positions.items():
            if symbol not in start_index.index or symbol not in end_index.index:
                missing_symbols += 1
                continue

            start_price = start_index.at[symbol, self.price_col]
            end_price = end_index.at[symbol, self.price_col]
            if pd.isna(start_price) or pd.isna(end_price) or start_price == 0:
                missing_symbols += 1
                continue

            symbol_return = (end_price / start_price) - 1
            gross_return += weight * symbol_return
            covered_weight += weight

        return {
            "gross_return": float(gross_return),
            "net_return": float(gross_return),
            "covered_weight": float(covered_weight),
            "missing_symbols": int(missing_symbols),
        }

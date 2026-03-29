import numpy as np
import pandas as pd


class ResultAnalyzer:
    """回测结果分析器。"""

    def analyze(self, daily_pnl: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
        """生成绩效汇总表。"""
        if daily_pnl is None or daily_pnl.empty:
            return pd.DataFrame(
                [
                    {
                        "total_return": 0.0,
                        "annual_return": 0.0,
                        "annual_volatility": 0.0,
                        "sharpe": 0.0,
                        "max_drawdown": 0.0,
                        "win_rate": 0.0,
                        "avg_turnover": 0.0,
                        "total_cost": 0.0,
                        "trading_days": 0,
                    }
                ]
            )

        net_returns = daily_pnl["net_return"].fillna(0.0)
        equity_curve = (1.0 + net_returns).cumprod()
        running_peak = equity_curve.cummax()
        drawdown = (equity_curve / running_peak) - 1.0

        total_return = equity_curve.iloc[-1] - 1.0
        trading_days = len(net_returns)
        annual_return = (equity_curve.iloc[-1] ** (252 / trading_days)) - 1.0 if trading_days > 0 else 0.0
        annual_volatility = net_returns.std(ddof=0) * np.sqrt(252) if trading_days > 1 else 0.0
        sharpe = annual_return / annual_volatility if annual_volatility > 0 else 0.0

        return pd.DataFrame(
            [
                {
                    "total_return": float(total_return),
                    "annual_return": float(annual_return),
                    "annual_volatility": float(annual_volatility),
                    "sharpe": float(sharpe),
                    "max_drawdown": float(drawdown.min()),
                    "win_rate": float((net_returns > 0).mean()),
                    "avg_turnover": float(daily_pnl["turnover"].fillna(0.0).mean()),
                    "total_cost": float(daily_pnl["trading_cost"].fillna(0.0).sum()),
                    "trading_days": int(trading_days),
                }
            ]
        )

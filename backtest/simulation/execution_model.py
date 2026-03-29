from dataclasses import dataclass
from typing import Dict


@dataclass
class ExecutionResult:
    """一次调仓执行的结果快照。"""

    signal_date: object
    execution_date: object
    previous_positions: Dict[str, float]
    target_positions: Dict[str, float]
    new_positions: Dict[str, float]
    turnover: float
    commission_cost: float
    slippage_cost: float
    total_cost: float


class ExecutionModel:
    """撮合与交易成本模型。"""

    def __init__(self, commission_rate: float = 0.001, slippage_rate: float = 0.0):
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate

    def estimate_turnover(self, current_positions: Dict[str, float], target_positions: Dict[str, float]) -> float:
        """估算调仓换手。"""
        symbols = set(current_positions) | set(target_positions)
        return sum(abs(target_positions.get(symbol, 0.0) - current_positions.get(symbol, 0.0)) for symbol in symbols)

    def execute(
        self,
        current_positions: Dict[str, float],
        target_positions: Dict[str, float],
        signal_date,
        execution_date,
    ) -> ExecutionResult:
        """执行一次调仓。"""
        turnover = self.estimate_turnover(current_positions, target_positions)
        commission_cost = turnover * self.commission_rate
        slippage_cost = turnover * self.slippage_rate
        total_cost = commission_cost + slippage_cost

        return ExecutionResult(
            signal_date=signal_date,
            execution_date=execution_date,
            previous_positions=dict(current_positions),
            target_positions=dict(target_positions),
            new_positions=dict(target_positions),
            turnover=turnover,
            commission_cost=commission_cost,
            slippage_cost=slippage_cost,
            total_cost=total_cost,
        )

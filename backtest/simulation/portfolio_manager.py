from dataclasses import dataclass
from typing import Dict, List, Optional

from backtest.simulation.execution_model import ExecutionModel


@dataclass
class RebalanceInstruction:
    """待执行调仓指令。"""

    signal_date: object
    execution_date: object
    target_positions: Dict[str, float]


class PortfolioManager:
    """持仓状态机。"""

    def __init__(self):
        self.positions: Dict[str, float] = {}
        self.pending_rebalances: List[RebalanceInstruction] = []

    def schedule_rebalance(self, signal_date, execution_date, target_positions: Dict[str, float]) -> None:
        """登记一笔未来执行的调仓指令。"""
        self.pending_rebalances.append(
            RebalanceInstruction(
                signal_date=signal_date,
                execution_date=execution_date,
                target_positions=dict(target_positions),
            )
        )

    def execute_due_rebalance(self, current_date, execution_model: ExecutionModel):
        """执行当前日期到期的调仓。"""
        due_instruction: Optional[RebalanceInstruction] = None

        for instruction in self.pending_rebalances:
            if instruction.execution_date == current_date:
                due_instruction = instruction
                break

        if due_instruction is None:
            return None

        execution_result = execution_model.execute(
            current_positions=self.positions,
            target_positions=due_instruction.target_positions,
            signal_date=due_instruction.signal_date,
            execution_date=current_date,
        )

        self.positions = dict(execution_result.new_positions)
        self.pending_rebalances.remove(due_instruction)
        return execution_result

    def get_position_snapshot(self, date):
        """输出当前时点的仓位快照。"""
        return [
            {
                "date": date,
                "symbol": symbol,
                "weight": weight,
            }
            for symbol, weight in sorted(self.positions.items())
        ]

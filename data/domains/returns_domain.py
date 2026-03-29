from data.processors.returns_processor import compute_future_returns
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class Returns:
    """
    📈 收益 Domain（语义层）

    职责：
    - 封装 future return 计算
    - 保证“数据增强（enrich）而不是破坏”

    设计原则：
    - ✔ 输入 panel → 输出 panel（增强）
    - ❌ 不允许丢失因子列
    """

    def __init__(self, panel: pd.DataFrame):
        if panel is None or panel.empty:
            raise ValueError("[Returns] Input panel is empty")

        self.panel = panel.copy()

    # =========================
    # 🚀 forward return
    # =========================
    def forward(self, horizon: int = 5) -> pd.DataFrame:
        """
        计算未来收益（增强 panel）

        返回：
            panel + ret_xd
        """

        logger.info(f"[Returns] Computing forward return | horizon={horizon}")

        df = compute_future_returns(self.panel, horizon)

        if df is None or df.empty:
            logger.warning("[Returns] Output is empty")

        # =========================
        # 可选：清理中间列
        # =========================
        if "future_close" in df.columns:
            df = df.drop(columns=["future_close"])

        return df
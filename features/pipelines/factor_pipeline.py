import numpy as np
import logging

from features.factors.registry import FactorRegistry

logger = logging.getLogger(__name__)


class FactorPipeline:
    """
    👻 动态因子管线（插件驱动）

    设计原则：
    - 因子解耦（registry）
    - 可观测（logging）
    - 可扩展（context）
    - 可复现（稳定顺序）
    """

    def __init__(self):
        self.registry = FactorRegistry().load_from_package()

    def run(self, df, factors=None, context=None):
        df = df.copy()

        # 👻 默认使用全部因子
        factors = factors or self.registry.list_factors()

        # 👻 保证执行顺序稳定（避免回测不一致）
        factors = sorted(factors)

        for name in factors:

            func = self.registry.get(name)

            if func is None:
                logger.warning(f"[FactorPipeline] factor not found: {name}")
                continue

            # 👻 避免重复计算（性能优化）
            if name in df.columns:
                continue

            try:
                df[name] = func(df, context=context)
            except Exception as e:
                logger.warning(f"[FactorPipeline] factor={name} failed: {e}")
                df[name] = np.nan

        return df
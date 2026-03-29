from pathlib import Path
from typing import Optional

import pandas as pd

from core.common.config import APP_CONFIG
from data.domains.universe_domain import Universe
from data.loaders.basic_loader import BasicLoader
from data.loaders.panel_loader import PanelLoader
from data.loaders.price_loader import PriceLoader
from data.loaders.universe_loader import UniverseLoader
from data.providers.analysis_provider import AnalysisProvider
from data.providers.panel_provider import PanelProvider
from data.providers.universe_provider import UniverseProvider


class DataService:
    """数据服务统一入口。

    这层是命令层、策略层、分析层访问数据的唯一门面：
    - 向下只依赖 Loader / Provider
    - 向上暴露面向业务语义的方法

    换句话说，Factor / IC 只应该说“我要分析用股票池 / 分析用 panel / 分析结果缓存”，
    而不应该知道缓存 key 如何组织、目录放在哪里、底层文件如何拼装。
    """

    def __init__(self, data_dir: Optional[str] = None):
        """初始化数据服务。

        默认路径统一从 Config 读取，这样项目里所有数据入口都共享同一套路径配置。
        """
        self.data_dir = Path(data_dir) if data_dir else APP_CONFIG.stock_dir
        self.lookback_days = APP_CONFIG.default_lookback_days

        self.price_loader = PriceLoader(self.data_dir)
        self.basic_loader = BasicLoader(self.data_dir)
        self.panel_loader = PanelLoader(self.price_loader, self.basic_loader)
        self.panel_provider = PanelProvider(self.panel_loader)
        self.analysis_provider = AnalysisProvider()
        self.universe_loader = UniverseLoader(self.data_dir)
        self.universe_provider = UniverseProvider(self.universe_loader)

    def get_analysis_panel(self, symbols, start, end, use_cache=True, cache_extras=None):
        """通用分析 panel 入口。

        这是更底层的分析 panel 方法，适合 Provider/DataService 内部复用。
        常规业务代码优先使用 `get_analysis_factor_panel()` 或
        `get_analysis_ic_panel()` 这类带场景语义的方法。
        """
        return self.panel_provider.load_analysis_panel(
            symbols=symbols,
            start=start,
            end=end,
            use_cache=use_cache,
            cache_extras=cache_extras,
        )

    def get_analysis_universe(self, limit=None, use_cache=True):
        """获取分析链路使用的股票池。"""
        symbols = self.universe_provider.load_analysis_universe(limit=limit, use_cache=use_cache)
        return Universe(symbols)

    def get_analysis_factor_panel(self, symbols, date, use_cache=True):
        """获取因子分析所需 panel。

        这里统一封装 lookback 规则，避免命令层重复计算窗口长度。
        """
        end = pd.to_datetime(date)
        start = end - pd.Timedelta(days=self.lookback_days)
        return self.get_analysis_panel(
            symbols=symbols,
            start=start,
            end=end,
            use_cache=use_cache,
            cache_extras={"lookback_days": self.lookback_days},
        )

    def load_factor_analysis(self, date, model, weights, top_n, limit):
        """读取 factor 分析结果缓存。"""
        return self.analysis_provider.load_factor_analysis(
            date=pd.to_datetime(date).strftime("%Y-%m-%d"),
            model=model,
            weights=weights,
            top_n=top_n,
            limit=limit,
            lookback_days=self.lookback_days,
        )

    def save_factor_analysis(self, date, model, weights, top_n, limit, scored: pd.DataFrame, metadata):
        """保存 factor 分析结果缓存。"""
        self.analysis_provider.save_factor_analysis(
            date=pd.to_datetime(date).strftime("%Y-%m-%d"),
            model=model,
            weights=weights,
            top_n=top_n,
            limit=limit,
            lookback_days=self.lookback_days,
            scored=scored,
            metadata=metadata,
        )

    def get_analysis_ic_panel(self, symbols, start, end, horizon, use_cache=True):
        """获取 IC 分析所需 panel。

        IC 需要额外的 forward return 计算空间，所以这里统一追加 buffer 天数，
        避免命令层重复处理日期扩展逻辑。
        """
        end_with_buffer = pd.to_datetime(end) + pd.Timedelta(days=horizon * 3)
        return self.get_analysis_panel(
            symbols=symbols,
            start=start,
            end=end_with_buffer,
            use_cache=use_cache,
            cache_extras={"lookback_buffer_days": horizon * 3},
        )

    def load_ic_analysis(self, start, end, horizon, limit, model, factors):
        """读取 IC 分析结果缓存。"""
        return self.analysis_provider.load_ic_analysis(
            start=pd.to_datetime(start).strftime("%Y-%m-%d"),
            end=pd.to_datetime(end).strftime("%Y-%m-%d"),
            horizon=horizon,
            limit=limit,
            model=model,
            factors=factors,
        )

    def save_ic_analysis(self, start, end, horizon, limit, model, factors, ic_df: pd.DataFrame, summary_df: pd.DataFrame, metadata):
        """保存 IC 分析结果缓存。"""
        self.analysis_provider.save_ic_analysis(
            start=pd.to_datetime(start).strftime("%Y-%m-%d"),
            end=pd.to_datetime(end).strftime("%Y-%m-%d"),
            horizon=horizon,
            limit=limit,
            model=model,
            factors=factors,
            ic_df=ic_df,
            summary_df=summary_df,
            metadata=metadata,
        )

    def get_panel(self, symbols, start, end, use_cache=True, cache_extras=None):
        """兼容旧接口，内部统一转到新的 analysis 入口。"""
        return self.get_analysis_panel(symbols, start, end, use_cache=use_cache, cache_extras=cache_extras)

    def get_universe(self, limit=None, use_cache=True):
        """兼容旧接口，内部统一转到新的 analysis 入口。"""
        return self.get_analysis_universe(limit=limit, use_cache=use_cache)

    def get_factor_panel(self, symbols, date, use_cache=True):
        """兼容旧接口，内部统一转到新的 analysis 入口。"""
        return self.get_analysis_factor_panel(symbols, date, use_cache=use_cache)

    def load_factor_result(self, date, model, weights, top_n, limit):
        """兼容旧接口，内部统一转到新的 analysis 入口。"""
        return self.load_factor_analysis(date, model, weights, top_n, limit)

    def save_factor_result(self, date, model, weights, top_n, limit, scored: pd.DataFrame, metadata):
        """兼容旧接口，内部统一转到新的 analysis 入口。"""
        self.save_factor_analysis(date, model, weights, top_n, limit, scored, metadata)

    def get_ic_panel(self, symbols, start, end, horizon, use_cache=True):
        """兼容旧接口，内部统一转到新的 analysis 入口。"""
        return self.get_analysis_ic_panel(symbols, start, end, horizon, use_cache=use_cache)

    def load_ic_result(self, start, end, horizon, limit, model, factors):
        """兼容旧接口，内部统一转到新的 analysis 入口。"""
        return self.load_ic_analysis(start, end, horizon, limit, model, factors)

    def save_ic_result(self, start, end, horizon, limit, model, factors, ic_df: pd.DataFrame, summary_df: pd.DataFrame, metadata):
        """兼容旧接口，内部统一转到新的 analysis 入口。"""
        self.save_ic_analysis(start, end, horizon, limit, model, factors, ic_df, summary_df, metadata)

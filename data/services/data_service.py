from pathlib import Path
from typing import Optional
import warnings

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
    """Shared data facade。

    `DataService` 是当前数据层对上层暴露的 shared data facade。
    它的职责边界应主要聚焦在两类能力：
    - 共享数据访问
    - 共享分析输入准备

    它负责把 Loader / Provider / Cache 组织成稳定的数据访问语义，
    让命令层、策略层、分析层不必感知底层文件、缓存 key 和拼装细节。

    同时也需要明确边界：
    product / trading 特定业务编排不应继续在这里膨胀；
    带有强场景语义的 factor / IC / backtest 规则应尽量停留在更上层。
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

    def _warn_legacy_interface(self, interface_name: str) -> None:
        warnings.warn(
            (
                f"{interface_name}() is a legacy DataService compatibility interface. "
                "New orchestration should compute scenario-specific rules at the "
                "application/engine layer and call get_analysis_panel(...)."
            ),
            DeprecationWarning,
            stacklevel=2,
        )

    # ------------------------------------------------------------------
    # Shared Analysis Input Access
    # ------------------------------------------------------------------

    # Preferred shared entry for new orchestration.
    def get_analysis_panel(self, symbols, start, end, use_cache=True, cache_extras=None):
        """[Shared Analysis Input Access] 获取通用分析 panel。

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
        """[Shared Analysis Input Access] 获取分析链路使用的股票池。"""
        symbols = self.universe_provider.load_analysis_universe(limit=limit, use_cache=use_cache)
        return Universe(symbols)

    # Legacy compatibility entry: keep for old factor callers only.
    # New orchestration should compute lookback at the application layer and
    # then call get_analysis_panel(...).
    def get_analysis_factor_panel(self, symbols, date, use_cache=True):
        self._warn_legacy_interface("get_analysis_factor_panel")
        """[Boundary Warning] 获取因子分析所需 panel。

        这里统一封装 lookback 规则，避免命令层重复计算窗口长度。
        当前保留该接口主要为了兼容旧调用点；
        新的业务编排应优先在 application 层组合 `get_analysis_panel(...)`。
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

    # Legacy compatibility entry: keep for old backtest callers only.
    # New orchestration should compute execution-delay/buffer at the upper layer
    # and then call get_analysis_panel(...).
    def get_analysis_backtest_panel(self, symbols, start, end, execution_delay=1, use_cache=True):
        self._warn_legacy_interface("get_analysis_backtest_panel")
        """[Boundary Warning] 获取回测分析所需 panel。

        回测需要在结束日期后额外保留一小段缓冲区间，
        用来承接“信号日 -> 执行日 -> 下一段收益区间”这条链路。
        """
        end_with_buffer = pd.to_datetime(end) + pd.Timedelta(days=max(execution_delay, 1) * 3)
        return self.get_analysis_panel(
            symbols=symbols,
            start=start,
            end=end_with_buffer,
            use_cache=use_cache,
            cache_extras={"execution_delay": execution_delay, "analysis": "backtest"},
        )

    def load_factor_analysis(self, date, model, weights, top_n, limit):
        """[Shared Analysis Input Access] 读取 factor 分析结果缓存。"""
        return self.analysis_provider.load_factor_analysis(
            date=pd.to_datetime(date).strftime("%Y-%m-%d"),
            model=model,
            weights=weights,
            top_n=top_n,
            limit=limit,
            lookback_days=self.lookback_days,
        )

    def save_factor_analysis(self, date, model, weights, top_n, limit, scored: pd.DataFrame, metadata):
        """[Shared Analysis Input Access] 保存 factor 分析结果缓存。"""
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

    # Legacy compatibility entry: keep for old IC callers only.
    # New orchestration should compute horizon buffer at the application layer
    # and then call get_analysis_panel(...).
    def get_analysis_ic_panel(self, symbols, start, end, horizon, use_cache=True):
        self._warn_legacy_interface("get_analysis_ic_panel")
        """[Boundary Warning] 获取 IC 分析所需 panel。

        IC 需要额外的 forward return 计算空间，所以这里统一追加 buffer 天数，
        避免命令层重复处理日期扩展逻辑。
        当前保留该接口主要为了兼容旧调用点；
        新的业务编排应优先在 application 层组合 `get_analysis_panel(...)`。
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
        """[Shared Analysis Input Access] 读取 IC 分析结果缓存。"""
        return self.analysis_provider.load_ic_analysis(
            start=pd.to_datetime(start).strftime("%Y-%m-%d"),
            end=pd.to_datetime(end).strftime("%Y-%m-%d"),
            horizon=horizon,
            limit=limit,
            model=model,
            factors=factors,
        )

    def save_ic_analysis(self, start, end, horizon, limit, model, factors, ic_df: pd.DataFrame, summary_df: pd.DataFrame, metadata):
        """[Shared Analysis Input Access] 保存 IC 分析结果缓存。"""
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

    # ------------------------------------------------------------------
    # Shared Raw Data Access
    # ------------------------------------------------------------------

    def get_panel(self, symbols, start, end, use_cache=True, cache_extras=None):
        """[Shared Raw Data Access] 兼容旧接口，获取基础 panel 数据入口。"""
        return self.get_analysis_panel(symbols, start, end, use_cache=use_cache, cache_extras=cache_extras)

    def get_universe(self, limit=None, use_cache=True):
        """[Shared Raw Data Access] 兼容旧接口，获取基础 universe 数据入口。"""
        return self.get_analysis_universe(limit=limit, use_cache=use_cache)

    # ------------------------------------------------------------------
    # Legacy / Boundary Warning
    # ------------------------------------------------------------------

    # Legacy alias: do not use as a new entry point.
    def get_factor_panel(self, symbols, date, use_cache=True):
        self._warn_legacy_interface("get_factor_panel")
        """[Boundary Warning] 兼容旧接口，获取 factor 场景 panel。"""
        return self.get_analysis_factor_panel(symbols, date, use_cache=use_cache)

    # Legacy alias: do not use as a new entry point.
    def get_backtest_panel(self, symbols, start, end, execution_delay=1, use_cache=True):
        self._warn_legacy_interface("get_backtest_panel")
        """[Boundary Warning] 兼容旧接口，获取 backtest 场景 panel。"""
        return self.get_analysis_backtest_panel(
            symbols,
            start,
            end,
            execution_delay=execution_delay,
            use_cache=use_cache,
        )

    def load_factor_result(self, date, model, weights, top_n, limit):
        """[Shared Analysis Input Access] 兼容旧接口，读取 factor 分析结果。"""
        return self.load_factor_analysis(date, model, weights, top_n, limit)

    def save_factor_result(self, date, model, weights, top_n, limit, scored: pd.DataFrame, metadata):
        """[Shared Analysis Input Access] 兼容旧接口，保存 factor 分析结果。"""
        self.save_factor_analysis(date, model, weights, top_n, limit, scored, metadata)

    # Legacy alias: do not use as a new entry point.
    def get_ic_panel(self, symbols, start, end, horizon, use_cache=True):
        self._warn_legacy_interface("get_ic_panel")
        """[Boundary Warning] 兼容旧接口，获取 IC 场景 panel。"""
        return self.get_analysis_ic_panel(symbols, start, end, horizon, use_cache=use_cache)

    def load_ic_result(self, start, end, horizon, limit, model, factors):
        """[Shared Analysis Input Access] 兼容旧接口，读取 IC 分析结果。"""
        return self.load_ic_analysis(start, end, horizon, limit, model, factors)

    def save_ic_result(self, start, end, horizon, limit, model, factors, ic_df: pd.DataFrame, summary_df: pd.DataFrame, metadata):
        """[Shared Analysis Input Access] 兼容旧接口，保存 IC 分析结果。"""
        self.save_ic_analysis(start, end, horizon, limit, model, factors, ic_df, summary_df, metadata)

    # ------------------------------------------------------------------
    # Future Out-of-Scope Examples
    # ------------------------------------------------------------------
    # get_signal_context(...)           # out of shared foundation scope
    # get_content_context(...)          # out of shared foundation scope
    # get_trade_decision_context(...)   # out of shared foundation scope

from typing import Any, Dict, Optional

import pandas as pd

from data.providers.cache.analysis_cache import AnalysisCache
from data.loaders.panel_loader import PanelLoader
from data.processors.cleaner_processor import clean_market_data
from data.domains.market_domain import Market


class PanelProvider:
    """Panel 数据拼装层。

    这一层只负责两件事：
    1. 根据分析场景生成稳定的 panel cache key；
    2. 在缓存与 Loader 之间做路由，并在返回前完成统一清洗。

    这样 DataService 和更上层的 Factor/IC 就不需要知道
    parquet 文件怎么读、缓存文件怎么命名、清洗步骤何时执行。
    """

    def __init__(self, panel_loader: PanelLoader, cache: Optional[AnalysisCache] = None):
        self.panel_loader = panel_loader
        self.cache = cache or AnalysisCache()

    def _panel_cache_key(self, symbols, start, end, cache_extras: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """构造 panel 缓存 key。

        `symbols/start/end` 是 panel 的主维度；
        `cache_extras` 用来追加分析场景特有的信息，例如：
        - 因子分析的 `lookback_days`
        - IC 分析的 `lookback_buffer_days`
        """
        cache_key = {
            "kind": "panel",
            "symbols": list(symbols),
            "start": pd.to_datetime(start).strftime("%Y-%m-%d"),
            "end": pd.to_datetime(end).strftime("%Y-%m-%d"),
        }
        if cache_extras:
            cache_key.update(cache_extras)
        return cache_key

    def load_analysis_panel(
        self,
        symbols,
        start,
        end,
        use_cache: bool = True,
        cache_extras: Optional[Dict[str, Any]] = None,
    ) -> Market:
        """读取分析用 panel。

        调用顺序固定为：
        1. 先尝试命中 `data/cache/panel`
        2. 未命中时再委托给 `PanelLoader`
        3. 对结果执行统一清洗
        4. 回写缓存并返回 `Market` 领域对象
        """
        panel = pd.DataFrame()
        cache_key = self._panel_cache_key(symbols, start, end, cache_extras) if use_cache else None

        if use_cache and cache_key:
            panel = self.cache.load_panel(cache_key)
            if not panel.empty:
                return Market(panel)

        panel = self.panel_loader.load_panel(symbols, start, end)
        if panel is None or panel.empty:
            return Market(panel)

        panel = clean_market_data(panel)
        if use_cache and cache_key:
            self.cache.save_panel(cache_key, panel)

        return Market(panel)

    def get_panel(
        self,
        symbols,
        start,
        end,
        use_cache: bool = True,
        cache_extras: Optional[Dict[str, Any]] = None,
    ) -> Market:
        """兼容旧接口，内部统一转到新的 analysis 入口。"""
        return self.load_analysis_panel(symbols, start, end, use_cache=use_cache, cache_extras=cache_extras)

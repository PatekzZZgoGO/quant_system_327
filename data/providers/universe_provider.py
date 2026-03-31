from typing import Optional

from data.providers.cache.analysis_cache import AnalysisCache
from data.loaders.universe_loader import UniverseLoader


class UniverseProvider:
    """Universe 数据拼装层。

    负责把 UniverseLoader 提供的股票池结果包装成可缓存的数据入口，
    让上层只关心“拿到一组股票代码”，不用关心股票池是从文件扫描
    还是从缓存恢复出来的。
    """

    def __init__(self, universe_loader: UniverseLoader, cache: Optional[AnalysisCache] = None):
        self.universe_loader = universe_loader
        self.cache = cache or AnalysisCache()

    def _universe_cache_key(self, limit: Optional[int]):
        """按分析场景生成 universe cache key。"""
        return {
            "kind": "universe",
            "limit": limit,
        }

    def load_analysis_universe(self, limit: Optional[int] = None, use_cache: bool = True):
        """读取分析用股票池。

        对分析链路来说，`limit` 不只是展示参数，也会影响实际计算对象，
        所以它必须进入缓存 key，确保不同 limit 的 universe 不会混用。
        """
        cache_key = self._universe_cache_key(limit)

        if use_cache:
            cached = self.cache.load_universe(cache_key)
            if cached is not None:
                return cached["symbols"]

        symbols = self.universe_loader.get_universe(limit=limit)

        if use_cache:
            self.cache.save_universe(
                cache_key,
                symbols=symbols,
                metadata={
                    "limit": limit,
                    "count": len(symbols),
                },
            )

        return symbols

    def get_universe(self, limit: Optional[int] = None, use_cache: bool = True):
        """兼容旧接口，内部统一转到新的 analysis 入口。"""
        return self.load_analysis_universe(limit=limit, use_cache=use_cache)

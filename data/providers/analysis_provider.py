from typing import Any, Dict, Iterable, Optional

import pandas as pd

from data.providers.cache.analysis_cache import AnalysisCache


class AnalysisProvider:
    """因子分析结果拼装层。

    这里不做实际的因子计算，只负责：
    - 为 factor / ic 结果生成稳定缓存 key
    - 在 DataService 与底层缓存之间做统一转发

    这样命令层和计算层都不用感知缓存目录结构与命名细节。
    """

    def __init__(self, cache: Optional[AnalysisCache] = None):
        self.cache = cache or AnalysisCache()

    def _factor_cache_key(
        self,
        date: str,
        model: str,
        weights: Dict[str, Any],
        top_n: int,
        limit: Optional[int],
        lookback_days: int,
    ) -> Dict[str, Any]:
        return {
            "kind": "factor",
            "date": date,
            "model": model,
            "weights": weights,
            "top_n": top_n,
            "limit": limit,
            "lookback_days": lookback_days,
        }

    def load_factor_analysis(
        self,
        date: str,
        model: str,
        weights: Dict[str, Any],
        top_n: int,
        limit: Optional[int],
        lookback_days: int,
    ):
        """加载 factor 分析结果缓存。"""
        return self.cache.load_factor_result(
            self._factor_cache_key(date, model, weights, top_n, limit, lookback_days)
        )

    def save_factor_analysis(
        self,
        date: str,
        model: str,
        weights: Dict[str, Any],
        top_n: int,
        limit: Optional[int],
        lookback_days: int,
        scored: pd.DataFrame,
        metadata: Dict[str, Any],
    ) -> None:
        """保存 factor 分析结果缓存。"""
        self.cache.save_factor_result(
            self._factor_cache_key(date, model, weights, top_n, limit, lookback_days),
            scored,
            metadata,
        )

    def _ic_cache_key(
        self,
        start: str,
        end: str,
        horizon: int,
        limit: Optional[int],
        model: Optional[str],
        factors: Iterable[str],
    ) -> Dict[str, Any]:
        return {
            "kind": "ic",
            "start": start,
            "end": end,
            "horizon": horizon,
            "limit": limit,
            "model": model,
            "factors": list(factors),
            "lookback_buffer_days": horizon * 3,
        }

    def load_ic_analysis(
        self,
        start: str,
        end: str,
        horizon: int,
        limit: Optional[int],
        model: Optional[str],
        factors: Iterable[str],
    ):
        """加载 IC 分析结果缓存。"""
        return self.cache.load_ic_result(self._ic_cache_key(start, end, horizon, limit, model, factors))

    def save_ic_analysis(
        self,
        start: str,
        end: str,
        horizon: int,
        limit: Optional[int],
        model: Optional[str],
        factors: Iterable[str],
        ic_df: pd.DataFrame,
        summary_df: pd.DataFrame,
        metadata: Dict[str, Any],
    ) -> None:
        """保存 IC 分析结果缓存。"""
        self.cache.save_ic_result(
            self._ic_cache_key(start, end, horizon, limit, model, factors),
            ic_df,
            summary_df,
            metadata,
        )

    def load_factor_result(
        self,
        date: str,
        model: str,
        weights: Dict[str, Any],
        top_n: int,
        limit: Optional[int],
        lookback_days: int,
    ):
        """兼容旧接口，内部统一转到新的 analysis 入口。"""
        return self.load_factor_analysis(date, model, weights, top_n, limit, lookback_days)

    def save_factor_result(
        self,
        date: str,
        model: str,
        weights: Dict[str, Any],
        top_n: int,
        limit: Optional[int],
        lookback_days: int,
        scored: pd.DataFrame,
        metadata: Dict[str, Any],
    ) -> None:
        """兼容旧接口，内部统一转到新的 analysis 入口。"""
        self.save_factor_analysis(date, model, weights, top_n, limit, lookback_days, scored, metadata)

    def load_ic_result(
        self,
        start: str,
        end: str,
        horizon: int,
        limit: Optional[int],
        model: Optional[str],
        factors: Iterable[str],
    ):
        """兼容旧接口，内部统一转到新的 analysis 入口。"""
        return self.load_ic_analysis(start, end, horizon, limit, model, factors)

    def save_ic_result(
        self,
        start: str,
        end: str,
        horizon: int,
        limit: Optional[int],
        model: Optional[str],
        factors: Iterable[str],
        ic_df: pd.DataFrame,
        summary_df: pd.DataFrame,
        metadata: Dict[str, Any],
    ) -> None:
        """兼容旧接口，内部统一转到新的 analysis 入口。"""
        self.save_ic_analysis(start, end, horizon, limit, model, factors, ic_df, summary_df, metadata)

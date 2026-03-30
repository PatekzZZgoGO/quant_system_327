import importlib
import logging
from typing import Dict, Optional

import pandas as pd

from data.services.data_service import DataService
from exceptions.config import ConfigurationError
from exceptions.pipeline import PipelineExecutionError
from features.analysis.ic_temp import compute_rank_corr
from features.engine.factor_engine import FactorEngine
from features.engine.scoring_engine import ScoringEngine
from utils.result_metadata import build_result_metadata

logger = logging.getLogger(__name__)


def load_model(name: str):
    try:
        logger.info("[FactorApp] Loading model: %s", name)
        return importlib.import_module(f"models.alpha.{name}")
    except ModuleNotFoundError as exc:
        logger.error("[FactorApp] model not found: %s", name)
        raise ConfigurationError(f"[FactorApp] model not found: {name}") from exc


def resolve_weights(model, date, user_weights: Optional[str] = None) -> Dict[str, float]:
    if user_weights:
        logger.info("[FactorApp] Using user weights: %s", user_weights)
        return dict((k.strip(), float(v)) for k, v in (item.split("=") for item in user_weights.split(",")))

    if hasattr(model, "get_weights"):
        return model.get_weights(date)
    if hasattr(model, "WEIGHTS"):
        return model.WEIGHTS
    raise ConfigurationError("[FactorApp] model has no weights")


def _load_factor_panel(data_service: DataService, symbols, date, use_cache: bool = True):
    end = pd.to_datetime(date)
    start = end - pd.Timedelta(days=data_service.lookback_days)
    return data_service.get_analysis_panel(
        symbols=symbols,
        start=start,
        end=end,
        use_cache=use_cache,
        cache_extras={"lookback_days": data_service.lookback_days},
    )


def run_factor_analysis(
    *,
    date,
    model_name: str,
    top_n: int = 50,
    limit=None,
    user_weights: Optional[str] = None,
    data_service: Optional[DataService] = None,
    factor_engine: Optional[FactorEngine] = None,
    scoring_engine: Optional[ScoringEngine] = None,
):
    logger.info("[FactorApp] Start factor orchestration")
    data_service = data_service or DataService()
    factor_engine = factor_engine or FactorEngine(None)
    scoring_engine = scoring_engine or ScoringEngine()

    analysis_date = pd.to_datetime(date)
    universe = data_service.get_analysis_universe(limit=limit)
    stock_list = universe.symbols
    if not stock_list:
        raise PipelineExecutionError("[FactorApp] stock list is empty")

    model = load_model(model_name)
    weights = resolve_weights(model, analysis_date, user_weights)

    cached_result = data_service.load_factor_analysis(
        date=analysis_date,
        model=model_name,
        weights=weights,
        top_n=top_n,
        limit=limit,
    )
    if cached_result is not None:
        logger.info("[FactorApp] Factor cache hit")
        return {
            "scored": cached_result["scored"],
            "rank_corr": cached_result["metadata"]["rank_corr"],
            "metadata": cached_result["metadata"],
            "weights": weights,
            "date": analysis_date,
            "model": model_name,
            "from_cache": True,
            "universe_size": universe.size(),
        }

    panel = _load_factor_panel(data_service, stock_list, analysis_date, use_cache=True).panel
    if panel is None or panel.empty:
        raise PipelineExecutionError("[FactorApp] panel is empty")

    panel = factor_engine.pipeline.run(panel.set_index("Date"), factors=list(weights.keys())).reset_index()
    panel = factor_engine.handle_missing(panel, factors=list(weights.keys()))

    snapshot = panel[panel["Date"] == analysis_date]
    if snapshot.empty:
        raise PipelineExecutionError("[FactorApp] snapshot is empty")

    scored = scoring_engine.score(snapshot, weights)
    rank_corr = compute_rank_corr(scored, target_col="score", factors=list(weights.keys()))
    source_start = analysis_date - pd.Timedelta(days=data_service.lookback_days)
    metadata = build_result_metadata(
        config={
            "model": model_name,
            "weights": weights,
            "top_n": top_n,
            "limit": limit,
            "lookback_days": data_service.lookback_days,
        },
        source_window={
            "start": source_start.strftime("%Y-%m-%d"),
            "end": analysis_date.strftime("%Y-%m-%d"),
        },
        universe_version=f"analysis_universe:limit={limit if limit is not None else 'all'}:count={universe.size()}",
        extra={
            "rank_corr": rank_corr,
            "weights": weights,
            "date": analysis_date.strftime("%Y-%m-%d"),
            "model": model_name,
        },
    )
    data_service.save_factor_analysis(
        date=analysis_date,
        model=model_name,
        weights=weights,
        top_n=top_n,
        limit=limit,
        scored=scored,
        metadata=metadata,
    )
    return {
        "scored": scored,
        "rank_corr": rank_corr,
        "metadata": metadata,
        "weights": weights,
        "date": analysis_date,
        "model": model_name,
        "from_cache": False,
        "universe_size": universe.size(),
    }

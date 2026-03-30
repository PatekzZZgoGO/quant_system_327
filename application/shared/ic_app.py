import importlib
import logging
from typing import Optional

import pandas as pd

from data.domains.ic_domain import IC
from data.domains.returns_domain import Returns
from data.services.data_service import DataService
from features.analysis.ic_temp import summarize_ic
from features.engine.factor_engine import FactorEngine

logger = logging.getLogger(__name__)


def load_model(name: str):
    return importlib.import_module(f"models.alpha.{name}")


def resolve_factors(model_name: Optional[str], user_factors, factor_engine: FactorEngine):
    if user_factors:
        return user_factors, "user"

    if model_name:
        model = load_model(model_name)
        if hasattr(model, "get_weights"):
            return list(model.get_weights().keys()), "model"
        if hasattr(model, "WEIGHTS"):
            return list(model.WEIGHTS.keys()), "model"

    return factor_engine.pipeline.registry.list_factors(), "registry"


def _load_ic_panel(data_service: DataService, symbols, start, end, horizon: int, use_cache: bool = True):
    end_with_buffer = pd.to_datetime(end) + pd.Timedelta(days=horizon * 3)
    return data_service.get_analysis_panel(
        symbols=symbols,
        start=start,
        end=end_with_buffer,
        use_cache=use_cache,
        cache_extras={"lookback_buffer_days": horizon * 3},
    )


def run_ic_analysis(
    *,
    start,
    end,
    horizon: int = 5,
    limit=None,
    model_name: Optional[str] = None,
    user_factors=None,
    data_service: Optional[DataService] = None,
    factor_engine: Optional[FactorEngine] = None,
):
    logger.info("[ICApp] Start IC orchestration")
    data_service = data_service or DataService()
    factor_engine = factor_engine or FactorEngine(None)

    universe = data_service.get_analysis_universe(limit=limit)
    stock_list = universe.symbols
    factors, source = resolve_factors(model_name, user_factors, factor_engine)

    cached_result = data_service.load_ic_analysis(
        start=start,
        end=end,
        horizon=horizon,
        limit=limit,
        model=model_name,
        factors=factors,
    )
    if cached_result is not None:
        logger.info("[ICApp] IC cache hit")
        return {
            "ic_df": cached_result["ic_df"],
            "summary": cached_result["summary"],
            "factors": factors,
            "source": source,
            "from_cache": True,
            "universe_size": universe.size(),
        }

    panel = _load_ic_panel(
        data_service,
        stock_list,
        start=start,
        end=end,
        horizon=horizon,
        use_cache=True,
    ).panel
    if panel is None or panel.empty:
        raise ValueError("[ICApp] panel is empty")

    panel = factor_engine.pipeline.run(panel.set_index("Date"), factors=factors).reset_index()
    panel = factor_engine.handle_missing(panel, factors)

    returns = Returns(panel)
    panel = returns.forward(horizon=horizon)
    ret_col = f"ret_{horizon}d"

    ic_engine = IC(panel)
    ic_df = ic_engine.compute(factors=factors, ret_col=ret_col, method="spearman")
    if ic_df.empty:
        raise ValueError("[ICApp] no IC results")

    summary = summarize_ic(ic_df)
    data_service.save_ic_analysis(
        start=start,
        end=end,
        horizon=horizon,
        limit=limit,
        model=model_name,
        factors=factors,
        ic_df=ic_df,
        summary_df=summary,
        metadata={
            "factors": factors,
            "source": source,
            "start": start,
            "end": end,
            "horizon": horizon,
        },
    )
    return {
        "ic_df": ic_df,
        "summary": summary,
        "factors": factors,
        "source": source,
        "from_cache": False,
        "universe_size": universe.size(),
    }

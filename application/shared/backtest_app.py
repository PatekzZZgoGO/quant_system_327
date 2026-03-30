import importlib
from datetime import datetime
from typing import Optional

from backtest.engine import BacktestEngine
from backtest.simulation import ExecutionModel
from core.common.config import APP_CONFIG
from data.services.data_service import DataService
from features.engine.factor_engine import FactorEngine
from features.engine.scoring_engine import ScoringEngine


def load_model(name: str):
    """Load alpha model module."""
    return importlib.import_module(f"models.alpha.{name}")


def resolve_weights(model, date=None):
    """Resolve weight definition from the model."""
    if hasattr(model, "get_weights"):
        return model.get_weights(date)
    if hasattr(model, "WEIGHTS"):
        return model.WEIGHTS
    raise ValueError("[BacktestApp] model has no weights")


def save_backtest_result(result, model_name: str):
    """Persist backtest artifacts to the current compatible output path."""
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = APP_CONFIG.backtest_runs_dir / f"{run_id}_{model_name}"
    output_dir.mkdir(parents=True, exist_ok=True)

    result["summary"].to_csv(output_dir / "summary.csv", index=False)
    result["daily_pnl"].to_csv(output_dir / "daily_pnl.csv", index=False)
    result["trades"].to_csv(output_dir / "trades.csv", index=False)
    result["signals"].to_csv(output_dir / "signals.csv", index=False)
    result["positions"].to_csv(output_dir / "positions.csv", index=False)

    return output_dir


def run_backtest_analysis(
    *,
    start,
    end,
    model_name: str,
    top_n: int = 20,
    limit: Optional[int] = None,
    rebalance_every: int = 1,
    execution_delay: int = 1,
    commission_rate: float = 0.001,
    slippage_rate: float = 0.0,
    use_cache: bool = True,
    save: bool = False,
    data_service: Optional[DataService] = None,
    factor_engine: Optional[FactorEngine] = None,
    scoring_engine: Optional[ScoringEngine] = None,
):
    data_service = data_service or DataService()
    factor_engine = factor_engine or FactorEngine(None)
    scoring_engine = scoring_engine or ScoringEngine()
    execution_model = ExecutionModel(
        commission_rate=commission_rate,
        slippage_rate=slippage_rate,
    )
    engine = BacktestEngine(
        data_service=data_service,
        factor_engine=factor_engine,
        scoring_engine=scoring_engine,
        execution_model=execution_model,
    )

    model = load_model(model_name)
    weights = resolve_weights(model, start)

    result = engine.run(
        start=start,
        end=end,
        weights=weights,
        model_name=model_name,
        top_n=top_n,
        limit=limit,
        rebalance_every=rebalance_every,
        execution_delay=execution_delay,
        use_cache=use_cache,
    )

    output_dir = save_backtest_result(result, model_name) if save else None
    return {
        "result": result,
        "weights": weights,
        "model": model_name,
        "output_dir": output_dir,
    }

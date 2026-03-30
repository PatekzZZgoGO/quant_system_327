from application.shared.backtest_app import run_backtest_analysis
from utils.run_tracker import fail_run, finish_run, start_run


def run_backtest_pipeline(
    *,
    start,
    end,
    model_name: str,
    top_n: int = 20,
    limit=None,
    rebalance_every: int = 1,
    execution_delay: int = 1,
    commission_rate: float = 0.001,
    slippage_rate: float = 0.0,
    use_cache: bool = True,
    save: bool = False,
):
    """Run the shared backtest pipeline."""
    run_record = start_run(
        task_name="backtest_pipeline",
        input_params={
            "start": start,
            "end": end,
            "model_name": model_name,
            "top_n": top_n,
            "limit": limit,
            "rebalance_every": rebalance_every,
            "execution_delay": execution_delay,
            "commission_rate": commission_rate,
            "slippage_rate": slippage_rate,
            "use_cache": use_cache,
            "save": save,
        },
    )
    try:
        payload = run_backtest_analysis(
            start=start,
            end=end,
            model_name=model_name,
            top_n=top_n,
            limit=limit,
            rebalance_every=rebalance_every,
            execution_delay=execution_delay,
            commission_rate=commission_rate,
            slippage_rate=slippage_rate,
            use_cache=use_cache,
            save=save,
        )
    except Exception as exc:
        fail_run(run_record, error_message=str(exc))
        raise

    tracker_record = finish_run(
        run_record,
        output_path=str(payload["output_dir"]) if payload.get("output_dir") is not None else None,
    )
    payload["run_record"] = tracker_record
    return payload

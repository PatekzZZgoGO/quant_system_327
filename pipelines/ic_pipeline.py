from application.shared.ic_app import run_ic_analysis
from utils.run_tracker import fail_run, finish_run, start_run


def run_ic_pipeline(
    *,
    start,
    end,
    horizon: int = 5,
    limit=None,
    model_name=None,
    user_factors=None,
):
    """Run the shared IC analysis pipeline.

    This pipeline is the top-level orchestration entry for IC analysis.
    It currently delegates to the shared application orchestration while
    establishing a stable pipeline-layer call site for commands.
    """
    run_record = start_run(
        task_name="ic_pipeline",
        input_params={
            "start": start,
            "end": end,
            "horizon": horizon,
            "limit": limit,
            "model_name": model_name,
            "user_factors": user_factors,
        },
    )
    try:
        payload = run_ic_analysis(
            start=start,
            end=end,
            horizon=horizon,
            limit=limit,
            model_name=model_name,
            user_factors=user_factors,
        )
    except Exception as exc:
        fail_run(run_record, error_message=str(exc))
        raise

    tracker_record = finish_run(
        run_record,
        output_path=None,
    )
    payload["run_record"] = tracker_record
    return payload

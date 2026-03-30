from application.shared.factor_app import run_factor_analysis
from utils.run_tracker import fail_run, finish_run, start_run


def run_factor_pipeline(
    *,
    date,
    model_name: str,
    top_n: int = 50,
    limit=None,
    user_weights=None,
):
    """Run the shared factor analysis pipeline.

    This pipeline is the top-level orchestration entry for factor analysis.
    It currently delegates to the shared application orchestration while
    establishing a stable pipeline-layer call site for commands.
    """
    run_record = start_run(
        task_name="factor_pipeline",
        input_params={
            "date": date,
            "model_name": model_name,
            "top_n": top_n,
            "limit": limit,
            "user_weights": user_weights,
        },
    )
    try:
        payload = run_factor_analysis(
            date=date,
            model_name=model_name,
            top_n=top_n,
            limit=limit,
            user_weights=user_weights,
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

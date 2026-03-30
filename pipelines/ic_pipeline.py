from application.shared.ic_app import run_ic_analysis


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
    return run_ic_analysis(
        start=start,
        end=end,
        horizon=horizon,
        limit=limit,
        model_name=model_name,
        user_factors=user_factors,
    )

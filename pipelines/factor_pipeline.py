from application.shared.factor_app import run_factor_analysis


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
    return run_factor_analysis(
        date=date,
        model_name=model_name,
        top_n=top_n,
        limit=limit,
        user_weights=user_weights,
    )

from pipelines import factor_pipeline


def test_run_factor_pipeline_wraps_app_payload(monkeypatch):
    monkeypatch.setattr(
        factor_pipeline,
        "run_factor_analysis",
        lambda **kwargs: {"date": kwargs["date"], "model": kwargs["model_name"]},
    )
    monkeypatch.setattr(
        factor_pipeline,
        "start_run",
        lambda **kwargs: {"task_name": kwargs["task_name"], "status": "running"},
    )
    monkeypatch.setattr(
        factor_pipeline,
        "finish_run",
        lambda run_record, output_path=None: {**run_record, "status": "success", "output_path": output_path},
    )

    payload = factor_pipeline.run_factor_pipeline(
        date="2024-01-05",
        model_name="simple_alpha",
        top_n=5,
        limit=10,
    )

    assert payload["date"] == "2024-01-05"
    assert payload["model"] == "simple_alpha"
    assert payload["run_record"]["task_name"] == "factor_pipeline"
    assert payload["run_record"]["status"] == "success"

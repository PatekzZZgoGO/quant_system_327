from pipelines import ic_pipeline


def test_run_ic_pipeline_wraps_app_payload(monkeypatch):
    monkeypatch.setattr(
        ic_pipeline,
        "run_ic_analysis",
        lambda **kwargs: {"summary": {"horizon": kwargs["horizon"]}, "source": "model"},
    )
    monkeypatch.setattr(
        ic_pipeline,
        "start_run",
        lambda **kwargs: {"task_name": kwargs["task_name"], "status": "running"},
    )
    monkeypatch.setattr(
        ic_pipeline,
        "finish_run",
        lambda run_record, output_path=None: {**run_record, "status": "success", "output_path": output_path},
    )

    payload = ic_pipeline.run_ic_pipeline(
        start="2024-01-01",
        end="2024-01-05",
        horizon=3,
        limit=10,
        model_name="simple_alpha",
    )

    assert payload["summary"] == {"horizon": 3}
    assert payload["source"] == "model"
    assert payload["run_record"]["task_name"] == "ic_pipeline"
    assert payload["run_record"]["status"] == "success"

from pipelines import data_pipeline


def test_run_data_update_stock_pipeline_wraps_app_result(monkeypatch):
    def fake_run_update_stock(**kwargs):
        return {"code": kwargs["code"], "success": True}

    monkeypatch.setattr(data_pipeline, "run_update_stock", fake_run_update_stock)

    payload = data_pipeline.run_data_update_stock_pipeline(
        code="000001.SZ",
        start_date="2024-01-01",
        end_date="2024-01-31",
        force_refresh=False,
    )

    assert payload["code"] == "000001.SZ"
    assert payload["run_record"]["status"] == "success"


def test_run_data_status_cache_pipeline_wraps_app_result(monkeypatch):
    monkeypatch.setattr(data_pipeline, "get_cache_status", lambda: {"stats": {"total": 1}})

    payload = data_pipeline.run_data_status_cache_pipeline()

    assert payload["stats"] == {"total": 1}
    assert payload["run_record"]["status"] == "success"

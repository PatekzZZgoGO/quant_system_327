from application.shared.data_app import get_cache_status, run_update_stock, run_update_stocks
from utils.run_tracker import fail_run, finish_run, start_run


def run_data_update_stock_pipeline(
    *,
    code: str,
    start_date=None,
    end_date=None,
    force_refresh: bool = False,
):
    run_record = start_run(
        task_name="data_update_stock_pipeline",
        input_params={
            "code": code,
            "start_date": start_date,
            "end_date": end_date,
            "force_refresh": force_refresh,
        },
    )
    try:
        payload = run_update_stock(
            code=code,
            start_date=start_date,
            end_date=end_date,
            force_refresh=force_refresh,
        )
    except Exception as exc:
        fail_run(run_record, error_message=str(exc))
        raise

    tracker_record = finish_run(run_record, output_path=None)
    payload["run_record"] = tracker_record
    return payload


def run_data_update_stocks_pipeline(
    *,
    start_date=None,
    end_date=None,
    limit=None,
    force_refresh: bool = False,
    resume: bool = False,
):
    run_record = start_run(
        task_name="data_update_stocks_pipeline",
        input_params={
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "force_refresh": force_refresh,
            "resume": resume,
        },
    )
    try:
        payload = run_update_stocks(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            force_refresh=force_refresh,
            resume=resume,
        )
    except Exception as exc:
        fail_run(run_record, error_message=str(exc))
        raise

    tracker_record = finish_run(run_record, output_path=None)
    payload["run_record"] = tracker_record
    return payload


def run_data_status_cache_pipeline():
    run_record = start_run(
        task_name="data_status_cache_pipeline",
        input_params={},
    )
    try:
        payload = get_cache_status()
    except Exception as exc:
        fail_run(run_record, error_message=str(exc))
        raise

    tracker_record = finish_run(run_record, output_path=None)
    payload["run_record"] = tracker_record
    return payload

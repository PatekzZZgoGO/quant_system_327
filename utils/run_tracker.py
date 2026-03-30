import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from core.common.config import APP_CONFIG
from utils.result_metadata import generate_run_id


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tracker_dir(base_dir: Optional[Path] = None) -> Path:
    root = Path(base_dir) if base_dir else APP_CONFIG.root_dir / "logs" / "run_tracker"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _tracker_path(task_name: str, base_dir: Optional[Path] = None) -> Path:
    return _tracker_dir(base_dir) / f"{task_name}.jsonl"


def _write_record(record: Dict[str, Any], base_dir: Optional[Path] = None) -> Path:
    path = _tracker_path(record["task_name"], base_dir=base_dir)
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(record, ensure_ascii=True, default=str) + "\n")
    return path


def start_run(task_name: str, input_params: Dict[str, Any], run_id: Optional[str] = None, base_dir: Optional[Path] = None):
    record = {
        "task_name": task_name,
        "run_id": run_id or generate_run_id(task_name),
        "start_time": _now_iso(),
        "end_time": None,
        "status": "running",
        "input_params": input_params,
        "output_path": None,
        "error_message": None,
    }
    _write_record(record, base_dir=base_dir)
    return record


def finish_run(record: Dict[str, Any], output_path: Optional[str] = None, base_dir: Optional[Path] = None):
    finished = dict(record)
    finished["end_time"] = _now_iso()
    finished["status"] = "success"
    finished["output_path"] = output_path
    _write_record(finished, base_dir=base_dir)
    return finished


def fail_run(record: Dict[str, Any], error_message: str, output_path: Optional[str] = None, base_dir: Optional[Path] = None):
    failed = dict(record)
    failed["end_time"] = _now_iso()
    failed["status"] = "failed"
    failed["output_path"] = output_path
    failed["error_message"] = error_message
    _write_record(failed, base_dir=base_dir)
    return failed

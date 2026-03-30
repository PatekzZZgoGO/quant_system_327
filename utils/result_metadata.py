import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional


DEFAULT_METADATA_VERSION = "v1"


def generate_run_id(prefix: str = "run") -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{prefix}_{timestamp}"


def compute_config_hash(config: Optional[Dict[str, Any]]) -> str:
    payload = config or {}
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def build_result_metadata(
    *,
    config: Optional[Dict[str, Any]],
    source_window: Dict[str, Any],
    universe_version: str,
    version: str = DEFAULT_METADATA_VERSION,
    run_id: Optional[str] = None,
    created_at: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    metadata = {
        "run_id": run_id or generate_run_id(),
        "version": version,
        "config_hash": compute_config_hash(config),
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "source_window": source_window,
        "universe_version": universe_version,
    }
    if extra:
        metadata.update(extra)
    return metadata

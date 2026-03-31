import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from core.common.config import APP_CONFIG


class AnalysisCache:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir) if base_dir else APP_CONFIG.cache_dir
        APP_CONFIG.ensure_dirs(
            [
                self.base_dir,
                self.panel_dir,
                self.factor_dir,
                self.ic_dir,
                self.universe_dir,
            ]
        )

    @property
    def panel_dir(self) -> Path:
        return self.base_dir / "panel"

    @property
    def factor_dir(self) -> Path:
        return self.base_dir / "factor"

    @property
    def ic_dir(self) -> Path:
        return self.base_dir / "ic"

    @property
    def universe_dir(self) -> Path:
        return self.base_dir / "universe"

    def _stable_key(self, payload: Dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def _json_path(self, directory: Path, key: str) -> Path:
        return directory / f"{key}.json"

    def _frame_path(self, directory: Path, key: str, suffix: str) -> Path:
        return directory / f"{key}_{suffix}.parquet"

    def load_panel(self, cache_key: Dict[str, Any]) -> pd.DataFrame:
        key = self._stable_key(cache_key)
        path = self._frame_path(self.panel_dir, key, "panel")
        if not path.exists():
            return pd.DataFrame()
        return pd.read_parquet(path)

    def save_panel(self, cache_key: Dict[str, Any], panel: pd.DataFrame) -> Path:
        key = self._stable_key(cache_key)
        path = self._frame_path(self.panel_dir, key, "panel")
        panel.to_parquet(path)
        return path

    def load_factor_result(self, cache_key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        key = self._stable_key(cache_key)
        meta_path = self._json_path(self.factor_dir, key)
        scored_path = self._frame_path(self.factor_dir, key, "scored")
        if not meta_path.exists() or not scored_path.exists():
            return None
        return {
            "metadata": json.loads(meta_path.read_text(encoding="utf-8")),
            "scored": pd.read_parquet(scored_path),
        }

    def save_factor_result(self, cache_key: Dict[str, Any], scored: pd.DataFrame, metadata: Dict[str, Any]) -> None:
        key = self._stable_key(cache_key)
        self._frame_path(self.factor_dir, key, "scored").parent.mkdir(parents=True, exist_ok=True)
        scored.to_parquet(self._frame_path(self.factor_dir, key, "scored"))
        self._json_path(self.factor_dir, key).write_text(
            json.dumps(metadata, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def load_ic_result(self, cache_key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        key = self._stable_key(cache_key)
        meta_path = self._json_path(self.ic_dir, key)
        ic_path = self._frame_path(self.ic_dir, key, "ic")
        summary_path = self._frame_path(self.ic_dir, key, "summary")
        if not meta_path.exists() or not ic_path.exists() or not summary_path.exists():
            return None
        return {
            "metadata": json.loads(meta_path.read_text(encoding="utf-8")),
            "ic_df": pd.read_parquet(ic_path),
            "summary": pd.read_parquet(summary_path),
        }

    def save_ic_result(
        self,
        cache_key: Dict[str, Any],
        ic_df: pd.DataFrame,
        summary_df: pd.DataFrame,
        metadata: Dict[str, Any],
    ) -> None:
        key = self._stable_key(cache_key)
        ic_df.to_parquet(self._frame_path(self.ic_dir, key, "ic"))
        summary_df.to_parquet(self._frame_path(self.ic_dir, key, "summary"))
        self._json_path(self.ic_dir, key).write_text(
            json.dumps(metadata, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def load_universe(self, cache_key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        key = self._stable_key(cache_key)
        meta_path = self._json_path(self.universe_dir, key)
        if not meta_path.exists():
            return None
        return json.loads(meta_path.read_text(encoding="utf-8"))

    def save_universe(self, cache_key: Dict[str, Any], symbols, metadata: Dict[str, Any]) -> None:
        key = self._stable_key(cache_key)
        payload = {
            "symbols": list(symbols),
            "metadata": metadata,
        }
        self._json_path(self.universe_dir, key).write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

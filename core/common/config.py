from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Config:
    root_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2])
    env: str = "dev"
    default_lookback_days: int = 252 * 2

    def __post_init__(self):
        self.ensure_dirs(
            [
                self.data_dir,
                self.raw_dir,
                self.processed_dir,
                self.stock_dir,
                self.cache_dir,
                self.cache_panel_dir,
                self.cache_factor_dir,
                self.cache_ic_dir,
                self.cache_universe_dir,
                self.backtest_dir,
                self.backtest_results_dir,
                self.backtest_runs_dir,
            ]
        )

    @property
    def data_dir(self) -> Path:
        return self.root_dir / "data" / "datasets"

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def stock_dir(self) -> Path:
        return self.processed_dir / "stocks"

    @property
    def stock_list_file(self) -> Path:
        return self.processed_dir / "stock_list.csv"

    @property
    def cache_dir(self) -> Path:
        return self.root_dir / "data" / "cache"

    @property
    def cache_panel_dir(self) -> Path:
        return self.cache_dir / "panel"

    @property
    def cache_factor_dir(self) -> Path:
        return self.cache_dir / "factor"

    @property
    def cache_ic_dir(self) -> Path:
        return self.cache_dir / "ic"

    @property
    def cache_universe_dir(self) -> Path:
        return self.cache_dir / "universe"

    @property
    def backtest_dir(self) -> Path:
        return self.root_dir / "backtest"

    @property
    def backtest_results_dir(self) -> Path:
        return self.backtest_dir / "results"

    @property
    def backtest_runs_dir(self) -> Path:
        return self.backtest_results_dir / "runs"

    def ensure_dirs(self, dirs: Iterable[Path]) -> None:
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)


APP_CONFIG = Config()

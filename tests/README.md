# tests

当前测试目录按“共享测试”和“未来更偏分支测试”两类理解。当前测试也正在向 `shared / product / trading` 分层演进。

以下目录当前可视为共享测试：

- `tests/data`
- `tests/features`
- `tests/backtest` 中的共享分析部分
- `tests/adapters` 中的共享适配基础能力

以下目录未来更偏分支测试：

- `tests/execution`
- `tests/portfolio`
- `tests/risk`
- `tests/strategies`

当前 `shared smoke/regression suite` 优先覆盖 `data / features / shared backtest analysis / shared adapters`。后续新增基础测试时，应优先判断它属于 `shared` 还是 `branch-specific`。这份分层说明反映的是当前边界方向，不表示现有测试已经完成严格拆分。在后续结构调整前，现有测试文件保持原有位置和逻辑不变。

## 临时目录策略

为避免测试运行时在仓库根目录散落临时目录，pytest 统一采用以下策略：

- `--basetemp=.tmp/pytest`
- `cache_dir=.tmp/pytest_cache`

这意味着：

- 测试临时工作目录应优先收敛到 `.tmp/pytest`
- pytest 自身缓存应优先收敛到 `.tmp/pytest_cache`
- 业务缓存仍应放在 `data/cache`
- 正式运行记录仍应放在 `logs/run_tracker`

以下根目录临时物通常可以视为测试残留，而不是业务数据：

- `.pytest_tmp`
- `.pytest_tmp_*` 或 `.pytest_tmp_local*`
- `pytest-cache-files-*`
- `pytest_temp_runtracker_*`
- `tmp*`

如果这些目录不再被进程占用，一般可以直接清理。清理前只需要确认两点：

- 当前没有正在运行的 `pytest` 或 Python 测试进程
- 目录下不包含你手动放入的文件

# tests

当前测试目录按“共享测试”和“未来更偏分支测试”两类理解。

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

这份分层说明反映的是当前边界方向，不表示现有测试已经完成严格拆分。
在后续结构调整前，现有测试文件保持原有位置和逻辑不变。

# Shared Regression Test Strategy

## Purpose

本文档用于定义当前仓库中的 `shared regression tests` 边界。

当前目标不是追求高覆盖率，也不是重写现有测试体系，而是先固定一套最小、稳定、可快速执行的 `shared smoke suite`，作为 shared 主干的基础回归入口。

## Current Test Baseline

当前 shared 测试基础主要集中在以下几类：

- `tests/data`
- `tests/pipelines`
- `tests/utils`
- `tests/backtest`

其中已经形成较稳定基础的方向包括：

- analysis cache / shared data path
- shared application / pipeline 轻量主链
- metadata / run tracker
- shared backtest analysis loop

## Shared Smoke Suite

`shared smoke suite` 应满足以下特点：

- 小而稳
- 快速执行
- 依赖少
- 不强依赖本地缓存状态
- 失败后易定位

当前固定纳入 shared smoke baseline 的最小测试集合为：

- `tests/data/test_analysis_cache.py`
  - 覆盖 analysis cache round-trip、`DataService` 默认路径与 `UniverseProvider` 缓存行为。
- `tests/data/test_data_app.py`
  - 覆盖 shared data application 层的结构化结果输出与轻量编排。
- `tests/data/test_loaders.py`
  - 覆盖 panel loader 拼装与 universe loader 的最小有效读取路径。
- `tests/data/test_processing.py`
  - 覆盖价格/基本面对齐与 future return 计算这两条最小 processing 主链。
- `tests/pipelines/test_data_pipeline.py`
  - 覆盖 data pipeline 的包装行为与 run record 附着。
- `tests/pipelines/test_factor_pipeline.py`
  - 覆盖 factor pipeline 对 shared application 结果的包装与 run record 附着。
- `tests/pipelines/test_ic_pipeline.py`
  - 覆盖 IC pipeline 对 shared application 结果的包装与 run record 附着。
- `tests/utils/test_result_metadata.py`
  - 覆盖共享 metadata helper 的稳定输出。
- `tests/utils/test_run_tracker.py`
  - 覆盖 run tracker 生命周期与 factor / ic pipeline 的 run record 附着行为。
- `tests/backtest/test_backtest_engine.py`
  - 覆盖 shared backtest analysis loop 的最小闭环，并验证 backtest 主路径通过共享分析输入接口取数。

这组 smoke baseline 当前已能覆盖：

- shared data/cache path
- loader / processing 最小有效链路
- factor / ic / data pipeline 主链包装层
- metadata / run tracker
- shared backtest analysis loop

## Execution Entry

当前将以下命令固定为 shared smoke suite 的统一执行入口：

```bash
python -m pytest --basetemp D:\quant_system_327\tmp_pytest_smoke tests/data/test_analysis_cache.py tests/data/test_data_app.py tests/data/test_loaders.py tests/data/test_processing.py tests/pipelines/test_data_pipeline.py tests/pipelines/test_factor_pipeline.py tests/pipelines/test_ic_pipeline.py tests/utils/test_result_metadata.py tests/utils/test_run_tracker.py tests/backtest/test_backtest_engine.py
```

这条命令应作为 shared 主干最小回归入口使用。后续扩展 shared regression scope 时，应先保证这条 smoke 命令持续稳定。

## Shared Regression Scope

`shared regression scope` 可以在 `shared smoke suite` 基础上继续扩展，但应优先围绕以下路径推进：

- loader 正常读取路径
- panel 拼装与对齐稳定性
- cache key 与 cache round-trip 稳定性
- `DataService` 核心共享接口稳定性
- 日期扩展 / lookback / buffer 规则稳定性
- shared backtest analysis 闭环稳定性

也就是说：

- `smoke suite` 负责最小可用性验证
- `regression scope` 负责在此基础上逐步补强 shared 主干回归保护

## Out-of-Scope Test Areas

当前以下测试区域暂不纳入 `shared suite`：

- execution-specific tests
- portfolio-specific tests
- risk-specific tests
- strategy-specific tests
- product-only tests

对应到当前仓库目录，主要包括：

- `tests/execution`
- `tests/portfolio`
- `tests/risk`
- `tests/strategies`
- 未来只服务于 product / trading 分支的测试

## Migration Principles

后续如继续推进 shared regression 建设，应遵循以下原则：

1. 先固定 `shared smoke suite`，再逐步扩展 `shared regression scope`。
2. 优先覆盖 shared 主干最核心、最稳定、最容易退化的路径。
3. 不把 branch-specific 测试提前混入 shared suite。
4. 新增 shared regression 测试时，优先保持测试小、稳、快。
5. 对当前仍为空壳或预留目录的测试区，先补最小有效测试，再考虑纳入 shared suite。

## Compatibility Notes

当前 shared tests 仍处在逐步成型阶段，而不是完整成熟体系。

因此当前阶段的重点不是“做大”，而是先把 shared baseline 做稳。

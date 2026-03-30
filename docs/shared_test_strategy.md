# Shared Regression Test Strategy

## Purpose

本文档用于定义当前仓库中 `shared regression tests` 的策略边界。

当前目标不是提升全面测试覆盖率，也不是重写现有测试框架。
本阶段的重点是：

1. 基于当前仓库现状识别共享主干已有的测试基础；
2. 定义一组最小且稳定的 `shared smoke suite`；
3. 明确哪些测试当前应纳入 shared regression scope，哪些暂时不纳入。

## Current Test Baseline

结合当前测试目录现状，shared tests 当前主要以以下几类为核心：

- `data`
- `features`
- shared backtest analysis capability
- shared adapters capability

其中现状并不完全均衡：

- `tests/data` 当前已经有一部分真实有效测试；
- `tests/backtest` 当前已有最小回测闭环测试，可视为 shared backtest analysis capability 的基础；
- `tests/features` 当前仍较轻；
- `tests/adapters` 方向正确，但当前基础仍较薄。

因此，shared regression 的建设应以“已有基础 + 少量关键补位”为主，而不是大规模扩张。

## Shared Smoke Suite

`shared smoke suite` 应小而稳、快速执行。

它的目标不是覆盖所有边界情况，而是优先验证共享主干是否仍然可用。

当前最适合纳入 `shared smoke suite` 的范围包括：

- loader read path
- panel assembly / alignment correctness
- analysis cache stability
- `DataService` shared interface stability
- basic backtest engine integration used by shared analysis path

这一层测试应尽量满足：

- 运行快
- 依赖少
- 输出稳定
- 问题定位直接

## Shared Regression Scope

`shared regression scope` 可以在 `smoke suite` 基础上逐步扩展。

建议优先围绕以下方向逐步补齐：

- loader 正常读数据
- panel 拼装与对齐稳定
- cache key 与 cache round-trip 稳定
- `DataService` 核心接口返回结构稳定
- 日期扩展 / lookback / buffer 逻辑稳定
- shared backtest analysis 闭环稳定
- shared adapters 最小兼容能力稳定

也就是说：

- `smoke suite` 负责最小可用性验证；
- `regression scope` 负责在此基础上逐步扩展共享主干回归保护面。

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
- 未来只服务 signal / explain / content / daily product 的测试

这些测试当前不应并入 `shared regression suite`，原因是：

- 它们更强依赖 product / trading 上下文；
- 它们的演进节奏不同于共享主干；
- 如果过早混入 shared suite，会让共享回归测试变得不稳定、边界不清晰。

## Migration Principles

后续如果推进 shared regression 建设，应遵循以下原则：

1. 先定义 shared smoke suite，再逐步扩 shared regression scope。
2. 优先覆盖共享主干最核心、最稳定、最容易退化的路径。
3. 不把 branch-specific 测试提前塞进 shared suite。
4. 新增 shared regression 测试时，优先保持测试小、稳定、可快速执行。
5. 对当前仍是空壳或预留目录的测试区，应先补最小有效测试，再考虑纳入 shared suite。

## Compatibility Notes

当前 shared tests 仍处于“逐步成型”阶段，而不是完整稳定体系。

因此当前阶段需要接受以下兼容事实：

- `tests/data` 是现阶段最重要的 shared test 基础；
- `tests/backtest` 只纳入 shared backtest analysis capability；
- `tests/features` 和 `tests/adapters` 当前仍需逐步补强；
- `execution / portfolio / risk / strategies / product-only tests` 暂不纳入 shared suite。

当前 shared regression 的目标不是做大，而是先做稳。

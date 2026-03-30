# Branch Split Checklist

## Purpose

本文档用于定义当前仓库在正式切出 `shared` 分支与 `trading` 分支之前的执行清单。

目标不是立刻做目录迁移或代码复制，而是先把：

- 哪些目录当前可视为 `shared-owned`
- 哪些目录当前可视为 `trading-owned`
- 哪些目录仍属于 `boundary-controlled`
- 哪些旧路径需要冻结新增
- 后续新增代码应优先落到哪里

这些问题固定下来。

本文档强调的是“现在就能执行的切割前清单”，不是最终分支结构蓝图。

## Current Readiness

基于当前仓库现状，已经具备以下基础：

- `commands -> pipelines -> application/shared` 主链路骨架已初步形成；
- `result metadata`、`run tracker`、`exceptions` 已开始做横向统一；
- `adapters/shared` 与 `adapters/trading` 的目录骨架与最小 mapping 已建立；
- `shared foundation` 与 `boundary-controlled` 的文档边界已较明确。

这意味着仓库已经进入“可以准备切分支”的阶段，但仍不建议在缺少目录拥有权和新增代码落点规则时直接切分支。

## Shared-Owned

以下目录当前建议视为 `shared-owned`：

- `data/`
- `features/`
- `application/shared/`
- `pipelines/`
- `utils/result_metadata.py`
- `utils/run_tracker.py`
- `exceptions/`
- `infra/config` 中的 shared/base 方向
- `infra/logging`
- `infra/monitoring`
- `docs/` 中的 shared boundary / contracts / strategy 文档
- `tests/data`
- `tests/utils`
- `tests/backtest` 中的 shared analysis 闭环相关测试

这些目录当前已经开始承担共享分析主链路、共享治理能力或共享契约说明的职责，更适合作为未来 `shared` 分支的稳定地基。

## Trading-Owned

以下目录当前建议视为 `trading-owned`：

- `adapters/broker/`
- `adapters/trading/`
- `execution/`
- `portfolio/`
- `risk/`
- `live/`
- `storage/trading_system/`
- `infra/config/trading/`

这些目录当前明显偏向交易运行域、执行域或实盘环境绑定域，不适合作为共享主干长期承诺给未来 `shared` 分支。

## Boundary-Controlled

以下目录当前建议继续保持 `boundary-controlled` 状态：

- `backtest/`
- `models/alpha/`
- `adapters/local/`
- `adapters/joinquant/`
- `adapters/shared/`
- `strategies/`
- `scripts/commands/`
- `run.py`

这些目录当前仍同时带有共享分析能力与强场景语义，短期内不适合直接归边到 `shared-owned` 或 `trading-owned`。

当前策略应为：

- 允许受控复用；
- 优先共享稳定接口和最小能力；
- 暂不承诺内部实现会长期不分化；
- 在后续 1 到 2 轮收口后再决定是否进一步归边。

## Freeze Old Path

以下旧路径当前建议进入“冻结新增”状态：

- `scripts/commands/*.py`
- `data/services/data_service.py` 中新增场景接口
- `adapters/local`
- `adapters/joinquant`
- `adapters/broker`
- 根层散落新增 helper
- 根层散落新增运行记录 / metadata / 异常处理逻辑

这里的“冻结新增”指的是：

- 可以继续维护；
- 可以继续修 bug；
- 可以做必要兼容；
- 但不应继续作为新增能力的首选落点。

## New Code Placement Rules

从当前阶段开始，新增代码建议遵循以下落点规则。

### Shared Analysis / Shared Orchestration

- 新的分析编排优先进入 `application/shared/`
- 新的 pipeline 入口优先进入 `pipelines/`

### Shared Governance

- 新的结果元信息治理优先进入 `utils/result_metadata.py`
- 新的运行状态治理优先进入 `utils/run_tracker.py`
- 新的异常语义优先进入 `exceptions/`

### Adapter Entry Grouping

- 新的 shared adapter 入口优先进入 `adapters/shared/`
- 新的 trading adapter 入口优先进入 `adapters/trading/`

### Trading Domain

- 新的 trading 侧能力优先进入：
  - `execution/`
  - `portfolio/`
  - `risk/`
  - `live/`

### Tests

- 新的 shared 测试优先进入：
  - `tests/data`
  - `tests/utils`
  - `tests/backtest` 中 shared 范围

- 新的 trading 测试优先进入：
  - `tests/execution`
  - `tests/portfolio`
  - `tests/risk`

## Pre-Split Hard Requirements

在正式切出 `shared` 与 `trading` 分支之前，建议至少再完成以下几项硬条件。

### 1. Stop New Code Backflow

必须确保新增代码不再回流到旧层。

尤其要避免新增能力继续优先落到：

- `scripts/commands/*.py`
- `DataService` 的场景化接口
- 旧 adapters 路径
- 根层散落 helper

### 2. Clarify Ownership of Boundary Modules

以下模块在切分支前应进一步明确拥有权或切割原则：

- `backtest`
- `models/alpha`
- `strategies`

至少需要回答：

- 哪些能力属于 shared analysis
- 哪些能力属于 trading runtime
- 哪些目录暂时继续保留 boundary-controlled

### 3. Strengthen Shared Smoke Baseline

正式切分支前，建议至少保证以下 shared smoke / regression 基线稳定：

- shared data load path
- shared factor pipeline
- shared IC pipeline
- shared backtest analysis loop
- metadata / run tracker / exceptions 基础行为

### 4. Keep Storage / Config Split Actionable

当前配置分层与存储分层已形成文档和目录骨架，切分支前应继续确保：

- 新增 shared 产物优先落到 shared 语义路径
- 新增 trading 产物优先落到 trading 语义路径
- 不再长期混合新增到旧的单一路径语义里

## Immediate Execution Order

当前建议按以下顺序推进：

1. 明确并执行 old path freeze 规则。
2. 把新增代码落点规则作为协作约定固定下来。
3. 给 `backtest`、`models/alpha`、`strategies` 再补一轮 owned vs boundary 说明。
4. 再补 1 到 2 个 shared smoke 测试。
5. 然后正式切 `shared` / `trading` 分支。

## Practical Interpretation

当前仓库状态已经不是“还不能谈切分支”，而是“需要先把切割前约束固定下来”。

如果以上清单大部分被执行，那么：

- `shared` 分支会更接近稳定地基；
- `trading` 分支会更容易在不反向污染共享层的前提下独立演进；
- 后续跨分支合并的成本也会显著降低。

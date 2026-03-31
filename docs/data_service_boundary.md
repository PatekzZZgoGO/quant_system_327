# DataService Shared Boundary

## Purpose

本文档用于定义 `DataService` 在当前仓库中的共享边界。

目标不是一次性重做数据层，而是基于现状明确：

- `DataService` 当前应该承担什么；
- `DataService` 不应该继续吸收什么；
- 后续如果继续演进，应该按照什么原则收敛接口。

## Current Role of DataService

`DataService` 当前是共享数据门面。

它位于命令层、策略层、分析层与底层 `Loader / Provider / Cache` 之间，向上提供统一入口，向下屏蔽底层文件读取、缓存命名、数据拼装和结果持久化细节。

从当前代码现状看，`DataService` 的核心价值主要有两类：

1. 共享原始数据访问。
2. 共享分析输入构造。

同时也要明确：

- `DataService` 不应继续膨胀为产品层/交易层业务编排中心。
- 它不应承接越来越多带有 factor、IC、backtest、execution 等场景语义的上层规则。

## In-Scope Responsibilities

以下职责属于 `DataService` 当前应重点承担的范围：

### Shared Raw Data Access

- 提供统一的数据访问门面。
- 统一装配底层 `Loader / Provider`。
- 为上层屏蔽原始数据读取、缓存读取和基础数据拼装细节。

这类职责的核心是：上层只表达“我要数据”，而不是自己去关心 parquet、缓存路径、底层文件组织方式。

### Shared Analysis Input Access

- 提供分析链路通用的 panel 访问入口。
- 提供分析链路通用的 universe 访问入口。
- 提供 factor / IC 等分析结果缓存的统一读取与保存入口。

这类职责的重点在于“共享分析输入构造”，也就是让上层分析模块拿到稳定输入，而不是自己管理缓存键、缓存目录和统一格式化逻辑。

## Out-of-Scope Responsibilities

以下职责不应继续在 `DataService` 内扩张：

- 产品层分析场景的窗口编排。
- 回测场景的缓冲区间推导。
- IC 场景的 forward return buffer 规则。
- 任何直接依赖未来 product / trading 业务上下文的场景装配。

换句话说：

- `DataService` 可以提供共享输入入口。
- 但它不应继续膨胀为产品层/交易层业务编排中心。

当前代码里，凡是已经直接体现“factor 用什么 lookback”“backtest 需要补多少 buffer”“IC 需要扩多少 horizon 空间”这类规则的部分，都已经开始越过共享数据门面的边界。

## Interface Grouping

### Group A: Shared Raw Data Access

- `get_panel(...)`
  - 语义：输入证券集合和时间区间，输出基础 panel 数据访问结果。
- `get_universe(...)`
  - 语义：输入股票池范围参数，输出基础 universe 数据访问结果。

### Group B: Shared Analysis Input Access

- `get_analysis_panel(...)`
  - 语义：输入分析对象和时间区间，输出统一的分析用 panel。
- `get_analysis_universe(...)`
  - 语义：输入分析范围参数，输出分析链路使用的 `Universe`。
- `load_factor_analysis(...)`
  - 语义：输入 factor 分析任务标识，输出已缓存的 factor 分析结果。
- `save_factor_analysis(...)`
  - 语义：输入 factor 分析任务标识和结果数据，完成统一持久化。
- `load_ic_analysis(...)`
  - 语义：输入 IC 分析任务标识，输出已缓存的 IC 分析结果。
- `save_ic_analysis(...)`
  - 语义：输入 IC 分析任务标识和结果数据，完成统一持久化。

### Group C: Out of Shared Foundation Scope

- `get_analysis_factor_panel(...)`
  - 语义：面向 factor 场景，额外封装 lookback 规则，已带明显产品分析语义。
- `get_analysis_backtest_panel(...)`
  - 语义：面向 backtest 场景，额外封装 execution delay 与 buffer 规则，已带明显业务编排语义。
- `get_analysis_ic_panel(...)`
  - 语义：面向 IC 场景，额外封装 horizon buffer 规则，已带明显分析场景编排语义。
- `get_factor_panel(...)`
  - 语义：旧接口兼容入口，但本质仍属于 factor 场景化接口。
- `get_backtest_panel(...)`
  - 语义：旧接口兼容入口，但本质仍属于 backtest 场景化接口。
- `get_ic_panel(...)`
  - 语义：旧接口兼容入口，但本质仍属于 IC 场景化接口。

## Refactor Principles

后续如果围绕 `DataService` 做边界收敛，应遵循以下原则：

1. 优先保留共享门面价值，不把 `DataService` 打散成到处直连底层 Loader。
2. 优先保留共享原始数据访问和共享分析输入构造，不主动吸收新的业务场景编排。
3. 所有带 factor、IC、backtest、execution 等业务上下文的窗口规则，应优先考虑上移到更靠近 product / trading 的装配层。
4. 兼容旧接口可以短期保留，但不应继续作为新增能力的承载点。
5. `DataService` 的增长方向应是“更稳定的共享访问语义”，而不是“更多场景特例入口”。

## Current Progress

当前围绕 `DataService` 边界的收口已取得阶段性进展：

- `DataService` 中的接口已经按 shared raw data access、shared analysis input access、legacy / boundary warning 三组明确标注。
- `factor` 与 `ic` 的主编排路径已经优先在 application 层组织 lookback / horizon buffer 规则，再调用 `get_analysis_panel(...)` 这类共享入口。
- `backtest` 的主路径已改为在上层组织 execution delay / buffer 规则后调用 `get_analysis_panel(...)`，不再继续依赖 `get_analysis_backtest_panel(...)` 作为主编排入口。

当前仍保留但已明确降级为兼容层的接口包括：

- `get_analysis_factor_panel(...)`
- `get_analysis_backtest_panel(...)`
- `get_analysis_ic_panel(...)`
- `get_factor_panel(...)`
- `get_backtest_panel(...)`
- `get_ic_panel(...)`

这些接口短期内可以继续存在，以承接旧调用或减轻一次性迁移成本；但后续新增编排逻辑不应再继续依赖它们。

简而言之：

- `DataService` 当前是共享数据门面；
- 它应主要负责共享原始数据访问和共享分析输入构造；
- 它不应继续膨胀为产品层/交易层业务编排中心。

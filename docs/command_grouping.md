# Command Grouping Strategy

## Purpose

本文档用于定义当前仓库入口层与命令层的分组策略。

当前目标不是重写 CLI，也不是立即迁移全部现有命令文件。
本阶段的重点是：

1. 识别当前真实存在的入口与命令；
2. 明确哪些命令更适合归入 `shared commands`、`product commands`、`trading commands`；
3. 先把目录边界和迁移方向固定下来，为后续逐步迁移做好结构准备。

当前阶段以“边界清晰化”为主，不追求一次迁移完成。

## Current Entry Points

根据当前仓库代码，主要入口包括：

- `run.py`
  - 当前总 CLI 入口
  - 负责统一注册 `scripts/commands/*.py`

- `scripts/commands/data.py`
  - 当前真实数据命令入口

- `scripts/commands/factor.py`
  - 当前真实因子命令入口

- `scripts/commands/ic.py`
  - 当前真实 IC 命令入口

- `scripts/commands/backtest.py`
  - 当前真实回测命令入口

- `scripts/run_backtest.py`
- `scripts/run_jq.py`
- `scripts/run_live.py`
  - 当前文件已存在，但仍更接近未来业务线专用入口预留文件

## Group Definitions

### `shared commands`

用于承载共享数据、共享分析输入、共享研究入口等命令。

### `product commands`

用于承载信号产品相关的信号输出、解释、内容和产品化导出命令。

### `trading commands`

用于承载回测、组合、交易执行、实盘运行和平台启动器相关命令。

## Shared Commands

当前建议归入 `shared commands` 的命令包括：

- `data`
- `factor`
- `ic`

原因如下：

- `data` 当前主要负责共享数据更新与缓存状态管理；
- `factor` 当前虽然带有选股语义，但仍主要依赖共享数据、共享分析输入和共享缓存；
- `ic` 当前更明显是共享分析入口，而不是交易执行入口。

## Product Commands

当前建议归入 `product commands` 的命令包括未来新增的：

- `signal`
- `explain`
- `content`
- `daily_product`

这些命令当前在仓库里还没有形成稳定主入口文件，但未来如果出现，应优先进入 `product commands`。

原因如下：

- 它们直接面向信号产品输出；
- 它们更贴近解释、内容化、导出和日产品化任务；
- 它们不应继续长期混在共享命令入口中。

## Trading Commands

当前建议归入 `trading commands` 的命令或入口包括：

- `backtest`
- `portfolio`
- `live`
- `jq/live launchers`

具体到当前仓库现状：

- `backtest` 当前可先保留兼容位置，但长期更适合 `trading commands`；
- `run_backtest.py` 更适合作为未来回测场景专用入口；
- `run_jq.py` 更偏平台运行 / 交易启动器；
- `run_live.py` 更偏实盘运行入口。

之所以这样划分，是因为这些入口更直接承载：

- 调仓语义
- 执行语义
- 成本与风控参数
- live / 平台运行上下文

## Migration Principles

后续如果推进命令迁移，应遵循以下原则：

1. 先文档分组，再逐步迁移命令文件。
2. 不因为目录骨架已存在，就立即改动现有注册逻辑。
3. `shared commands` 保持共享分析与共享数据语义，不持续吸收产品解释和交易运行命令。
4. 新增产品化命令优先进入 `product commands`。
5. 新增回测、组合、执行、实盘相关命令优先进入 `trading commands`。

## Compatibility Notes

当前阶段仍保持以下兼容事实：

- `run.py` 当前仍作为统一入口；
- `scripts/commands/*.py` 当前仍是实际命令注册位置；
- `backtest` 当前仍可先保留在兼容位置；
- `scripts/commands/shared`、`scripts/commands/product`、`scripts/commands/trading` 当前仍主要是分组骨架。

同时需要明确：

- `run.py` 当前仍作为统一入口，但后续要支持按业务线分组调度；
- 当前不应强行立即重写自动注册逻辑；
- 后续迁移应优先围绕命令边界清晰化推进，而不是一次性改掉整个 CLI。

# Storage Partitioning Strategy

## Purpose

本文档用于定义当前仓库存储路径的分区策略。

当前目标不是重写现有存储逻辑，也不是一次性迁移全部历史文件。
本阶段的重点是：

1. 识别当前真实存在的存储区、缓存区和结果区；
2. 明确未来应按 `shared storage`、`signal_product storage`、`trading_system storage` 三层分区；
3. 先把目录边界和迁移方向固定下来，为后续逐步迁移做好结构准备。

当前阶段以“边界清晰化”为主，不追求一次迁移完成。

## Current Storage Areas

根据当前仓库代码与目录现状，主要存储区域包括：

- `data/cache/`
  - 当前最明确的分析缓存区
  - 已包含 `panel`、`factor`、`ic`、`universe` 等内容

- `data/storage/`
  - 当前主要是存储抽象实现代码目录
  - 还不是主链路真实数据分区

- `data/snapshots/`
  - 当前存在快照文件
  - 但统一读写协议尚未完全固定

- `features/store/`
  - 当前更像特征/因子相关的预留存储区

- `portfolio/store/`
  - 当前更像持仓与权重相关的预留存储区

- `execution/store/`
  - 当前更像订单与成交相关的预留存储区

- `backtest/results/runs/`
  - 当前明确承载回测运行结果输出

## Partition Definitions

未来建议逐步形成统一的存储分区骨架：

- `storage/shared/`
- `storage/signal_product/`
- `storage/trading_system/`

这三个分区的目标不是立刻替换现有路径，而是先定义清楚未来迁移方向。

### `shared storage`

用于承载共享主干需要复用的稳定数据资产、缓存和快照。

### `signal_product storage`

用于承载信号产品侧的结果、解释、内容和导出产物。

### `trading_system storage`

用于承载交易系统侧的回测、组合、执行与 live 运行相关结果。

## Shared Storage

未来 `shared storage` 建议优先承载以下内容：

- `panels`
- `factors`
- `ic`
- `universe`
- `snapshots`

建议结构示意：

- `storage/shared/panels/`
- `storage/shared/factors/`
- `storage/shared/ic/`
- `storage/shared/universe/`
- `storage/shared/snapshots/`

结合当前仓库现状，这一层主要对应：

- `data/cache/panel`
- `data/cache/factor`
- `data/cache/ic`
- `data/cache/universe`
- `data/snapshots`

需要注意的是，当前 `factor` 和 `ic` 在语义上已经带有分析结果属性，但本阶段先按照你要求的共享优先落位来定义未来骨架，不在此阶段强行改造现有代码路径。

## Signal Product Storage

未来 `signal_product storage` 建议优先承载以下内容：

- `signals`
- `explain`
- `content`
- `exports`

建议结构示意：

- `storage/signal_product/signals/`
- `storage/signal_product/explain/`
- `storage/signal_product/content/`
- `storage/signal_product/exports/`

结合当前仓库现状，这一层更适合逐步吸收：

- 信号输出结果
- 因子解释与内容化产物
- 导出报表
- 未来独立于共享缓存的产品结果文件

当前这类内容还没有在仓库中完全形成稳定独立目录，因此本阶段主要先固定边界，而不是立即迁移。

## Trading System Storage

未来 `trading_system storage` 建议优先承载以下内容：

- `backtests`
- `portfolio`
- `execution`
- `live`

建议结构示意：

- `storage/trading_system/backtests/`
- `storage/trading_system/portfolio/`
- `storage/trading_system/execution/`
- `storage/trading_system/live/`

结合当前仓库现状，这一层更适合逐步吸收：

- `backtest/results/runs`
- `portfolio/store`
- `execution/store`
- `live/`

这些目录当前已经天然带有交易系统或回测系统语义，因此未来整理到 `trading_system storage` 会更清晰。

## Migration Principles

后续如果推进存储分区迁移，应遵循以下原则：

1. 先文档分区，再逐步迁移真实路径。
2. 先迁移边界最清楚的结果目录，不急于改动所有缓存逻辑。
3. 不因为目录已经存在，就默认它已经是稳定的正式分区。
4. 保持共享数据、信号产品结果、交易系统状态三者边界逐步清晰。
5. 对当前还未形成统一写入协议的目录，应先补说明，再决定是否迁移。

## Compatibility Notes

当前仓库已经有一批正在使用的真实路径，包括：

- `data/cache/*`
- `data/snapshots/*`
- `backtest/results/runs/*`
- `portfolio/store/*`
- `execution/store/*`

因此当前阶段不应强行立即切换到 `storage/shared/`、`storage/signal_product/`、`storage/trading_system/`。

兼容性处理原则应当是：

- 保持现有行为不变；
- 保留当前路径继续工作；
- 先把未来分区骨架和边界写清楚；
- 后续按目录、按结果类型、按模块逐步迁移，而不是一次性替换所有读写路径。

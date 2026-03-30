# Shared Foundation Boundary

## Purpose

本文档用于定义当前仓库在“未来产品分支 + 未来交易分支共享地基”目标下的边界草案。

核心目的有三点：

1. 明确哪些目录属于当前阶段的 `shared_foundation`。
2. 明确哪些目录只能以 `boundary_controlled` 方式共享，而不能视为共享主干。
3. 明确哪些目录属于 `branch_owned`，应由未来产品分支或未来交易分支分别演进。

本文档强调的是“当前可执行边界”，不是一次性完成的终局架构设计。

## Classification Rules

### `shared_foundation`

满足以下条件的模块可以进入 `shared_foundation`：

- 同时服务未来产品分支和未来交易分支。
- 抽象相对稳定，短期内不会被某一侧业务快速牵引变形。
- 提供基础能力、公共契约、通用配置或共享文档，而不是具体场景编排。
- 可以被两侧依赖，但不应反向依赖某个分支特有实现。

### `boundary_controlled`

满足以下特征的模块应归入 `boundary_controlled`：

- 两侧都可能使用，但业务语义偏强。
- 共享方式应以接口、协议、输入输出约定、最小可复用能力为主。
- 不能默认允许内部实现被两侧自由穿透复用。
- 后续可以继续拆分，部分能力转入 `shared_foundation`，部分能力下沉到 `branch_owned`。

### `branch_owned`

满足以下特征的模块应归入 `branch_owned`：

- 明显服务于某一条分支的具体目标、运行环境或演进节奏。
- 变化频繁，容易被产品实验或交易执行约束直接拉动。
- 可以依赖共享层，但不应被当作共享主干承诺给另一侧。

## Shared Foundation

当前明确纳入共享主干的范围如下：

- `data`
- `features`
- `infra(config/logging/monitoring)`
- `docs`
- `shared tests`

说明如下：

- `data`：作为共享主干，重点是数据访问约定、数据处理通路、通用数据服务能力，而不是所有缓存和环境产物。
- `features`：作为共享主干，重点是特征/因子流水线、公共计算框架和通用分析支撑。
- `infra(config/logging/monitoring)`：属于最典型的共享基础设施，应优先保持稳定和通用。
- `docs`：共享架构说明、共享边界定义、公共运行约定都应沉淀在文档层。
- `shared tests`：共享主干相关测试应视为共享资产，用于保障公共能力稳定性。

关于 `core` 的单独说明：

- `core` 当前除 `common/config` 相关内容外，大部分仍偏骨架/空壳。
- 因此，`core` 目前不纳入当前共享主干核心承诺。
- 后续若其中部分模块形成稳定抽象，再按实际成熟度吸收到 `shared_foundation`。

## Boundary-Controlled Modules

当前属于条件共享，也就是 `boundary_controlled` 的模块如下：

- `backtest`
- `models/alpha`
- `adapters/local`
- `adapters/joinquant`
- `scripts/commands`
- `strategies`

这些模块的使用原则如下：

- 可以共享，但只能共享稳定边界，不共享全部内部实现自由度。
- 应优先共享接口、输入输出格式、运行约定和可复用组件。
- 若某部分实现明显偏向产品研究或交易运行，应及时从条件共享中收缩出去。

逐项说明：

- `backtest`：可为产品研究与策略验证提供共享能力，但不应成为交易主链路的核心依赖。
- `models/alpha`：可以共享信号生成思想与轻量 Alpha 输出协议，但不应默认共享所有研究实现。
- `adapters/local`：本地模拟和本地运行支撑可跨分支复用，但应控制环境假设扩散。
- `adapters/joinquant`：可作为特定平台接入层条件共享，但不应把平台绑定逻辑上升为共享主干。
- `scripts/commands`：命令编排层可以阶段性共享，但应避免变成所有场景入口的永久聚合点。
- `strategies`：当前可作为条件共享区观察与整理，但长期更可能回到分支自有管理。

## Branch-Owned Modules

当前明确不纳入共享主干，也就是属于 `branch_owned` 的重点模块如下：

- `portfolio`
- `risk`
- `execution`
- `adapters/broker`
- `models/ml`
- `infra/database`

这里需要明确的是：以上模块属于“非共享主干”。

这意味着：

- 它们不是当前阶段的共享主干承诺。
- 即使未来存在局部复用，也应以受控接口方式发生，而不是默认作为共享骨干建设。
- 它们更适合由未来产品分支或未来交易分支按各自目标分别演进。

逐项说明：

- `portfolio`：组合构建、持仓状态和调仓约束高度贴近业务决策，不适合作为当前共享主干。
- `risk`：风控口径虽然需要对齐，但实时约束与研究评估差异很大，不宜直接进入共享主干。
- `execution`：订单与执行链路天然偏交易运行域，不应作为当前共享主干承诺。
- `adapters/broker`：券商接入实现强依赖交易环境，属于交易分支主导范围。
- `models/ml`：机器学习研究资产变化快、实验性强，应避免纳入当前共享主干。
- `infra/database`：数据库落地方案通常受部署形态和运行链路影响，不适合作为当前共享主干一部分。

## Current Practical Notes

当前阶段的实际执行建议如下：

- 共享主干优先围绕 `data`、`features`、`infra(config/logging/monitoring)`、`docs`、`shared tests` 做稳定化整理。
- 条件共享模块先保留边界，不急于完全下沉或完全提升，避免过早承诺错误抽象。
- 非共享主干模块允许未来产品分支和未来交易分支各自形成更贴身的实现。
- `core` 不应在当前阶段被默认视为共享核心；除 `common/config` 相关外，其余部分更适合继续观察成熟度。
- 文档和测试应先于大规模目录重组落地，先把边界说清楚，再做结构迁移。
- 后续如果要进一步推进，可在不改变本原则的前提下，把 `shared tests` 从现有测试目录中显式分层出来。

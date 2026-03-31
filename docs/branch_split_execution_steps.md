# Branch Split Execution Steps

## Purpose

本文档用于把正式切出 `shared` / `trading` 分支之前的执行动作整理为可逐步推进的步骤清单。

重点不是一次性完成目录迁移，也不是立即重写现有结构，而是：

- 先固定边界
- 先冻结旧路径回流
- 先建立 shared 主干可验证基线
- 再在约束明确的前提下切分分支

本文档中的每一步都按以下结构组织：

- `Goal`
- `Scope`
- `Do First`
- `Do Not Do Yet`
- `Exit Criteria`

## Step 1. Freeze Entry Backflow

### Goal

冻结旧入口层继续吸收新能力的趋势，避免在正式切出 `shared` / `trading` 分支之前，新增代码继续回流到旧的命令路径。

### Scope

- `scripts/commands/`
- `run.py`

### Do First

- 明确 `scripts/commands/*.py` 当前仅作为兼容入口层保留。
- 明确 `run.py` 当前仅承担统一入口、注册、分发职责。
- 约定新增业务编排优先落到：
  - `pipelines/`
  - `application/shared/`
- 给现有命令补充归属说明：
  - `data`
  - `factor`
  - `ic`
  - `backtest`

### Do Not Do Yet

- 不立刻重写 CLI 自动注册逻辑。
- 不一次性迁移全部命令文件。
- 不在这一阶段直接引入新的完整多入口 CLI 体系。

### Exit Criteria

- 新增能力不再优先落入 `scripts/commands/*.py`。
- `run.py` 的职责边界被明确限制在入口分发层。
- 现有命令的 shared / boundary / trading 归属说明已固定。

### Current Progress

Status: partially complete

已完成：

- `factor`、`ic`、`backtest` 的业务编排已优先下沉到 `pipelines/`，其中 `factor` 与 `ic` 已进一步下沉到 `application/shared/`。
- `run.py` 已明确为统一入口与分发层。
- 入口层职责说明已补充到 `run.py` 与相关命令文件。

仍未完全完成：

- `data` 命令仍保留较多直接入口逻辑，尚未像 `factor`、`ic`、`backtest` 一样形成清晰的 pipeline/application 下沉。
- `scripts/commands/` 当前主要依赖约定与文档来防止新逻辑回流，尚未形成更强的结构性限制。

结论：

- Step 1 已完成大部分目标，足以支撑继续推进后续步骤。
- 但从“完全解决诉求”的标准看，当前状态更准确地应记为 `partially complete`。

## Step 2. Constrain DataService Boundary

### Goal

把 `DataService` 稳定为 shared data facade，而不是继续膨胀为场景编排中心。

### Scope

- `data/services/data_service.py`

### Do First

- 固定 `DataService` 的三类接口分组：
  - shared raw data access
  - shared analysis input access
  - legacy / boundary warning
- 约定新增 shared 数据能力优先进入前两类接口。
- 把已有 factor / IC / backtest 场景化方法视为兼容层，而不是未来新增能力承载点。
- 明确上层 application 编排负责组织 lookback / buffer / horizon 等场景规则。

### Do Not Do Yet

- 不把 `DataService` 打散回直接访问 loader / provider。
- 不一次性删除旧接口。
- 不继续向 `DataService` 增加 execution / signal / content / trade decision 等强场景接口。

### Exit Criteria

- `DataService` 的共享职责被稳定限定。
- 新需求不再推动它继续场景膨胀。
- shared 分支未来可以直接承接这层 facade，而不引入 trading 反向污染。

## Step 3. Clarify Backtest Ownership

### Goal

明确 `backtest/` 中哪些能力属于 shared analysis，哪些能力属于 trading/runtime 语义，避免切分时整块目录归属失控。

### Scope

- `backtest/`

### Do First

- 盘点 `backtest/` 内现有能力并分为三类：
  - shared analysis capability
  - boundary-controlled capability
  - trading/runtime-specific capability
- 明确哪些结果对象、分析流程、统计口径可被 shared 复用。
- 明确哪些执行、调仓、成本、持仓、延迟语义更适合下沉 trading。
- 补一份 `backtest` owned vs boundary 说明。

### Do Not Do Yet

- 不把整个 `backtest/` 直接整体划归 `shared` 或 `trading`。
- 不在边界未清晰前做大规模目录迁移。
- 不把所有 simulation / execution 细节都承诺为 shared 能力。

### Exit Criteria

- `backtest/` 的 shared / boundary / trading 边界说明清晰。
- 至少能说清楚：
  - 哪些能力保留 boundary-controlled
  - 哪些未来下沉 trading
  - 哪些可以抽到 shared
- 后续切分分支时，`backtest/` 不会继续无边界扩张。

## Step 4. Clarify Research Asset Ownership

### Goal

明确 `models/alpha/` 与 `strategies/` 的共享资产边界，避免研究实现、产品逻辑和交易运行语义混在一起。

### Scope

- `models/alpha/`
- `strategies/`

### Do First

- 定义共享研究资产与分支私有资产的判断标准。
- 盘点 `models/alpha/`：
  - 哪些是共享最小协议或轻量 alpha 能力
  - 哪些已经带产品化或特定业务语义
- 盘点 `strategies/`：
  - 哪些只是研究样例
  - 哪些已明显偏向交易运行或实盘语义
- 先补文档归属说明，不急于移动文件。

### Do Not Do Yet

- 不批量迁移 `models/alpha/` 或 `strategies/`。
- 不把所有 alpha / strategy 默认视为 shared 资产。
- 不把实验性实现过早冻结成 shared 契约。

### Exit Criteria

- `models/alpha/` 与 `strategies/` 的 owned vs boundary 规则明确。
- 已能区分：
  - 共享最小协议
  - 研究实现资产
  - trading/runtime 相关资产
- 分支切出后，不会因为归属不明产生频繁双向复制或反复搬迁。

## Step 5. Stabilize Shared Smoke Baseline

### Goal

在切分支前建立最小 shared regression baseline，保证 `shared` 分支切出后有独立、快速、稳定的回归保护。

### Scope

- `tests/data`
- `tests/utils`
- shared 范围内的 `tests/backtest`
- 相关 shared 主链测试入口

### Do First

- 固定 shared smoke suite 的最小范围。
- 优先覆盖以下路径：
  - shared data load path
  - panel / universe 基础稳定性
  - factor pipeline 主链
  - IC pipeline 主链
  - metadata / run tracker / exceptions
  - shared backtest analysis loop
- 尽量保证这套测试：
  - 执行快
  - 依赖少
  - 不强依赖本地缓存状态
  - 失败后易定位

### Do Not Do Yet

- 不追求一次性补齐高覆盖率。
- 不把 execution / portfolio / risk / strategy-specific 测试混入 shared suite。
- 不引入过重、过慢、强依赖本地数据状态的测试集合。

### Exit Criteria

- shared 分支具备最小可运行回归基线。
- shared 改动可被快速验证。
- trading 分支可以在 shared baseline 之上独立扩展自身测试。

## Step 6. Final Pre-Split Review

### Goal

在正式切 `shared` / `trading` 分支前，对前 5 步的边界约束做一次统一确认，避免带着未收口的问题直接切分。

### Scope

- entry layer
- DataService boundary
- backtest ownership
- research asset ownership
- shared smoke baseline

### Do First

- 逐项确认 Step 1 到 Step 5 的 exit criteria 是否满足。
- 确认新增代码落点规则已经实际生效。
- 确认 shared / boundary / trading 的分类不再停留在口头约定。
- 确认 shared smoke baseline 已可稳定作为切分后验证基础。

### Do Not Do Yet

- 不在 exit criteria 未满足时仓促切分支。
- 不把“已有目录骨架”误判为“已经完成边界收口”。

### Exit Criteria

- Step 1 到 Step 5 已基本完成。
- 可以在不大规模重写、不一次性搬空目录的前提下正式切出 `shared` / `trading` 分支。
- 切分之后两条分支都能在明确边界下继续演进。

## Split Readiness Gate

当以下条件全部满足时，可以认为仓库已经达到正式切 `shared` / `trading` 分支的最低门槛：

- 新代码不再回流旧命令层。
- `DataService` 不再继续场景膨胀。
- `backtest/` 的 shared / boundary / trading 边界已写清楚。
- `models/alpha/` 与 `strategies/` 的归属原则已写清楚。
- shared smoke suite 可以稳定执行。

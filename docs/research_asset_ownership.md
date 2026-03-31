# Research Asset Ownership

## Purpose

本文档用于明确 `models/alpha/` 与 `strategies/` 当前的 ownership 边界。

目标不是立刻迁移目录，也不是把所有研究资产统一承诺为 `shared`，而是先建立一套可复用的判断标准，回答三件事：

- 哪些能力更接近 `shared minimal alpha capability`
- 哪些能力当前更适合作为 `research implementation assets`
- 哪些能力一旦长出执行、账户、事件调度或风控语义，就应转入 `trading/runtime-specific capability`

## Directory-Level Classification

### `models/alpha/`

当前建议归类为：

- `shared minimal alpha capability` 候选目录

原因是：

- 当前文件主要体现轻量 alpha 配方或权重定义
- 没有明显的订单、账户、执行、风控、事件循环等 trading/runtime 语义
- 更接近共享研究最小协议，而不是完整策略实现

但当前阶段仍不建议把整个 `models/alpha/` 直接等同于稳定 shared 主干，因为后续仍可能引入实验性、产品化或特定业务语义更重的模型实现。

### `strategies/`

当前建议归类为：

- `research implementation assets`

原因是：

- 目录按具体策略组织，而不是按共享协议组织
- 每个策略目录都带有局部 `config.yaml`
- 当前更像研究方案、研究样例和策略实现位，而不是共享最小 alpha 契约位

## Ownership Categories

### Shared Minimal Alpha Capability

这类能力通常只承载：

- 轻量 alpha 配方
- 因子权重定义
- 最小模型接口

它们不应直接绑定：

- 具体策略目录
- 局部运行配置
- 账户 / 订单 / 执行 / 风控
- live 调度或事件驱动语义

### Research Implementation Assets

这类能力通常代表：

- 具体研究策略
- 研究样例
- 局部实验实现
- 面向某个策略目录的参数配置

它们可以复用 `models/alpha/` 中的轻量能力，但自身不应直接被承诺为 shared 主干能力。

### Trading/Runtime-Specific Capability

这类能力一旦出现，通常说明它已经不再只是研究资产，而应转向 trading/runtime 侧。典型信号包括：

- broker / account / order / execution 依赖
- live scheduler / event loop / runtime orchestration
- 实盘风控、持仓约束、成交约束
- 明显面向交易运行而不是研究验证的目录与接口

当前在 `models/alpha/` 与 `strategies/` 这两个目录内，这类资产还不明显，因此不建议在当前阶段过度预判。

## File-by-File Ownership

### Shared Minimal Alpha Capability

- `models/alpha/simple_alpha.py`
  - 当前只提供轻量的因子权重定义与 `TOP_N` 参数
  - 不带明显产品化上下文或 trading/runtime 语义
- `models/alpha/momentum_only.py`
  - 当前只提供单因子 momentum 权重定义
  - 语义较轻，适合作为共享最小 alpha 能力候选
- `models/alpha/low_vol.py`
  - 当前只提供 low volatility 权重定义
  - 仍属于轻量 alpha 配方，而不是完整策略实现

### Research Implementation Assets

- `strategies/mean_reversion/strategy.py`
  - 当前代表均值回归策略实现位
  - 即使实现仍较轻，也应优先视为研究实现资产
- `strategies/momentum/strategy.py`
  - 当前代表动量策略实现位
  - 目录与命名都更接近策略研究实现，而不是共享最小模型定义
- `strategies/multi_factor/strategy.py`
  - 当前代表多因子策略实现位
  - 即使后续复用 `models/alpha/` 中的轻量能力，也不应直接等同于 shared 资产
- `strategies/mean_reversion/config.yaml`
  - 当前承载均值回归策略的局部研究参数
- `strategies/momentum/config.yaml`
  - 当前承载动量策略的局部研究参数
- `strategies/multi_factor/config.yaml`
  - 当前承载多因子策略的局部研究参数

### Trading/Runtime-Specific Capability

当前在 `models/alpha/` 与 `strategies/` 这两个目录里，还没有特别明确的 trading/runtime-specific 文件。

原因是：

- `models/alpha/` 目前主要是轻量权重定义
- `strategies/` 目前主要是策略目录骨架与局部配置
- 还没有明显耦合 broker、account、order、execution、live event 或实盘风控语义的实现文件

## New Asset Placement Rules

后续新增研究资产时，应优先按下面的规则判断落点：

### 新增到 `models/alpha/` 的前提

一个新文件只有在满足以下条件时，才应优先进入 `models/alpha/`：

- 它提供的是轻量 alpha 配方或最小模型接口
- 不依赖具体策略目录
- 不依赖局部运行配置
- 不带执行、账户、订单、风控或 live runtime 语义

如果一个模型实现已经开始绑定：

- 某个产品策略
- 某类场景专属参数
- 更重的研究实验流程

那么它应优先留在研究实现侧，而不是直接进入 shared minimal alpha capability。

### 新增到 `strategies/` 的前提

一个新文件如果主要承载以下内容，应优先进入 `strategies/`：

- 策略样例
- 研究实现
- 面向单个策略目录的局部配置
- 组合某些 alpha / signal / ranking 规则的研究逻辑

只要它还停留在研究与验证语义，而没有长出 trading/runtime 依赖，就仍应优先保留在 `strategies/`。

### 何时从 `strategies/` 转为 `trading/runtime-specific`

如果某个策略目录或文件开始长出以下信号，就不应继续只视为 research implementation：

- 明确依赖 broker / account / order / execution
- 引入 live runtime / scheduler / event loop
- 持仓、风控、成交限制成为核心职责
- 文件职责明显从“研究验证”转向“交易运行”

此时应将其视为 `trading/runtime-specific capability` 候选，而不是继续默认留在 Step 4 的研究资产边界内。

## Current Judgement

当前阶段对 `models/alpha/` 与 `strategies/` 的判断可以概括为：

- `models/alpha/` 中现有文件更接近 `shared minimal alpha capability`
- `strategies/` 当前整体更接近 `research implementation assets`
- 当前尚不需要把现有文件大规模判定为 `trading/runtime-specific`

## Do Not Do Yet

- 不批量迁移 `models/alpha/` 到 shared 主干目录
- 不批量迁移 `strategies/` 到 trading/runtime 目录
- 不把所有 alpha 文件默认承诺为稳定 shared 契约
- 不把所有 strategy 目录默认解释为 trading/runtime-specific
- 不在当前实现仍较轻、语义仍未展开前，过早冻结研究资产边界

## Exit Criteria for Step 4

围绕 research asset ownership 的说明至少应达到以下状态：

- 可以明确区分 `shared minimal alpha capability` 与 `research implementation assets`
- 可以说明哪些资产当前仍不应直接视为 `trading/runtime-specific`
- 后续新资产加入时，有明确判断标准决定它应进入 alpha、strategy 还是 trading/runtime 范围
- 分支切出后，不会因为归属不清导致频繁双向复制或反复迁移

## Summary

简而言之：

- `models/alpha/` 当前更接近共享最小 alpha 能力候选区
- `strategies/` 当前更接近研究实现资产区
- 这两个目录里目前还没有特别明确的 trading/runtime-specific 主体
- 当前阶段已不仅是“盘点现状”，而是已经固定了一套后续新增研究资产也可复用的落点判断标准

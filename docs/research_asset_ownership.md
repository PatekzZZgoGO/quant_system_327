# Research Asset Ownership

## Purpose

本文档用于明确 `models/alpha/` 与 `strategies/` 当前的 ownership 边界。

目标不是立刻迁移目录，也不是把所有研究资产统一承诺为 `shared`，而是基于当前代码现状先回答三件事：

- 哪些能力更接近 `shared minimal alpha capability`
- 哪些能力当前更适合作为 `research implementation assets`
- 哪些能力已经明显带有 `trading/runtime-specific` 语义

这份说明的重点是先为 Step 4 建立稳定判断标准，避免后续在边界未明确前发生频繁双向复制、反复搬迁或过早冻结共享契约。

## Directory-Level Classification

### `models/alpha/`

当前建议归类为：

- `shared minimal alpha capability` 候选目录

原因是：

- 当前文件主要体现轻量的 alpha 配方或权重定义；
- 没有明显的订单、账户、执行、风控、事件循环等交易运行时语义；
- 更接近共享研究最小协议，而不是完整策略实现。

但当前阶段仍不建议把整个 `models/alpha/` 直接等同于稳定共享主干，因为后续仍可能继续引入实验性、产品化或特定业务语义的模型实现。

### `strategies/`

当前建议归类为：

- `research implementation assets`

原因是：

- 目录按具体策略组织，而不是按共享协议组织；
- 每个策略目录都已有局部 `config.yaml`，天然带有研究场景和局部参数语义；
- 当前更像研究方案与策略实现位，而不是共享最小 alpha 契约位。

## Ownership Categories

### Shared Minimal Alpha Capability

这类能力通常只承载轻量 alpha 配方、权重定义或最小模型接口，不直接绑定具体策略目录、局部运行配置或交易运行时语义。

### Research Implementation Assets

这类能力通常代表具体研究策略、研究样例或局部实验实现。

它们可能会复用共享 alpha 配方，但自身不应直接承诺为共享主干能力。

### Trading/Runtime-Specific Capability

这类能力通常已经带有执行、账户、订单、事件调度、实盘运行、风控约束等明显 trading/runtime 语义。

当前在 `models/alpha/` 与 `strategies/` 这两个目录内，这类资产还不明显，因此不建议在当前阶段过度预判。

## File-by-File Ownership

### Shared Minimal Alpha Capability

- `models/alpha/simple_alpha.py`
  - 当前只提供轻量的因子权重定义与 `TOP_N` 参数。
  - 不带明显产品化上下文或交易运行时语义。
  - 当前更接近共享最小 alpha 配方。

- `models/alpha/momentum_only.py`
  - 当前只提供单因子 momentum 权重定义。
  - 语义较轻，适合作为共享最小 alpha 能力候选。

- `models/alpha/low_vol.py`
  - 当前只提供 low volatility 权重定义。
  - 仍属于轻量 alpha 配方，而不是完整策略实现。

### Research Implementation Assets

- `strategies/mean_reversion/strategy.py`
  - 当前代表均值回归策略实现位。
  - 即使实现仍较轻，也应优先视为研究实现资产，而不是共享 alpha 契约。

- `strategies/momentum/strategy.py`
  - 当前代表动量策略实现位。
  - 目录与命名语义都更接近策略研究实现，而不是共享最小模型定义。

- `strategies/multi_factor/strategy.py`
  - 当前代表多因子策略实现位。
  - 即使后续会复用 `models/alpha/` 中的轻量能力，也不应直接等同于共享主干资产。

- `strategies/mean_reversion/config.yaml`
  - 当前承载均值回归策略的局部研究参数。
  - 应视为策略局部配置，而不是共享协议的一部分。

- `strategies/momentum/config.yaml`
  - 当前承载动量策略的局部研究参数。
  - 应视为研究实现资产的一部分。

- `strategies/multi_factor/config.yaml`
  - 当前承载多因子策略的局部研究参数。
  - 应视为研究实现资产的一部分。

### Trading/Runtime-Specific Capability

当前在 `models/alpha/` 与 `strategies/` 这两个目录里，还没有特别明确的 trading/runtime-specific 文件。

原因是：

- `models/alpha/` 下目前主要是轻量权重定义；
- `strategies/` 下目前主要是策略目录骨架与局部配置；
- 还没有看到明显耦合 broker、account、order、execution、live event、实盘风控等语义的实现文件。

因此，当前阶段不建议在这两个目录内强行扩大 trading/runtime-specific 资产范围。

## Current Judgement

当前阶段对 `models/alpha/` 与 `strategies/` 的判断可以概括为：

- `models/alpha/` 中现有文件更接近 shared minimal alpha capability
- `strategies/` 当前整体更接近 research implementation assets
- 当前尚不需要把现有文件大规模判定为 trading/runtime-specific

## Do Not Do Yet

- 不批量迁移 `models/alpha/` 到共享主干目录。
- 不批量迁移 `strategies/` 到 trading/runtime 目录。
- 不把所有 alpha 文件默认承诺为稳定共享契约。
- 不把所有 strategy 目录默认解释为 trading/runtime-specific。
- 不在当前实现仍较轻、语义仍未展开前，过早冻结研究资产边界。

## Exit Criteria for Step 4

围绕 research asset ownership 的说明至少应达到以下状态：

- 可以明确区分 shared minimal alpha capability 与 research implementation assets
- 可以说明哪些资产当前仍不应直接视为 trading/runtime-specific
- 后续新资产加入时，有明确判断标准决定它应进入 alpha、strategy 还是 trading/runtime 范围
- 分支切出后，不会因为归属不清导致频繁双向复制或反复搬迁

## Summary

简而言之：

- `models/alpha/` 当前更接近共享最小 alpha 能力候选区
- `strategies/` 当前更接近研究实现资产区
- 这两个目录里目前还没有特别明确的 trading/runtime-specific 主体
- 当前阶段先固定 ownership 判断标准，比仓促迁移目录更重要

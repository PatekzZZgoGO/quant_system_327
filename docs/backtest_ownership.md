# Backtest Ownership

## Purpose

本文档用于明确 `backtest/` 目录当前的 ownership 边界。

目标不是立刻把整个 `backtest/` 目录一次性拆到 `shared` 或 `trading`，而是基于当前代码现状先回答三件事：

- 哪些能力更接近 `shared analysis capability`
- 哪些能力当前更适合保留为 `boundary-controlled`
- 哪些能力已经明显带有 `trading/runtime-specific` 语义

这份说明的重点是为后续分支切分和目录收口提供稳定判断依据，避免在边界未清晰前做整块目录迁移。

## Directory-Level Classification

当前对 `backtest/` 的整体判断仍维持为：

- `Classification: boundary-controlled`

原因是：

- 它直接服务研究验证与回测分析；
- 它复用共享数据与共享因子能力；
- 同时又承接了执行延迟、调仓、持仓、交易成本、PnL 等明显偏运行时的语义。

因此，当前阶段不应把整个 `backtest/` 直接整体划归 `shared` 或 `trading`，而应在目录内部进一步拆分 ownership。

## Ownership Categories

### Shared Analysis Capability

这类能力更接近研究分析结果汇总、统计口径和共享分析输出，不直接承载执行状态机或交易运行细节。

### Boundary-Controlled Capability

这类能力当前位于 `backtest/` 的受控边界内，负责把共享分析输入与回测链路串起来。

它们通常既包含研究验证语义，也夹带部分运行时语义，因此不适合在当前阶段简单归并到 `shared` 或 `trading` 任一侧。

### Trading/Runtime-Specific Capability

这类能力已经明显承载执行、调仓、持仓、成本、运行状态等语义。

它们与未来 trading/runtime 边界更接近，应在后续切分中优先考虑下沉到 trading 相关范围，而不是继续作为 shared 主干能力。

## File-by-File Ownership

### Shared Analysis Capability

- `backtest/analysis/result_analyzer.py`
  - 负责将 `daily_pnl` 与 `trades` 汇总为收益、波动、Sharpe、回撤、换手等结果指标。
  - 当前更接近共享分析结果汇总器，而不是交易运行时组件。
  - 后续若需要抽 shared 分析能力，这是当前最明确的候选文件。

### Boundary-Controlled Capability

- `backtest/engine/backtest_engine.py`
  - 当前是回测主链的混合编排点。
  - 它串接共享分析输入、因子计算、信号生成、调仓执行、PnL 统计与结果汇总。
  - 由于同时混合了 shared analysis 与 trading/runtime 语义，当前更适合保留为 boundary-controlled，而不是直接归并到任一侧。

- `backtest/simulation/signal_generator.py`
  - 负责把单日 snapshot 与 weights 转为 target positions。
  - 它已经带有“从研究分数转为调仓目标”的桥接语义。
  - 当前更适合作为 boundary-controlled 组件保留。

- `backtest/simulation/pnl_calculator.py`
  - 负责根据持仓和价格区间计算组合收益。
  - 它与持仓状态、价格区间和覆盖权重密切相关，既有分析口径，也带运行时上下文。
  - 当前先归为 boundary-controlled，更稳妥。

- `backtest/results/runs/`
  - 当前是兼容性的回测结果输出目录。
  - 这里承接历史输出路径，但不应被误判为 shared 主干目录。
  - 当前建议继续按 boundary-controlled output path 处理。

### Trading/Runtime-Specific Capability

- `backtest/simulation/execution_model.py`
  - 负责估算 turnover、commission、slippage，并输出 execution result。
  - 这是典型的交易执行与成本语义，更接近 trading/runtime-specific。

- `backtest/simulation/portfolio_manager.py`
  - 负责维护 positions、pending rebalances 和调仓执行结果。
  - 这是典型的持仓与调仓状态机语义，更接近 trading/runtime-specific。

## Current Judgement

当前阶段对 `backtest/` 的判断可以概括为：

- 整体目录仍保持 `boundary-controlled`
- `analysis/result_analyzer.py` 是最明确的 shared analysis 候选
- `simulation/execution_model.py` 与 `simulation/portfolio_manager.py` 是最明确的 trading/runtime 候选
- `engine/backtest_engine.py`、`simulation/signal_generator.py`、`simulation/pnl_calculator.py` 当前仍属于过渡期边界组件

## Do Not Do Yet

- 不把整个 `backtest/` 一次性整体迁到 `shared`。
- 不把整个 `backtest/` 一次性整体迁到 `trading`。
- 不在尚未进一步拆出 engine / simulation 边界前，直接承诺所有回测能力都属于 shared。
- 不在尚未稳定 trading/runtime 目录结构前，仓促迁移 execution / portfolio / cost 相关组件。

## Exit Criteria for Step 3

围绕 `backtest/` ownership 的说明至少应达到以下状态：

- 可以明确说清 `backtest/` 内哪些是 shared analysis capability
- 可以明确说清哪些当前保留为 boundary-controlled
- 可以明确说清哪些未来优先下沉 trading/runtime
- 后续切分 `shared` / `trading` 分支时，不再以整个 `backtest/` 作为单一整体处理

## Summary

简而言之：

- `backtest/` 当前整体仍应视为 `boundary-controlled`
- 其中 `result_analyzer.py` 是最明确的 shared analysis 候选
- `execution_model.py` 与 `portfolio_manager.py` 是最明确的 trading/runtime-specific 候选
- 其余主链文件当前先保留在受控边界内，待后续边界进一步稳定后再继续下沉

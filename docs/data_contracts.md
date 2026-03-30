# Core Data Contracts

## Purpose

本文档用于定义当前仓库主链路中的核心数据对象契约。

当前目标不是引入新的 schema 框架，也不是把所有 `DataFrame` 重写成 dataclass / pydantic / pandera。
本阶段只做三件事：

1. 识别当前主链路中真实存在的数据对象；
2. 为这些对象定义最小共享契约；
3. 明确哪些字段当前纳入共享范围，哪些字段暂时不纳入。

本文档中的结论全部基于当前仓库代码中的真实流转关系，而不是理想化架构设计。

## Contract Design Principles

当前契约设计遵循以下原则：

1. 优先定义“最小稳定字段”，不追求一次性穷尽所有列。
2. 优先覆盖多条主链路共同消费的对象和字段。
3. 输入契约优先于展示契约，运行主链路优先于导出视图。
4. 不把 product 解释字段和 trading 执行字段提前写入共享契约。
5. 若对象当前结构尚未完全稳定，则记录“最小建议结构”，而不是伪造完整 schema。

## UniverseFrame

### 定义

`UniverseFrame` 当前在仓库里并不是真正的 `DataFrame`。
真实流动的是 `symbols: list[str]`，并通过 `Universe(symbols)` 领域对象在主链路中传递。

### 最小必需字段

- `symbols`

### 推荐索引/主键

- 若继续保持列表语义：要求元素唯一且有序。
- 若未来需要表结构表达：推荐主键为 `Symbol`。

### 主要生产者

- `data/loaders/universe_loader.py`
- `data/providers/universe_provider.py`

### 主要消费者

- `data/services/data_service.py`
- `scripts/commands/factor.py`
- `scripts/commands/ic.py`
- `backtest/engine/backtest_engine.py`

### 当前不纳入共享契约的字段示例

- `rank_pct`
- `tags`
- `risk_flag`
- `holding_days`

这些字段当前都不属于股票池基础契约，更接近产品解释、风控或持仓语义。

## PanelFrame

### 定义

`PanelFrame` 是当前主链路里最核心的数据对象。
它由价格数据和基础信息拼接后形成，并在分析、因子、IC、回测链路中复用。

### 最小必需字段

- `Date`
- `Symbol`
- `Close`

### 推荐索引/主键

- 行唯一键建议：`Date + Symbol`
- 若使用索引：推荐保留 `Date` 时间语义，并继续显式保留 `Symbol` 列

### 主要生产者

- `data/loaders/price_loader.py`
- `data/loaders/basic_loader.py`
- `data/loaders/panel_loader.py`
- `data/processors/cleaner_processor.py`
- `data/providers/panel_provider.py`

### 主要消费者

- `data/services/data_service.py`
- `features/engine/factor_engine.py`
- `scripts/commands/factor.py`
- `scripts/commands/ic.py`
- `backtest/engine/backtest_engine.py`
- `data/processors/returns_processor.py`

### 当前不纳入共享契约的字段示例

- `delta`
- `rank_pct`
- `streak`
- `tags`
- `target_weight`
- `holding_days`
- `risk_flag`
- `execution_price`

这些字段不是当前共享市场面板的稳定输入字段，更多属于解释层、信号层或交易执行层。

## FactorFrame

### 定义

`FactorFrame` 当前真实存在，形态是 `PanelFrame` 上追加一组因子列后的 `DataFrame`。
它用于因子研究、snapshot 提取、打分和 IC 计算。

### 最小必需字段

- `Date`
- `Symbol`
- `Close`
- 至少一个因子列

### 推荐索引/主键

- 行唯一键建议：`Date + Symbol`

### 主要生产者

- `features/pipelines/factor_pipeline.py`
- `features/engine/factor_engine.py`
- `backtest/engine/backtest_engine.py`

### 主要消费者

- `features/engine/scoring_engine.py`
- `scripts/commands/factor.py`
- `scripts/commands/ic.py`
- `backtest/engine/backtest_engine.py`

### 当前不纳入共享契约的字段示例

- `score`
- `*_z`
- `*_contrib`
- `rank_pct`
- `delta`
- `streak`
- `tags`

这些字段已经属于打分层、解释层或中间过程字段，不应提前提升为共享 `FactorFrame` 契约的一部分。

## ScoreFrame

### 定义

`ScoreFrame` 当前真实存在，来源于单日 snapshot 经过 `ScoringEngine.score()` 之后的结果。
它是从因子横截面到可排序信号的中间结果。

### 最小必需字段

- `Symbol`
- `score`

### 推荐索引/主键

- 单日横截面时：推荐主键为 `Symbol`
- 若未来支持跨日：建议主键为 `Date + Symbol`

### 主要生产者

- `features/engine/scoring_engine.py`
- `backtest/simulation/signal_generator.py`

### 主要消费者

- `scripts/commands/factor.py`
- `backtest/simulation/signal_generator.py`
- `backtest/engine/backtest_engine.py`

### 当前不纳入共享契约的字段示例

- `rank_pct`
- `delta`
- `streak`
- `tags`
- `risk_flag`
- `holding_days`
- `target_weight`
- `execution_price`

当前共享打分契约应只关注稳定排序语义，不应提前吸收解释字段和执行决策字段。

## ICResult

### 定义

`ICResult` 当前真实存在，是 IC 分析链路的结果包。
它至少包含 `ic_df` 和 `summary`，并通常附带 `metadata`。

其中内部的 `ic_df` 当前是最稳定的 IC 明细表结构。

### 最小必需字段

- `ic_df`
- `summary`

对于 `ic_df` 本身，最小必需字段为：

- `Date`
- `factor`
- `ic`

### 推荐索引/主键

- `ic_df` 建议主键为 `Date + factor`
- `ICResult` 本身不是单表，更像结果包；其结果标识目前主要由缓存 key 决定

### 主要生产者

- `data/domains/ic_domain.py`
- `scripts/commands/ic.py`
- `data/providers/analysis_provider.py`
- `data/cache/analysis_cache.py`

### 主要消费者

- `scripts/commands/ic.py`
- `data/providers/analysis_provider.py`
- `data/cache/analysis_cache.py`

### 当前不纳入共享契约的字段示例

- `report_text`
- `tags`
- `delta`
- `streak`
- `risk_flag`

这些字段更偏解释层、展示层或其他业务域，不属于当前最小 IC 共享契约。

## BacktestResult

### 定义

`BacktestResult` 当前真实存在，是 `BacktestEngine.run()` 返回的结果包。
它是一个 `dict payload`，内部包含多个 `DataFrame`，并会被命令层打印和落盘。

### 最小必需字段

- `summary`
- `daily_pnl`
- `trades`
- `signals`
- `positions`
- `factor_panel`

其中当前比较稳定的子结构包括：

- `summary`
  - `total_return`
  - `annual_return`
  - `annual_volatility`
  - `sharpe`
  - `max_drawdown`
  - `win_rate`
  - `avg_turnover`
  - `total_cost`
  - `trading_days`

- `daily_pnl`
  - `date`
  - `gross_return`
  - `net_return`
  - `turnover`
  - `trading_cost`
  - `covered_weight`
  - `missing_symbols`
  - `position_count`

### 推荐索引/主键

- `BacktestResult` 顶层不是单表，无统一主键
- `daily_pnl` 建议主键为 `date`
- `trades` 建议主键为 `signal_date + execution_date`
- `signals` 建议主键为 `signal_date`
- `factor_panel` 建议主键为 `Date + Symbol`

### 主要生产者

- `backtest/engine/backtest_engine.py`
- `backtest/analysis/result_analyzer.py`

### 主要消费者

- `scripts/commands/backtest.py`
- `backtest/results/runs/*` 落盘结果

### 当前不纳入共享契约的字段示例

- `report_markdown`
- `chart_spec`
- `delta`
- `rank_pct`
- `streak`
- `tags`
- `risk_flag`
- `execution_price`
- `target_weight`
- `holding_days`

这些字段不是当前回测主结果对象的稳定共享字段，更多属于解释层、展示层或执行细节层。

## Shared vs Out-of-Scope Fields

当前应纳入共享契约的字段，优先满足以下条件：

- 在多条主链路中重复出现；
- 输入/输出语义稳定；
- 当前已有真实生产者和真实消费者；
- 不依赖 product / trading 特定上下文。

当前暂不纳入共享契约的字段，主要有三类：

1. 产品解释字段
   - `delta`
   - `rank_pct`
   - `streak`
   - `tags`

2. 交易执行字段
   - `target_weight`
   - `holding_days`
   - `risk_flag`
   - `execution_price`

3. 展示与报告字段
   - 报表文本
   - markdown 导出内容
   - 图表描述结构

这些字段未来可能会存在，但当前阶段不应提前写进共享主干契约。

## Evolution Rules

后续如果要扩展这些契约，应遵循以下规则：

1. 先确认字段已在真实主链路中稳定出现，再考虑纳入共享契约。
2. 先新增文档约束，再考虑是否需要最小代码注释。
3. 不因为单一命令、单一模型、单一策略需要，就把字段提升为共享契约字段。
4. 所有 product 解释字段和 trading 执行字段，默认先留在共享契约外。
5. 若对象结构尚未稳定，应优先记录“最小建议结构”，而不是强行冻结完整 schema。

当前阶段最重要的不是把所有数据对象做重，而是先把主链路中真正共享的最小对象契约固定下来。

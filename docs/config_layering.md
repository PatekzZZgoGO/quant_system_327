# Config Layering Strategy

## Purpose

本文档用于定义当前仓库配置体系的分层策略。

当前目标不是重写整个配置系统，也不是一次性迁移所有配置读取逻辑。
本阶段的重点是：

1. 识别当前真实存在的配置来源；
2. 明确哪些配置应归入 `base config`、`product config`、`trading config`；
3. 先把边界说清楚，为后续渐进迁移提供骨架。

当前阶段以“边界清晰化”为主，不追求一次迁移完成。

## Current Config Sources

根据当前仓库代码，配置主要来自以下几类来源：

1. 全局 YAML
   - `infra/config/settings.yaml`
   - 由 `infra/config/config_loader.py` 读取

2. 共享基础配置对象
   - `core/common/config.py`
   - 以 `APP_CONFIG` 形式向主链路暴露

3. 策略局部 `config.yaml`
   - `strategies/*/config.yaml`
   - 当前文件已存在，但尚未形成稳定加载链路

4. 环境变量
   - 目前主要通过 `${TUSHARE_TOKEN}` 这类占位方式进入 `settings.yaml`

5. 代码内默认参数
   - 分散在命令行参数默认值、模型定义、回测参数、抓取参数中

这说明当前仓库并不是单一配置中心，而是多入口并存状态。

## Layer Definitions

### `base config`

`base config` 承载共享主干所需的稳定配置。

这类配置应满足：

- 同时服务多个模块；
- 不直接绑定某个 product 或 trading 场景；
- 更多体现基础路径、基础环境、基础设施和共享数据访问约定。

### `product config`

`product config` 承载信号产品相关参数。

这类配置应满足：

- 直接影响因子、模型、信号、解释、研究分析结果；
- 更贴近信号产品逻辑，而不是基础设施；
- 允许随着产品演进而变化。

### `trading config`

`trading config` 承载交易系统相关参数。

这类配置应满足：

- 直接影响执行、调仓、风控、交易成本、live 运行行为；
- 更贴近交易系统，而不是共享分析主干；
- 可以与产品参数独立演进。

## Base Config

当前更适合归入 `base config` 的配置包括：

- `root_dir`
- `env`
- 数据路径相关：
  - `data_dir`
  - `raw_dir`
  - `processed_dir`
  - `stock_dir`
  - `stock_list_file`
- 缓存路径相关：
  - `cache_dir`
  - `cache_panel_dir`
  - `cache_factor_dir`
  - `cache_ic_dir`
  - `cache_universe_dir`
- logging 相关配置
- 市场基础设置：
  - `data.market`
- 数据接入基础配置：
  - `tushare.token`
  - `tushare.request_delay`
  - `tushare.max_retries`
  - `tushare.cache_expiry_days`
- 基础批量更新区间：
  - `data.batch_start_date`
  - `data.batch_end_date`
- 基础设施配置：
  - `database.host`

这些配置当前要么已经由 `APP_CONFIG` 提供，要么已经由 `settings.yaml` 在数据抓取链路中使用。
它们共同特点是：服务共享基础能力，而不是直接定义信号产品或交易系统行为。

## Product Config

当前更适合归入 `product config` 的配置包括：

- `default_lookback_days`
- 因子列表
- 模型权重
- `TopN`
- score 相关参数
- 因子研究参数
- 内容/解释参数
  - `delta`
  - `rank_pct`
  - `streak`
  - `tags`
- 策略局部参数：
  - `window`
  - `entry_z`
  - `exit_z`
  - `period`
  - `threshold`
  - `factors`

这些配置当前分散在：

- `models/alpha/*.py`
- `strategies/*/config.yaml`
- 命令层默认参数
- 少量共享分析默认值

它们的共同特点是：直接定义信号产品、因子分析、选股输出或解释口径。

## Trading Config

当前更适合归入 `trading config` 的配置包括：

- `commission_rate`
- `slippage_rate`
- `rebalance_every`
- `execution_delay`
- 执行参数
- 风控参数
- live 参数
- 交易系统运行参数

未来更可能属于这一层的典型字段包括：

- `target_weight`
- `holding_days`
- `risk_flag`
- `execution_price`

这些参数当前主要散落在：

- `scripts/commands/backtest.py`
- `backtest/simulation/execution_model.py`
- `backtest/engine/backtest_engine.py`

它们的共同特点是：直接影响调仓节奏、执行建模、成本建模、交易落地和风控行为。

## Migration Principles

后续如果推进配置迁移，应遵循以下原则：

1. 先文档分层，再逐步迁移实现。
2. 优先迁移重复出现、跨模块复用的稳定配置。
3. 不因为某一个命令、某一个模型、某一个策略需要，就立即提升为共享配置。
4. `base config` 保持稳定和共享性，不要混入大量 product / trading 特定参数。
5. `product config` 与 `trading config` 应允许分别演进，不互相绑定。
6. 对现有 CLI 默认值、模型常量、策略局部 YAML，应先建立映射关系，再决定是否迁移到统一配置入口。

## Compatibility Notes

当前仓库存在两套已生效的配置入口：

- `core/common/config.py` 中的 `APP_CONFIG`
- `infra/config/settings.yaml` + `infra/config/config_loader.py`

因此当前阶段不应强行立即合并为单一入口。

兼容性处理原则应当是：

- 保持现有行为不变；
- 保留当前读取方式；
- 先明确每个配置属于哪一层；
- 后续按层分批迁移，而不是一次性替换。

特别说明：

- `APP_CONFIG` 当前更接近共享主干的基础配置入口；
- `settings.yaml` 当前更接近数据抓取与环境配置入口；
- `strategies/*/config.yaml` 当前更像产品层预留配置；
- CLI 默认值和模型内常量目前仍是重要现实来源，迁移时必须尊重其现状。

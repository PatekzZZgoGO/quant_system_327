quant_system/
│
├── core/                                  # 核心引擎层：系统调度中枢，定义策略如何运行，与平台完全解耦
│   ├── strategy/                          # 策略抽象层：定义统一策略接口和生命周期管理
│   │   ├── base_strategy.py               # 策略基类，定义 initialize / on_bar / on_order 等标准接口
│   │   ├── strategy_context.py            # 策略上下文，封装当前持仓、账户资金、当前时间等运行时信息
│   │   ├── strategy_state.py              # 策略内部状态管理，用于缓存历史信号、中间变量等
│   │   └── strategy_manager.py            # ✨ 多策略管理器，管理多个策略实例，接收市场事件并汇总信号
│   │
│   ├── event/                             # 事件系统：EDA核心，实现事件驱动架构
│   │   ├── event.py                       # 事件对象定义（MarketEvent, OrderEvent, TradeEvent等）
│   │   ├── event_queue.py                 # 事件队列（FIFO），解耦数据流与执行逻辑
│   │   └── event_types.py                 # 事件类型枚举（BAR, SIGNAL, ORDER, FILL等）
│   │
│   ├── engine/                            # 核心调度引擎：系统大脑，负责调度与事件分发
│   │   ├── engine.py                      # 主引擎抽象接口，定义 run/stop 等方法，供具体平台实现
│   │   ├── scheduler.py                   # 定时调度器，基于时间触发（开盘/收盘/调仓）
│   │   └── dispatcher.py                  # 事件分发器，将事件派发给策略、执行模块等
│   │
│   └── common/                            # 通用定义：枚举、常量、异常等
│       ├── enums.py                       # 枚举定义（买卖方向、订单状态、市场状态等）
│       ├── constants.py                   # 系统常量（交易时间、默认参数等）
│       └── exceptions.py                  # 自定义异常类（策略异常、数据异常、风控异常等）
│
├── adapters/                              # 平台适配层：实现一套策略多环境运行的关键抽象
│   ├── joinquant/                         # 聚宽平台适配，用于在聚宽上验证策略
│   │   ├── jq_entry.py                    # 聚宽入口，实现 initialize/handle_data 等回调函数
│   │   ├── jq_context_adapter.py          # 将聚宽的 context 对象转换为系统标准上下文
│   │   ├── jq_data_adapter.py             # 封装聚宽数据接口（get_price等），实现 MarketDataFeed 接口
│   │   ├── jq_order_adapter.py            # 封装聚宽下单接口（order_target等），转换为系统订单事件
│   │   └── jq_scheduler_adapter.py        # 映射聚宽定时任务（run_daily）到系统调度器
│   │
│   ├── local/                             # 本地回测适配：基于 pandas 的高性能回测引擎
│   │   ├── local_engine.py                # 本地回测引擎，实现 core/engine/engine.py 接口
│   │   ├── local_context.py               # 模拟账户系统，管理资金、持仓、订单状态
│   │   ├── local_data_feed.py             # 本地数据加载器，从 parquet 文件读取数据，实现 MarketDataFeed 接口
│   │   ├── local_broker_simulator.py      # 模拟撮合器，处理订单成交、滑点、手续费等
│   │   └── local_event_loop.py            # 本地事件循环，按时间顺序回放历史数据
│   │
│   └── broker/                            # 实盘接口抽象，支持对接券商 API（未来扩展）
│       ├── base/                          # 实盘接口抽象基类，定义订单、查询、行情等标准方法
│       ├── qmt/                           # 迅投 QMT 接口实现
│       └── huatai/                        # 华泰证券接口实现
│
├── data/                                  # 数据层：数据生命周期（采集 → 清洗 → 存储 → 读取）
│   ├── ingestion/                         # 数据采集模块，从不同数据源获取原始数据
│   │   ├── tushare_client.py              # Tushare 数据源客户端
│   │   ├── akshare_client.py              # AKShare 数据源客户端
│   │   └── jq_client.py                   # 聚宽数据源客户端（通常用于获取实时行情）
│   │
│   ├── processing/                        # 数据清洗与预处理
│   │   ├── adjust_price.py                # 复权处理（前复权/后复权）
│   │   ├── align_calendar.py              # 时间对齐，按交易日历标准化
│   │   ├── fill_missing.py                # 缺失值处理（插值、填充）
│   │   └── universe_filter.py             # 股票池过滤（剔除 ST、停牌、新股等）
│   │
│   ├── loaders/                           # 数据读取接口（供上层模块使用）
│   │   ├── market_loader.py               # 市场数据加载器，定义 MarketDataFeed 抽象基类
│   │   ├── factor_loader.py               # ✨ 因子数据统一加载器，封装因子存储读取，提供 get_factor 接口
│   │   └── universe_loader.py             # 股票池加载器
│   │
│   ├── storage/                           # 存储抽象，支持多种存储后端
│   │   ├── parquet_store.py               # Parquet 格式存储（推荐高性能列存储）
│   │   ├── file_store.py                  # 通用文件存储（CSV、Pickle等）
│   │   └── cache_store.py                 # 缓存存储（内存、Redis）
│   │
│   ├── datasets/                          # 数据文件落地目录
│   │   ├── raw/                           # 原始数据，不可修改，用于数据溯源
│   │   ├── processed/                     # 清洗后标准数据，供回测和分析使用
│   │   └── cache/                         # 临时缓存数据（如因子中间结果）
│   │
│   ├── snapshots/                         # ✨ 数据快照管理，记录数据版本，保证回测可复现
│   │   ├── snapshot_20260101.yaml         # 快照元数据（日期范围、数据源hash、数据版本号等）
│   │   └── ...
│   │
│   └── schema/                            # 数据结构定义（使用 Pydantic 或 dataclass）
│
├── features/                              # 特征工程层（因子层）：数据 → 因子 → 特征
│   ├── factors/                           # 因子定义模块
│   │   ├── momentum/                      # 动量类因子（如 N 日收益率、RSI 等）
│   │   ├── volatility/                    # 波动率类因子（如 ATR、标准差等）
│   │   └── fundamental/                   # 基本面因子（如 ROE、营收增速等）
│   │
│   ├── pipelines/                         # 因子处理流程
│   │   ├── factor_pipeline.py             # 因子生成管道，串联多个因子计算步骤
│   │   ├── normalization.py               # 因子标准化（z-score、min-max 等）
│   │   └── feature_union.py               # 多因子合并（加权、PCA 等）
│   │
│   ├── loader.py                          # ✨ 因子统一加载器，封装 store 读取逻辑，供策略层调用
│   │
│   └── store/                             # 因子数据存储（按因子类别组织）
│       ├── momentum/                      # 动量因子存储目录
│       ├── technical/                     # 技术指标因子存储目录
│       └── combined/                      # 复合因子存储目录
│
├── models/                                # 信号生成层：特征 → 交易信号
│   ├── alpha/                             # 规则模型（如阈值、逻辑判断）
│   ├── ml/                                # 机器学习模型（sklearn, xgboost, lightgbm 等）
│   └── output/                            # 信号输出存储（按策略/模型组织）
│
├── portfolio/                             # 组合构建层：信号 → 权重
│   ├── construction/                      # 权重构建方法（等权、风险平价、优化器等）
│   ├── constraints/                       # 组合约束（仓位限制、行业暴露、单票上限等）
│   └── store/                             # 组合数据存储
│       ├── weights/                       # 每日权重矩阵
│       └── holdings/                      # 持仓快照
│
├── risk/                                  # 风控系统：实时风险控制
│   ├── rules/                             # 风控规则（止损、限仓、黑名单等）
│   ├── monitors/                          # 实时监控（回撤、波动率、敞口等）
│   └── risk_manager.py                    # 风控总控，调用规则引擎和监控模块，拦截危险订单
│
├── execution/                             # 执行系统：权重 → 订单 → 成交
│   ├── order/                             # 订单管理模块
│   │   ├── order_manager.py               # 订单管理器，维护订单状态（已报、部分成交、已撤等）
│   │   └── order_generator.py             # ✨ 订单生成器，根据组合权重和目标仓位生成具体订单
│   ├── algo/                              # 执行算法（VWAP, TWAP, POV 等）
│   ├── cost/                              # 成本模型（滑点、手续费、冲击成本）
│   └── store/                             # 交易数据存储
│       ├── orders/                        # 订单明细
│       └── trades/                        # 成交明细
│
├── backtest/                              # 回测系统：历史数据重放 + 策略验证
│   ├── engine/                            # 回测引擎（调用 core 引擎，串联数据、策略、执行）
│   ├── simulation/                        # 模拟器（账户、撮合、成本）
│   ├── analysis/                          # 绩效分析（收益、回撤、夏普比率、多因子归因等）
│   │
│   └── results/                           # 回测结果存储
│       └── runs/                          # 单次运行结果目录
│           └── run_001/
│               ├── config_snapshot.yaml   # ✨ 回测配置快照（策略参数、数据版本、系统版本等）
│               ├── equity_curve.csv       # 净值曲线
│               ├── transactions.csv       # ✨ 成交明细（用于归因分析）
│               ├── log.txt                # ✨ 该次回测的完整日志副本
│               └── report.html            # 可视化分析报告
│
├── strategies/                            # 策略实现区（核心开发区）
│   ├── momentum/                          # 动量策略示例
│   │   ├── strategy.py                    # 策略逻辑实现（继承 BaseStrategy）
│   │   └── config.yaml                    # ✨ 策略参数配置（周期、阈值、资金分配等）
│   ├── mean_reversion/                    # 均值回归策略
│   │   ├── strategy.py
│   │   └── config.yaml
│   └── multi_factor/                      # 多因子策略
│       ├── strategy.py
│       └── config.yaml
│
├── infra/                                 # 基础设施层：支撑系统稳定性与可观测性
│   ├── logging/                           # 日志系统（结构化日志，支持 JSON 格式）
│   │   ├── logger.py                      # 日志入口，提供 get_logger 函数
│   │   ├── log_config.yaml                # 日志配置（级别、格式、输出路径、轮转策略）
│   │   ├── handlers/                      # 自定义处理器
│   │   │   ├── file_handler.py            # 文件输出
│   │   │   ├── console_handler.py         # 控制台输出
│   │   │   └── rotating_handler.py        # 日志轮转
│   │   ├── formatters/                    # 日志格式器
│   │   │   ├── text_formatter.py          # 文本格式
│   │   │   └── json_formatter.py          # JSON 结构化格式（推荐）
│   │   └── filters/                       # 日志过滤器
│   │       └── level_filter.py            # 按级别过滤
│   │
│   ├── config/                            # 配置系统（YAML 配置，支持环境变量覆盖）
│   │   ├── config_loader.py               # 配置加载器，读取 YAML 并合并环境变量
│   │   └── settings.yaml                  # 全局配置文件（数据库连接、日志路径、API keys 等）
│   │
│   ├── database/                          # 数据库连接管理（SQLAlchemy, MySQL, PostgreSQL 等）
│   ├── cache/                             # 缓存抽象（Redis, Memcached 等）
│   │
│   └── monitoring/                        # ✨ 监控与告警模块（实盘必备）
│       ├── metrics.py                     # 指标收集（使用 prometheus_client 暴露接口）
│       ├── alert_rules.yaml               # 告警规则配置（如回撤超限、订单延迟、风控触发）
│       └── health_check.py                # 系统健康检查（心跳、依赖服务状态）
│
├── logs/                                  # 日志输出目录（运行时生成）
│   ├── system/                            # 系统级日志（引擎、调度器）
│   ├── strategy/                          # 策略日志（信号生成、交易决策）
│   ├── execution/                         # 执行日志（订单、成交）
│   ├── risk/                              # 风控日志（规则触发）
│   ├── backtest/                          # 回测专用日志
│   └── error/                             # 错误日志（单独存放便于排查）
│
├── live/                                  # 实盘运行数据（与账户相关，通常不提交 git）
│   ├── account/                           # 账户信息（资金、佣金费率）
│   ├── positions/                         # 实时持仓快照
│   └── logs/                              # 实盘日志（按日切割）
│
├── cache/                                 # 全局缓存目录（临时数据，如因子计算结果）
│
├── scripts/                               # 系统入口脚本
│   ├── run_jq.py                          # 启动聚宽运行（通过 adapter 映射）
│   ├── run_backtest.py                    # 启动本地回测（指定策略、参数、时间范围）
│   ├── run_live.py                        # 启动实盘（从配置文件加载券商接口）
│   └── update_data.py                     # 数据更新任务（拉取最新行情、因子）
│
├── tests/                                 # 单元测试（与模块结构对应，使用 pytest）
│   ├── conftest.py                        # 共享 fixtures，如测试数据、模拟引擎
│   ├── core/                              # 核心模块测试
│   │   ├── test_engine.py                 # 引擎调度逻辑测试
│   │   └── test_strategy_manager.py       # 策略管理器测试
│   ├── adapters/                          # 适配器测试
│   │   ├── test_local_engine.py           # 本地引擎测试
│   │   └── test_jq_adapter.py             # 聚宽适配器测试
│   ├── data/                              # 数据层测试
│   │   ├── test_loaders.py                # 数据加载器测试
│   │   └── test_processing.py             # 数据清洗测试
│   ├── features/                          # 因子模块测试
│   ├── models/                            # 信号模型测试
│   ├── portfolio/                         # 组合构建测试
│   ├── risk/                              # 风控规则测试
│   ├── execution/                         # 执行模块测试
│   ├── backtest/                          # 回测系统测试
│   └── strategies/                        # 策略测试（每个策略应有独立测试）
│
├── notebooks/                             # Jupyter 研究环境（策略研究、因子分析、结果可视化）
│
└── docs/                                  # 项目文档
    ├── architecture.md                    # 架构设计文档
    ├── development_guide.md               # 开发规范与协作指南
    ├── data_dictionary.md                 # 数据字段说明
    └── ...
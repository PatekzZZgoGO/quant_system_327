🧠【量化系统上下文 v2.0（强化版，可直接复制）】
🧩 一、项目定位

我正在构建一个：

🔥 多因子量化研究平台（Factor Research Platform）

当前阶段定位：

✅ Research System（研究级）
⏳ 向 Production / Backtest System 过渡

当前核心目标：

因子计算（Factor Engine）
因子评估（IC Analysis）
数据层解耦（Data Layer Refactor）
性能优化（Performance Optimization）
🏗️ 二、系统整体架构

采用 分层架构（Layered Architecture） + Domain Driven Design（简化版）

CLI（scripts/commands）
    ↓
Application Layer（Factor / IC）
    ↓
DataService（统一入口）
    ↓
Domain（Market / Returns / IC）
    ↓
Processor（纯计算逻辑）
    ↓
Loader（数据 IO）
    ↓
Parquet（存储层）

设计原则：

✅ 单一职责（SRP）
✅ IO 与计算分离
✅ 上层不感知底层数据细节
✅ 面向 panel 数据（而非单标的）
⚙️ 三、Data Layer（已完成重构）
✅ 1. DataService（统一入口）
data_service.get_panel(symbols, start, end)
data_service.get_universe(limit)

返回：

Market（包含 panel）
Universe（symbols）

👉 作用：屏蔽底层 Loader / Processor 复杂性

✅ 2. Loader（IO 层）
price_loader.py
basic_loader.py
panel_loader.py
universe_loader.py

特点：

Parquet 存储
支持批量加载
ThreadPoolExecutor 并行
✅ 3. Processor（纯函数计算）
aligner_processor.py
merge_asof(direction="backward")（防未来函数）
cleaner_processor.py
排序 / 缺失处理
returns_processor.py
future return 计算

👉 严格无副作用（Stateless）

✅ 4. Domain（语义封装）
Market
Returns
IC

👉 提供语义化接口（而不是 DataFrame 操作）

📊 四、Factor 模块
执行流程
panel（全量）
 → factor_engine.pipeline.run()   ← 一次性计算所有因子
 → handle_missing（统一处理）
 → snapshot（按日期切片）
 → scoring_engine.score()
 → select()
核心设计
✅ 向量化（groupby / rolling）
✅ 因子一次性计算（避免重复 IO）
✅ snapshot 延迟切片（提升效率）
✅ 因子与打分解耦
📈 五、IC 模块
执行流程
panel
 → factor（一次性）
 → missing（统一处理）
 → returns.forward()
 → IC.compute()
 → summarize_ic()
核心实现
1️⃣ Future Return
df.groupby("Symbol")["Close"].shift(-horizon)
2️⃣ 横截面 IC（Spearman）
df.groupby("Date").apply(
    lambda x: x[factors].corrwith(x[ret_col], method="spearman")
)
3️⃣ 输出指标
mean IC
std IC
IR（Information Ratio）
⚠️ 六、关键设计问题（已解决）
❗1. 未来函数问题
merge_asof(direction="backward")
❗2. returns 覆盖 panel（严重 bug）

❌ 错误：

panel = returns

✅ 正确：

panel = panel.merge(returns)
❗3. 因子列丢失问题

原因：

missing 处理覆盖
pipeline 输出不一致

当前策略：

保留 raw factor（momentum）
可选标准化列（momentum_z）
📦 七、技术栈
数据
pandas
parquet
计算
groupby / rolling / shift
向量化计算
并行
ThreadPoolExecutor（Loader 层）
架构
Layered Architecture
Domain + Service
Pipeline Pattern（Factor）
CLI（argparse）
📊 八、当前系统能力
✅ 已完成
因子计算引擎
IC 分析系统
数据层解耦
无未来函数数据处理
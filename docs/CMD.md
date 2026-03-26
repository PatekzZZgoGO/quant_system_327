# 初始化环境
        uik00533@RXL1718W MINGW64 /d/qaunt_system_327/quant_system_327 (main)
        $ python -m venv venv

        uik00533@RXL1718W MINGW64 /d/qaunt_system_327/quant_system_327 (main)
        $ source venv/Scripts/activate  //每次重新打开vscode终端都需要重新source一次
        (venv) 
        uik00533@RXL1718W MINGW64 /d/qaunt_system_327/quant_system_327 (main)
        $ PYTHONUTF8=1 pip install -r requirements.txt
# 数据获取
        # =========================

        python run.py data update stocks       # 全量更新股票数据（默认带缓存、断点续传）

        python run.py data update stocks --limit 200     # 仅更新前200只（调试/测试用）

        python run.py data update stocks --force-refresh # 强制刷新（忽略缓存，重新拉）

        python run.py data update stocks --start-date 2020-01-01 --end-date 2024-01-01   # 指定时间范围

        python run.py data update stocks --resume        # 断点续传（默认其实已经开启）

        # =========================
        # 股票列表
        # =========================

        python run.py data update stock_list   # 从Tushare获取最新股票列表

        # =========================
        # 缓存状态
        # =========================

        python run.py data status              # 查看缓存覆盖率（总数/已缓存/缺失）

        # =========================
        # 调试常用
        # =========================

        python run.py data update stocks --limit 10      # 小规模测试（10只）

        python run.py data update stocks --limit 50 --force-refresh   # 强制重跑小批数据

        python run.py data update stocks --limit 1       # 单只调试（定位bug用）



下一步做这个
1️⃣ IC 分析（核心）

👉 判断因子有没有用

2️⃣ 因子组合优化

👉 不只是手写 weights

3️⃣ 行业中性化

👉 去掉行业 bias


🚀 强烈建议你再做一个升级
👉 统一时间窗口（核心）

你现在最大的问题是：

price ≠ basic 时间长度不一致
正确做法：

在 data update stocks 里：

start_date = "20100101"   # 固定全历史
end_date = today

👉 永远拉：

全量历史
🧠 你现在系统的状态

你已经从：

❌ demo脚本

进化到：

⚠️ 数据系统（但有一致性风险）
🔥 下一步（必须做）

我给你一个优先级👇

🥇 P0（必须马上修）
 防止 cache 被短数据覆盖
 price / basic 对齐（时间）
🥈 P1（你刚刚做到一半）
 factor 不再调用 API
 只读 parquet
🥉 P2（高级玩家）
 数据 schema 统一（字段标准）
 parquet 分区（加速）


 🚀 如果你愿意再进阶一点

我可以帮你升级成：

✅ 支持多周期因子（momentum_5d / 20d 自动组合）
✅ 自动标准化 + 打分 pipeline
✅ 因子配置 YAML 化（量化私募级别）
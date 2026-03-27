# 初始化环境
        uik00533@RXL1718W MINGW64 /d/qaunt_system_327/quant_system_327 (main)
        $ python -m venv venv

        uik00533@RXL1718W MINGW64 /d/qaunt_system_327/quant_system_327 (main)
        $ source venv/Scripts/activate  //每次重新打开vscode终端都需要重新source一次
        (venv) 
        uik00533@RXL1718W MINGW64 /d/qaunt_system_327/quant_system_327 (main)
        $ PYTHONUTF8=1 pip install -r requirements.txt
# 数据获取
        1️⃣ 更新单只股票
        python run.py data update stock --code <股票代码>

        参数说明：

        --code           必填，股票代码，如 000001.SZ
        --start-date     起始日期 YYYY-MM-DD
        --end-date       结束日期 YYYY-MM-DD
        --force-refresh  强制重新下载
        2️⃣ 更新多只股票
        python run.py data update stocks

        参数说明：

        --start-date     起始日期
        --end-date       结束日期
        --limit          仅更新前 N 只股票（测试用）
        --force-refresh  强制刷新（忽略缓存）
        --resume         断点续传（跳过已存在数据）
        3️⃣ 查看缓存状态
        python run.py data status cache
# 因子选股

        # 📊 Factor 模块 CLI

        ## 🚀 运行因子选股

        ```bash
        python run.py factor run --date 20240105 --model simple_alpha
        ```

        ---

        ## 📌 参数说明

        ### 必填参数

        ```bash
        --date 20240105
        ```

        * 交易日期（YYYYMMDD）
        * 用于生成当日横截面（防未来函数）

        ```bash
        --model simple_alpha
        ```

        * 策略模型名称
        * 对应路径：models/alpha/simple_alpha.py
        * 提供因子权重（WEIGHTS 或 get_weights）

        ---

        ### 可选参数

        ```bash
        --top-n 50
        ```

        * 选股数量（默认 50）

        ---

        ```bash
        --limit 20
        ```

        * 限制股票池数量（测试用，强烈建议调试时使用）

        ---

        ```bash
        --weights momentum_20d=1.0,volatility_20d=-1.0
        ```

        * 手动指定权重（覆盖 model）
        * 格式：因子名=权重（必须与因子函数名一致）

        ---

        ```bash
        --save
        ```

        * 保存结果到 outputs/ 目录

        ---

        ## 🧪 常用示例

        ### 基础运行

        ```bash
        python run.py factor run --date 20240105 --model simple_alpha
        ```

        ---

        ### 小样本测试

        ```bash
        python run.py factor run --date 20240105 --model simple_alpha --limit 20
        ```

        ---

        ### 单因子测试

        ```bash
        python run.py factor run --date 20240105 --model low_vol --limit 20
        ```

        ---

        ### 覆盖权重

        ```bash
        python run.py factor run \
        --date 20240105 \
        --model simple_alpha \
        --weights momentum_20d=1.0,volatility_20d=-0.3
        ```

        ---

        ## 📊 输出说明（简要）

        * **Top Stocks**：最终选股结果
        * **Factor Contribution**：各因子贡献（zscore × weight）
        * **Debug Info**：样本数量 / score 范围
        * **Factor Stats**：因子影响力统计


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
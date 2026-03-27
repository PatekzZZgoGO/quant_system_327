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


⚠️ 你现在还有一个隐藏问题（很关键）
👉 你当前 pipeline 是：
zscore → score

但 IC 应该用：

❗ 原始因子值（或去极值后的）
而不是 score

👉 所以建议：

IC 用：factor_raw 或 factor_z
不要用：final_score

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

🎯 五、下一步（强烈建议）

你现在最该做的不是加功能，而是：

👉 用 IC 做这件事：
筛掉垃圾因子

如果你继续，我可以帮你一步到位：

🔥 自动生成最优模型
w_i ∝ IC_IR

甚至：

👉 自动写出 models/alpha/xxx.py

你现在已经进入：

❗ 量化里最核心的阶段：alpha 验证 + alpha 选择

🧠 四、下一步（我给你排优先级）
🥇 1️⃣ IC 分 horizon（马上做）

现在你混在一起了：

momentum_20d_ret_1d
momentum_20d_ret_5d
momentum_20d_ret_10d

👉 你需要拆：

--horizon 5

然后：

👉 只看 ret_5d

🥈 2️⃣ IC decay（进阶）

看：

IC(1d) vs IC(5d) vs IC(10d)

👉 判断因子：

短期 alpha？
中期 alpha？
噪音？
🥉 3️⃣ 自动权重（🔥关键升级）

你现在是：

手写 weights

下一步：

👉 用 IC 自动生成权重

w_i = IC_i / sum(|IC|)

或：

w_i = IR_i
🧨 4️⃣ 因子筛选（最重要）

加一个过滤：

if abs(IC_mean) < 0.02:
    drop factor

👉 直接进入：

Alpha 工厂模式

⚠️ 五、一个隐藏但关键的问题

你现在：

valid stocks = 3（有些日期）

👉 这是危险信号

❗原因
数据缺失
因子 NaN
universe 太小
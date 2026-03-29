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
# IC

        python run.py ic --start 2024-01-01 --end 2024-01-05 --limit 20




        

如果你下一步继续，我建议直接干这个：

🚀 IC Engine 升级（彻底去 merge + 全向量化 + 单次 groupby）

这个会再给你一个 2~5x 提升

🔥 接下来最值得做的 3 件事

我按“收益最大”排序：

🥇 1. 加 Panel Cache（最赚钱优化）

你现在每次：

load_panel → parquet IO

👉 很慢

直接加：

内存缓存 + parquet cache
🥈 2. 因子缓存（Factor Cache）
panel → factor（很慢）

👉 可以缓存：

factor_panel.parquet
🥉 3. IC 结果持久化

现在只是 print：

=== IC Summary ===

👉 应该：

data/snapshots/ic/
    ic_20240101_20240105.parquet
⚠️ 一个非常关键的提醒（你已经快踩到了）

你现在：

panel = factor_engine.pipeline.run(...)
panel = factor_engine.handle_missing(...)

👉 这里有一个隐患：

❗ 因子被 overwrite（尤其 _z）

建议你统一：

raw factor: momentum
normalized: momentum_z

不要混用
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

        python scripts/run.py data update stocks       # 全量更新股票数据（默认带缓存、断点续传）

        python scripts/run.py data update stocks --limit 200     # 仅更新前200只（调试/测试用）

        python scripts/run.py data update stocks --force-refresh # 强制刷新（忽略缓存，重新拉）

        python scripts/run.py data update stocks --start-date 2020-01-01 --end-date 2024-01-01   # 指定时间范围

        python scripts/run.py data update stocks --resume        # 断点续传（默认其实已经开启）

        # =========================
        # 股票列表
        # =========================

        python scripts/run.py data update stock_list   # 从Tushare获取最新股票列表

        # =========================
        # 缓存状态
        # =========================

        python scripts/run.py data status              # 查看缓存覆盖率（总数/已缓存/缺失）

        # =========================
        # 调试常用
        # =========================

        python scripts/run.py data update stocks --limit 10      # 小规模测试（10只）

        python scripts/run.py data update stocks --limit 50 --force-refresh   # 强制重跑小批数据

        python scripts/run.py data update stocks --limit 1       # 单只调试（定位bug用）
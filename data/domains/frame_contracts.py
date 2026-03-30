"""Shared contract reference for core data objects.

当前文件仅作为 shared contract reference，不是强约束实现。
这里不做运行时校验，不参与现有主链路逻辑，只用于集中记录当前最小字段契约。
"""

# UniverseFrame 当前在运行时更接近 symbols 列表；这里保留最小表结构参考。
UNIVERSE_REQUIRED_FIELDS = ["Symbol"]

# PanelFrame 是当前主链路里最核心的基础数据对象。
PANEL_REQUIRED_FIELDS = ["Date", "Symbol", "Close"]

# FactorFrame 本质上是 PanelFrame 加上一组因子列。
# 这里仅记录基础骨架，具体因子列集合由实际 pipeline / model 决定。
FACTOR_REQUIRED_FIELDS = ["Date", "Symbol", "Close"]

# ScoreFrame 是单日横截面打分结果的最小共享结构。
SCORE_REQUIRED_FIELDS = ["Symbol", "score"]

# ICFrame 是当前最稳定的 IC 明细结构。
IC_REQUIRED_FIELDS = ["Date", "factor", "ic"]

# BacktestResult 是结果包而不是单表；这里记录顶层最小键集合参考。
BACKTEST_RESULT_REQUIRED_KEYS = [
    "summary",
    "daily_pnl",
    "trades",
    "signals",
    "positions",
    "factor_panel",
]

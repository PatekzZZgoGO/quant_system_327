# Quant System

可扩展、可复用、跨平台运行的量化交易系统。

## 快速开始

1. 安装依赖：`pip install -r requirements.txt`
2. 配置环境：复制 `.env.example` 为 `.env` 并填写必要配置
3. 运行回测：`python scripts/run_backtest.py --strategy momentum --start 2020-01-01 --end 2023-12-31`
4. 在聚宽上运行：`python scripts/run_jq.py`（需配置聚宽环境）

## 项目结构

详见 `docs/architecture.md`。

## 开发指南

请参考 `docs/development_guide.md`。

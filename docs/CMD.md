# Run.py 命令速查表

`run.py` 是项目统一入口，支持两种使用方式：

- 交互模式：`python run.py`
- CLI 模式：`python run.py <module> ...`

当前统一入口下的模块有：`data`、`factor`、`ic`、`backtest`。

## 交互入口

```bash
python run.py
```

适合临时执行命令或不想手写参数时使用。

## Factor

最小命令：

```bash
python run.py factor run --date 2024-01-31 --model simple_alpha
```

必填参数：

- `--date`：分析日期
- `--model`：模型名称，对应 `models/alpha/<model>.py`

常用参数：

- `--top-n`：选股数量，默认 `50`
- `--limit`：限制股票池数量
- `--weights`：手工覆盖权重，格式如 `momentum_20d=1,liquidity=0.5`
- `--save`：保存结果

常用示例：

```bash
python run.py factor run --date 2024-01-31 --model simple_alpha --limit 20
```

```bash
python run.py factor run --date 2024-01-31 --model low_vol
```

```bash
python run.py factor run --date 2024-01-31 --model simple_alpha --weights momentum_20d=1.0,volatility_20d=-0.3
```

## IC

最小命令：

```bash
python run.py ic --start 2024-01-01 --end 2024-01-31
```

常用写法：

```bash
python run.py ic --start 2024-01-01 --end 2024-01-31 --model simple_alpha
```

必填参数：

- `--start`：开始日期
- `--end`：结束日期

常用参数：

- `--model`：模型名称
- `--factors`：指定因子列表，如 `--factors momentum_20d liquidity`
- `--horizon`：前瞻收益周期，默认 `5`
- `--limit`：限制股票池数量

常用示例：

```bash
python run.py ic --start 2024-01-01 --end 2024-01-31 --limit 20
```

```bash
python run.py ic --start 2024-01-01 --end 2024-01-31 --model simple_alpha --limit 20
```

```bash
python run.py ic --start 2024-01-01 --end 2024-01-31 --factors momentum_20d liquidity --horizon 10
```

## Backtest

最小命令：

```bash
python run.py backtest run --start 2024-01-01 --end 2024-01-31 --model simple_alpha
```

必填参数：

- `--start`：回测开始日期
- `--end`：回测结束日期
- `--model`：模型名称

常用参数：

- `--top-n`：持仓数量，默认 `20`
- `--limit`：限制股票池数量
- `--rebalance-every`：调仓频率，默认 `1`
- `--execution-delay`：执行延迟，默认 `1`
- `--commission-rate`：手续费率，默认 `0.001`
- `--slippage-rate`：滑点率，默认 `0.0`
- `--save`：保存结果
- `--no-cache`：关闭缓存

常用示例：

```bash
python run.py backtest run --start 2024-01-01 --end 2024-01-31 --model simple_alpha --limit 20 --top-n 5
```

```bash
python run.py backtest run --start 2024-01-01 --end 2024-01-31 --model simple_alpha --rebalance-every 5 --execution-delay 1
```

```bash
python run.py backtest run --start 2024-01-01 --end 2024-01-31 --model simple_alpha --save
```

## Data

### 查看缓存状态

```bash
python run.py data status cache
```

### 更新单只股票

```bash
python run.py data update stock --code 000001.SZ
```

必填参数：

- `--code`：股票代码，如 `000001.SZ`

常用参数：

- `--start-date`：开始日期
- `--end-date`：结束日期
- `--force-refresh`：忽略本地缓存并强制刷新

示例：

```bash
python run.py data update stock --code 000001.SZ --start-date 2024-01-01 --end-date 2024-03-31
```

### 批量更新股票

```bash
python run.py data update stocks
```

常用参数：

- `--start-date`：开始日期
- `--end-date`：结束日期
- `--limit`：仅处理前 N 只股票
- `--force-refresh`：忽略缓存并强制刷新
- `--resume`：兼容保留参数

示例：

```bash
python run.py data update stocks --limit 20
```

```bash
python run.py data update stocks --start-date 2024-01-01 --end-date 2024-03-31 --force-refresh
```

## 帮助命令

```bash
python run.py --help
python run.py data --help
python run.py factor run --help
python run.py ic --help
python run.py backtest run --help
```

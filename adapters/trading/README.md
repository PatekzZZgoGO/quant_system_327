# adapters/trading

Classification: `Trading-Owned Adapters`

当前目录用于承载明显偏交易运行域的适配器入口。

当前建议映射如下：

- `broker`
  - 券商接入、交易环境绑定和实盘执行相关适配
  - 更适合归入 trading adapters，而不是 shared adapters

当前阶段这里只提供分层入口与最小 mapping，不迁移原有 `adapters/broker`
目录中的实现文件。

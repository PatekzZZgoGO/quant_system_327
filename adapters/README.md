# adapters

Classification: `Boundary-Controlled`

当前目录同时包含 `local/`、`joinquant/` 与 `broker/`，共享性和交易环境绑定性并存。
它更像外部环境接入层，而不是稳定纯净的共享主干。
基于现状，适合按接口和具体适配器边界受控使用，不宜整体按共享主干承诺。

## Suggested Grouping

当前建议的过渡分层如下：

- `adapters/shared`
  - 暂时暴露 `local`
  - 暂时暴露 `joinquant`

- `adapters/trading`
  - 暂时暴露 `broker`

当前阶段先通过目录骨架与最小 re-export 明确 shared vs trading 的映射关系，
不迁移现有实现文件，不修改旧导入路径。

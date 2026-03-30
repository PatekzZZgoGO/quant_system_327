# adapters/shared

Classification: `Boundary-Controlled Shared Adapters`

当前目录用于承载“可受控共享”的适配器入口，而不是立即迁移全部旧实现。

当前建议映射如下：

- `local`
  - 本地模拟 / 本地运行支撑
  - 可同时服务研究验证与部分共享分析路径
  - 适合作为 shared adapters 暂时暴露

- `joinquant`
  - 特定平台接入层
  - 仍带明显平台绑定语义
  - 当前可作为 boundary-controlled shared adapters 暴露

当前阶段这里只提供分层入口与最小 mapping，不迁移原有 `adapters/local` 或
`adapters/joinquant` 目录中的实现文件。

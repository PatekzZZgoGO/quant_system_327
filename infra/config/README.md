# infra/config

当前配置体系正从单层配置向 `base / product / trading` 三层过渡。

现有 `settings.yaml` 仍作为兼容入口继续保留。
当前已存在的读取方式和现有行为暂不改变。

后续新增配置应优先按分层落位：

- `base/`：shared foundation config
- `product/`：signal product config
- `trading/`：trading system config

不建议继续把新配置长期混加到单一全局配置文件中。

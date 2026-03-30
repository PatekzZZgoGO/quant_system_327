# data/storage

`data/storage` 当前承载的是存储实现层。
它更接近 storage implementation / repository utilities。

仓库顶层的 `storage/` 承载的是业务产物与结果分区。
它更接近 artifact partitioning。

当前阶段两者并存：

- `data/storage/` 负责实现语义
- `storage/` 负责产物分区语义

后续会逐步建立两者之间的映射关系。

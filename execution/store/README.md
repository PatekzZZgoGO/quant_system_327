# execution/store

`execution/store` 当前是订单与成交相关的预留存储区。
目录骨架已经建立，但实际持久化链路仍较轻，当前更接近预留状态。

后续如果这里承载正式持久化结果，应逐步映射到顶层 `storage/trading_system/execution/` 对应分区。

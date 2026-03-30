# data/services

Classification: `Shared Foundation`

`data/services` 当前属于共享地基的一部分。
`DataService` 是面向上层的共享数据门面。
它的主要职责是提供稳定的数据访问语义和分析输入语义。
这包括统一访问 panel、universe，以及分析结果缓存入口。
它不应承载 `product` / `trading` 特定业务编排。
场景化窗口规则和业务装配应尽量停留在更上层。

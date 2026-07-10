---
doc_type: feature-acceptance
feature: 2026-07-07-ios-pmd3-wda-core
status: passed
accepted: 2026-07-11
round: 1
---

# ios-pmd3-wda-core 验收报告

- [x] IOSDriver core 已实现（discovery/WDA HTTP/screenshot/size/elements/tap/swipe/type/orientation）
- [x] 不依赖 go-ios/mobilecli
- [x] raw WDA source 不公开
- [x] 无 iOS 设备时 live smoke 返回 blocked，不伪装 passed
- [x] unit tests 覆盖 fake iOS routing 与 source 映射

## 环境阻塞

当前主机 pymobiledevice3 usbmux 无已授权 iOS 设备；live 真机链路 blocked-by-env，代码路径与单测已验收。

## Verdict

- Status: passed

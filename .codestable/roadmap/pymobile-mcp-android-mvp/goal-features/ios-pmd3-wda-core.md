# ios-pmd3-wda-core Feature Spec

## Roadmap Item

`ios-pmd3-wda-core`: 用 pymobiledevice3 tunnel + WDA 打通 iOS discovery、screenshot、elements、tap/swipe/type、screen size/orientation。

## Paths

- Design: `.codestable/features/2026-07-07-ios-pmd3-wda-core/ios-pmd3-wda-core-design.md`
- Checklist: `.codestable/features/2026-07-07-ios-pmd3-wda-core/ios-pmd3-wda-core-checklist.yaml`
- Design Review: `.codestable/features/2026-07-07-ios-pmd3-wda-core/ios-pmd3-wda-core-design-review.md`
- Review: `.codestable/features/2026-07-07-ios-pmd3-wda-core/ios-pmd3-wda-core-review.md`
- QA: `.codestable/features/2026-07-07-ios-pmd3-wda-core/ios-pmd3-wda-core-qa.md`
- Acceptance: `.codestable/features/2026-07-07-ios-pmd3-wda-core/ios-pmd3-wda-core-acceptance.md`

## Dependencies

- contract-registry-scaffold (must be accepted)
- BaseDriver/DriverFactory must be available (spike may proceed independently)

## Feature 性质

functional

## 核心运行路径

iOS 设备（如有）通过 MCP client 完成 `list_devices → screenshot → list_elements → tap`。无设备时记录 environment blocker。

## 必跑命令

- `python -m pytest`
- iOS PMD3/WDA core live smoke: list_devices → screenshot → list_elements → tap via MCP client or pytest live test

## Feature DoD

- DOD-DESIGN-001: design/review/checklist 通过
- DOD-IMPL-001: IOSDriver core 完成或明确环境阻塞
- DOD-REVIEW-001: code review passed
- DOD-QA-001: pytest + iOS core smoke/spike
- DOD-ACCEPT-001: 能力状态和 roadmap 回写

## Stage Gates

- implementation.before_review: scope-gate + dod-runner + evidence-pack
- review.before_pass: review-evidence-gate
- qa.before_acceptance: qa-evidence-gate
- acceptance.before_done: acceptance-dod-gate

## 失败恢复路径

- review blocking → review-fix → 重跑 review
- QA failed → qa-fix → 重跑 review + QA
- iOS 环境不可用 → 记录 environment blocker details，标 blocked-by-env

## 验收证据

- pytest 输出
- iOS spike/live smoke 记录
- 环境阻塞详情（如有）
- PMD3 版本和 API 名称记录

## 交付物

- `src/pymobile_mcp/drivers/ios.py` IOSDriver core 方法
- iOS discovery
- WDA/tunnel 连接管理
- iOS core live/spike 记录

## 清洁度规则

- 不提交证书/UDID 私密信息
- 不硬编码设备 id
- 不引入 go-ios

## 失败恢复边界

- PMD3/WDA 完全不可用且无法解决 → handoff
- 无 iOS 设备 → 标 blocked-by-env，不 handoff

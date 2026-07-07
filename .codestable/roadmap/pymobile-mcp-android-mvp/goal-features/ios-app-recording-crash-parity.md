# ios-app-recording-crash-parity Feature Spec

## Roadmap Item

`ios-app-recording-crash-parity`: 在 iOS core driver 基础上补 app lifecycle、recording/crash 能力或稳定 unsupported 行为。

## Paths

- Design: `.codestable/features/2026-07-07-ios-app-recording-crash-parity/ios-app-recording-crash-parity-design.md`
- Checklist: `.codestable/features/2026-07-07-ios-app-recording-crash-parity/ios-app-recording-crash-parity-checklist.yaml`
- Design Review: `.codestable/features/2026-07-07-ios-app-recording-crash-parity/ios-app-recording-crash-parity-design-review.md`
- Review: `.codestable/features/2026-07-07-ios-app-recording-crash-parity/ios-app-recording-crash-parity-review.md`
- QA: `.codestable/features/2026-07-07-ios-app-recording-crash-parity/ios-app-recording-crash-parity-qa.md`
- Acceptance: `.codestable/features/2026-07-07-ios-app-recording-crash-parity/ios-app-recording-crash-parity-acceptance.md`

## Dependencies

- ios-pmd3-wda-core (must be accepted)

## Feature 性质

functional

## 核心运行路径

iOS 设备上 app lifecycle / recording / crash 工具要么可用，要么返回 stable unsupported_platform。

## 必跑命令

- `python -m pytest`
- iOS app/recording/crash smoke or unsupported checks

## Feature DoD

- DOD-DESIGN-001: design/review/checklist 通过
- DOD-IMPL-001: iOS parity 分支实现或 stable unsupported
- DOD-REVIEW-001: code review passed
- DOD-QA-001: pytest + iOS parity smoke/spike
- DOD-ACCEPT-001: 能力状态和 roadmap 回写

## Stage Gates

- implementation.before_review: scope-gate + dod-runner + evidence-pack
- review.before_pass: review-evidence-gate
- qa.before_acceptance: qa-evidence-gate
- acceptance.before_done: acceptance-dod-gate

## 失败恢复路径

- review blocking → review-fix → 重跑 review
- QA failed → qa-fix → 重跑 review + QA
- PMD3 无能力 → 落 unsupported_platform，不阻塞

## 验收证据

- pytest 输出
- iOS capability spike 记录
- 能力矩阵候选
- no go-ios 验证

## 交付物

- IOSDriver app/recording/crash 方法或 unsupported 分支
- capability spike 记录
- 能力矩阵候选

## 清洁度规则

- 不引入 go-ios/mobilecli
- 不提交设备私密 crash 内容
- 不硬编码 bundle id

## 失败恢复边界

- PMD3 完全无相关能力 → 落 unsupported，不 handoff
- iOS 环境不可用 → 标 blocked-by-env

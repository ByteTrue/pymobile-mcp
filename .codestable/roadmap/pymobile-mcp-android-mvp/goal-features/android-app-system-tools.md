# android-app-system-tools Feature Spec

## Roadmap Item

`android-app-system-tools`: 补齐 Android app lifecycle、orientation、button、open_url、save_screenshot 等非 recording 系统工具。

## Paths

- Design: `.codestable/features/2026-07-07-android-app-system-tools/android-app-system-tools-design.md`
- Checklist: `.codestable/features/2026-07-07-android-app-system-tools/android-app-system-tools-checklist.yaml`
- Design Review: `.codestable/features/2026-07-07-android-app-system-tools/android-app-system-tools-design-review.md`
- Review: `.codestable/features/2026-07-07-android-app-system-tools/android-app-system-tools-review.md`
- QA: `.codestable/features/2026-07-07-android-app-system-tools/android-app-system-tools-qa.md`
- Acceptance: `.codestable/features/2026-07-07-android-app-system-tools/android-app-system-tools-acceptance.md`

## Dependencies

- android-live-ui-slice (must be accepted)

## Feature 性质

functional

## 核心运行路径

Android 真机上 list_apps、open_url(http)、press_button(BACK/HOME)、orientation get/set、save_screenshot 到安全路径。

## 必跑命令

- `python -m pytest`
- Android app/system live smoke via MCP tools

## Feature DoD

- DOD-DESIGN-001: design/review/checklist 通过
- DOD-IMPL-001: Android app/system handlers 完成
- DOD-REVIEW-001: code review passed
- DOD-QA-001: pytest + Android app/system smoke 通过或明确 blocked
- DOD-ACCEPT-001: 能力状态和 roadmap 回写

## Stage Gates

- implementation.before_review: scope-gate + dod-runner + evidence-pack
- review.before_pass: review-evidence-gate
- qa.before_acceptance: qa-evidence-gate
- acceptance.before_done: acceptance-dod-gate

## 失败恢复路径

- review blocking → review-fix → 重跑 review
- QA failed → qa-fix → 重跑 review + QA
- install/uninstall 无测试 APK → QA 标 blocked，不阻塞其他工具

## 验收证据

- pytest 输出
- live smoke 步骤/输出
- 安全路径测试证据
- saved screenshot path

## 交付物

- AndroidDriver app/system 方法
- path/url validation utilities
- destructive annotation on install/uninstall
- live smoke 说明

## 清洁度规则

- 不硬编码 package name
- 不提交临时截图
- 不绕过 path 校验

## 失败恢复边界

- 无测试 APK 做 install/uninstall smoke → 标 blocked，handoff 让用户提供

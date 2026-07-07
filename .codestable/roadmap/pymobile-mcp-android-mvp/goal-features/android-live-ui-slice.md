# android-live-ui-slice Feature Spec

## Roadmap Item

`android-live-ui-slice`: 用已连接 Android 真机跑通 list_devices → screen_size → screenshot → elements → tap/swipe/type 最小闭环。

## Paths

- Design: `.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-design.md`
- Checklist: `.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-checklist.yaml`
- Design Review: `.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-design-review.md`
- Review: `.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-review.md`
- QA: `.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-qa.md`
- Acceptance: `.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-acceptance.md`

## Dependencies

- contract-registry-scaffold (must be accepted)

## Feature 性质

functional

## 核心运行路径

Android 真机通过 MCP client 完成 `list_devices → screen_size → screenshot → list_elements → click → swipe → type_keys`。

## 必跑命令

- `python -m pytest`
- Android live smoke: `list_devices → screen_size → screenshot → list_elements → click → swipe → type_keys` via MCP client or pytest live test

## Feature DoD

- DOD-DESIGN-001: design/review/checklist 通过
- DOD-IMPL-001: Android UI driver 和 handlers 完成
- DOD-REVIEW-001: code review passed
- DOD-QA-001: pytest + Android live smoke 通过
- DOD-ACCEPT-001: 最小闭环证据和 roadmap 回写

## Stage Gates

- implementation.before_review: scope-gate + dod-runner + evidence-pack
- review.before_pass: review-evidence-gate
- qa.before_acceptance: qa-evidence-gate
- acceptance.before_done: acceptance-dod-gate

## 失败恢复路径

- review blocking → review-fix → 重跑 review
- QA failed → qa-fix → 重跑 review + QA
- 设备不可用 → blocked，handoff 等用户连接设备

## 验收证据

- pytest 输出
- live smoke device id / 步骤 / 结果
- screenshot 证据
- elements JSON 输出

## 交付物

- `src/pymobile_mcp/drivers/android.py` AndroidDriver
- Android device discovery
- 核心 UI tool handlers（screenshot, elements, tap, double_tap, long_press, swipe, type_keys）
- live smoke 说明

## 清洁度规则

- 不硬编码用户设备 id
- 不在 registry 层 import uiautomator2
- 不提交临时截图文件

## 失败恢复边界

- 设备不可用且用户无法提供 → handoff
- uiautomator2 API 不兼容 → handoff

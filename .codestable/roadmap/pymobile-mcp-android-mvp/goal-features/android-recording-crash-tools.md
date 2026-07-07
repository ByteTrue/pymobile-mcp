# android-recording-crash-tools Feature Spec

## Roadmap Item

`android-recording-crash-tools`: 实现 Android screen recording，crash 工具给出可靠实现或稳定 unsupported。

## Paths

- Design: `.codestable/features/2026-07-07-android-recording-crash-tools/android-recording-crash-tools-design.md`
- Checklist: `.codestable/features/2026-07-07-android-recording-crash-tools/android-recording-crash-tools-checklist.yaml`
- Design Review: `.codestable/features/2026-07-07-android-recording-crash-tools/android-recording-crash-tools-design-review.md`
- Review: `.codestable/features/2026-07-07-android-recording-crash-tools/android-recording-crash-tools-review.md`
- QA: `.codestable/features/2026-07-07-android-recording-crash-tools/android-recording-crash-tools-qa.md`
- Acceptance: `.codestable/features/2026-07-07-android-recording-crash-tools/android-recording-crash-tools-acceptance.md`

## Dependencies

- android-live-ui-slice (must be accepted)

## Feature 性质

functional

## 核心运行路径

Android 真机上 start_recording → stop_recording 生成 MP4；crash tools 返回 implemented 或 unsupported_platform。

## 必跑命令

- `python -m pytest`
- Android recording smoke: start_recording → wait → stop_recording via MCP client, verify MP4 output
- Android crash spike: call list_crashes and verify implemented or unsupported_platform

## Feature DoD

- DOD-DESIGN-001: design/review/checklist 通过
- DOD-IMPL-001: recording 状态机和 crash 分支完成
- DOD-REVIEW-001: code review passed
- DOD-QA-001: pytest + Android recording/crash smoke/spike 完成
- DOD-ACCEPT-001: 能力状态和 roadmap 回写

## Stage Gates

- implementation.before_review: scope-gate + dod-runner + evidence-pack
- review.before_pass: review-evidence-gate
- qa.before_acceptance: qa-evidence-gate
- acceptance.before_done: acceptance-dod-gate

## 失败恢复路径

- review blocking → review-fix → 重跑 review
- QA failed → qa-fix → 重跑 review + QA
- crash spike 无可靠来源 → 落 unsupported_platform，不阻塞

## 验收证据

- pytest 输出
- recording 文件证据或错误
- crash spike 结论
- asyncio.Lock 并发测试

## 交付物

- AndroidDriver recording 方法
- ActiveRecording 状态机 + per-device lock
- crash 工具实现或 unsupported 分支
- recording/crash smoke 说明

## 清洁度规则

- 不遗留设备端临时 MP4
- 不硬编码 host path
- 不吞掉后台进程错误

## 失败恢复边界

- screenrecord 完全不可用 → handoff
- crash 无可靠来源 → 落 unsupported，不 handoff

# parity-hardening-docs Feature Spec

## Roadmap Item

`parity-hardening-docs`: 收口契约测试、live smoke 文档、README 能力状态表、安装/调试说明和已知限制。

## Paths

- Design: `.codestable/features/2026-07-07-parity-hardening-docs/parity-hardening-docs-design.md`
- Checklist: `.codestable/features/2026-07-07-parity-hardening-docs/parity-hardening-docs-checklist.yaml`
- Design Review: `.codestable/features/2026-07-07-parity-hardening-docs/parity-hardening-docs-design-review.md`
- Review: `.codestable/features/2026-07-07-parity-hardening-docs/parity-hardening-docs-review.md`
- QA: `.codestable/features/2026-07-07-parity-hardening-docs/parity-hardening-docs-qa.md`
- Acceptance: `.codestable/features/2026-07-07-parity-hardening-docs/parity-hardening-docs-acceptance.md`

## Dependencies

- android-app-system-tools (must be accepted)
- android-recording-crash-tools (must be accepted)
- ios-app-recording-crash-parity (must be accepted)

## Feature 性质

mixed

## 核心运行路径

README 能力矩阵准确反映 23 core tools × Android/iOS 状态；schema parity tests 通过；live smoke 文档可复跑。

## 必跑命令

- `python -m pytest`
- `python3 .codestable/tools/codestable-goal-consistency-gate.py --roadmap .codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-roadmap.md`
- `python3 .codestable/tools/validate-yaml.py --file .codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-items.yaml --yaml-only`
- available Android/iOS live smoke from README

## Feature DoD

- DOD-DESIGN-001: design/review/checklist 通过
- DOD-IMPL-001: README/tests/smoke docs 更新
- DOD-REVIEW-001: code review/docs review passed
- DOD-QA-001: aggregate checks 通过或 env blocker 明确
- DOD-ACCEPT-001: roadmap 最终收口输入齐全

## Stage Gates

- implementation.before_review: scope-gate + dod-runner + evidence-pack
- review.before_pass: review-evidence-gate
- qa.before_acceptance: qa-evidence-gate
- acceptance.before_done: acceptance-dod-gate

## 失败恢复路径

- review blocking → review-fix → 重跑 review
- QA failed → qa-fix → 重跑 review + QA
- 前置 feature 未 accepted → S0 blocked，等前置完成

## 验收证据

- README diff
- pytest 输出
- consistency gate 输出
- live smoke 证据/blocked 说明
- schema fixture source metadata
- knowledge candidates

## 交付物

- README 能力矩阵（23 tools × 2 platforms）
- 安装/配置说明
- live smoke 说明
- schema parity tests/fixture 收口
- 最终验证报告输入
- knowledge candidates 列表

## 清洁度规则

- 不复制大段源码
- 不提交设备私密信息
- 不写未经验证的成功声明

## 失败恢复边界

- 前置 feature 长期 blocked → handoff
- schema fixture drift 无法解决 → handoff

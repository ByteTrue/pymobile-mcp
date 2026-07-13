# Goal Feature Spec: release-0.3-black-box

## Roadmap binding
- roadmap: pymobile-mcp-productize-0.3
- roadmap_item: release-0.3-black-box
- feature_dir: `.codestable/features/2026-07-13-release-0.3-black-box/`
- design: `.codestable/features/2026-07-13-release-0.3-black-box/release-0.3-black-box-design.md` (**approved**)
- checklist: `.codestable/features/2026-07-13-release-0.3-black-box/release-0.3-black-box-checklist.yaml`
- design-review: `.codestable/features/2026-07-13-release-0.3-black-box/release-0.3-black-box-design-review.md` (passed)
- review: `.codestable/features/2026-07-13-release-0.3-black-box/release-0.3-black-box-review.md`
- qa: `.codestable/features/2026-07-13-release-0.3-black-box/release-0.3-black-box-qa.md`
- acceptance: `.codestable/features/2026-07-13-release-0.3-black-box/release-0.3-black-box-acceptance.md`

## 依赖
none

## 性质
non-functional

## 核心运行路径
none（发布元数据/文档）

## 必跑命令
CMD-001, CMD-REL-001, CMD-REL-002, CMD-BUNDLE-001

## Feature DoD / gates
- design approved + design-review passed（已满足）
- implementation → independent code-review → QA → acceptance
- review blocking → review-fix → re-review
- QA failed/blocked → qa-fix → re-run review/QA as needed
- gate inputs: design, checklist, scope/dod/evidence artifacts per goal-protocol-gates.md

## 验收证据
command outputs + Release body + clean bundle

## 交付物
version 0.3.0 triple, CHANGELOG/README/regression-checklist, tag+Release

## 清洁度
- no unrelated staged files
- no temp media in commit
- no go-ios / no public schema change
- pypi optional must not rewrite core complete

## 失败恢复边界
- do not expand into runtime features
- do not upgrade mobile-mcp pin in this epic unless user re-approves scope
- optional blocked/failed stays optional

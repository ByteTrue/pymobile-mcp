# Goal Feature Spec: exception-triage

## Roadmap binding
- roadmap: pymobile-mcp-productize-0.3
- roadmap_item: exception-triage
- feature_dir: `.codestable/features/2026-07-13-exception-triage/`
- design: `.codestable/features/2026-07-13-exception-triage/exception-triage-design.md` (**approved**)
- checklist: `.codestable/features/2026-07-13-exception-triage/exception-triage-checklist.yaml`
- design-review: `.codestable/features/2026-07-13-exception-triage/exception-triage-design-review.md` (passed)
- review: `.codestable/features/2026-07-13-exception-triage/exception-triage-review.md`
- qa: `.codestable/features/2026-07-13-exception-triage/exception-triage-qa.md`
- acceptance: `.codestable/features/2026-07-13-exception-triage/exception-triage-acceptance.md`

## 依赖
none

## 性质
non-functional

## 核心运行路径
none（决策文档）

## 必跑命令
CMD-001, CMD-TRIAGE-001

## Feature DoD / gates
- design approved + design-review passed（已满足）
- implementation → independent code-review → QA → acceptance
- review blocking → review-fix → re-review
- QA failed/blocked → qa-fix → re-run review/QA as needed
- gate inputs: design, checklist, scope/dod/evidence artifacts per goal-protocol-gates.md

## 验收证据
both EXC cases + decision fields; docs-only diff

## 交付物
docs/exception-triage-0.3.md

## 清洁度
- no unrelated staged files
- no temp media in commit
- no go-ios / no public schema change
- pypi optional must not rewrite core complete

## 失败恢复边界
- do not expand into runtime features
- do not upgrade mobile-mcp pin in this epic unless user re-approves scope
- optional blocked/failed stays optional

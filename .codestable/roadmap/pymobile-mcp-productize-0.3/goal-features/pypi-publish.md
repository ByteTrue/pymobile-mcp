# Goal Feature Spec: pypi-publish

## Roadmap binding
- roadmap: pymobile-mcp-productize-0.3
- roadmap_item: pypi-publish
- feature_dir: `.codestable/features/2026-07-13-pypi-publish/`
- design: `.codestable/features/2026-07-13-pypi-publish/pypi-publish-design.md` (**approved**)
- checklist: `.codestable/features/2026-07-13-pypi-publish/pypi-publish-checklist.yaml`
- design-review: `.codestable/features/2026-07-13-pypi-publish/pypi-publish-design-review.md` (passed)
- review: `.codestable/features/2026-07-13-pypi-publish/pypi-publish-review.md`
- qa: `.codestable/features/2026-07-13-pypi-publish/pypi-publish-qa.md`
- acceptance: `.codestable/features/2026-07-13-pypi-publish/pypi-publish-acceptance.md`

## 依赖
release-0.3-black-box

## 性质
non-functional

## 核心运行路径
none（optional 分发）

## 必跑命令
CMD-001, CMD-PYPI-001

## Feature DoD / gates
- design approved + design-review passed（已满足）
- implementation → independent code-review → QA → acceptance
- review blocking → review-fix → re-review
- QA failed/blocked → qa-fix → re-run review/QA as needed
- gate inputs: design, checklist, scope/dod/evidence artifacts per goal-protocol-gates.md

## 验收证据
status published|blocked-by-env|failed; optional only

## 交付物
.codestable/features/2026-07-13-pypi-publish/pypi-publish-status.md (+ optional workflow)

## 清洁度
- no unrelated staged files
- no temp media in commit
- no go-ios / no public schema change
- pypi optional must not rewrite core complete

## 失败恢复边界
- do not expand into runtime features
- do not upgrade mobile-mcp pin in this epic unless user re-approves scope
- optional blocked/failed stays optional

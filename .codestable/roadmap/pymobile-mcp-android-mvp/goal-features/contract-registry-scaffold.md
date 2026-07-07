# contract-registry-scaffold Feature Spec

## Roadmap Item

`contract-registry-scaffold`: 建立 Python 包骨架、MCP stdio server、23 个 mobile-mcp 常驻核心工具 registry、手写 schema parity fixture 和统一结构化错误。

## Paths

- Design: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-design.md`
- Checklist: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-checklist.yaml`
- Design Review: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-design-review.md`
- Review: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-review.md`
- QA: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-qa.md`
- Acceptance: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-acceptance.md`

## Dependencies

none

## Feature 性质

functional

## 核心运行路径

MCP server 启动后 `list_tools` 返回 23 个 core tools；`call_tool` 任一未实现工具返回结构化 `not_implemented` 错误。

## 必跑命令

- `python -m pytest`
- `python -m pip install -e .`
- `python -c 'from pymobile_mcp.cli import main'`

## Feature DoD

- DOD-DESIGN-001: design/review/checklist 通过
- DOD-IMPL-001: registry、stub、fixture、tests 落盘
- DOD-REVIEW-001: code review 无 unresolved blocking
- DOD-QA-001: contract tests 和 CLI smoke 通过
- DOD-ACCEPT-001: roadmap item 回写

## Stage Gates

- implementation.before_review: scope-gate + dod-runner + evidence-pack
- review.before_pass: review-evidence-gate
- qa.before_acceptance: qa-evidence-gate
- acceptance.before_done: acceptance-dod-gate

## Gate 输入产物

- evidence pack (Scope, DoD Results, Validation Commands, Scope And Cleanliness, Residual Risks)
- gate results (scope-gate, dod-runner, evidence-pack)
- review report
- QA report
- acceptance report

## 失败恢复路径

- review blocking → review-fix → 重跑 review
- QA failed → qa-fix → 重跑 review + QA
- acceptance blocking → 回 impl 修 → 重跑 review + QA + acceptance

## 验收证据

- pytest 输出
- schema fixture diff
- CLI import smoke 输出
- schema source revision 记录

## 交付物

- `src/pymobile_mcp/` 包（server, tools, drivers, errors, cli）
- `tests/` contract tests
- schema parity fixture

## 清洁度规则

- 不允许临时 debug print
- 不允许注释掉代码
- 不允许未使用 import
- 不允许额外公开工具（no page_source, no remote fleet）

## 失败恢复边界

- 同一失败项三轮修复仍不通过 → handoff
- MCP SDK API 不兼容 → handoff 让用户决定版本

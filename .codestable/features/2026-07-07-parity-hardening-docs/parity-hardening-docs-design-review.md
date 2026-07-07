---
doc_type: feature-design-review
feature: 2026-07-07-parity-hardening-docs
status: passed
reviewed: 2026-07-07
round: 1
---

# parity-hardening-docs feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-07-parity-hardening-docs/parity-hardening-docs-design.md`
- Checklist: `.codestable/features/2026-07-07-parity-hardening-docs/parity-hardening-docs-checklist.yaml`
- Roadmap: `.codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-roadmap.md`

### Independent Review

- Status: completed
- Detection: native-agent
- Provider / agent: builtin `reviewer` subagent
- Raw output: 1 blocking, 5 important, 1 nit, 1 suggestion, 1 learning, 3 praise
- Merge policy: 主 agent 已逐条核验并合并修复；blocking 已解决
- Gate effect: none

## 2. Design Summary

- Goal: 收口 parity 契约测试、README 能力矩阵、live smoke 文档、已知限制
- Key contracts: 矩阵只读 acceptance 事实、no not-applicable for core tools、schema fixture source metadata
- Steps: 6 步（依赖就绪检查 → 事实收集 → 能力矩阵 → 文档更新 → 聚合验证 → 收尾候选）
- Checks: 8 条（含新增 not-applicable 审计、schema fixture metadata、blocked-by-env probe evidence）

## 3. Findings

### blocking

- [x] FDR-001 依赖就绪检查缺失 → 已补 S0 步骤：验证所有前置 feature accepted/done，否则 blocked

### important

- [x] FDR-002 not-applicable 状态未定义 → 已改为不允许对 23 core tools 使用 not-applicable
- [x] FDR-003 schema fixture source metadata 未进 artifacts → 已补 schema_fixture_source_metadata 证据项
- [x] FDR-004 live smoke env blocker 证据标准偏松 → 已补 blocked-by-env probe evidence check
- [x] FDR-005 validate-yaml 未进 DoD → 已补 CMD-YAML-001
- [x] FDR-006 roadmap md vs yaml 状态漂移 → 已知，consistency gate 会捕获

### nit

- [x] FDR-007 README 现状描述不精确 → 接受，实现时审计现有 README 全部内容

### praise

- strict parity 边界把得住
- README claims 有反乐观约束
- final aggregate checks 覆盖核心命令

## 4. User Review Focus

- 用户需要重点拍板：not-applicable 是否完全禁止（当前设计禁止）
- implement 需要重点遵守：依赖就绪检查、矩阵只读 acceptance 事实
- code review / QA 需要重点复核：schema fixture source metadata、blocked-by-env probe

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | 5 场景覆盖 | none |
| DoD Contract | pass | E | 5 条 DoD + 4 条 Validation Commands | none |
| Steps and checks traceability | pass | E | 6 steps + 8 checks | none |
| Roadmap contract compliance | pass | E | no remote fleet, no page_source, consistency gate | none |
| Module interface design | n/a | E | 非功能性 feature | none |
| Validation and artifacts | pass | E | pytest + consistency gate + live smoke + yaml | none |

Summary: E=5, C=0, H=0, H-only core checks=none。

## 6. Residual Risk

- 矩阵准确性依赖所有前置 feature 的 acceptance 证据质量。
- schema fixture drift 需要持续维护。

## 7. Verdict

- Status: passed
- Next: 交给用户整体 review

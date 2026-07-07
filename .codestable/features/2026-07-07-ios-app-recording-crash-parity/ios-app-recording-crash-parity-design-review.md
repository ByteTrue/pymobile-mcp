---
doc_type: feature-design-review
feature: 2026-07-07-ios-app-recording-crash-parity
status: passed
reviewed: 2026-07-07
round: 1
---

# ios-app-recording-crash-parity feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-07-ios-app-recording-crash-parity/ios-app-recording-crash-parity-design.md`
- Checklist: `.codestable/features/2026-07-07-ios-app-recording-crash-parity/ios-app-recording-crash-parity-checklist.yaml`
- Roadmap: `.codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-roadmap.md`
- Code facts checked: `pyproject.toml`, `/Users/byte/workspace/forks/mobile-mcp/src/ios.ts`, `/Users/byte/workspace/forks/mobile-mcp/src/server.ts`

### Independent Review

- Status: completed
- Detection: native-agent
- Provider / agent: builtin `reviewer` subagent
- Raw output: 2 important, 1 suggestion, 1 nit, 1 learning, 2 praise
- Merge policy: 主 agent 已逐条核验并合并修复
- Gate effect: none

## 2. Design Summary

- Goal: iOS app lifecycle、recording/crash 能力补齐或稳定 unsupported
- Key contracts: PMD3 capability spike、stable unsupported 不伪造、no go-ios、schema 保持
- Steps: 5 步（capability spikes → app lifecycle → recording → crash → 能力矩阵候选）
- Checks: 7 条（含新增 recording path safety、no go-ios imports、locale? schema）

## 3. Findings

### blocking

none

### important

- [x] FDR-001 环境缺失 vs unsupported 区分不清 → 已改 design 明确：缺环境标 blocked-by-env，只有 spike 证明平台无能力才落 unsupported
- [x] FDR-002 recording path safety 未进 checklist → 已补 recording output path safety 检查

### suggestion

- [ ] RMR-001 加 no-go-ios dependency/import 检查命令

### nit

- [x] FDR-003 locale? 缺 → 已补 locale? 到 schema 保持列表和 check

### learning

- mobile-mcp iOS app lifecycle 依赖 go-ios，recording/crash 走 mobilecli；本项目禁止两者，必须用 PMD3 重新验证或 stable unsupported

### praise

- 不引入 go-ios/mobilecli
- schema 保持方向正确

## 4. User Review Focus

- 用户需要重点拍板：iOS 环境缺失时是否接受 blocked-by-env 而非 unsupported
- implement 需要重点遵守：capability spike 先行、no go-ios、recording path safety
- code review / QA 需要重点复核：PMD3 能力边界、unsupported 原因记录

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | 5 场景覆盖 | none |
| DoD Contract | pass | E | 5 条 DoD + 2 条 Validation Commands | none |
| Steps and checks traceability | pass | E | 5 steps + 7 checks | none |
| Roadmap contract compliance | pass | E | no go-ios, schema 保持, spike-first | none |
| Module interface design | pass | E | 复用 IOSDriver adapter | none |
| Validation and artifacts | pass | E | pytest + iOS parity smoke | none |

Summary: E=6, C=0, H=0, H-only core checks=none。

## 6. Residual Risk

- PMD3 app/recording/crash 能力边界只能靠真实环境 spike 验证。
- 当前仓库无 src/ 实现，设计阶段只能约束契约。

## 7. Verdict

- Status: passed
- Next: 交给用户整体 review

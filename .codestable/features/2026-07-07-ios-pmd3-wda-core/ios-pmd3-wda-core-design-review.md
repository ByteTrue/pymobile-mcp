---
doc_type: feature-design-review
feature: 2026-07-07-ios-pmd3-wda-core
status: passed
reviewed: 2026-07-07
round: 1
---

# ios-pmd3-wda-core feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-07-ios-pmd3-wda-core/ios-pmd3-wda-core-design.md`
- Checklist: `.codestable/features/2026-07-07-ios-pmd3-wda-core/ios-pmd3-wda-core-checklist.yaml`
- Roadmap: `.codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-roadmap.md`
- Code facts checked: `pyproject.toml`, `README.md`

### Independent Review

- Status: completed
- Detection: native-agent
- Provider / agent: builtin `reviewer` subagent
- Raw output: 2 important, 1 nit, 1 suggestion, 2 learning, 3 praise
- Merge policy: 主 agent 已逐条核验并合并修复
- Gate effect: none

## 2. Design Summary

- Goal: 用 pymobiledevice3 tunnel + WDA 打通 iOS 核心 UI 链路
- Key contracts: spike-first、no go-ios、raw source internal only、env blocker 不伪装通过
- Steps: 6 步（spike → 连接生命周期 → 只读能力 → elements → interactions → 证据）
- Checks: 6 条（含新增 environment_blocker_details 证据项）

## 3. Findings

### blocking

none

### important

- [x] FDR-001 隐含 DriverFactory 依赖未落 checklist → 已补 prerequisite: contract-registry-scaffold accepted + BaseDriver/DriverFactory available
- [x] FDR-002 live smoke DoD 不可复跑 → 已改 CMD-IOS-CORE-001 为具体 MCP tool 调用序列；已补 environment_blocker_details 证据项

### nit

- [x] FDR-003 状态字段轻微漂移 → 已知，items.yaml 为执行权威源

### suggestion

- [ ] RMR-001 spike notes 记录 PMD3 版本和真实调用 API 名称

### praise

- PMD3/WDA spike-first 做得对
- no go-ios / raw source internal only 边界一致
- iOS live blocker 不伪装通过

## 4. User Review Focus

- 用户需要重点拍板：iOS 环境缺失时的 blocked 处理策略
- implement 需要重点遵守：spike-first、no go-ios、env blocker 记录
- code review / QA 需要重点复核：PMD3 API 版本、WDA session 管理

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | 5 场景覆盖 | none |
| DoD Contract | pass | E | 5 条 DoD + 2 条 Validation Commands | none |
| Steps and checks traceability | pass | E | 6 steps + 6 checks | none |
| Roadmap contract compliance | pass | E | no go-ios, no page_source, spike-first | none |
| Module interface design | pass | E | IOSDriver adapter seam | none |
| Validation and artifacts | pass | E | pytest + iOS live smoke + env blocker | none |

Summary: E=6, C=0, H=0, H-only core checks=none。

## 6. Residual Risk

- PMD3 + WDA 真实可行性只能靠后续 live/spike 验证。
- DriverFactory/BaseDriver 可用性取决于前置 feature。

## 7. Verdict

- Status: passed
- Next: 交给用户整体 review

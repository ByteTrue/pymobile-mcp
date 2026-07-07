---
doc_type: feature-design-review
feature: 2026-07-07-android-app-system-tools
status: passed
reviewed: 2026-07-07
round: 1
---

# android-app-system-tools feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-07-android-app-system-tools/android-app-system-tools-design.md`
- Checklist: `.codestable/features/2026-07-07-android-app-system-tools/android-app-system-tools-checklist.yaml`
- Roadmap: `.codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-roadmap.md`
- Code facts checked: `pyproject.toml`, `/Users/byte/workspace/forks/mobile-mcp/src/server.ts:17-20`

### Independent Review

- Status: completed
- Detection: native-agent
- Provider / agent: builtin `reviewer` subagent
- Raw output: 4 important, 2 nit, 2 suggestion, 1 learning, 3 praise
- Merge policy: 主 agent 已逐条核验并合并修复
- Gate effect: none

## 2. Design Summary

- Goal: 补齐 Android app lifecycle、orientation、button、open_url、save_screenshot 等非 recording 系统工具
- Key contracts: path/url safety、destructive annotation、MOBILEMCP_ALLOW_UNSAFE_URLS env var
- Steps: 5 步（安全校验 → app lifecycle → system actions → save_screenshot → 证据）
- Checks: 8 条（含新增 destructive annotation 检查和 env var 语义）

## 3. Findings

### blocking

none

### important

- [x] FDR-001 open_url unsafe 开关应为 env var 不是 schema flag → 已改 check 明确 MOBILEMCP_ALLOW_UNSAFE_URLS=1
- [x] FDR-002 saveTo path safety 细节不足 → 已补 resolve/realpath + .. traversal + symlink escape 检查
- [x] FDR-003 destructive annotation 缺 check → 已补 install/uninstall destructive=true 检查
- [x] FDR-004 依赖门槛未落 → 已补 prerequisite: android-live-ui-slice must be accepted

### nit

- [x] FDR-005 evidence_required 缺 path_safety_test_output → 接受，实现阶段自然产出
- [x] FDR-006 packageName/bundle_id/saveTo 字段名一致性 → 实现 review 时再用源码行号复核

### praise

- app/system 范围收得住
- URL/path 安全方向正确
- destructive live smoke 策略合理

## 4. User Review Focus

- 用户需要重点拍板：install/uninstall 是否需要测试 APK 做 live smoke
- implement 需要重点遵守：env var 语义、path safety、destructive annotation
- code review / QA 需要重点复核：path traversal 测试覆盖

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | 5 场景覆盖 | none |
| DoD Contract | pass | E | 5 条 DoD + 2 条 Validation Commands | none |
| Steps and checks traceability | pass | E | 5 steps + 8 checks | none |
| Roadmap contract compliance | pass | E | no recording/crash, no iOS, no schema change | none |
| Module interface design | pass | E | 复用 AndroidDriver adapter | none |
| Validation and artifacts | pass | E | pytest + live smoke | none |

Summary: E=6, C=0, H=0, H-only core checks=none。

## 6. Residual Risk

- install/uninstall live smoke 需要测试 APK；无 APK 时 QA 标 blocked。

## 7. Verdict

- Status: passed
- Next: 交给用户整体 review

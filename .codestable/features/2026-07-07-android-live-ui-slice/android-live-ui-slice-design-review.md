---
doc_type: feature-design-review
feature: 2026-07-07-android-live-ui-slice
status: passed
reviewed: 2026-07-07
round: 1
---

# android-live-ui-slice feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-design.md`
- Checklist: `.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-checklist.yaml`
- Roadmap: `.codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-roadmap.md`
- Code facts checked: `pyproject.toml`, `README.md`

### Independent Review

- Status: completed
- Detection: native-agent
- Provider / agent: builtin `reviewer` subagent
- Raw output: 4 important, 1 nit, 2 suggestion, 1 learning, 3 praise
- Merge policy: 主 agent 已逐条核验并合并修复
- Gate effect: none

## 2. Design Summary

- Goal: 用已连接 Android 真机跑通 list_devices → screen_size → screenshot → elements → tap/swipe/type 最小闭环
- Key contracts: AndroidDriver seam、ScreenElement 字段对齐 mobile-mcp、live smoke 不 skip
- Steps: 6 步（discovery → screenshot/size → elements → coordinates → type → smoke evidence）
- Checks: 7 条（含新增 double_tap/long_press 覆盖和 elements 字段级断言）

## 3. Findings

### blocking

none

### important

- [x] FDR-001 依赖门槛未落 checklist → 已补 prerequisite: contract-registry-scaffold must be accepted
- [x] FDR-002 checklist 漏 double_tap/long_press → 已改 check 覆盖 tap/double_tap/long_press/swipe/type_keys
- [x] FDR-003 elements 字段覆盖弱 → 已补 type + coordinates + stable field semantics 检查
- [x] FDR-004 live smoke 不可复跑 → 已改 CMD-ANDROID-001 为具体 MCP tool 调用序列

### nit

- [x] FDR-005 roadmap md vs items 状态不一致 → 已知，items.yaml 为执行权威源

### suggestion

- [ ] RMR-001 coordinate step 退出信号细化为每个 tool 一条证据
- [ ] RMR-002 no page_source public tool 留最小 contract test

### praise

- live smoke 与 unit/contract 明确区分
- AndroidDriver seam 放置合理
- 范围控制清楚

## 4. User Review Focus

- 用户需要重点拍板：live smoke 的具体设备/页面选择
- implement 需要重点遵守：elements 字段级契约、no page_source
- code review / QA 需要重点复核：double_tap/long_press handler 覆盖

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | 5 场景覆盖 | none |
| DoD Contract | pass | E | 5 条 DoD + 2 条 Validation Commands | none |
| Steps and checks traceability | pass | E | 6 steps + 7 checks | none |
| Roadmap contract compliance | pass | E | no page_source, no iOS, no recording | none |
| Module interface design | pass | E | AndroidDriver adapter seam | none |
| Validation and artifacts | pass | E | pytest + live smoke 具体序列 | none |

Summary: E=6, C=0, H=0, H-only core checks=none。

## 6. Residual Risk

- uiautomator2 screenshot/source 行为、坐标误触、非 ASCII 输入稳定性只能靠真机验证。

## 7. Verdict

- Status: passed
- Next: 交给用户整体 review

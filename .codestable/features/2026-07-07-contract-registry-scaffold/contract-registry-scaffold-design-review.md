---
doc_type: feature-design-review
feature: 2026-07-07-contract-registry-scaffold
status: passed
reviewed: 2026-07-07
round: 1
---

# contract-registry-scaffold feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-design.md`
- Checklist: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-checklist.yaml`
- Roadmap: `.codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-roadmap.md`
- Code facts checked: `pyproject.toml`, `/Users/byte/workspace/forks/mobile-mcp/src/server.ts`

### Independent Review

- Status: completed
- Detection: native-agent
- Provider / agent: builtin `reviewer` subagent
- Raw output: 4 important, 2 nit, 1 suggestion, 1 learning, 2 praise
- Merge policy: 主 agent 已逐条核验并合并修复
- Gate effect: none

## 2. Design Summary

- Goal: 建立 Python MCP 包骨架、23 个 mobile-mcp 常驻工具 registry、schema parity fixture 和统一错误语义
- Key contracts: ToolSpec + handler、structured error envelope、schema parity fixture
- Steps: 5 步（包骨架 → manifest → stub → schema parity → 错误转换）
- Checks: 6 条（含新增 schema source revision 检查）
- Baseline / validation: `python -m pytest`、`python -m pip install -e .`、CLI import smoke

## 3. Findings

### blocking

none

### important

- [x] FDR-001 CLI smoke 未在 DoD/checklist 落地 → 已补 CMD-003 `python -c 'from pymobile_mcp.cli import main'`
- [x] FDR-002 "任意未实现工具稳定失败"验收未覆盖全部 23 工具 → 已改 exit_signal 为遍历所有 23 个注册工具
- [x] FDR-003 schema fixture 缺参考源码 revision 记录 → 已补 schema_source_revision 证据项和检查
- [x] FDR-004 roadmap md vs items.yaml 状态漂移 → 已知，items.yaml 为执行权威源，md 在 acceptance 回写时同步

### nit

- [x] FDR-005 checklist source 标签不可追溯 → 接受，后续实现阶段可细化
- [x] FDR-006 S2/S4 边界重叠 → 接受，实现时自然区分

### suggestion

- [ ] RMR-001 保持 manifest/fixture 单一事实源，不加生成器

### learning

- mobile-mcp 参考源码实际 26 个工具注册名，3 个 remote 受 MOBILEFLEET_ENABLE 控制，核心 23 个

### praise

- 需求边界与 roadmap 大方向一致
- YAML 校验通过

## 4. User Review Focus

- 用户需要重点拍板：schema parity fixture 手写 vs 后续 codegen 的时机
- implement 需要重点遵守：23 工具全量 not_implemented 覆盖、schema source revision 记录
- code review / QA / acceptance 需要重点复核：schema fixture 与 server.ts 的一致性

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3 覆盖 4 场景 | none |
| DoD Contract | pass | E | 5 条 DoD + 3 条 Validation Commands | none |
| Steps and checks traceability | pass | E | 5 steps + 6 checks 可追溯到 design | none |
| Roadmap contract compliance | pass | E | 不公开 page_source、不含 remote fleet | none |
| Module interface design | pass | E | ToolSpec + handler seam 清楚 | none |
| Validation and artifacts | pass | E | pytest + install + CLI smoke | none |

Summary: E=6, C=0, H=0, H-only core checks=none。

## 6. Residual Risk

- 手写 schema fixture 依赖人工对照 server.ts，需记录参考 revision 防 drift。

## 7. Verdict

- Status: passed
- Next: 交给用户整体 review

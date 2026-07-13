---
doc_type: roadmap-review
slug: pymobile-mcp-productize-0.3
status: passed
round: 2
created: 2026-07-13
reviewer: independent-task-agent
local_merge: true
---

# pymobile-mcp-productize-0.3 Roadmap Review

## 结论

**passed**（round 2）

独立 reviewer round 1：`changes-requested`（6 条 important）。  
主 agent 修订 roadmap / items / goal-plan 后，独立 reviewer round 2：**passed**，blocking/important = 0。

## 审查范围

- `.codestable/roadmap/pymobile-mcp-productize-0.3/pymobile-mcp-productize-0.3-roadmap.md`
- `.codestable/roadmap/pymobile-mcp-productize-0.3/pymobile-mcp-productize-0.3-items.yaml`
- `.codestable/roadmap/pymobile-mcp-productize-0.3/goal-plan.md`
- CONTEXT / ADR-001 / ADR-002 / compound deterministic-bundle
- 当前 release 面：`0.2.0`、CI unit-only、scripts/* oracle 入口

## Round 1 important → Round 2 状态

| # | 项 | 状态 |
|---|---|---|
| 1 | core vs optional DoD；PyPI blocked 不污染 complete | 解除 |
| 2 | 版本三元一致 pyproject + `__version__` + tag/Release | 解除 |
| 3 | parity 策略可观察（0.3 不 re-capture；升 pin 才 CMD-002~008） | 解除 |
| 4 | DAG 与 items 一致 | 解除 |
| 5 | release 切割面含 CHANGELOG / README / regression-checklist | 解除 |
| 6 | live 策略写死 | 解除 |

## Findings（最终）

### blocking

无

### important

无

### nit

1. goal-plan Core complete 列表可把 `CMD-ORACLE-001` 写成显式第 6 条（意图已由 playbook accepted 信号覆盖）。
2. playbook 实现时统一 env 名，避免 `MOBILE_MCP_SOURCE` 与测试侧 `PYMOBILE_MCP_UPSTREAM_SOURCE` 双名。

### suggestion

1. release 执行时别漏 Unreleased→0.3.0 切割与 README / regression-checklist 版本头。
2. optional PyPI `blocked-by-env` 书面记录固定路径，避免口头 blocked。

### residual-risk

1. 默认 live 不阻塞 tag：无设备时 dual-device 回归可能推后（已写明的产品选择）。
2. 0.3 轻量门（pytest 内嵌 black-box + clean bundle）≠ 全量 CMD-005/006 re-assert；升 pin 才全量。
3. PyPI 可能 optional-blocked，不影响 core complete。

### praise

- 范围克制：无 runtime/schema 变更；exception 只 triage。
- 与 ADR / deterministic-bundle 一致。
- DoD 防污染清楚。

## Evidence Confidence Ledger

| 判断 | 级别 | 依据 |
|---|---|---|
| 范围与明确不做 | E | roadmap §2 |
| Core/Optional DoD | E | roadmap §5 + goal-plan complete 定义 |
| 版本三元一致 | E | CMD-REL-001 + items notes |
| parity 策略 | E+C | roadmap §5 + compound + black-box feature |
| DAG | E | items.yaml depends_on |
| 无 runtime 接口变更 | E | roadmap §2/§3 |

## 下一步

HumanCheckpoint：**ConfirmRoadmap**  
用户确认本 epic 规划后，进入子 feature design batch（仍不实现 runtime）。

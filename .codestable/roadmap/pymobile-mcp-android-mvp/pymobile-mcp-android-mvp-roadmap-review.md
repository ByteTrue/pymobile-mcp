---
doc_type: roadmap-review
roadmap: pymobile-mcp-android-mvp
status: passed
reviewed: 2026-07-07
round: 2
---

# pymobile-mcp-android-mvp roadmap 审查报告

## 1. Scope And Inputs

- Roadmap: `.codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-roadmap.md`
- Items: `.codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-items.yaml`
- Related docs: `.codestable/brainstorms/pymobile-mcp-android-mvp/brainstorm.md`, `KICKOFF.md`, `pyproject.toml`, `README.md`
- Code facts checked: `/Users/byte/workspace/forks/mobile-mcp/src/server.ts`, `/Users/byte/workspace/forks/mobile-mcp/src/robot.ts`, `/Users/byte/workspace/forks/mobile-mcp/src/android.ts`, `/Users/byte/workspace/forks/mobile-mcp/src/ios.ts`

### Independent Review

- Status: completed
- Detection: native-agent
- Provider / agent: builtin `reviewer` subagent
- Raw output: round 2 复审确认 roadmap/items 已改成 strict mobile-mcp parity；指出 2 个 important 和 2 个 nit，均已修复。
- Merge policy: 主 agent 已逐条核验并合并修复：KICKOFF 不再作为契约来源；Goal Coverage 列名改成 roadmap critical；`elements/source` wording 改为内部 source；旧 review artifact 已覆盖。
- Gate effect: none，允许进入用户 review。

## 2. Roadmap Summary

- Goal completion signal: MCP 工具契约稳定；Android 真机能跑通 `list_devices → screen_size → screenshot → elements → tap/swipe/type`；后续补 Android 周边、iOS、文档和 parity hardening。
- Module split: MCP Server / Tool Registry、Tool Execution Layer、Driver Contract、Android Driver、iOS Driver、Verification / Docs。
- Interface contracts: `ToolSpec + handler`、`BaseDriver` async contract、`DriverFactory`、23 个 mobile-mcp 常驻核心工具 schema、结构化错误 envelope、recording 状态。
- Items: 7 条；最小闭环是 `android-live-ui-slice`；高风险点是 `ios-pmd3-wda-core`。
- Dependency shape: DAG，无循环；Android MVP 不依赖 iOS。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- [ ] RMR-001 `parity-hardening-docs` 后续可把 mobile-mcp 源码工具 schema 固化成小型 fixture/快照，避免人工对齐 drift。
  - Evidence: roadmap 已要求 `contract-registry-scaffold` 做 schema parity fixture，最终 hardening 做能力矩阵。
  - Impact: 非阻塞，只是降低后续维护成本。

### learning

- mobile-mcp 源码基准是 23 个常驻 core tools；3 个 remote tools 受 `MOBILEFLEET_ENABLE` 控制；源码没有公开 `mobile_get_page_source`。
- raw XML / WDA source 是元素过滤的内部实现输入；对外只暴露 `mobile_list_elements_on_screen`。
- Kickoff 只保留技术栈背景，不作为额外工具契约来源。

### praise

- 已移除公开 `mobile_get_page_source` extension，roadmap 回到 strict mobile-mcp parity。
- 23 个常驻 core tools vs remote fleet 条件工具边界清楚。
- Android-first 最小闭环清晰，不被 iOS/WDA 和 recording/crash 风险拖住。
- 接口 seam 放置合理：MCP registry 不直接调用设备库，工具层只依赖 driver contract，Android/iOS driver 是真实 adapters。
- `items.yaml` 校验通过，且最小闭环只有一条。

## 4. User Review Focus

- 用户需要重点拍板：是否接受 strict mobile-mcp parity（不公开 `mobile_get_page_source`）；是否接受 Android-first 排期；是否接受 iOS/WDA 延后到独立高风险条目。
- 后续 feature-design 需要重点复核：23 个常驻 core tools 的 schema parity fixture；Android live smoke 可复跑步骤；iOS `pymobiledevice3 + WDA` 最小 spike。
- 不能靠 roadmap review 完全确认的点：真实 iOS tunnel/WDA 行为、Android 非 ASCII 输入体验、Android crash report 的可靠来源。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Granularity Gate | pass | E | roadmap 第 2 节说明跨 MCP/driver/test/docs 多交付，非 single feature；brainstorm + owner 最新修正确认 strict parity。 | none |
| Goal Coverage Matrix | pass | E | roadmap 第 5 节矩阵把每个完成信号映射到 item、验证入口和证据类型；列名已避免混淆 core contract。 | none |
| DAG and minimal loop | pass | E | items.yaml 依赖为 acyclic；`android-live-ui-slice` 是唯一 `minimal_loop: true`。 | none |
| Interface contract usability | pass | C | roadmap 第 4 节有 ToolSpec、BaseDriver、DriverFactory、公开工具 schema 与错误 envelope；对照 mobile-mcp `server.ts` 字段修订。 | feature-design 固化 fixture |
| Module interface depth | pass | E/C | roadmap 第 3/4 节说明 seam placement、dependency strategy、adapter 结论；Android/iOS 是真实 adapters。 | none |

Summary: E=4, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- iOS `pymobiledevice3 + WdaServiceClient` 路线必须靠后续 live/spike 证明；当前 roadmap 已隔离为 `ios-pmd3-wda-core`，不阻塞 Android MVP。
- Android live smoke 依赖本机 ADB/uiautomator2 和已授权真机；后续 acceptance 不能把 skip 当通过。
- Android 非 ASCII 输入和 crash report 来源可能需要额外沉淀或降级策略。
- 手写 schema parity fixture 需要固定 mobile-mcp 源码版本或快照，避免源码上游变动导致人工 drift。

## 7. Verdict

- Status: passed
- Next: 交给用户 review；用户确认后由 `cs-roadmap` 将 roadmap 从 `draft` 标为 `active`。

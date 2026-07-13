---
doc_type: feature-design-review
feature: 2026-07-12-mobile-mcp-black-box-contract-parity
status: passed
reviewed: 2026-07-12
round: 9
reviewer: subagent
---

# mobile-mcp-black-box-contract-parity feature design 审查报告

> Historical design-gate report：pending exception language below records the pre-approval review state；the current approved exception ledger and lifecycle artifacts supersede that status.

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-design.md`
- Checklist: `.codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-checklist.yaml`
- Scenario manifest: `.codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-scenarios.yaml`
- Exception ledger: `.codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-exceptions.yaml`
- Upstream facts: `/Users/byte/workspace/forks/mobile-mcp/src/server.ts`、`image-utils.ts`、`utils.ts`、Android/iOS/WDA runtime @ `c5d7d27fd61e4762e15ae4b1c68b6c011be88bb7`

### Independent Review

- Status: completed
- Detection: native-agent
- Provider / agent: builtin `reviewer` subagent，fresh context
- Review rounds: 9
- Final verdict: passed
- Gate effect: 进入用户整体 design checkpoint；不得自动 approved

## 2. Design Summary

- Goal: 除实现栈外，MCP `initialize`、default/fleet tool discovery、工具提示词/schema、逐公开 return branch、错误/`isError`、image condition modes、设备类型分支与 Pi/live 用户路径均复用固定上游黑盒契约。
- Fixed upstream: commit `c5d7d27...`，tag `0.0.61`，wire advertised version `0.0.1`，SDK `1.26.0`。
- Scenarios: 91 个唯一 cases（4 wire、57 call、30 validation/error）。
- Commands: CMD-001~008；统一 timeout、machine report、raw frames/fixtures，exit 2 视为 blocked。
- Exceptions: remote fleet 成功 runtime 与 iOS real-device recording 两项具体提案，均为 `approval: pending`。

## 3. Findings

### blocking

none

### important

none

### 已解决的主要 findings

- [x] 完整 `initialize/serverInfo` 与 default/fleet `list_tools` golden。
- [x] 每个 public return/validation/error/backend branch 均有 source-linked scenario。
- [x] ActionableError / unexpected error / screenshot error 的 content 与 `isError` 语义。
- [x] sips/ImageMagick/fallback/no-scaling 与 PSNR/artifact gate。
- [x] timeLimit/swipe/coercion 的 callback 与 Android ADB/iOS WDA backend effects。
- [x] exception ledger 的 allowed case 双向集合、platform/device type、approval enum 和 machine consumption。
- [x] deterministic oracle bundle 的逐文件 SHA 与 aggregate 算法。
- [x] Android physical 对外 `type=emulator` 的固定上游兼容行为。
- [x] iOS Simulator discovery、WDA representative runtime 与 `simctl` recording exact path；不扩大 real-device recording exception。
- [x] Pi 使用新会话自然 direct tools，不走 generic MCP gateway。

## 4. User Review Focus

用户需要明确拍板：

1. 是否批准整个 design。
2. `EXC-REMOTE-FLEET-RUNTIME`：默认 23 tools 无差异；fleet env 的 3 tools / 4 success cases 暂无 Python fleet provider，调用时返回上游 mobilecli-unavailable ActionableError 文本。
3. `EXC-IOS-SCREEN-RECORDING-RUNTIME`：仅 iOS real device start/stop；工具/schema 不变，runtime 返回纯 pmd3/WDA 暂不支持的 ActionableError 文本。

若任一 exception 被拒绝，对应成功 runtime 会成为 blocking implementation scope；不能回退到当前 JSON `unsupported_platform` envelope。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Spec/checklist traceability | pass | E | 8 steps、16+ checks、91 cases | implementation evidence |
| Initialize/default/fleet discovery | pass | E | raw frame + golden commands | CMD-002/003/005/006 |
| Call result/error/image coverage | pass | E | source-linked exhaustive manifest | CMD-001/004/008 |
| Source/guard/backend coverage | pass | E | 36+ required groups + CMD-007 | implement validator |
| Exception scope | pass | E | ledger/case refs 双向一致 | user approve/reject |
| Android/iOS device types | pass | E | physical/simulator cases | live QA |
| Pi user path | pass | E | natural direct-tools manual gate | PI-001 |

Summary: E=7, C=0, H=0, H-only core checks=none。

## 6. Residual Risk

- 两项 exception 未获用户批准前，implementation/QA/acceptance 必须保持 blocked disposition，不能宣称 full exact parity。
- capture/assert/source/image scripts 尚未实现；design passed 只证明方案可执行，不预先证明 runtime parity。
- iOS Simulator exact path依赖本机 Xcode `simctl` 和 simulator WDA；环境缺失为 blocked，不是 pass。

## 7. Verdict

- Status: passed
- Next: 用户整体 review design + 两项 exception；确认后将 design 标记 approved，进入 goal package / implementation worktree。

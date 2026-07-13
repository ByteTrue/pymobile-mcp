---
doc_type: feature-acceptance
feature: 2026-07-12-mobile-mcp-black-box-contract-parity
status: passed
accepted: 2026-07-13
round: 1
---

# mobile-mcp-black-box-contract-parity 验收报告

> 阶段：最终验收（用户已确认）  
> 验收日期：2026-07-13  
> 关联方案：`mobile-mcp-black-box-contract-parity-design.md`

## 1. 接口契约核对

- [x] `initialize`：`serverInfo.name=mobile-mcp`、`version=0.0.1`、capabilities、旧/非法 protocol negotiation 与固定上游一致。
- [x] Default discovery：23 tools；fleet discovery：26 tools；完整 tool object（name/title/description/schema/annotations）deep-equal。
- [x] CallToolResult：自然语言、JSON text、image content、Actionable error、unexpected error、`isError` 省略/true 均按固定上游 wire 行为输出。
- [x] 成功/错误输入域：JS/Zod number coercion、聚合 issues、URL raw-prefix、unknown tool、截图与 recording 边界均有 raw stdio golden。
- [x] `mobile_get_page_source` 未公开；fleet 只在 `MOBILEFLEET_ENABLE=1` 暴露三项工具。

## 2. 行为与决策核对

- [x] 唯一事实源固定为 `mobile-mcp@c5d7d27fd61e4762e15ae4b1c68b6c011be88bb7`；lock、Node、npm、SDK、命令与 raw frames 均留 provenance。
- [x] Python 只替换实现栈；默认对外 contract 不改。
- [x] `EXC-REMOTE-FLEET-RUNTIME` 仅覆盖 3 tools / 4 success cases。
- [x] `EXC-IOS-SCREEN-RECORDING-RUNTIME` 仅覆盖 iOS real start/stop；Simulator recording 为真实 `simctl` 实现。
- [x] deterministic bundle 为 fail-closed：manifest、CMD-004 report、call golden、CMD-005~008 均为 `952c55cf10c45ce35857016a70639ea3cc4377b5bea31bd3b30cb57c06a1889c`。
- [x] call golden provenance 不匹配时在启动 stdio 前失败；有独立 negative regression。
- [x] 挂载点与 design 2.3 一致：server/stdio、registry/specs/formatter/errors、Android/iOS/Simulator drivers、oracle scripts/fixtures/tests、docs/evidence。
- [x] 反向 grep / 拔除推演：移除新增 contract/oracle 层会恢复旧 Python envelope；没有清单外 runtime fallback 或 page-source registration。
- [x] Runtime 不引入 go-ios / mobilecli fallback；`mobilecli` 只出现在 approved exception 文案与上游 oracle fixture。

## 3. 验收场景核对

- [x] pytest：107 passed。
- [x] CMD-002/003：upstream default 23 / fleet 26。
- [x] CMD-004：47 source-linked upstream call captures；完整 bundle provenance 已记录。
- [x] CMD-005：default 23 tools / 106 stdio scenarios。
- [x] CMD-006：fleet 26 tools / 110 stdio scenarios。
- [x] CMD-007：91/91 source-linked scenarios，100% disposition coverage。
- [x] CMD-008：Sips / ImageMagick / fallback 三种 backend passed；scenario 声明的九个 artifact 路径均存在；strict JSON 用字符串 `"Infinity"` 表示无穷 PSNR。
- [x] LIVE-001：Android physical、Android emulator、iOS Simulator、iOS real 共 16/16 sub-smokes passed。
- [x] PI-001：Pi 0.80.6 fresh session direct tools 覆盖 text、image、action、actionable error。
- [x] Review Test And QA Focus 均覆盖；最新独立 review 与 QA 均无 blocking/important。
- [x] Evidence pack / Gate Results / DoD Results 已复核，无核心 failed/blocked。

## 4. 术语一致性

- [x] `black-box contract`：指固定上游可观察 wire/API 行为。
- [x] `wire golden`：保留 raw JSON-RPC frames，不把 omitted `isError` 归一化。
- [x] `exception ledger`：唯一允许偏离上游的显式、用户批准、精确 scope 清单。
- [x] `deterministic bundle`：oracle 输入逐文件 SHA 与 canonical aggregate；所有下游证据 fail-closed 消费。
- [x] 禁用词/范围：无公开 page source、无 runtime go-ios/mobilecli fallback、无默认 Python JSON error envelope。

## 5. 领域影响盘点

建议后续走 `cs-domain` 评估以下候选，不在 acceptance 中直接改 CONTEXT/ADR：

1. 术语：`black-box contract`、`wire golden`、`exception ledger`。
2. 结构性决策：实现栈可替换，但外部 contract 不得无批准漂移。
3. 流程级约束：pinned snapshot + manual diff + exception-ledger + fail-closed bundle workflow。

## 6. requirement delta / clarification 回写

- Design `requirement: null`；本 feature 没有 owner-approved req delta。
- 本轮不自由创建/升级 requirement；建议后续需要长期能力愿景时用 `cs-req` backfill。

## 7. roadmap 回写

- Design 未声明 `roadmap` / `roadmap_item`；非 roadmap 起头，无 items.yaml 回写。

## 8. attention.md 候选盘点

- 无 attention 候选：oracle bundle / call-golden 刷新规则属于本 feature 的专项维护知识，不需要每次会话启动加载。
- 建议 `cs-keep` 候选：deterministic bundle fail-closed 模式、strict JSON/PSNR artifact 模式、Pi direct-tools fresh-session验收方法。

## 9. 遗留

- Approved limitation：无 Python fleet provider，fleet runtime success cases返回上游风格 actionable error。
- Approved limitation：iOS real screen recording 保持 approved unsupported；iOS Simulator recording 已真实通过。
- Destructive install/uninstall：有自动 contract coverage；live 未授权，且未计为 passed。
- 维护成本：上游 revision 更新时必须重新 capture、manual diff、更新 bundle/goldens，并重新审批任何 exception scope 变化。

## 10. 最终审计

- [x] 原始 design、checklist、exceptions、review、QA、evidence、gate/DoD 全文重新核对。
- [x] 最新独立 acceptance auditor：19/19 checks 有证据，DOD-ACCEPT-001 实质满足，0 blocking，0 important，推荐 Accept。
- [x] 最后 nit 已修：iOS destructive 提示只引用 `PYMOBILE_MCP_IOS_DESTRUCTIVE=1`；full pytest仍107 passed。
- [x] `git diff --check` passed；staged files=0。
- [x] 工作区规模（写本报告前）：27 tracked modified + 61 untracked；tracked diff 1306 insertions / 876 deletions。
- [x] 无 session HTML、凭据或未脱敏设备 ID 进入 feature evidence。
- [x] 用户终审确认。

用户已于 2026-07-13 确认验收。Lifecycle 回写 `complete/passed` 后执行 scoped commit。

```json
{
  "criteriaSatisfied": {
    "designContract": true,
    "reviewPassed": true,
    "qaPassed": true,
    "acceptanceChecks": "19/19",
    "dodAccept001": true,
    "userFinalConfirmation": true
  },
  "changedFiles": [
    "src/pymobile_mcp/server.py and src/pymobile_mcp/stdio.py",
    "src/pymobile_mcp/tools/{specs,registry,contract,fleet,android,recording,validation}.py",
    "src/pymobile_mcp/drivers/{android,ios,ios_simulator}.py",
    "scripts/capture/assert/coverage/image oracle scripts",
    "tests/fixtures/mobile_mcp* and black-box/live regression tests",
    "README.md, CHANGELOG.md, docs/regression-checklist.md",
    ".codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/*"
  ],
  "testsAddedOrUpdated": [
    "107 pytest tests",
    "106 default stdio scenarios",
    "110 fleet stdio scenarios",
    "91 source-linked scenarios",
    "16 live device sub-smokes",
    "Pi fresh-session direct-tools path"
  ],
  "commandsRun": [
    {"command": "python -m pytest -q", "result": "passed", "summary": "107 passed"},
    {"command": "CMD-002/003/004 pinned upstream capture", "result": "passed", "summary": "23 tools, 26 tools, 47 calls"},
    {"command": "CMD-005/006", "result": "passed", "summary": "23/106 and 26/110"},
    {"command": "CMD-007", "result": "passed", "summary": "91 scenarios"},
    {"command": "CMD-008", "result": "passed", "summary": "3 image modes"},
    {"command": "all device live smokes plus exact iOS-real run", "result": "passed", "summary": "16/16"},
    {"command": "Pi fresh-session direct tools", "result": "passed", "summary": "text/image/action/error"}
  ],
  "validationOutput": {
    "bundleSha256": "952c55cf10c45ce35857016a70639ea3cc4377b5bea31bd3b30cb57c06a1889c",
    "strictArtifacts": "passed",
    "diffCheck": "passed"
  },
  "residualRisks": [
    "Approved fleet runtime exception",
    "Approved iOS real-device recording exception",
    "Destructive install/uninstall not live-attested"
  ],
  "noStagedFiles": true,
  "diffSummary": "27 tracked files changed before acceptance artifact; 1306 insertions, 876 deletions; 61 untracked feature files",
  "reviewFindings": {"blocking": [], "important": [], "nitsResolved": 1},
  "manualNotes": [
    "User-approved exceptions remain exact and unchanged",
    "User confirmed acceptance 2026-07-13; complete/passed and scoped commit next"
  ]
}
```

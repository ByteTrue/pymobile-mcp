# mobile-mcp-black-box-contract-parity Goal Plan

## 输入

- Design: `.codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-design.md`
- Checklist: `.codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-checklist.yaml`
- Design review: `.codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-design-review.md`
- Scenarios: `.codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-scenarios.yaml`
- Exceptions: `.codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-exceptions.yaml`
- Baseline: `ffa668376c78e59c00b50cce319e96c581ef420c`

## 用户确认

2026-07-12，用户明确回复“批准并继续”。Design 与两项 exception 均已批准：

- `EXC-REMOTE-FLEET-RUNTIME`
- `EXC-IOS-SCREEN-RECORDING-RUNTIME`

批准只允许 ledger 中精确 case 使用 `approved_exception`；不能扩展到 schema/discovery、iOS Simulator 或其他工具。

## 目标

除实现栈外，让 pymobile-mcp 对固定 `mobile-mcp@c5d7d27` 的外部可观察黑盒契约 exact：initialize、default/fleet discovery、工具提示词与 schema、成功文本、错误/`isError`、image、设备类型分支、Pi direct-tools 与双端 live。

## Implementation TDD Policy

代码行为 step 默认 RED → GREEN → VERIFY：

1. RED：先增加或更新一个能证伪上游差异的 fixture/scenario/test。
2. GREEN：做最小实现使 focused test 通过。
3. VERIFY：重跑 focused test 与受影响的 contract matrix，并把命令/结果写入 implementation evidence。

若某步只能由真实设备/Pi 验证，必须写 `TDD exception`，记录不能自动 RED 的原因与替代证据；blocked 不得记 pass。

## 执行顺序

1. 建立 deterministic upstream oracle、raw frames、bundle/source coverage 工具。
2. 做最小 contract formatter/error wrapper 微重构，保持 driver side effects 不变。
3. 对齐 initialize/serverInfo、default 23 / fleet 26 tool discovery。
4. 对齐 91 个 success/validation/error/image/device-type scenarios。
5. 接通 iOS Simulator 的 `simctl + WDA` exact 路径；真实 iOS recording 仅使用已批准 exception。
6. 完成 Pi 新会话 direct-tools 与 Android/iOS live evidence。
7. 同步 README、CHANGELOG、regression checklist 和 exceptions 事实。

## 必跑验证

机器权威命令为 checklist `dod.commands` 的 CMD-001~008，必须逐字执行：

- CMD-001：pytest + JUnit + timeout report。
- CMD-002/003：固定上游 default/fleet initialize/list_tools capture。
- CMD-004：固定上游 CallToolResult capture。
- CMD-005/006：Python default/fleet raw stdio parity + exception disposition。
- CMD-007：source/schema/guard/backend/exception scope coverage。
- CMD-008：upstream/Python image backend artifacts、尺寸与 PSNR。

exit 0=passed；exit 1=failed/mismatch；exit 2=environment blocked。任何 core exit 2 都阻塞最终通过。

## 核心验收路径

- raw InitializeResult 与 tool arrays deep-equal。
- scenario disposition coverage=100%；exact / approved_exception / blocked 分开统计。
- Actionable errors 为普通 text 且 `isError` 省略；unexpected/screenshot errors 为 `Error:` text 且 `isError=true`。
- Android physical 对外仍为 `type=emulator`；iOS Simulator discovery/runtime/recording exact。
- Pi 使用新会话自然 direct tools；保存脱敏摘要，不提交原始 session HTML。
- 双平台 live 子项逐条保留 pass/blocked/fail。

## DoD / Gates

- Implementation：checklist steps 完成；TDD/exception evidence、raw frames、reports 落盘。
- Code review：独立 subagent，无 unresolved blocking/important。
- QA：CMD-001~008 + PI-001 + LIVE-001；core blocked 不算 pass。
- Acceptance：逐 design 场景、交付物、exceptions、文档和 git 事实核验。

## Handoff 条件

- 需要改变 approved design、exception scope、公开契约或固定上游 revision。
- 独立 review 不可用且未获降级授权。
- 同一失败项修复三轮仍失败。
- 核心 upstream/npm/Xcode/设备/Pi 环境缺失导致不能判断。
- 用户要求暂停或改方向。

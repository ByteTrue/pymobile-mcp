# mobile-mcp-black-box-contract-parity Goal Protocol

## Execution Loop

1. 读取 design、checklist、scenarios、exceptions、goal-plan、goal-state。
2. 按 checklist 顺序进入 implementation；行为 step 默认 RED → GREEN → VERIFY，不能 TDD 时写 `TDD exception` 与替代证据。
3. 每完成一个 step，立即更新 checklist status 与 implementation evidence；运行对应 focused validation。
4. 完成 implementation gates 后写 evidence pack / command reports / DoD results，并把 `goal-state.yaml` 更新为 `stage: review` / `status: ready`。
5. 运行独立 `cs-code-review`；有 blocking/important 时写 `review/fixing`，做最小 review-fix 后回 `review/ready` 重审。
6. review passed 后写 `qa/ready`，运行 `cs-feat` QA；QA failed/blocked 时写 `qa/fixing`，修复后回 `review/ready`，重跑 review + QA。
7. QA passed 后写 `acceptance/ready`，运行 `cs-feat` acceptance，核对 design、91 scenarios、exceptions、CMD-001~008、PI-001、LIVE-001、文档和 git 交付物。
8. acceptance passed 后先写 `stage: complete` / `status: passed`，再输出 `CS_FEATURE_GOAL_COMPLETE`。

## Goal 模式

普通阶段的非产品 checkpoint 由 driver 通过报告、状态和证据自动推进；只有命中 handoff 条件才停。每次 stage/status 变化立即写回 goal-state。恢复时先以仓库产物和 checklist/git 事实校正 goal-state。

## 硬规则

- 不得绕过 TDD policy；缺 RED/GREEN/VERIFY 且无 TDD exception 时 implementation gate 不通过。
- 上游源码/真实 stdio 是 oracle；不得从 Python specs 或 scenarios expected 反向生成 upstream golden。
- `approved_exception` 只允许 exception ledger 的精确 allowed_case_ids、platform/device_type 与 approval。
- blocked、destructive 未授权、设备缺失、backend 缺失均不得聚合为 pass。
- runtime 不引入 go-ios/mobilecli fallback；iOS Simulator 使用 `simctl + WDA`。
- 不提交本地 Pi session HTML、设备私密信息或临时 probe/debug 输出。
- 独立 design/code review 必须使用 Task agent；主 agent 不得自批 passed。

## State Transitions

- `implementation/ready-to-dispatch` → driver 派发。
- `implementation/running` → 执行 checklist。
- `review/ready|fixing` → 独立 review / review-fix。
- `qa/ready|fixing` → QA / qa-fix 后回 review。
- `acceptance/ready` → acceptance。
- `complete/passed` → 终态。
- `handoff/blocked` → 终态，等待用户动作。

## Handoff

命中以下任一条件时，先写：

```yaml
stage: handoff
status: blocked
handoff_reason: <具体原因>
handoff_next: <建议动作>
```

然后输出：

```text
CS_FEATURE_GOAL_HANDOFF
Reason: <具体阻塞>
Next: <建议动作>
```

条件：

- 需要改变 approved design、exception scope、公开契约或上游 revision；
- 独立 reviewer pending/failed/blocked 且无降级授权；
- 同一失败项三轮修复仍未通过；
- 核心外部环境缺失导致无法判断；
- 用户要求暂停、改方向或终止。

---
id: 002
title: 用 Exception Ledger 约束已批准 runtime 差异
status: accepted
date: 2026-07-13
relates_to: [requirements/CONTEXT, 001]
---

# 用 Exception Ledger 约束已批准 runtime 差异

## Context

黑盒契约要求对外 wire 对齐上游，但两类 runtime 能力短期无法 exact 实现：

1. remote fleet 成功路径需要 Python fleet provider，当前没有。
2. iOS 真机 screen recording 在 pure pymobiledevice3 / WDA 路径上不可靠。

若不显式约束，后续实现容易把“暂时做不到”扩成静默假成功、空列表或大范围 unsupported。

## Decision

维护 `Exception Ledger`：

1. 默认 discovery / schema / 参数校验 / 非 exception case 必须 exact。
2. 仅允许设计批准的 case id / tool / platform / device_type 走差异路径。
3. 当前批准项：
   - remote fleet runtime：工具与 schema 仍公开；成功场景返回上游风格 `mobilecli unavailable` actionable error。
   - iOS real-device recording：start/stop 返回批准的 unsupported 文本；iOS Simulator recording 不豁免。
4. pending / rejected exception 不得在 QA/acceptance 中计 pass。

## Consequences

正向：

- 能力缺口可见、可审计、范围不膨胀。
- Simulator recording 与 fleet schema 仍被 gate 保护。

负向 / 约束：

- 以后补齐 fleet provider 或 iOS recording 时，必须同步收窄/删除 ledger 项并重跑 parity。
- live smoke 必须区分 “approved unsupported” 与 “环境 blocked / 真实 fail”。

## Alternatives Considered

1. **全部标 unsupported_platform**  
   简单，但会破坏 fleet tool 公开与 Simulator recording 成功契约。

2. **假成功 / 空结果掩盖缺口**  
   最危险；会让 LLM 认为操作已完成。明确禁止。

3. **无限期口头约定“先这样”**  
   无法 fail-closed，review/QA 容易把 exception 当普通 pass。

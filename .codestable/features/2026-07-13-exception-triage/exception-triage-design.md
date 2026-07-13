---
doc_type: feature-design
slug: exception-triage
status: approved
created: 2026-07-13
roadmap: pymobile-mcp-productize-0.3
roadmap_item: exception-triage
nature: non-functional
---

# approved exception triage

## 1. 目标
对两项 approved exception 输出 go/no-go 决策，防止半实现 runtime。

## 2. 输出路径
`docs/exception-triage-0.3.md`

## 3. 必须覆盖的 case（绑定 ledger）

### EXC-REMOTE-FLEET-RUNTIME
- tools：`mobile_list_remote_devices`, `mobile_allocate_remote_device`, `mobile_release_remote_device`
- env：`MOBILEFLEET_ENABLE=1`
- platform/device_type：`n/a`（ledger 无此字段）
- cases：`S-REMOTE-LIST`, `S-REMOTE-ALLOCATE-IOS`, `S-REMOTE-ALLOCATE-ANDROID`, `S-REMOTE-RELEASE`
- 来源：exceptions.yaml + ADR-002

### EXC-IOS-SCREEN-RECORDING-RUNTIME
- tools：start/stop screen recording
- platform：ios，device_type：real
- cases：`S-START-REC-IOS` / `S-STOP-REC-IOS`
- Simulator recording **不在** exception 内

## 4. 每 case 必填字段
```yaml
case_id: EXC-...
tools: [...]
platform: ...
device_type: ...
decision: defer | open_roadmap | narrow_now
# defer = no-go now; open_roadmap/narrow_now = go paths with different follow-ups
trigger: ...
ledger_narrowing: ...   # 何时可收窄/删除 exception；默认复用 ledger transition_condition
future_roadmap_slug: null | string
rationale: ...
```

## 5. 写权限边界
允许：
- `docs/exception-triage-0.3.md`
- 本 feature 目录 design/checklist/review/qa/acceptance

禁止（本 feature）：
- `src/**`
- 任何对 `mobile-mcp-black-box-contract-parity-exceptions.yaml` 的修改
- 实现 fleet provider 或 iOS real recording

说明：`ledger_narrowing` 写“何时收窄”，**不是**现在改 ledger。

## 6. 成功标准
- 两 case 字段齐全
- CMD-TRIAGE-001 通过
- docs-only diff

## 7. 明确不做
不实现 runtime；不静默扩 exception 范围。

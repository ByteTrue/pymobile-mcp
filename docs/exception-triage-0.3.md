# Exception Triage 0.3

Productize-0.3 决策文档。绑定 black-box Exception Ledger（ADR-002）。  
本文件 **只决策**；不实现 fleet provider / iOS real recording，不修改 exceptions.yaml。

## EXC-REMOTE-FLEET-RUNTIME

```yaml
case_id: EXC-REMOTE-FLEET-RUNTIME
tools:
  - mobile_list_remote_devices
  - mobile_allocate_remote_device
  - mobile_release_remote_device
platform: n/a
device_type: n/a
env: MOBILEFLEET_ENABLE=1
cases:
  - S-REMOTE-LIST
  - S-REMOTE-ALLOCATE-IOS
  - S-REMOTE-ALLOCATE-ANDROID
  - S-REMOTE-RELEASE
decision: defer
trigger: "Need multi-device remote fleet scheduling in production agent workflows"
ledger_narrowing: "Python fleet provider exists and S-REMOTE-* success paths match upstream exact wire without ActionableError substitute"
future_roadmap_slug: pymobile-mcp-fleet-runtime
rationale: |
  Schema/discovery already exact under fleet mode. Success runtime still lacks a Python
  provider. Implementing half a provider would risk fake allocate/release. Defer until a
  real multi-device product need and provider design exist. Keep returning upstream-style
  mobilecli-unavailable ActionableError for success cases under the approved exception.
```

## EXC-IOS-SCREEN-RECORDING-RUNTIME

```yaml
case_id: EXC-IOS-SCREEN-RECORDING-RUNTIME
tools:
  - mobile_start_screen_recording
  - mobile_stop_screen_recording
platform: ios
device_type: real
cases:
  - S-START-REC-IOS
  - S-STOP-REC-IOS
decision: defer
trigger: "iOS real device can export finalized screen recording via pure pmd3/WDA path without go-ios"
ledger_narrowing: "Reliable start+stop finalize producing usable media on iOS real; Simulator remains exact and must stay non-exception"
future_roadmap_slug: null
rationale: |
  Spike on iOS 26.5.2 userspace RSD: no displayservice; WDA video start works but stop
  finalize fails. Simulator recording via simctl already works and is NOT covered by this
  exception. Do not reopen go-ios. Revisit only when platform/WDA path can finalize media.
```

## Mapping
- `defer` = no-go for 0.3 / current mainline runtime work
- `open_roadmap` = spawn dedicated epic (used only if decision changes)
- `narrow_now` = would require a separate parity task to edit the ledger; **not** done here

## Write boundary
Allowed: this file + feature lifecycle artifacts under `.codestable/features/2026-07-13-exception-triage/`.  
Forbidden: `src/**`, any mutation of `mobile-mcp-black-box-contract-parity-exceptions.yaml`.

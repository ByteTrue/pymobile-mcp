---
doc_type: roadmap
slug: pymobile-mcp-post-mvp
status: draft
created: 2026-07-11
last_reviewed: 2026-07-11
tags: [mcp, mobile, ios, crash, post-mvp, roadmap]
related_requirements: []
related_architecture: []
---

# pymobile-mcp post-MVP：iOS live 与 crash 真实现

## 1. 背景

`pymobile-mcp-android-mvp` 已完成并合入 `main`（`93641e3`）。

当前能力边界（见 README 矩阵）：

- Android UI / app / system / recording：**supported**
- Android crash：**unsupported_platform**（无可靠非 root 来源）
- iOS core UI 代码路径存在，但本机 **blocked-by-env**（无配对设备 + WDA）
- iOS app / recording / crash：**unsupported_platform**（不引入 go-ios）

本 roadmap 只处理 MVP 明确留下的洞：iOS 真机 live 补证，以及 crash（含可选 iOS app lifecycle）真实现。

## 2. 范围与明确不做

### 覆盖

- 用真实 iOS 设备 + 可达 WDA 把 core UI smoke 从 blocked-by-env 推进到 live passed。
- 评估并实现 iOS app lifecycle（list/launch/terminate/install/uninstall）的 **pure pymobiledevice3/WDA** 路径；失败则保持 stable unsupported 并更新矩阵证据。
- 为 Android/iOS crash list/get 找到可靠来源并实现，或留下可复现 spike 证明仍不可行。
- 补齐 iOS 上仍弱的 system helpers：`press_button` / `open_url` / `save_screenshot`（若 core 已具备能力则薄封装）。

### 明确不做

- 不引入 `go-ios` / `mobilecli` 作为运行时依赖。
- 不实现 remote fleet 工具。
- 不重开 23-tool 契约或改 public schema 字段名。
- 不做跨进程 recording resume、设备池、发布运营。

### Granularity Gate

| 判断项 | 结论 |
|---|---|
| 为什么不是 single feature | iOS live 验证、app lifecycle、crash 来源是不同风险面，可独立 spike/验收。 |
| 为什么不是 brainstorm | 缺口已由 MVP 矩阵与 acceptance 明确。 |
| 最小闭环 | 配对 iPhone + WDA 后，`ios_pmd3_wda_live_smoke.py` 返回 `status=passed`。 |

## 3. 模块拆分

```text
iOS Driver (pymobiledevice3 + WDA)
Tool Execution Layer (handlers / validation)
Verification / Docs (live smoke, matrix, spike notes)
```

Android Driver 仅在 crash 真实现条目中触碰。

## 4. 子 feature 列表（有序）

1. **ios-live-wda-verification** — 配对设备 + WDA，把 iOS core live smoke 跑成 passed，并固化复跑步骤。
2. **ios-system-helpers-parity** — 实现或明确 iOS `press_button` / `open_url` / `save_screenshot`。
3. **ios-app-lifecycle-pmd3** — pure-PMD3/WDA app list/launch/terminate/install/uninstall 实现或 stable unsupported + 新证据。
4. **crash-tools-real-source** — Android/iOS crash list/get 真来源 spike→实现或继续 unsupported（禁止假成功空列表）。

依赖：`2`/`3` 依赖 `1`；`4` 可与 `2`/`3` 并行，但默认排在 live 验证之后。

## 5. 验收

- iOS live smoke：`PATH=.venv/bin:$PATH python tests/ios_pmd3_wda_live_smoke.py` → `passed`（有设备时）。
- app/crash：实现则 live/unit 覆盖；否则 `unsupported_platform` + spike 证据更新 README 矩阵。
- `python -m pytest` 全绿；无 go-ios 依赖。

## 6. 风险

1. 本机长期无 iOS 设备 → `ios-live-wda-verification` handoff，不伪造 passed。
2. PMD3 无稳定 app/crash API → 保持 unsupported，不硬接 go-ios。
3. crash 权限/路径随系统版本漂移 → spike 必须绑定 OS 版本与命令输出。

# LIVE-001 设备证据（2026-07-12）

Exit 0=passed，2=blocked，1=failed；逐项保留，不把 blocked 计为 pass。设备标识均脱敏。

## Android physical / Android emulator / iOS Simulator 动态矩阵

命令：

```bash
PYMOBILE_MCP_ACTIONS=1 PYMOBILE_MCP_LIVE_TIMEOUT=180 \
  PATH=.venv/bin:$PATH python tests/all_devices_live_smoke.py
```

结果：exit 0，`status=passed`，3 online devices，12/12 child smokes passed，0 blocked，0 failed，0 timeout。原始摘要见 `live-matrix-2026-07-12.json`。

| 设备 | 子项 | 结果 | 摘要 |
|---|---|---|---|
| Android physical（public type 与 upstream 兼容为 emulator） | UI/actions | passed | 1200x2652，elements=72，tap完成 |
| Android physical | app/system | passed | 11 apps，portrait，screenshot saved；destructive未授权 |
| Android physical | crash | passed | real dropbox source，当前0 entries |
| Android physical | recording/crash | passed | safe-size retry + local adb SIGINT finalize；MP4=3232 bytes |
| Android emulator | UI/actions | passed | 1080x2400，elements=51，tap完成 |
| Android emulator | app/system | passed | 19 apps，portrait，screenshot saved；destructive未授权 |
| Android emulator | crash | passed | real dropbox source，当前0 entries |
| Android emulator | recording/crash | passed | MP4=62408 bytes |
| iOS Simulator | core UI/WDA | passed | 402x874，elements=258 |
| iOS Simulator | helpers | passed | screenshot=2592894 bytes，open_url/HOME完成 |
| iOS Simulator | app lifecycle | passed | 26 apps，launch/terminate Settings；destructive未授权 |
| iOS Simulator | recording/crash | passed | simctl MP4=128447 bytes；真实 simulator CrashReporter source 当前0 entries |

动态 runner 只枚举当时 online devices；不同设备并发、同设备脚本串行；每个 child 独立180秒硬超时并实时输出 start/complete JSONL。`crash_tools_live_smoke.py` 服从精确 device selector，不再误扫未授权设备。

## iOS real 授权证据

最终解锁后结果：4/4 child smokes passed，0 blocked，0 failed，0 timeout。原始脱敏摘要见 `ios-real-live-2026-07-12.json`。

| 子项 | 结果 | 摘要 |
|---|---|---|
| core UI/WDA | passed | 402x874，elements=234 |
| helpers | passed | screenshot=3382376 bytes，open_url/HOME完成 |
| app lifecycle | passed | 49 apps，launch/terminate Settings；destructive未授权 |
| recording/crash | passed | real recording 精确匹配 approved `EXC-IOS-SCREEN-RECORDING-RUNTIME` unsupported；真实 crash source 51 entries，sample read passed |

首次 app lifecycle 尝试因设备自动锁定失败；设备解锁后的最终授权结果 passed，并取代该历史尝试的 current disposition。

## Aggregate 与未覆盖项

- 四类设备（Android physical、Android emulator、iOS Simulator、iOS real）均有当前证据：**16/16 feature sub-smokes passed**。
- PI-001 fresh-session direct-tools：**passed**；脱敏证据见 `pi-redacted.md`。
- destructive install/uninstall：未提供 APK/IPA 与 destructive opt-in，保持 not-authorized / not-run；不作为 QA blocker，也不推断为 passed。

Manual aggregate：**LIVE-001 passed；PI-001 passed；destructive paths remain explicitly not-authorized/non-blocking**。

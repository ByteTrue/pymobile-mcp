---
doc_type: feature-qa-fix
feature: 2026-07-12-mobile-mcp-black-box-contract-parity
status: completed
fixed: 2026-07-13
round: 15
---

# mobile-mcp-black-box-contract-parity QA-fix 证据

> Sections 1–17 are historical fix/synchronization evidence. Current disposition is recorded in Section 18; superseded live failures, exclusions, and lifecycle states are not current findings.

## 1. 修复范围

Round 1 修复 iOS live smoke parser/timeout；Round 2 修复动态全设备 live 调度和 crash smoke 精确设备选择；Round 3 修复动态 runner 的跨设备并发与即时进度；Round 4 修复 Xcode 26 Simulator/Android recording fallback/live smoke 分支；Round 5 收口 recording lifecycle 与 Simulator crash 安全回归；Round 6 修复第二轮授权 live matrix 暴露的 Android stop 顺序与 Simulator 子进程 stdio 污染；Round 7 收窄 Android stop remote fallback 的异常边界。各轮均不修改 approved public contract、upstream revision 或 exception scope：

- QA-015：四个 iOS live smoke 仍按旧 `success/error` JSON envelope 读取结果，无法消费当前 mobile-mcp parity 的原始文本、JSON object/array 与 image content。
- QA-016：四个脚本没有各自的硬超时，只能依赖父级总超时。

## 2. 改动与证据

### QA-015：live content parser

- 新增 `tests/ios_live_smoke_support.py`，集中处理 devices JSON object、screen-size 文本、elements 前缀 + JSON array、apps 前缀文本、save path 文本、crash JSON array、get crash 原文以及 actionable/unsupported/locked 文本分类。
- 四个 iOS live smoke 改用上述 parser；截图仍直接核对 MCP image content。
- 新增 `tests/test_ios_live_smoke_support.py`，覆盖成功 content、actionable、unsupported、locked，无设备依赖。

TDD 证据：

- RED：`.venv/bin/python -m pytest -q tests/test_ios_live_smoke_support.py` → collection error，`ModuleNotFoundError: ios_live_smoke_support`。
- GREEN/VERIFY：同命令 → `3 passed in 0.02s`。

### QA-016：每脚本独立 timeout

- 四个脚本入口统一通过 `run_with_timeout(main)`。
- 默认 `180` 秒；`PYMOBILE_MCP_LIVE_TIMEOUT` 可覆盖。
- 超时打印 JSON `status=blocked`、`timeout_seconds` 并返回 exit 2。
- 无设备实跑：设置 `PYMOBILE_MCP_LIVE_TIMEOUT=2` 逐一运行四个脚本，均在自身超时后输出 blocked 并 exit 2；没有启动 GUI simulator。

## 3. 验证

- focused pytest：`3 passed in 0.02s`。
- full pytest：`79 passed in 44.22s`。
- compileall：六个本轮 Python 文件编译通过。
- 四脚本 timeout smoke：全部 exit 2，输出 `reason: iOS live smoke timed out`。
- `git diff --check`：通过。
- 清洁度：未修改 runtime contract/driver；无新增 TODO/FIXME/调试代码；未 stage 文件。

## 4. 结论与下一步

QA-015/QA-016 已完成实现修复，但本报告不判定 QA passed。按 goal protocol，状态回到 `review/ready`；独立 code review 通过后必须重跑 QA。原 QA-010~QA-013 的设备/环境阻塞结论不在本轮改写范围内。


## 5. Round 2：动态在线设备 live smoke

### QA-017：单次发现与精确设备调度

- 新增 `tests/all_devices_live_smoke.py`：只通过 production MCP stdio 调用一次 `mobile_list_available_devices`，过滤当前 `online` Android/iOS，并为每个快照设备运行指定的四个现有平台脚本。
- 每个 child 同时设置统一 `PYMOBILE_MCP_DEVICE` 和对应平台 selector，清除另一平台 selector，避免脚本回退到未选择设备。
- 默认清除平台 actions/destructive 标志；仅 `PYMOBILE_MCP_ACTIONS=1` 时映射为当前平台 actions 标志。不会启用 install/uninstall。
- 每个 device/script child 独立使用 `PYMOBILE_MCP_LIVE_TIMEOUT`（默认 180 秒）；捕获 exit/stdout/stderr，timeout 记录为 failed。聚合优先级为 failed/exit 1 > blocked/exit 2 > all passed/exit 0；无在线设备为 blocked/exit 2。

### QA-018：crash smoke 精确选择与内部 timeout

- `tests/crash_tools_live_smoke.py` 优先使用显式 `PYMOBILE_MCP_DEVICE`；未提供时只使用显式存在的 Android/iOS selector；有 selector 时绝不扩展到其他在线设备。
- crash smoke 复用 `run_with_timeout`，默认 180 秒，超时 blocked/exit 2；helper 只增加可选 smoke 名称，原四个 iOS caller 行为不变。

TDD 证据：

- RED：`.venv/bin/python -m pytest -q tests/test_all_devices_live_smoke.py` → collection error，`ModuleNotFoundError: all_devices_live_smoke`。
- GREEN/VERIFY：`.venv/bin/python -m pytest -q tests/test_all_devices_live_smoke.py tests/test_ios_live_smoke_support.py` → `9 passed in 0.02s`。
- 无设备 unit 覆盖 online selection、统一 selector 优先级、safe child env、聚合优先级和 subprocess hard timeout；没有调用真实设备。

Round 2 验证：

- full pytest：`85 passed in 4.07s`。
- compileall：四个本轮 Python 文件编译通过。
- Black check：本轮四个 Python 文件格式通过。
- `git diff --check`：通过。
- 按用户指令未运行任何 live smoke，避免触碰当前连接的真实 iOS 设备。
- 本轮不判定 review/QA/acceptance passed；`goal-state.yaml` 回到 `review/ready`，等待独立 review。

## 6. Round 3：动态 runner review-fix

### QA-019：设备并发 pipeline 与即时 child progress

- RED：新增 no-device orchestration tests 后，`.venv/bin/python -m pytest -q tests/test_all_devices_live_smoke.py` → `2 failed, 6 passed`：缺少 `_run_pipelines`，且 child 启动前未输出 progress。
- GREEN：每台在线设备使用一个 asyncio pipeline，通过 `asyncio.to_thread` 并发执行；每个 pipeline 内仍逐个 await 平台脚本，保持同设备顺序。未增加固定 concurrency 配置，并发自然受 snapshot 在线设备数限制。
- 每个 `_run_child` 在 subprocess 前输出 `child_start`，完成或 timeout 后输出 `child_complete`；均为 stderr JSON line 且 `flush=True`。最终聚合 JSON 仍只写 stdout。
- 独立 timeout、status、exit code、stdout/stderr capture 与精确 device env pinning 保持不变；actions 仍需统一 opt-in，destructive 默认继续清除。

Round 3 验证：

- GREEN focused：runner unit `8 passed in 0.01s`。
- 最终 focused：runner + iOS support `11 passed in 0.02s`。
- full pytest：`87 passed in 3.74s`。
- compileall：三个涉及的 Python 文件通过。
- Black：runner、runner unit 与顺手修复 formatting nit 的 `test_ios_live_smoke_support.py` 均通过 check。
- `git diff --check`：通过；没有 staged 文件。
- 按用户指令未运行 live tests；`goal-state.yaml` 保持 `review/ready`。本报告不判定 review、QA 或 acceptance passed，下一步为独立 code review。


## 7. Round 4：authorized live matrix QA-fix

### QA-020：Xcode 26 Simulator app/crash sources

- RED：新增 `tests/test_driver_qa_fixes.py` 后 focused test 为 `5 failed, 1 passed`；失败分别证明 `listapps --json` 不能解析 OpenStep plist、Simulator crash helper 缺失、Android recording 没有 retry。
- GREEN：Simulator `listapps` 保持 raw `xcrun simctl listapps <UDID>`，经无 shell 的 `plutil -convert json -o - -- -` 转换；device listing 继续 `_simctl_json`。
- Simulator crash 递归读取 `~/Library/Developer/CoreSimulator/Devices/<UDID>/data/Library/Logs/CrashReporter`，ID 为相对 POSIX path；空目录返回 `[]`，绝对路径、`..` 与 symlink escape 均不能越出 crash root。

### QA-021：Android encoder fallback

- 默认 `screenrecord` 启动后用 `wait(timeout=0.25)` 检测即时非零退出；仍存活或 exit 0 不 retry。即时失败时清理 remote file，按当前方向只 retry 一次 `720x1280` / `1280x720`；第二次即时非零退出抛 `DriverError`。
- stdout/stderr 均为 `DEVNULL`，不新增 pipe，避免无人消费的 stderr deadlock。未改变 MCP schema，也未新增依赖。

### QA-022：iOS app/recording/crash live smoke 分支

- 精确使用已选 device 的 `type`：real iOS 仍要求已批准的 unsupported result；Simulator 必须 start/stop recording、检查 host MP4 非空后再 list/get crashes。未增加 install/uninstall 或其他 destructive call。
- no-device unit 通过 mock MCP session 验证 real/simulator 两个分支及 exact tool calls；按用户指令没有运行任何 live device/simulator。

### QA-023：验证与 deterministic evidence refresh

- focused RED：`5 failed, 1 passed`；smoke branch RED：`1 failed, 6 passed`。
- GREEN/VERIFY focused：`7 passed in 0.06s`；full pytest / CMD-001：`94 passed`。
- CMD-004：47 upstream call results；CMD-005：23 tools / 106 scenarios；CMD-006：26 tools / 110 scenarios；CMD-007：91 source-linked scenarios；CMD-008：3 image modes passed。
- Source backend manifest 与 deterministic bundle 已刷新，bundle SHA-256 为 `9f26dac304a654ca40cc9c9921294a84ef478b48255f087de5cb73f83a511b0a`。
- 本机默认 npm 已为 12.0.1，CMD-008 首次 fail-closed；通过 isolated `npm@12.0.0`（approved expected version）重跑后通过，未改变 upstream revision/expected npm。
- compileall 与 `git diff --check` 通过；无 staged files。
- `goal-state.yaml` 保持 `review/ready`。本报告不判定 review、QA 或 acceptance passed；下一步为独立 code review。


## 8. Round 5：recording lifecycle QA review-fix

### QA-024：Android fallback 使用当前 window dimensions

- RED：focused suite 的 reverse-portrait 与 landscape-native rotation-zero 两项失败；旧实现按 `user_rotation == 0` 选择 size，分别得到错误的 `1280x720` / `720x1280`。
- GREEN：fallback 从已连接 uiautomator2 device 的 `window_size()` 读取当前宽高；`width <= height` 使用 `720x1280`，否则使用 `1280x720`。默认 screenrecord、单次 retry、即时退出判定和公开输出保持不变。
- VERIFY：参数化覆盖 portrait、reverse portrait、landscape 和 landscape-native orientation edge。

### QA-025：per-device start lock 覆盖 spawn 与 state registration

- RED：两个已同步 connect 的并发 start 均在 state registration 前通过 active check，focused test 观测到 `spawn_calls == 2`。
- GREEN：新增 `spawn_recording` lifecycle helper；同一个 per-device lock 内完成 active check、driver process spawn 和 `_active` registration。既有 `start_recording` fixture helper保留并复用同一 check/register helper。
- VERIFY：并发 test 仅 spawn 一次，另一调用收到 structured `already_recording`。

### QA-026：Simulator stop timeout 清理

- RED：`IOSSimulatorDriver.stop_recording` 的 30 秒 wait timeout 直接泄漏 `TimeoutError`，没有 kill/reap child。
- GREEN：timeout 后 best-effort `kill()` 并再次限时 `wait()` reap，然后抛含 device/timeout details 的 `DriverError`。
- VERIFY：focused fake process 断言 SIGINT、kill、两次 wait 均发生，最终错误为 `driver_error`。

### QA-027：Simulator crash symlink 与临时 artifact 清洁度

- 新增独立 symlink escape regression：list 不暴露越界 symlink，get 返回 structured not-found/unreadable `DriverError`。
- 删除 repo root 的 `tmp-android-recording-smoke.mp4` 临时 artifact。
- TDD exception：symlink case 是对既有安全实现的 committed regression guard，增加时已通过，不伪造 RED。

Round 5 验证：

- focused RED：`3 failed, 10 passed`（window dimensions / timeout）；并发专测 RED：`1 failed, 12 deselected`（spawn 2 次）。
- GREEN/VERIFY focused：`13 passed in 0.23s`。
- full pytest / CMD-001：`100 passed in 3.92s`。
- compileall 与 `git diff --check`：通过；未 staged 文件。
- deterministic oracle bundle 输入未变化，因此未重跑 CMD-004~008；固定 upstream revision、approved exceptions 与现有 bundle SHA 保持不变。
- 按用户指令未运行任何 live device/simulator。`goal-state.yaml` 保持 `review/ready`；本报告不判定 review、QA 或 acceptance passed，下一步为独立 code review。


## 9. Round 6：second authorized live matrix QA-fix

### QA-028：Android recording stop 先向本地 adb 发送 SIGINT

- RED：新增 stop lifecycle unit 后 focused 为 `2 failed`。成功 wait case 仍观测到 remote `pkill`；timeout case只执行一次 5 秒 wait 后直接 kill，没有 remote fallback 后的 bounded wait。
- GREEN：`_stop_recording_sync` 先向仍存活的本地 adb process 发送 `SIGINT` 并等待最多 5 秒，让 adb 转发 Ctrl-C、由 `screenrecord` finalize MP4。只有该 wait 未完成才执行 remote `pkill` / `killall` fallback，再等待最多 5 秒；仍未退出才 local kill 并以 3 秒 bounded wait reap。
- VERIFY：unit 精确断言成功 local SIGINT 不调用 remote kill；两次 timeout 路径依次发生 local SIGINT、remote fallback、local kill/reap。既有 pull、remote cleanup 与 non-empty validation未改。
- Live provenance：第二轮授权 matrix 中 safe-size fallback 已能启动，但旧 stop 顺序失败；独立 manual probe 对本地 adb PID 发送 SIGINT 后 exit 0 并产出 64820-byte MP4。该 probe 只用于根因证据，不计为修复后 MCP live pass。

### QA-029：Simulator recordVideo 子进程不继承 MCP server stdio

- RED：production subprocess seam exact test 为 `1 failed`，实际 kwargs `{}`，期望 `stdout=DEVNULL` / `stderr=DEVNULL`。
- GREEN/VERIFY：`start_simctl_recording` 创建 `xcrun simctl io ... recordVideo` 时把 stdout、stderr 均设为 `subprocess.DEVNULL`；argv、返回 process、stop/exception 与 public MCP output均未改。
- Live provenance：第二轮授权 matrix 中 `Recording completed...` / `Wrote video...` 被 stdio server 当作 JSON-RPC 解析；本轮只关闭该 child 输出通道，没有运行设备或 Simulator。

Round 6 验证：

- focused RED：Android stop `2 failed`；Simulator exact kwargs `1 failed`。
- GREEN/VERIFY：新行为 focused `3 passed`；driver/contract focused suites `44 passed in 2.82s`。
- Round 6 pytest machine report was superseded；the current machine report is `evidence/pytest.json` with **105 passed**.
- compileall：四个涉及的 runtime/test Python 文件通过；`git diff --check`通过；未 staged 文件。
- deterministic oracle bundle 输入、public contract、scenario/exception ledger均未变化，因此未重跑 CMD-004~008。
- 按用户指令未运行任何 live device/simulator。`goal-state.yaml` 保持 `review/ready`；本报告不判定 review、QA 或 acceptance passed，下一步为独立 code review。


## 10. Round 7：Android stop exception-boundary review-fix

### QA-030：仅 timeout 触发 remote fallback

- RED：参数化 RuntimeError/OSError focused test 为 `2 failed`，证明旧实现吞掉异常并继续 remote kill/pull。
- GREEN：`process.send_signal(SIGINT)` 保持在 timeout handler 外；首个 `process.wait(timeout=5)` 仅捕获 `subprocess.TimeoutExpired`。因此 send/wait 的其他异常原样传播且不会调用 remote pkill/killall；timeout 后 fallback 自身的 bounded cleanup 继续 best-effort。
- VERIFY：stop focused `4 passed`；`tests/test_driver_qa_fixes.py` `17 passed`；full pytest `104 passed in 4.30s`；compileall 与 `git diff --check`通过。
- 按指令未运行任何 live call。`goal-state.yaml` 保持 `review/ready`；本报告不判定 review、QA 或 acceptance passed，下一步为独立 code review。


## 11. Round 8：artifact-only QA synchronization

- 本轮只同步 CodeStable artifacts；未修改 runtime/tests，未调用 live device。
- 最新独立 reviews 已覆盖 dynamic runner、Simulator app/crash/recording、Android recording fallback/lifecycle 与 2 秒 recording probe；当前 blocking/important findings 均为 none。
- Current automated：pytest 105 passed；CMD-005=23/106；CMD-006=26/110；CMD-007=91；CMD-008=3 modes under pinned npm 12.0.0，全部 exit 0。
- Current deterministic bundle manifest：`1588eefbf8848385a5aaa9f6166949d1c45daa657d9b47dbba951e8701eea810`。
- Current LIVE-001：Android physical、Android emulator、iOS Simulator、iOS real 共 16/16 feature sub-smokes passed。
- Current manual：PI-001 fresh-session direct-tools passed；destructive install/uninstall not-authorized/not-run and non-blocking。


## 12. Round 9：authorized iOS-real artifact synchronization

- 本轮只同步 CodeStable artifacts；未修改 runtime/tests，未调用 live device。
- 最终授权 iOS-real evidence 在设备解锁后 4/4 passed：core 402x874/234 elements；helpers screenshot 3382376 bytes/open_url/HOME；49-app Settings launch+terminate；real crash source 51 entries/sample read passed。
- iOS real recording 精确匹配 approved `EXC-IOS-SCREEN-RECORDING-RUNTIME` unsupported；不把 unsupported 擅自改写为成功 runtime。
- 原授权 Android physical + Android emulator + iOS Simulator 动态 matrix 12/12 保持 passed。四类设备现有 16/16 feature sub-smokes，LIVE-001 为 passed。
- destructive install/uninstall 未授权、未运行，不作为 QA blocker，也不计为 passed。
- Final QA-fix validation：bundle=`1588eefbf8848385a5aaa9f6166949d1c45daa657d9b47dbba951e8701eea810`；CMD-001=105 passed；CMD-005/006/007/008 全部 exit 0。
- Historical Round 9 close：state was `review/ready` pending the then-required final QA-fix review and QA rerun；acceptance was not-run。This state is superseded by Section 14.


## 13. Round 10：strict JSON / pinned npm / final artifact synchronization

- Scope remained artifact and contract-harness only；no device calls and no runtime public contract/upstream/exception changes.
- RED focused：2 failed；`_json_psnr` missing and `write_json` accepted `NaN`.
- GREEN focused：2 passed；`write_json(... allow_nan=False)` rejects non-finite values, while perfect-match numeric PSNR still clears the threshold and report serialization emits `"Infinity"`.
- CMD-008 checklist command now uses `npx --yes --package npm@12.0.0 -c`；the exact command passed all 3 image modes and refreshed six images plus `image-backends.json`.
- Bundle manifest was recomputed after script/scenario changes：`1588eefbf8848385a5aaa9f6166949d1c45daa657d9b47dbba951e8701eea810`.
- CMD-005/006/007 reran：23/106、26/110、91，all exit 0. CMD-001 refreshed `pytest.json`/XML：105 passed.
- Current manual evidence：LIVE-001 16/16 passed；PI-001 passed；destructive install/uninstall remains not-authorized/not-run and non-blocking.
- Strict parse of all JSON artifacts, YAML parse, compileall, formatting/diff checks and no-staged-files verification passed.
- Historical Round 10 close：this fix did not self-pass review, QA, or acceptance；state was `review/ready` pending independent gates。This state is superseded by Section 14.


## 14. Round 11：final independent gate transition

- Artifact-only transition：no code/tests changes and no device calls。
- Final independent code review passed with blocking none and important none；review includes the strict-JSON、numeric PSNR、exact pinned npm command and refreshed deterministic evidence QA-fix details。
- Independent QA functional/evidence checks passed：pytest 105；default 23/106；fleet 26/110；source 91；CMD-008 exact `npx --yes --package npm@12.0.0 -c` pinned command，3 modes；bundle `1588eefbf8848385a5aaa9f6166949d1c45daa657d9b47dbba951e8701eea810`。
- LIVE-001 remains passed at 16/16；PI-001 passed；destructive install/uninstall remains not-authorized/not-run and non-blocking。
- Historical Round 11 lifecycle was `acceptance/ready`; acceptance remained pending/not-run. This state is superseded by Section 15.


## 15. Round 12：acceptance-found stale-golden fail-closed QA-fix

- Scope remained contract harness, deterministic artifacts, and status/docs only; no live devices, public runtime, upstream revision, or exception-scope changes.
- TDD RED: focused stale call-golden regression was `1 failed`, proving stdio still started. GREEN: `1 passed`, proving mismatched `provenance.bundle_sha256` fails before `StdioProbe` construction.
- CMD-004 now records the complete deterministic `bundle` object and aggregate; the call golden provenance references the same final aggregate.
- Design and checklist now use exact `npx --yes --package npm@12.0.0 -c` wrappers for CMD-002/003/004/008.
- Final deterministic bundle: `7d0ded471b2c21ce1024581e79da9ecb02d91b4b01bc32e6ca4d13f302d366df`.
- Exact refresh results: CMD-002=23 tools; CMD-003=26 tools; CMD-004=47 call results; CMD-005=23/106; CMD-006=26/110; CMD-007=91; CMD-008=3 modes; full pytest/CMD-001=106 passed.
- Existing LIVE-001 remains 16/16 and PI-001 remains passed. Android and iOS Simulator recording passed live; iOS real recording remains the exact approved exception.
- Historical Round 12 close: lifecycle was `qa/ready`; independent QA still had to rerun and acceptance was not-run/not passed. This state is superseded by Section 16.

## 16. Round 13：final independent QA transition

- Artifact-only transition: no code/test changes and no device calls.
- Final independent QA passed: pytest 106; default 23/106; fleet 26/110; source 91; image 3 modes; bundle `7d0ded471b2c21ce1024581e79da9ecb02d91b4b01bc32e6ca4d13f302d366df`.
- Existing LIVE-001 remains passed at 16/16 and PI-001 remains passed. Destructive install/uninstall remains not-authorized/not-run and non-blocking.
- Independent review is passed, QA is passed, and there are no blockers.
- Historical Round 13 lifecycle was `acceptance/ready`; acceptance was pending/not-run, no acceptance report existed, and all 19 acceptance checks remained pending. This state is superseded by Section 17.


## 17. Round 14：acceptance-found image live-artifact QA-fix

- Scope stayed within scenario evidence references, one no-device regression, deterministic artifacts, docs, and lifecycle synchronization. Public runtime, upstream revision, exceptions, LIVE-001, and PI-001 are unchanged.
- TDD RED: focused regression failed `1 failed` because `S-TAKE-JPEG-SIPS.report` named nonexistent `evidence/images/psnr-sips.json`.
- GREEN: all scenario `live_artifacts` mappings now require committed regular files; SIPS, ImageMagick, and fallback reference the consolidated `evidence/image-backends.json`, and fallback filenames use `upstream-sips_fallback.jpg` / `python-sips_fallback.jpg`.
- Final deterministic bundle: `952c55cf10c45ce35857016a70639ea3cc4377b5bea31bd3b30cb57c06a1889c`.
- Refresh results: CMD-004=47 call results; CMD-005=23/106; CMD-006=26/110; CMD-007=91; CMD-008=3 modes; full pytest/CMD-001=107 passed.
- Historical Round 14 close: the latest independent review had passed with no blocking or important findings. Lifecycle was `qa/ready`; independent QA was pending, acceptance was not-run/not passed, and all 19 acceptance checks remained pending. This state is superseded by Section 18.


## 18. Round 15：final independent QA transition

- Artifact-only transition: no code/test changes and no device calls.
- Final independent QA passed for bundle `952c55cf10c45ce35857016a70639ea3cc4377b5bea31bd3b30cb57c06a1889c`: pytest 107; default 23/106; fleet 26/110; source 91; image 3 modes; artifact regression passed.
- Existing LIVE-001 remains passed at 16/16 and PI-001 remains passed. Destructive install/uninstall remains not-authorized/not-run and non-blocking.
- Independent review is passed, QA is passed, and there are no blockers.
- Current lifecycle is `acceptance/ready`; acceptance is pending/not-run, no acceptance report exists, and all 19 acceptance checks remain pending.
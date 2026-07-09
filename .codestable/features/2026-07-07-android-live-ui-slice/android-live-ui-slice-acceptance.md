---
doc_type: feature-acceptance
feature: 2026-07-07-android-live-ui-slice
status: passed
accepted: 2026-07-10
round: 1
---

# android-live-ui-slice 验收报告

> 阶段：阶段 3（验收闭环）
> 验收日期：2026-07-10
> 关联方案 doc：`.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-design.md`

## 1. 接口契约核对

**接口示例逐项核对**：

- [x] `mobile_list_available_devices`：通过 MCP stdio live smoke 返回在线 Android emulator `emulator-5554`，platform 为 `android`。
- [x] `mobile_get_screen_size`：返回正数宽高，live smoke 证据为 `width=1080`、`height=2400`、`scale=1.0`。
- [x] `mobile_take_screenshot`：返回 MCP image content，脚本断言 `type=image` 且 `mimeType=image/png`。
- [x] `mobile_list_elements_on_screen`：返回 JSON text，元素含 `type/text/label/name/value/identifier/focused/coordinates`，不返回 raw XML。
- [x] `mobile_click_on_screen_at_coordinates` / `mobile_double_tap_on_screen` / `mobile_long_press_on_screen_at_coordinates` / `mobile_swipe_on_screen` / `mobile_type_keys`：live smoke 通过 MCP stdio 调用，若 action 返回 structured error 脚本会失败；最终命令 exit 0。

**名词层“现状 → 变化”核对**：

- [x] `AndroidDriver(BaseDriver)`：落在 `src/pymobile_mcp/drivers/android.py`，实现 discovery、screen size、screenshot、elements、tap/double/long/swipe/type 的最小闭环。
- [x] Android tool handlers：落在 `src/pymobile_mcp/tools/android.py`，通过 `register_android_handlers()` 接入 registry。
- [x] `ScreenElement` → MCP output：handler 将 `ScreenElement.rect` 转成 `coordinates` 字段，并保留 text/label/name/value/identifier/focused。
- [x] fake-driver seam：`configure_android_tools_for_tests()` 让 unit test 不依赖真实设备。

**流程图核对**：

- [x] MCP client → tool handler → Android driver：`tests/android_live_smoke.py` 使用 `mcp.client.stdio.ClientSession` 启动 `pymobile_mcp.cli run`，真实走 server/list/call 协议。
- [x] device discovery → driver routing：`_driver_for()` 先检查在线 device id，再创建 Android driver。
- [x] driver exception → structured envelope：registry 保持 `ToolError` / generic exception 到 JSON text envelope 的转换；live smoke 对 action result 做 structured error 反查。

## 2. 行为与决策核对

**需求摘要逐项验证**：

- [x] 已连接 Android 设备 discovery：`emulator-5554` online。
- [x] screen size + screenshot：live smoke 已验证。
- [x] elements：live smoke returned `element_count=41`；unit fake-driver 断言 coordinates 结构。
- [x] tap/swipe/type 最小闭环：live smoke action sequence exit 0。

**明确不做逐项核对**：

- [x] 不实现 Android app lifecycle、orientation、button、open_url、save_screenshot：这些工具仍留给后续 `android-app-system-tools`。
- [x] 不实现 recording/crash：留给 `android-recording-crash-tools`。
- [x] 不公开 raw XML/page source：`mobile_get_page_source` 未出现在 list_tools；elements handler 不输出 XML。
- [x] 不做 iOS：未触碰 iOS driver。

**关键决策落地**：

- [x] Android driver 使用 `uiautomator2`，device discovery 使用 `adbutils`。
- [x] 阻塞 API 包进 `asyncio.to_thread()`，避免直接阻塞 event loop。
- [x] registry/specs 不直接 import `uiautomator2` / `pymobiledevice3`。
- [x] 设备缺失不能算通过：prior smoke 记录 `status=blocked`；最终 DoD 用真实 emulator pass。

**挂载点反向核对（可卸载性）**：

- [x] Driver 挂载点集中在 `src/pymobile_mcp/drivers/android.py`。
- [x] Tool handler 挂载点集中在 `src/pymobile_mcp/tools/android.py`，registry 只有注册调用。
- [x] Live smoke 单独在 `tests/android_live_smoke.py`，不提交截图临时文件。
- [x] Roadmap / goal-state 回写只涉及本 feature 进度。

## 3. 验收场景核对

- [x] **S1**：已授权 Android 设备连接 → `mobile_list_available_devices` 返回该设备，platform 为 `android`。
  - Evidence: `android-live-ui-slice-live-smoke.md`，device `emulator-5554`。
- [x] **S2**：`mobile_get_screen_size` → 返回宽高为正数。
  - Evidence: `width=1080`、`height=2400`。
- [x] **S3**：`mobile_take_screenshot` → 返回 MCP image content。
  - Evidence: live smoke 脚本断言 `type=image`、`mimeType=image/png`，DoD command exit 0。
- [x] **S4**：`mobile_list_elements_on_screen` → 返回元素 JSON，至少包含 coordinates。
  - Evidence: live smoke element_count=41；fake-driver test 断言 coordinates shape。
- [x] **S5**：tap/swipe/type → driver 调用成功，错误时返回 structured error。
  - Evidence: live smoke action sequence exit 0；脚本会在 action structured error 时 fail。

**review 报告重点复核**：

- [x] Android discovery、screen_size/screenshot、elements、tap/double/long/swipe/type 已由 live smoke + unit covered。
- [x] registry/specs 不直接 import device libs。
- [x] no-device path blocked，不是 passed。
- [x] residual risk 为 emulator/UI 状态波动；已有 env override `PYMOBILE_MCP_ANDROID_TAP=x,y`。

**QA 报告重点复核**：

- [x] QA frontmatter `status=passed`。
- [x] Verification Matrix 覆盖 design 第 3 节、review focus 和 cleanliness。
- [x] failed / blocked 项为 none。
- [x] `python -m pytest` 与 live smoke 均在 QA 阶段重跑通过。

## 4. 术语一致性

- `Android live slice`：实现集中在 Android driver + handlers + live smoke，不扩展到 app/system/recording/iOS。
- `elements`：对外输出 filtered accessibility elements；raw XML 只在 `parse_uiautomator_xml()` 内部使用。
- `live smoke`：`tests/android_live_smoke.py` 是可复跑入口，记录 device id、screen size、element count、tap 坐标。

## 5. 领域影响盘点（提示而非代写）

- 新术语候选：Android live smoke、AndroidDriver、elements coordinates。
- 结构性选择：tool handler 层通过 `register_android_handlers()` 接入，driver library imports 被隔离到 driver/lazy handler。
- 流程级约束：真实设备缺失必须 blocked；不能把 skip/no-device 当 pass。
- 处理：本 roadmap 末尾 `parity-hardening-docs` 会收口 README 能力矩阵和 live smoke 文档；本 feature 不直接写 CONTEXT/ADR。

## 6. requirement delta / clarification 回写

- Design frontmatter `requirement: null`。
- 本 feature 是 roadmap 内部能力推进；仓库当前没有独立 requirements 文档需要更新。
- 能力状态通过 roadmap item `android-live-ui-slice` 回写为 done 表达。

## 7. roadmap 回写

- [x] `.codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-items.yaml` 中 `android-live-ui-slice` 已改为 `status: done`。
- [x] `.codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-roadmap.md` 第 5 节对应子 feature 已改为 `状态：done`，对应 feature 为 `2026-07-07-android-live-ui-slice`。
- [x] 后续 goal-state 将在 scoped commit 前推进到 `accepted` / `current_feature_index=2`。

## 8. attention.md 候选盘点

- 候选：Android live feature 的核心验收必须跑真实 device smoke；无设备时写 blocked，不可把 no-device skip 当 pass。
- 候选：uiautomator2 / adbutils import 不放 registry/specs；registry 只注册 handler。
- 处理：建议后续 parity-hardening-docs 或 cs-keep 沉淀；本 acceptance 不直接改 attention。

## 9. 遗留

- Android app lifecycle、orientation、button、open_url、save_screenshot 留给下一 feature。
- Android recording/crash 留给后续 feature。
- `pytest_asyncio` loop-scope deprecation warning 非本 feature blocker。
- live smoke tap point 是 heuristic；必要时用 `PYMOBILE_MCP_ANDROID_TAP=x,y` 覆盖。

## 10. 最终审计

- 验证证据来源：`android-live-ui-slice-qa.md`、`android-live-ui-slice-live-smoke.md`、`android-live-ui-slice-dod-results.json`。
- 聚合命令：
  - `.venv/bin/python -m pytest` → exit 0：37 passed。
  - `PYMOBILE_MCP_ANDROID_ACTIONS=1 PATH=.venv/bin:$PATH python tests/android_live_smoke.py` → exit 0：status passed，device `emulator-5554`。
- Scope gates：scope gate passed；DoD runner passed；evidence pack generated/passed。
- Review：independent Paseo review passed；OCR unavailable recorded as non-blocking fallback。
- QA：passed。
- Cleanliness：src/tests scoped grep clean；no temp screenshot files committed；device id appears only in evidence, not implementation.
- 结论：通过。

## Verdict

- Status: passed
- Next: update goal-state to accepted, scoped-commit, then continue `android-app-system-tools`.

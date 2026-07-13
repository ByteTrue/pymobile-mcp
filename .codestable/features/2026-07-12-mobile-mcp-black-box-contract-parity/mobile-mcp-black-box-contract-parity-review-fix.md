# mobile-mcp-black-box-contract-parity Review Fix（Round 1）

> Historical review-fix log：per-round pending/failed/blocked and lifecycle statements below describe evidence at that round and are superseded by the current `review/ready` state after an acceptance-found QA-fix; independent review and QA rerun are pending, and acceptance is not passed.

仅处理独立 review 的 REV-001~REV-011 blocking；REV-012/013 与同一修改自然覆盖。未修改 approved design、exception scope 或 upstream revision。

## REV-001 / REV-013 — MCP SDK protocol negotiation 与完整协议面

- RED：`test_stdio_negotiates_protocol_and_supports_ping` 在旧实现返回固定 `2025-11-25`，请求 `2024-11-05` 失败；手写 loop 对 `ping` 返回 method-not-found。
- GREEN：恢复 `mcp.Server.run` / `ServerSession`；仅保留 raw arguments contract transport adapter。SDK 继续负责 initialize negotiation、ping、cancel、并发和生命周期。
- VERIFY：固定 upstream 与 Python 均对 `2024-11-05` 回显旧版本、非法 `1900-01-01` 回落 `2025-11-25`；ping `{}`。CMD-002/003 goldens 新增三版本 initialize raw frames。

## REV-002 — 全部 contract cases 走真实 Python stdio

- RED：round-1 report 证明 89 个场景直接调用 `call_tool()`，仅 2 个 raw cases 走 stdio。
- GREEN：新增 `tests/mobile_mcp_stdio_fixture_server.py`；CMD-005/006 对每个 case 启动 SDK stdio fixture server、initialize、raw `tools/call`、保存 request/response frames。in-process runner仅保留 focused diagnostics。
- VERIFY：fleet 报告 `contract_case_count_including_wire=91`、`core_raw_stdio_case_count=87`、`review_raw_stdio_case_count=10`、`raw_frame_count=485`，所有 disposition `raw_stdio=true`、mismatches=[]。

## REV-003 — effects/backend/CLI argv

- RED：mutation test 把 click expected args 改为 `[999,999]`；旧 runner仍 pass。x-only swipe 实际为 center→20%，不是 upstream 80%→20%。
- GREEN：fixture recorder消费每个 `expected_effects`、`expected_backend_effects`、`expected_cli_argv`；记录 driver semantic effects、ADB/WDA coordinates、simctl argv、recording/file effects。center swipe改为 80%→20%；Android distance=0 用默认距离、iOS distance=0 保留零。
- VERIFY：effect mutation test真实失败；fleet 87 core + 10 review stdio cases effect_errors 全空。

## REV-004 — JS/Zod number coercion 与 timeLimit fraction

- RED：focused test 显示 `""`/空白/null/bool/[]/[5] 被 Python拒绝；`1.9` 被截断；Infinity处理文本不同。
- GREEN：集中 `_coerce_js_number` 复刻有限 JS Number 语义；拒绝 NaN/±Infinity；`timeLimit` 保留有限 int/float。
- VERIFY：新增 10 个 upstream wire review goldens（coercion/Infinity/time fraction/URL边界）；Python SDK stdio exact。`R-TIME-FRACTION` effect argv保留 `"1.9"`。

## REV-005 / REV-012 — manual/live 状态与 README

- RED：Android recording exit 1 被写为 blocked-environment；gate/DoD aggregate 为 passed；README supported 与 live evidence混淆。
- GREEN：Android recording明确 `failed`；PI/iOS/Simulator保持 blocked；manual aggregate为 `partial/blocked with one failed subtest`；gate/DoD顶层为 `partial`。README把 implemented contract 与本轮 live attestation分开。
- VERIFY：gate/dod JSON可解析，blocking数组保留所有 manual gaps；CMD command gate通过不再覆盖 manual 状态。

## REV-006 — iOS `/wda/screen` scale

- RED：fake client要求 `/wda/screen`/scale=3，旧 real driver调用 window size并返回1.0。
- GREEN：real 与 Simulator driver均读取 session `/wda/screen` 的 `screenSize` + `scale`，formatter据此缩放。
- VERIFY：real/simulator scale focused test均返回1179x2556@3；CMD-008 production formatter dimensions通过。

## REV-007 — URL raw startsWith

- RED：focused test证明旧 URL parser允许 uppercase `HTTP://`、拒绝 `https://`。
- GREEN：gate改为原始字符串 `startswith("http://"|"https://")`，unsafe env逻辑不变。
- VERIFY：uppercase得到 exact Actionable；empty-host `https://` 成功并记录 `openUrl` effect；两项 upstream/Python stdio review goldens exact。

## REV-008 — source 双向 coverage

- RED：在临时 upstream callback插入未映射 return，旧 marker validator不会失败。
- GREEN：从固定源码枚举26 tools、29 public callback returns、49 schema、8 guards、7 backend identities；与 manifest source refs/return identities双向比较。
- VERIFY：mutation触发 `return inventory mismatch`；CMD-007 91 core scenarios / source inventory / exception scope / bundle 全通过。

## REV-009 — CMD-008 production image path

- RED：spy test证明旧 `_python()` 没调用 `tools.contract.screenshot`。
- GREEN：拆出 production `_run_sips/_run_magick` seams；CMD-008 Python artifact调用真实 `contract.screenshot`，仅通过 seam强制 sips、magick、sips-fallback；不复制算法。
- VERIFY：spy test通过；报告记录 `sips-316`、ImageMagick 7.1.2-23；三 backend尺寸一致、PSNR=Infinity。

## REV-010 — exception state/scope/exit codes

- RED：pending ledger在旧 runner仍作为 approved behavior pass。
- GREEN：`validate_exception_ledger` 共同守护 approval、双向 IDs、tool/env/platform/device_type；actual text/`isError`仍由 stdio exact compare。
- VERIFY：pending→exit 2；scope mismatch→exit 1；approved fleet报告仅精确6 cases为 approved_exception，discovery/schema无 exception。

## REV-011 — iOS driver/session cleanup

- RED：连续两次 call 的 fake driver统计 `(connected, disconnected)=(2,0)`；real WDA session未DELETE。
- GREEN：ContextVar跟踪每个 call临时 driver，registry finally disconnect；real/Simulator disconnect DELETE session；共享 userspace tunnel/XCUITest task保留复用。
- VERIFY：连续 calls `(2,2)`；real WDA DELETE `/session/session`；61 tests通过。

## Gate summary

- CMD-001：61 passed。
- CMD-002/003：default/fleet三版本 initialize negotiation + 23/26 tools。
- CMD-004：24 core + 10 review upstream call/error goldens。
- CMD-005/006：SDK stdio逐 case raw frames + effects，default 93 / fleet 97 applicable calls，fleet完整91 contract cases。
- CMD-007：双向 source inventory、exception scope、bundle通过。
- CMD-008：production formatter path、backend versions、dimensions、PSNR通过。
- Manual aggregate仍为 partial：Android recording failed；PI/iOS/Simulator blocked。未伪装为 pass。

## Round 2：REV-016~REV-023

仅处理 round-2 blocking REV-016~REV-020 及同范围 REV-021~023；未修改 approved design、exception scope 或 upstream revision。

### REV-016 — JSON 域 JS Number / Zod issues / raw JSON types

- RED：round-2 对抗探针证明 `+0x10`、`[[5]]`、三字段 invalid 与 raw string/number/bool 不一致；旧实现只返回首个 issue 且使用 Python 类型名。
- GREEN：`registry.py` 集中实现 JSON type names、JS Array-to-string/Number coercion 与一次聚合全部 Zod issues；`stdio.py` raw arguments 使用相同 JSON type names。新增 signed radix、nested array、multi-invalid、raw scalar 六个 review cases。
- VERIFY：CMD-004 从固定 upstream 真实 stdio 捕获 `R-COERCE-SIGNED-RADIX`、`R-COERCE-NESTED-ARRAY`、`R-MULTI-INVALID`、`R-RAW-*`；CMD-005/006 Python SDK stdio 分别 99/103 cases exact，16 个 review cases 全部 `raw_stdio=true`。

### REV-017 — backend source 双向 inventory

- RED：round-2 mutation 在 backend source 新增调用时旧 marker/group 仍可通过。
- GREEN：CMD-007 枚举固定 upstream Android/iOS/WebDriverAgent/mobile-device 及 Python Android/iOS/WDA/simctl backend 调用，按 identity 的 count+SHA 与 manifest 双向相等；report 保存逐调用 path/line/source inventory。
- VERIFY：`test_source_coverage_rejects_unmapped_backend_source_mutation` 向 `ios_simulator.py` 注入未映射 `_simctl` branch 后 validator exit 1；CMD-007 当前 91 scenarios、backend inventory、bundle、exception scope 全通过。

### REV-018 — Safari fallback session cleanup

- RED：round-2 连续 fallback 发现每次 `POST /session` 只清理 base session，Safari session 累积。
- GREEN：每个 Safari fallback session 创建后立即 `DELETE /session/<id>`；DELETE 失败时保留 ID，由 disconnect 再清理。
- VERIFY：`test_ios_open_url_fallback_deletes_all_created_sessions_across_calls` 连续两次 fallback，断言全部创建 session 均 DELETE 且 fallback set 为空；full pytest 通过。

### REV-019 — production effect/backend/CLI seams

- RED：round-2 mutation 证明 screenshot write 与 simulator argv 可由 scenario 自身合成，破坏 production backend 仍不失败。
- GREEN：screenshot 只从 production `_write_screenshot(path,data)` 记录；Android 调用真实 `AndroidDriver.swipe→adb.shell(argv)`；iOS 调用真实 `IOSDriver.swipe→WDA endpoint/payload`；Simulator 调用真实 `start_simctl_recording→create_subprocess_exec(argv)`；recording CLI 从 production `_observe_recording_cli` 实参记录。
- VERIFY：`test_effect_evidence_uses_production_screenshot_adb_wda_and_simctl_seams` 固定 write path/bytes、ADB argv、WDA endpoint/payload、simctl argv；scenario expected 同时固定 WDA endpoint，任一 production 参数 mutation 均失败。CMD-005/006 effects 无 mismatch。

### REV-020 — CMD-008 backend availability/exit 2

- RED：round-2 证明旧脚本强制 Sips 可用、Sips mode 可落到 Magick、backend 缺失 RuntimeError 返回 exit 1。
- GREEN：先读取 production Sips/Magick 版本并按 mode 校验依赖；缺任一指定 backend 抛 `ExceptionBlockedError` 并 exit 2；Sips mode 禁止 Magick fallback，fallback mode 明确要求两者可用。
- VERIFY：`test_image_backend_availability_matrix_and_sips_no_fallback` 覆盖 Sips-only/Magick-only/fallback availability 与禁止静默降级；CMD-008 记录 `sips-316`、ImageMagick `7.1.2-23`，3 modes exit 0。

### REV-021~023 — machine audit / SDK range / artifact status

- RED：round-2 report 仅有 exception IDs、`mcp>=1.12.0` 且 scenario/baseline 状态不一致。
- GREEN：CMD-005/006/007 reports 逐 exception 记录 approval、allowed IDs、scope 与 case disposition；dependency 精确约束 `mcp==1.28.1`，CMD-005/006 对实际 1.28.1 与 manifest 做 fail-closed 校验并记录；scenario 标记 approved，goal-state baseline 统一为 `4ce5dfc...`。
- VERIFY：`assert-default.json`/`assert-fleet.json` 包含 `python_mcp_version=1.28.1` 与逐 case disposition；`source-coverage.json` 包含完整 exception summaries；scope/evidence/goal baseline 一致。

## Round 2 Gate summary

- CMD-001：66 passed。
- CMD-002/003：固定 upstream default/fleet，23/26 tools。
- CMD-004：24 core + 16 review upstream call/error goldens（40 captures）。
- CMD-005/006：default 99 / fleet 103 Python SDK stdio cases；16 review cases；effects/backend/CLI 无 mismatch。
- CMD-007：91 source-linked scenarios、双向 backend inventory、mutation guard、exception audit、bundle 全通过。
- CMD-008：实际 backend/version 校验、3 modes、dimensions/PSNR 全通过。
- Manual aggregate 仍为 partial：Android recording failed；PI/iOS/Simulator blocked。未伪装为 pass；本报告不自行判定 review passed。

## Round 3：REV-024~REV-026

仅处理 round-3 blocking REV-024~REV-026；未修改 approved design、exception scope 或 upstream revision。

### REV-024 — JS Number string grammar

- RED：focused test 证明旧 `_coerce_js_number` 接受 Python 扩展 `1_000` 与小写 `infinity`，两者均未抛出 `ValueError`。
- GREEN：字符串先按 ECMAScript StrWhiteSpace 集合裁剪，再仅接受无符号 radix、JS decimal/exponent 与大小写精确的 `Infinity` grammar；不再把 Python `float()` 扩展语法当作 JS Number。
- VERIFY：固定 upstream CMD-004 新增 `R-COERCE-UNDERSCORE`、`R-COERCE-LOWER-INFINITY` 两项 raw stdio golden；CMD-005/006 各 18 个 review cases exact，既有 `R-MULTI-INVALID` 全 issues 文本保持 exact。

### REV-025 — adbutils shell 参数层

- RED：production seam 期望 `AdbDevice.shell(["input", "swipe", ...])` 时，旧实现实际传入重复的 `["shell", "input", "swipe", ...]`。
- GREEN：`AndroidDriver.swipe` 删除 argv 首项 `shell`，五个 Android swipe scenario backend expectations 同步 production seam。
- VERIFY：focused production seam 通过；CMD-005/006 effects/backend 无 mismatch。授权目标 `emulator-5554` 的 live swipe 检查实际 exit 2：当前没有该授权 emulator，仅有一台非目标 Android endpoint；按规则记录 blocked，未计 pass。

### REV-026 — direct backend sinks fail-closed

- RED：分别向 source copy 注入 direct `adbutils.adb.device(...).shell(...)` 与 `subprocess.run(["xcrun", "simctl", ...])`，旧完整 CMD-007 validator 均 exit 0。
- GREEN：Python backend inventory 收敛到 ADB helper/direct shell、WDA request/helper、simctl helper/direct subprocess sinks，并刷新 count+SHA manifest。
- VERIFY：新增参数化 mutation test 对两种 direct sink 都执行完整 CMD-007 CLI 并断言 exit 1 与 `backend inventory mismatch`；正常 CMD-007 exit 0，91 source-linked scenarios 通过。

## Round 3 Gate summary

- Focused：5 passed（Number grammar、multi-issue、ADB seam、两种完整 CMD-007 mutation）。
- CMD-001：68 passed。
- CMD-002/003：固定 upstream default/fleet 重新 capture，23/26 tools。
- CMD-004：24 core + 18 review upstream call/error goldens（42 captures）。
- CMD-005/006：default 101 / fleet 105 Python SDK stdio cases；18 review cases；effects/backend/CLI 无 mismatch。
- CMD-007：91 source-linked scenarios、direct sink 双向 backend inventory、两种完整 validator mutation、bundle/exception scope 全通过。
- CMD-008：3 production image backend modes通过。
- Bundle SHA-256：`4ee453d208a024ada71c0cfd7cf82357c7f51bad67339fb942ae955ab41409ce`。
- Manual aggregate 仍为 partial-with-failure；本轮 emulator swipe 为 blocked exit 2，Android recording仍 failed，PI/iOS/Simulator仍 blocked。本报告不自行判定 review passed。

## Round 4：REV-027~REV-028

仅处理 round-4 blocking REV-027~REV-028；未修改 approved design、exception scope 或 upstream revision。

### REV-027 — 多行 direct backend sinks fail-closed

- RED：把多行 `adbutils.adb.device(...).shell(...)` 与多行 `subprocess.run(["xcrun", "simctl", ...])` 分别注入 driver source copy；旧完整 CMD-007 均 exit 0。
- GREEN：Python backend inventory 改用 stdlib `ast` 完整解析文件，识别 direct ADB shell、xcrun simctl subprocess、WDA requests 与异步 helper callers；每项继续保存 identity、起始 line 与完整归一化 source。
- VERIFY：两种多行 mutation 均执行完整 CMD-007 CLI，分别 exit 1 且 stderr 包含 `backend inventory mismatch`；正常 CMD-007 exit 0，91 source-linked scenarios 通过。

### REV-028 — arbitrary int / JavaScript Infinity parity

- RED：`_coerce_js_number(10**400)` 在旧实现抛出 Python `OverflowError: int too large to convert to float`，没有生成上游 Zod issue。
- GREEN：任意精度 Python `int` 转 float 溢出时按符号映射为 `_NonFiniteNumber(±Infinity)`，复用既有 non-finite issue formatter。
- VERIFY：固定 upstream CMD-004 新增 `R-COERCE-HUGE-INTEGER` raw stdio golden，收到 `Infinity` non-finite Zod issue；CMD-005/006 Python SDK raw stdio exact，既有 coercion 与 multi-issue cases 保持 exact。

## Round 4 Gate summary

- Focused：4 passed（超大整数、multi-issue、两种多行完整 CMD-007 mutation）。
- CMD-001：68 passed。
- CMD-004：24 core + 19 review upstream call/error goldens（43 captures）。
- CMD-005/006：default 102 / fleet 106 Python SDK stdio cases；19 个 review cases；effects/backend/CLI 无 mismatch。
- CMD-007：91 source-linked scenarios、AST backend inventory、两种多行 validator mutation、bundle/exception scope 全通过。
- CMD-008：3 production image backend modes 通过。
- Bundle SHA-256：`59c88d2baa4bbfa2540c5db6431558c6b03866f5155b022172a992923d73cce5`。
- Manual aggregate 仍为 partial-with-failure；本报告不自行判定 review passed，下一步为独立 code review round 5。

## Round 5：REV-029~REV-032 与文档 nit

仅处理 round-5 `REV-029`~`REV-032` 和同一报告的 regression checklist nit；未修改 approved design、exception scope 或 fixed upstream revision。

### REV-029 — 负 non-finite Zod received

- RED：focused test 对 `-(10**400)` 期望固定 upstream 的 `received: "Infinity"`，旧实现实际为 `-Infinity`。
- GREEN：`_NonFiniteNumber` 仅区分 `NaN` 与 infinity；正负 infinity wire received 均为 `Infinity`。
- VERIFY：固定 upstream 新增 `R-COERCE-HUGE-NEGATIVE-INTEGER` raw stdio golden；CMD-005/006 Python SDK stdio exact。focused test同时守护 `NaN` 仍为 `NaN`。

### REV-030 — radix int→float overflow

- RED：focused test 对 `"0x" + "f" * 400` 触发未包装的 `OverflowError: int too large to convert to float`。
- GREEN：radix parse 后复用整数 coercion，让任意精度 int overflow进入相同 non-finite issue。
- VERIFY：固定 upstream 新增 `R-COERCE-RADIX-OVERFLOW` raw stdio golden，received 为 `Infinity`；CMD-005/006 exact。

### REV-031 — 外部 upstream checkout 的 clean-CI 行为

- RED：round-5 review 的隔离环境证明绝对路径缺失时 source/backend tests 泄漏 `FileNotFoundError`。
- GREEN：仅依赖外部 checkout 的三项 test instance 通过 `_require_upstream_checkout` 显式 `pytest.skip`；CMD-007 仍使用 checklist 固定真实 upstream 命令，未降级。
- VERIFY：`PYMOBILE_MCP_UPSTREAM_SOURCE=/nonexistent/clean-ci ... pytest -q` full suite为 `67 passed, 3 skipped`，没有 `FileNotFoundError`；模块focused为`20 passed, 3 skipped`；真实 CMD-007 exit 0。

### REV-032 — Sips test portability 与 portable no-scaling

- TDD exception：这是测试环境可用性守护，不改变 runtime 行为；直接增加 backend availability skip 与 portable contract assertion。
- GREEN：Sips bytes assertion仅在 `_sips_available()` 时执行；新增强制 `_scaling_available=False` 的 PNG bytes/mime no-scaling test。
- VERIFY：focused 四项测试通过；真实 CMD-008 继续使用 Sips 316、ImageMagick 7.1.2-23 三 backend modes，exit 0。

### 文档 nit

- TDD exception：纯文档修订。
- regression checklist full-suite count更新为70，并合并重复 blocked-as-pass 规则。

## Round 5 Gate summary

- Focused RED/GREEN/VERIFY：负超大整数和 radix overflow 均先失败后通过；NaN、portable no-scaling、Sips backend guard通过。
- Clean-CI isolation full suite：`67 passed, 3 skipped`，外部 oracle缺失显式 skip。
- CMD-001：70 passed。
- CMD-004：24 core + 21 review upstream call/error goldens（45 captures）。
- CMD-005/006：default 104 / fleet 108 Python SDK stdio cases；21 个 review cases；raw frames/effects 无 mismatch。
- CMD-007：固定真实 upstream、91 source-linked scenarios、bundle/exception scope全通过。
- CMD-008：真实 Sips/ImageMagick/fallback 3 modes通过。
- Bundle SHA-256：`4016372afa6d7482d3a8b1059b06c28ca5056c34fceccbdc0aba89f7cdbbef9e`。
- Manual aggregate仍为 partial-with-failure；本报告不自行判定 review passed，下一步为独立 code review round 6。


## Round 6：REV-033

仅处理 round-6 blocking `REV-033`；未修改 approved design、exception scope 或 fixed upstream revision。radix focused test按本轮许可扩为 hex/bin/oct 参数化，未扩大 runtime 范围。

### REV-033 — 超过 Python digit limit 的 raw JSON 整数

- RED：新增正/负 5000 位 raw JSON request（request id 5001/5002）；旧 transport 两例均在 3 秒内无对应 response，实际为 `TimeoutError: no response for request`。
- GREEN：`stdio.py` 的 `json.loads` 使用局部 `parse_int`；普通整数继续调用并返回内建 `int`，仅合法十进制 token 超过当前 Python digit limit 时按符号映射为 `±Infinity`，未调用全局 `set_int_max_str_digits`。MCP SDK dispatch 前的 JSON-mode re-dump 使用局部 request model 配置保留 infinity，确保 registry 输出固定上游的 `received: "Infinity"` Zod issue。
- VERIFY：focused 5000 位正负 request 均返回带原 request id 的 `CallToolResult`，不是 notification/timeout；固定 upstream 新增 `R-COERCE-5000-DIGIT-POSITIVE/NEGATIVE` 两项 raw stdio golden，Python default/fleet SDK stdio均 exact。`_parse_int` focused test同时守护正常 `123` 的类型仍为 `int`；radix overflow focused test参数化覆盖 hex/bin/oct。

## Round 6 Gate summary

- Focused RED：2 failed，均为 5000 位 request timeout；GREEN/VERIFY：6 passed（正负 raw stdio、正常/超限 parse、hex/bin/oct radix）。
- CMD-001/full pytest：76 passed。
- Clean-CI isolation full suite：73 passed, 3 skipped；外部 upstream checkout缺失仍显式 skip。
- CMD-004：24 core + 23 review upstream call/error goldens（47 captures）。
- CMD-005/006：default 106 / fleet 110 Python SDK stdio cases；23 个 review cases；新正负 5000 位 response均保留 request id并 exact。
- CMD-007：91 source-linked scenarios、bundle/exception/source/backend coverage通过。
- Bundle SHA-256：`72ddc9e5fbfbf18fc3e091236c05606bff1457b48898035cbcde6dcc2ac88c09`。
- Manual aggregate仍为 partial-with-failure；本报告不自行判定 review passed，下一步为独立 code review round 7。

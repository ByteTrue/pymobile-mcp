# mobile-mcp-black-box-contract-parity 实现证据

> Historical implementation log：per-round pending/failed/blocked and lifecycle statements below describe evidence at that round and are superseded by the current `review/ready` state after an acceptance-found QA-fix; independent review and QA rerun are pending, and acceptance is not passed.

## 基线预检

- 基线 `4ce5dfc` 工作树干净；设计基线为 `ffa6683`，其后仅包含已批准 goal package。
- 初始 `.venv/bin/python -m pytest -q` 被本机自动加载的 `xonsh` pytest 插件阻塞（`getpwuid(): uid not found: 501`）；`-p no:xonsh` 可进入项目测试，后续在 CMD-001 配置中做最小隔离。

## Step 1 — Upstream oracle

- 退出信号：CMD-002/003/004/007 全部 exit 0；provenance、raw frames、machine reports 完整。
- RED：`.venv/bin/python -m pytest -q -p no:xonsh tests/test_black_box_contract.py` 首次失败，报告 `scripts/capture_mobile_mcp_contract.py` 不存在。
- GREEN：新增固定 revision/lock/Node/npm 校验、真实 stdio raw probe、default/fleet/call capture、source/exception/bundle coverage 与 timeout/image 命令入口；golden 均由固定 upstream 实际 stdio 产生。
- VERIFY：CMD-002 exit 0（23 tools）；CMD-003 exit 0（26 tools）；CMD-004 exit 0（24 个需要 wire golden 的 CallToolResult/JSON-RPC error）；CMD-007 exit 0（91 scenarios，source-linked/disposition 100%）。
- 失败修复证据：CMD-004 初次 timeout 定位为 probe 在存活子进程上阻塞读取 stderr；修复为仅在进程退出后读取。第二次发现 recording fake 在 listener 注册前同步发 `close`；改为 next-tick。第三次发现 null arguments 是 JSON-RPC error 而非 CallToolResult；raw capture 保留 error frame，不做 false 规范化。
- TDD exception：oracle capture 是测试基础设施且 expected 必须来自 upstream，不能先由 Python test 构造 expected；以真实 RED capture 失败、固定 upstream raw frames、machine reports 和 source coverage 作为替代证据。
- 影响面：`scripts/` contract commands、`tests/fixtures/mobile_mcp/` deterministic fake/bundle/goldens、feature evidence。
- 清洁度：无临时 debug 输出；无 Python specs/scenarios 反向生成 upstream golden；无 go-ios/mobilecli runtime fallback（mobilecli 仅 oracle 测试 fake）。

## Step 2 — 最小 formatter/error wrapper 微重构

- 退出信号：CMD-001 通过，driver side effects 未改变，diff 仅职责移动。
- TDD exception：纯职责搬迁，不改变公开行为；以 refactor 前后同一 `tests/test_contract_registry.py` 47/47 passed 作为替代证据。
- GREEN：新增 `tools/contract.py`，集中 text/Actionable/unexpected 格式化原语；Android handlers 与 registry 复用同一 text 构造。
- VERIFY：`.venv/bin/python -m pytest -q -p no:xonsh tests/test_contract_registry.py tests/test_black_box_contract.py` → 48 passed。
- 精确性：dict 使用 insertion order + compact separators 复刻 `JSON.stringify`，不排序 key；Actionable suffix 无条件增加 `.`，保留上游 message 自带句点形成的双句点。
- 清洁度：无 driver 调用、参数或 side effect 变化；无新增 runtime dependency。

## Step 3 — Initialize / ToolSpec parity

- 退出信号：CMD-005/006 的 raw InitializeResult 与完整 tool arrays deep-equal，fleet discovery 无豁免。
- RED：新增 default/fleet `Tool.model_dump(exclude_none=True)` 对 upstream wire golden 的直接 equality；首次两例均失败（缺 `$schema`/execution，额外 `additionalProperties`/空 required，缺 fleet tools）。
- GREEN：server metadata 固定为 `mobile-mcp/0.0.1`，capabilities 仅 `tools.listChanged=true`；Tool schema/description/constraints/execution 对齐；`MOBILEFLEET_ENABLE=1` 按 upstream 顺序注册 3 个工具，runtime 返回已批准 Actionable exception，不调用 mobilecli。
- VERIFY：focused tool object tests 2 passed；Python raw stdio default 23 / fleet 26 的 initialize 与完整 tools arrays 分别 deep-equal upstream golden。
- 影响面：`server.py`、`tools/specs.py`、`tools/registry.py`、`tools/fleet.py`。
- 清洁度：fleet discovery 不使用 exception；runtime 无 mobilecli/go-ios fallback。

## Step 4 — Success branch parity

- 退出信号：scenario disposition coverage=100%，exact/approved_exception/blocked 分开统计，blocked 不算 pass。
- RED：新增 upstream template success matrix；首个 screen-size case 返回 Python JSON 而失败。新增 Sips bytes 对 upstream CallToolResult 精确比较，首次 PNG/mime 不同而失败。
- GREEN：23 个 core handler 改为 upstream 自然语言/JSON-string/image 模板；Android physical public type 固定 `emulator`；iOS Simulator 增加 booted `simctl` discovery、simctl app/system/recording 与 WDA UI driver；截图执行 PNG header/dimension validation 和 conditional JPEG scaling。
- VERIFY：`assert_mobile_mcp_contract.py` 实际执行 scenario runner；default 83/83、fleet 87/87 passed，fleet 四项与 real iOS recording 两项精确记录 `approved_exception`，无 blocked。
- 影响面：`tools/android.py`、`tools/contract.py`、`drivers/ios_simulator.py`、recording state；driver side effect 参数由 scenario fake 记录。

## Step 5 — Validation / Error parity

- 退出信号：error disposition coverage=100%，包含 coercion/min/max/null/unknown 与 `isError` omission/true。
- RED：raw upstream error goldens 先证明 Python structured JSON envelope、`isError=false`、bool/enum 文本与 upstream 不同。
- GREEN：registry 实现 Zod-compatible required/type/coercion/enum/min/max 文本；未知工具/schema/unexpected/screenshot 为 `isError=true`；Actionable/approved exception 省略 `isError`；raw stdio 精确保留 null/array JSON-RPC errors。default env 的 fleet tool 为 unknown。
- VERIFY：CMD-005 focused → 23 tools + 83 scenarios passed；CMD-006 focused → 26 tools + 87 scenarios passed。validator negative tests证明漏 case、错 exception scope、stale bundle 均被拒绝；required_groups 对实际 source branch marker 与 cases 映射。

## Step 6 — Image parity

- 退出信号：fake bytes 精确；upstream/Python artifacts 尺寸及 PSNR 达标，错误 `isError=true`。
- RED：Sips golden test 首次得到 Python PNG；实现 scaling 后首次发现 oracle fake scale=1 产出 486x1080，修正 upstream hook 从真实 callback 注入 scale=3 后重 capture。
- GREEN：no-scaling 保持 PNG；Sips 使用 `-Z`（162x360）；ImageMagick/fallback 使用 width resize（360x800）；invalid/zero/scaling failure 返回 exact `Error:`。
- VERIFY：Sips bytes 与 upstream golden 精确；CMD-008 focused 3 backends passed，尺寸一致且 PSNR gate 通过。
- 清洁度：测试 hook 经 `node --check`；golden 由 checked hook 下真实 upstream stdio 重生成。

## Step 7 — User-path evidence

- TDD exception：真实 Pi/设备环境不可自动制造 RED；以 `--no-session` Pi run、Android physical 原始 exit/stdout、iOS/CoreSimulator blocked 原因和 exact scenario matrix 为替代证据。
- Android：UI/action exit 0；app/system exit 0（destructive 未授权单列 blocked）；crash real-source exit 0；recording 被设备 `INVALID_LAYER_STACK` 阻塞，未计 pass。
- iOS：当前 usbmux 无授权真机，相关 scripts exit 2；CoreSimulatorService connection refused，Simulator live blocked。两项均未聚合成 pass。
- Pi：0.80.6 新 session 能发现 cached 23-tool server/prefixed names，但首轮只暴露 generic `mcp`，direct-tools gate blocked；没有提交 `/tmp` JSONL/HTML。
- 证据：`evidence/pi-redacted.md`、`evidence/live-evidence.md`、Step 7 窄修复说明。

## Step 8 — 文档收口

- TDD exception：纯文档；以 grep/diff、scenario/exception report 与 regression command 可执行性为替代证据。
- README/CHANGELOG/regression checklist 已同步 23/26 contract、自然语言/error 语义、fleet/real-iOS approved exceptions、iOS Simulator simctl+WDA 和 no fallback。
- Live scripts 更新为解析 upstream natural-language/image contract，不再反向要求 Python-native JSON envelope。
- 清洁度：没有设备标识、凭证、本地 Pi session 或 HTML；exception ledger scope/approval 未扩大。

## Implementation gates / final audit

| Gate | 结果 |
|---|---|
| CMD-001 | exit 0；61 passed；JUnit + timeout report 落盘 |
| CMD-002 | exit 0；真实 upstream default initialize protocol matrix + 23 tools |
| CMD-003 | exit 0；真实 upstream fleet initialize protocol matrix + 26 tools |
| CMD-004 | exit 0；24 core + 10 review-focused 真实 upstream CallToolResult/raw error goldens |
| CMD-005 | exit 0；default SDK stdio 83 core + 10 review calls；逐 case raw frames/effects，mismatches=[] |
| CMD-006 | exit 0；fleet SDK stdio 完整 91 contract cases + 10 review cases；逐 case effects，6 approved_exception |
| CMD-007 | exit 0；91 scenarios，源码 tools/returns/schema/guards/backends 双向 inventory、exception scope、bundle 全通过 |
| CMD-008 | exit 0；Python artifacts 走 production formatter；记录 Sips/ImageMagick versions；尺寸/PSNR 通过 |

- 所有 8 个 checklist steps 均 done；checks 保持 pending，留给 acceptance gate。
- Current bundle SHA-256：`7d0ded471b2c21ce1024581e79da9ecb02d91b4b01bc32e6ca4d13f302d366df`；exception ledger SHA-256：`356b18cbf93ffd5a9e222e15c8b9a3c64f40fd334cd56bb67f83077fdd9cf82f`。
- Final audit：`compileall`、node hook syntax、`git diff --check` 通过；新增测试/脚本无 TODO/FIXME/XXX；无 staged files。
- Initial implementation manual-evidence checkpoint（superseded by current evidence pack）：PI-001 and some live paths were not yet complete at that checkpoint；current PI-001 is passed and LIVE-001 is 16/16.
- 交付物索引：public server/spec/formatter/error/fleet/simulator code；deterministic oracle scripts/fakes/goldens/raw frames/reports/images；scenario matrix tests；Pi/live redacted evidence；README/CHANGELOG/regression checklist。
- 知识候选：Pi MCP direct tools 使用 server-prefixed names 且可能晚于首轮初始化；Android physical 某些 display state 会让 `screenrecord` exit 218；后续 acceptance 决定是否沉淀。

## Review-fix round 1

- REV-001~REV-011 blocking 已按 `mobile-mcp-black-box-contract-parity-review-fix.md` 窄修复；REV-012/013 随 REV-005/001 自然覆盖。
- 权威 parity gate 现为 MCP SDK stdio：fleet 覆盖完整 91 contract cases，另有10个 review-focused raw cases；每 case 保留 raw frames并消费 effects/backend/CLI argv。
- Command gates CMD-001~008 passed；manual aggregate仍 partial（Android recording failed；PI/iOS/Simulator blocked），不自批 review passed。

## Review-fix round 2

- REV-016：补齐 JSON 域 signed radix/nested array/multi-issue/raw scalar exact 语义与 upstream/Python SDK stdio raw goldens。
- REV-017：backend source gate 扩为 upstream Android/iOS/WebDriverAgent/mobile-device 与 Python Android/iOS/WDA/simctl 双向 inventory，并保留未映射 branch mutation test。
- REV-018：Safari fallback session 每次完成即 DELETE，失败留到 disconnect；连续两次 session-count test 通过。
- REV-019：effect/backend/CLI 记录改为 production seam 实参；新增 screenshot write、ADB、WDA endpoint/payload、simctl argv 直接 mutation guards。
- REV-020：CMD-008 指定 backend 缺失统一 blocked/exit 2；Sips mode 禁止静默落到 Magick；availability matrix 通过。
- REV-021~023：machine reports 增加逐 exception approval/allowed IDs/scope/disposition；`mcp==1.28.1` fail-closed 并记录实际版本；scenario/baseline 状态统一。
- RED/GREEN/VERIFY 逐项证据见 `mobile-mcp-black-box-contract-parity-review-fix.md`；CMD-001~008 均 exit 0，full pytest 66 passed，bundle SHA-256 `f7a2e3f07f9441545ea13d282f7cb65c41c41046226c0eff4bfb4c4fd81dbacf`。
- Manual aggregate 保持 partial-with-failure；下一步仅为 round-3 独立 review，不自行判定 passed。

## Review-fix round 3

- REV-024：JS Number string grammar 拒绝 Python `1_000`/小写 `infinity` 扩展；新增两项固定 upstream/Python SDK stdio goldens，既有 multi-issue exact 保持不变。
- REV-025：`AdbDevice.shell` argv 删除重复 `shell`；production seam 与五项 Android swipe scenario 同步。授权目标 emulator live 实际 exit 2/block，不计 pass。
- REV-026：backend inventory覆盖 direct adbutils shell、direct subprocess xcrun simctl、WDA request 与 helper callers；两种 direct mutation 均执行完整 CMD-007 并要求 exit 1。
- RED/GREEN/VERIFY 逐项见 `mobile-mcp-black-box-contract-parity-review-fix.md`；CMD-001 为 68 passed，CMD-002~008 均 exit 0，bundle SHA-256 `4ee453d208a024ada71c0cfd7cf82357c7f51bad67339fb942ae955ab41409ce`。
- Manual aggregate 仍为 partial-with-failure；goal state 回到 `review/ready` 等待 round-4 独立 review，本实现线程不自行判定 passed。


## Review-fix round 6

- REV-033：stdio `json.loads` 使用局部 `parse_int`；正常整数保持 `int`，仅超过 Python digit limit 的正负十进制整数映射为 `±Infinity` 并穿过 MCP SDK dispatch 到 registry；未全局修改 digit limit。
- RED/GREEN/VERIFY 见 `mobile-mcp-black-box-contract-parity-review-fix.md`；正负 5000 位固定 upstream/Python raw stdio均返回带对应 request id 的 exact Infinity Zod `CallToolResult`，focused 6 passed。
- CMD-001 为 76 passed；clean-CI 为 73 passed/3 skipped；CMD-004/005/006/007 均 exit 0；bundle SHA-256 `72ddc9e5fbfbf18fc3e091236c05606bff1457b48898035cbcde6dcc2ac88c09`。
- Manual aggregate仍为 partial-with-failure；goal state回到 `review/ready` 等待 round-7 独立 review，本实现线程不自行判定 passed。

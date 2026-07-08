---
doc_type: feature-acceptance
feature: 2026-07-07-contract-registry-scaffold
status: passed
accepted: 2026-07-09
round: 1
---

# contract-registry-scaffold 验收报告

> 阶段：阶段 3（验收闭环）
> 验收日期：2026-07-09
> 关联方案 doc：`.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-design.md`

## 1. 接口契约核对

**接口示例逐项核对**：

- [x] `list_tool_specs()`：返回 23 个 `ToolSpec`，名称顺序与 `tests/fixtures/mobile_mcp_core_tools.json` 一致。
- [x] `call_tool(name, args)`：已知但未实现工具返回 MCP `TextContent`，文本是 JSON envelope：`status=error`、`code=not_implemented`、`tool=<原工具名>`。
- [x] `PyMobileMCPServer`：注册 `list_tools` / `call_tool(validate_input=False)`，MCP SDK 参数校验不抢占项目 structured error。
- [x] CLI entry point：`pymobile-mcp = pymobile_mcp.cli:main` 保持在 `pyproject.toml`，`from pymobile_mcp.cli import main` 可导入。

**名词层“现状 → 变化”核对**：

- [x] `ToolSpec` 落在 `src/pymobile_mcp/tools/specs.py`，承载 `name/title/description/input_schema/annotations/content_kind`。
- [x] `ToolError` 层级落在 `src/pymobile_mcp/errors.py`，覆盖 `NotImplementedToolError`、`UnsupportedPlatformError`、`DeviceNotFoundError`、`InvalidArgumentError`、`DriverError`。
- [x] schema parity fixture 落在 `tests/fixtures/mobile_mcp_core_tools.json`，记录 mobile-mcp `server.ts` source path、git revision、captured date 和 23 个 core tools。

**流程图核对**：

- [x] MCP server starts → load 23 specs：`PyMobileMCPServer._register_tools()` 从 `list_tool_specs()` 生成 SDK tool。
- [x] `list_tools` returns specs：server handler、stdio client 测试均覆盖。
- [x] `call_tool` known?：`get_tool_spec()` 区分 unknown tool 与 known tool。
- [x] known + no handler → `not_implemented`：`TOOL_HANDLERS.get(name)` 为空时抛 `NotImplementedToolError`。
- [x] implemented seam → `register_tool_handler()` / `unregister_tool_handler()` 已有成功分支测试，后续真实 driver 可接入。

## 2. 行为与决策核对

**需求摘要逐项验证**：

- [x] Python 包骨架存在：`src/pymobile_mcp/`、`tools/`、`drivers/`、`server.py`、`cli.py` 已落盘。
- [x] MCP client 能列出 23 个常驻 core tools：registry、server handler、stdio client 三路径由 `python -m pytest` 覆盖。
- [x] 所有未接通 handler 返回 stable structured error：direct/server/stdio 路径覆盖 `not_implemented`、unknown `invalid_argument`、missing required、enum invalid。

**明确不做逐项核对**：

- [x] 不公开 `mobile_get_page_source`：fixture excluded tools 与 `CORE_TOOL_NAMES` / server list / stdio list 无交集；unknown call 返回 `invalid_argument`。
- [x] 不注册 remote fleet 三工具：`mobile_list_remote_devices` / `mobile_allocate_remote_device` / `mobile_release_remote_device` 均只出现在 fixture excluded list，不在 core specs。
- [x] 不接入真实 Android/iOS driver：registry/specs 无 `uiautomator2` / `pymobiledevice3` import；真实设备能力留给后续 feature。
- [x] 不实现截图、录屏、元素解析等设备能力：本轮只提供 stub handler 和 driver contract dataclass。

**关键决策落地**：

- [x] 外部边界用 `ToolSpec + async handler`：`ToolSpec` manifest + `ToolHandler` / `TOOL_HANDLERS` seam 已实现。
- [x] registry 数据集中：23 个 core specs 集中在 `src/pymobile_mcp/tools/specs.py`，测试 fixture 单点对齐。
- [x] `mobile_take_screenshot` 标记 image content：`content_kind="image"` 且 fixture 有 `content_kind=image`。

**挂载点反向核对（可卸载性）**：

- [x] CLI entry point：`pyproject.toml [project.scripts]` 已指向 `pymobile_mcp.cli:main`，无需改 script 名称。
- [x] MCP tool registry：新增文件集中在 `src/pymobile_mcp/tools/`；移除本 feature 可从 `tools/specs.py`、`tools/registry.py`、server import 回退。
- [x] Contract tests：新增 `tests/test_contract_registry.py` 和 fixture；没有散落到其他测试目录。
- [x] 反向 grep：`src/` scoped grep 未命中 excluded tools 或设备库 import；`tests/` 只用 excluded names 做反向断言。

## 3. 验收场景核对

- [x] **S1**：触发 `list_tools` → 返回 23 个 mobile-mcp 常驻 core tools，且不包含 remote fleet 和 `mobile_get_page_source`。
  - 证据来源：`python -m pytest`，registry/server/stdio 三路径断言。
  - 结果：通过。
- [x] **S2**：调用任一未实现工具 → 返回 JSON text error，`code=not_implemented` 且 `tool` 为原工具名。
  - 证据来源：`test_stub_tools_return_structured_not_implemented_error` 遍历 23 tools；server/stdio 抽样覆盖。
  - 结果：通过。
- [x] **S3**：schema fixture 校验特殊字段。
  - 证据来源：`test_schema_parity_fixture` 覆盖 `bundle_id`、`saveTo`、`submit`、`orientation`、`direction`、enum、annotations、`content_kind=image`。
  - 结果：通过。
- [x] **S4**：CLI/server import smoke。
  - 证据来源：`python -m pytest` + `python -c 'from pymobile_mcp.cli import main'`。
  - 结果：通过。

**review 报告重点复核**：

- [x] QA 已覆盖 registry / server handler / stdio 三路径。
- [x] QA 已覆盖 unknown / not_implemented / invalid_argument 三态 envelope。
- [x] QA 已覆盖不公开 `mobile_get_page_source` / remote fleet。
- [x] QA 已覆盖 registry/specs 不 import 设备库。

**QA 报告重点复核**：

- [x] 验证证据来源：`contract-registry-scaffold-qa.md`，frontmatter `status=passed`。
- [x] QA matrix 覆盖 design 关键场景和 review QA focus。
- [x] failed / blocked 项为 none。
- [x] residual-risk 不包含核心验收缺口；真实设备能力不属于本 feature。
- [x] Evidence pack、DoD Results、Gate Results 已复核，blocking 为空。

## 4. 术语一致性

- `core tools`：代码中通过 `CORE_TOOL_SPECS` / `CORE_TOOL_NAMES` 表达；fixture excluded list 防止误收 page_source/remote fleet。
- `schema parity fixture`：`tests/fixtures/mobile_mcp_core_tools.json` 命名一致。
- `structured error`：`ToolError.to_json()` 统一 envelope，registry 捕获后转换为 MCP text content。
- 禁用词核对：`mobile_get_page_source` / remote fleet 只在 tests fixture 和负例断言中出现，不在 `src/` public registry。

## 5. 领域影响盘点（提示而非代写）

- [x] 新术语候选：`core tools`、`ToolSpec`、`structured error`。
  - 结论：当前 README/compound 沉淀延后到 roadmap 最后一条 `parity-hardening-docs`；本 feature 不直接写 CONTEXT/ADR。
- [x] 结构性选择：MCP SDK 只在 server 层，registry 负责 manifest/validation/error envelope。
  - 结论：实现形态稳定但仍是 scaffold；暂不写 ADR，后续真实 driver 接入后再判断是否值得沉淀。
- [x] 流程级约束：`call_tool(validate_input=False)` 让 registry 统一 structured error。
  - 结论：记录在 review/acceptance；如后续 feature 复用该约束，可在 parity hardening 或 cs-keep 时沉淀。

## 6. requirement delta / clarification 回写

- Design frontmatter `requirement: null`。
- 本 feature 来自已批准 roadmap item，交付的是 roadmap 内部契约锚点和包骨架；仓库当前没有独立 requirements/CONTEXT.md。
- 本次不自由创建或改写 requirement；能力状态通过 roadmap item `contract-registry-scaffold` 回写为 done 表达。

## 7. roadmap 回写

- [x] `roadmap: pymobile-mcp-android-mvp` / `roadmap_item: contract-registry-scaffold` 均存在。
- [x] `.codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-items.yaml` 中 `contract-registry-scaffold` 已改为 `status: done`。
- [x] `.codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-roadmap.md` 第 5 节对应子 feature 已改为 `状态：done`，对应 feature 为 `2026-07-07-contract-registry-scaffold`。
- [x] `validate-yaml.py --file ...items.yaml --yaml-only` 通过。

## 8. attention.md 候选盘点

- 候选：MCP SDK server 默认 input validation 会绕过项目 JSON envelope；本项目在 server 层用 `call_tool(validate_input=False)`，把 required/enum/unknown 校验集中到 registry。
- 处理：作为可复用技术约束，建议后续通过 `cs-keep` 或 parity-hardening-docs 沉淀；本阶段不直接改 attention.md。

## 9. 遗留

- 后续优化点：真实 Android/iOS handler 接入时继续复用 `register_tool_handler()` seam，并保留 error envelope 测试。
- 已知限制：当前所有 core tools 仍是 stub，真实设备能力由后续 roadmap feature 实现。
- 实现阶段顺手发现：`pytest_asyncio` event loop scope warning，不影响当前验收；后续测试配置整理时可处理。

## 10. 最终审计

- 验证证据来源：`contract-registry-scaffold-qa.md`。
- Evidence sources：`contract-registry-scaffold-evidence-pack.md`、`contract-registry-scaffold-dod-results.json`、`contract-registry-scaffold-scope-gate-results.json`、`contract-registry-scaffold-gate-results.json`、`contract-registry-scaffold-dod-contract-results.json`。
- 聚合命令：
  - `.venv/bin/python -m pytest` → exit 0：36 passed。
  - `PATH=.venv/bin:$PATH python -c 'from pymobile_mcp.cli import main'` → exit 0。
  - `PATH=.venv/bin:$PATH python3 .codestable/tools/validate-yaml.py --file .codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-items.yaml --yaml-only` → exit 0。
  - `python -m pip install -e .` → trust-prior-verify：QA 阶段同一最终 diff 下 exit 0。
- 场景复核：re-verified 6 / trust-prior-verify 1。
- 交付物复核：代码、schema fixture、tests、review、QA、gate/evidence、roadmap items/main doc 均已落盘。
- 完整工作区复核：`git status --short` 中 dirty/untracked 均为本 feature 交付物或 roadmap 回写；无 staged diff。
- diff 清洁度：`src/` / `tests/` scoped grep 通过；无 debug print、临时 TODO/FIXME/XXX、注释掉代码。
- 知识沉淀出口：已登记 attention/learning 候选；不在 accept 内直接写。
- 结论：通过。

## Verdict

- Status: passed
- Next: update goal-state to accepted, scoped-commit, then continue `android-live-ui-slice`.

---
doc_type: feature-qa
feature: 2026-07-07-contract-registry-scaffold
status: passed
tested: 2026-07-09
round: 1
---

# contract-registry-scaffold QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-design.md`
- Checklist: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-checklist.yaml`
- Review: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-review.md`
- Evidence pack: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-scope-gate-results.json`
- DoD results: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-dod-results.json`
- Diff basis: `git status --short` 显示本 feature 范围内新增 `src/`、`tests/`、`.gitignore`、review/evidence/gate 产物，以及 checklist steps 更新；无 staged diff。
- Baseline dirty files: none；当前 dirty/untracked 均属于 `contract-registry-scaffold`。
- Feature type: functional（新增 MCP server / tool registry / CLI 入口与错误语义）。
- Core evidence gate: 必须有运行证据覆盖 `list_tools` 23 core tools、反向排除 page_source/remote fleet、registered stub `not_implemented`、unknown/invalid argument structured envelope、CLI/server import smoke。

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | design S1 / review focus | core-functional | MCP `list_tools` 只返回 23 个 mobile-mcp 常驻 core tools | integration/unit | `python -m pytest` | registry、server handler、stdio client 三路径 names 等于 fixture | pass |
| QA-002 | design S2 / review focus | core-functional | 调用已注册未实现工具返回 JSON text `not_implemented` | integration/unit | `python -m pytest` | `status=error`, `code=not_implemented`, `tool` 为原工具名，`isError=False` | pass |
| QA-003 | design S3 / checklist | core-functional | schema parity 覆盖特殊字段和枚举 | unit/schema | `python -m pytest` | `bundle_id/saveTo/submit/orientation/direction` required/optional/enum/annotations/content_kind 与 fixture 一致 | pass |
| QA-004 | design S4 | core-functional | CLI/server import smoke | command/unit | `python -m pytest`; `python -c 'from pymobile_mcp.cli import main'` | server 可构造，CLI main 可导入 | pass |
| QA-005 | 反向核对 | core-functional | 不公开 `mobile_get_page_source` 和 remote fleet 三工具 | integration/unit | `python -m pytest` | `CORE_TOOL_NAMES` / server list / stdio list 均不含 excluded tools；unknown call 返回 invalid_argument | pass |
| QA-006 | review residual risk | supporting | MCP SDK validation 不覆盖项目 structured error | integration | `python -m pytest` | `call_tool(validate_input=False)` 后 registry 统一输出 JSON text envelope | pass |
| QA-007 | DoD supporting | supporting | editable install 可用 | command | `python -m pip install -e .` | exit 0 | pass |
| QA-008 | cleanliness | supporting | 无新增 debug/TODO/注释掉临时代码；registry/specs 不 import 设备库 | static/test | scoped grep `src/`、`tests/`; `python -m pytest` | src/tests 无 TODO/FIXME/XXX/print/console.log；registry/specs 无 `uiautomator2`/`pymobiledevice3` | pass |

## 3. Command Results

- `.venv/bin/python -m pytest` → exit 0：36 collected，36 passed；覆盖 contract registry、schema parity、server handler、真实 `mcp.client.stdio` 路径。
- `PATH=.venv/bin:$PATH python -m pip install -e .` → exit 0：editable wheel built and installed as `pymobile-mcp==0.1.0`。
- `PATH=.venv/bin:$PATH python -c 'from pymobile_mcp.cli import main'` → exit 0：无输出，CLI import smoke 通过。
- scoped grep `src/` for `TODO|FIXME|XXX|print\(|console\.log|uiautomator2|pymobiledevice3|mobile_get_page_source|mobile_list_remote_devices|mobile_allocate_remote_device|mobile_release_remote_device` → 0 matches。
- scoped grep `tests/` for `TODO|FIXME|XXX|print\(|console\.log` → 0 matches。

## 4. Scenario Results

- [x] QA-001 `list_tools` 只返回 23 core tools：pass
  - Evidence: `tests/test_contract_registry.py` 中 registry fixture、`PyMobileMCPServer().mcp.request_handlers[types.ListToolsRequest]`、真实 `mcp.client.stdio` 都断言 names 与 `CORE_TOOL_NAMES` 一致。
- [x] QA-002 已注册 stub tool structured error：pass
  - Evidence: pytest 覆盖全部 23 个 tool 的 direct call，并覆盖 server handler / stdio client 的 `mobile_list_apps` stub。
- [x] QA-003 schema parity：pass
  - Evidence: fixture `tests/fixtures/mobile_mcp_core_tools.json` 记录 23 tools、required/optional/enum/annotations/content_kind/source revision；pytest 参数化逐项比对。
- [x] QA-004 CLI/server smoke：pass
  - Evidence: pytest 构造 `PyMobileMCPServer`；CLI import 命令 exit 0。
- [x] QA-005 反向排除 page_source/remote fleet：pass
  - Evidence: tests 断言 excluded tools 与 `CORE_TOOL_NAMES` / server list / stdio list 无交集；`mobile_get_page_source` call 返回 structured `invalid_argument`。
- [x] QA-006 错误 envelope 稳定：pass
  - Evidence: direct/server/stdio 三路径覆盖 `not_implemented`、unknown `invalid_argument`、missing required、enum invalid；MCP result `isError=False` 且 content type 为 text。
- [x] QA-007 editable install：pass
  - Evidence: `python -m pip install -e .` exit 0。
- [x] QA-008 清洁度：pass
  - Evidence: scoped grep 对 `src/`、`tests/` 通过；pytest 断言 registry/specs source 和 `sys.modules` 未加载 `uiautomator2` / `pymobiledevice3`。

## 5. Findings

### failed

none

### blocked

none

### residual-risk

- `pytest_asyncio` warning：当前 pytest 输出提示未来 fixture loop scope 默认值变化；不影响本 feature contract 行为，后续可在测试配置整理时处理。
- 本 feature 只验证契约骨架和 stub behavior；真实 Android/iOS 设备能力按 design 明确不在本 feature 范围内。

## 6. Cleanliness

- Debug output: pass
- Temporary TODO/FIXME/XXX: pass
- Commented-out code: pass
- Unused imports / dead code from this feature: pass（pytest/import smoke 通过；源码层无明显未用路径）
- Out-of-scope files: pass（scope gate passed；dirty/untracked 均属于本 feature）

## 7. Verdict

- Status: passed
- Next: `cs-feat-accept`

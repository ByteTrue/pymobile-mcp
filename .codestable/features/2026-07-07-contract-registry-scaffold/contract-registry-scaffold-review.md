---
doc_type: feature-review
feature: 2026-07-07-contract-registry-scaffold
status: passed
reviewer: subagent
reviewed: 2026-07-08
round: 3
---

# contract-registry-scaffold 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-design.md`
- Checklist: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-scope-gate-results.json`
- DoD results: `.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-dod-results.json`
- Implementation evidence: `python -m pytest` 36 passed；`python -m pip install -e .` passed；`python -c 'from pymobile_mcp.cli import main'` passed。
- Diff basis: 新增 Python 包骨架、MCP server wrapper、tool registry/spec manifest、driver contract 最小 dataclass、contract tests、schema fixture、CodeStable evidence/gate 产物。
- Baseline dirty files: none；当前 dirty 均属于本 feature 范围。

### Independent Review

- Detection: Paseo subagent 可用；原生 pi-subagents reviewer 多次无有效输出；OCR CLI 已安装但未配置 LLM，`ocr llm test` failed。
- 环节 A 独立隔离 Task agent: paseo completed（三轮）。最终轮 `d0253c05-383a-4409-9c66-b97094530fa0`：blocking none，提出 important/nit/test focus。
- 环节 B OCR CLI: failed（未配置 LLM endpoint）。
- OCR severity mapping: not applicable。
- Merge policy: subagent findings 已逐条本地核验；无 blocking。关于 checklist checks pending 的 finding 属 acceptance 阶段职责，不阻塞 review；关于三路径证据的 finding 已由 registry/server/stdio 三组测试覆盖。
- Gate effect: `reviewer: subagent` 放行；OCR 不可用记录为非阻塞。

## 2. Diff Summary

- 新增：
  - `.gitignore`
  - `src/pymobile_mcp/__init__.py`
  - `src/pymobile_mcp/cli.py`
  - `src/pymobile_mcp/server.py`
  - `src/pymobile_mcp/errors.py`
  - `src/pymobile_mcp/tools/__init__.py`
  - `src/pymobile_mcp/tools/registry.py`
  - `src/pymobile_mcp/tools/specs.py`
  - `src/pymobile_mcp/drivers/__init__.py`
  - `src/pymobile_mcp/drivers/base.py`
  - `tests/fixtures/mobile_mcp_core_tools.json`
  - `tests/test_contract_registry.py`
  - feature gate/evidence JSON/Markdown 产物
- 修改：`.codestable/features/2026-07-07-contract-registry-scaffold/contract-registry-scaffold-checklist.yaml` steps marked done；去掉 design 阶段重复 checklist 键。
- 删除：none
- 未跟踪 / staged：未 staged；untracked 均属于本 feature。
- 风险热点：公共 MCP tool contract、schema parity、错误 envelope。

## 3. Adversarial Pass

- 假设的生产 bug：MCP client 能列工具但 `call_tool` 返回 SDK validation 文本而非项目 structured error。
- 主动攻击过的反例：
  - registry 直调：unknown / not_implemented / invalid_argument 三态。
  - `PyMobileMCPServer` request handler：`list_tools`、registered stub、unknown、required missing、enum invalid。
  - 真实 `mcp.client.stdio`：server lifecycle + `list_tools` + registered stub + unknown + required missing + enum invalid。
  - schema fixture：23 core tool names、required/optional、enum、annotations、`content_kind=image`、`additionalProperties=false`。
  - 反向范围：`mobile_get_page_source` 和 remote fleet 三工具不在 `CORE_TOOL_NAMES` / server list_tools。
- 结果：无 blocking；QA 需复核相同命令和 fixture source revision。

## 4. Findings

### blocking

none

### important

none

### nit

- [ ] REV-001 `tests/test_contract_registry.py:25-26` `_valid_args` 是测试内的最小参数生成 helper，当前只覆盖本 fixture 的 required 字段类型；后续 schema 若引入非字符串 required 字段需同步扩展。
  - Evidence: 当前 fixture required 字段中除 `direction` / `orientation` 外均可用字符串哨兵，坐标/布尔字段只在 required 里出现时测试不依赖真实类型校验。
  - Impact: 不影响本 feature parity；后续真实实现或更严格 JSON Schema type 校验时需补测试数据生成。

### suggestion

- 后续 feature 接入真实 handler 时，保留 `register_tool_handler` 的 registry 级 envelope 测试，避免底层 driver exception 漏出 Python traceback。

### learning

- MCP SDK server 的内置 input validation 会返回非 JSON 文本；本项目为了稳定 structured error，server 层使用 `call_tool(validate_input=False)`，把边界校验集中到 registry。

### praise

- Schema fixture 显式记录 mobile-mcp `server.ts` path、git revision 和 captured date，能作为后续 parity drift 的恢复锚点。

## 5. Test And QA Focus

- QA 必须重点复核：
  - `python -m pytest` 通过，确认 36 个 contract tests 覆盖 registry/server/stdio 三路径。
  - `python -m pip install -e .` 通过，确认 editable install 和 console script metadata 可生成。
  - `python -c 'from pymobile_mcp.cli import main'` 通过。
  - `tests/fixtures/mobile_mcp_core_tools.json` 的 `source.git_revision` 为 `c5d7d27fd61e4762e15ae4b1c68b6c011be88bb7`。
- Evidence pack residual risks / gate warnings: pytest 有 `pytest_asyncio` deprecation warning；非本 feature 行为风险，QA 可记录为 non-blocking。
- 建议新增或加强的测试：none for this feature。
- 不能靠 review 完全确认的点：真实移动设备能力未实现，按 design 明确不做；后续 feature 负责。

## 6. Residual Risk

- 当前只验证 contract scaffold 和 stub behavior，不验证 Android/iOS live device；这是 design 明确不做，不阻塞。
- OCR 行级增强不可用；已有独立 Paseo review + 本地事实核验。

## 7. Verdict

- Status: passed
- Next: `cs-feat-qa`

# PyMobile MCP

Python 实现的 mobile-mcp 黑盒兼容 MCP server：对外契约对齐固定上游，对内用 pure Python 驱动 Android / iOS / Simulator。

## Language

**Wire Contract**:
MCP 对外可见的 initialize / list_tools / call_tool 请求与响应语义，包含 tool 名称、title、description、参数 schema、annotations、成功文本、错误文本与 image content。
_Avoid_: API surface, public API, interface surface

**Upstream Oracle**:
固定 revision 的 mobile-mcp 源码与一次真实 MCP 抓取结果，作为 wire contract 的权威对照。
_Avoid_: golden source, reference implementation, upstream runtime dependency

**Deterministic Bundle**:
把 upstream capture、Python capture、scenario manifest、image artifacts 和 content hash 固定在一起的可复现证据包；hash 不一致时 fail-closed。
_Avoid_: snapshot archive, fixture dump, evidence zip

**Exception Ledger**:
经设计批准的、允许与上游 runtime 成功路径不同的有限差异清单；每项必须限定 tool / platform / device_type / case id。
_Avoid_: known issues, TODO list, deferred bugs

**Actionable Error**:
与上游风格一致、可供 LLM 直接修复后重试的错误文本；成功路径通常不带 isError，意外错误才 isError=true。
_Avoid_: structured error envelope, ToolError JSON, machine-only error

**Device Class**:
验收与 smoke 的设备分类：Android physical、Android emulator、iOS real、iOS Simulator。
_Avoid_: platform flavor, target kind

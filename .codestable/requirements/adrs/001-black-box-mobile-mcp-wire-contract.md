---
id: 001
title: 以固定上游 wire contract 作为黑盒契约权威
status: accepted
date: 2026-07-13
relates_to: [requirements/CONTEXT]
---

# 以固定上游 wire contract 作为黑盒契约权威

## Context

pymobile-mcp 的实现栈是 pure Python（uiautomator2 / pymobiledevice3 / simctl），但产品目标是让 LLM 客户端像使用 mobile-mcp 一样使用它。早期只对齐 tool 名和参数 required/optional，导致成功返回文本、错误文本、image content 和输入边界与上游不一致，用户路径失败。

## Decision

以 `mobile-mcp@c5d7d27`（tag `0.0.61`）的源码声明 + 真实 MCP wire capture 为权威：

1. 源码复制 tool 提示词、参数描述、成功/错误文本与 annotations。
2. 固定一次 initialize / list_tools / call_tool capture 作为 golden。
3. Python 侧通过 deterministic bundle gate fail-closed 比对 wire 输出。
4. 运行时实现可以不同，但对外契约不得自行“改进”。

## Consequences

正向：

- drop-in 替换目标可被机器证明，而不只是“语义差不多”。
- review 能用 exact mismatch 抓住 coercion、URL gate、image scale 等问题。

负向 / 约束：

- 上游固定 revision 后，升级 mobile-mcp 需要重新 capture + 重跑 parity。
- Python MCP SDK 版本也要固定（当前 `mcp==1.28.1`），避免 transport 漂移。
- 不能再维护另一套“更结构化”的对外错误 JSON 作为默认契约。

## Alternatives Considered

1. **只对齐 schema，自由设计返回文本**  
   实现快，但不能做 black-box 替换；已在 Pi 用户路径失败。

2. **运行时直接代理 mobile-mcp Node 进程**  
   契约天然一致，但违背 pure-Python / 无 go-ios runtime 目标，并引入双运行时。

3. **按能力重写“更好”的 MCP API**  
   对新人友好，但破坏现有 mobile-mcp prompt / client 假设。

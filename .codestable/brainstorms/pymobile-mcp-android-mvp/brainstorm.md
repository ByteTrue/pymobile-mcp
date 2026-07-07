---
doc_type: brainstorm
slug: pymobile-mcp-android-mvp
created: 2026-07-07
status: active
summary: 探索 pymobile-mcp 首轮以 mobile-mcp 兼容契约和 Android 真机闭环为核心的实现路线
tags: [mcp, mobile, android, roadmap]
---

# pymobile-mcp Android MVP

> 创意空间 | 2026-07-07 | 下一步：cs-roadmap

## 出发点

项目目标是实现一个纯 Python MCP server，用于移动设备自动化，功能最终对齐 `mobile-next/mobile-mcp`。现有 `KICKOFF.md` 已给出技术栈、三层架构、23 个目标工具、Android/iOS 驱动方向与实现优先级。

这不是单 feature：它至少包含 MCP server、Android driver、iOS driver、工具契约、测试/发布等多个子模块。当前先把首轮范围收窄，避免直接把 23 个工具和双端支持一次性塞进实现。

## 聊过的方向

- 严格兼容 mobile-mcp vs Python-native API：倾向外部契约严格对齐，内部实现保持 Python 简单结构。
- 一次注册全部工具 vs 只注册已实现工具：倾向一次注册 23 个 `mobile_*` 工具，未实现功能返回稳定结构化错误，避免后续工具名/参数变化影响 MCP client。
- 首轮验收深度：跳过仅协议 smoke，选择 Android 真机闭环；暂不把 app 安装/启动和 iOS/WDA 拉进首轮验收。

## 当前倾向

首轮走“兼容契约 + Android MVP vertical slice”：MCP 层先稳定暴露 mobile-mcp 对齐的 23 个工具；实现上优先打通 Android 真机的核心 UI 自动化链路。

## 已敲定的点

- 已确认：外部工具名、参数和返回结构尽量对齐 `mobile-next/mobile-mcp`，不要先发明 Python-only 契约。
- 已确认：MCP 层一次注册 23 个工具；未实现/当前平台不支持的工具返回稳定结构化错误。
- 已确认：首轮验收为 Android live smoke：`list_devices → screenshot → page_source/elements → tap/swipe/type` 能在已连接 Android 真机上跑通。
- 已确认：用户已有 Android 真机连接，可在实现阶段直接 debug。
- 倾向：iOS、recording、crash、app 管理不作为首轮 vertical slice 的阻塞项。

## 遗留问题 & 下一步

- `cs-roadmap` 需要把大需求拆成可执行子 feature，建议第一项就是 Android MVP vertical slice。
- roadmap/design 阶段需要读取 `/Users/byte/workspace/forks/mobile-mcp/src/`，确认 mobile-mcp 的真实工具 schema 和返回结构，避免只按 kickoff 猜。
- 实现阶段需要用已连接 Android 真机做最小闭环调试。

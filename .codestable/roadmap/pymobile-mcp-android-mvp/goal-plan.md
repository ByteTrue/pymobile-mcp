# pymobile-mcp-android-mvp Goal Plan

## Roadmap

- Roadmap: `.codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-roadmap.md`
- Items: `.codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-items.yaml`

## Feature 执行顺序

| # | Feature slug | 性质 | 一句话交付物 |
|---|---|---|---|
| 1 | contract-registry-scaffold | functional | Python MCP 包骨架 + 23 core tools registry + schema parity fixture + 结构化错误 |
| 2 | android-live-ui-slice | functional | Android 真机 list_devices → screen_size → screenshot → elements → tap/swipe/type 闭环 |
| 3 | android-app-system-tools | functional | Android app lifecycle + orientation + button + open_url + save_screenshot |
| 4 | android-recording-crash-tools | functional | Android recording 状态机 + crash 实现或 unsupported |
| 5 | ios-pmd3-wda-core | functional | iOS PMD3/WDA discovery + screenshot + elements + tap/swipe/type |
| 6 | ios-app-recording-crash-parity | functional | iOS app/recording/crash 实现或 stable unsupported |
| 7 | parity-hardening-docs | mixed | README 能力矩阵 + schema parity tests + live smoke docs + 已知限制 |

## Roadmap 级核心验收路径

Android 真机通过 MCP client 完成 `list_devices → screen_size → screenshot → elements → tap/swipe/type`，iOS 设备（如有）完成同等核心 UI smoke。

## 关键假设

- 用户接受 Android-first，iOS 延后到独立条目。
- 成功输出尽量贴 mobile-mcp 文本语义，稳定结构化错误优先。
- `mobile_list_elements_on_screen` 是对外元素定位入口；raw source 只在 driver 内部使用。
- 不公开 `mobile_get_page_source`。

## Top 3 风险与缓解

1. iOS PMD3/WDA API 与预期不一致 → spike-first，失败不阻塞 Android MVP。
2. Android crash 来源不可靠 → design-time default unsupported，spike 可推翻。
3. 真实设备 live smoke 不稳定 → 每条 live feature 留下可复跑步骤，skip 不算通过。

## 必跑验证命令集合

| ID | 命令 | 核心性 |
|---|---|---|
| CMD-001 | `python -m pytest` | core |
| CMD-002 | `python -m pip install -e .` | supporting |
| CMD-003 | `python -c 'from pymobile_mcp.cli import main'` | core |
| CMD-ANDROID-001 | Android live smoke via MCP tools | core |
| CMD-ANDROID-APP-001 | Android app/system live smoke | core |
| CMD-ANDROID-REC-001 | Android recording smoke | core |
| CMD-ANDROID-CRASH-001 | Android crash spike | core |
| CMD-IOS-CORE-001 | iOS PMD3/WDA core live smoke | core |
| CMD-IOS-PARITY-001 | iOS parity smoke or unsupported checks | core |
| CMD-GOAL-001 | `python3 .codestable/tools/codestable-goal-consistency-gate.py --roadmap .codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-roadmap.md` | core |
| CMD-YAML-001 | `python3 .codestable/tools/validate-yaml.py --file .codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-items.yaml --yaml-only` | core |

## 最终聚合测试命令集合

roadmap 完成前必须重跑：

1. `python -m pytest` — 全量测试 + schema parity
2. `python3 .codestable/tools/codestable-goal-consistency-gate.py --roadmap .codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-roadmap.md`
3. `python3 .codestable/tools/validate-yaml.py --file .codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-items.yaml --yaml-only`
4. 可用设备 live smoke（Android 必跑，iOS 有设备则跑）

## 预检策略

每个 feature 实现前先跑 `python -m pytest` 确认基线；live smoke 前确认设备可用。

## DoD Policy

每个 feature 必须满足其 design 中的 DoD Contract 所有 blocking 条目。

## Gate Policy

按 `goal-protocol-gates.md` 执行。gate 脚本由 `cs-onboard` 安装到 `.codestable/tools/`。

## Provider Policy

- archguard / meta-cc unavailable 不阻塞，记录 fallback。
- provider warning 由 review / QA / audit 解释。
- 未解释的核心风险可阻塞。

## 验证工具缺失恢复策略

只能补测试依赖、锁文件或既有 runner 配置，不能新增同名 shim 或伪造验证结果。

## 最终审计核验的交付物类型

- 源码：`src/pymobile_mcp/`
- 测试：`tests/`
- 文档：`README.md`
- CodeStable spec：各 feature 目录下的 design/checklist/review/qa/acceptance
- Roadmap 回写：items.yaml 状态

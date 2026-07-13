---
doc_type: roadmap
slug: pymobile-mcp-productize-0.3
status: draft
created: 2026-07-13
last_reviewed: 2026-07-13
tags: [mcp, mobile, release, productize, roadmap, v0.3]
related_requirements: [CONTEXT]
related_architecture: [adrs/001-black-box-mobile-mcp-wire-contract, adrs/002-approved-runtime-exception-ledger]
---

# pymobile-mcp productize 0.3

## 1. 背景

Android MVP、post-MVP、black-box contract parity 均已完成并合入 `main`（`f44f291` / docs `9871205`）。

当前产品状态：

- 双端 23 core tools，fleet 模式下 26 tools discovery exact
- black-box wire 对齐 `mobile-mcp@c5d7d27`
- 四端 live 16/16 + Pi direct-tools 已过
- 发布面仍偏“开发仓库可用”，不是完整产品发布面

已知已批准例外（不在本 roadmap 必做范围）：

1. remote fleet 成功 runtime（无 Python fleet provider）
2. iOS real-device screen recording unsupported

## 2. 范围与明确不做

### 覆盖

1. 把 black-box parity 成果打成 **v0.3.0** 发布点。
2. 固化上游 oracle / deterministic bundle 升级 playbook，降低下次 pin 变更成本。
3. 补齐 PyPI 发布路径与 tag 触发 CI（可选但推荐）。
4. 对两项 exception 做明确 triage 决策记录：继续 defer / 另开 roadmap。

### 明确不做

- 不实现 iOS 真机录屏 exact 路径。
- 不实现 remote fleet provider / 设备池。
- 不重开 23-tool public schema 字段名。
- 不引入 go-ios / mobilecli runtime。
- 不扩 destructive install/uninstall 的默认 live 授权。

### Granularity Gate

| 判断项 | 结论 |
|---|---|
| 为什么不是 single feature | release、playbook、publish、exception triage 可独立验收，风险面不同。 |
| 为什么不是 brainstorm | 产品化缺口已由当前 main 状态直接可见。 |
| 最小闭环 | `v0.3.0` tag + Release 文案 + 回归清单可复跑。 |

## 3. 模块拆分

```text
Release Packaging (version / CHANGELOG / GitHub Release)
Oracle Maintainability (upgrade playbook / bundle refresh SOP)
Distribution (PyPI + CI publish)
Exception Governance (triage note, not new runtime)
```

## 4. 子 feature 列表（有序）

1. **release-0.3-black-box**  
   版本 `0.3.0`、CHANGELOG、GitHub Release、README 指向当前 cut。

2. **oracle-upgrade-playbook**  
   写清如何 re-capture mobile-mcp、刷新 deterministic bundle、跑 CMD-001~008 与最小 live 集。

3. **pypi-publish**  
   打包元数据检查、tag→PyPI workflow、安装路径从 git URL 切到 `pip install`（若发布成功）。

4. **exception-triage**  
   对 fleet provider / iOS real recording 输出 go/no-go 决策与触发条件；不在本项实现 runtime。

依赖：`2`/`3`/`4` 可并行，但默认 `1` 先定版本锚点；`3` 依赖 `1` 的 tag 策略。

## 5. 验收

- `pyproject.toml` / package version = `0.3.0`
- GitHub Release `v0.3.0` 存在且说明 black-box parity + 两项 exception
- playbook 文档可按步骤复跑 oracle 刷新（至少 dry-run 命令齐全）
- 若启用 PyPI：`pip install pymobile-mcp==0.3.0` 可装；否则明确记录“本机/组织暂不发 PyPI”
- exception triage 文档写明：何时开 fleet roadmap、何时重开 iOS recording
- `python -m pytest` 全绿；既有 parity gates 不退化

## 6. 风险

1. PyPI 包名占用 / token 未配置 → `pypi-publish` 可降级为“准备就绪但 blocked-by-env”，不阻塞 `0.3.0` git release。
2. 上游 mobile-mcp 在 playbook 落地前变更 → 仍 pin `c5d7d27`，升级必须走 playbook。
3. 把 triage 误做成半实现 runtime → 明确 exception-triage 只出决策，不写 provider/recording 代码。

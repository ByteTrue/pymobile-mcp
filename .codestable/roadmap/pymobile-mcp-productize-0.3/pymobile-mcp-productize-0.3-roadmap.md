---
doc_type: roadmap
slug: pymobile-mcp-productize-0.3
status: completed
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
3. 补齐 PyPI 发布路径与 tag 触发 CI（可选，不进入 core DoD）。
4. 对两项 exception 做明确 triage 决策记录：继续 defer / 另开 roadmap。

### 明确不做

- 不实现 iOS 真机录屏 exact 路径。
- 不实现 remote fleet provider / 设备池。
- 不重开 23-tool public schema 字段名。
- 不引入 go-ios / mobilecli runtime。
- 不扩 destructive install/uninstall 的默认 live 授权。
- 本 roadmap **无 runtime 接口变更**；不改 MCP tool schema / 成功错误文本契约。

### Granularity Gate

| 判断项 | 结论 |
|---|---|
| 为什么不是 single feature | release、playbook、publish、exception triage 可独立验收，风险面不同。 |
| 为什么不是 brainstorm | 产品化缺口已由当前 main 状态直接可见。 |
| 最小闭环 | `v0.3.0` tag + Release 文案 + 回归清单版本对齐 + pytest 全绿。 |

## 3. 模块拆分

```text
Release Packaging (version / CHANGELOG / GitHub Release / README / regression checklist)
Oracle Maintainability (upgrade playbook / bundle refresh SOP)
Distribution (PyPI + CI publish)   # optional
Exception Governance (triage note, not new runtime)
```

跨模块 runtime 接口：无。本 roadmap 只产出发布与治理文档/脚本入口约定。

## 4. 子 feature 列表（有序）

默认串行锚点：

1. **release-0.3-black-box**（minimal_loop）  
2. **oracle-upgrade-playbook**（可与 4 并行，但默认接在 1 后）  
3. **pypi-publish**（依赖 1 的 tag 策略；optional）  
4. **exception-triage**（可与 2 并行）

### 4.1 release-0.3-black-box

- `pyproject.toml` version = `0.3.0`
- `src/pymobile_mcp/__init__.py` `__version__` = `0.3.0`
- Git tag / GitHub Release `v0.3.0` 与上述版本一致
- `CHANGELOG.md`：`Unreleased` 中 black-box 条目切割到 `## 0.3.0`
- `README.md`：当前 release 与 install ref 指向 `0.3.0` / `v0.3.0`
- `docs/regression-checklist.md`：版本头更新为 v0.3.0
- Release notes 写明 black-box parity + 两项 approved exception

### 4.2 oracle-upgrade-playbook

- 文档化 pin=`c5d7d27` 的 **no-op maintenance** vs **升 pin 全量 re-capture**
- 挂现有脚本入口（不新造抽象）：
  - `scripts/capture_mobile_mcp_contract.py`
  - `scripts/capture_mobile_mcp_calls.py`
  - `scripts/assert_mobile_mcp_contract.py`
  - `scripts/validate_mobile_mcp_source_coverage.py`
  - `scripts/compare_mobile_mcp_image_backends.py`
- 命令用 env 占位（如 `MOBILE_MCP_SOURCE`），禁止写死本机绝对路径
- 写清 exit `0/1/2`：blocked≠pass
- 链接权威命令表：
  `.codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/`

### 4.3 pypi-publish（optional）

- tag→PyPI workflow 或等价发布路径
- 成功：`pip install pymobile-mcp==0.3.0`
- 失败/缺 token：书面 `blocked-by-env`，**不阻塞 core DoD**

### 4.4 exception-triage

- 输出决策文档（模板字段）：case id / tool / platform / 触发条件 / ledger 收窄条件 / 是否另开 roadmap
- 只决策，不写 provider / recording runtime 代码

依赖（与 items.yaml 一致）：

- `pypi-publish` → `release-0.3-black-box`
- `oracle-upgrade-playbook` / `exception-triage` → 无硬依赖；默认执行顺序 1→2→3→4

## 5. 验收

### Core DoD（roadmap complete 必须全部满足）

| 项 | 完成信号 |
|---|---|
| release-0.3-black-box | 版本三元一致 + Release + CHANGELOG/README/regression-checklist 切割到 0.3.0 |
| oracle-upgrade-playbook | 可复制 SOP + 脚本入口 + exit 语义 + dry-run 检查通过 |
| exception-triage | go/no-go 文档落盘，字段齐全 |
| CMD-001 | `python -m pytest` exit 0 |
| parity 策略 | **本轮 0.3.0 不升上游 pin、不强制全量 re-capture**；要求 pytest 内嵌 black-box contract tests 全绿，且 `tests/fixtures/mobile_mcp/bundle-manifest.json` 未脏。若未来升 pin，必须走 playbook 全量 CMD-002~008 |

### Optional（分开记账）

| 项 | 完成信号 |
|---|---|
| pypi-publish | `published` **或** 书面 `blocked-by-env`（不得记为 core fail，也不得记为 core pass） |

### Live 策略（tag 前）

- **必过**：unit + contract（CMD-001 / pytest 内嵌 black-box）
- **推荐**：`docs/regression-checklist.md` dual-device 最小集
- live `blocked` = 环境缺口，**不计入 pass**；**默认不阻塞** `v0.3.0` git tag（用户可在执行时改口强制 live）

### 命令

| ID | 命令 | 核心性 |
|---|---|---|
| CMD-001 | `python -m pytest` | core |
| CMD-REL-001 | `pyproject.toml` + `__version__` + tag/Release `v0.3.0` 三元一致 | core |
| CMD-ORACLE-001 | playbook dry-run：脚本路径存在 + 文档命令与 scripts 参数一致 | core |
| CMD-PYPI-001 | `pip index versions pymobile-mcp` 见 0.3.0，或 blocked 记录 | optional |

## 6. 风险

1. PyPI 包名占用 / token 未配置 → optional blocked-by-env，不阻塞 core。
2. 上游 mobile-mcp 变更 → 0.3 仍 pin `c5d7d27`；升级必须走 playbook。
3. triage 被做成半实现 runtime → review 盯 diff，本项只允许决策文档。
4. 误把 pytest 绿当成 wire 全量重证 → 本轮明确“不 re-capture”；升 pin 才全量 CMD-002~008。

# pymobile-mcp-productize-0.3 Goal Plan（draft）

## Roadmap

- Roadmap: `.codestable/roadmap/pymobile-mcp-productize-0.3/pymobile-mcp-productize-0.3-roadmap.md`
- Items: `.codestable/roadmap/pymobile-mcp-productize-0.3/pymobile-mcp-productize-0.3-items.yaml`

## Feature 执行顺序

| # | Feature slug | 性质 | 一句话交付物 |
|---|---|---|---|
| 1 | release-0.3-black-box | release | `v0.3.0` version + CHANGELOG + GitHub Release |
| 2 | oracle-upgrade-playbook | docs/process | 可执行的 oracle/bundle 升级 SOP |
| 3 | pypi-publish | distribution | PyPI/tag CI 或明确 blocked-by-env |
| 4 | exception-triage | decision | fleet/iOS-recording go/no-go 与触发条件 |

## 前置

- Android MVP / post-MVP / black-box parity 已完成
- `main` tip 含 black-box feature + domain docs
- 两项 approved exception 已 ADR 化，不在本 roadmap 强做

## 必跑验证

| ID | 命令 | 核心性 |
|---|---|---|
| CMD-001 | `python -m pytest` | core |
| CMD-REL-001 | version 文件与 tag/Release 一致 | core（release 条目） |
| CMD-ORACLE-001 | playbook dry-run 命令可复制执行 | core（playbook 条目） |
| CMD-PYPI-001 | `pip index versions pymobile-mcp` 或 blocked 记录 | optional |

## 状态

- roadmap status: **draft**
- 未生成 feature design / goal-state
- 用户确认本规划后，再推进 review / goal-package / 执行

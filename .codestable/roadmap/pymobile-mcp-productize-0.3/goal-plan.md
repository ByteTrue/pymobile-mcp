# pymobile-mcp-productize-0.3 Goal Plan（draft）

## Roadmap

- Roadmap: `.codestable/roadmap/pymobile-mcp-productize-0.3/pymobile-mcp-productize-0.3-roadmap.md`
- Items: `.codestable/roadmap/pymobile-mcp-productize-0.3/pymobile-mcp-productize-0.3-items.yaml`

## Feature 执行顺序

| # | Feature slug | 性质 | 一句话交付物 | DoD |
|---|---|---|---|---|
| 1 | release-0.3-black-box | release | `v0.3.0` 版本三元一致 + 文档切割 + GitHub Release | core |
| 2 | oracle-upgrade-playbook | docs/process | 可执行 oracle/bundle 升级 SOP | core |
| 3 | pypi-publish | distribution | PyPI/tag CI **或** 书面 blocked-by-env | optional |
| 4 | exception-triage | decision | fleet/iOS-recording go/no-go | core |

默认顺序 1→2→3→4；`2` 与 `4` 无硬依赖，可并行。

## Roadmap complete 定义

**Core complete** 当且仅当：

1. `release-0.3-black-box` accepted  
2. `oracle-upgrade-playbook` accepted  
3. `exception-triage` accepted  
4. CMD-001 exit 0  
5. CMD-REL-001 通过  

**Optional**：

- `pypi-publish` = `published` **或** `blocked-by-env`  
- 两种结果都不改写 core complete；禁止把 blocked 记为 pass 或 fail

## 前置

- Android MVP / post-MVP / black-box parity 已完成
- 上游 pin 保持 `mobile-mcp@c5d7d27`（本轮不升 pin）
- 两项 approved exception 已 ADR 化

## 必跑验证

| ID | 命令 | 核心性 |
|---|---|---|
| CMD-001 | `python -m pytest` | core |
| CMD-REL-001 | `pyproject.toml` + `src/pymobile_mcp/__init__.py` + tag/Release `v0.3.0` 三元一致 | core |
| CMD-ORACLE-001 | playbook 文档命令可复制；`scripts/capture_mobile_mcp_*.py` / `assert_mobile_mcp_contract.py` / `validate_mobile_mcp_source_coverage.py` / `compare_mobile_mcp_image_backends.py` 路径存在 | core |
| CMD-PYPI-001 | `pip index versions pymobile-mcp` 或 blocked 记录 | optional |

### Parity 策略（0.3.0）

- **不**强制全量 re-capture / CMD-002~008 重跑
- **要求** pytest 内嵌 black-box contract tests 全绿
- **要求** `tests/fixtures/mobile_mcp/bundle-manifest.json` 工作树未脏
- 未来升 pin：必须走 playbook 全量 CMD-002~008；exit 2 = blocked ≠ pass

### Live 策略

- tag 前必过 unit+contract
- dual-device live 推荐；blocked 不计入 pass；默认不阻塞 git tag

## 关键假设

- GitHub Release 可写
- PyPI token 可能缺失
- 上游 checkout 路径通过 `MOBILE_MCP_SOURCE` 提供，不写死本机路径

## Top 3 风险

1. PyPI blocked 被误算进 core → DoD 矩阵切开  
2. 只改 toml 导致 version 漂移 → CMD-REL-001 三元一致  
3. triage 半实现 runtime → review 只允许决策文档

## 状态

- roadmap status: **draft**（修订后待 re-review）
- 未生成 feature design / goal-state

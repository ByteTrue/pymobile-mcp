# pymobile-mcp-productize-0.3 Goal Plan

## Roadmap
- Roadmap: `.codestable/roadmap/pymobile-mcp-productize-0.3/pymobile-mcp-productize-0.3-roadmap.md`
- Items: `.codestable/roadmap/pymobile-mcp-productize-0.3/pymobile-mcp-productize-0.3-items.yaml`
- Review: `.codestable/roadmap/pymobile-mcp-productize-0.3/pymobile-mcp-productize-0.3-roadmap-review.md` (passed)
- Baseline: `d1fccc7ebce6514622045ea7a3be7b91e15aed78`

## Feature 执行顺序
| # | Feature slug | 性质 | 交付物 | DoD |
|---|---|---|---|---|
| 1 | release-0.3-black-box | non-functional | v0.3.0 版本三元一致 + 文档切割 + GitHub Release | core |
| 2 | oracle-upgrade-playbook | non-functional | docs/oracle-upgrade-playbook.md + dry-run | core |
| 3 | pypi-publish | non-functional | published 或 blocked/failed 状态文件 | optional |
| 4 | exception-triage | non-functional | docs/exception-triage-0.3.md | core |

默认顺序 1→2→3→4。

## Roadmap 级核心验收路径
本 epic 为 **纯非功能性 productize**（release/docs/decision/optional publish），无新增 runtime 用户路径。
核心验收改为：
1. CMD-001 `python -m pytest` exit 0
2. CMD-REL-001/002 + CMD-BUNDLE-001（release feature）
3. Core features 1/2/4 accepted
4. Optional feature 3 = published | blocked-by-env | failed（failed 仅记 optional fail，不改写 core complete）

## 最终聚合测试命令
- `python -m pytest`
- release 后：`python -c '...'` 版本三元 + `git rev-parse refs/tags/v0.3.0`
- `test -z "$(git status --porcelain -- tests/fixtures/mobile_mcp/bundle-manifest.json)"`
- 最终审计：`python3 <cs-onboard>/tools/codestable-goal-consistency-gate.py --roadmap .codestable/roadmap/pymobile-mcp-productize-0.3`

## Parity / Live 策略
- 0.3 不升 pin、不强制 CMD-002~008 re-capture
- pytest 内嵌 black-box 全绿 + clean bundle
- live 推荐；blocked≠pass；默认不阻塞 tag

## 关键假设
- GitHub Release 可写
- PyPI token 可能缺失
- 上游路径用 `PYMOBILE_MCP_UPSTREAM_SOURCE`

## Top 3 风险
1. PyPI optional 污染 core → 分账
2. 版本只改 toml → CMD-REL 三元
3. triage 半实现 runtime → review 盯 src/**

## DoD Policy
- Core complete = features 1+2+4 accepted + CMD-001 + CMD-REL 通过
- Optional pypi 不进 core pass/fail 聚合（failed 仅 optional）

## Gate Policy
按 `goal-protocol-gates.md`：scope-gate / dod-runner / evidence-pack / design-review / code-review / QA / acceptance。
缺 gate 脚本时更新 CodeStable，不得假 pass。

## Provider Policy
archguard / meta-cc unavailable → 记录 fallback warning，不自动阻塞；由 review/QA/audit 解释。

## 验证工具缺失恢复
只能补测试依赖/锁文件/既有 runner 配置；禁止新增同名 shim 或伪造结果。

## 最终审计交付物类型
- 每个 feature：design(approved)、checklist、design-review、review、qa、acceptance
- release：tag/Release/version/docs
- playbook：docs/oracle-upgrade-playbook.md
- triage：docs/exception-triage-0.3.md
- optional：pypi-publish-status.md
- goal-audit.md + consistency gate

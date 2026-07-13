---
doc_type: feature-design
slug: oracle-upgrade-playbook
status: approved
created: 2026-07-13
roadmap: pymobile-mcp-productize-0.3
roadmap_item: oracle-upgrade-playbook
nature: non-functional
---

# oracle / deterministic bundle 升级 playbook

## 1. 目标
落地可复制 SOP：维护现 pin 或升级 pin 时如何 refresh deterministic bundle，并 fail-closed。

## 2. Playbook 大纲（必须写入 docs/oracle-upgrade-playbook.md）

### A. No-op maintenance（pin 仍为 c5d7d27）
1. `python -m pytest`（含内嵌 black-box）
2. `git status --porcelain tests/fixtures/mobile_mcp/bundle-manifest.json` 为空
3. **禁止**无故 re-capture 或重写 golden

### B. Pin upgrade full re-capture
1. 设置上游路径：`--source "$PYMOBILE_MCP_UPSTREAM_SOURCE"`（允许别名 `MOBILE_MCP_SOURCE`）
2. 按序：CMD-002 capture default → CMD-003 fleet → CMD-004 calls → CMD-005/006 assert → CMD-007 source → CMD-008 image
3. 更新 fixtures/evidence/bundle-manifest
4. exit：0 pass / 1 fail / 2 blocked；blocked≠pass；不得把 approved_exception 聚合成 pass

### C. 脚本入口（不新造抽象）
playbook 必须给出 **去绝对路径的完整命令模板**（含必要 flag），不是只列 basename。
assert 脚本不吃 `--source`；capture/image 需要 pin 与可选 `npx --package npm@12.0.0` 包装。
`approved_exception`：pending/rejected → exit 2；approved 仅作为 scoped disposition，不能用来忽略 mismatch。

### C2. 脚本入口清单
- scripts/capture_mobile_mcp_contract.py
- scripts/capture_mobile_mcp_calls.py
- scripts/assert_mobile_mcp_contract.py
- scripts/validate_mobile_mcp_source_coverage.py
- scripts/compare_mobile_mcp_image_backends.py

### D. Pin / 工具链表
从 black-box feature 权威表复制：commit `c5d7d27…`、lock、node/npm 版本；命令去绝对路径。

权威命令源：
`.codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/`

## 3. 成功标准
- playbook 文件存在
- 区分 no-op vs upgrade
- 无 `/Users/` 硬编码
- CMD-ORACLE-001：脚本存在 + 文档含 env/exit/blocked 语义
- playbook 参数与 scripts CLI 一致（对照 --help）

## 4. 明确不做
本项不实际升 pin；不强制全量 capture（除非用户另开任务）。

## 5. 验证
CMD-001 + CMD-ORACLE-001（见 checklist）。

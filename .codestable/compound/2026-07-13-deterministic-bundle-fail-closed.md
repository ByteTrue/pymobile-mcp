# deterministic bundle fail-closed

## 背景

black-box contract parity 做到后几轮 review 时，测试数量已经很多，但仍然出现“gate 全绿、真实 wire 不一致”的假阳性：in-process 直接调 handler、effect 由 scenario 自己合成、image report 的 bundle hash 与当前 fixture 不一致。这些都能让 CMD 报告 passed，却不能证明生产 stdio 路径。

## 结论

黑盒契约证据必须是 **deterministic bundle + fail-closed**：

1. 固定 upstream revision 与 capture。
2. Python 侧所有权威 case 走真实 MCP SDK stdio，不走 in-process 旁路。
3. bundle-manifest 记录 capture / scenario / image artifact 的 content hash；任一不一致直接失败。
4. effect / backend argv 必须从 production seam 观察，不能从 expected YAML 回填。
5. image report、assert report、source-coverage report 必须带同一 bundle hash；artifact 链不一致就不能进 acceptance。
6. blocked / approved-exception / fail 必须分开记账，禁止把 blocked 或 exception 聚合成 pass。

一句话：通过数不等于契约成立；只有“同一 bundle 上的 raw wire + production side effects”成立才算。

## 证据

- Feature: `.codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/`
- Bundle manifest: `tests/fixtures/mobile_mcp/bundle-manifest.json`
- Assert scripts: `scripts/assert_mobile_mcp_contract.py`, `scripts/validate_mobile_mcp_source_coverage.py`, `scripts/compare_mobile_mcp_image_backends.py`
- Acceptance commit: `f44f291`
- Final numbers: pytest 107; default 23/106; fleet 26/110; source 91; image 3 modes; live 16/16; Pi direct-tools passed

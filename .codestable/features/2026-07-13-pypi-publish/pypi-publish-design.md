---
doc_type: feature-design
slug: pypi-publish
status: draft
created: 2026-07-13
roadmap: pymobile-mcp-productize-0.3
roadmap_item: pypi-publish
nature: non-functional
---

# PyPI 发布路径（optional）

## 1. 目标
提供 tag→PyPI 分发，或留下可审计 blocked-by-env 证据；**永不改写 core complete**。

## 2. 前置
- `release-0.3-black-box` accepted
- 版本三元 `0.3.0` 已成立

## 3. 发布路径（若凭证可用）
- 独立 workflow：`.github/workflows/publish.yml`（不要做成 unit CI 必跑 job）
- trigger：`v*` tag
- auth：OIDC Trusted Publisher 或 `PYPI_API_TOKEN`（实现时二选一写死）
- build：`python -m build`
- verify：`pip index versions pymobile-mcp` 可见 0.3.0 或等价 install 证据

## 4. 状态文件（固定路径）
**published 与 blocked 都必须写此文件。** published 时 evidence 需含 pip index/install 与 0.3.0。

## 4b. 状态文件（固定路径）
`.codestable/features/2026-07-13-pypi-publish/pypi-publish-status.md`

字段：
```yaml
status: published | blocked-by-env | failed
version: 0.3.0
reason: ...
timestamp: ISO-8601
evidence: ...
```

## 5. 错误分类
- 缺 token / 无 Trusted Publisher 配置 → `blocked-by-env`
- 包名冲突 / build 失败 / upload 失败 / install 失败 → status=`failed`（acceptance fail；不是 blocked）
- published/blocked/failed 都写同一状态文件；任一结果都不改写 core DoD

## 6. 成功标准
- status 文件存在且 status ∈ {published, blocked-by-env}
- CMD-PYPI-001 校验 status 文件
- 无 public API/schema 变更

## 7. 明确不做
不因 PyPI 阻塞 git release；不改 package 公共 API。

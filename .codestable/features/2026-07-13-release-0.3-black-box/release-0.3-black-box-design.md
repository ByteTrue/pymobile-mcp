---
doc_type: feature-design
slug: release-0.3-black-box
status: approved
created: 2026-07-13
roadmap: pymobile-mcp-productize-0.3
roadmap_item: release-0.3-black-box
nature: non-functional
---

# 发布 v0.3.0 black-box cut

## 0. 术语与范围
- Wire Contract / Deterministic Bundle / Exception Ledger：见 CONTEXT.md
- 无 runtime 接口变更

## 1. 目标与成功标准
**目标**：把 black-box parity 打成可观察的 v0.3.0 发布点。

**核心行为**：
1. `pyproject.toml` version 与 `src/pymobile_mcp/__init__.py` `__version__` = `0.3.0`
2. `CHANGELOG.md`：将 **整个** Unreleased 迁入 `## 0.3.0 — <date>`，Unreleased 置空（或仅含切割后新笔记）
3. `README.md` 与 `docs/regression-checklist.md` 版本头/安装引用 → 0.3.0 / v0.3.0
4. 创建 annotated tag `v0.3.0` 与 GitHub Release；body 含 black-box parity + 两项 exception

**成功标准**：
- CMD-001 pytest exit 0
- CMD-REL-001：pyproject == __version__ == 0.3.0
- CMD-REL-002：tag + Release 存在且 body 含 parity/fleet/recording
- CMD-BUNDLE-001：bundle-manifest 工作树未脏
- diff 无 runtime/schema 契约改动

**明确不做**：不改 runtime/schema；不升 pin；不强制 live；不做 PyPI。

**基线**：当前 0.2.0；Unreleased 含 black-box 与基建条目。

## 2. 名词层
现状：0.2.0 发布面。  
变化：版本元数据 + 文档切割 + Release；不改 MCP wire 契约。

## 3. 编排层
```text
precheck pytest/bundle
  → bump versions
  → cut CHANGELOG/README/checklist
  → tag + gh release
  → CMD-REL-001/002 + BUNDLE-001
```

## 4. 约束
- tag 已存在则不强制覆盖
- blocked live 默认不阻塞本 release
- 挂载点：version 字段、CHANGELOG 节、README、regression-checklist、Release

## 5. 验证
见 checklist dod.commands。

## 6. 失败恢复
验证红回到本契约；不扩 runtime scope。

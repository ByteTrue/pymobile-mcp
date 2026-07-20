---
doc_type: feature-acceptance
slug: ios-gray-feedback
status: passed
created: 2026-07-20
auditor: independent-subagent
---

# ios-gray-feedback Acceptance

## Verdict

**passed / Accept**。

## Criteria

- Windows 截图不再调用不存在的 `os.uname()`：passed。
- 无缩放后端时返回原始 PNG：passed（MIME + 既有 byte-identity evidence）。
- iOS core smoke 继承父环境并覆盖 `PYTHONPATH=src`：passed。
- runner / port / device 配置透传：passed。
- runtime、README、regression checklist、core smoke 不宣称支持远程 WDA host：passed。
- focused 3 / full 110 / focused isort / diff check：passed。
- independent review：passed，blocking / important / minor = 0。
- independent QA round 2：passed。
- staged files：none。
- scope cleanliness：passed；无新依赖、无无关重构、无提交 `uv.lock`。

## TDD Policy

Evidence pack 记录三项 RED failure，随后 GREEN 与 focused/full VERIFY 均通过。无 TDD exception。

## Blocked And Residual Risk

真实 Windows 与物理 iOS/WDA live 未执行或 blocked，未计为 pass。由于核心改动可在确定性 seam 完整验证，独立 QA 与 acceptance 判断其为非核心残余风险，不阻塞本 feature。

## Writebacks

本 feature 为灰度缺陷修复，无 roadmap item、architecture 或 requirement 文档需额外回写；README 与 regression checklist 已是要求内的公开契约回写。

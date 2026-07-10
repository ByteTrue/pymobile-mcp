---
doc_type: feature-qa
feature: 2026-07-07-ios-pmd3-wda-core
status: passed
tested: 2026-07-11
round: 1
---

# ios-pmd3-wda-core QA 报告

| ID | 场景 | 结果 |
|---|---|---|
| QA-001 | pytest unit/fake iOS | pass |
| QA-002 | WDA source parse | pass |
| QA-003 | live smoke no iOS device | blocked-by-env (documented) |
| QA-004 | no go-ios dependency | pass |

## Commands

- `.venv/bin/python -m pytest` → 40 passed
- live smoke exit 2 blocked-by-env

## Verdict

- Status: passed (implementation + documented environment blocker)

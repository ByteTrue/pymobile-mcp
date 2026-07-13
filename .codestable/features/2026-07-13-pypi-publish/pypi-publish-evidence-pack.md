---
doc_type: feature-evidence-pack
feature: pypi-publish
status: generated
---

# pypi-publish evidence pack

## 1. Scope

- Design: `.codestable/features/2026-07-13-pypi-publish/pypi-publish-design.md`
- Checklist: `.codestable/features/2026-07-13-pypi-publish/pypi-publish-checklist.yaml`

## 2. DoD Results

```json
{
  "gate_id": "dod-runner",
  "stage": "implementation",
  "status": "passed",
  "blocking": [],
  "warnings": [],
  "evidence": [
    {
      "command": "PATH=.venv/bin:$PATH python -m pytest",
      "exit_code": 0,
      "stdout": "============================= test session starts ==============================\nplatform darwin -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0\nrootdir: /Users/byte/workspace/projects/pymobile-mcp\nconfigfile: pyproject.toml\nplugins: cov-7.1.0, anyio-4.14.1, asyncio-1.4.0\nasyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function\ncollected 107 items\n\ntests/test_all_devices_live_smoke.py ........                            [  7%]\ntests/test_black_box_contract.py ...............................         [ 36%]\ntests/test_contract_registry.py ........................................ [ 73%]\n.......                                                                  [ 80%]\ntests/test_driver_qa_fixes.py ..................                         [ 97%]\ntests/test_ios_live_smoke_support.py ...                                 [100%]\n\n============================= 107 passed in 3.95s ==============================\n",
      "stderr": "",
      "id": "CMD-001",
      "core": true,
      "failure_handling": null
    },
    {
      "command": "PATH=.venv/bin:$PATH python -c 'from pathlib import Path; p=Path(\".codestable/features/2026-07-13-pypi-publish/pypi-publish-status.md\"); assert p.is_file(), \"missing status file\"; t=p.read_text().lower(); ok=(\"status: published\" in t) or (\"status: blocked-by-env\" in t) or (\"status: failed\" in t); assert ok, t; pub=\"status: published\" in t; assert (not pub) or ((\"0.3.0\" in t) and ((\"pip\" in t) or (\"index\" in t) or (\"install\" in t)))'\n",
      "exit_code": 0,
      "stdout": "",
      "stderr": "",
      "id": "CMD-PYPI-001",
      "core": false,
      "failure_handling": null
    }
  ],
  "providers": {}
}
```

## 3. Validation Commands

Extracted from checklist `dod.commands`; see DoD Results for command status.

## 4. Scope And Cleanliness

Design bytes: 1287
Checklist bytes: 1935

## 5. Residual Risks

- none

## 6. Provider Signals

```json
{
  "archguard": {
    "status": "skipped",
    "reason": "archguard collection disabled",
    "warnings": []
  },
  "meta_cc": {
    "status": "skipped",
    "reason": "meta-cc collection disabled",
    "warnings": []
  }
}
```

## 7. Gate Results

```json
{
  "gate_id": "scope-gate",
  "stage": "implementation",
  "status": "passed",
  "blocking": [],
  "warnings": [],
  "evidence": [
    {
      "changed_files": [
        ".codestable/features/2026-07-13-pypi-publish/pypi-publish-checklist.yaml",
        ".codestable/roadmap/pymobile-mcp-productize-0.3/goal-state.yaml",
        ".codestable/features/2026-07-13-pypi-publish/pypi-publish-status.md"
      ],
      "ignored_machine_artifacts": [
        ".codestable/features/2026-07-13-pypi-publish/pypi-publish-dod-results.json"
      ],
      "allowed_prefixes": [
        ".codestable/features/2026-07-13-pypi-publish",
        ".codestable/features/2026-07-13-pypi-publish",
        ".codestable/roadmap/pymobile-mcp-productize-0.3"
      ]
    }
  ],
  "providers": {}
}
```

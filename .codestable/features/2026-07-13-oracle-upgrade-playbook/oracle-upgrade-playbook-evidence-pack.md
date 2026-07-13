---
doc_type: feature-evidence-pack
feature: oracle-upgrade-playbook
status: generated
---

# oracle-upgrade-playbook evidence pack

## 1. Scope

- Design: `.codestable/features/2026-07-13-oracle-upgrade-playbook/oracle-upgrade-playbook-design.md`
- Checklist: `.codestable/features/2026-07-13-oracle-upgrade-playbook/oracle-upgrade-playbook-checklist.yaml`

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
      "stdout": "============================= test session starts ==============================\nplatform darwin -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0\nrootdir: /Users/byte/workspace/projects/pymobile-mcp\nconfigfile: pyproject.toml\nplugins: cov-7.1.0, anyio-4.14.1, asyncio-1.4.0\nasyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function\ncollected 107 items\n\ntests/test_all_devices_live_smoke.py ........                            [  7%]\ntests/test_black_box_contract.py ...............................         [ 36%]\ntests/test_contract_registry.py ........................................ [ 73%]\n.......                                                                  [ 80%]\ntests/test_driver_qa_fixes.py ..................                         [ 97%]\ntests/test_ios_live_smoke_support.py ...                                 [100%]\n\n============================= 107 passed in 3.94s ==============================\n",
      "stderr": "",
      "id": "CMD-001",
      "core": true,
      "failure_handling": null
    },
    {
      "command": "python -c 'from pathlib import Path; req=[\"scripts/capture_mobile_mcp_contract.py\",\"scripts/capture_mobile_mcp_calls.py\",\"scripts/assert_mobile_mcp_contract.py\",\"scripts/validate_mobile_mcp_source_coverage.py\",\"scripts/compare_mobile_mcp_image_backends.py\"]; missing=[p for p in req if not Path(p).is_file()]; assert not missing, missing; pb=Path(\"docs/oracle-upgrade-playbook.md\"); assert pb.is_file(), pb; text=pb.read_text(); assert \"PYMOBILE_MCP_UPSTREAM_SOURCE\" in text; assert \"/Users/\" not in text; assert all(flag in text for flag in [\"--source\",\"--mode\",\"--expected-revision\",\"--scenarios\",\"--bundle-manifest\",\"blocked\"])'\n",
      "exit_code": 0,
      "stdout": "",
      "stderr": "",
      "id": "CMD-ORACLE-001",
      "core": true,
      "failure_handling": null
    }
  ],
  "providers": {}
}
```

## 3. Validation Commands

Extracted from checklist `dod.commands`; see DoD Results for command status.

## 4. Scope And Cleanliness

Design bytes: 1832
Checklist bytes: 2069

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
        ".codestable/features/2026-07-13-oracle-upgrade-playbook/oracle-upgrade-playbook-checklist.yaml",
        ".codestable/roadmap/pymobile-mcp-productize-0.3/goal-state.yaml",
        "docs/oracle-upgrade-playbook.md"
      ],
      "ignored_machine_artifacts": [
        ".codestable/features/2026-07-13-oracle-upgrade-playbook/oracle-upgrade-playbook-dod-results.json"
      ],
      "allowed_prefixes": [
        ".codestable/features/2026-07-13-oracle-upgrade-playbook",
        "docs",
        ".codestable/features/2026-07-13-oracle-upgrade-playbook",
        ".codestable/roadmap/pymobile-mcp-productize-0.3"
      ]
    }
  ],
  "providers": {}
}
```

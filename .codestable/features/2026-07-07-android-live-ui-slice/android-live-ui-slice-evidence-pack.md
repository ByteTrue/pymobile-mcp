---
doc_type: feature-evidence-pack
feature: 2026-07-07-android-live-ui-slice
status: generated
---

# 2026-07-07-android-live-ui-slice evidence pack

## 1. Scope

- Design: `.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-design.md`
- Checklist: `.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-checklist.yaml`

## 2. DoD Results

```json
{
  "gate_id": "dod-runner",
  "stage": "implementation.before_review",
  "status": "passed",
  "blocking": [],
  "warnings": [],
  "evidence": [
    {
      "command": "python -m pytest",
      "exit_code": 0,
      "stdout": "============================= test session starts ==============================\nplatform darwin -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0\nrootdir: /Users/byte/workspace/projects/pymobile-mcp-android-mvp-goal\nconfigfile: pyproject.toml\nplugins: cov-7.1.0, anyio-4.14.1, asyncio-1.4.0, xonsh-0.24.0\nasyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function\ncollected 37 items\n\ntests/test_contract_registry.py .....................................    [100%]\n\n============================== 37 passed in 0.40s ==============================\n",
      "stderr": "/Users/byte/workspace/projects/pymobile-mcp-android-mvp-goal/.venv/lib/python3.14/site-packages/pytest_asyncio/plugin.py:299: PytestDeprecationWarning: The configuration option \"asyncio_default_fixture_loop_scope\" is unset.\nThe event loop scope for asynchronous fixtures will default to the \"fixture\" caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to \"function\" scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: \"function\", \"class\", \"module\", \"package\", \"session\"\n\n  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))\n",
      "id": "CMD-001",
      "core": true,
      "failure_handling": "fix-or-block"
    },
    {
      "command": "PYMOBILE_MCP_ANDROID_ACTIONS=1 PATH=.venv/bin:$PATH python tests/android_live_smoke.py",
      "exit_code": 0,
      "stdout": "{\n  \"status\": \"passed\",\n  \"device\": \"emulator-5554\",\n  \"screen_size\": {\n    \"height\": 2400,\n    \"scale\": 1.0,\n    \"width\": 1080\n  },\n  \"element_count\": 41,\n  \"tap\": {\n    \"x\": 540.0,\n    \"y\": 163.5\n  }\n}\n",
      "stderr": "",
      "id": "CMD-ANDROID-001",
      "core": true,
      "failure_handling": "fix-or-block"
    }
  ],
  "providers": {}
}
```

## 3. Validation Commands

Extracted from checklist `dod.commands`; see DoD Results for command status.

## 4. Scope And Cleanliness

Design bytes: 6528
Checklist bytes: 2720

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
  "stage": "implementation.before_review",
  "status": "passed",
  "blocking": [],
  "warnings": [],
  "evidence": [
    {
      "changed_files": [
        ".codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-checklist.yaml",
        ".codestable/roadmap/pymobile-mcp-android-mvp/goal-state.yaml",
        "src/pymobile_mcp/tools/registry.py",
        "tests/test_contract_registry.py",
        ".codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-implementation-blocked.md",
        ".codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-live-smoke.md",
        "src/pymobile_mcp/drivers/android.py",
        "src/pymobile_mcp/tools/android.py",
        "tests/android_live_smoke.py"
      ],
      "ignored_machine_artifacts": [],
      "allowed_prefixes": [
        ".codestable/features/2026-07-07-android-live-ui-slice",
        "src",
        "tests",
        ".codestable/roadmap/pymobile-mcp-android-mvp/goal-state.yaml"
      ]
    }
  ],
  "providers": {}
}
```

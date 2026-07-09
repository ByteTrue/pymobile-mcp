---
doc_type: feature-review
feature: 2026-07-07-android-live-ui-slice
status: passed
reviewer: subagent
reviewed: 2026-07-10
round: 1
---

# android-live-ui-slice 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-design.md`
- Checklist: `.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-scope-gate-results.json`
- DoD results: `.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-dod-results.json`
- Live smoke evidence: `.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-live-smoke.md`
- Diff basis: Android driver + Android tool handlers + registry registration + fake-driver tests + stdio live smoke script + roadmap goal-state progress.
- Baseline dirty files: none from previous feature; current dirty/untracked are this feature artifacts.

### Independent Review

- Ring A independent reviewer: Paseo agent `ac6cd966-73f6-42ef-aad2-2fed7ec3a696` completed with `Verdict: passed`.
- Ring B OCR: `ocr llm test` failed because no LLM endpoint is configured; recorded as non-blocking fallback.
- Merge policy: no blocking / important findings. Nits and residual risks are acknowledged below; none require implementation change before QA.

## 2. Diff Summary

- Added:
  - `src/pymobile_mcp/drivers/android.py`
  - `src/pymobile_mcp/tools/android.py`
  - `tests/android_live_smoke.py`
  - `.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-live-smoke.md`
  - gate/evidence JSON/Markdown artifacts
- Modified:
  - `src/pymobile_mcp/tools/registry.py` registers Android handlers while keeping device libraries out of registry/specs.
  - `tests/test_contract_registry.py` covers Android fake-driver path and preserves contract registry coverage.
  - `.codestable/features/2026-07-07-android-live-ui-slice/android-live-ui-slice-checklist.yaml` steps done and checks passed.
  - `.codestable/roadmap/pymobile-mcp-android-mvp/goal-state.yaml` marks feature as implementing.

## 3. Adversarial Pass

- Attacked risk: Android handlers silently return success while driver call fails.
  - Evidence: `tests/android_live_smoke.py` checks each action result for structured error and fails if one appears.
- Attacked risk: raw UIAutomator XML leaks through MCP output.
  - Evidence: handler returns JSON with `elements[*].coordinates` and semantic fields; no raw XML field is emitted.
- Attacked risk: registry layer imports `uiautomator2` directly.
  - Evidence: registry imports `.android` handlers only; device library import is in `drivers/android.py` and lazy path in `tools/android.py`.
- Attacked risk: no-device path is counted as passed.
  - Evidence: live smoke returned `blocked` before emulator was available; final DoD required action-enabled live smoke with exit 0.

## 4. Findings

### blocking

none

### important

none

### nit

- `src/pymobile_mcp/tools/android.py` `_driver_for()` filters online devices and then lets `AndroidDriver.connect()` surface connection failures through the common `DriverError` envelope. This is acceptable for this slice because live smoke covers the online emulator path.
- `tests/android_live_smoke.py` chooses a safe tap point heuristically when `PYMOBILE_MCP_ANDROID_TAP` is not set. It worked on the current launcher search field; callers can override it via env when needed.

### suggestion

- Add a focused unit test for `parse_uiautomator_xml()` if XML parsing grows. Current fake-driver and live smoke evidence are enough for this feature.

### residual-risk

- Android screenshot/hierarchy behavior depends on emulator/device state and launcher UI. This is the known live-device volatility called out in the design.
- `pytest_asyncio` emits a deprecation warning about default fixture loop scope; non-blocking for this feature.

## 5. Test And QA Focus

QA must re-run and verify:

- `.venv/bin/python -m pytest`
- `PYMOBILE_MCP_ANDROID_ACTIONS=1 PATH=.venv/bin:$PATH python tests/android_live_smoke.py`
- Confirm live smoke evidence includes device id, positive screen size, image screenshot, element count, and successful tap/double/long/swipe/type actions.
- Confirm `mobile_get_page_source` remains absent from `list_tools`.
- Confirm registry/specs still do not directly import `uiautomator2` / `pymobiledevice3`.

## 6. Verdict

- Status: passed
- Next: `cs-feat-qa`

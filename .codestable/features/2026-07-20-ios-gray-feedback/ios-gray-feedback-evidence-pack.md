# ios-gray-feedback Implementation Evidence

## Scope

- `src/pymobile_mcp/tools/contract.py`: cross-platform screenshot backend detection.
- `tests/ios_pmd3_wda_live_smoke.py`: inherit MCP child environment and report only effective WDA settings.
- `tests/test_gray_feedback.py`: focused regression checks.
- `README.md`, `docs/regression-checklist.md`: accurate RSD/WDA configuration contract.

## RED → GREEN → VERIFY

| Step | RED | GREEN | VERIFY |
|---|---|---|---|
| Windows screenshot | `test_windows_screenshot_without_scaler_returns_png` failed with `AttributeError: module 'os' has no attribute 'uname'` | `_sips_available()` now uses `platform.system()` | focused test passed |
| iOS smoke env | `test_ios_core_smoke_inherits_wda_environment` showed child env was only `PYTHONPATH` | env now starts from `dict(os.environ)` and overrides `PYTHONPATH` | focused test passed |
| WDA host contract | static regression test found `PYMOBILE_MCP_WDA_HOST` in README and smoke | removed host claim; documented RSD service-client port semantics | focused test passed |

## Validation Commands

- `uv run --extra dev python -m pytest tests/test_gray_feedback.py -q` → 3 passed.
- `uv run --extra dev python -m pytest` → 110 passed.
- `git diff --check` → passed.

## Scope And Cleanliness

Changes are limited to the approved files and CodeStable artifacts. `.venv` is ignored. No new dependency was added.

## Residual Risks

No Windows host or physical iOS device was available in this worktree. Deterministic platform/env tests cover both regressions; existing live smoke remains the hardware acceptance path.

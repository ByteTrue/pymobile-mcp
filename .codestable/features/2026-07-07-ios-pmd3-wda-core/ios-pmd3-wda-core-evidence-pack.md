# ios-pmd3-wda-core Evidence Pack

## Commands

1. `.venv/bin/python -m pytest` → 40 passed
2. `PATH=.venv/bin:$PATH python tests/ios_pmd3_wda_live_smoke.py` → blocked-by-env (exit 2)

## Artifacts

- `src/pymobile_mcp/drivers/ios.py`
- `tests/ios_pmd3_wda_live_smoke.py`
- live/spike notes: `ios-pmd3-wda-core-live-smoke.md`

## Notes

- Feature completed as code + unit coverage + documented environment blocker.
- Live iOS pass remains blocked until a paired device and reachable WDA are available.

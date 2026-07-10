# android-app-system-tools Evidence Pack

## Commands

1. `.venv/bin/python -m pytest` → 38 passed
2. `PATH=.venv/bin:$PATH python tests/android_app_system_live_smoke.py` → status passed on emulator-5554

## Artifacts

- Live smoke notes: `android-app-system-tools-live-smoke.md`
- Validation helpers: `src/pymobile_mcp/tools/validation.py`
- Android driver app/system methods: `src/pymobile_mcp/drivers/android.py`
- Android handlers: `src/pymobile_mcp/tools/android.py`

## Notes

- install/uninstall live path intentionally blocked without `PYMOBILE_MCP_ANDROID_APK` + `PYMOBILE_MCP_ANDROID_DESTRUCTIVE=1`
- temporary screenshot file is deleted by the live smoke script after verification

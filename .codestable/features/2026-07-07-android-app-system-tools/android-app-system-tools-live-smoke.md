# android-app-system-tools Live Smoke

## Command

```bash
PATH=.venv/bin:$PATH python tests/android_app_system_live_smoke.py
```

Optional destructive install/uninstall:

```bash
PYMOBILE_MCP_ANDROID_APK=/path/to/app.apk \
PYMOBILE_MCP_ANDROID_PACKAGE=com.example.app \
PYMOBILE_MCP_ANDROID_DESTRUCTIVE=1 \
PATH=.venv/bin:$PATH python tests/android_app_system_live_smoke.py
```

## Result (2026-07-11)

```json
{
  "status": "passed",
  "device": "emulator-5554",
  "app_count": 19,
  "orientation": "portrait",
  "saveTo": "/Users/byte/workspace/projects/pymobile-mcp-android-mvp-goal/tmp-android-app-system-smoke.png",
  "destructive": {
    "status": "blocked",
    "reason": "install/uninstall require PYMOBILE_MCP_ANDROID_APK and PYMOBILE_MCP_ANDROID_DESTRUCTIVE=1"
  }
}
```

## Covered

- `mobile_list_apps`
- `mobile_open_url` https success + custom scheme rejected
- `mobile_press_button` HOME
- `mobile_get_orientation` / `mobile_set_orientation`
- `mobile_save_screenshot` safe path write + unsafe path rejected
- `mobile_launch_app` / `mobile_terminate_app` on first listed launcher app
- install/uninstall left blocked without explicit APK env

# pymobile-mcp

Pure Python MCP server for mobile automation — Android via `uiautomator2`/`adbutils`, iOS via `pymobiledevice3` + WebDriverAgent HTTP.

Public contract: **23 mobile-mcp core tools** from `mobile-mcp` `src/server.ts` (`c5d7d27`).  
Not public: `mobile_get_page_source`, remote fleet tools.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
# or: pip install pymobile-mcp
```

## MCP config

```json
{
  "mcpServers": {
    "pymobile-mcp": {
      "command": "pymobile-mcp",
      "args": ["run"]
    }
  }
}
```

From a checkout, use:

```json
{
  "mcpServers": {
    "pymobile-mcp": {
      "command": "python",
      "args": ["-m", "pymobile_mcp.cli", "run"],
      "env": { "PYTHONPATH": "src" }
    }
  }
}
```

## Live smoke

### Android UI

```bash
# read-only-ish probe stops before interactions unless ACTIONS=1
PATH=.venv/bin:$PATH python tests/android_live_smoke.py
PYMOBILE_MCP_ANDROID_ACTIONS=1 PATH=.venv/bin:$PATH python tests/android_live_smoke.py
# optional: PYMOBILE_MCP_ANDROID_DEVICE=emulator-5554 PYMOBILE_MCP_ANDROID_TAP=x,y
```

### Android app/system

```bash
PATH=.venv/bin:$PATH python tests/android_app_system_live_smoke.py
# install/uninstall only with:
# PYMOBILE_MCP_ANDROID_APK=/path/app.apk PYMOBILE_MCP_ANDROID_PACKAGE=com.example \
# PYMOBILE_MCP_ANDROID_DESTRUCTIVE=1 PATH=.venv/bin:$PATH python tests/android_app_system_live_smoke.py
```

### Android recording/crash

```bash
PATH=.venv/bin:$PATH python tests/android_recording_crash_live_smoke.py
```

### iOS core / parity

iOS uses pure `pymobiledevice3` userspace tunnel + in-process WDA service client.
No go-ios runtime and no root. Requires installed WDA runner
(`PYMOBILE_MCP_WDA_XCTRUNNER`, default `com.byte.WebDriverAgentRunner.xctrunner`).

```bash
PATH=.venv/bin:$PATH python tests/ios_pmd3_wda_live_smoke.py
PYMOBILE_MCP_IOS_ACTIONS=1 PATH=.venv/bin:$PATH python tests/ios_pmd3_wda_live_smoke.py
PATH=.venv/bin:$PATH python tests/ios_system_helpers_live_smoke.py
PATH=.venv/bin:$PATH python tests/ios_app_lifecycle_live_smoke.py
PATH=.venv/bin:$PATH python tests/crash_tools_live_smoke.py
PATH=.venv/bin:$PATH python tests/ios_app_recording_crash_live_smoke.py
# optional:
# PYMOBILE_MCP_IOS_DEVICE=<udid>
# PYMOBILE_MCP_WDA_PORT=8100
# PYMOBILE_MCP_WDA_XCTRUNNER=com.byte.WebDriverAgentRunner.xctrunner
```

No authorized device/WDA ⇒ scripts exit `2` with `status=blocked` (not pass).

## Env knobs

| Env | Purpose |
|---|---|
| `MOBILEMCP_ALLOW_UNSAFE_URLS=1` | allow non-http(s) `mobile_open_url` schemes |
| `PYMOBILE_MCP_ANDROID_ACTIONS=1` | enable tap/type interactions in Android UI smoke |
| `PYMOBILE_MCP_ANDROID_TAP=x,y` | override Android tap point |
| `PYMOBILE_MCP_ANDROID_APK` + `PYMOBILE_MCP_ANDROID_DESTRUCTIVE=1` | allow install/uninstall smoke |
| `PYMOBILE_MCP_WDA_HOST` / `PYMOBILE_MCP_WDA_PORT` | iOS WebDriverAgent endpoint |

## Capability matrix (23 core tools)

Legend:

- **supported**: implemented and smoke/unit covered on this platform
- **unsupported**: stable structured `unsupported_platform` (not fake empty success)
- **blocked-by-env**: code path exists; live verification needs device/WDA on this host

| Tool | Android | iOS |
|---|---|---|
| mobile_list_available_devices | supported | supported (usbmux discovery; empty when none) |
| mobile_list_apps | supported | supported |
| mobile_launch_app | supported | supported |
| mobile_terminate_app | supported | supported |
| mobile_install_app | supported (destructive) | supported (destructive, guarded) |
| mobile_uninstall_app | supported (destructive) | supported (destructive, guarded) |
| mobile_get_screen_size | supported | supported |
| mobile_click_on_screen_at_coordinates | supported | supported |
| mobile_double_tap_on_screen | supported | supported |
| mobile_long_press_on_screen_at_coordinates | supported | supported |
| mobile_list_elements_on_screen | supported | supported (WDA source internal only) |
| mobile_press_button | supported | supported (HOME/VOLUME_*; BACK unsupported) |
| mobile_open_url | supported (http/https default) | supported (http/https; device must be unlocked) |
| mobile_swipe_on_screen | supported | supported |
| mobile_type_keys | supported | supported |
| mobile_save_screenshot | supported | supported |
| mobile_take_screenshot | supported | supported |
| mobile_set_orientation | supported | supported |
| mobile_get_orientation | supported | supported |
| mobile_start_screen_recording | supported | unsupported |
| mobile_stop_screen_recording | supported | unsupported |
| mobile_list_crashes | supported (dropbox) | supported (crash reports) |
| mobile_get_crash | supported (dropbox) | supported (crash reports) |

\* iOS core driver implements UI/session methods; some app/system helpers stay Android-first and return platform/driver errors if not routed. Prefer the matrix cells above for product status.

### Evidence sources

- Android UI/app/recording acceptance under `.codestable/features/2026-07-07-android-*`
- iOS core/parity acceptance under `.codestable/features/2026-07-07-ios-*`
- Schema fixture: `tests/fixtures/mobile_mcp_core_tools.json` (`source.path` + `git_revision`)

## Tests

```bash
python -m pytest
```

## Known limits

- Android crash tools use `dumpsys dropbox --print` (includes non-crash diagnostics tags when no app crashes exist).
- iOS core UI/app/crash use pure pymobiledevice3; screen recording remains unsupported (userspace RSD lacks `com.apple.coredevice.displayservice`; see recording spike).
- Recording is process-local (`ActiveRecording`); no cross-process resume.
- `mobile_open_url` rejects custom schemes unless `MOBILEMCP_ALLOW_UNSAFE_URLS=1`.
- Screenshot/recording host paths must resolve under cwd or system temp.

## License

GPL-3.0

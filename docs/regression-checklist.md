# Live regression checklist (v0.3.1)

Use this after device reconnects, dependency bumps, or before tagging.

## Rules

| Exit | Meaning | Treat as |
|---|---|---|
| `0` + `"status":"passed"` | smoke passed | pass |
| `2` + `"status":"blocked"` | no authorized device / env missing | **not** a pass; env gap |
| `1` + `"status":"failed"` | code/path broke | fail |

Never promote `blocked` to pass. No go-ios.

Unit gate (always):

```bash
PATH=.venv/bin:$PATH python -m pytest -q
# expect: 107 passed
```

Optional Android crash listing: `PYMOBILE_MCP_ANDROID_DROPBOX_ALL=1` includes non-crash dropbox tags.

Unset proxies for iOS/usbmux runs:

```bash
export NO_PROXY='*'
# optional: unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy
```

Public result checks use upstream natural-language/image content. Actionable errors omit `isError`; schema/unexpected/screenshot errors set `isError=true`.

---

## Android (need authorized device / emulator)

### A1. UI core
```bash
PATH=.venv/bin:$PATH python tests/android_live_smoke.py
# interactions:
PYMOBILE_MCP_ANDROID_ACTIONS=1 PATH=.venv/bin:$PATH python tests/android_live_smoke.py
# optional: PYMOBILE_MCP_ANDROID_DEVICE=emulator-5554 PYMOBILE_MCP_ANDROID_TAP=x,y
```
Covers: devices, screen size, screenshot, elements, tap/double/long/swipe/type.

### A2. App / system
```bash
PATH=.venv/bin:$PATH python tests/android_app_system_live_smoke.py
# destructive install/uninstall only when intentional:
# PYMOBILE_MCP_ANDROID_APK=/path/app.apk \
# PYMOBILE_MCP_ANDROID_PACKAGE=com.example \
# PYMOBILE_MCP_ANDROID_DESTRUCTIVE=1 \
# PATH=.venv/bin:$PATH python tests/android_app_system_live_smoke.py
```
Covers: list/launch/terminate apps, buttons, open_url, orientation, save_screenshot.

### A3. Recording + crash
```bash
PATH=.venv/bin:$PATH python tests/android_recording_crash_live_smoke.py
```
Covers: start/stop screenrecord → host mp4; list/get crash via dropbox.

---

## iOS (need paired device + installed WDA runner)

Overrides: `PYMOBILE_MCP_WDA_XCTRUNNER`, `PYMOBILE_MCP_WDA_PORT`, and `PYMOBILE_MCP_IOS_DEVICE`.
The port is used by the in-process userspace RSD service client; remote WDA host URLs are not supported.
### I1. Core UI (pmd3 userspace + WDA)
```bash
PATH=.venv/bin:$PATH python tests/ios_pmd3_wda_live_smoke.py
PYMOBILE_MCP_IOS_ACTIONS=1 PATH=.venv/bin:$PATH python tests/ios_pmd3_wda_live_smoke.py
```
Covers: devices, screen size, screenshot, elements, gestures, type.

### I2. System helpers
```bash
# unlock phone first for open_url
PATH=.venv/bin:$PATH python tests/ios_system_helpers_live_smoke.py
```
Covers: HOME/VOLUME press, open_url, save_screenshot.  
Locked device: open_url may fail with explicit driver error (expected).

### I3. App lifecycle
```bash
PATH=.venv/bin:$PATH python tests/ios_app_lifecycle_live_smoke.py
# install/uninstall only with IPA + DESTRUCTIVE=1 (same pattern as Android)
```
Covers: list/launch/terminate apps.

### I4. Crash (both platforms if both online)
```bash
PATH=.venv/bin:$PATH python tests/crash_tools_live_smoke.py
```

### I5. Recording parity (real-device approved exception)
```bash
PATH=.venv/bin:$PATH python tests/ios_app_recording_crash_live_smoke.py
```
Expect exact Actionable text for real iOS recording, with `isError` omitted. A booted iOS Simulator is tested separately through `simctl recordVideo` + WDA and must not use this exception.

---

## Minimal dual-device gate (recommended before release)

```bash
export NO_PROXY='*'
PATH=.venv/bin:$PATH python -m pytest -q
PATH=.venv/bin:$PATH python tests/android_live_smoke.py
PYMOBILE_MCP_ANDROID_ACTIONS=1 PATH=.venv/bin:$PATH python tests/android_live_smoke.py
PATH=.venv/bin:$PATH python tests/android_app_system_live_smoke.py
PATH=.venv/bin:$PATH python tests/android_recording_crash_live_smoke.py
PATH=.venv/bin:$PATH python tests/ios_pmd3_wda_live_smoke.py
PYMOBILE_MCP_IOS_ACTIONS=1 PATH=.venv/bin:$PATH python tests/ios_pmd3_wda_live_smoke.py
PATH=.venv/bin:$PATH python tests/ios_system_helpers_live_smoke.py
PATH=.venv/bin:$PATH python tests/ios_app_lifecycle_live_smoke.py
PATH=.venv/bin:$PATH python tests/crash_tools_live_smoke.py
PATH=.venv/bin:$PATH python tests/ios_app_recording_crash_live_smoke.py
```

Record: host OS, device ids, iOS/Android versions, commit SHA, pass/blocked/fail per script.

Pi gate: use a fresh session and the prefixed direct tools (`pymobile_mcp_mobile_*`); generic `mcp` gateway-only availability is blocked evidence, not a direct-tools pass.

---

## Explicit non-goals

- go-ios / mobilecli runtime fallback
- Unapproved exception expansion (especially fleet discovery/schema or iOS Simulator)
- Fake empty crash lists
- Treating `blocked` as pass

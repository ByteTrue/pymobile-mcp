# pymobile-mcp

Pure Python [MCP](https://modelcontextprotocol.io/) server for mobile automation.

- **Android**: `uiautomator2` + `adbutils`
- **iOS**: pure `pymobiledevice3` userspace tunnel + WebDriverAgent (no go-ios, no root)

Public contract: **23** tools aligned with [mobile-mcp](https://github.com/mobile-next/mobile-mcp) core tools.  
Not public: `mobile_get_page_source`, remote fleet tools.

[![CI](https://github.com/ByteTrue/pymobile-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/ByteTrue/pymobile-mcp/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/ByteTrue/pymobile-mcp?display_name=tag)](https://github.com/ByteTrue/pymobile-mcp/releases/latest)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/downloads/)
[![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)

Current release: **0.2.0** · [Changelog](CHANGELOG.md) · [Live regression checklist](docs/regression-checklist.md)

## Features

- One stdio MCP server for **Android + iOS**
- Structured errors (`invalid_argument`, `unsupported_platform`, driver failures) instead of silent empty success
- Live smoke scripts that exit `blocked` (code 2) when devices are missing — never fake pass
- Destructive actions (install/uninstall) gated by explicit env flags

## Requirements

| Platform | Need |
|---|---|
| Host | Python **≥ 3.10**, `pip` |
| Android | `adb` in `PATH`, authorized device or emulator |
| iOS | macOS recommended, paired iPhone/iPad, **Developer Mode**, mounted DDI, installed WDA runner (default `com.byte.WebDriverAgentRunner.xctrunner`) |

> [!NOTE]
> iOS screen recording is **unsupported** on current pure-userspace RSD (iOS 26.5.2): no `com.apple.coredevice.displayservice`; WDA `/wda/video` can start but finalize on stop fails. See the [recording spike](.codestable/features/2026-07-11-ios-screen-recording-spike/).

## Install

### From a git checkout (recommended while pre-PyPI)

```bash
git clone https://github.com/ByteTrue/pymobile-mcp.git
cd pymobile-mcp
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
pymobile-mcp --help
```

### Dev install (tests)

```bash
pip install -e ".[dev]"
python -m pytest -q
```

### From GitHub (no local clone of tooling)

```bash
pip install "git+https://github.com/ByteTrue/pymobile-mcp.git@v0.2.0"
```

> [!TIP]
> Prefer a venv. System Python + `pip install` often fights with Homebrew/PEP 668.

## Quick start

1. Connect an Android emulator/device (`adb devices`) and/or a paired iPhone.
2. For iOS, ensure your WDA runner is installed (Xcode once); pymobile-mcp launches it over userspace tunnel.
3. Run the server:

```bash
pymobile-mcp run
# equivalent:
python -m pymobile_mcp.cli run
```

4. Point an MCP client at the process (stdio).

### MCP client config

**Installed entrypoint** (`pymobile-mcp` on `PATH`):

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

**Checkout / venv** (absolute paths are more reliable for GUI clients):

```json
{
  "mcpServers": {
    "pymobile-mcp": {
      "command": "/ABS/PATH/pymobile-mcp/.venv/bin/python",
      "args": ["-m", "pymobile_mcp.cli", "run"],
      "cwd": "/ABS/PATH/pymobile-mcp",
      "env": {
        "NO_PROXY": "*",
        "PYTHONPATH": "src"
      }
    }
  }
}
```

> [!IMPORTANT]
> For iOS USB, unset or bypass HTTP proxies (`NO_PROXY=*` or clear `http_proxy`/`https_proxy`). Proxy env often breaks usbmux / userspace tunnel.

## First tools to try

After the client connects:

1. `mobile_list_available_devices` — confirm Android/iOS ids
2. `mobile_get_screen_size` / `mobile_take_screenshot`
3. `mobile_list_elements_on_screen` — UI tree (no raw page source tool)
4. `mobile_list_apps` → `mobile_launch_app` with a known package/bundle id

## Capability matrix (23 core tools)

| Status | Meaning |
|---|---|
| **supported** | Implemented and covered by unit/live smoke on this platform |
| **unsupported** | Stable `unsupported_platform` (not fake empty success) |

| Tool | Android | iOS |
|---|---|---|
| mobile_list_available_devices | supported | supported |
| mobile_list_apps | supported | supported |
| mobile_launch_app | supported | supported |
| mobile_terminate_app | supported | supported |
| mobile_install_app | supported (destructive) | supported (destructive, gated) |
| mobile_uninstall_app | supported (destructive) | supported (destructive, gated) |
| mobile_get_screen_size | supported | supported |
| mobile_click_on_screen_at_coordinates | supported | supported |
| mobile_double_tap_on_screen | supported | supported |
| mobile_long_press_on_screen_at_coordinates | supported | supported |
| mobile_list_elements_on_screen | supported | supported (WDA source internal) |
| mobile_press_button | supported | supported (`HOME`/`VOLUME_*`; `BACK` unsupported) |
| mobile_open_url | supported (http/https default) | supported (device must be unlocked) |
| mobile_swipe_on_screen | supported | supported |
| mobile_type_keys | supported | supported |
| mobile_save_screenshot | supported | supported |
| mobile_take_screenshot | supported | supported |
| mobile_set_orientation | supported | supported |
| mobile_get_orientation | supported | supported |
| mobile_start_screen_recording | supported | **unsupported** |
| mobile_stop_screen_recording | supported | **unsupported** |
| mobile_list_crashes | supported (dropbox) | supported (crash reports) |
| mobile_get_crash | supported (dropbox) | supported (crash reports) |

## Environment variables

| Env | Purpose |
|---|---|
| `MOBILEMCP_ALLOW_UNSAFE_URLS=1` | allow non-http(s) schemes for `mobile_open_url` |
| `PYMOBILE_MCP_ANDROID_DROPBOX_ALL=1` | include non-crash dropbox tags (strictmode/boot/…) |
| `PYMOBILE_MCP_ANDROID_DEVICE` | pin Android serial for smokes |
| `PYMOBILE_MCP_ANDROID_ACTIONS=1` | enable tap/type interactions in Android UI smoke |
| `PYMOBILE_MCP_ANDROID_TAP=x,y` | override Android tap point |
| `PYMOBILE_MCP_ANDROID_APK` + `PYMOBILE_MCP_ANDROID_PACKAGE` + `PYMOBILE_MCP_ANDROID_DESTRUCTIVE=1` | allow install/uninstall smoke |
| `PYMOBILE_MCP_IOS_DEVICE` | pin iOS UDID |
| `PYMOBILE_MCP_IOS_ACTIONS=1` | enable interaction steps in iOS core smoke |
| `PYMOBILE_MCP_WDA_XCTRUNNER` | WDA runner bundle id (default `com.byte.WebDriverAgentRunner.xctrunner`) |
| `PYMOBILE_MCP_WDA_HOST` / `PYMOBILE_MCP_WDA_PORT` | legacy WDA HTTP endpoint knobs (userspace path prefers in-process service client) |
| `PYMOBILE_MCP_IOS_IPA` + `PYMOBILE_MCP_IOS_DESTRUCTIVE=1` | allow iOS install/uninstall smoke |
| `NO_PROXY=*` | recommended for iOS USB / usbmux |

## Live smoke

Scripts print JSON with `status: passed|failed|blocked`.  
**Exit `2` + `blocked` = missing device/env, not a product pass.**

```bash
export NO_PROXY='*'
PATH=.venv/bin:$PATH

# Android
python tests/android_live_smoke.py
PYMOBILE_MCP_ANDROID_ACTIONS=1 python tests/android_live_smoke.py
python tests/android_app_system_live_smoke.py
python tests/android_recording_crash_live_smoke.py

# iOS (unlock phone for open_url)
python tests/ios_pmd3_wda_live_smoke.py
PYMOBILE_MCP_IOS_ACTIONS=1 python tests/ios_pmd3_wda_live_smoke.py
python tests/ios_system_helpers_live_smoke.py
python tests/ios_app_lifecycle_live_smoke.py
python tests/crash_tools_live_smoke.py
python tests/ios_app_recording_crash_live_smoke.py   # recording stays unsupported
```

Full dual-device gate: [docs/regression-checklist.md](docs/regression-checklist.md).

## Architecture (short)

```
MCP client  --stdio-->  pymobile-mcp server
                           │
                           ├─ tools/registry + specs   (23-tool contract)
                           ├─ tools/* handlers
                           └─ drivers/
                                ├─ android.py  (adbutils / uiautomator2)
                                └─ ios.py      (UserspaceRsdTunnel + WDA)
```

## Development

```bash
pip install -e ".[dev]"
python -m pytest -q
```

CI runs unit tests on Python 3.11 and 3.12 ([workflow](.github/workflows/ci.yml)). Device live smokes stay local.

## Known limits

- Android crashes come from `dumpsys dropbox --print`, filtered to crash/ANR/tombstone-like tags by default
- iOS screen recording remains **unsupported** under pure userspace RSD on iOS 26.5.2
- Recording state is process-local (`ActiveRecording`); no cross-process resume
- Custom URL schemes need `MOBILEMCP_ALLOW_UNSAFE_URLS=1`
- Screenshot/recording host paths must resolve under cwd or system temp
- No go-ios runtime path by design

## Troubleshooting

| Symptom | What to check |
|---|---|
| iOS device list empty | Cable/trust, `pymobiledevice3 usbmux list`, proxies (`NO_PROXY=*`) |
| iOS driver tunnel errors | Developer Mode, `pymobiledevice3 mounter auto-mount`, only one userspace tunnel process |
| `open_url` fails on iPhone | Unlock the device (passcode lock blocks Safari/WDA URL open) |
| Android no devices | `adb devices` authorized; kill stale `adb` if offline |
| Install/uninstall smoke skipped | Set package/apk/ipa **and** `*_DESTRUCTIVE=1` |
| CI green but live red | Expected — CI is unit-only; use [regression checklist](docs/regression-checklist.md) |

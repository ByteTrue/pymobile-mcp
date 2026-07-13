# Changelog

## Unreleased

- Packaging: add root `LICENSE` (GPL-3.0), SPDX license field, PyPI badge; mark android-mvp roadmap completed

## 0.3.0 — 2026-07-13

- Packaging: published `0.3.0` to PyPI via Trusted Publisher (`.github/workflows/publish.yml`)

Black-box contract parity cut against pinned `mobile-mcp@c5d7d27`.

- Docs: rewrite README install/MCP client quickstart and troubleshooting
- CI: GitHub Actions unit tests on Python 3.11/3.12
- Android: `PYMOBILE_MCP_ANDROID_DROPBOX_ALL=1` to include non-crash dropbox tags
- Contract: exact pinned `mobile-mcp@c5d7d27` initialize, 23/default + 26/fleet tool discovery, natural-language/image results, validation and `isError` semantics
- iOS Simulator: native `simctl` discovery/app/system/recording with WDA UI; no go-ios/mobilecli runtime fallback
- Contract verification: deterministic upstream raw-wire/call goldens, 91-scenario matrix, exception scope guard, image backend PSNR artifacts
- Exceptions: remote-fleet success runtime and iOS real-device recording use user-approved exact Actionable responses

### Known approved exceptions
- Remote fleet success runtime without a Python fleet provider (documented Actionable response)
- iOS real-device screen recording unsupported under pure userspace RSD (documented Actionable response)

## 0.2.0 — 2026-07-11

First dual-platform usable cut of the 23 mobile-mcp core tools.

### Android
- Live UI: devices, screen size, screenshot, elements, tap/double/long/swipe/type
- App/system: list/launch/terminate/install/uninstall, buttons, open_url, orientation, save_screenshot
- Screen recording via `adb shell screenrecord`
- Crash list/get via `dumpsys dropbox --print`

### iOS (pure pymobiledevice3, no go-ios)
- Userspace RSD tunnel + WDA service client
- Live UI + system helpers (HOME/VOLUME_*, open_url when unlocked, save_screenshot)
- App lifecycle: list/launch/terminate; install/uninstall gated destructive
- Crash list/get via `CrashReportsManager`
- Screen recording: **unsupported** on iOS 26.5.2 userspace RSD (no `displayservice`; WDA `/wda/video` start works, stop finalize fails)

### Contract
- 23 core tools only; no public `mobile_get_page_source` / remote fleet
- Structured errors: `invalid_argument` / `not_implemented` / `unsupported_platform` / driver errors
- Live smoke scripts exit `blocked` (code 2) when no device — never fake pass

### Known limits
- Android dropbox defaults to crash/ANR/tombstone tags (strictmode/boot filtered)
- iOS recording deferred (see `.codestable/features/2026-07-11-ios-screen-recording-spike/`)
- Recording state is process-local

## 0.1.0

Initial package scaffold / early registry work.

# Changelog

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
- Android dropbox may include non-crash diagnostics tags
- iOS recording deferred (see `.codestable/features/2026-07-11-ios-screen-recording-spike/`)
- Recording state is process-local

## 0.1.0

Initial package scaffold / early registry work.

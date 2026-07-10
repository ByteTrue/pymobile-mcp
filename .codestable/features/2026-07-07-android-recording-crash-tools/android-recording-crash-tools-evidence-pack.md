# android-recording-crash-tools Evidence Pack

## Commands

1. `.venv/bin/python -m pytest` → 38 passed
2. `PATH=.venv/bin:$PATH python tests/android_recording_crash_live_smoke.py` → passed

## Notes

- recording uses adb `screenrecord` + pull to host path
- ActiveRecording is process-local with per-device asyncio.Lock
- crash tools intentionally unsupported on Android for this MVP

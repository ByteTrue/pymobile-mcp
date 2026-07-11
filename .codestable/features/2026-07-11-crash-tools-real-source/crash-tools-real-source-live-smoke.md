# crash-tools-real-source Live Smoke

```bash
PATH=.venv/bin:$PATH python tests/crash_tools_live_smoke.py
```

```json
{
  "status": "passed",
  "results": [
    {"device": "emulator-5554", "count": 38, "sample_id": "2026-07-10 01:17:03::system_server_strictmode"},
    {"device": "00008140-0008484C3AC2801C", "count": 52, "sample_id": "BackgroundShortcutRunner.diskwrites_resource-2026-06-28-002044.ips"}
  ]
}
```

## Sources

- Android: `adb shell dumpsys dropbox --print` (no root; includes strictmode/boot/crash tags when present)
- iOS: `pymobiledevice3.services.crash_reports.CrashReportsManager` over lockdown AFC (`com.apple.crashreportcopymobile`)

# ios-app-recording-crash-parity Live Smoke / Spike

## Capability spike (2026-07-11)

| Capability | PMD3/WDA pure-Python reliability | Decision |
|---|---|---|
| app list/launch/terminate/install/uninstall | no stable WDA/PMD3 path without go-ios/extra tooling | unsupported_platform |
| recording | no pure-PMD3 host MP4 capture equivalent to Android screenrecord | unsupported_platform |
| crash list/get | no reliable non-private crash report source via PMD3/WDA | unsupported_platform |

## Live command

```bash
PATH=.venv/bin:$PATH python tests/ios_app_recording_crash_live_smoke.py
```

Result on this host:

```json
{"status":"blocked","reason":"no authorized iOS device"}
```

Unit tests cover unsupported_platform envelopes with fake iOS driver/WDA.

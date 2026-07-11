# ios-system-helpers-parity Live Smoke

```bash
PATH=.venv/bin:$PATH python tests/ios_system_helpers_live_smoke.py
```

Result:

```json
{
  "status": "passed",
  "device": "00008140-0008484C3AC2801C",
  "save_size": 4717378,
  "open_url": "locked",
  "press_home": "ok"
}
```

Notes:
- `open_url` implementation is present; this host/device was passcode-locked for Safari launch, so smoke records `open_url=locked` with structured `driver_error` rather than fake success.
- Unlock the iPhone to exercise the full Safari URL path.

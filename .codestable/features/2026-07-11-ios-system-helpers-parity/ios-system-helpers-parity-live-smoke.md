# ios-system-helpers-parity Live Smoke

```bash
PATH=.venv/bin:$PATH python tests/ios_system_helpers_live_smoke.py
```

## Result (unlocked, 2026-07-11)

```json
{
  "status": "passed",
  "device": "00008140-0008484C3AC2801C",
  "save_size": 3183948,
  "open_url": "ok",
  "press_home": "ok"
}
```

Also re-verified core smoke:

```bash
PATH=.venv/bin:$PATH python tests/ios_pmd3_wda_live_smoke.py
# status=passed, element_count=244
```

Notes:
- Passcode lock previously returned structured `driver_error` for open_url; unlocked device opens Safari URL successfully.

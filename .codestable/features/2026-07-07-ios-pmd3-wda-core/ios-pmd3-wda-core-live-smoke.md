# ios-pmd3-wda-core Live Smoke / Spike

## Command

```bash
PATH=.venv/bin:$PATH python tests/ios_pmd3_wda_live_smoke.py
# optional interactions:
# PYMOBILE_MCP_IOS_ACTIONS=1 PATH=.venv/bin:$PATH python tests/ios_pmd3_wda_live_smoke.py
```

## Environment

- pymobiledevice3 usbmux list: empty on this host (2026-07-11)
- WebDriverAgent default probe: 127.0.0.1:8100 (not required once no device is present)
- Android emulator still present and does not count as iOS environment

## Result

```json
{
  "status": "blocked",
  "reason": "no authorized iOS device via pymobiledevice3 usbmux",
  "devices": [
    {
      "id": "emulator-5554",
      "platform": "android",
      "state": "online"
    }
  ],
  "wda": {"host": "127.0.0.1", "port": "8100"}
}
```

exit code: 2

## Implementation covered without live iOS

- unit: fake iOS driver through shared MCP tool handlers
- unit: `parse_wda_source` maps WDA JSON tree to ScreenElement coordinates
- discovery: `list_ios_devices()` uses pymobiledevice3 usbmux async list
- WDA client: pure HTTP stdlib client, no go-ios

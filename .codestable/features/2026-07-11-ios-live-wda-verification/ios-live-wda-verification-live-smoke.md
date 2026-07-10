# ios-live-wda-verification Live Smoke

## Device

- UDID: `00008140-0008484C3AC2801C`
- Name: C’s iPhone
- iOS: 26.5.2
- WDA runner: `com.byte.WebDriverAgentRunner.xctrunner`

## Transport

- pure `pymobiledevice3` `UserspaceRsdTunnel` (no root)
- `WdaServiceClient` over service connection (not localhost:8100)
- process-wide shared tunnel (PyTCP one-tunnel-per-process)

## Commands

```bash
PATH=.venv/bin:$PATH python tests/ios_pmd3_wda_live_smoke.py
PYMOBILE_MCP_IOS_ACTIONS=1 PATH=.venv/bin:$PATH python tests/ios_pmd3_wda_live_smoke.py
```

## Result (2026-07-11)

```json
{
  "status": "passed",
  "device": "00008140-0008484C3AC2801C",
  "screen_size": {"height": 874.0, "scale": 1.0, "width": 402.0},
  "element_count": 237
}
```

Both with and without `PYMOBILE_MCP_IOS_ACTIONS=1` passed.

# ios-app-lifecycle-pmd3 Live Smoke

```bash
PATH=.venv/bin:$PATH python tests/ios_app_lifecycle_live_smoke.py
```

```json
{
  "status": "passed",
  "device": "00008140-0008484C3AC2801C",
  "app_count": 49,
  "launched": "com.apple.Preferences",
  "destructive": {"status": "blocked"}
}
```

Install/uninstall require `PYMOBILE_MCP_IOS_IPA` + `PYMOBILE_MCP_IOS_DESTRUCTIVE=1` + `PYMOBILE_MCP_IOS_PACKAGE`.

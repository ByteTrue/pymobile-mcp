"""iOS app/recording/crash parity smoke (updated)."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any


def _payload(content: Any) -> dict[str, Any]:
    return json.loads(content[0].text)


def _error_payload(content: Any) -> dict[str, Any] | None:
    if content[0].type != "text":
        return None
    payload = json.loads(content[0].text)
    return payload if payload.get("status") == "error" else None


async def main() -> int:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    for k in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "all_proxy"]:
        env.pop(k, None)
    env["NO_PROXY"] = "*"
    env["no_proxy"] = "*"
    params = StdioServerParameters(command=sys.executable, args=["-m", "pymobile_mcp.cli", "run"], cwd=str(Path.cwd()), env=env)
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            devices_payload = _payload((await session.call_tool("mobile_list_available_devices", {})).content)
            devices = [d for d in devices_payload.get("devices", []) if d.get("platform") == "ios" and d.get("state") == "online"]
            wanted = os.environ.get("PYMOBILE_MCP_IOS_DEVICE")
            device = next((item for item in devices if not wanted or item["id"] == wanted), None)
            if device is None:
                print(json.dumps({"status": "blocked", "reason": "no authorized iOS device", "devices": devices_payload.get("devices", [])}, indent=2))
                return 2
            device_id = device["id"]
            apps = _payload((await session.call_tool("mobile_list_apps", {"device": device_id})).content)
            if not apps.get("apps"):
                print(json.dumps({"status": "failed", "reason": "list_apps empty"}, indent=2))
                return 1
            rec = await session.call_tool("mobile_start_screen_recording", {"device": device_id, "output": "tmp-ios.mp4"})
            rec_err = _error_payload(rec.content)
            if rec_err is None or rec_err.get("code") != "unsupported_platform":
                print(json.dumps({"status": "failed", "tool": "mobile_start_screen_recording", "payload": rec_err or _payload(rec.content)}, indent=2))
                return 1
            crashes = _payload((await session.call_tool("mobile_list_crashes", {"device": device_id})).content)
            crash_list = crashes.get("crashes") or []
            sample = None
            if crash_list:
                sample = crash_list[0]["id"]
                body = _payload((await session.call_tool("mobile_get_crash", {"device": device_id, "id": sample})).content)
                if not body.get("content"):
                    print(json.dumps({"status": "failed", "reason": "empty crash"}, indent=2))
                    return 1
            print(json.dumps({"status": "passed", "device": device_id, "app_count": len(apps["apps"]), "recording": "unsupported_platform", "crash_count": len(crash_list), "sample_id": sample}, indent=2))
            return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

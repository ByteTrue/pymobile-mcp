"""iOS app/recording/crash parity smoke.

Without a paired iOS device this exits 2 blocked-by-env.
With an iOS device present, verifies app/recording/crash tools return
stable unsupported_platform (not fake empty success).
"""

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

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "pymobile_mcp.cli", "run"],
        cwd=str(Path.cwd()),
        env={"PYTHONPATH": "src"},
    )
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
            results = {}
            checks = [
                ("mobile_list_apps", {"device": device_id}),
                ("mobile_launch_app", {"device": device_id, "packageName": "com.example.app"}),
                ("mobile_start_screen_recording", {"device": device_id, "output": "tmp-ios.mp4"}),
                ("mobile_list_crashes", {"device": device_id}),
                ("mobile_get_crash", {"device": device_id, "id": "demo"}),
            ]
            for tool, args in checks:
                payload = _error_payload((await session.call_tool(tool, args)).content)
                if payload is None or payload.get("code") != "unsupported_platform":
                    print(json.dumps({"status": "failed", "tool": tool, "payload": payload}, indent=2))
                    return 1
                results[tool] = "unsupported_platform"

            print(json.dumps({"status": "passed", "device": device_id, "results": results}, indent=2))
            return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

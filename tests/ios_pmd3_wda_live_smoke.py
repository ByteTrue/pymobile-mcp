"""iOS PMD3/WDA core live smoke.

Requires:
- a paired iOS device visible to pymobiledevice3 usbmux, and
- WebDriverAgent reachable at PYMOBILE_MCP_WDA_HOST:PYMOBILE_MCP_WDA_PORT (default 127.0.0.1:8100)

Without that environment this script exits 2 with status=blocked.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any


from ios_live_smoke_support import elements, error_text, json_object, run_with_timeout, screen_size


def _failed(reason: str, **extra: Any) -> int:
    print(json.dumps({"status": "failed", "reason": reason, **extra}, indent=2))
    return 1


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
            devices_result = await session.call_tool("mobile_list_available_devices", {})
            devices_error = error_text(devices_result.content)
            if devices_error is not None:
                return _failed("device discovery failed", error=devices_error)
            devices_payload = json_object(devices_result.content)
            devices = [
                device
                for device in devices_payload.get("devices", [])
                if device.get("platform") == "ios" and device.get("state") == "online"
            ]
            wanted = os.environ.get("PYMOBILE_MCP_IOS_DEVICE")
            device = next((item for item in devices if not wanted or item["id"] == wanted), None)
            if device is None:
                print(
                    json.dumps(
                        {
                            "status": "blocked",
                            "reason": "no authorized iOS device via pymobiledevice3 usbmux",
                            "devices": devices_payload.get("devices", []),
                            "wda": {
                                "host": os.environ.get("PYMOBILE_MCP_WDA_HOST", "127.0.0.1"),
                                "port": os.environ.get("PYMOBILE_MCP_WDA_PORT", "8100"),
                            },
                        },
                        indent=2,
                    )
                )
                return 2

            device_id = device["id"]
            size = await session.call_tool("mobile_get_screen_size", {"device": device_id})
            size_error = error_text(size.content)
            if size_error is not None:
                return _failed("screen size failed", error=size_error)
            size_payload = screen_size(size.content)
            if size_payload["width"] <= 0 or size_payload["height"] <= 0:
                return _failed("invalid screen size", size=size_payload)

            shot = await session.call_tool("mobile_take_screenshot", {"device": device_id})
            if shot.content[0].type != "image":
                return _failed("screenshot not image")

            element_result = await session.call_tool("mobile_list_elements_on_screen", {"device": device_id})
            element_error = error_text(element_result.content)
            if element_error is not None:
                return _failed("elements failed", error=element_error)
            items = elements(element_result.content)
            if not all("coordinates" in item for item in items):
                return _failed("element missing coordinates", sample=items[:1])

            if os.environ.get("PYMOBILE_MCP_IOS_ACTIONS") == "1" and items:
                rect = items[0]["coordinates"]
                x = rect["x"] + rect["width"] / 2
                y = rect["y"] + rect["height"] / 2
                tap = await session.call_tool(
                    "mobile_click_on_screen_at_coordinates",
                    {"device": device_id, "x": x, "y": y},
                )
                tap_error = error_text(tap.content)
                if tap_error is not None:
                    return _failed("tap failed", error=tap_error)

            print(
                json.dumps(
                    {
                        "status": "passed",
                        "device": device_id,
                        "screen_size": size_payload,
                        "element_count": len(items),
                    },
                    indent=2,
                )
            )
            return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_with_timeout(main)))

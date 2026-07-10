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


def _payload(content: Any) -> dict[str, Any]:
    return json.loads(content[0].text)


def _error_payload(content: Any) -> dict[str, Any] | None:
    if content[0].type != "text":
        return None
    payload = json.loads(content[0].text)
    return payload if payload.get("status") == "error" else None


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
            devices_payload = _payload((await session.call_tool("mobile_list_available_devices", {})).content)
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
            if _error_payload(size.content) is not None:
                return _failed("screen size failed", error=_payload(size.content))
            size_payload = _payload(size.content)
            if size_payload.get("width", 0) <= 0:
                return _failed("invalid screen size", size=size_payload)

            shot = await session.call_tool("mobile_take_screenshot", {"device": device_id})
            if shot.content[0].type != "image":
                return _failed("screenshot not image")

            elements = await session.call_tool("mobile_list_elements_on_screen", {"device": device_id})
            if _error_payload(elements.content) is not None:
                return _failed("elements failed", error=_payload(elements.content))
            element_payload = _payload(elements.content)
            items = element_payload.get("elements", [])
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
                if _error_payload(tap.content) is not None:
                    return _failed("tap failed", error=_payload(tap.content))

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
    raise SystemExit(asyncio.run(main()))

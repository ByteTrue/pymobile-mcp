"""Live Android MCP smoke. Requires an authorized Android device.

Set PYMOBILE_MCP_ANDROID_DEVICE to choose a device. Destructive interaction
steps require PYMOBILE_MCP_ANDROID_ACTIONS=1. Override the tap point with
PYMOBILE_MCP_ANDROID_TAP=x,y when needed.
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


def _tap_point(elements: list[dict[str, Any]], size: dict[str, Any]) -> tuple[float, float]:
    explicit = os.environ.get("PYMOBILE_MCP_ANDROID_TAP")
    if explicit:
        x_text, y_text = explicit.split(",", 1)
        return float(x_text), float(y_text)

    for element in elements:
        label = " ".join(str(element.get(key) or "") for key in ("type", "text", "label", "name", "identifier"))
        if "EditText" in label or "Search" in label:
            rect = element["coordinates"]
            return rect["x"] + rect["width"] / 2, rect["y"] + rect["height"] / 2
    return size["width"] / 2, size["height"] * 0.92


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
            tools = await session.list_tools()
            names = [tool.name for tool in tools.tools]
            if "mobile_get_page_source" in names:
                print(json.dumps({"status": "failed", "reason": "mobile_get_page_source is public"}, indent=2))
                return 1

            devices_payload = _payload((await session.call_tool("mobile_list_available_devices", {})).content)
            devices = [device for device in devices_payload.get("devices", []) if device.get("platform") == "android" and device.get("state") == "online"]
            wanted = os.environ.get("PYMOBILE_MCP_ANDROID_DEVICE")
            device = next((item for item in devices if not wanted or item["id"] == wanted), None)
            if device is None:
                print(json.dumps({"status": "blocked", "reason": "no authorized Android device", "devices": devices}, indent=2))
                return 2

            device_id = device["id"]
            size = _payload((await session.call_tool("mobile_get_screen_size", {"device": device_id})).content)
            if size["width"] <= 0 or size["height"] <= 0:
                print(json.dumps({"status": "failed", "reason": "invalid screen size", "size": size}, indent=2))
                return 1

            screenshot = await session.call_tool("mobile_take_screenshot", {"device": device_id})
            if screenshot.content[0].type != "image" or screenshot.content[0].mimeType != "image/png":
                print(json.dumps({"status": "failed", "reason": "invalid screenshot content"}, indent=2))
                return 1

            elements_payload = _payload((await session.call_tool("mobile_list_elements_on_screen", {"device": device_id})).content)
            elements = elements_payload.get("elements", [])
            if not all("coordinates" in element for element in elements):
                print(json.dumps({"status": "failed", "reason": "element missing coordinates", "elements": elements[:3]}, indent=2))
                return 1

            if os.environ.get("PYMOBILE_MCP_ANDROID_ACTIONS") != "1":
                print(
                    json.dumps(
                        {
                            "status": "blocked",
                            "reason": "interaction steps require PYMOBILE_MCP_ANDROID_ACTIONS=1",
                            "device": device_id,
                            "screen_size": size,
                            "element_count": len(elements),
                        },
                        indent=2,
                    )
                )
                return 2

            x, y = _tap_point(elements, size)
            text = os.environ.get("PYMOBILE_MCP_ANDROID_TEXT", "pymobile")
            action_calls = [
                ("mobile_click_on_screen_at_coordinates", {"device": device_id, "x": x, "y": y}),
                ("mobile_double_tap_on_screen", {"device": device_id, "x": x, "y": y}),
                ("mobile_long_press_on_screen_at_coordinates", {"device": device_id, "x": x, "y": y, "duration": 500}),
                ("mobile_swipe_on_screen", {"device": device_id, "direction": "up"}),
                ("mobile_type_keys", {"device": device_id, "text": text, "submit": True}),
            ]
            for tool, arguments in action_calls:
                result = await session.call_tool(tool, arguments)
                error = _error_payload(result.content)
                if error is not None:
                    return _failed("action returned structured error", tool=tool, error=error)
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "device": device_id,
                        "screen_size": size,
                        "element_count": len(elements),
                        "tap": {"x": x, "y": y},
                    },
                    indent=2,
                )
            )
            return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

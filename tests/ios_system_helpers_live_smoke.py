"""iOS system helpers live smoke: press_button / open_url / save_screenshot."""

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

    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    for k in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "all_proxy"]:
        env.pop(k, None)
    env["NO_PROXY"] = "*"
    env["no_proxy"] = "*"

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "pymobile_mcp.cli", "run"],
        cwd=str(Path.cwd()),
        env=env,
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
            open_url = await session.call_tool("mobile_open_url", {"device": device_id, "url": "https://example.com"})
            open_err = _error_payload(open_url.content)
            open_status = "ok"
            if open_err is not None:
                # Locked device is an environment condition; still prove the tool path and message.
                if open_err.get("code") == "driver_error" and "locked" in str(open_err.get("message", "")).lower():
                    open_status = "locked"
                else:
                    return _failed("open_url failed", error=open_err)

            press = await session.call_tool("mobile_press_button", {"device": device_id, "button": "HOME"})
            if _error_payload(press.content) is not None:
                return _failed("press_button HOME failed", error=_payload(press.content))

            save_to = Path("tmp-ios-system-helper.png")
            saved = await session.call_tool("mobile_save_screenshot", {"device": device_id, "saveTo": str(save_to)})
            saved_payload = _payload(saved.content)
            if _error_payload(saved.content) is not None:
                return _failed("save_screenshot failed", error=saved_payload)
            path = Path(saved_payload["saveTo"])
            if not path.exists() or path.stat().st_size <= 0:
                return _failed("saved file missing", saveTo=str(path))

            # Android-only button should stay unsupported on iOS
            back = await session.call_tool("mobile_press_button", {"device": device_id, "button": "BACK"})
            back_payload = _error_payload(back.content)
            if back_payload is None or back_payload.get("code") != "unsupported_platform":
                return _failed("expected unsupported BACK on iOS", result=_payload(back.content))

            size = path.stat().st_size
            path.unlink(missing_ok=True)
            print(json.dumps({"status": "passed", "device": device_id, "save_size": size, "open_url": open_status, "press_home": "ok"}, indent=2))
            return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

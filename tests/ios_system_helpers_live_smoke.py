"""iOS system helpers live smoke: press_button / open_url / save_screenshot."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any


from ios_live_smoke_support import error_text, is_locked, is_unsupported, json_object, run_with_timeout, saved_path


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
            devices_result = await session.call_tool("mobile_list_available_devices", {})
            devices_error = error_text(devices_result.content)
            if devices_error is not None:
                return _failed("device discovery failed", error=devices_error)
            devices_payload = json_object(devices_result.content)
            devices = [d for d in devices_payload.get("devices", []) if d.get("platform") == "ios" and d.get("state") == "online"]
            wanted = os.environ.get("PYMOBILE_MCP_IOS_DEVICE")
            device = next((item for item in devices if not wanted or item["id"] == wanted), None)
            if device is None:
                print(json.dumps({"status": "blocked", "reason": "no authorized iOS device", "devices": devices_payload.get("devices", [])}, indent=2))
                return 2

            device_id = device["id"]
            open_url = await session.call_tool("mobile_open_url", {"device": device_id, "url": "https://example.com"})
            open_error = error_text(open_url.content)
            open_status = "ok"
            if open_error is not None:
                if is_locked(open_error):
                    open_status = "locked"
                else:
                    return _failed("open_url failed", error=open_error)

            press = await session.call_tool("mobile_press_button", {"device": device_id, "button": "HOME"})
            press_error = error_text(press.content)
            if press_error is not None:
                return _failed("press_button HOME failed", error=press_error)

            save_to = Path("tmp-ios-system-helper.png")
            saved = await session.call_tool("mobile_save_screenshot", {"device": device_id, "saveTo": str(save_to)})
            saved_error = error_text(saved.content)
            if saved_error is not None:
                return _failed("save_screenshot failed", error=saved_error)
            path = saved_path(saved.content)
            if not path.exists() or path.stat().st_size <= 0:
                return _failed("saved file missing", saveTo=str(path))

            # Android-only button should stay unsupported on iOS
            back = await session.call_tool("mobile_press_button", {"device": device_id, "button": "BACK"})
            back_error = error_text(back.content)
            if not is_unsupported(back_error):
                return _failed("expected unsupported BACK on iOS", result=back.content[0].text)

            size = path.stat().st_size
            path.unlink(missing_ok=True)
            print(json.dumps({"status": "passed", "device": device_id, "save_size": size, "open_url": open_status, "press_home": "ok"}, indent=2))
            return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_with_timeout(main)))

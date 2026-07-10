"""Live Android recording/crash MCP smoke.

Requires an authorized Android device.

Runs:
- start_screen_recording for a few seconds
- stop_screen_recording and verify MP4 exists
- list_crashes / get_crash return unsupported_platform
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
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
    output = Path("tmp-android-recording-smoke.mp4")
    if output.exists():
        output.unlink()

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            devices_payload = _payload((await session.call_tool("mobile_list_available_devices", {})).content)
            devices = [
                device
                for device in devices_payload.get("devices", [])
                if device.get("platform") == "android" and device.get("state") == "online"
            ]
            wanted = os.environ.get("PYMOBILE_MCP_ANDROID_DEVICE")
            device = next((item for item in devices if not wanted or item["id"] == wanted), None)
            if device is None:
                print(json.dumps({"status": "blocked", "reason": "no authorized Android device", "devices": devices}, indent=2))
                return 2

            device_id = device["id"]
            started = await session.call_tool(
                "mobile_start_screen_recording",
                {"device": device_id, "output": str(output), "timeLimit": 5},
            )
            if _error_payload(started.content) is not None:
                return _failed("start recording failed", error=_payload(started.content))
            time.sleep(2)
            stopped = await session.call_tool("mobile_stop_screen_recording", {"device": device_id})
            stopped_payload = _payload(stopped.content)
            if _error_payload(stopped.content) is not None:
                return _failed("stop recording failed", error=stopped_payload)
            path = Path(stopped_payload["output"])
            if not path.exists() or path.stat().st_size <= 0:
                return _failed("recording file missing", output=str(path))

            no_active = await session.call_tool("mobile_stop_screen_recording", {"device": device_id})
            no_active_payload = _error_payload(no_active.content)
            if no_active_payload is None or no_active_payload.get("code") != "no_active_recording":
                return _failed("expected no_active_recording", result=_payload(no_active.content))

            crashes = await session.call_tool("mobile_list_crashes", {"device": device_id})
            crash_payload = _error_payload(crashes.content)
            if crash_payload is None or crash_payload.get("code") != "unsupported_platform":
                return _failed("expected unsupported_platform for list_crashes", result=_payload(crashes.content))

            get_crash = await session.call_tool("mobile_get_crash", {"device": device_id, "id": "demo"})
            get_payload = _error_payload(get_crash.content)
            if get_payload is None or get_payload.get("code") != "unsupported_platform":
                return _failed("expected unsupported_platform for get_crash", result=_payload(get_crash.content))

            size = path.stat().st_size
            path.unlink(missing_ok=True)
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "device": device_id,
                        "recording_size": size,
                        "crash": "unsupported_platform",
                    },
                    indent=2,
                )
            )
            return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

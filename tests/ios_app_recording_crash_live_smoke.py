"""iOS app/recording/crash parity smoke (updated)."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from ios_live_smoke_support import apps, error_text, is_unsupported, json_array, json_object, run_with_timeout, text


async def _exercise_recording(session, device, output: Path, *, sleep=asyncio.sleep) -> dict[str, int | str | None]:
    device_id = device["id"]
    simulator = device.get("type") == "simulator"
    if simulator:
        output.unlink(missing_ok=True)

    started = await session.call_tool(
        "mobile_start_screen_recording",
        {"device": device_id, "output": str(output)},
    )
    start_error = error_text(started.content)
    if not simulator:
        if not is_unsupported(start_error):
            raise RuntimeError(
                f"real iOS recording did not return approved unsupported result: {text(started.content)}"
            )
        return {"status": "unsupported_platform", "size": None}

    if start_error is not None:
        raise RuntimeError(f"simulator recording start failed: {start_error}")
    await sleep(2)
    stopped = await session.call_tool(
        "mobile_stop_screen_recording", {"device": device_id}
    )
    stop_error = error_text(stopped.content)
    if stop_error is not None:
        raise RuntimeError(f"simulator recording stop failed: {stop_error}")
    if not output.is_file() or output.stat().st_size <= 0:
        raise RuntimeError(f"simulator recording file missing or empty: {output}")
    return {"status": "simctl", "size": output.stat().st_size}


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
            devices_result = await session.call_tool("mobile_list_available_devices", {})
            devices_error = error_text(devices_result.content)
            if devices_error is not None:
                print(json.dumps({"status": "failed", "reason": "device discovery failed", "error": devices_error}, indent=2))
                return 1
            devices_payload = json_object(devices_result.content)
            devices = [d for d in devices_payload.get("devices", []) if d.get("platform") == "ios" and d.get("state") == "online"]
            wanted = os.environ.get("PYMOBILE_MCP_IOS_DEVICE")
            device = next((item for item in devices if not wanted or item["id"] == wanted), None)
            if device is None:
                print(json.dumps({"status": "blocked", "reason": "no authorized iOS device", "devices": devices_payload.get("devices", [])}, indent=2))
                return 2
            device_id = device["id"]
            apps_result = await session.call_tool("mobile_list_apps", {"device": device_id})
            apps_error = error_text(apps_result.content)
            if apps_error is not None:
                print(json.dumps({"status": "failed", "reason": "list_apps failed", "error": apps_error}, indent=2))
                return 1
            app_list = apps(apps_result.content)
            if not app_list:
                print(json.dumps({"status": "failed", "reason": "list_apps empty"}, indent=2))
                return 1
            output = Path("tmp-ios.mp4")
            try:
                recording = await _exercise_recording(session, device, output)
            except RuntimeError as exc:
                print(json.dumps({"status": "failed", "reason": str(exc)}, indent=2))
                return 1
            if device.get("type") == "simulator":
                output.unlink(missing_ok=True)
            crashes_result = await session.call_tool("mobile_list_crashes", {"device": device_id})
            crashes_error = error_text(crashes_result.content)
            if crashes_error is not None:
                print(json.dumps({"status": "failed", "reason": "list_crashes failed", "error": crashes_error}, indent=2))
                return 1
            crash_list = json_array(crashes_result.content)
            sample = None
            if crash_list:
                sample = crash_list[0]["id"]
                crash_result = await session.call_tool("mobile_get_crash", {"device": device_id, "id": sample})
                crash_error = error_text(crash_result.content)
                if crash_error is not None:
                    print(json.dumps({"status": "failed", "reason": "get_crash failed", "error": crash_error}, indent=2))
                    return 1
                body = text(crash_result.content)
                if not body:
                    print(json.dumps({"status": "failed", "reason": "empty crash"}, indent=2))
                    return 1
            print(json.dumps({"status": "passed", "device": device_id, "device_type": device.get("type"), "app_count": len(app_list), "recording": recording["status"], "recording_size": recording["size"], "crash_count": len(crash_list), "sample_id": sample}, indent=2))
            return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_with_timeout(main)))

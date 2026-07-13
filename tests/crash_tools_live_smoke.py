"""Cross-platform crash tools live smoke."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
import json
import os
import sys
from pathlib import Path
from typing import Any

from ios_live_smoke_support import run_with_timeout


def _payload(content: Any) -> Any:
    return json.loads(content[0].text)


def _error_payload(content: Any) -> dict[str, Any] | None:
    if content[0].type != "text":
        return None
    text = content[0].text
    if text.startswith(("Error:", "MCP error")) or text.endswith(
        "Please fix the issue and try again."
    ):
        return {"message": text}
    return None


def _failed(reason: str, **extra: Any) -> int:
    print(json.dumps({"status": "failed", "reason": reason, **extra}, indent=2))
    return 1


def _selected_devices(
    payload: Mapping[str, Any], environ: Mapping[str, str]
) -> list[dict[str, Any]]:
    devices = [
        device
        for device in payload.get("devices", [])
        if device.get("state") == "online"
    ]
    if "PYMOBILE_MCP_DEVICE" in environ:
        wanted = environ["PYMOBILE_MCP_DEVICE"]
        return [device for device in devices if device.get("id") == wanted]

    selectors = {
        platform: environ[name]
        for platform, name in (
            ("android", "PYMOBILE_MCP_ANDROID_DEVICE"),
            ("ios", "PYMOBILE_MCP_IOS_DEVICE"),
        )
        if name in environ
    }
    if selectors:
        return [
            device
            for device in devices
            if device.get("platform") in selectors
            and device.get("id") == selectors[device["platform"]]
        ]
    return devices


async def _check_device(session, device_id: str) -> dict[str, Any]:
    listed = await session.call_tool("mobile_list_crashes", {"device": device_id})
    err = _error_payload(listed.content)
    if err is not None:
        return {"device": device_id, "status": "failed", "error": err}
    crashes = _payload(listed.content) or []
    # Empty list is allowed if truly no reports; still prove list works.
    result: dict[str, Any] = {
        "device": device_id,
        "status": "passed",
        "count": len(crashes),
    }
    if crashes:
        crash_id = crashes[0].get("id")
        got = await session.call_tool(
            "mobile_get_crash", {"device": device_id, "id": crash_id}
        )
        gerr = _error_payload(got.content)
        if gerr is not None:
            return {"device": device_id, "status": "failed", "error": gerr}
        body = got.content[0].text
        if not body:
            return {
                "device": device_id,
                "status": "failed",
                "reason": "empty crash content",
                "id": crash_id,
            }
        result["sample_id"] = crash_id
        result["content_len"] = len(body)
    return result


async def main() -> int:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    for k in [
        "http_proxy",
        "https_proxy",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "all_proxy",
    ]:
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
            devices_payload = _payload(
                (await session.call_tool("mobile_list_available_devices", {})).content
            )
            devices = _selected_devices(devices_payload, os.environ)
            if not devices:
                print(
                    json.dumps(
                        {"status": "blocked", "reason": "no selected online devices"},
                        indent=2,
                    )
                )
                return 2
            results = []
            for device in devices:
                results.append(await _check_device(session, device["id"]))
            failed = [r for r in results if r.get("status") != "passed"]
            print(
                json.dumps(
                    {"status": "failed" if failed else "passed", "results": results},
                    indent=2,
                )
            )
            return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_with_timeout(main, name="crash tools live smoke")))

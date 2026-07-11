"""Cross-platform crash tools live smoke."""

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


async def _check_device(session, device_id: str) -> dict[str, Any]:
    listed = await session.call_tool("mobile_list_crashes", {"device": device_id})
    err = _error_payload(listed.content)
    if err is not None:
        return {"device": device_id, "status": "failed", "error": err}
    payload = _payload(listed.content)
    crashes = payload.get("crashes") or []
    # Empty list is allowed if truly no reports; still prove list works.
    result: dict[str, Any] = {"device": device_id, "status": "passed", "count": len(crashes)}
    if crashes:
        crash_id = crashes[0].get("id")
        got = await session.call_tool("mobile_get_crash", {"device": device_id, "id": crash_id})
        gerr = _error_payload(got.content)
        if gerr is not None:
            return {"device": device_id, "status": "failed", "error": gerr}
        body = _payload(got.content)
        if not body.get("content"):
            return {"device": device_id, "status": "failed", "reason": "empty crash content", "id": crash_id}
        result["sample_id"] = crash_id
        result["content_len"] = len(body["content"])
    return result


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
            devices = [d for d in devices_payload.get("devices", []) if d.get("state") == "online"]
            if not devices:
                print(json.dumps({"status": "blocked", "reason": "no online devices"}, indent=2))
                return 2
            results = []
            for device in devices:
                results.append(await _check_device(session, device["id"]))
            failed = [r for r in results if r.get("status") != "passed"]
            print(json.dumps({"status": "failed" if failed else "passed", "results": results}, indent=2))
            return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

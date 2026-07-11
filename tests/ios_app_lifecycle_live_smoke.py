"""iOS app lifecycle live smoke via pure pymobiledevice3/WDA.

Safe by default: list_apps, launch Preferences, terminate Preferences.
Install/uninstall remain blocked unless PYMOBILE_MCP_IOS_IPA + DESTRUCTIVE=1.
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
            devices = [d for d in devices_payload.get("devices", []) if d.get("platform") == "ios" and d.get("state") == "online"]
            wanted = os.environ.get("PYMOBILE_MCP_IOS_DEVICE")
            device = next((item for item in devices if not wanted or item["id"] == wanted), None)
            if device is None:
                print(json.dumps({"status": "blocked", "reason": "no authorized iOS device", "devices": devices_payload.get("devices", [])}, indent=2))
                return 2

            device_id = device["id"]
            apps = _payload((await session.call_tool("mobile_list_apps", {"device": device_id})).content)
            app_list = apps.get("apps") or []
            if not app_list:
                return _failed("list_apps empty", apps=apps)

            package = "com.apple.Preferences"
            launch = await session.call_tool("mobile_launch_app", {"device": device_id, "packageName": package})
            if _error_payload(launch.content) is not None:
                return _failed("launch failed", error=_payload(launch.content))
            terminate = await session.call_tool("mobile_terminate_app", {"device": device_id, "packageName": package})
            if _error_payload(terminate.content) is not None:
                return _failed("terminate failed", error=_payload(terminate.content))

            destructive = {
                "status": "blocked",
                "reason": "install/uninstall require PYMOBILE_MCP_IOS_IPA and PYMOBILE_MCP_ANDROID_DESTRUCTIVE=1 or PYMOBILE_MCP_IOS_DESTRUCTIVE=1",
            }
            ipa = os.environ.get("PYMOBILE_MCP_IOS_IPA")
            if ipa and os.environ.get("PYMOBILE_MCP_IOS_DESTRUCTIVE") == "1":
                install = await session.call_tool("mobile_install_app", {"device": device_id, "path": ipa})
                if _error_payload(install.content) is not None:
                    return _failed("install failed", error=_payload(install.content))
                bundle = os.environ.get("PYMOBILE_MCP_IOS_PACKAGE")
                if not bundle:
                    return _failed("install ran but PYMOBILE_MCP_IOS_PACKAGE missing")
                uninstall = await session.call_tool("mobile_uninstall_app", {"device": device_id, "bundle_id": bundle})
                if _error_payload(uninstall.content) is not None:
                    return _failed("uninstall failed", error=_payload(uninstall.content))
                destructive = {"status": "passed", "ipa": ipa, "package": bundle}

            print(
                json.dumps(
                    {
                        "status": "passed",
                        "device": device_id,
                        "app_count": len(app_list),
                        "launched": package,
                        "destructive": destructive,
                    },
                    indent=2,
                )
            )
            return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

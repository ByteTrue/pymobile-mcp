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


from ios_live_smoke_support import apps, error_text, json_object, run_with_timeout


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
            apps_result = await session.call_tool("mobile_list_apps", {"device": device_id})
            apps_error = error_text(apps_result.content)
            if apps_error is not None:
                return _failed("list_apps failed", error=apps_error)
            app_list = apps(apps_result.content)
            if not app_list:
                return _failed("list_apps empty")

            package = "com.apple.Preferences"
            launch = await session.call_tool("mobile_launch_app", {"device": device_id, "packageName": package})
            launch_error = error_text(launch.content)
            if launch_error is not None:
                return _failed("launch failed", error=launch_error)
            terminate = await session.call_tool("mobile_terminate_app", {"device": device_id, "packageName": package})
            terminate_error = error_text(terminate.content)
            if terminate_error is not None:
                return _failed("terminate failed", error=terminate_error)

            destructive = {
                "status": "blocked",
                "reason": "install/uninstall require PYMOBILE_MCP_IOS_IPA and PYMOBILE_MCP_IOS_DESTRUCTIVE=1",
            }
            ipa = os.environ.get("PYMOBILE_MCP_IOS_IPA")
            if ipa and os.environ.get("PYMOBILE_MCP_IOS_DESTRUCTIVE") == "1":
                install = await session.call_tool("mobile_install_app", {"device": device_id, "path": ipa})
                install_error = error_text(install.content)
                if install_error is not None:
                    return _failed("install failed", error=install_error)
                bundle = os.environ.get("PYMOBILE_MCP_IOS_PACKAGE")
                if not bundle:
                    return _failed("install ran but PYMOBILE_MCP_IOS_PACKAGE missing")
                uninstall = await session.call_tool("mobile_uninstall_app", {"device": device_id, "bundle_id": bundle})
                uninstall_error = error_text(uninstall.content)
                if uninstall_error is not None:
                    return _failed("uninstall failed", error=uninstall_error)
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
    raise SystemExit(asyncio.run(run_with_timeout(main)))

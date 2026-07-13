"""Live Android app/system MCP smoke.

Requires an authorized Android device.

Safe by default:
- list_apps
- open_url(https)
- press_button(HOME)
- get/set orientation
- save_screenshot to a cwd-relative path

Destructive install/uninstall are blocked unless PYMOBILE_MCP_ANDROID_APK is set
and PYMOBILE_MCP_ANDROID_DESTRUCTIVE=1.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


def _payload(content: Any) -> dict[str, Any]:
    return json.loads(content[0].text)


def _error_payload(content: Any) -> dict[str, Any] | None:
    if content[0].type != "text":
        return None
    text = content[0].text
    if text.startswith(("Error:", "MCP error")) or text.endswith("Please fix the issue and try again."):
        return {"message": text}
    return None


def _apps(content: Any) -> list[dict[str, str]]:
    prefix = "Found these apps on device: "
    return [{"appName": name, "packageName": package} for name, package in re.findall(r"([^,]+) \(([^)]+)\)", content[0].text.removeprefix(prefix))]


def _orientation(content: Any) -> str:
    return content[0].text.removeprefix("Current device orientation is ")


def _saved_path(content: Any) -> Path:
    return Path(content[0].text.removeprefix("Screenshot saved to: "))

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
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            required = {
                "mobile_list_apps",
                "mobile_open_url",
                "mobile_press_button",
                "mobile_get_orientation",
                "mobile_set_orientation",
                "mobile_save_screenshot",
            }
            if not required.issubset(names):
                return _failed("missing app/system tools", missing=sorted(required - names))

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
            apps = _apps((await session.call_tool("mobile_list_apps", {"device": device_id})).content)
            if not apps:
                return _failed("list_apps returned empty", apps=apps)

            for tool, arguments in [
                ("mobile_open_url", {"device": device_id, "url": "https://example.com"}),
                ("mobile_press_button", {"device": device_id, "button": "HOME"}),
                ("mobile_set_orientation", {"device": device_id, "orientation": "portrait"}),
            ]:
                result = await session.call_tool(tool, arguments)
                error = _error_payload(result.content)
                if error is not None:
                    return _failed("action returned structured error", tool=tool, error=error)

            # invalid url must stay rejected without env override
            invalid = await session.call_tool("mobile_open_url", {"device": device_id, "url": "myapp://home"})
            invalid_payload = _error_payload(invalid.content)
            if invalid_payload is None:
                return _failed("custom scheme was not rejected", result=invalid.content[0].text)

            orientation = _orientation((await session.call_tool("mobile_get_orientation", {"device": device_id})).content)
            if orientation not in {"portrait", "landscape"}:
                return _failed("invalid orientation", orientation=orientation)

            save_to = Path("tmp-android-app-system-smoke.png")
            saved = await session.call_tool("mobile_save_screenshot", {"device": device_id, "saveTo": str(save_to)})
            if _error_payload(saved.content) is not None:
                return _failed("save_screenshot failed", error=saved.content[0].text)
            path = _saved_path(saved.content)
            if not path.exists() or path.stat().st_size <= 0:
                return _failed("saved screenshot missing", saveTo=str(path))

            unsafe = await session.call_tool("mobile_save_screenshot", {"device": device_id, "saveTo": "/etc/passwd.png"})
            if _error_payload(unsafe.content) is None:
                return _failed("unsafe saveTo was accepted")

            package = apps[0]["packageName"]
            for tool, arguments in [
                ("mobile_launch_app", {"device": device_id, "packageName": package}),
                ("mobile_terminate_app", {"device": device_id, "packageName": package}),
            ]:
                result = await session.call_tool(tool, arguments)
                error = _error_payload(result.content)
                if error is not None:
                    return _failed("app lifecycle action failed", tool=tool, error=error)

            destructive = {
                "status": "blocked",
                "reason": "install/uninstall require PYMOBILE_MCP_ANDROID_APK and PYMOBILE_MCP_ANDROID_DESTRUCTIVE=1",
            }
            apk = os.environ.get("PYMOBILE_MCP_ANDROID_APK")
            if apk and os.environ.get("PYMOBILE_MCP_ANDROID_DESTRUCTIVE") == "1":
                install = await session.call_tool("mobile_install_app", {"device": device_id, "path": apk})
                if _error_payload(install.content) is not None:
                    return _failed("install failed", error=_payload(install.content))
                # package name for uninstall is intentionally left to the caller via env
                bundle = os.environ.get("PYMOBILE_MCP_ANDROID_PACKAGE")
                if not bundle:
                    return _failed("install ran but PYMOBILE_MCP_ANDROID_PACKAGE missing for uninstall")
                uninstall = await session.call_tool("mobile_uninstall_app", {"device": device_id, "bundle_id": bundle})
                if _error_payload(uninstall.content) is not None:
                    return _failed("uninstall failed", error=_payload(uninstall.content))
                destructive = {"status": "passed", "apk": apk, "package": bundle}

            print(
                json.dumps(
                    {
                        "status": "passed",
                        "device": device_id,
                        "app_count": len(apps),
                        "orientation": orientation,
                        "saveTo": str(path),
                        "destructive": destructive,
                    },
                    indent=2,
                )
            )
            path.unlink(missing_ok=True)
            return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

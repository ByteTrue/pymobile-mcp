"""iOS Simulator driver using simctl for system work and WebDriverAgent for UI."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import signal
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

from pymobile_mcp.errors import DriverError, UnsupportedPlatformError

from .base import AppInfo, BaseDriver, DeviceInfo, ScreenElement, ScreenSize

_create_subprocess_exec = asyncio.create_subprocess_exec


async def start_simctl_recording(
    device_id: str, output_path: str
) -> asyncio.subprocess.Process:
    return await _create_subprocess_exec(
        "xcrun",
        "simctl",
        "io",
        device_id,
        "recordVideo",
        output_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class IOSSimulatorDriver(BaseDriver):
    platform = "ios"
    device_type = "simulator"

    def __init__(self, device_id: str) -> None:
        self.device_id = device_id
        self._session_id: str | None = None
        self._wda_url = os.environ.get(
            "PYMOBILE_MCP_SIMULATOR_WDA_URL", "http://127.0.0.1:8100"
        )

    async def connect(self, capabilities: dict[str, Any] | None = None) -> None:
        del capabilities
        devices = await asyncio.to_thread(_simctl_json, "list", "devices", "available")
        if not any(
            item.get("udid") == self.device_id and item.get("state") == "Booted"
            for values in devices.get("devices", {}).values()
            for item in values
        ):
            raise DriverError(
                "ios",
                f'iOS Simulator "{self.device_id}" is not booted',
                {"device": self.device_id},
            )
        await asyncio.to_thread(self._request, "GET", "/status", None)

    async def disconnect(self) -> None:
        if self._session_id is not None:
            try:
                await asyncio.to_thread(
                    self._request, "DELETE", f"/session/{self._session_id}", None
                )
            except Exception:
                pass
        self._session_id = None

    async def screenshot(self) -> bytes:
        value = await asyncio.to_thread(self._request, "GET", "/screenshot", None)
        return base64.b64decode(value)

    async def get_elements_on_screen(self) -> list[ScreenElement]:
        from .ios import parse_wda_source_xml

        value = await asyncio.to_thread(
            self._request, "GET", f"/session/{await self._session()}/source", None
        )
        return parse_wda_source_xml(str(value))

    async def get_screen_size(self) -> ScreenSize:
        value = await asyncio.to_thread(
            self._request, "GET", f"/session/{await self._session()}/wda/screen", None
        )
        screen = value.get("screenSize", value)
        return ScreenSize(
            width=int(screen.get("width", 0)),
            height=int(screen.get("height", 0)),
            scale=float(value.get("scale") or 1.0),
        )

    async def tap(self, x: float, y: float) -> None:
        await asyncio.to_thread(
            self._request,
            "POST",
            f"/session/{await self._session()}/wda/tap",
            {"x": x, "y": y},
        )

    async def double_tap(self, x: float, y: float) -> None:
        await asyncio.to_thread(
            self._request,
            "POST",
            f"/session/{await self._session()}/wda/doubleTap",
            {"x": x, "y": y},
        )

    async def long_press(self, x: float, y: float, duration: float = 0.5) -> None:
        await asyncio.to_thread(
            self._request,
            "POST",
            f"/session/{await self._session()}/wda/touchAndHold",
            {"x": x, "y": y, "duration": duration},
        )

    async def swipe(
        self, start_x: float, start_y: float, end_x: float, end_y: float
    ) -> None:
        await asyncio.to_thread(
            self._request,
            "POST",
            f"/session/{await self._session()}/wda/dragfromtoforduration",
            {
                "fromX": start_x,
                "fromY": start_y,
                "toX": end_x,
                "toY": end_y,
                "duration": 0.5,
            },
        )

    async def type_keys(self, text: str, submit: bool) -> None:
        value = text + ("\n" if submit else "")
        await asyncio.to_thread(
            self._request,
            "POST",
            f"/session/{await self._session()}/wda/keys",
            {"value": list(value)},
        )

    async def list_apps(self) -> list[AppInfo]:
        data = await asyncio.to_thread(_simctl_listapps_json, self.device_id)
        return sorted(
            [
                AppInfo(
                    package_name=bundle,
                    app_name=str(
                        info.get("CFBundleDisplayName")
                        or info.get("CFBundleName")
                        or bundle
                    ),
                )
                for bundle, info in data.items()
            ],
            key=lambda app: app.package_name.lower(),
        )

    async def launch_app(self, package_name: str, locale: str | None = None) -> None:
        args = ["launch", self.device_id, package_name]
        if locale:
            args.extend(["-AppleLanguages", f"({locale})"])
        await asyncio.to_thread(_simctl, *args)

    async def terminate_app(self, package_name: str) -> None:
        await asyncio.to_thread(_simctl, "terminate", self.device_id, package_name)

    async def install_app(self, path: str) -> None:
        await asyncio.to_thread(_simctl, "install", self.device_id, path)

    async def uninstall_app(self, package_name: str) -> None:
        await asyncio.to_thread(_simctl, "uninstall", self.device_id, package_name)

    async def press_button(self, button: str) -> None:
        name = {"KEYCODE_HOME": "home", "HOME": "home"}.get(button)
        if name is None:
            raise UnsupportedPlatformError(
                "mobile_press_button",
                f"Button {button} is not supported on iOS Simulator",
            )
        await asyncio.to_thread(
            self._request,
            "POST",
            f"/session/{await self._session()}/wda/pressButton",
            {"name": name},
        )

    async def open_url(self, url: str) -> None:
        await asyncio.to_thread(_simctl, "openurl", self.device_id, url)

    async def get_orientation(self) -> str:
        value = await asyncio.to_thread(
            self._request, "GET", f"/session/{await self._session()}/orientation", None
        )
        return "landscape" if "LANDSCAPE" in str(value).upper() else "portrait"

    async def set_orientation(self, orientation: str) -> None:
        await asyncio.to_thread(
            self._request,
            "POST",
            f"/session/{await self._session()}/orientation",
            {"orientation": orientation.upper()},
        )

    async def start_recording(
        self, output_path: str, time_limit: int | float | None = None
    ) -> asyncio.subprocess.Process:
        del time_limit
        return await start_simctl_recording(self.device_id, output_path)

    async def stop_recording(
        self, process: asyncio.subprocess.Process, remote_path: str, local_path: Any
    ) -> int:
        del remote_path
        process.send_signal(signal.SIGINT)
        try:
            await asyncio.wait_for(process.wait(), timeout=30)
        except asyncio.TimeoutError as exc:
            try:
                process.kill()
            except Exception:
                pass
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except Exception:
                pass
            raise DriverError(
                "ios",
                "iOS Simulator screen recording did not stop within 30 seconds",
                {"device": self.device_id, "timeout": 30},
            ) from exc
        return Path(local_path).stat().st_size

    async def list_crashes(self) -> list[dict[str, Any]]:
        return await asyncio.to_thread(_list_simulator_crashes, self.device_id)

    async def get_crash(self, crash_id: str) -> str:
        return await asyncio.to_thread(_read_simulator_crash, self.device_id, crash_id)

    async def _session(self) -> str:
        if self._session_id is None:
            value = await asyncio.to_thread(
                self._request,
                "POST",
                "/session",
                {
                    "capabilities": {"alwaysMatch": {"shouldWaitForQuiescence": False}},
                    "desiredCapabilities": {},
                },
            )
            self._session_id = str(
                value.get("sessionId") or value.get("value", {}).get("sessionId")
            )
        return self._session_id

    def _request(self, method: str, path: str, payload: dict[str, Any] | None) -> Any:
        body = None if payload is None else json.dumps(payload).encode()
        request = urllib.request.Request(
            self._wda_url + path,
            data=body,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                data = json.load(response)
        except Exception as exc:
            raise DriverError(
                "ios",
                f"Simulator WDA request failed: {exc}",
                {"device": self.device_id, "path": path},
            ) from exc
        value = data.get("value", data)
        if isinstance(value, dict) and value.get("error"):
            raise DriverError(
                "ios", str(value.get("message") or value["error"]), {"path": path}
            )
        return value


def list_ios_simulators() -> list[DeviceInfo]:
    try:
        data = _simctl_json("list", "devices", "available")
    except Exception:
        return []
    return [
        DeviceInfo(
            id=str(item["udid"]),
            name=str(item["name"]),
            platform="ios",
            type="simulator",
            version=runtime.removeprefix("com.apple.CoreSimulator.SimRuntime.").replace(
                "-", "."
            ),
            state="online",
        )
        for runtime, items in data.get("devices", {}).items()
        for item in items
        if item.get("isAvailable", True) and item.get("state") == "Booted"
    ]


def _simctl(*args: str) -> str:
    return subprocess.run(
        ["xcrun", "simctl", *args], check=True, capture_output=True, text=True
    ).stdout


def _simctl_json(*args: str) -> dict[str, Any]:
    return json.loads(_simctl(*args, "--json"))


def _simctl_listapps_json(device_id: str) -> dict[str, Any]:
    raw = _simctl("listapps", device_id)
    converted = subprocess.run(
        ["plutil", "-convert", "json", "-o", "-", "--", "-"],
        input=raw,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(converted.stdout)


def _simulator_crash_root(device_id: str) -> Path:
    return (
        Path.home()
        / "Library/Developer/CoreSimulator/Devices"
        / device_id
        / "data/Library/Logs/CrashReporter"
    )


def _list_simulator_crashes(device_id: str) -> list[dict[str, Any]]:
    root = _simulator_crash_root(device_id)
    if not root.is_dir():
        return []
    resolved_root = root.resolve()
    crashes = []
    for report in root.rglob("*"):
        if not report.is_file():
            continue
        try:
            report.resolve().relative_to(resolved_root)
        except ValueError:
            continue
        crash_id = report.relative_to(root).as_posix()
        crashes.append({"id": crash_id, "name": crash_id, "path": str(report)})
    return sorted(crashes, key=lambda crash: str(crash["id"]).lower())


def _read_simulator_crash(device_id: str, crash_id: str) -> str:
    root = _simulator_crash_root(device_id).resolve()
    requested = Path(crash_id)
    try:
        report = (root / requested).resolve()
        report.relative_to(root)
        if requested.is_absolute() or not report.is_file():
            raise ValueError
        return report.read_text(errors="replace")
    except (OSError, ValueError) as exc:
        raise DriverError(
            "ios",
            f'Crash report "{crash_id}" not found or unreadable',
            {"id": crash_id},
        ) from exc

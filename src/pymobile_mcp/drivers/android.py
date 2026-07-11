"""Android driver implementation using uiautomator2."""

from __future__ import annotations

import asyncio
import os
import io
from pathlib import Path
from typing import Any

import adbutils
import uiautomator2 as u2

from pymobile_mcp.errors import DriverError

from .base import AppInfo, BaseDriver, DeviceInfo, ScreenElement, ScreenElementRect, ScreenSize


def list_android_devices() -> list[DeviceInfo]:
    devices: list[DeviceInfo] = []
    for device in adbutils.adb.device_list():
        devices.append(
            DeviceInfo(
                id=device.serial,
                name=device.prop.name or device.serial,
                platform="android",
                type="emulator" if device.serial.startswith("emulator-") else "real",
                version=device.prop.get("ro.build.version.release") or "unknown",
                state="online" if device.get_state() == "device" else "offline",
            )
        )
    return devices


class AndroidDriver(BaseDriver):
    platform = "android"

    def __init__(self, device_id: str) -> None:
        self.device_id = device_id
        self._device: Any | None = None

    async def connect(self, capabilities: dict[str, Any] | None = None) -> None:
        del capabilities
        self._device = await asyncio.to_thread(u2.connect, self.device_id)

    async def disconnect(self) -> None:
        self._device = None

    async def screenshot(self) -> bytes:
        device = await self._connected()
        image = await asyncio.to_thread(device.screenshot)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    async def get_elements_on_screen(self) -> list[ScreenElement]:
        device = await self._connected()
        xml = await asyncio.to_thread(device.dump_hierarchy)
        return parse_uiautomator_xml(xml)

    async def get_screen_size(self) -> ScreenSize:
        device = await self._connected()
        width, height = await asyncio.to_thread(lambda: device.window_size())
        return ScreenSize(width=int(width), height=int(height))

    async def tap(self, x: float, y: float) -> None:
        device = await self._connected()
        await asyncio.to_thread(device.click, x, y)

    async def double_tap(self, x: float, y: float) -> None:
        device = await self._connected()
        await asyncio.to_thread(device.double_click, x, y)

    async def long_press(self, x: float, y: float, duration: float = 0.5) -> None:
        device = await self._connected()
        await asyncio.to_thread(device.long_click, x, y, duration)

    async def swipe(self, start_x: float, start_y: float, end_x: float, end_y: float) -> None:
        device = await self._connected()
        await asyncio.to_thread(device.swipe, start_x, start_y, end_x, end_y)

    async def type_keys(self, text: str, submit: bool) -> None:
        device = await self._connected()
        await asyncio.to_thread(device.send_keys, text)
        if submit:
            await asyncio.to_thread(device.press, "enter")

    async def list_apps(self) -> list[AppInfo]:
        return await asyncio.to_thread(self._list_apps_sync)

    async def launch_app(self, package_name: str, locale: str | None = None) -> None:
        await asyncio.to_thread(self._launch_app_sync, package_name, locale)

    async def terminate_app(self, package_name: str) -> None:
        await asyncio.to_thread(self._adb().app_stop, package_name)

    async def install_app(self, path: str) -> None:
        await asyncio.to_thread(self._adb().install, path, True, False, True)

    async def uninstall_app(self, package_name: str) -> None:
        await asyncio.to_thread(self._adb().uninstall, package_name)

    async def press_button(self, button: str) -> None:
        # button is already mapped to KEYCODE_* by tool validation
        await asyncio.to_thread(self._adb().keyevent, button)

    async def open_url(self, url: str) -> None:
        device = await self._connected()
        await asyncio.to_thread(device.open_url, url)

    async def get_orientation(self) -> str:
        return await asyncio.to_thread(self._get_orientation_sync)

    async def set_orientation(self, orientation: str) -> None:
        await asyncio.to_thread(self._set_orientation_sync, orientation)


    async def list_crashes(self) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._list_crashes_sync)

    async def get_crash(self, crash_id: str) -> str:
        return await asyncio.to_thread(self._get_crash_sync, crash_id)

    def _list_crashes_sync(self) -> list[dict[str, Any]]:
        entries = self._parse_dropbox_print(self._adb().shell(["dumpsys", "dropbox", "--print"]))
        return [
            {
                "id": entry["id"],
                "name": entry["tag"],
                "timestamp": entry["timestamp"],
                "size": entry["size"],
                "kind": entry["kind"],
            }
            for entry in entries
        ]

    def _get_crash_sync(self, crash_id: str) -> str:
        entries = self._parse_dropbox_print(self._adb().shell(["dumpsys", "dropbox", "--print"]))
        for entry in entries:
            if entry["id"] == crash_id:
                return entry["content"]
        raise DriverError("android", f'Crash report "{crash_id}" not found', {"id": crash_id})

    # Tags that are usually crash/ANR-ish. Strictmode/boot noise is excluded by default.
    # ponytail: keep this allowlist simple; expand if real crash tags are missing.
    _DROPBOX_CRASH_TAGS = (
        "system_app_crash",
        "system_app_anr",
        "system_server_crash",
        "system_server_anr",
        "data_app_crash",
        "data_app_anr",
        "system_app_native_crash",
        "data_app_native_crash",
        "system_server_native_crash",
        "SYSTEM_TOMBSTONE",
        "SYSTEM_TOMBSTONE_PROTO",
        "system_app_wtf",
        "system_server_wtf",
    )


    @staticmethod
    def _dropbox_include_all_env() -> bool:
        return os.environ.get("PYMOBILE_MCP_ANDROID_DROPBOX_ALL", "").strip() in {"1", "true", "TRUE", "yes", "YES"}

    @classmethod
    def _is_crashish_dropbox_tag(cls, tag: str) -> bool:
        if tag in cls._DROPBOX_CRASH_TAGS:
            return True
        low = tag.lower()
        return "crash" in low or "anr" in low or "tombstone" in low

    def _parse_dropbox_print(self, output: Any, *, include_all: bool = False) -> list[dict[str, Any]]:
        import re

        text = str(output)
        parts = re.split(r"={5,}\n", text)
        header_re = re.compile(
            r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\S+) \(([^,]+), (\d+) bytes\)\s*$"
        )
        entries: list[dict[str, Any]] = []
        counts: dict[str, int] = {}
        for part in parts:
            lines = part.strip().splitlines()
            if not lines:
                continue
            match = header_re.match(lines[0].strip())
            if not match:
                continue
            timestamp, tag, kind, size_s = match.groups()
            if not include_all and not self._dropbox_include_all_env() and not self._is_crashish_dropbox_tag(tag):
                continue
            base_id = f"{timestamp}::{tag}"
            n = counts.get(base_id, 0)
            counts[base_id] = n + 1
            crash_id = base_id if n == 0 else f"{base_id}#{n}"
            entries.append(
                {
                    "id": crash_id,
                    "timestamp": timestamp,
                    "tag": tag,
                    "kind": kind,
                    "size": int(size_s),
                    "content": "\n".join(lines[1:]).strip(),
                }
            )
        return entries

    def _adb(self) -> Any:
        return adbutils.adb.device(self.device_id)

    def _list_apps_sync(self) -> list[AppInfo]:
        output = self._adb().shell(
            [
                "cmd",
                "package",
                "query-activities",
                "-a",
                "android.intent.action.MAIN",
                "-c",
                "android.intent.category.LAUNCHER",
            ]
        )
        packages: list[str] = []
        seen: set[str] = set()
        for line in str(output).splitlines():
            text = line.strip()
            if not text.startswith("packageName="):
                continue
            package = text.split("=", 1)[1]
            if package in seen:
                continue
            seen.add(package)
            packages.append(package)
        return [AppInfo(package_name=package, app_name=package) for package in packages]

    def _launch_app_sync(self, package_name: str, locale: str | None) -> None:
        adb = self._adb()
        if locale:
            try:
                adb.shell(["cmd", "locale", "set-app-locales", package_name, "--locales", locale])
            except Exception:
                # Android < 13 has no set-app-locales; ignore like mobile-mcp.
                pass
        try:
            adb.shell(["monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"])
        except Exception as exc:
            raise DriverError(
                "android",
                f'Failed launching app with package name "{package_name}", please make sure it exists',
                {"packageName": package_name},
            ) from exc

    def _get_orientation_sync(self) -> str:
        rotation = str(self._adb().shell(["settings", "get", "system", "user_rotation"])).strip()
        return "portrait" if rotation in {"0", "null", ""} else "landscape"

    def _set_orientation_sync(self, orientation: str) -> None:
        value = "0" if orientation == "portrait" else "1"
        adb = self._adb()
        adb.shell(["settings", "put", "system", "accelerometer_rotation", "0"])
        adb.shell(
            [
                "content",
                "insert",
                "--uri",
                "content://settings/system",
                "--bind",
                "name:s:user_rotation",
                "--bind",
                f"value:i:{value}",
            ]
        )


    async def start_recording(self, remote_path: str, time_limit: int | None = None) -> Any:
        return await asyncio.to_thread(self._start_recording_sync, remote_path, time_limit)

    async def stop_recording(self, process: Any, remote_path: str, local_path: Path) -> int:
        return await asyncio.to_thread(self._stop_recording_sync, process, remote_path, local_path)

    def _start_recording_sync(self, remote_path: str, time_limit: int | None) -> Any:
        import subprocess

        cmd = ["adb", "-s", self.device_id, "shell", "screenrecord"]
        if time_limit is not None:
            cmd.extend(["--time-limit", str(time_limit)])
        cmd.append(remote_path)
        try:
            self._adb().shell(["rm", "-f", remote_path])
        except Exception:
            pass
        return subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _stop_recording_sync(self, process: Any, remote_path: str, local_path: Path) -> int:
        import signal
        import time

        # Prefer stopping the on-device screenrecord process; local adb may not
        # forward SIGINT reliably and can hang if stdout pipes fill.
        try:
            self._adb().shell(["pkill", "-l", "INT", "screenrecord"])
        except Exception:
            try:
                self._adb().shell(["killall", "-2", "screenrecord"])
            except Exception:
                pass
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=5)
            except Exception:
                process.kill()
                try:
                    process.wait(timeout=3)
                except Exception:
                    pass
        # pull file
        local_path.parent.mkdir(parents=True, exist_ok=True)
        if local_path.exists():
            local_path.unlink()
        # give filesystem a moment
        for _ in range(20):
            listing = str(self._adb().shell(["ls", "-l", remote_path]))
            if "No such file" not in listing and remote_path.split("/")[-1] in listing:
                break
            time.sleep(0.1)
        self._adb().sync.pull(remote_path, str(local_path))
        try:
            self._adb().shell(["rm", "-f", remote_path])
        except Exception:
            pass
        if not local_path.exists() or local_path.stat().st_size <= 0:
            raise DriverError("android", f"Recording file was not produced at {local_path}")
        return local_path.stat().st_size

    async def _connected(self) -> Any:
        if self._device is None:
            await self.connect()
        if self._device is None:
            raise DriverError("android", f'Device "{self.device_id}" is not connected.')
        return self._device


def parse_uiautomator_xml(xml: str) -> list[ScreenElement]:
    from xml.etree import ElementTree

    root = ElementTree.fromstring(xml)
    elements: list[ScreenElement] = []
    for node in root.iter("node"):
        bounds = node.attrib.get("bounds")
        rect = _parse_bounds(bounds or "")
        if rect is None:
            continue
        text = node.attrib.get("text") or None
        label = node.attrib.get("content-desc") or None
        identifier = node.attrib.get("resource-id") or None
        class_name = node.attrib.get("class") or "android.view.View"
        value = text or label or identifier
        if not value:
            continue
        elements.append(
            ScreenElement(
                type=class_name,
                rect=rect,
                label=label,
                text=text,
                name=label or text,
                value=value,
                identifier=identifier,
                focused=_bool_or_none(node.attrib.get("focused")),
            )
        )
    return elements


def _parse_bounds(bounds: str) -> ScreenElementRect | None:
    if not bounds.startswith("[") or "][" not in bounds or not bounds.endswith("]"):
        return None
    try:
        first, second = bounds[1:-1].split("][", 1)
        left, top = [int(part) for part in first.split(",", 1)]
        right, bottom = [int(part) for part in second.split(",", 1)]
    except ValueError:
        return None
    return ScreenElementRect(x=left, y=top, width=right - left, height=bottom - top)


def _bool_or_none(value: str | None) -> bool | None:
    if value is None:
        return None
    return value.lower() == "true"

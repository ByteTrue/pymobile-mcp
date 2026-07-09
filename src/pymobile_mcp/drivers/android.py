"""Android driver implementation using uiautomator2."""

from __future__ import annotations

import asyncio
import io
from typing import Any

import adbutils
import uiautomator2 as u2

from pymobile_mcp.errors import DriverError


from .base import BaseDriver, DeviceInfo, ScreenElement, ScreenElementRect, ScreenSize


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

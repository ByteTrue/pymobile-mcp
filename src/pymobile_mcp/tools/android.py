"""Android-backed MCP tool handlers."""

from __future__ import annotations

import asyncio

import base64
import json
from dataclasses import asdict
from typing import Any, Callable, Protocol

from mcp.types import ImageContent, TextContent

from pymobile_mcp.drivers.base import DeviceInfo, ScreenElement, ScreenSize
from pymobile_mcp.errors import DeviceNotFoundError


class AndroidDriverLike(Protocol):
    async def connect(self, capabilities: dict[str, Any] | None = None) -> None: ...
    async def get_screen_size(self) -> ScreenSize: ...
    async def screenshot(self) -> bytes: ...
    async def get_elements_on_screen(self) -> list[ScreenElement]: ...
    async def tap(self, x: float, y: float) -> None: ...
    async def double_tap(self, x: float, y: float) -> None: ...
    async def long_press(self, x: float, y: float, duration: float = 0.5) -> None: ...
    async def swipe(self, start_x: float, start_y: float, end_x: float, end_y: float) -> None: ...
    async def type_keys(self, text: str, submit: bool) -> None: ...


DeviceDiscovery = Callable[[], list[DeviceInfo]]
DriverFactory = Callable[[str], AndroidDriverLike]
Register = Callable[[str, Callable[[dict[str, Any]], Any]], None]

_device_discovery: DeviceDiscovery | None = None
_driver_factory: DriverFactory | None = None


def configure_android_tools_for_tests(device_discovery: DeviceDiscovery, driver_factory: DriverFactory) -> None:
    global _device_discovery, _driver_factory
    _device_discovery = device_discovery
    _driver_factory = driver_factory


def reset_android_tools_for_tests() -> None:
    global _device_discovery, _driver_factory
    _device_discovery = None
    _driver_factory = None


def register_android_handlers(register: Register) -> None:
    register("mobile_list_available_devices", list_available_devices)
    register("mobile_get_screen_size", get_screen_size)
    register("mobile_take_screenshot", take_screenshot)
    register("mobile_list_elements_on_screen", list_elements_on_screen)
    register("mobile_click_on_screen_at_coordinates", tap)
    register("mobile_double_tap_on_screen", double_tap)
    register("mobile_long_press_on_screen_at_coordinates", long_press)
    register("mobile_swipe_on_screen", swipe)
    register("mobile_type_keys", type_keys)


async def list_available_devices(args: dict[str, Any]) -> list[TextContent]:
    del args
    devices = [_device_to_dict(device) for device in await asyncio.to_thread(_discover_devices)]
    return [_text({"devices": devices})]


async def get_screen_size(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_get_screen_size", str(args["device"]))
    size = await driver.get_screen_size()
    return [_text(asdict(size))]


async def take_screenshot(args: dict[str, Any]) -> list[ImageContent]:
    driver = await _driver_for("mobile_take_screenshot", str(args["device"]))
    data = await driver.screenshot()
    return [ImageContent(type="image", data=base64.b64encode(data).decode("ascii"), mimeType="image/png")]


async def list_elements_on_screen(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_list_elements_on_screen", str(args["device"]))
    elements = await driver.get_elements_on_screen()
    return [_text({"elements": [_element_to_dict(element) for element in elements]})]


async def tap(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_click_on_screen_at_coordinates", str(args["device"]))
    await driver.tap(float(args["x"]), float(args["y"]))
    return [_ok("mobile_click_on_screen_at_coordinates")]


async def double_tap(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_double_tap_on_screen", str(args["device"]))
    await driver.double_tap(float(args["x"]), float(args["y"]))
    return [_ok("mobile_double_tap_on_screen")]


async def long_press(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_long_press_on_screen_at_coordinates", str(args["device"]))
    duration = float(args.get("duration", 500)) / 1000
    await driver.long_press(float(args["x"]), float(args["y"]), duration)
    return [_ok("mobile_long_press_on_screen_at_coordinates")]


async def swipe(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_swipe_on_screen", str(args["device"]))
    size = await driver.get_screen_size()
    direction = str(args["direction"])
    start_x = float(args.get("x", size.width / 2))
    start_y = float(args.get("y", size.height / 2))
    distance = float(args.get("distance", (size.height if direction in {"up", "down"} else size.width) * 0.3))
    end_x, end_y = _swipe_end(start_x, start_y, direction, distance, size)
    await driver.swipe(start_x, start_y, end_x, end_y)
    return [_ok("mobile_swipe_on_screen")]


async def type_keys(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_type_keys", str(args["device"]))
    await driver.type_keys(str(args["text"]), bool(args["submit"]))
    return [_ok("mobile_type_keys")]


async def _driver_for(tool: str, device_id: str) -> AndroidDriverLike:
    devices = await asyncio.to_thread(_discover_devices)
    if device_id not in {device.id for device in devices if device.state == "online"}:
        raise DeviceNotFoundError(tool, device_id)
    driver = _make_driver(device_id)
    await driver.connect()
    return driver


def _discover_devices() -> list[DeviceInfo]:
    if _device_discovery is not None:
        return _device_discovery()
    from pymobile_mcp.drivers.android import list_android_devices

    return list_android_devices()


def _make_driver(device_id: str) -> AndroidDriverLike:
    if _driver_factory is not None:
        return _driver_factory(device_id)
    from pymobile_mcp.drivers.android import AndroidDriver

    return AndroidDriver(device_id)


def _device_to_dict(device: DeviceInfo) -> dict[str, Any]:
    return asdict(device)


def _element_to_dict(element: ScreenElement) -> dict[str, Any]:
    return {
        "type": element.type,
        "text": element.text,
        "label": element.label,
        "name": element.name,
        "value": element.value,
        "identifier": element.identifier,
        "focused": element.focused,
        "coordinates": asdict(element.rect),
    }


def _swipe_end(start_x: float, start_y: float, direction: str, distance: float, size: ScreenSize) -> tuple[float, float]:
    if direction == "up":
        return start_x, max(0, start_y - distance)
    if direction == "down":
        return start_x, min(size.height - 1, start_y + distance)
    if direction == "left":
        return max(0, start_x - distance), start_y
    return min(size.width - 1, start_x + distance), start_y


def _text(payload: dict[str, Any]) -> TextContent:
    return TextContent(type="text", text=json.dumps(payload, sort_keys=True))


def _ok(tool: str) -> TextContent:
    return _text({"status": "ok", "tool": tool})

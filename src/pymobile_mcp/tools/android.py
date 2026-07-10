"""Android-backed MCP tool handlers."""

from __future__ import annotations

import asyncio
import base64
import json
from dataclasses import asdict
from typing import Any, Callable, Protocol

from mcp.types import ImageContent, TextContent

from pymobile_mcp.drivers.base import AppInfo, DeviceInfo, ScreenElement, ScreenSize
from pymobile_mcp.errors import DeviceNotFoundError
from pymobile_mcp.tools.validation import (
    validate_button,
    validate_orientation,
    validate_output_path,
    validate_recording_output,
    validate_time_limit,
    validate_url,
)
from pymobile_mcp.tools import recording as recording_state
from pymobile_mcp.errors import UnsupportedPlatformError


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
    async def list_apps(self) -> list[AppInfo]: ...
    async def launch_app(self, package_name: str, locale: str | None = None) -> None: ...
    async def terminate_app(self, package_name: str) -> None: ...
    async def install_app(self, path: str) -> None: ...
    async def uninstall_app(self, package_name: str) -> None: ...
    async def press_button(self, button: str) -> None: ...
    async def open_url(self, url: str) -> None: ...
    async def get_orientation(self) -> str: ...
    async def set_orientation(self, orientation: str) -> None: ...
    async def start_recording(self, remote_path: str, time_limit: int | None = None) -> Any: ...
    async def stop_recording(self, process: Any, remote_path: str, local_path: Any) -> int: ...


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
    register("mobile_list_apps", list_apps)
    register("mobile_launch_app", launch_app)
    register("mobile_terminate_app", terminate_app)
    register("mobile_install_app", install_app)
    register("mobile_uninstall_app", uninstall_app)
    register("mobile_press_button", press_button)
    register("mobile_open_url", open_url)
    register("mobile_get_orientation", get_orientation)
    register("mobile_set_orientation", set_orientation)
    register("mobile_save_screenshot", save_screenshot)
    register("mobile_start_screen_recording", start_screen_recording)
    register("mobile_stop_screen_recording", stop_screen_recording)
    register("mobile_list_crashes", list_crashes)
    register("mobile_get_crash", get_crash)


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


async def list_apps(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_list_apps", str(args["device"]))
    apps = await driver.list_apps()
    return [_text({"apps": [_app_to_dict(app) for app in apps]})]


async def launch_app(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_launch_app", str(args["device"]))
    package_name = str(args["packageName"])
    locale = args.get("locale")
    await driver.launch_app(package_name, None if locale is None else str(locale))
    return [_text({"status": "ok", "tool": "mobile_launch_app", "packageName": package_name})]


async def terminate_app(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_terminate_app", str(args["device"]))
    package_name = str(args["packageName"])
    await driver.terminate_app(package_name)
    return [_text({"status": "ok", "tool": "mobile_terminate_app", "packageName": package_name})]


async def install_app(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_install_app", str(args["device"]))
    path = str(args["path"])
    await driver.install_app(path)
    return [_text({"status": "ok", "tool": "mobile_install_app", "path": path})]


async def uninstall_app(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_uninstall_app", str(args["device"]))
    bundle_id = str(args["bundle_id"])
    await driver.uninstall_app(bundle_id)
    return [_text({"status": "ok", "tool": "mobile_uninstall_app", "bundle_id": bundle_id})]


async def press_button(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_press_button", str(args["device"]))
    keycode = validate_button("mobile_press_button", str(args["button"]))
    await driver.press_button(keycode)
    return [_text({"status": "ok", "tool": "mobile_press_button", "button": args["button"]})]


async def open_url(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_open_url", str(args["device"]))
    url = validate_url("mobile_open_url", str(args["url"]))
    await driver.open_url(url)
    return [_text({"status": "ok", "tool": "mobile_open_url", "url": url})]


async def get_orientation(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_get_orientation", str(args["device"]))
    orientation = await driver.get_orientation()
    return [_text({"orientation": orientation})]


async def set_orientation(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_set_orientation", str(args["device"]))
    orientation = validate_orientation("mobile_set_orientation", str(args["orientation"]))
    await driver.set_orientation(orientation)
    return [_text({"status": "ok", "tool": "mobile_set_orientation", "orientation": orientation})]


async def save_screenshot(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_save_screenshot", str(args["device"]))
    path = validate_output_path("mobile_save_screenshot", str(args["saveTo"]))
    data = await driver.screenshot()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return [_text({"status": "ok", "tool": "mobile_save_screenshot", "saveTo": str(path)})]




async def start_screen_recording(args: dict[str, Any]) -> list[TextContent]:
    device_id = str(args["device"])
    driver = await _driver_for("mobile_start_screen_recording", device_id)
    output = validate_recording_output("mobile_start_screen_recording", None if args.get("output") is None else str(args.get("output")))
    time_limit = validate_time_limit("mobile_start_screen_recording", args.get("timeLimit"))
    remote_path = f"/sdcard/pymobile-mcp-{device_id.replace(':', '_')}.mp4"
    process = await driver.start_recording(remote_path, time_limit)
    recording = await recording_state.start_recording(device_id, output, process, remote_path)
    return [_text({"status": "started", "tool": "mobile_start_screen_recording", "device": device_id, "output": str(recording.output_path)})]


async def stop_screen_recording(args: dict[str, Any]) -> list[TextContent]:
    device_id = str(args["device"])
    driver = await _driver_for("mobile_stop_screen_recording", device_id)
    recording = await recording_state.pop_recording(device_id)
    try:
        size = await driver.stop_recording(recording.process, recording.remote_path, recording.output_path)
    except Exception:
        # ensure no orphan process / remote file best-effort already handled in driver
        raise
    duration = max(0, int(__import__('time').time() - recording.started_at))
    return [_text({
        "status": "stopped",
        "tool": "mobile_stop_screen_recording",
        "device": device_id,
        "output": str(recording.output_path),
        "size": size,
        "duration_seconds": duration,
    })]


async def list_crashes(args: dict[str, Any]) -> list[TextContent]:
    await _driver_for("mobile_list_crashes", str(args["device"]))
    raise UnsupportedPlatformError(
        "mobile_list_crashes",
        "Android crash reports are not exposed through a reliable pure-Python/ADB source in this MVP.",
        {"platform": "android"},
    )


async def get_crash(args: dict[str, Any]) -> list[TextContent]:
    await _driver_for("mobile_get_crash", str(args["device"]))
    raise UnsupportedPlatformError(
        "mobile_get_crash",
        "Android crash reports are not exposed through a reliable pure-Python/ADB source in this MVP.",
        {"platform": "android", "id": str(args["id"])},
    )


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


def _app_to_dict(app: AppInfo) -> dict[str, Any]:
    payload = {"packageName": app.package_name, "appName": app.app_name}
    if app.version is not None:
        payload["version"] = app.version
    return payload


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

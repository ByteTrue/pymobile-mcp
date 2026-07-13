"""Android-backed MCP tool handlers."""

from __future__ import annotations

import asyncio
from contextvars import ContextVar
from dataclasses import asdict
from typing import Any, Callable, Protocol

from mcp.types import ImageContent, TextContent

from pymobile_mcp.drivers.base import AppInfo, DeviceInfo, ScreenElement, ScreenSize
from pymobile_mcp.errors import DeviceNotFoundError
from pymobile_mcp.tools.contract import screenshot as format_screenshot, text as _text
from pymobile_mcp.tools.validation import (
    validate_button,
    validate_orientation,
    validate_locale,
    validate_package_name,
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
    async def start_recording(self, remote_path: str, time_limit: int | float | None = None) -> Any: ...
    async def stop_recording(self, process: Any, remote_path: str, local_path: Any) -> int: ...


DeviceDiscovery = Callable[[], list[DeviceInfo]]
DriverFactory = Callable[[str], AndroidDriverLike]
Register = Callable[[str, Callable[[dict[str, Any]], Any]], None]

_device_discovery: DeviceDiscovery | None = None
_driver_factory: DriverFactory | None = None
_temporary_drivers: ContextVar[tuple[AndroidDriverLike, ...]] = ContextVar("temporary_mobile_drivers", default=())


def configure_android_tools_for_tests(device_discovery: DeviceDiscovery, driver_factory: DriverFactory) -> None:
    global _device_discovery, _driver_factory
    _device_discovery = device_discovery
    _driver_factory = driver_factory


def reset_android_tools_for_tests() -> None:
    global _device_discovery, _driver_factory
    _device_discovery = None
    _driver_factory = None
    _temporary_drivers.set(())


async def cleanup_temporary_drivers() -> None:
    drivers = _temporary_drivers.get()
    _temporary_drivers.set(())
    for driver in reversed(drivers):
        disconnect = getattr(driver, "disconnect", None)
        if disconnect is not None:
            try:
                result = disconnect()
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                pass


def _remember_driver(driver: AndroidDriverLike) -> AndroidDriverLike:
    _temporary_drivers.set((*_temporary_drivers.get(), driver))
    return driver


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


def _write_screenshot(path: Any, data: bytes) -> None:
    path.write_bytes(data)


def screenrecord_contract_argv(device_id: str, output: str, time_limit: int | float | None) -> list[str]:
    argv = ["screenrecord", "--device", device_id, "--output", output, "--silent"]
    if time_limit is not None:
        argv.extend(["--time-limit", _number(float(time_limit))])
    return argv


def _observe_recording_cli(argv: list[str]) -> None:
    del argv


async def get_screen_size(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_get_screen_size", str(args["device"]))
    size = await driver.get_screen_size()
    return [_text(f"Screen size is {size.width}x{size.height} pixels")]


async def take_screenshot(args: dict[str, Any]) -> list[ImageContent]:
    driver = await _driver_for("mobile_take_screenshot", str(args["device"]))
    size = await driver.get_screen_size()
    data = await driver.screenshot()
    return [format_screenshot(data, size.scale)]


async def list_elements_on_screen(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_list_elements_on_screen", str(args["device"]))
    elements = await driver.get_elements_on_screen()
    return [_text(f"Found these elements on screen: {_json([_element_to_dict(element) for element in elements])}")]


async def tap(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_click_on_screen_at_coordinates", str(args["device"]))
    x, y = float(args["x"]), float(args["y"])
    await driver.tap(x, y)
    return [_text(f"Clicked on screen at coordinates: {_number(x)}, {_number(y)}")]


async def double_tap(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_double_tap_on_screen", str(args["device"]))
    x, y = float(args["x"]), float(args["y"])
    await driver.double_tap(x, y)
    return [_text(f"Double-tapped on screen at coordinates: {_number(x)}, {_number(y)}")]


async def long_press(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_long_press_on_screen_at_coordinates", str(args["device"]))
    x, y, duration = float(args["x"]), float(args["y"]), float(args.get("duration", 500))
    await driver.long_press(x, y, duration / 1000)
    return [_text(f"Long pressed on screen at coordinates: {_number(x)}, {_number(y)} for {_number(duration)}ms")]


async def swipe(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_swipe_on_screen", str(args["device"]))
    size = await driver.get_screen_size()
    direction = str(args["direction"])
    if "x" in args and "y" in args:
        start_x, start_y = float(args["x"]), float(args["y"])
        is_ios = getattr(driver, "platform", None) == "ios"
        default = 400 if is_ios else (size.height if direction in {"up", "down"} else size.width) * 0.3
        raw_distance = args.get("distance")
        distance = float(raw_distance) if raw_distance is not None and (raw_distance != 0 or is_ios) else default
        end_x, end_y = _swipe_end(start_x, start_y, direction, distance, size)
        await driver.swipe(start_x, start_y, end_x, end_y)
        distance_text = f" {_number(float(args['distance']))} pixels" if args.get("distance") else ""
        return [_text(f"Swiped {direction}{distance_text} from coordinates: {_number(start_x)}, {_number(start_y)}")]
    center_x, center_y = size.width // 2, size.height // 2
    horizontal = int(size.width * 0.3)
    vertical = int(size.height * 0.3)
    if direction == "up":
        start_x = end_x = center_x
        start_y, end_y = center_y + vertical, center_y - vertical
    elif direction == "down":
        start_x = end_x = center_x
        start_y, end_y = center_y - vertical, center_y + vertical
    elif direction == "left":
        start_y = end_y = center_y
        start_x, end_x = center_x + horizontal, center_x - horizontal
    else:
        start_y = end_y = center_y
        start_x, end_x = center_x - horizontal, center_x + horizontal
    await driver.swipe(start_x, start_y, end_x, end_y)
    return [_text(f"Swiped {direction} on screen")]


async def type_keys(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_type_keys", str(args["device"]))
    await driver.type_keys(str(args["text"]), bool(args["submit"]))
    return [_text(f"Typed text: {args['text']}")]


async def list_apps(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_list_apps", str(args["device"]))
    apps = await driver.list_apps()
    return [_text(f"Found these apps on device: {', '.join(f'{app.app_name} ({app.package_name})' for app in apps)}")]


async def launch_app(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_launch_app", str(args["device"]))
    package_name = validate_package_name("mobile_launch_app", str(args["packageName"]))
    locale = args.get("locale")
    if locale is not None:
        locale = validate_locale("mobile_launch_app", str(locale))
    await driver.launch_app(package_name, None if locale is None else str(locale))
    return [_text(f"Launched app {package_name}")]


async def terminate_app(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_terminate_app", str(args["device"]))
    package_name = validate_package_name("mobile_terminate_app", str(args["packageName"]))
    await driver.terminate_app(package_name)
    return [_text(f"Terminated app {package_name}")]


async def install_app(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_install_app", str(args["device"]))
    path = str(args["path"])
    await driver.install_app(path)
    return [_text(f"Installed app from {path}")]


async def uninstall_app(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_uninstall_app", str(args["device"]))
    bundle_id = str(args["bundle_id"])
    await driver.uninstall_app(bundle_id)
    return [_text(f"Uninstalled app {bundle_id}")]


async def press_button(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_press_button", str(args["device"]))
    keycode = validate_button("mobile_press_button", str(args["button"]))
    await driver.press_button(keycode)
    return [_text(f"Pressed the button: {args['button']}")]


async def open_url(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_open_url", str(args["device"]))
    url = validate_url("mobile_open_url", str(args["url"]))
    await driver.open_url(url)
    return [_text(f"Opened URL: {url}")]


async def get_orientation(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_get_orientation", str(args["device"]))
    orientation = await driver.get_orientation()
    return [_text(f"Current device orientation is {orientation}")]


async def set_orientation(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_set_orientation", str(args["device"]))
    orientation = validate_orientation("mobile_set_orientation", str(args["orientation"]))
    await driver.set_orientation(orientation)
    return [_text(f"Changed device orientation to {orientation}")]


async def save_screenshot(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_save_screenshot", str(args["device"]))
    path = validate_output_path("mobile_save_screenshot", str(args["saveTo"]))
    data = await driver.screenshot()
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_screenshot(path, data)
    return [_text(f"Screenshot saved to: {args['saveTo']}")]


async def start_screen_recording(args: dict[str, Any]) -> list[TextContent]:
    device_id = str(args["device"])
    driver = await _driver_for("mobile_start_screen_recording", device_id)
    output = validate_recording_output(
        "mobile_start_screen_recording",
        None if args.get("output") is None else str(args.get("output")),
    )
    time_limit = validate_time_limit(
        "mobile_start_screen_recording", args.get("timeLimit")
    )
    remote_path = (
        str(output)
        if getattr(driver, "device_type", None) == "simulator"
        else f"/sdcard/pymobile-mcp-{device_id.replace(':', '_')}.mp4"
    )
    recording = await recording_state.spawn_recording(
        device_id,
        output,
        remote_path,
        lambda: driver.start_recording(remote_path, time_limit),
    )
    _observe_recording_cli(
        screenrecord_contract_argv(device_id, str(output), time_limit)
    )
    return [
        _text(
            f"Screen recording started. Output will be saved to: {recording.output_path}"
        )
    ]


async def stop_screen_recording(args: dict[str, Any]) -> list[TextContent]:
    device_id = str(args["device"])
    driver = await _driver_for("mobile_stop_screen_recording", device_id)
    recording = await recording_state.pop_recording(device_id)
    try:
        size = await driver.stop_recording(recording.process, recording.remote_path, recording.output_path)
    except Exception:
        # ensure no orphan process / remote file best-effort already handled in driver
        raise
    duration = max(0, round(__import__('time').time() - recording.started_at))
    if not recording.output_path.exists():
        return [_text(f"Recording stopped after ~{duration}s but the output file was not found at: {recording.output_path}")]
    size = recording.output_path.stat().st_size if recording.output_path.exists() else size
    return [_text(f"Recording stopped. File: {recording.output_path} ({size / (1024 * 1024):.2f} MB, ~{duration}s)")]


async def list_crashes(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_list_crashes", str(args["device"]))
    if hasattr(driver, "list_crashes"):
        crashes = await driver.list_crashes()  # type: ignore[attr-defined]
        return [_text(_json(crashes))]
    raise UnsupportedPlatformError(
        "mobile_list_crashes",
        "Android crash reports are not exposed through a reliable pure-Python/ADB source in this MVP.",
        {"platform": "android"},
    )


async def get_crash(args: dict[str, Any]) -> list[TextContent]:
    driver = await _driver_for("mobile_get_crash", str(args["device"]))
    if hasattr(driver, "get_crash"):
        content = await driver.get_crash(str(args["id"]))  # type: ignore[attr-defined]
        return [_text(content)]
    raise UnsupportedPlatformError(
        "mobile_get_crash",
        "Android crash reports are not exposed through a reliable pure-Python/ADB source in this MVP.",
        {"platform": "android", "id": str(args["id"])},
    )


async def _driver_for(tool: str, device_id: str) -> AndroidDriverLike:
    if _device_discovery is None:
        from pymobile_mcp.drivers.android import AndroidDriver, list_android_devices

        if device_id in {device.id for device in list_android_devices() if device.state == "online"}:
            driver = AndroidDriver(device_id)
            await driver.connect()
            return _remember_driver(driver)
    devices = await asyncio.to_thread(_discover_devices)
    if device_id not in {device.id for device in devices if device.state == "online"}:
        raise DeviceNotFoundError(tool, device_id)
    driver = _make_driver(device_id)
    await driver.connect()
    return _remember_driver(driver)


def _discover_devices() -> list[DeviceInfo]:
    if _device_discovery is not None:
        return _device_discovery()
    from pymobile_mcp.drivers.android import list_android_devices
    from pymobile_mcp.drivers.ios import list_ios_devices
    from pymobile_mcp.drivers.ios_simulator import list_ios_simulators

    return list_android_devices() + list_ios_devices() + list_ios_simulators()


def _make_driver(device_id: str) -> AndroidDriverLike:
    if _driver_factory is not None:
        return _driver_factory(device_id)

    devices = {device.id: device for device in _discover_devices()}
    device = devices.get(device_id)
    platform = device.platform if device is not None else "android"
    if platform == "ios":
        if device is not None and device.type == "simulator":
            from pymobile_mcp.drivers.ios_simulator import IOSSimulatorDriver

            return IOSSimulatorDriver(device_id)
        from pymobile_mcp.drivers.ios import IOSDriver

        return IOSDriver(device_id)
    from pymobile_mcp.drivers.android import AndroidDriver

    return AndroidDriver(device_id)


def _device_to_dict(device: DeviceInfo) -> dict[str, Any]:
    payload = asdict(device)
    if device.platform == "android":
        payload["type"] = "emulator"
    return payload


def _element_to_dict(element: ScreenElement) -> dict[str, Any]:
    payload = {
        "type": element.type,
        "text": element.text,
        "label": element.label,
        "name": element.name,
        "value": element.value,
        "identifier": element.identifier,
        "coordinates": asdict(element.rect),
    }
    if element.focused:
        payload["focused"] = True
    return payload


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

def _json(value: Any) -> str:
    import json

    return json.dumps(value, separators=(",", ":"))


def _number(value: float) -> str:
    return format(value, "g")

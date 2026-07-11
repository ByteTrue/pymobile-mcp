"""iOS driver via pure pymobiledevice3 (userspace tunnel + WDA service client).

No external iOS CLI runtime dependency. For iOS 17+, connects with
`establish_userspace_rsd` (no root). Talks to WebDriverAgent through
`WdaServiceClient` over the service connection, not localhost:8100.
"""

from __future__ import annotations

import asyncio
import os
from contextlib import suppress
from typing import Any
from xml.etree import ElementTree as ET

from pymobile_mcp.errors import DriverError, UnsupportedPlatformError

from .base import BaseDriver, DeviceInfo, ScreenElement, ScreenElementRect, ScreenSize

DEFAULT_WDA_PORT = int(os.environ.get("PYMOBILE_MCP_WDA_PORT", "8100"))
DEFAULT_XCTRUNNER = os.environ.get(
    "PYMOBILE_MCP_WDA_XCTRUNNER",
    "com.byte.WebDriverAgentRunner.xctrunner",
)

# Process-wide userspace tunnel: PyTCP allows only one active tunnel per process.
_PROCESS_TUNNEL: Any | None = None
_PROCESS_RSD: Any | None = None
_PROCESS_TUNNEL_DEVICE: str | None = None
_PROCESS_XCT_TASK: asyncio.Task[Any] | None = None
_PROCESS_TUNNEL_LOCK = asyncio.Lock()



def _ios_button_name(button: str) -> str:
    key = button.strip().upper()
    if key in {
        "BACK", "KEYCODE_BACK",
        "ENTER", "KEYCODE_ENTER",
        "DPAD_CENTER", "KEYCODE_DPAD_CENTER",
        "DPAD_UP", "KEYCODE_DPAD_UP",
        "DPAD_DOWN", "KEYCODE_DPAD_DOWN",
        "DPAD_LEFT", "KEYCODE_DPAD_LEFT",
        "DPAD_RIGHT", "KEYCODE_DPAD_RIGHT",
    }:
        raise UnsupportedPlatformError(
            "mobile_press_button",
            f'Button "{button}" is not supported on iOS via WDA hardware buttons.',
            {"button": button, "platform": "ios"},
        )
    mapping = {
        "HOME": "home",
        "KEYCODE_HOME": "home",
        "VOLUME_UP": "volumeUp",
        "KEYCODE_VOLUME_UP": "volumeUp",
        "VOLUME_DOWN": "volumeDown",
        "KEYCODE_VOLUME_DOWN": "volumeDown",
    }
    return mapping.get(key, button)

async def _shared_userspace_rsd(device_id: str) -> Any:
    global _PROCESS_TUNNEL, _PROCESS_RSD, _PROCESS_TUNNEL_DEVICE
    async with _PROCESS_TUNNEL_LOCK:
        if _PROCESS_RSD is not None and _PROCESS_TUNNEL_DEVICE == device_id:
            return _PROCESS_RSD
        if _PROCESS_TUNNEL is not None and _PROCESS_TUNNEL_DEVICE != device_id:
            with suppress(Exception):
                await _PROCESS_TUNNEL.aclose()
            _PROCESS_TUNNEL = None
            _PROCESS_RSD = None
            _PROCESS_TUNNEL_DEVICE = None
        from pymobiledevice3.remote.userspace_tunnel import UserspaceRsdTunnel

        tunnel = UserspaceRsdTunnel(serial=device_id)
        rsd = await tunnel.aopen()
        _PROCESS_TUNNEL = tunnel
        _PROCESS_RSD = rsd
        _PROCESS_TUNNEL_DEVICE = device_id
        return rsd


def list_ios_devices() -> list[DeviceInfo]:
    """Best-effort usbmux discovery. Safe from sync contexts."""
    try:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_list_ios_devices_async())
        # Already inside an event loop (MCP handlers). Use a worker thread.
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(_list_ios_devices_async())).result(timeout=15)
    except Exception:
        return []


async def _list_ios_devices_async() -> list[DeviceInfo]:
    from pymobiledevice3.lockdown import create_using_usbmux
    from pymobiledevice3.usbmux import list_devices

    devices: list[DeviceInfo] = []
    for device in await list_devices():
        serial = str(getattr(device, "serial", None) or getattr(device, "udid", None) or device)
        name = serial
        version = "unknown"
        try:
            lockdown = await create_using_usbmux(serial=serial)
            vals = getattr(lockdown, "all_values", {}) or {}
            name = str(vals.get("DeviceName") or serial)
            version = str(vals.get("ProductVersion") or "unknown")
        except Exception:
            pass
        devices.append(
            DeviceInfo(
                id=serial,
                name=name,
                platform="ios",
                type="simulator" if "simulator" in serial.lower() else "real",
                version=version,
                state="online",
            )
        )
    return devices


def parse_wda_source(node: dict[str, Any] | None, elements: list[ScreenElement] | None = None) -> list[ScreenElement]:
    if elements is None:
        elements = []
    if not isinstance(node, dict):
        return elements
    rect = node.get("rect") or {}
    try:
        x = float(rect.get("x", 0))
        y = float(rect.get("y", 0))
        width = float(rect.get("width", 0))
        height = float(rect.get("height", 0))
    except (TypeError, ValueError):
        x = y = width = height = 0.0
    if width > 0 and height > 0:
        label = node.get("label")
        name = node.get("name")
        value = None if node.get("value") is None else str(node.get("value"))
        identifier = node.get("rawIdentifier") or name
        # Skip pure containers without identity (keeps matrix elements useful).
        if label or name or value or identifier:
            elements.append(
                ScreenElement(
                    type=str(node.get("type") or node.get("class") or "unknown"),
                    rect=ScreenElementRect(x=x, y=y, width=width, height=height),
                    label=label,
                    name=name,
                    value=value,
                    text=label or name or value,
                    identifier=identifier,
                    focused=bool(node.get("focused") or False),
                )
            )
    for child in node.get("children") or []:
        parse_wda_source(child, elements)
    return elements


def parse_wda_source_xml(xml_text: str) -> list[ScreenElement]:
    """Parse WDA /source XML into ScreenElement list."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    elements: list[ScreenElement] = []

    def walk(el: ET.Element) -> None:
        attrib = el.attrib
        try:
            x = float(attrib.get("x", 0))
            y = float(attrib.get("y", 0))
            width = float(attrib.get("width", 0))
            height = float(attrib.get("height", 0))
        except ValueError:
            x = y = width = height = 0.0
        if width > 0 and height > 0:
            label = attrib.get("label")
            name = attrib.get("name")
            value = attrib.get("value")
            elements.append(
                ScreenElement(
                    type=el.tag or attrib.get("type") or "unknown",
                    rect=ScreenElementRect(x=x, y=y, width=width, height=height),
                    label=label,
                    name=name,
                    value=value,
                    text=label or name or value,
                    identifier=name or attrib.get("rawIdentifier"),
                    focused=str(attrib.get("focused", "false")).lower() == "true",
                )
            )
        for child in list(el):
            walk(child)

    walk(root)
    return elements


class IOSDriver(BaseDriver):
    platform = "ios"

    def __init__(self, device_id: str, wda: Any | None = None) -> None:
        # `wda` is accepted for tests (fake object with is_running / methods).
        self.device_id = device_id
        self._fake_wda = wda
        self._rsd: Any | None = None
        self._tunnel: Any | None = None
        self._client: Any | None = None
        self._session_id: str | None = None
        self._xct_task: asyncio.Task[Any] | None = None
        self._connected = False
        self._lock = asyncio.Lock()

    async def connect(self, capabilities: dict[str, Any] | None = None) -> None:
        del capabilities
        if self._fake_wda is not None:
            running = self._fake_wda.is_running() if callable(getattr(self._fake_wda, "is_running", None)) else True
            if not running:
                raise DriverError("ios", f'Fake WDA not ready for device "{self.device_id}"')
            self._connected = True
            return
        async with self._lock:
            await self._ensure_runtime_locked()
            self._connected = True

    async def disconnect(self) -> None:
        async with self._lock:
            await self._teardown_locked()
            self._connected = False

    async def screenshot(self) -> bytes:
        if self._fake_wda is not None:
            return await self._fake_call("screenshot", b"")
        await self._ensure_connected()
        assert self._client is not None
        return await self._client.get_screenshot(session_id=await self._session())

    async def get_elements_on_screen(self) -> list[ScreenElement]:
        if self._fake_wda is not None:
            return await self._fake_call("get_elements_on_screen", [])
        await self._ensure_connected()
        assert self._client is not None
        source = await self._client.get_source(session_id=await self._session())
        if isinstance(source, dict):
            root = source.get("value") if isinstance(source.get("value"), dict) else source
            return parse_wda_source(root if isinstance(root, dict) else None)
        return parse_wda_source_xml(str(source))

    async def get_screen_size(self) -> ScreenSize:
        if self._fake_wda is not None:
            return await self._fake_call("get_screen_size", ScreenSize(width=0, height=0))
        await self._ensure_connected()
        assert self._client is not None
        value = await self._client.get_window_size(session_id=await self._session())
        return ScreenSize(width=float(value.get("width", 0)), height=float(value.get("height", 0)), scale=1.0)

    async def tap(self, x: float, y: float) -> None:
        if self._fake_wda is not None:
            await self._fake_call("tap", None, x, y)
            return
        await self._ensure_connected()
        assert self._client is not None
        sid = await self._session()
        # prefer wda/tap; fall back to short swipe
        try:
            await self._client._request_json("POST", f"/session/{sid}/wda/tap", {"x": x, "y": y})
        except Exception:
            await self._client.swipe(int(x), int(y), int(x), int(y), duration=0.05, session_id=sid)

    async def double_tap(self, x: float, y: float) -> None:
        if self._fake_wda is not None:
            await self._fake_call("double_tap", None, x, y)
            return
        await self._ensure_connected()
        assert self._client is not None
        sid = await self._session()
        try:
            await self._client._request_json("POST", f"/session/{sid}/wda/doubleTap", {"x": x, "y": y})
        except Exception:
            await self.tap(x, y)
            await self.tap(x, y)

    async def long_press(self, x: float, y: float, duration: float = 0.5) -> None:
        if self._fake_wda is not None:
            await self._fake_call("long_press", None, x, y, duration)
            return
        await self._ensure_connected()
        assert self._client is not None
        sid = await self._session()
        try:
            await self._client._request_json(
                "POST",
                f"/session/{sid}/wda/touchAndHold",
                {"x": x, "y": y, "duration": duration},
            )
        except Exception:
            await self._client.swipe(int(x), int(y), int(x), int(y), duration=duration, session_id=sid)

    async def swipe(self, start_x: float, start_y: float, end_x: float, end_y: float) -> None:
        if self._fake_wda is not None:
            await self._fake_call("swipe", None, start_x, start_y, end_x, end_y)
            return
        await self._ensure_connected()
        assert self._client is not None
        await self._client.swipe(int(start_x), int(start_y), int(end_x), int(end_y), session_id=await self._session())

    async def type_keys(self, text: str, submit: bool) -> None:
        if self._fake_wda is not None:
            await self._fake_call("type_keys", None, text, submit)
            return
        await self._ensure_connected()
        assert self._client is not None
        sid = await self._session()
        await self._client.send_keys(text, session_id=sid)
        if submit:
            await self._client.send_keys("\n", session_id=sid)

    async def get_orientation(self) -> str:
        if self._fake_wda is not None:
            return await self._fake_call("get_orientation", "portrait")
        await self._ensure_connected()
        assert self._client is not None
        sid = await self._session()
        data = await self._client._request_json("GET", f"/session/{sid}/orientation", None)
        value = str(data.get("value") or "PORTRAIT").upper()
        return "landscape" if "LANDSCAPE" in value else "portrait"

    async def set_orientation(self, orientation: str) -> None:
        if self._fake_wda is not None:
            await self._fake_call("set_orientation", None, orientation)
            return
        await self._ensure_connected()
        assert self._client is not None
        sid = await self._session()
        value = "LANDSCAPE" if orientation == "landscape" else "PORTRAIT"
        await self._client._request_json("POST", f"/session/{sid}/orientation", {"orientation": value})


    async def press_button(self, button: str) -> None:
        """Accept Android KEYCODE_* or raw names; map to WDA button names."""
        if self._fake_wda is not None:
            await self._fake_call("press_button", None, button)
            return
        await self._ensure_connected()
        assert self._client is not None
        name = _ios_button_name(button)
        await self._client.press_button(name, session_id=await self._session())

    async def open_url(self, url: str) -> None:
        if self._fake_wda is not None:
            await self._fake_call("open_url", None, url)
            return
        await self._ensure_connected()
        assert self._client is not None
        sid = await self._session()
        last_exc: Exception | None = None
        for path in (f"/session/{sid}/url", f"/session/{sid}/wda/url"):
            try:
                await self._client._request_json("POST", path, {"url": url})
                return
            except Exception as exc:
                last_exc = exc
                msg = str(exc)
                if "Locked" in msg or "not, or could not be, unlocked" in msg:
                    raise DriverError(
                        "ios",
                        "iPhone is locked; unlock it to open URLs.",
                        {"url": url, "device": self.device_id},
                    ) from exc
        # Fallback: launch Safari with URL argument via a dedicated session.
        try:
            caps = {
                "bundleId": "com.apple.mobilesafari",
                "arguments": [url],
                "shouldWaitForQuiescence": False,
            }
            payload = {"capabilities": {"alwaysMatch": caps}, "desiredCapabilities": caps}
            await self._client._request_json("POST", "/session", payload)
            return
        except Exception as exc:
            last_exc = exc
            msg = str(exc)
            if "Locked" in msg or "not, or could not be, unlocked" in msg:
                raise DriverError(
                    "ios",
                    "iPhone is locked; unlock it to open URLs.",
                    {"url": url, "device": self.device_id},
                ) from exc
        raise DriverError("ios", f"Failed to open url via WDA: {last_exc}", {"url": url}) from last_exc

    async def list_apps(self):
        raise UnsupportedPlatformError(
            "mobile_list_apps",
            "iOS app listing via pure pymobiledevice3/WDA is not implemented yet.",
            {"platform": "ios"},
        )

    async def launch_app(self, package_name: str, locale: str | None = None) -> None:
        del package_name, locale
        raise UnsupportedPlatformError(
            "mobile_launch_app",
            "iOS app launch via pure pymobiledevice3/WDA is not implemented yet.",
            {"platform": "ios"},
        )

    async def terminate_app(self, package_name: str) -> None:
        del package_name
        raise UnsupportedPlatformError(
            "mobile_terminate_app",
            "iOS app terminate via pure pymobiledevice3/WDA is not implemented yet.",
            {"platform": "ios"},
        )

    async def install_app(self, path: str) -> None:
        del path
        raise UnsupportedPlatformError(
            "mobile_install_app",
            "iOS app install via pure pymobiledevice3/WDA is not implemented yet.",
            {"platform": "ios"},
        )

    async def uninstall_app(self, package_name: str) -> None:
        del package_name
        raise UnsupportedPlatformError(
            "mobile_uninstall_app",
            "iOS app uninstall via pure pymobiledevice3/WDA is not implemented yet.",
            {"platform": "ios"},
        )

    async def start_recording(self, remote_path: str, time_limit: int | None = None):
        del remote_path, time_limit
        raise UnsupportedPlatformError(
            "mobile_start_screen_recording",
            "iOS screen recording is not available through pure pymobiledevice3/WDA yet.",
            {"platform": "ios"},
        )

    async def stop_recording(self, process: Any, remote_path: str, local_path: Any) -> int:
        del process, remote_path, local_path
        raise UnsupportedPlatformError(
            "mobile_stop_screen_recording",
            "iOS screen recording is not available through pure pymobiledevice3/WDA yet.",
            {"platform": "ios"},
        )

    async def list_crashes(self):
        raise UnsupportedPlatformError(
            "mobile_list_crashes",
            "iOS crash report listing is not available through pure pymobiledevice3/WDA yet.",
            {"platform": "ios"},
        )

    async def get_crash(self, crash_id: str) -> str:
        del crash_id
        raise UnsupportedPlatformError(
            "mobile_get_crash",
            "iOS crash report reading is not available through pure pymobiledevice3/WDA yet.",
            {"platform": "ios"},
        )

    async def _ensure_connected(self) -> None:
        if self._fake_wda is not None:
            if not self._connected:
                await self.connect()
            return
        if not self._connected or self._client is None or self._rsd is None:
            await self.connect()

    async def _session(self) -> str:
        assert self._client is not None
        if self._session_id:
            return self._session_id
        self._session_id = await self._client.start_session()
        return self._session_id

    async def _ensure_runtime_locked(self) -> None:
        from pymobiledevice3.services.wda import WdaServiceClient

        if self._rsd is None:
            try:
                self._rsd = await _shared_userspace_rsd(self.device_id)
            except Exception as exc:
                raise DriverError(
                    "ios",
                    f'Failed to establish pymobiledevice3 userspace tunnel for "{self.device_id}": {exc}',
                    {"device": self.device_id},
                ) from exc
        if self._client is None:
            self._client = WdaServiceClient(service_provider=self._rsd, port=DEFAULT_WDA_PORT, timeout=20.0)
        if not await self._wda_ready():
            await self._start_xctrunner_locked()
            if not await self._wait_wda_ready(timeout=90.0):
                raise DriverError(
                    "ios",
                    f'WDA is not ready for device "{self.device_id}". '
                    f"Install WebDriverAgent runner ({DEFAULT_XCTRUNNER}) and ensure Developer Mode is enabled. "
                    "Uses pure pymobiledevice3 userspace tunnel (no go-ios, no root).",
                    {"device": self.device_id, "xctrunner": DEFAULT_XCTRUNNER, "wda_port": DEFAULT_WDA_PORT},
                )

    async def _wda_ready(self) -> bool:
        if self._client is None:
            return False
        try:
            status = await self._client.get_status()
            value = status.get("value") or {}
            return bool(value.get("ready") is True or value.get("message") or status.get("sessionId"))
        except Exception:
            return False

    async def _wait_wda_ready(self, timeout: float) -> bool:
        deadline = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < deadline:
            if await self._wda_ready():
                return True
            if self._xct_task is not None and self._xct_task.done():
                exc = self._xct_task.exception()
                if exc is not None:
                    raise DriverError("ios", f"WDA XCUITest runner failed: {exc}", {"device": self.device_id}) from exc
            await asyncio.sleep(0.4)
        return False

    async def _start_xctrunner_locked(self) -> None:
        global _PROCESS_XCT_TASK
        if _PROCESS_XCT_TASK is not None and not _PROCESS_XCT_TASK.done():
            self._xct_task = _PROCESS_XCT_TASK
            return
        assert self._rsd is not None
        from pymobiledevice3.services.dvt.testmanaged.xcuitest import TestConfig, XCUITestService

        try:
            cfg = await TestConfig.create_for(self._rsd, runner_bundle_id=DEFAULT_XCTRUNNER)
            service = XCUITestService(self._rsd)
            _PROCESS_XCT_TASK = asyncio.create_task(service.run(cfg), name=f"wda-xctrunner-{self.device_id}")
            self._xct_task = _PROCESS_XCT_TASK
        except Exception as exc:
            raise DriverError(
                "ios",
                f"Failed to start WDA XCUITest runner {DEFAULT_XCTRUNNER}: {exc}",
                {"device": self.device_id, "xctrunner": DEFAULT_XCTRUNNER},
            ) from exc

    async def _teardown_locked(self) -> None:
        if self._xct_task is not None:
            self._xct_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._xct_task
            self._xct_task = None
        self._session_id = None
        # Keep process-wide userspace tunnel alive for subsequent MCP calls.
        self._client = None
        self._rsd = None

    async def _fake_call(self, name: str, default: Any, *args: Any) -> Any:
        method = getattr(self._fake_wda, name, None)
        if method is None:
            return default
        result = method(*args)
        if asyncio.iscoroutine(result):
            return await result
        return result

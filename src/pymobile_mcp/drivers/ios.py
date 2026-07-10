"""iOS driver via pymobiledevice3 discovery + WebDriverAgent HTTP client."""

from __future__ import annotations

import asyncio
import base64
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pymobile_mcp.errors import DriverError

from .base import BaseDriver, DeviceInfo, ScreenElement, ScreenElementRect, ScreenSize

DEFAULT_WDA_HOST = os.environ.get("PYMOBILE_MCP_WDA_HOST", "127.0.0.1")
DEFAULT_WDA_PORT = int(os.environ.get("PYMOBILE_MCP_WDA_PORT", "8100"))


def list_ios_devices() -> list[DeviceInfo]:
    try:
        return asyncio.run(_list_ios_devices_async())
    except Exception:
        # usbmux/lockdown unavailable or not paired — discovery stays empty, not a hard crash
        return []


async def _list_ios_devices_async() -> list[DeviceInfo]:
    from pymobiledevice3.usbmux import list_devices

    devices: list[DeviceInfo] = []
    for device in await list_devices():
        serial = getattr(device, "serial", None) or getattr(device, "udid", None) or str(device)
        connection_type = str(getattr(device, "connection_type", "") or "").lower()
        is_network = "network" in connection_type
        devices.append(
            DeviceInfo(
                id=str(serial),
                name=str(serial),
                platform="ios",
                type="simulator" if "simulator" in str(serial).lower() else "real",
                version="unknown",
                state="online",
            )
        )
        if is_network:
            # keep name as serial; type already real
            pass
    return devices


class WdaClient:
    def __init__(self, host: str = DEFAULT_WDA_HOST, port: int = DEFAULT_WDA_PORT) -> None:
        self.host = host
        self.port = port

    @property
    def base(self) -> str:
        return f"http://{self.host}:{self.port}"

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = Request(
            f"{self.base}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"} if body is not None else {},
        )
        try:
            with urlopen(req, timeout=30) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise DriverError("ios", f"WDA {method} {path} failed: HTTP {exc.code} {detail}") from exc
        except URLError as exc:
            raise DriverError(
                "ios",
                f"WDA not reachable at {self.base}: {exc.reason}. "
                "Start WebDriverAgent and set PYMOBILE_MCP_WDA_HOST/PORT if needed.",
            ) from exc

    def is_running(self) -> bool:
        try:
            payload = self._request("GET", "/status")
        except DriverError:
            return False
        value = payload.get("value") or {}
        return bool(value.get("ready") is True or payload.get("sessionId") or value.get("message"))

    def create_session(self) -> str:
        payload = self._request(
            "POST",
            "/session",
            {"capabilities": {"alwaysMatch": {"platformName": "iOS"}}},
        )
        value = payload.get("value") or {}
        session_id = value.get("sessionId") or payload.get("sessionId")
        if not session_id:
            raise DriverError("ios", f"Invalid WDA session response: {payload}")
        return str(session_id)

    def delete_session(self, session_id: str) -> None:
        try:
            self._request("DELETE", f"/session/{session_id}")
        except DriverError:
            pass

    def screenshot_png(self) -> bytes:
        payload = self._request("GET", "/screenshot")
        value = payload.get("value")
        if not value:
            raise DriverError("ios", "WDA screenshot returned empty value")
        return base64.b64decode(value)

    def screen_size(self) -> ScreenSize:
        session_id = self.create_session()
        try:
            payload = self._request("GET", f"/session/{session_id}/wda/screen")
            value = payload.get("value") or {}
            size = value.get("screenSize") or value
            return ScreenSize(
                width=int(size["width"]),
                height=int(size["height"]),
                scale=float(value.get("scale") or 1.0),
            )
        finally:
            self.delete_session(session_id)

    def page_source_tree(self) -> dict[str, Any]:
        payload = self._request("GET", "/source/?format=json")
        return payload

    def orientation(self) -> str:
        session_id = self.create_session()
        try:
            payload = self._request("GET", f"/session/{session_id}/orientation")
            value = str(payload.get("value") or "").upper()
            return "landscape" if "LANDSCAPE" in value else "portrait"
        finally:
            self.delete_session(session_id)

    def set_orientation(self, orientation: str) -> None:
        session_id = self.create_session()
        try:
            value = "LANDSCAPE" if orientation == "landscape" else "PORTRAIT"
            self._request("POST", f"/session/{session_id}/orientation", {"orientation": value})
        finally:
            self.delete_session(session_id)

    def tap(self, x: float, y: float) -> None:
        session_id = self.create_session()
        try:
            self._request("POST", f"/session/{session_id}/actions", _pointer_tap(x, y))
        finally:
            self.delete_session(session_id)

    def double_tap(self, x: float, y: float) -> None:
        session_id = self.create_session()
        try:
            self._request("POST", f"/session/{session_id}/wda/doubleTap", {"x": x, "y": y})
        finally:
            self.delete_session(session_id)

    def long_press(self, x: float, y: float, duration: float) -> None:
        session_id = self.create_session()
        try:
            self._request(
                "POST",
                f"/session/{session_id}/wda/touchAndHold",
                {"x": x, "y": y, "duration": duration},
            )
        finally:
            self.delete_session(session_id)

    def swipe(self, start_x: float, start_y: float, end_x: float, end_y: float) -> None:
        session_id = self.create_session()
        try:
            self._request(
                "POST",
                f"/session/{session_id}/actions",
                _pointer_swipe(start_x, start_y, end_x, end_y),
            )
        finally:
            self.delete_session(session_id)

    def type_keys(self, text: str) -> None:
        session_id = self.create_session()
        try:
            self._request("POST", f"/session/{session_id}/wda/keys", {"value": [text]})
        finally:
            self.delete_session(session_id)


class IOSDriver(BaseDriver):
    platform = "ios"

    def __init__(self, device_id: str, wda: WdaClient | None = None) -> None:
        self.device_id = device_id
        self._wda = wda or WdaClient()
        self._connected = False

    async def connect(self, capabilities: dict[str, Any] | None = None) -> None:
        del capabilities
        running = await asyncio.to_thread(self._wda.is_running)
        if not running:
            raise DriverError(
                "ios",
                f'WDA is not ready for device "{self.device_id}" at {self._wda.base}. '
                "Install/start WebDriverAgent, ensure pymobiledevice3 tunnel/forward if needed, "
                "and set PYMOBILE_MCP_WDA_HOST/PORT.",
                {"device": self.device_id, "wda": self._wda.base},
            )
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def screenshot(self) -> bytes:
        await self._ensure_connected()
        return await asyncio.to_thread(self._wda.screenshot_png)

    async def get_elements_on_screen(self) -> list[ScreenElement]:
        await self._ensure_connected()
        tree = await asyncio.to_thread(self._wda.page_source_tree)
        root = tree.get("value") if isinstance(tree, dict) else None
        if not isinstance(root, dict):
            return []
        return parse_wda_source(root)

    async def get_screen_size(self) -> ScreenSize:
        await self._ensure_connected()
        return await asyncio.to_thread(self._wda.screen_size)

    async def tap(self, x: float, y: float) -> None:
        await self._ensure_connected()
        await asyncio.to_thread(self._wda.tap, x, y)

    async def double_tap(self, x: float, y: float) -> None:
        await self._ensure_connected()
        await asyncio.to_thread(self._wda.double_tap, x, y)

    async def long_press(self, x: float, y: float, duration: float = 0.5) -> None:
        await self._ensure_connected()
        await asyncio.to_thread(self._wda.long_press, x, y, duration)

    async def swipe(self, start_x: float, start_y: float, end_x: float, end_y: float) -> None:
        await self._ensure_connected()
        await asyncio.to_thread(self._wda.swipe, start_x, start_y, end_x, end_y)

    async def type_keys(self, text: str, submit: bool) -> None:
        await self._ensure_connected()
        await asyncio.to_thread(self._wda.type_keys, text)
        if submit:
            await asyncio.to_thread(self._wda.type_keys, "\n")

    async def get_orientation(self) -> str:
        await self._ensure_connected()
        return await asyncio.to_thread(self._wda.orientation)

    async def set_orientation(self, orientation: str) -> None:
        await self._ensure_connected()
        await asyncio.to_thread(self._wda.set_orientation, orientation)

    async def _ensure_connected(self) -> None:
        if not self._connected:
            await self.connect()


def parse_wda_source(node: dict[str, Any]) -> list[ScreenElement]:
    elements: list[ScreenElement] = []
    _collect_wda_elements(node, elements)
    return elements


def _collect_wda_elements(node: dict[str, Any], out: list[ScreenElement]) -> None:
    rect = node.get("rect") or {}
    try:
        element_rect = ScreenElementRect(
            x=int(rect.get("x", 0)),
            y=int(rect.get("y", 0)),
            width=int(rect.get("width", 0)),
            height=int(rect.get("height", 0)),
        )
    except (TypeError, ValueError):
        element_rect = None

    label = node.get("label")
    name = node.get("name")
    value = node.get("value")
    identifier = node.get("rawIdentifier") or node.get("identifier")
    visible = str(node.get("isVisible", "1")) != "0"
    if element_rect is not None and visible and (label or name or value or identifier):
        out.append(
            ScreenElement(
                type=str(node.get("type") or "XCUIElement"),
                rect=element_rect,
                label=None if label is None else str(label),
                text=None if value is None else str(value),
                name=None if name is None else str(name),
                value=None if value is None else str(value),
                identifier=None if identifier is None else str(identifier),
                focused=None,
            )
        )

    for child in node.get("children") or []:
        if isinstance(child, dict):
            _collect_wda_elements(child, out)


def _pointer_tap(x: float, y: float) -> dict[str, Any]:
    return {
        "actions": [
            {
                "type": "pointer",
                "id": "finger1",
                "parameters": {"pointerType": "touch"},
                "actions": [
                    {"type": "pointerMove", "duration": 0, "x": x, "y": y},
                    {"type": "pointerDown", "button": 0},
                    {"type": "pointerUp", "button": 0},
                ],
            }
        ]
    }


def _pointer_swipe(start_x: float, start_y: float, end_x: float, end_y: float) -> dict[str, Any]:
    return {
        "actions": [
            {
                "type": "pointer",
                "id": "finger1",
                "parameters": {"pointerType": "touch"},
                "actions": [
                    {"type": "pointerMove", "duration": 0, "x": start_x, "y": start_y},
                    {"type": "pointerDown", "button": 0},
                    {"type": "pointerMove", "duration": 500, "x": end_x, "y": end_y},
                    {"type": "pointerUp", "button": 0},
                ],
            }
        ]
    }

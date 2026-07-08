"""Minimal driver contract for future platform implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    id: str
    name: str
    platform: Literal["android", "ios"]
    type: Literal["real", "emulator", "simulator"]
    version: str
    state: Literal["online", "offline"]


@dataclass(frozen=True, slots=True)
class ScreenSize:
    width: int
    height: int
    scale: float = 1.0


@dataclass(frozen=True, slots=True)
class ScreenElementRect:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class ScreenElement:
    type: str
    rect: ScreenElementRect
    label: str | None = None
    text: str | None = None
    name: str | None = None
    value: str | None = None
    identifier: str | None = None
    focused: bool | None = None


@dataclass(frozen=True, slots=True)
class AppInfo:
    package_name: str
    app_name: str
    version: str | None = None


class BaseDriver(ABC):
    device_id: str
    platform: Literal["android", "ios"]

    @abstractmethod
    async def connect(self, capabilities: dict[str, Any] | None = None) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    async def screenshot(self) -> bytes: ...

    @abstractmethod
    async def get_elements_on_screen(self) -> list[ScreenElement]: ...

    @abstractmethod
    async def get_screen_size(self) -> ScreenSize: ...

"""Approved remote-fleet runtime exception handlers."""

from __future__ import annotations

from typing import Any, Callable

from pymobile_mcp.errors import ToolError


MESSAGE = (
    "mobilecli is not available or not working properly. Please review the documentation at "
    "https://github.com/mobile-next/mobile-mcp/wiki for installation instructions"
)


def register_fleet_handlers(register: Callable[[str, Callable[[dict[str, Any]], Any]], None]) -> None:
    register("mobile_list_remote_devices", unavailable)
    register("mobile_allocate_remote_device", unavailable)
    register("mobile_release_remote_device", unavailable)


async def unavailable(args: dict[str, Any]) -> list[Any]:
    del args
    raise ToolError("fleet_unavailable", "remote_fleet", MESSAGE)

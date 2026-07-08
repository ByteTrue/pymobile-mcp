"""Structured tool errors."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ToolError(Exception):
    code: str
    tool: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(
            {
                "status": "error",
                "code": self.code,
                "tool": self.tool,
                "message": self.message,
                "details": self.details,
            },
            sort_keys=True,
        )


class NotImplementedToolError(ToolError):
    def __init__(self, tool: str) -> None:
        super().__init__(
            code="not_implemented",
            tool=tool,
            message=f"{tool} is registered but not implemented yet.",
        )


class UnsupportedPlatformError(ToolError):
    def __init__(self, tool: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__("unsupported_platform", tool, message, details or {})


class DeviceNotFoundError(ToolError):
    def __init__(self, tool: str, device: str) -> None:
        super().__init__(
            "device_not_found",
            tool,
            f'Device "{device}" not found. Use mobile_list_available_devices to see available devices.',
            {"device": device},
        )


class InvalidArgumentError(ToolError):
    def __init__(self, tool: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__("invalid_argument", tool, message, details or {})


class DriverError(ToolError):
    def __init__(self, tool: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__("driver_error", tool, message, details or {})

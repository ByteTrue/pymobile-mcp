"""Shared parsers and timeout guard for iOS live smoke scripts."""

from __future__ import annotations

import asyncio
import json
import os
import re
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

_ACTIONABLE_SUFFIX = "Please fix the issue and try again."


def text(content: Any) -> str:
    if not content or content[0].type != "text":
        raise ValueError("expected text tool content")
    return content[0].text


def json_object(content: Any) -> dict[str, Any]:
    value = json.loads(text(content))
    if not isinstance(value, dict):
        raise ValueError("expected JSON object tool content")
    return value


def json_array(content: Any) -> list[Any]:
    value = json.loads(text(content))
    if not isinstance(value, list):
        raise ValueError("expected JSON array tool content")
    return value


def screen_size(content: Any) -> dict[str, int]:
    match = re.fullmatch(r"Screen size is (\d+)x(\d+) pixels", text(content))
    if match is None:
        raise ValueError(text(content))
    return {"width": int(match.group(1)), "height": int(match.group(2))}


def elements(content: Any) -> list[dict[str, Any]]:
    prefix = "Found these elements on screen: "
    value = text(content)
    if not value.startswith(prefix):
        raise ValueError(value)
    parsed = json.loads(value[len(prefix) :])
    if not isinstance(parsed, list):
        raise ValueError(value)
    return parsed


def apps(content: Any) -> list[dict[str, str]]:
    prefix = "Found these apps on device: "
    value = text(content)
    if not value.startswith(prefix):
        raise ValueError(value)
    return [
        {"appName": name.strip(), "packageName": package}
        for name, package in re.findall(r"([^,]+) \(([^)]+)\)", value[len(prefix) :])
    ]


def saved_path(content: Any) -> Path:
    prefix = "Screenshot saved to: "
    value = text(content)
    if not value.startswith(prefix):
        raise ValueError(value)
    return Path(value[len(prefix) :])


def error_text(content: Any) -> str | None:
    if not content or content[0].type != "text":
        return None
    value = content[0].text
    if value.startswith(("Error:", "MCP error")) or value.endswith(_ACTIONABLE_SUFFIX):
        return value
    return None


def is_unsupported(error: str | None) -> bool:
    value = (error or "").lower()
    return "not supported" in value or "not available" in value


def is_locked(error: str | None) -> bool:
    return "locked" in (error or "").lower()


async def run_with_timeout(
    main: Callable[[], Awaitable[int]], *, name: str = "iOS live smoke"
) -> int:
    timeout = float(os.environ.get("PYMOBILE_MCP_LIVE_TIMEOUT", "180"))
    try:
        return await asyncio.wait_for(main(), timeout=timeout)
    except asyncio.TimeoutError:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": f"{name} timed out",
                    "timeout_seconds": timeout,
                },
                indent=2,
            )
        )
        return 2

"""Host-side validation for Android app/system tools."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pymobile_mcp.errors import InvalidArgumentError

SAFE_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
SAFE_VIDEO_EXTENSIONS = {".mp4"}
BUTTON_KEYCODES = {
    "BACK": "KEYCODE_BACK",
    "HOME": "KEYCODE_HOME",
    "VOLUME_UP": "KEYCODE_VOLUME_UP",
    "VOLUME_DOWN": "KEYCODE_VOLUME_DOWN",
    "ENTER": "KEYCODE_ENTER",
    "DPAD_CENTER": "KEYCODE_DPAD_CENTER",
    "DPAD_UP": "KEYCODE_DPAD_UP",
    "DPAD_DOWN": "KEYCODE_DPAD_DOWN",
    "DPAD_LEFT": "KEYCODE_DPAD_LEFT",
    "DPAD_RIGHT": "KEYCODE_DPAD_RIGHT",
}
ORIENTATIONS = {"portrait", "landscape"}


def validate_url(tool: str, url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme.lower() in {"http", "https"} and parsed.netloc:
        return url
    if os.environ.get("MOBILEMCP_ALLOW_UNSAFE_URLS") == "1":
        return url
    raise InvalidArgumentError(
        tool,
        "Only http:// and https:// URLs are allowed. Set MOBILEMCP_ALLOW_UNSAFE_URLS=1 to allow other URL schemes.",
        {"url": url},
    )


def validate_button(tool: str, button: str) -> str:
    if button not in BUTTON_KEYCODES:
        raise InvalidArgumentError(tool, f'Button "{button}" is not supported', {"button": button, "allowed": sorted(BUTTON_KEYCODES)})
    return BUTTON_KEYCODES[button]


def validate_orientation(tool: str, orientation: str) -> str:
    if orientation not in ORIENTATIONS:
        raise InvalidArgumentError(
            tool,
            f'Orientation "{orientation}" is not supported',
            {"orientation": orientation, "allowed": sorted(ORIENTATIONS)},
        )
    return orientation


def validate_output_path(tool: str, save_to: str, *, allowed_extensions: set[str] | None = None, field: str = "saveTo") -> Path:
    path = Path(save_to).expanduser()
    extensions = allowed_extensions or SAFE_IMAGE_EXTENSIONS
    if path.suffix.lower() not in extensions:
        raise InvalidArgumentError(
            tool,
            f"Filename must end with one of: {', '.join(sorted(extensions))}",
            {field: save_to, "allowed_extensions": sorted(extensions)},
        )

    # Resolve relative paths against cwd. Reject absolute paths outside cwd/temp.
    candidate = path if path.is_absolute() else (Path.cwd() / path)
    resolved = candidate.resolve(strict=False)
    allowed_roots = [Path.cwd().resolve(), Path(tempfile.gettempdir()).resolve()]
    if not any(_is_within(resolved, root) for root in allowed_roots):
        raise InvalidArgumentError(
            tool,
            f"{field} must resolve under the current working directory or system temp directory",
            {field: save_to, "resolved": str(resolved)},
        )
    return resolved


def validate_recording_output(tool: str, output: str | None) -> Path:
    if output is None:
        return Path(tempfile.gettempdir()).resolve() / f"pymobile-mcp-{os.getpid()}-{int(__import__('time').time())}.mp4"
    return validate_output_path(tool, output, allowed_extensions=SAFE_VIDEO_EXTENSIONS, field="output")


def validate_time_limit(tool: str, time_limit: Any | None) -> int | None:
    if time_limit is None:
        return None
    if isinstance(time_limit, bool) or not isinstance(time_limit, (int, float)):
        raise InvalidArgumentError(tool, "timeLimit must be a positive number", {"timeLimit": time_limit})
    value = int(time_limit)
    if value <= 0:
        raise InvalidArgumentError(tool, "timeLimit must be > 0", {"timeLimit": time_limit})
    return value


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False

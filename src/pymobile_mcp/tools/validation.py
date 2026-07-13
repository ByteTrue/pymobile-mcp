"""Host-side validation for Android app/system tools."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

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


def validate_package_name(tool: str, package_name: str) -> str:
    import re

    if re.fullmatch(r"[a-zA-Z0-9._]+", package_name) is None:
        raise InvalidArgumentError(tool, f'Invalid package name: "{package_name}"', {"packageName": package_name})
    return package_name


def validate_locale(tool: str, locale: str) -> str:
    import re

    if re.fullmatch(r"[a-zA-Z0-9,\- ]+", locale) is None:
        raise InvalidArgumentError(tool, f'Invalid locale: "{locale}"', {"locale": locale})
    return locale


def validate_url(tool: str, url: str) -> str:
    if url.startswith(("http://", "https://")):
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
        ordered = [ext for ext in (".png", ".jpg", ".jpeg", ".mp4") if ext in extensions]
        public_tool = tool.removeprefix("mobile_")
        raise InvalidArgumentError(
            tool,
            f'{public_tool} requires a {", ".join(ordered)} file extension, got: "{path.suffix.lower() or "(none)"}"',
            {field: save_to, "allowed_extensions": ordered},
        )

    # Resolve relative paths against cwd. Reject absolute paths outside cwd/temp.
    candidate = path if path.is_absolute() else (Path.cwd() / path)
    resolved = candidate.resolve(strict=False)
    allowed_roots = [Path.cwd().resolve(), Path(tempfile.gettempdir()).resolve(), Path("/tmp").resolve(), Path("/private/tmp").resolve()]
    if not any(_is_within(resolved, root) for root in allowed_roots):
        raise InvalidArgumentError(
            tool,
            f'"{resolved.parent}" is not in the list of allowed directories. Allowed directories include the current directory and the temp directory on this host.',
            {field: save_to, "resolved": str(resolved)},
        )
    return path if path.is_absolute() else resolved


def validate_recording_output(tool: str, output: str | None) -> Path:
    if output is None:
        return Path(tempfile.gettempdir()).resolve() / f"screen-recording-{int(__import__('time').time() * 1000)}.mp4"
    return validate_output_path(tool, output, allowed_extensions=SAFE_VIDEO_EXTENSIONS, field="output")


def validate_time_limit(tool: str, time_limit: Any | None) -> int | float | None:
    if time_limit is None:
        return None
    try:
        value = float(time_limit)
    except (TypeError, ValueError) as exc:
        raise InvalidArgumentError(tool, "timeLimit must be a finite number", {"timeLimit": time_limit}) from exc
    if not __import__("math").isfinite(value):
        raise InvalidArgumentError(tool, "timeLimit must be a finite number", {"timeLimit": time_limit})
    return int(value) if value.is_integer() else value


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False

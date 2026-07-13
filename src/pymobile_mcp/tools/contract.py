"""Formatting primitives for the public mobile-mcp wire contract."""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from mcp.types import ImageContent, TextContent


ACTIONABLE_SUFFIX = ". Please fix the issue and try again."


def text(value: str | Any) -> TextContent:
    rendered = value if isinstance(value, str) else json.dumps(value, separators=(",", ":"))
    return TextContent(type="text", text=rendered)


def actionable(message: str) -> TextContent:
    return text(f"{message}{ACTIONABLE_SUFFIX}")


def unexpected(message: str) -> TextContent:
    return text(f"Error: {message}")


def screenshot(data: bytes, scale: float) -> ImageContent:
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Not a valid PNG file")
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    if width <= 0 or height <= 0:
        raise ValueError("Screenshot is invalid. Please try again.")
    if not _scaling_available():
        return ImageContent(type="image", data=_base64(data), mimeType="image/png")
    resized = _resize_jpeg(data, math.floor(width / scale))
    return ImageContent(type="image", data=_base64(resized), mimeType="image/jpeg")


def _sips_available() -> bool:
    return os.uname().sysname == "Darwin" and Path("/usr/bin/sips").is_file()


def _scaling_available() -> bool:
    return shutil.which("magick") is not None or _sips_available()


def _run_sips(data: bytes, width: int) -> bytes:
    with tempfile.TemporaryDirectory(prefix="image-") as directory:
        input_path = Path(directory) / "input"
        output_path = Path(directory) / "output.jpg"
        input_path.write_bytes(data)
        subprocess.run(
            ["/usr/bin/sips", "-s", "format", "jpeg", "-s", "formatOptions", "high", "-Z", str(width), "--out", str(output_path), str(input_path)],
            check=True,
            capture_output=True,
        )
        return output_path.read_bytes()


def _run_magick(data: bytes, width: int) -> bytes:
    magick = shutil.which("magick")
    if magick is None:
        raise RuntimeError("Image scaling unavailable (requires Sips or ImageMagick).")
    completed = subprocess.run([magick, "-", "-resize", f"{width}x", "-quality", "75", "jpg:-"], input=data, capture_output=True, check=False)
    if completed.returncode != 0 or not completed.stdout:
        raise RuntimeError("Image scaling unavailable (requires Sips or ImageMagick).")
    return completed.stdout


def _resize_jpeg(data: bytes, width: int) -> bytes:
    if _sips_available():
        try:
            return _run_sips(data, width)
        except Exception:
            pass
    return _run_magick(data, width)


def _base64(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode("ascii")

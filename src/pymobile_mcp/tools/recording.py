"""In-process Android screen recording state."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pymobile_mcp.errors import ToolError


@dataclass(slots=True)
class ActiveRecording:
    device_id: str
    output_path: Path
    started_at: float
    remote_path: str
    process: Any


_active: dict[str, ActiveRecording] = {}
_locks: dict[str, asyncio.Lock] = {}


def reset_recording_state_for_tests() -> None:
    _active.clear()
    _locks.clear()


def _lock_for(device_id: str) -> asyncio.Lock:
    lock = _locks.get(device_id)
    if lock is None:
        lock = asyncio.Lock()
        _locks[device_id] = lock
    return lock


async def start_recording(device_id: str, output_path: Path, process: Any, remote_path: str) -> ActiveRecording:
    async with _lock_for(device_id):
        if device_id in _active:
            raise ToolError(
                "already_recording",
                "mobile_start_screen_recording",
                f'Device "{device_id}" already has an active screen recording.',
                {"device": device_id, "output": str(_active[device_id].output_path)},
            )
        recording = ActiveRecording(
            device_id=device_id,
            output_path=output_path,
            started_at=time.time(),
            remote_path=remote_path,
            process=process,
        )
        _active[device_id] = recording
        return recording


async def pop_recording(device_id: str) -> ActiveRecording:
    async with _lock_for(device_id):
        recording = _active.pop(device_id, None)
        if recording is None:
            raise ToolError(
                "no_active_recording",
                "mobile_stop_screen_recording",
                f'No active screen recording for device "{device_id}".',
                {"device": device_id},
            )
        return recording


def get_recording(device_id: str) -> ActiveRecording | None:
    return _active.get(device_id)

"""Run the existing live smoke set once for every device currently online."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import threading
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = {
    "android": (
        "android_live_smoke.py",
        "android_app_system_live_smoke.py",
        "crash_tools_live_smoke.py",
        "android_recording_crash_live_smoke.py",
    ),
    "ios": (
        "ios_pmd3_wda_live_smoke.py",
        "ios_system_helpers_live_smoke.py",
        "ios_app_lifecycle_live_smoke.py",
        "ios_app_recording_crash_live_smoke.py",
    ),
}

_PROGRESS_LOCK = threading.Lock()


def _online_devices(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        device
        for device in payload.get("devices", [])
        if device.get("state") == "online" and device.get("platform") in SCRIPTS
    ]


def _aggregate(results: Sequence[Mapping[str, Any]]) -> tuple[str, int]:
    statuses = {result["status"] for result in results}
    if "failed" in statuses:
        return "failed", 1
    if not results or "blocked" in statuses:
        return "blocked", 2
    return "passed", 0


def _child_env(
    device: Mapping[str, Any], base_env: Mapping[str, str]
) -> dict[str, str]:
    env = dict(base_env)
    platform = device["platform"]
    device_id = device["id"]

    for name in (
        "PYMOBILE_MCP_ANDROID_DEVICE",
        "PYMOBILE_MCP_IOS_DEVICE",
        "PYMOBILE_MCP_ANDROID_ACTIONS",
        "PYMOBILE_MCP_IOS_ACTIONS",
        "PYMOBILE_MCP_ANDROID_DESTRUCTIVE",
        "PYMOBILE_MCP_IOS_DESTRUCTIVE",
    ):
        env.pop(name, None)

    env["PYMOBILE_MCP_DEVICE"] = device_id
    env[f"PYMOBILE_MCP_{platform.upper()}_DEVICE"] = device_id
    if base_env.get("PYMOBILE_MCP_ACTIONS") == "1":
        env[f"PYMOBILE_MCP_{platform.upper()}_ACTIONS"] = "1"
    return env


def _as_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value or ""


def _emit_progress(event: str, payload: Mapping[str, Any]) -> None:
    with _PROGRESS_LOCK:
        print(
            json.dumps({"event": event, **payload}, sort_keys=True),
            file=sys.stderr,
            flush=True,
        )


def _run_child(
    device: Mapping[str, Any],
    script: str,
    *,
    timeout: float,
    base_env: Mapping[str, str],
) -> dict[str, Any]:
    common = {
        "device": device["id"],
        "platform": device["platform"],
        "script": script,
    }
    command = [sys.executable, str(ROOT / "tests" / script)]
    _emit_progress("child_start", common)
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=_child_env(device, base_env),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        result = {
            **common,
            "status": "failed",
            "exit_code": None,
            "timed_out": True,
            "timeout_seconds": timeout,
            "stdout": _as_text(exc.stdout),
            "stderr": _as_text(exc.stderr),
        }
    else:
        status = (
            "passed"
            if completed.returncode == 0
            else "blocked" if completed.returncode == 2 else "failed"
        )
        result = {
            **common,
            "status": status,
            "exit_code": completed.returncode,
            "timed_out": False,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }

    _emit_progress(
        "child_complete",
        {
            **common,
            "status": result["status"],
            "exit_code": result["exit_code"],
            "timed_out": result["timed_out"],
        },
    )
    return result


async def _run_device_pipeline(
    device: Mapping[str, Any], *, timeout: float, base_env: Mapping[str, str]
) -> list[dict[str, Any]]:
    results = []
    for script in SCRIPTS[device["platform"]]:
        results.append(
            await asyncio.to_thread(
                _run_child, device, script, timeout=timeout, base_env=base_env
            )
        )
    return results


async def _run_pipelines(
    devices: Sequence[Mapping[str, Any]],
    *,
    timeout: float,
    base_env: Mapping[str, str],
) -> list[dict[str, Any]]:
    pipelines = await asyncio.gather(
        *(
            _run_device_pipeline(device, timeout=timeout, base_env=base_env)
            for device in devices
        )
    )
    return [result for pipeline in pipelines for result in pipeline]


async def _discover_devices() -> list[dict[str, Any]]:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    for name in (
        "http_proxy",
        "https_proxy",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "all_proxy",
    ):
        env.pop(name, None)
    env["NO_PROXY"] = "*"
    env["no_proxy"] = "*"
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "pymobile_mcp.cli", "run"],
        cwd=str(ROOT),
        env=env,
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("mobile_list_available_devices", {})
            return _online_devices(json.loads(result.content[0].text))


def _timeout_seconds(env: Mapping[str, str]) -> float:
    timeout = float(env.get("PYMOBILE_MCP_LIVE_TIMEOUT", "180"))
    if timeout <= 0:
        raise ValueError("PYMOBILE_MCP_LIVE_TIMEOUT must be greater than zero")
    return timeout


async def main() -> int:
    try:
        timeout = _timeout_seconds(os.environ)
        devices = await asyncio.wait_for(_discover_devices(), timeout=timeout)
    except asyncio.TimeoutError:
        print(
            json.dumps(
                {"status": "blocked", "reason": "device discovery timed out"}, indent=2
            )
        )
        return 2
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "reason": "device discovery failed",
                    "error": str(exc),
                },
                indent=2,
            )
        )
        return 1

    if not devices:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": "no online Android or iOS devices",
                    "results": [],
                },
                indent=2,
            )
        )
        return 2

    results = await _run_pipelines(devices, timeout=timeout, base_env=os.environ)
    status, exit_code = _aggregate(results)
    print(
        json.dumps({"status": status, "devices": devices, "results": results}, indent=2)
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

from __future__ import annotations

import asyncio
import builtins
import json
import subprocess
import sys
import threading

import all_devices_live_smoke as fleet
from crash_tools_live_smoke import _selected_devices

DEVICES = {
    "devices": [
        {"id": "android-1", "platform": "android", "state": "online"},
        {"id": "android-off", "platform": "android", "state": "offline"},
        {"id": "ios-1", "platform": "ios", "state": "online"},
    ]
}


def test_selects_only_current_online_supported_devices():
    assert [device["id"] for device in fleet._online_devices(DEVICES)] == [
        "android-1",
        "ios-1",
    ]


def test_crash_selector_prefers_unified_and_never_expands_exact_selection():
    assert [
        device["id"]
        for device in _selected_devices(
            DEVICES,
            {
                "PYMOBILE_MCP_DEVICE": "ios-1",
                "PYMOBILE_MCP_ANDROID_DEVICE": "android-1",
            },
        )
    ] == ["ios-1"]
    assert [
        device["id"]
        for device in _selected_devices(
            DEVICES, {"PYMOBILE_MCP_ANDROID_DEVICE": "android-1"}
        )
    ] == ["android-1"]
    assert _selected_devices(DEVICES, {"PYMOBILE_MCP_DEVICE": "missing"}) == []
    assert [device["id"] for device in _selected_devices(DEVICES, {})] == [
        "android-1",
        "ios-1",
    ]


def test_child_env_pins_device_and_requires_unified_action_opt_in():
    inherited = {
        "PYMOBILE_MCP_ANDROID_ACTIONS": "1",
        "PYMOBILE_MCP_ANDROID_DESTRUCTIVE": "1",
        "PYMOBILE_MCP_IOS_DEVICE": "unrelated",
    }
    safe = fleet._child_env(DEVICES["devices"][0], inherited)
    assert (
        safe["PYMOBILE_MCP_DEVICE"]
        == safe["PYMOBILE_MCP_ANDROID_DEVICE"]
        == "android-1"
    )
    assert "PYMOBILE_MCP_IOS_DEVICE" not in safe
    assert "PYMOBILE_MCP_ANDROID_ACTIONS" not in safe
    assert "PYMOBILE_MCP_ANDROID_DESTRUCTIVE" not in safe

    opted_in = fleet._child_env(DEVICES["devices"][0], {"PYMOBILE_MCP_ACTIONS": "1"})
    assert opted_in["PYMOBILE_MCP_ANDROID_ACTIONS"] == "1"


def test_aggregate_exit_precedence():
    passed = {"status": "passed"}
    blocked = {"status": "blocked"}
    failed = {"status": "failed"}

    assert fleet._aggregate([passed, passed]) == ("passed", 0)
    assert fleet._aggregate([passed, blocked]) == ("blocked", 2)
    assert fleet._aggregate([blocked, failed]) == ("failed", 1)


def test_child_exit_codes_map_to_exact_statuses(monkeypatch):
    exit_codes = iter((0, 2, 7))

    def complete(command, **kwargs):
        return subprocess.CompletedProcess(
            command, next(exit_codes), stdout="captured out", stderr="captured err"
        )

    monkeypatch.setattr(subprocess, "run", complete)
    results = [
        fleet._run_child(
            {"id": "ios-1", "platform": "ios"},
            "ios_system_helpers_live_smoke.py",
            timeout=1,
            base_env={},
        )
        for _ in range(3)
    ]

    assert [result["status"] for result in results] == ["passed", "blocked", "failed"]
    assert [result["exit_code"] for result in results] == [0, 2, 7]
    assert all(
        result["stdout"] == "captured out" and result["stderr"] == "captured err"
        for result in results
    )


def test_child_timeout_is_captured_as_failure(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            args[0], kwargs["timeout"], output="partial out", stderr="partial err"
        )

    monkeypatch.setattr(subprocess, "run", timeout)
    result = fleet._run_child(
        {"id": "android-1", "platform": "android"},
        "android_live_smoke.py",
        timeout=0.01,
        base_env={"PYMOBILE_MCP_ACTIONS": "0"},
    )

    assert result == {
        "device": "android-1",
        "platform": "android",
        "script": "android_live_smoke.py",
        "status": "failed",
        "exit_code": None,
        "timed_out": True,
        "timeout_seconds": 0.01,
        "stdout": "partial out",
        "stderr": "partial err",
    }


def test_device_pipelines_overlap_but_each_device_remains_sequential(monkeypatch):
    scripts = ("first.py", "second.py")
    monkeypatch.setattr(fleet, "SCRIPTS", {"android": scripts})
    barrier = threading.Barrier(2)
    lock = threading.Lock()
    active_devices: set[str] = set()
    order: dict[str, list[str]] = {"android-1": [], "android-2": []}
    max_active = 0

    def run_child(device, script, **kwargs):
        nonlocal max_active
        device_id = device["id"]
        with lock:
            assert device_id not in active_devices
            active_devices.add(device_id)
            order[device_id].append(script)
            max_active = max(max_active, len(active_devices))
        if script == "first.py":
            barrier.wait(timeout=1)
        with lock:
            active_devices.remove(device_id)
        return {"device": device_id, "script": script, "status": "passed"}

    monkeypatch.setattr(fleet, "_run_child", run_child)
    devices = [
        {"id": "android-1", "platform": "android"},
        {"id": "android-2", "platform": "android"},
    ]

    results = asyncio.run(fleet._run_pipelines(devices, timeout=1, base_env={}))

    assert max_active == 2
    assert order == {"android-1": list(scripts), "android-2": list(scripts)}
    assert [(result["device"], result["script"]) for result in results] == [
        ("android-1", "first.py"),
        ("android-1", "second.py"),
        ("android-2", "first.py"),
        ("android-2", "second.py"),
    ]


def test_child_progress_is_machine_readable_and_flushed(monkeypatch):
    writes = []

    def print_progress(*args, **kwargs):
        writes.append((args, kwargs))

    def complete(command, **kwargs):
        assert [json.loads(args[0])["event"] for args, _ in writes] == ["child_start"]
        return subprocess.CompletedProcess(command, 0, stdout="out", stderr="err")

    monkeypatch.setattr(builtins, "print", print_progress)
    monkeypatch.setattr(subprocess, "run", complete)

    result = fleet._run_child(
        {"id": "ios-1", "platform": "ios"},
        "ios_system_helpers_live_smoke.py",
        timeout=1,
        base_env={},
    )

    progress = [json.loads(args[0]) for args, _ in writes]
    assert [item["event"] for item in progress] == ["child_start", "child_complete"]
    assert progress[0] == {
        "device": "ios-1",
        "event": "child_start",
        "platform": "ios",
        "script": "ios_system_helpers_live_smoke.py",
    }
    assert progress[1] == {
        "device": "ios-1",
        "event": "child_complete",
        "exit_code": 0,
        "platform": "ios",
        "script": "ios_system_helpers_live_smoke.py",
        "status": "passed",
        "timed_out": False,
    }
    assert all(kwargs == {"file": sys.stderr, "flush": True} for _, kwargs in writes)
    assert result["status"] == "passed"

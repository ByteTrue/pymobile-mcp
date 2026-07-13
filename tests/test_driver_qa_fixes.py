from __future__ import annotations

import asyncio
import json
import signal
import subprocess
from types import SimpleNamespace

import pytest

OPENSTEP_LISTAPPS = b"""{
    "com.example.Zebra" = {
        CFBundleDisplayName = Zebra;
    };
    "com.apple.Preferences" = {
        CFBundleName = Settings;
    };
}""".decode()


@pytest.mark.asyncio
async def test_simulator_list_apps_converts_openstep_plist_with_plutil(
    monkeypatch,
) -> None:
    from pymobile_mcp.drivers.base import AppInfo
    from pymobile_mcp.drivers import ios_simulator

    simctl_calls = []
    plutil_calls = []

    def fake_simctl(*args: str) -> str:
        simctl_calls.append(args)
        return OPENSTEP_LISTAPPS

    def fake_run(argv, **kwargs):
        plutil_calls.append((argv, kwargs))
        return SimpleNamespace(
            stdout=json.dumps(
                {
                    "com.example.Zebra": {"CFBundleDisplayName": "Zebra"},
                    "com.apple.Preferences": {"CFBundleName": "Settings"},
                }
            )
        )

    monkeypatch.setattr(ios_simulator, "_simctl", fake_simctl)
    monkeypatch.setattr(ios_simulator.subprocess, "run", fake_run)

    apps = await ios_simulator.IOSSimulatorDriver("SIM-1").list_apps()

    assert simctl_calls == [("listapps", "SIM-1")]
    assert plutil_calls == [
        (
            ["plutil", "-convert", "json", "-o", "-", "--", "-"],
            {
                "input": OPENSTEP_LISTAPPS,
                "check": True,
                "capture_output": True,
                "text": True,
            },
        )
    ]
    assert apps == [
        AppInfo(package_name="com.apple.Preferences", app_name="Settings"),
        AppInfo(package_name="com.example.Zebra", app_name="Zebra"),
    ]


@pytest.mark.asyncio
async def test_simulator_crashes_are_recursive_relative_and_readable(
    tmp_path, monkeypatch
) -> None:
    from pymobile_mcp.drivers import ios_simulator

    root = tmp_path / "CrashReporter"
    report = root / "DiagnosticLogs" / "Demo-2026.ips"
    report.parent.mkdir(parents=True)
    report.write_text("real simulator crash report")
    monkeypatch.setattr(ios_simulator, "_simulator_crash_root", lambda _: root)

    driver = ios_simulator.IOSSimulatorDriver("SIM-1")
    assert await driver.list_crashes() == [
        {
            "id": "DiagnosticLogs/Demo-2026.ips",
            "name": "DiagnosticLogs/Demo-2026.ips",
            "path": str(report),
        }
    ]
    assert (
        await driver.get_crash("DiagnosticLogs/Demo-2026.ips")
        == "real simulator crash report"
    )


@pytest.mark.asyncio
async def test_simulator_crashes_empty_and_reject_traversal(
    tmp_path, monkeypatch
) -> None:
    from pymobile_mcp.drivers import ios_simulator
    from pymobile_mcp.errors import DriverError

    root = tmp_path / "CrashReporter"
    root.mkdir()
    secret = tmp_path / "secret.ips"
    secret.write_text("do not read")
    monkeypatch.setattr(ios_simulator, "_simulator_crash_root", lambda _: root)

    driver = ios_simulator.IOSSimulatorDriver("SIM-1")
    assert await driver.list_crashes() == []
    with pytest.raises(DriverError, match="not found or unreadable"):
        await driver.get_crash("../secret.ips")
    with pytest.raises(DriverError, match="not found or unreadable"):
        await driver.get_crash(str(secret))


@pytest.mark.asyncio
async def test_simulator_crash_symlink_cannot_escape_root(
    tmp_path, monkeypatch
) -> None:
    from pymobile_mcp.drivers import ios_simulator
    from pymobile_mcp.errors import DriverError

    root = tmp_path / "CrashReporter"
    root.mkdir()
    secret = tmp_path / "secret.ips"
    secret.write_text("do not read")
    (root / "escape.ips").symlink_to(secret)
    monkeypatch.setattr(ios_simulator, "_simulator_crash_root", lambda _: root)

    driver = ios_simulator.IOSSimulatorDriver("SIM-1")
    assert await driver.list_crashes() == []
    with pytest.raises(DriverError, match="not found or unreadable"):
        await driver.get_crash("escape.ips")


def _recording_driver(
    monkeypatch, processes, *, window_size=(720, 1280), orientation="portrait"
):
    from pymobile_mcp.drivers.android import AndroidDriver

    adb_calls = []

    class Adb:
        def shell(self, argv):
            adb_calls.append(argv)

    popen_calls = []

    def fake_popen(argv, **kwargs):
        popen_calls.append((argv, kwargs))
        return processes[len(popen_calls) - 1]

    driver = AndroidDriver("physical-1")
    driver._device = SimpleNamespace(window_size=lambda: window_size)
    monkeypatch.setattr(driver, "_adb", lambda: Adb())
    monkeypatch.setattr(driver, "_get_orientation_sync", lambda: orientation)
    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    return driver, adb_calls, popen_calls


class _LiveProcess:
    def wait(self, timeout):
        raise subprocess.TimeoutExpired("adb screenrecord", timeout)


class _ExitedProcess:
    def __init__(self, returncode):
        self.returncode = returncode

    def wait(self, timeout):
        return self.returncode


def test_android_recording_live_default_does_not_retry(monkeypatch) -> None:
    process = _LiveProcess()
    driver, adb_calls, popen_calls = _recording_driver(monkeypatch, [process])

    assert driver._start_recording_sync("/sdcard/out.mp4", 5) is process
    assert adb_calls == [["rm", "-f", "/sdcard/out.mp4"]]
    assert popen_calls == [
        (
            [
                "adb",
                "-s",
                "physical-1",
                "shell",
                "screenrecord",
                "--time-limit",
                "5",
                "/sdcard/out.mp4",
            ],
            {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL},
        )
    ]


@pytest.mark.parametrize(
    ("window_size", "legacy_orientation", "expected_size"),
    [
        ((720, 1280), "portrait", "720x1280"),
        ((720, 1280), "landscape", "720x1280"),  # reverse portrait
        ((1280, 720), "landscape", "1280x720"),
        ((1280, 720), "portrait", "1280x720"),  # landscape-native rotation zero
    ],
)
def test_android_recording_immediate_failure_retries_current_window_size(
    monkeypatch, window_size, legacy_orientation, expected_size
) -> None:
    retry = _LiveProcess()
    driver, adb_calls, popen_calls = _recording_driver(
        monkeypatch,
        [_ExitedProcess(235), retry],
        window_size=window_size,
        orientation=legacy_orientation,
    )

    assert driver._start_recording_sync("/sdcard/out.mp4", None) is retry
    assert adb_calls == [
        ["rm", "-f", "/sdcard/out.mp4"],
        ["rm", "-f", "/sdcard/out.mp4"],
    ]
    assert [call[0] for call in popen_calls] == [
        ["adb", "-s", "physical-1", "shell", "screenrecord", "/sdcard/out.mp4"],
        [
            "adb",
            "-s",
            "physical-1",
            "shell",
            "screenrecord",
            "--size",
            expected_size,
            "/sdcard/out.mp4",
        ],
    ]


def test_android_recording_retry_immediate_failure_raises(monkeypatch) -> None:
    from pymobile_mcp.errors import DriverError

    driver, _, _ = _recording_driver(
        monkeypatch, [_ExitedProcess(235), _ExitedProcess(235)]
    )

    with pytest.raises(DriverError, match="safe-size retry exited with code 235"):
        driver._start_recording_sync("/sdcard/out.mp4", 5)


class _RecordingStopAdb:
    def __init__(self, local_path):
        self.calls = []
        self.sync = SimpleNamespace(pull=self._pull)
        self.local_path = local_path

    def shell(self, argv):
        self.calls.append(argv)
        if argv[0] == "ls":
            return f"-rw-r--r-- 1 shell shell 5 {argv[-1]}"
        return ""

    def _pull(self, remote_path, local_path):
        assert remote_path == "/sdcard/out.mp4"
        assert local_path == str(self.local_path)
        self.local_path.write_bytes(b"video")


class _RecordingStopProcess:
    def __init__(self, wait_results, send_error=None):
        self.wait_results = iter(wait_results)
        self.send_error = send_error
        self.signals = []
        self.wait_timeouts = []
        self.killed = False

    def poll(self):
        return None

    def send_signal(self, value):
        self.signals.append(value)
        if self.send_error is not None:
            raise self.send_error

    def wait(self, timeout):
        self.wait_timeouts.append(timeout)
        result = next(self.wait_results)
        if isinstance(result, Exception):
            raise result
        return result

    def kill(self):
        self.killed = True


def test_android_recording_stop_prefers_local_sigint_without_remote_kill(
    tmp_path, monkeypatch
) -> None:
    from pymobile_mcp.drivers.android import AndroidDriver

    local_path = tmp_path / "out.mp4"
    adb = _RecordingStopAdb(local_path)
    process = _RecordingStopProcess([0])
    driver = AndroidDriver("physical-1")
    monkeypatch.setattr(driver, "_adb", lambda: adb)

    assert driver._stop_recording_sync(process, "/sdcard/out.mp4", local_path) == 5
    assert process.signals == [signal.SIGINT]
    assert process.wait_timeouts == [5]
    assert process.killed is False
    assert ["pkill", "-INT", "screenrecord"] not in adb.calls
    assert ["killall", "-2", "screenrecord"] not in adb.calls


@pytest.mark.parametrize(
    "error", [RuntimeError("unexpected wait failure"), OSError("wait failed")]
)
def test_android_recording_stop_unexpected_wait_error_propagates_without_remote_kill(
    tmp_path, monkeypatch, error
) -> None:
    from pymobile_mcp.drivers.android import AndroidDriver

    local_path = tmp_path / "out.mp4"
    adb = _RecordingStopAdb(local_path)
    process = _RecordingStopProcess([error])
    driver = AndroidDriver("physical-1")
    monkeypatch.setattr(driver, "_adb", lambda: adb)

    with pytest.raises(type(error), match=str(error)):
        driver._stop_recording_sync(process, "/sdcard/out.mp4", local_path)

    assert process.signals == [signal.SIGINT]
    assert process.wait_timeouts == [5]
    assert process.killed is False
    assert ["pkill", "-INT", "screenrecord"] not in adb.calls
    assert ["killall", "-2", "screenrecord"] not in adb.calls


def test_android_recording_stop_send_signal_error_propagates_without_remote_kill(
    tmp_path, monkeypatch
) -> None:
    from pymobile_mcp.drivers.android import AndroidDriver

    local_path = tmp_path / "out.mp4"
    adb = _RecordingStopAdb(local_path)
    process = _RecordingStopProcess([], send_error=OSError("signal failed"))
    driver = AndroidDriver("physical-1")
    monkeypatch.setattr(driver, "_adb", lambda: adb)

    with pytest.raises(OSError, match="signal failed"):
        driver._stop_recording_sync(process, "/sdcard/out.mp4", local_path)

    assert process.signals == [signal.SIGINT]
    assert process.wait_timeouts == []
    assert process.killed is False
    assert ["pkill", "-INT", "screenrecord"] not in adb.calls
    assert ["killall", "-2", "screenrecord"] not in adb.calls


def test_android_recording_stop_timeout_uses_remote_fallback_then_kills(
    tmp_path, monkeypatch
) -> None:
    from pymobile_mcp.drivers.android import AndroidDriver

    local_path = tmp_path / "out.mp4"
    adb = _RecordingStopAdb(local_path)
    process = _RecordingStopProcess(
        [
            subprocess.TimeoutExpired("adb screenrecord", 5),
            subprocess.TimeoutExpired("adb screenrecord", 5),
            137,
        ]
    )
    driver = AndroidDriver("physical-1")
    monkeypatch.setattr(driver, "_adb", lambda: adb)

    assert driver._stop_recording_sync(process, "/sdcard/out.mp4", local_path) == 5
    assert process.signals == [signal.SIGINT]
    assert process.wait_timeouts == [5, 5, 3]
    assert process.killed is True
    assert ["pkill", "-INT", "screenrecord"] in adb.calls


@pytest.mark.asyncio
async def test_concurrent_recording_start_spawns_once_and_loser_is_already_recording(
    tmp_path,
) -> None:
    from pymobile_mcp.drivers.base import DeviceInfo
    from pymobile_mcp.errors import ToolError
    from pymobile_mcp.tools import android
    from pymobile_mcp.tools.android import (
        configure_android_tools_for_tests,
        reset_android_tools_for_tests,
    )
    from pymobile_mcp.tools.recording import reset_recording_state_for_tests

    spawn_started = asyncio.Event()
    allow_spawn = asyncio.Event()
    spawn_calls = 0
    both_connected = asyncio.Event()
    connect_calls = 0

    class Driver:
        platform = "android"

        async def connect(self, capabilities=None):
            nonlocal connect_calls
            connect_calls += 1
            if connect_calls == 2:
                both_connected.set()
            await both_connected.wait()

        async def start_recording(self, remote_path, time_limit=None):
            nonlocal spawn_calls
            spawn_calls += 1
            spawn_started.set()
            await allow_spawn.wait()
            return object()

    configure_android_tools_for_tests(
        lambda: [DeviceInfo("d", "d", "android", "emulator", "1", "online")],
        lambda _: Driver(),
    )
    reset_recording_state_for_tests()
    args = {"device": "d", "output": str(tmp_path / "recording.mp4")}
    try:
        winner = asyncio.create_task(android.start_screen_recording(args))
        loser = asyncio.create_task(android.start_screen_recording(args))
        await spawn_started.wait()
        await asyncio.sleep(0)
        allow_spawn.set()
        results = await asyncio.gather(winner, loser, return_exceptions=True)
    finally:
        reset_recording_state_for_tests()
        reset_android_tools_for_tests()

    assert spawn_calls == 1
    errors = [result for result in results if isinstance(result, ToolError)]
    assert len(errors) == 1
    assert errors[0].code == "already_recording"


@pytest.mark.asyncio
async def test_simulator_stop_recording_timeout_kills_and_reaps_before_driver_error(
    tmp_path, monkeypatch
) -> None:
    from pymobile_mcp.drivers import ios_simulator
    from pymobile_mcp.errors import DriverError

    class Process:
        def __init__(self):
            self.signals = []
            self.killed = False
            self.waits = 0

        def send_signal(self, value):
            self.signals.append(value)

        def kill(self):
            self.killed = True

        def wait(self):
            self.waits += 1

            async def done():
                return 137

            return done()

    wait_for_calls = 0

    async def fake_wait_for(awaitable, timeout):
        nonlocal wait_for_calls
        wait_for_calls += 1
        awaitable.close()
        if wait_for_calls == 1:
            raise asyncio.TimeoutError
        return 137

    monkeypatch.setattr(ios_simulator.asyncio, "wait_for", fake_wait_for)
    process = Process()

    with pytest.raises(DriverError) as raised:
        await ios_simulator.IOSSimulatorDriver("SIM-1").stop_recording(
            process, str(tmp_path / "recording.mp4"), tmp_path / "recording.mp4"
        )

    assert raised.value.code == "driver_error"
    assert raised.value.tool == "ios"
    assert raised.value.details == {"device": "SIM-1", "timeout": 30}
    assert process.signals == [ios_simulator.signal.SIGINT]
    assert process.killed is True
    assert process.waits == 2
    assert wait_for_calls == 2


def _text_result(value: str):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=value)])


@pytest.mark.asyncio
async def test_ios_recording_smoke_keeps_real_exception_and_runs_simulator(
    tmp_path,
) -> None:
    from ios_app_recording_crash_live_smoke import _exercise_recording

    class RealSession:
        async def call_tool(self, name, args):
            assert name == "mobile_start_screen_recording"
            assert args["device"] == "real-1"
            return _text_result(
                "iOS screen recording is not available through pure "
                "pymobiledevice3/WDA yet. Please fix the issue and try again."
            )

    async def no_sleep(_):
        return None

    real = await _exercise_recording(
        RealSession(),
        {"id": "real-1", "type": "real"},
        tmp_path / "real.mp4",
        sleep=no_sleep,
    )
    assert real == {"status": "unsupported_platform", "size": None}

    output = tmp_path / "simulator.mp4"
    calls = []

    class SimulatorSession:
        async def call_tool(self, name, args):
            calls.append((name, args))
            if name == "mobile_stop_screen_recording":
                output.write_bytes(b"mp4")
                return _text_result(f"Recording stopped. File: {output} (0.00 MB, ~1s)")
            return _text_result(
                f"Screen recording started. Output will be saved to: {output}"
            )

    simulator = await _exercise_recording(
        SimulatorSession(),
        {"id": "sim-1", "type": "simulator"},
        output,
        sleep=no_sleep,
    )
    assert simulator == {"status": "simctl", "size": 3}
    assert calls == [
        (
            "mobile_start_screen_recording",
            {"device": "sim-1", "output": str(output)},
        ),
        ("mobile_stop_screen_recording", {"device": "sim-1"}),
    ]

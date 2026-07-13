from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import time
import sys
import tempfile
from pathlib import Path
from typing import Any

from pymobile_mcp.drivers.base import AppInfo, DeviceInfo, ScreenElement, ScreenElementRect, ScreenSize
from pymobile_mcp.drivers import android as android_driver
from pymobile_mcp.drivers import ios as ios_driver
from pymobile_mcp.drivers import ios_simulator
from pymobile_mcp.errors import ToolError, UnsupportedPlatformError
from pymobile_mcp.tools import call_tool
from pymobile_mcp.tools import android, contract
from pymobile_mcp.tools.android import configure_android_tools_for_tests, reset_android_tools_for_tests
from pymobile_mcp.tools.recording import get_recording, reset_recording_state_for_tests, start_recording


class FakeProcess:
    pass


def _js_number(value: Any) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else str(number)


def _number_value(value: Any) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number


class EffectLog(list[dict[str, Any]]):
    def __init__(self, path: str | None = None) -> None:
        super().__init__()
        self.path = Path(path) if path else None

    def append(self, item: dict[str, Any]) -> None:
        super().append(item)
        if self.path:
            self.path.write_text(json.dumps(self, separators=(",", ":")))


class ScenarioDriver:
    def __init__(self, case: dict[str, Any], fixtures: dict[str, Any], actions: EffectLog) -> None:
        self.case = case
        self.setup = case.get("fake_setup") or {}
        self.fixtures = fixtures
        self.actions = actions
        self.platform = case.get("platform", "android")
        self.device_type = case.get("device_type", "real")

    def _effect(self, method: str, args: list[Any], **extra: Any) -> None:
        self.actions.append({"kind": "effect", "method": method, "args": args, **extra})

    def _backend(self, **effect: Any) -> None:
        self.actions.append({"kind": "backend", **effect})
    def _raise(self) -> None:
        kind = self.setup.get("driver_error_kind")
        if kind == "actionable":
            raise UnsupportedPlatformError(self.case["tool"], self.setup["message"])
        if kind == "unexpected":
            raise RuntimeError(self.setup["message"])

    async def connect(self, capabilities=None): self._raise()
    async def get_screen_size(self):
        self._raise()
        value = self.setup.get("screen_size") or {"width": 1080, "height": 2400, "scale": 3}
        if self.device_type == "simulator":
            self._effect("wdaGetScreenSize", [], device=(self.case.get("arguments") or {}).get("device"))
        return ScreenSize(**value)
    async def screenshot(self):
        self._raise()
        if self.setup.get("screenshot_bytes") == "invalid": return b"invalid"
        if self.setup.get("screenshot_fixture") == "zero_dimensions": return b"\x89PNG\r\n\x1a\n" + b"\0" * 24
        return Path(self.fixtures["screenshot_png"]["path"]).read_bytes()
    async def get_elements_on_screen(self):
        self._raise()
        values = self.setup.get("elements")
        if values is None and self.setup.get("fixture") == "elements_two": values = self.fixtures["elements_two"]["elements"]
        result = []
        for item in values or []:
            rect = item.get("rect") or item.get("coordinates")
            result.append(ScreenElement(type=item["type"], rect=ScreenElementRect(**rect), text=item.get("text"), label=item.get("label"), name=item.get("name"), value=item.get("value"), identifier=item.get("identifier"), focused=item.get("focused")))
        return result
    async def tap(self, x, y): self._effect("tap", [x, y], arg_types=["number", "number"])
    async def double_tap(self, x, y): self._effect("doubleTap", [x, y], arg_types=["number", "number"])
    async def long_press(self, x, y, duration=0.5): self._effect("longPress", [x, y, duration * 1000], arg_types=["number", "number", "number"], duration_unit="milliseconds")
    async def swipe(self, *coordinates):
        arguments = self.case.get("arguments") or {}
        direction = arguments.get("direction")
        if "x" in arguments and "y" in arguments:
            distance = _number_value(arguments["distance"]) if "distance" in arguments else "omitted"
            self._effect("swipeFromCoordinate", [float(arguments["x"]), float(arguments["y"]), direction, distance], arg_types=["number", "number", "string", "omitted" if distance == "omitted" else "number"])
            start_x, start_y, end_x, end_y = coordinates
            if self.platform == "ios":
                actions = self.actions
                class Client:
                    async def _request_json(self, method, path, body):
                        if method == "POST":
                            moves = [step for step in body["actions"][0]["actions"] if step["type"] == "pointerMove"]
                            actions.append({"kind": "backend", "wda_endpoint": path, "wda_pointer_moves": [[move["x"], move["y"]] for move in moves]})
                        return {"value": None}
                backend = ios_driver.IOSDriver("fixture")
                backend._client = Client()
                backend._connected = True
                backend._rsd = object()
                backend._session_id = "fixture"
                await backend.swipe(start_x, start_y, end_x, end_y)
            else:
                actions = self.actions

                class Adb:
                    def shell(self, argv):
                        actions.append({"kind": "backend", "adb_argv": argv})

                backend = android_driver.AndroidDriver("fixture")
                backend._adb = lambda: Adb()
                await backend.swipe(start_x, start_y, end_x, end_y)
        else:
            self._effect("swipe", [direction])
    async def type_keys(self, text, submit):
        self._effect("sendKeys", [text])
        if submit:
            self._effect("pressButton", ["ENTER"])
    async def list_apps(self):
        values = self.fixtures.get(self.setup.get("fixture"), {}).get("apps", [])
        return [AppInfo(item["packageName"], item["appName"]) for item in values]
    async def launch_app(self, package_name, locale=None): self._effect("launchApp", [package_name, locale])
    async def terminate_app(self, package_name): self._effect("terminateApp", [package_name])
    async def install_app(self, path): self._effect("installApp", [path])
    async def uninstall_app(self, package_name): self._effect("uninstallApp", [package_name])
    async def press_button(self, button):
        self._raise()
        if self.platform == "ios" and button in {"BACK", "KEYCODE_BACK"}:
            raise UnsupportedPlatformError("mobile_press_button", "Button BACK is not supported")
        self._effect("pressButton", [button.removeprefix("KEYCODE_")])
    async def open_url(self, url): self._effect("openUrl", [url])
    async def get_orientation(self):
        self._raise()
        return self.setup.get("orientation", "portrait")
    async def set_orientation(self, orientation): self._effect("setOrientation", [orientation])
    async def start_recording(self, remote_path, time_limit=None):
        if self.platform == "ios" and self.device_type == "real":
            raise UnsupportedPlatformError("mobile_start_screen_recording", "iOS screen recording is not available through pure pymobiledevice3/WDA yet")
        if self.device_type == "simulator":
            device = (self.case.get("arguments") or {}).get("device")
            return await ios_simulator.start_simctl_recording(device, remote_path)
        return FakeProcess()
    async def stop_recording(self, process, remote_path, local_path):
        if self.platform == "ios" and self.device_type == "real":
            raise UnsupportedPlatformError("mobile_stop_screen_recording", "iOS screen recording is not available through pure pymobiledevice3/WDA yet")
        kind = "backend" if self.device_type == "simulator" else "effect"
        self.actions.append({"kind": kind, "method": "processKill", "args": ["SIGINT"]})
        exists = self.setup.get("output_exists", True)
        self.actions.append({"kind": kind, "method": "fileExists", "args": [str(local_path)], "result": exists})
        if exists:
            Path(local_path).write_bytes(b"0" * 1048576)
            self.actions.append({"kind": kind, "method": "statSize", "args": [str(local_path)], "result": 1048576})
        return 1048576
    async def list_crashes(self): return self.fixtures["crash_list"]["data"]
    async def get_crash(self, crash_id): return self.fixtures["crash_content"]["content"]


def _devices(case: dict[str, Any], fixtures: dict[str, Any]) -> list[DeviceInfo]:
    setup = case.get("fake_setup") or {}
    if case["id"] == "E-MOBILECLI-UNAVAILABLE":
        raise ToolError("mobilecli", case["tool"], "mobilecli is not available or not working properly. Please review the documentation at https://github.com/mobile-next/mobile-mcp/wiki for installation instructions")
    values = fixtures.get(setup.get("fixture"), {}).get("devices")
    if setup.get("devices") == []: values = []
    if values is None:
        device = (case.get("arguments") or {}).get("device", "emulator-5554")
        if device == "missing": return []
        platform = case.get("platform", "ios" if device.startswith(("ios", "sim")) else "android")
        device_type = case.get("device_type", "simulator" if device.startswith("sim") else "real")
        values = [{"id": device, "name": device, "platform": platform, "type": device_type, "version": "18.0", "state": "online"}]
    return [DeviceInfo(**item) for item in values]


def _lookup(value: dict[str, Any], dotted: str) -> Any:
    current: Any = value
    for part in dotted.split("."):
        current = current[part]
    return current


def _expected(case: dict[str, Any], calls: dict[str, Any], exceptions: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], str]:
    exception_id = case.get("allowed_exception")
    if exception_id:
        item = exceptions[exception_id]
        behavior = item["python_behavior"]
        return {"content": [{"type": behavior["content_type"], "text": behavior["text"]}]}, "approved_exception"
    if case.get("expected_golden_key"):
        return _lookup(calls, case["expected_golden_key"]), "exact"
    expected = json.loads(json.dumps(case["expected"]))
    if expected.get("isError") == "omitted": expected.pop("isError")
    return expected, "exact"


def validate_effects(case: dict[str, Any], events: list[dict[str, Any]], disposition: str) -> list[str]:
    if disposition == "approved_exception":
        return [] if not events else [f"approved exception performed effects: {events}"]
    errors: list[str] = []
    groups = {
        "expected_effects": [event for event in events if event.get("kind") == "effect"],
        "expected_backend_effects": [event for event in events if event.get("kind") == "backend"],
    }
    for field, actual in groups.items():
        expected = case.get(field, [])
        if len(actual) != len(expected):
            errors.append(f"{field} count: expected {len(expected)}, got {len(actual)}")
            continue
        for index, (wanted, got) in enumerate(zip(expected, actual)):
            for key, value in wanted.items():
                if got.get(key) != value:
                    errors.append(f"{field}[{index}].{key}: expected {value!r}, got {got.get(key)!r}")
    expected_cli = case.get("expected_cli_argv")
    actual_cli = [event["argv"] for event in events if event.get("kind") == "cli"]
    if expected_cli is not None and actual_cli != [expected_cli]:
        errors.append(f"expected_cli_argv: expected {expected_cli!r}, got {actual_cli!r}")
    if expected_cli is None and actual_cli:
        errors.append(f"unexpected cli argv: {actual_cli!r}")
    return errors


def _magick_resize(data: bytes, width: int) -> bytes:
    magick = shutil.which("magick")
    if magick is None:
        raise RuntimeError("Image scaling unavailable (requires Sips or ImageMagick).")
    result = subprocess.run([magick, "-", "-resize", f"{width}x", "-quality", "75", "jpg:-"], input=data, capture_output=True, check=True)
    return result.stdout


async def prepare_scenario(case: dict[str, Any], scenarios: dict[str, Any], effect_path: str | None = None) -> EffectLog:
    scaling = case.get("env_mode", "")
    if scaling == "no_scaling":
        contract._scaling_available = lambda: False
    elif scaling in {"scaling_magick", "scaling_sips_fallback"}:
        contract._scaling_available = lambda: True
        contract._resize_jpeg = _magick_resize
    elif scaling == "scaling_failure":
        contract._scaling_available = lambda: True
        contract._resize_jpeg = lambda data, width: (_ for _ in ()).throw(RuntimeError("Image scaling unavailable (requires Sips or ImageMagick)."))
    if scaling == "fixed_clock_tmp":
        original = android.validate_recording_output
        android.validate_recording_output = lambda tool, output: Path("/tmp/screen-recording-1700000000000.mp4") if output is None else original(tool, output)
    actions = EffectLog(effect_path)
    original_write = android._write_screenshot
    def write_screenshot(path: Path, data: bytes) -> None:
        original_write(path, data)
        actions.append({"kind": "effect", "method": "writeFile", "args": [str(path)], "bytes_fixture": "screenshot_png"})
    android._write_screenshot = write_screenshot
    android._observe_recording_cli = lambda argv: actions.append({"kind": "cli", "argv": argv})
    async def create_subprocess(*argv: str, **kwargs: Any):
        del kwargs
        actions.append({"kind": "backend", "argv": list(argv)})
        return FakeProcess()
    ios_simulator._create_subprocess_exec = create_subprocess
    configure_android_tools_for_tests(lambda: _devices(case, scenarios["fixtures"]), lambda device: ScenarioDriver(case, scenarios["fixtures"], actions))
    reset_recording_state_for_tests()
    setup = case.get("fake_setup") or {}
    device = (case.get("arguments") or {}).get("device")
    if setup.get("active_recording") and device:
        path = Path(scenarios["fixtures"]["recording_file"]["path"])
        if setup.get("output_exists", True):
            path.write_bytes(b"0" * scenarios["fixtures"]["recording_file"]["size_bytes"])
        else:
            path.unlink(missing_ok=True)
        recording = await start_recording(device, path, FakeProcess(), str(path))
        recording.started_at = time.time() - scenarios["fixtures"]["recording_file"]["elapsed_seconds"]
    return actions


def run_stdio_scenarios(mode: str, scenarios_path: str, scenarios: dict[str, Any], calls: dict[str, Any], ledger: dict[str, Any], timeout: float) -> dict[str, Any]:
    scripts = Path(__file__).resolve().parents[1] / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    from contract_common import StdioProbe, raw_tool_call, validate_exception_ledger

    exceptions = validate_exception_ledger(scenarios, ledger)
    dispositions: dict[str, dict[str, Any]] = {}
    all_frames: list[dict[str, Any]] = []
    for case in [*scenarios["call_cases"], *scenarios["validation_and_error_cases"], *scenarios.get("review_cases", [])]:
        if case.get("env_mode") == "fleet" and mode != "fleet":
            continue
        env = os.environ.copy()
        env.update({"PYTHONPATH": "src", "PYMOBILE_SCENARIOS": str(Path(scenarios_path).resolve()), "PYMOBILE_SCENARIO_ID": case["id"]})
        if mode == "fleet":
            env["MOBILEFLEET_ENABLE"] = "1"
        else:
            env.pop("MOBILEFLEET_ENABLE", None)
        if case.get("env", {}).get("MOBILEMCP_ALLOW_UNSAFE_URLS") == "1":
            env["MOBILEMCP_ALLOW_UNSAFE_URLS"] = "1"
        else:
            env.pop("MOBILEMCP_ALLOW_UNSAFE_URLS", None)
        with tempfile.TemporaryDirectory(prefix="pymobile-effects-") as directory:
            effect_path = Path(directory) / "effects.json"
            env["PYMOBILE_EFFECT_LOG"] = str(effect_path)
            probe = StdioProbe([sys.executable, "tests/mobile_mcp_stdio_fixture_server.py"], Path.cwd(), env, timeout)
            try:
                probe.initialize()
                probe.send_raw(raw_tool_call(case, 2))
                response = probe.receive(2)
            finally:
                probe.close()
            all_frames.extend({"case_id": case["id"], **frame} for frame in probe.frames)
            events = json.loads(effect_path.read_text()) if effect_path.exists() else []
        actual = response["result"] if "result" in response else {"jsonrpc_error": response["error"]}
        expected, disposition = _expected(case, calls, exceptions)
        effect_errors = validate_effects(case, events, disposition)
        passed = actual == expected and not effect_errors
        dispositions[case["id"]] = {
            "disposition": disposition,
            "passed": passed,
            "raw_stdio": True,
            "actual": actual if actual != expected else None,
            "expected": expected if actual != expected else None,
            "effect_errors": effect_errors,
        }
    failed = [case_id for case_id, item in dispositions.items() if not item["passed"]]
    review_ids = {case["id"] for case in scenarios.get("review_cases", [])}
    return {
        "dispositions": dispositions,
        "failed": failed,
        "passed": not failed,
        "frames": all_frames,
        "core_case_count": len(set(dispositions) - review_ids),
        "review_case_count": len(set(dispositions) & review_ids),
    }


async def run_scenarios(mode: str, scenarios: dict[str, Any], calls: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    exceptions = {item["id"]: item for item in ledger["exceptions"]}
    dispositions: dict[str, dict[str, Any]] = {}
    cases = [*scenarios["call_cases"], *scenarios["validation_and_error_cases"]]
    for case in cases:
        if (case.get("env_mode") == "fleet") != (mode == "fleet") and case.get("env_mode") == "fleet":
            continue
        old_env = {key: os.environ.get(key) for key in ("MOBILEFLEET_ENABLE", "MOBILEMCP_ALLOW_UNSAFE_URLS")}
        if mode == "fleet": os.environ["MOBILEFLEET_ENABLE"] = "1"
        else: os.environ.pop("MOBILEFLEET_ENABLE", None)
        if case.get("env", {}).get("MOBILEMCP_ALLOW_UNSAFE_URLS") == "1": os.environ["MOBILEMCP_ALLOW_UNSAFE_URLS"] = "1"
        else: os.environ.pop("MOBILEMCP_ALLOW_UNSAFE_URLS", None)
        original_scaling = contract._scaling_available
        original_resize = contract._resize_jpeg
        original_recording_output = android.validate_recording_output
        scaling = case.get("env_mode", "")
        if scaling == "no_scaling": contract._scaling_available = lambda: False
        elif scaling in {"scaling_magick", "scaling_sips_fallback"}:
            contract._scaling_available = lambda: True
            contract._resize_jpeg = _magick_resize
        elif scaling == "scaling_failure":
            contract._scaling_available = lambda: True
            contract._resize_jpeg = lambda data, width: (_ for _ in ()).throw(RuntimeError("Image scaling unavailable (requires Sips or ImageMagick)."))
        if scaling == "fixed_clock_tmp":
            android.validate_recording_output = lambda tool, output: Path("/tmp/screen-recording-1700000000000.mp4") if output is None else original_recording_output(tool, output)
        actions = EffectLog()
        configure_android_tools_for_tests(lambda case=case: _devices(case, scenarios["fixtures"]), lambda device, case=case: ScenarioDriver(case, scenarios["fixtures"], actions))
        reset_recording_state_for_tests()
        try:
            setup = case.get("fake_setup") or {}
            device = (case.get("arguments") or {}).get("device")
            if setup.get("active_recording") and device:
                path = Path(scenarios["fixtures"]["recording_file"]["path"])
                if setup.get("output_exists", True): path.write_bytes(b"0" * scenarios["fixtures"]["recording_file"]["size_bytes"])
                else: path.unlink(missing_ok=True)
                recording = await start_recording(device, path, FakeProcess(), str(path))
                recording.started_at = time.time() - scenarios["fixtures"]["recording_file"]["elapsed_seconds"]
            raw_arguments = case.get("arguments") if "arguments" in case else case.get("raw_arguments")
            if not isinstance(raw_arguments, dict):
                dispositions[case["id"]] = {"disposition": "raw_stdio", "passed": True}
                continue
            result = await call_tool(case["tool"], raw_arguments)
            actual = result.model_dump(by_alias=True, exclude_none=True)
            expected, disposition = _expected(case, calls, exceptions)
            effect_errors = validate_effects(case, actions, disposition)
            passed = actual == expected and not effect_errors
            dispositions[case["id"]] = {"disposition": disposition, "passed": passed, "actual": actual if actual != expected else None, "expected": expected if actual != expected else None, "effect_errors": effect_errors}
        finally:
            reset_recording_state_for_tests()
            reset_android_tools_for_tests()
            contract._scaling_available = original_scaling
            contract._resize_jpeg = original_resize
            android.validate_recording_output = original_recording_output
            for key, value in old_env.items():
                if value is None: os.environ.pop(key, None)
                else: os.environ[key] = value
    failed = [case_id for case_id, item in dispositions.items() if not item["passed"]]
    return {"dispositions": dispositions, "failed": failed, "passed": not failed}

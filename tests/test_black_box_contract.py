from pathlib import Path
import json
import subprocess
import sys
import os

import pytest


SCRIPTS = (
    "capture_mobile_mcp_contract.py",
    "capture_mobile_mcp_calls.py",
    "assert_mobile_mcp_contract.py",
    "validate_mobile_mcp_source_coverage.py",
    "compare_mobile_mcp_image_backends.py",
    "run_with_timeout.py",
)


UPSTREAM_CHECKOUT = Path(os.environ.get("PYMOBILE_MCP_UPSTREAM_SOURCE", "/Users/byte/workspace/forks/mobile-mcp"))


def _require_upstream_checkout(path: Path = UPSTREAM_CHECKOUT) -> Path:
    if not path.is_dir():
        pytest.skip(f"external upstream checkout unavailable: {path}; run CMD-007 in the oracle environment")
    return path


def test_contract_commands_have_runnable_help() -> None:
    for name in SCRIPTS:
        path = Path("scripts") / name
        assert path.is_file(), name
        completed = subprocess.run(
            [sys.executable, str(path), "--help"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert completed.returncode == 0, completed.stderr
        assert "usage:" in completed.stdout


def test_contract_assertion_rejects_stale_call_golden_before_stdio(tmp_path, monkeypatch) -> None:
    sys.path.insert(0, str(Path("scripts").resolve()))
    import assert_mobile_mcp_contract as contract_assertion

    call_golden = tmp_path / "stale-calls.json"
    call_golden.write_text(json.dumps({"provenance": {"bundle_sha256": "stale"}}))
    report = tmp_path / "report.json"
    scenarios = contract_assertion.load_yaml(
        ".codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-scenarios.yaml"
    )
    bundle_manifest = tmp_path / "bundle-manifest.json"
    bundle_manifest.write_text(json.dumps(contract_assertion.compute_bundle(scenarios)))
    probe_started = False

    def fail_if_started(*args, **kwargs):
        nonlocal probe_started
        probe_started = True
        raise AssertionError("stdio should not start for a stale call golden")

    monkeypatch.setattr(contract_assertion, "StdioProbe", fail_if_started)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "assert_mobile_mcp_contract.py",
            "--mode",
            "default",
            "--scenarios",
            ".codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-scenarios.yaml",
            "--exceptions",
            ".codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-exceptions.yaml",
            "--bundle-manifest",
            str(bundle_manifest),
            "--golden",
            "tests/fixtures/mobile_mcp_wire_default.json",
            "--calls",
            str(call_golden),
            "--raw-frames",
            str(tmp_path / "frames.jsonl"),
            "--report",
            str(report),
        ],
    )

    assert contract_assertion.main() == 1
    assert probe_started is False
    assert "call golden provenance bundle is stale" in json.loads(report.read_text())["reason"]


def test_scenario_live_artifacts_reference_committed_regular_files() -> None:
    import yaml

    scenarios = yaml.safe_load(
        Path(
            ".codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/"
            "mobile-mcp-black-box-contract-parity-scenarios.yaml"
        ).read_text()
    )
    pending = [scenarios]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            artifacts = value.get("live_artifacts") or {}
            for name in ("upstream", "python", "report"):
                if name in artifacts:
                    assert Path(artifacts[name]).is_file(), f"{value.get('id', '<unknown>')}.{name}: {artifacts[name]}"
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)


def test_default_tool_objects_match_upstream_wire_golden(monkeypatch) -> None:
    import json

    from pymobile_mcp.tools import list_tool_specs

    monkeypatch.delenv("MOBILEFLEET_ENABLE", raising=False)
    expected = json.loads(Path("tests/fixtures/mobile_mcp_wire_default.json").read_text())["list_tools"]["tools"]
    actual = [spec.to_mcp_tool().model_dump(by_alias=True, exclude_none=True) for spec in list_tool_specs()]
    assert actual == expected


def test_fleet_tool_objects_match_upstream_wire_golden(monkeypatch) -> None:
    import json

    from pymobile_mcp.tools import list_tool_specs

    monkeypatch.setenv("MOBILEFLEET_ENABLE", "1")
    expected = json.loads(Path("tests/fixtures/mobile_mcp_wire_fleet.json").read_text())["list_tools"]["tools"]
    actual = [spec.to_mcp_tool().model_dump(by_alias=True, exclude_none=True) for spec in list_tool_specs()]
    assert actual == expected


@pytest.mark.asyncio
async def test_success_text_contract_uses_upstream_templates() -> None:
    from pymobile_mcp.drivers.base import AppInfo, DeviceInfo, ScreenElement, ScreenElementRect, ScreenSize
    from pymobile_mcp.tools import call_tool
    from pymobile_mcp.tools.android import configure_android_tools_for_tests, reset_android_tools_for_tests

    class Driver:
        platform = "android"

        async def connect(self, capabilities=None): pass
        async def get_screen_size(self): return ScreenSize(1080, 2400, 3)
        async def list_apps(self): return [AppInfo("com.android.settings", "Settings"), AppInfo("com.android.chrome", "Chrome")]
        async def launch_app(self, package_name, locale=None): pass
        async def terminate_app(self, package_name): pass
        async def install_app(self, path): pass
        async def uninstall_app(self, package_name): pass
        async def tap(self, x, y): pass
        async def double_tap(self, x, y): pass
        async def long_press(self, x, y, duration=0.5): pass
        async def swipe(self, *coordinates): pass
        async def type_keys(self, text, submit): pass
        async def get_elements_on_screen(self):
            return [ScreenElement("Button", ScreenElementRect(1, 2, 3, 4), text="OK", identifier="ok", focused=False)]
        async def press_button(self, button): pass
        async def open_url(self, url): pass
        async def set_orientation(self, orientation): pass
        async def get_orientation(self): return "portrait"
        async def screenshot(self): return b"not-used"
        async def list_crashes(self): return [{"processName": "Demo", "timestamp": "2026-07-12T00:00:00Z", "id": "crash-1"}]
        async def get_crash(self, crash_id): return "crash body"

    configure_android_tools_for_tests(
        lambda: [DeviceInfo("emulator-5554", "Pixel", "android", "real", "16", "online")],
        lambda device_id: Driver(),
    )
    cases = [
        ("mobile_get_screen_size", {"device": "emulator-5554"}, "Screen size is 1080x2400 pixels"),
        ("mobile_list_apps", {"device": "emulator-5554"}, "Found these apps on device: Settings (com.android.settings), Chrome (com.android.chrome)"),
        ("mobile_launch_app", {"device": "emulator-5554", "packageName": "com.android.chrome"}, "Launched app com.android.chrome"),
        ("mobile_terminate_app", {"device": "emulator-5554", "packageName": "com.android.chrome"}, "Terminated app com.android.chrome"),
        ("mobile_install_app", {"device": "emulator-5554", "path": "/tmp/demo.apk"}, "Installed app from /tmp/demo.apk"),
        ("mobile_uninstall_app", {"device": "emulator-5554", "bundle_id": "com.example.demo"}, "Uninstalled app com.example.demo"),
        ("mobile_click_on_screen_at_coordinates", {"device": "emulator-5554", "x": "10", "y": "20"}, "Clicked on screen at coordinates: 10, 20"),
        ("mobile_double_tap_on_screen", {"device": "emulator-5554", "x": "10", "y": "20"}, "Double-tapped on screen at coordinates: 10, 20"),
        ("mobile_long_press_on_screen_at_coordinates", {"device": "emulator-5554", "x": 10, "y": 20}, "Long pressed on screen at coordinates: 10, 20 for 500ms"),
        ("mobile_list_elements_on_screen", {"device": "emulator-5554"}, 'Found these elements on screen: [{"type":"Button","text":"OK","label":null,"name":null,"value":null,"identifier":"ok","coordinates":{"x":1,"y":2,"width":3,"height":4}}]'),
        ("mobile_press_button", {"device": "emulator-5554", "button": "HOME"}, "Pressed the button: HOME"),
        ("mobile_open_url", {"device": "emulator-5554", "url": "https://example.com"}, "Opened URL: https://example.com"),
        ("mobile_set_orientation", {"device": "emulator-5554", "orientation": "landscape"}, "Changed device orientation to landscape"),
        ("mobile_get_orientation", {"device": "emulator-5554"}, "Current device orientation is portrait"),
        ("mobile_list_crashes", {"device": "emulator-5554"}, '[{"processName":"Demo","timestamp":"2026-07-12T00:00:00Z","id":"crash-1"}]'),
        ("mobile_get_crash", {"device": "emulator-5554", "id": "crash-1"}, "crash body"),
    ]
    try:
        for name, arguments, expected in cases:
            result = await call_tool(name, arguments)
            assert result[0].text == expected, name
    finally:
        reset_android_tools_for_tests()


@pytest.mark.asyncio
async def test_screenshot_without_scaling_preserves_png(monkeypatch) -> None:
    import base64

    from pymobile_mcp.tools import contract

    data = Path("tests/fixtures/mobile_mcp/input-1080x2400.png").read_bytes()
    monkeypatch.setattr(contract, "_scaling_available", lambda: False)
    actual = contract.screenshot(data, 3)
    assert actual.mimeType == "image/png"
    assert base64.b64decode(actual.data) == data


@pytest.mark.asyncio
async def test_screenshot_sips_bytes_match_upstream_call_golden() -> None:
    from pymobile_mcp.tools import contract

    if not contract._sips_available():
        pytest.skip("Sips backend unavailable; CMD-008 remains the real-backend gate")
    import json

    from pymobile_mcp.drivers.base import DeviceInfo, ScreenSize
    from pymobile_mcp.tools import call_tool
    from pymobile_mcp.tools.android import configure_android_tools_for_tests, reset_android_tools_for_tests

    class Driver:
        platform = "android"
        async def connect(self, capabilities=None): pass
        async def get_screen_size(self): return ScreenSize(1080, 2400, 3)
        async def screenshot(self): return Path("tests/fixtures/mobile_mcp/input-1080x2400.png").read_bytes()

    configure_android_tools_for_tests(
        lambda: [DeviceInfo("emulator-5554", "Pixel", "android", "emulator", "16", "online")],
        lambda device_id: Driver(),
    )
    try:
        actual = (await call_tool("mobile_take_screenshot", {"device": "emulator-5554"}))[0].model_dump(by_alias=True, exclude_none=True)
    finally:
        reset_android_tools_for_tests()
    expected = json.loads(Path("tests/fixtures/mobile_mcp_call_results.json").read_text())["calls"]["S-TAKE-JPEG-SIPS"]["content"][0]
    assert actual == expected


@pytest.mark.asyncio
async def test_unexpected_screenshot_error_sets_is_error_true() -> None:
    from pymobile_mcp.drivers.base import DeviceInfo, ScreenSize
    from pymobile_mcp.tools import call_tool
    from pymobile_mcp.tools.android import configure_android_tools_for_tests, reset_android_tools_for_tests

    class Driver:
        async def connect(self, capabilities=None): pass
        async def get_screen_size(self): return ScreenSize(1, 1, 1)
        async def screenshot(self): return b"invalid"

    configure_android_tools_for_tests(lambda: [DeviceInfo("d", "d", "android", "emulator", "1", "online")], lambda _: Driver())
    try:
        result = await call_tool("mobile_take_screenshot", {"device": "d"})
    finally:
        reset_android_tools_for_tests()
    assert result.model_dump(by_alias=True, exclude_none=True) == {
        "content": [{"type": "text", "text": "Error: Not a valid PNG file"}],
        "isError": True,
    }


@pytest.mark.asyncio
async def test_remote_tool_is_unknown_without_fleet_env(monkeypatch) -> None:
    from pymobile_mcp.tools import call_tool

    monkeypatch.delenv("MOBILEFLEET_ENABLE", raising=False)
    result = await call_tool("mobile_list_remote_devices", {})
    assert result.isError is True
    assert result.content[0].text == "MCP error -32602: Tool mobile_list_remote_devices not found"


@pytest.mark.asyncio
async def test_zero_distance_uses_android_default_but_ios_zero() -> None:
    from pymobile_mcp.drivers.base import DeviceInfo, ScreenSize
    from pymobile_mcp.tools import call_tool
    from pymobile_mcp.tools.android import configure_android_tools_for_tests, reset_android_tools_for_tests

    for platform, expected_end_x in (("android", 176.0), ("ios", 500.0)):
        actions = []
        class Driver:
            async def connect(self, capabilities=None): pass
            async def get_screen_size(self): return ScreenSize(1080, 2400)
            async def swipe(self, *values): actions.append(values)
        driver = Driver()
        driver.platform = platform
        device = "ios-1" if platform == "ios" else "emulator-5554"
        configure_android_tools_for_tests(lambda: [DeviceInfo(device, device, platform, "real", "1", "online")], lambda _: driver)
        try:
            await call_tool("mobile_swipe_on_screen", {"device": device, "direction": "left", "x": 500, "y": 1000, "distance": 0})
        finally:
            reset_android_tools_for_tests()
        assert actions[0][2] == expected_end_x

    actions = []
    driver = Driver()
    driver.platform = "android"
    configure_android_tools_for_tests(lambda: [DeviceInfo("emulator-5554", "Pixel", "android", "emulator", "1", "online")], lambda _: driver)
    try:
        await call_tool("mobile_swipe_on_screen", {"device": "emulator-5554", "direction": "up", "x": 10})
    finally:
        reset_android_tools_for_tests()
    assert actions == [(540, 1920, 540, 480)]

def test_stdio_negotiates_protocol_and_supports_ping() -> None:
    sys.path.insert(0, str(Path("scripts").resolve()))
    from contract_common import StdioProbe

    for requested, expected in (("2024-11-05", "2024-11-05"), ("1900-01-01", "2025-11-25")):
        probe = StdioProbe([sys.executable, "-m", "pymobile_mcp.cli", "run"], Path.cwd(), {**os.environ, "PYTHONPATH": "src"}, 10)
        try:
            result = probe.request(1, "initialize", {"protocolVersion": requested, "capabilities": {}, "clientInfo": {"name": "review", "version": "1"}})
            assert result["protocolVersion"] == expected
            probe.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
            assert probe.request(2, "ping", {}) == {}
        finally:
            probe.close()


@pytest.mark.parametrize(
    ("request_id", "sign", "golden_key"),
    (
        (5001, "", "R-COERCE-5000-DIGIT-POSITIVE"),
        (5002, "-", "R-COERCE-5000-DIGIT-NEGATIVE"),
    ),
)
def test_stdio_returns_call_tool_result_for_5000_digit_integers(request_id: int, sign: str, golden_key: str) -> None:
    import json

    sys.path.insert(0, str(Path("scripts").resolve()))
    from contract_common import StdioProbe

    expected = json.loads(Path("tests/fixtures/mobile_mcp_call_results.json").read_text())["review"][golden_key]
    probe = StdioProbe([sys.executable, "-m", "pymobile_mcp.cli", "run"], Path.cwd(), {**os.environ, "PYTHONPATH": "src"}, 3)
    try:
        probe.initialize()
        integer = sign + "1" + "0" * 4999
        probe.send_raw(
            f'{{"jsonrpc":"2.0","id":{request_id},"method":"tools/call","params":'
            f'{{"name":"mobile_click_on_screen_at_coordinates","arguments":'
            f'{{"device":"emulator-5554","x":{integer},"y":20}}}}}}'
        )
        response = probe.receive(request_id)
        assert response == {"jsonrpc": "2.0", "id": request_id, "result": expected}
    finally:
        probe.close()


def test_stdio_parse_int_preserves_normal_integers_and_maps_digit_limit_overflow() -> None:
    import math

    from pymobile_mcp.stdio import _parse_int

    normal = _parse_int("123")
    assert type(normal) is int and normal == 123
    assert _parse_int("1" * 5000) == math.inf
    assert _parse_int("-" + "1" * 5000) == -math.inf

@pytest.mark.asyncio
async def test_zod_number_coercion_preserves_fraction_and_url_raw_prefix(monkeypatch) -> None:
    from pymobile_mcp.drivers.base import DeviceInfo
    from pymobile_mcp.tools import call_tool
    from pymobile_mcp.tools.android import configure_android_tools_for_tests, reset_android_tools_for_tests
    from pymobile_mcp.tools.recording import reset_recording_state_for_tests

    taps = []
    limits = []
    urls = []
    class Driver:
        platform = "android"
        async def connect(self, capabilities=None): pass
        async def tap(self, x, y): taps.append(x)
        async def open_url(self, url): urls.append(url)
        async def start_recording(self, remote_path, time_limit=None): limits.append(time_limit); return object()
    configure_android_tools_for_tests(lambda: [DeviceInfo("d", "d", "android", "emulator", "1", "online")], lambda _: Driver())
    monkeypatch.delenv("MOBILEMCP_ALLOW_UNSAFE_URLS", raising=False)
    try:
        for raw, expected in (("", 0), ("  ", 0), (None, 0), (True, 1), ([], 0), ([5], 5)):
            result = await call_tool("mobile_click_on_screen_at_coordinates", {"device": "d", "x": raw, "y": 20})
            assert result.isError is None
            assert taps[-1] == expected
        for raw in (float("inf"), float("nan"), "Infinity"):
            assert (await call_tool("mobile_click_on_screen_at_coordinates", {"device": "d", "x": raw, "y": 20})).isError is True
        started = await call_tool("mobile_start_screen_recording", {"device": "d", "output": "/tmp/review-fraction.mp4", "timeLimit": 1.9})
        assert started.isError is None
        assert limits == [1.9]
        uppercase = await call_tool("mobile_open_url", {"device": "d", "url": "HTTP://example.com"})
        assert uppercase.content[0].text.startswith("Only http:// and https:// URLs are allowed")
        assert (await call_tool("mobile_open_url", {"device": "d", "url": "https://"})).content[0].text == "Opened URL: https://"
        assert urls == ["https://"]
    finally:
        reset_recording_state_for_tests()
        reset_android_tools_for_tests()


def test_json_domain_number_and_raw_type_names() -> None:
    import yaml
    from pymobile_mcp.stdio import _argument_error
    from pymobile_mcp.tools.registry import _coerce_js_number, _NonFiniteNumber

    with pytest.raises(ValueError):
        _coerce_js_number("+0x10")
    assert _coerce_js_number([[5]]) == 5
    for text in ("1_000", "infinity"):
        with pytest.raises(ValueError):
            _coerce_js_number(text)
    with pytest.raises(_NonFiniteNumber) as huge:
        _coerce_js_number(10**400)
    assert huge.value.received == "Infinity"
    with pytest.raises(_NonFiniteNumber) as negative_huge:
        _coerce_js_number(-(10**400))
    assert negative_huge.value.received == "Infinity"
    with pytest.raises(_NonFiniteNumber) as negative_infinity:
        _coerce_js_number("-Infinity")
    assert negative_infinity.value.received == "Infinity"
    with pytest.raises(_NonFiniteNumber) as nan:
        _coerce_js_number(float("nan"))
    assert nan.value.received == "NaN"
    for value, name in (("raw", "string"), (5, "number"), (True, "boolean"), (None, "null"), ([], "array")):
        error = _argument_error({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "mobile_get_screen_size", "arguments": value}})
        assert f"received {name}" in error["error"]["message"]
    manifest = yaml.safe_load(Path(".codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-scenarios.yaml").read_text())
    review_cases = {case["id"]: case for case in manifest["review_cases"]}
    assert review_cases["R-COERCE-HUGE-NEGATIVE-INTEGER"]["arguments"]["x"] == -(10**400)
    radix = review_cases["R-COERCE-RADIX-OVERFLOW"]["arguments"]["x"]
    assert radix.startswith("0x") and set(radix[2:]) == {"f"} and len(radix) >= 402


@pytest.mark.parametrize(("prefix", "digit"), (("0x", "f"), ("0b", "1"), ("0o", "7")))
def test_js_number_radix_overflow_is_non_finite(prefix: str, digit: str) -> None:
    from pymobile_mcp.tools.registry import _coerce_js_number, _NonFiniteNumber

    with pytest.raises(_NonFiniteNumber) as overflow:
        _coerce_js_number(prefix + digit * 1400)
    assert overflow.value.received == "Infinity"


@pytest.mark.asyncio
async def test_zod_validation_aggregates_all_field_issues() -> None:
    from pymobile_mcp.tools import call_tool

    result = await call_tool("mobile_long_press_on_screen_at_coordinates", {"device": "d", "x": "bad", "y": "bad", "duration": 0})
    assert result.isError is True
    assert result.content[0].text.count('"code"') == 3


@pytest.mark.asyncio
async def test_ios_real_and_simulator_use_wda_screen_scale(monkeypatch) -> None:
    from pymobile_mcp.drivers.ios import IOSDriver
    from pymobile_mcp.drivers.ios_simulator import IOSSimulatorDriver

    payload = {"value": {"screenSize": {"width": 1179, "height": 2556}, "scale": 3}}
    deleted = []
    class Client:
        async def _request_json(self, method, path, body):
            if method == "DELETE":
                deleted.append(path)
                return {"value": None}
            assert path.endswith("/wda/screen")
            return payload
    real = IOSDriver("ios-1")
    real._client = Client()
    real._connected = True
    real._rsd = object()
    real._session_id = "session"
    assert (await real.get_screen_size()).scale == 3
    await real.disconnect()
    assert deleted == ["/session/session"]

    simulator = IOSSimulatorDriver("sim-1")
    simulator._session_id = "session"
    monkeypatch.setattr(simulator, "_request", lambda method, path, body: payload["value"])
    size = await simulator.get_screen_size()
    assert (size.width, size.height, size.scale) == (1179, 2556, 3)


@pytest.mark.asyncio
async def test_ios_safari_fallback_sessions_are_deleted_each_time() -> None:
    from pymobile_mcp.drivers.ios import IOSDriver

    created = []
    deleted = []
    class Client:
        async def _request_json(self, method, path, body):
            if method == "POST" and path.endswith(("/url", "/wda/url")):
                raise RuntimeError("url endpoint unavailable")
            if method == "POST" and path == "/session":
                session = f"safari-{len(created) + 1}"
                created.append(session)
                return {"sessionId": session}
            if method == "DELETE":
                deleted.append(path)
                return {"value": None}
            raise AssertionError((method, path))
    driver = IOSDriver("ios-1")
    driver._client = Client()
    driver._connected = True
    driver._rsd = object()
    driver._session_id = "base"
    await driver.open_url("https://example.com/1")
    await driver.open_url("https://example.com/2")
    assert created == ["safari-1", "safari-2"]
    assert deleted == ["/session/safari-1", "/session/safari-2"]
@pytest.mark.asyncio
async def test_temporary_driver_is_disconnected_after_each_call() -> None:
    from pymobile_mcp.drivers.base import DeviceInfo, ScreenSize
    from pymobile_mcp.tools import call_tool
    from pymobile_mcp.tools.android import configure_android_tools_for_tests, reset_android_tools_for_tests

    connected = 0
    disconnected = 0
    class Driver:
        async def connect(self, capabilities=None):
            nonlocal connected
            connected += 1
        async def disconnect(self):
            nonlocal disconnected
            disconnected += 1
        async def get_screen_size(self): return ScreenSize(100, 200)
    configure_android_tools_for_tests(lambda: [DeviceInfo("ios-1", "iPhone", "ios", "real", "18", "online")], lambda _: Driver())
    try:
        await call_tool("mobile_get_screen_size", {"device": "ios-1"})
        await call_tool("mobile_get_screen_size", {"device": "ios-1"})
    finally:
        reset_android_tools_for_tests()
    assert (connected, disconnected) == (2, 2)


def test_missing_external_upstream_checkout_is_explicitly_skipped(tmp_path) -> None:
    with pytest.raises(pytest.skip.Exception, match="external upstream checkout unavailable"):
        _require_upstream_checkout(tmp_path / "missing-upstream")


def test_source_coverage_negative_guards_reject_missing_case_wrong_exception_and_stale_bundle(tmp_path) -> None:
    import copy
    import json
    import shutil

    import yaml

    sys.path.insert(0, str(Path("scripts").resolve()))
    sys.path.insert(0, str(Path("tests").resolve()))
    from contract_common import ExceptionBlockedError, compute_bundle, validate_exception_ledger
    from validate_mobile_mcp_source_coverage import backend_inventory_summary, backend_source_inventory, validate_bidirectional_inventory, validate_branch_groups, validate_exception_scope
    from mobile_mcp_scenario_runner import validate_effects

    scenarios = yaml.safe_load(Path(".codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-scenarios.yaml").read_text())
    ledger = yaml.safe_load(Path(".codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-exceptions.yaml").read_text())
    upstream_root = _require_upstream_checkout()
    upstream = upstream_root / "src"
    missing = copy.deepcopy(scenarios)
    missing["validation_and_error_cases"] = [case for case in missing["validation_and_error_cases"] if case["id"] != "E-BAD-DIRECTION"]
    ids = {case["id"] for group in ("wire_cases", "call_cases", "validation_and_error_cases") for case in missing[group]}
    _, missing_errors = validate_branch_groups(upstream_root, missing, ids)
    assert any("schema_enum: mapped cases missing" in error for error in missing_errors)

    # The fixed upstream source is an external review oracle, not a unit-test dependency.
    (tmp_path / "src").mkdir()
    server_lines = (upstream / "server.ts").read_text().splitlines()
    server_lines.insert(839, '\t\t\treturn "unmapped-review-branch";')
    (tmp_path / "src/server.ts").write_text("\n".join(server_lines) + "\n")
    (tmp_path / "src/image-utils.ts").write_text((upstream / "image-utils.ts").read_text())
    _, inventory_errors = validate_bidirectional_inventory(tmp_path, scenarios)
    assert any("return inventory mismatch" in error for error in inventory_errors)

    repo_copy = tmp_path / "repo/src/pymobile_mcp/drivers"
    repo_copy.mkdir(parents=True)
    for name in ("android.py", "ios.py", "ios_simulator.py"):
        shutil.copy(Path("src/pymobile_mcp/drivers") / name, repo_copy / name)
    with (repo_copy / "ios_simulator.py").open("a") as stream:
        stream.write('\n_simctl("review-unmapped-backend")\n')
    mutated_backend = backend_inventory_summary(backend_source_inventory(upstream_root, tmp_path / "repo"))
    assert mutated_backend != scenarios["source_coverage"]["backend_inventory_manifest"]

    click = next(case for case in scenarios["call_cases"] if case["id"] == "S-CLICK-COERCE")
    impossible = copy.deepcopy(click)
    impossible["expected_effects"][0]["args"] = [999, 999]
    actual_effects = [{"kind": "effect", "method": "tap", "args": [10, 20], "arg_types": ["number", "number"]}]
    assert validate_effects(impossible, actual_effects, "exact")

    wrong_ledger = copy.deepcopy(ledger)
    wrong_ledger["exceptions"][0]["allowed_case_ids"].pop()
    _, exception_errors = validate_exception_scope(scenarios, wrong_ledger)
    assert any("allowed_case_ids mismatch" in error for error in exception_errors)

    pending_ledger = copy.deepcopy(ledger)
    pending_ledger["exceptions"][0]["approval"] = "pending"
    with pytest.raises(ExceptionBlockedError):
        validate_exception_ledger(scenarios, pending_ledger)

    assert compute_bundle(scenarios) != json.loads("{}")


@pytest.mark.parametrize(
    ("filename", "mutation"),
    [
        ("android.py", '\nadbutils.adb.device(\n    "review"\n).shell(\n    ["id"]\n)\n'),
        ("ios_simulator.py", '\nsubprocess.run(\n    ["xcrun", "simctl", "list"]\n)\n'),
    ],
)
def test_full_source_coverage_rejects_direct_backend_sink_mutations(tmp_path, filename, mutation) -> None:
    import json
    import shutil

    upstream = _require_upstream_checkout()
    root = Path.cwd().resolve()
    sandbox = tmp_path / "repo"
    drivers = sandbox / "src/pymobile_mcp/drivers"
    drivers.mkdir(parents=True)
    for name in ("android.py", "ios.py", "ios_simulator.py"):
        shutil.copy(root / "src/pymobile_mcp/drivers" / name, drivers / name)
    with (drivers / filename).open("a") as stream:
        stream.write(mutation)
    for name in (".codestable", "scripts", "tests"):
        (sandbox / name).symlink_to(root / name, target_is_directory=True)

    report = sandbox / "mutation-report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/validate_mobile_mcp_source_coverage.py"),
            "--source", str(upstream),
            "--expected-revision", "c5d7d27fd61e4762e15ae4b1c68b6c011be88bb7",
            "--scenarios", str(root / ".codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-scenarios.yaml"),
            "--exceptions", str(root / ".codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-exceptions.yaml"),
            "--bundle-manifest", str(root / "tests/fixtures/mobile_mcp/bundle-manifest.json"),
            "--timeout", "30",
            "--report", str(report),
        ],
        cwd=sandbox,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 1, completed.stderr
    assert "backend inventory mismatch" in completed.stderr
    mutation_entries = json.loads(report.read_text())["backend_inventory"]
    assert any(
        entry["identity"] == f"python:drivers/{filename}"
        and entry["line"] > 0
        and ("review" in entry["source"] or '["xcrun", "simctl", "list"]' in entry["source"])
        for entry in mutation_entries
    )


def test_image_compare_uses_production_formatter_and_perfect_report_is_strict_json(tmp_path, monkeypatch) -> None:
    import base64

    sys.path.insert(0, str(Path("scripts").resolve()))
    import compare_mobile_mcp_image_backends as compare
    from contract_common import write_json

    called = []
    monkeypatch.setattr(
        compare.contract,
        "screenshot",
        lambda data, scale: called.append((data, scale))
        or compare.ImageContent(type="image", data=base64.b64encode(b"jpeg").decode(), mimeType="image/jpeg"),
    )
    fixture = Path("tests/fixtures/mobile_mcp/input-1080x2400.png")
    output = tmp_path / "python.jpg"
    compare._python(fixture, 3, "sips", output, 5)
    assert called and output.read_bytes() == b"jpeg"

    psnr = compare._psnr(fixture, fixture)
    assert psnr >= 35
    report = tmp_path / "perfect-report.json"
    write_json(report, {"status": "passed", "psnr_db": compare._json_psnr(psnr)})
    parsed = json.loads(
        report.read_text(),
        parse_constant=lambda value: pytest.fail(f"non-RFC JSON constant: {value}"),
    )
    assert parsed == {"psnr_db": "Infinity", "status": "passed"}


def test_machine_report_writer_rejects_non_finite_numbers_and_image_backend_availability(tmp_path, monkeypatch) -> None:
    sys.path.insert(0, str(Path("scripts").resolve()))
    import compare_mobile_mcp_image_backends as compare
    from contract_common import ExceptionBlockedError, write_json

    with pytest.raises(ValueError, match="Out of range float values"):
        write_json(tmp_path / "invalid.json", {"value": float("nan")})

    compare._require_backends(["sips"], {"sips": "sips-1", "imagemagick": None})
    compare._require_backends(["imagemagick"], {"sips": None, "imagemagick": "magick-1"})
    compare._require_backends(["sips_fallback"], {"sips": "sips-1", "imagemagick": "magick-1"})
    for mode, versions in (
        ("sips", {"sips": None, "imagemagick": "magick-1"}),
        ("imagemagick", {"sips": "sips-1", "imagemagick": None}),
        ("sips_fallback", {"sips": "sips-1", "imagemagick": None}),
    ):
        with pytest.raises(ExceptionBlockedError):
            compare._require_backends([mode], versions)

    monkeypatch.setattr(compare.contract, "_sips_available", lambda: True)
    monkeypatch.setattr(compare.contract, "_run_sips", lambda data, width: (_ for _ in ()).throw(RuntimeError("broken sips")))
    with pytest.raises(RuntimeError, match="must not fall back"):
        compare._python(Path("tests/fixtures/mobile_mcp/input-1080x2400.png"), 3, "sips", tmp_path / "never.jpg", 5)


@pytest.mark.asyncio
async def test_effect_evidence_uses_production_screenshot_adb_wda_and_simctl_seams(tmp_path, monkeypatch) -> None:
    from pymobile_mcp.drivers.android import AndroidDriver
    from pymobile_mcp.drivers.base import DeviceInfo
    from pymobile_mcp.drivers.ios import IOSDriver
    from pymobile_mcp.drivers import ios_simulator
    from pymobile_mcp.tools import android as android_tools

    writes = []

    class ScreenshotDriver:
        async def connect(self, capabilities=None): pass
        async def screenshot(self): return b"production-screenshot-bytes"

    android_tools.configure_android_tools_for_tests(
        lambda: [DeviceInfo("d", "d", "android", "emulator", "1", "online")],
        lambda _: ScreenshotDriver(),
    )
    monkeypatch.setattr(android_tools, "_write_screenshot", lambda path, data: writes.append((path, data)))
    target = tmp_path / "proof.png"
    try:
        await android_tools.save_screenshot({"device": "d", "saveTo": str(target)})
    finally:
        android_tools.reset_android_tools_for_tests()
    assert writes == [(target.resolve(), b"production-screenshot-bytes")]

    adb_calls = []

    class Adb:
        def shell(self, argv): adb_calls.append(argv)

    android = AndroidDriver("emulator-5554")
    monkeypatch.setattr(android, "_adb", lambda: Adb())
    await android.swipe(10, 20, 30, 40)
    assert adb_calls == [["input", "swipe", "10", "20", "30", "40", "1000"]]

    wda_calls = []

    class WdaClient:
        async def _request_json(self, method, path, body):
            wda_calls.append((method, path, body))
            return {"value": None}

    ios = IOSDriver("ios-1")
    ios._client = WdaClient()
    ios._connected = True
    ios._rsd = object()
    ios._session_id = "session"
    await ios.swipe(10, 20, 30, 40)
    assert wda_calls == [
        (
            "POST",
            "/session/session/actions",
            {
                "actions": [
                    {
                        "type": "pointer",
                        "id": "finger1",
                        "parameters": {"pointerType": "touch"},
                        "actions": [
                            {"type": "pointerMove", "duration": 0, "x": 10, "y": 20},
                            {"type": "pointerDown", "button": 0},
                            {"type": "pointerMove", "duration": 1000, "x": 30, "y": 40},
                            {"type": "pointerUp", "button": 0},
                        ],
                    }
                ]
            },
        ),
        ("DELETE", "/session/session/actions", None),
    ]

    simctl_calls = []
    process = object()

    async def create_process(*argv, **kwargs):
        simctl_calls.append((argv, kwargs))
        return process

    monkeypatch.setattr(ios_simulator, "_create_subprocess_exec", create_process)
    actual = await ios_simulator.start_simctl_recording("sim-1", "/tmp/out.mp4")
    assert actual is process
    assert simctl_calls == [
        (
            ("xcrun", "simctl", "io", "sim-1", "recordVideo", "/tmp/out.mp4"),
            {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL},
        )
    ]

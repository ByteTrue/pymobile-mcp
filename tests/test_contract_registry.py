from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from pymobile_mcp.tools import CORE_TOOL_NAMES, call_tool, list_tool_specs
from mcp import types

from pymobile_mcp.server import PyMobileMCPServer
from pymobile_mcp.tools import register_tool_handler, unregister_tool_handler

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "mobile_mcp_core_tools.json").read_text())
STDIO_ENV = {"PYTHONPATH": "src"}
ANDROID_TOOL_NAMES = {
    "mobile_list_available_devices",
    "mobile_get_screen_size",
    "mobile_take_screenshot",
    "mobile_list_elements_on_screen",
    "mobile_click_on_screen_at_coordinates",
    "mobile_double_tap_on_screen",
    "mobile_long_press_on_screen_at_coordinates",
    "mobile_swipe_on_screen",
    "mobile_type_keys",
    "mobile_list_apps",
    "mobile_launch_app",
    "mobile_terminate_app",
    "mobile_install_app",
    "mobile_uninstall_app",
    "mobile_press_button",
    "mobile_open_url",
    "mobile_get_orientation",
    "mobile_set_orientation",
    "mobile_save_screenshot",
    "mobile_start_screen_recording",
    "mobile_stop_screen_recording",
    "mobile_list_crashes",
    "mobile_get_crash",
}


def _fields(spec):
    properties = spec.input_schema["properties"]
    required = set(spec.input_schema.get("required", []))
    return required, set(properties) - required


def _valid_args(spec):
    return {field: "up" if field == "direction" else "portrait" if field == "orientation" else "demo" for field in spec.input_schema["required"]}


def _assert_error_content(content, code, tool, details=None):
    assert content[0].type == "text"
    payload = json.loads(content[0].text)
    assert payload["status"] == "error"
    assert payload["code"] == code
    assert payload["tool"] == tool
    if details is not None:
        assert payload["details"] == details
    return payload


def test_core_tool_names_match_fixture():
    expected = [tool["name"] for tool in FIXTURE["tools"]]
    assert list(CORE_TOOL_NAMES) == expected
    assert len(CORE_TOOL_NAMES) == 23
    assert not set(FIXTURE["excluded_tools"]) & set(CORE_TOOL_NAMES)


@pytest.mark.parametrize("tool", FIXTURE["tools"])
def test_schema_parity_fixture(tool):
    specs = {spec.name: spec for spec in list_tool_specs()}
    spec = specs[tool["name"]]
    required, optional = _fields(spec)

    assert required == set(tool["required"])
    assert optional == set(tool["optional"])

    for annotation in ("readOnlyHint", "destructiveHint"):
        if annotation in tool:
            assert spec.annotations.get(annotation) is tool[annotation]

    for field, values in tool.get("enum", {}).items():
        assert spec.input_schema["properties"][field]["enum"] == values

    if "content_kind" in tool:
        assert spec.content_kind == tool["content_kind"]
    assert "additionalProperties" not in spec.input_schema


@pytest.mark.asyncio
async def test_stub_tools_return_structured_not_implemented_error():
    for name in CORE_TOOL_NAMES:
        spec = next(spec for spec in list_tool_specs() if spec.name == name)
        if name in ANDROID_TOOL_NAMES:
            continue
        content = await call_tool(name, _valid_args(spec))
        _assert_error_content(content, "not_implemented", name)


@pytest.mark.asyncio
async def test_registry_validates_invalid_arguments_before_stub():
    missing = await call_tool("mobile_list_apps", {})
    assert missing.isError is True
    assert "Input validation error" in missing[0].text
    invalid_enum = await call_tool("mobile_swipe_on_screen", {"device": "demo", "direction": "diagonal"})
    assert invalid_enum.isError is True
    assert "invalid_value" in invalid_enum[0].text

@pytest.mark.asyncio
async def test_registered_handler_can_return_success_content():
    from pymobile_mcp.tools.android import get_crash

    async def handler(args):
        return []

    register_tool_handler("mobile_get_crash", handler)
    try:
        content = await call_tool("mobile_get_crash", {"device": "demo", "id": "crash"})
        assert content == []
    finally:
        register_tool_handler("mobile_get_crash", get_crash)


@pytest.mark.asyncio
async def test_android_handlers_with_fake_driver():
    from pymobile_mcp.drivers.base import DeviceInfo, ScreenSize
    from pymobile_mcp.tools.android import configure_android_tools_for_tests, reset_android_tools_for_tests

    actions = []
    class FakeDriver:
        async def connect(self, capabilities=None): pass
        async def get_screen_size(self): return ScreenSize(width=100, height=200)
        async def tap(self, x, y): actions.append((x, y))
    configure_android_tools_for_tests(lambda: [DeviceInfo("android-1", "Pixel", "android", "real", "14", "online")], lambda _: FakeDriver())
    try:
        devices = json.loads((await call_tool("mobile_list_available_devices", {}))[0].text)
        assert devices["devices"][0]["type"] == "emulator"
        assert (await call_tool("mobile_get_screen_size", {"device": "android-1"}))[0].text == "Screen size is 100x200 pixels"
        await call_tool("mobile_click_on_screen_at_coordinates", {"device": "android-1", "x": "10", "y": "20"})
        assert actions == [(10.0, 20.0)]
    finally:
        reset_android_tools_for_tests()


@pytest.mark.asyncio
async def test_server_handlers_list_and_call_tools():
    server = PyMobileMCPServer().mcp
    listed = await server.request_handlers[types.ListToolsRequest](types.ListToolsRequest())
    assert [tool.name for tool in listed.root.tools] == list(CORE_TOOL_NAMES)
    called = await server.request_handlers[types.CallToolRequest](types.CallToolRequest(params=types.CallToolRequestParams(name="mobile_get_page_source", arguments={})))
    assert called.root.isError is True
    assert called.root.content[0].text == "MCP error -32602: Tool mobile_get_page_source not found"


@pytest.mark.asyncio
async def test_server_handlers_validate_required_and_enum_arguments():
    server = PyMobileMCPServer().mcp
    missing = await server.request_handlers[types.CallToolRequest](types.CallToolRequest(params=types.CallToolRequestParams(name="mobile_list_apps", arguments={})))
    assert missing.root.isError is True
    assert "Input validation error" in missing.root.content[0].text
    invalid = await server.request_handlers[types.CallToolRequest](types.CallToolRequest(params=types.CallToolRequestParams(name="mobile_swipe_on_screen", arguments={"device": "demo", "direction": "diagonal"})))
    assert invalid.root.isError is True
    assert "invalid_value" in invalid.root.content[0].text


@pytest.mark.asyncio
@pytest.mark.parametrize(("name", "args"), [("mobile_get_crash", {"device": "demo", "id": "crash"}), ("mobile_get_page_source", {}), ("mobile_swipe_on_screen", {"device": "demo", "direction": "diagonal"})])
async def test_registry_and_server_error_envelopes_match(name, args):
    direct = await call_tool(name, args)
    server = PyMobileMCPServer().mcp
    response = await server.request_handlers[types.CallToolRequest](types.CallToolRequest(params=types.CallToolRequestParams(name=name, arguments=args)))
    assert response.root.model_dump(by_alias=True, exclude_none=True) == direct.model_dump(by_alias=True, exclude_none=True)


@pytest.mark.asyncio
async def test_stdio_client_can_list_and_call_tools():
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    params = StdioServerParameters(command=sys.executable, args=["-m", "pymobile_mcp.cli", "run"], cwd=str(Path.cwd()), env=STDIO_ENV)
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            initialized = await session.initialize()
            assert initialized.serverInfo.name == "mobile-mcp"
            tools = await session.list_tools()
            assert [tool.name for tool in tools.tools] == list(CORE_TOOL_NAMES)
            unknown = await session.call_tool("mobile_get_page_source", {})
            assert unknown.isError is True
            assert unknown.content[0].text == "MCP error -32602: Tool mobile_get_page_source not found"

@pytest.mark.asyncio
async def test_unknown_tool_returns_structured_invalid_argument_error():
    result = await call_tool("mobile_get_page_source", {})
    assert result.isError is True
    assert result[0].text == "MCP error -32602: Tool mobile_get_page_source not found"


def test_server_and_cli_import():
    from pymobile_mcp.cli import main
    from pymobile_mcp.server import PyMobileMCPServer

    assert callable(main)
    assert PyMobileMCPServer().mcp is not None


def test_registry_layer_does_not_import_device_libraries():
    registry_source = Path("src/pymobile_mcp/tools/registry.py").read_text()
    specs_source = Path("src/pymobile_mcp/tools/specs.py").read_text()
    assert "uiautomator2" not in registry_source + specs_source
    assert "pymobiledevice3" not in registry_source + specs_source


def test_url_and_path_validation_helpers(tmp_path, monkeypatch):
    from pymobile_mcp.errors import InvalidArgumentError
    from pymobile_mcp.tools.validation import (
        validate_button,
        validate_orientation,
        validate_output_path,
        validate_recording_output,
        validate_time_limit,
        validate_url,
    )

    assert validate_url("mobile_open_url", "https://example.com") == "https://example.com"
    try:
        validate_url("mobile_open_url", "myapp://home")
        raise AssertionError("expected invalid url")
    except InvalidArgumentError as exc:
        assert "http" in exc.message

    monkeypatch.setenv("MOBILEMCP_ALLOW_UNSAFE_URLS", "1")
    assert validate_url("mobile_open_url", "myapp://home") == "myapp://home"

    assert validate_button("mobile_press_button", "HOME") == "KEYCODE_HOME"
    assert validate_orientation("mobile_set_orientation", "portrait") == "portrait"

    safe = validate_output_path("mobile_save_screenshot", str(tmp_path / "shot.png"))
    assert safe.suffix == ".png"
    try:
        validate_output_path("mobile_save_screenshot", str(tmp_path / "shot.txt"))
        raise AssertionError("expected invalid extension")
    except InvalidArgumentError:
        pass
    try:
        validate_output_path("mobile_save_screenshot", "/etc/passwd.png")
        raise AssertionError("expected unsafe path")
    except InvalidArgumentError:
        pass
    rec = validate_recording_output("mobile_start_screen_recording", str(tmp_path / "clip.mp4"))
    assert rec.suffix == ".mp4"
    try:
        validate_recording_output("mobile_start_screen_recording", str(tmp_path / "clip.mov"))
        raise AssertionError("expected invalid recording extension")
    except InvalidArgumentError:
        pass
    assert validate_time_limit("mobile_start_screen_recording", 5) == 5
    assert validate_time_limit("mobile_start_screen_recording", 0) == 0
    assert validate_time_limit("mobile_start_screen_recording", -1) == -1
    assert validate_time_limit("mobile_start_screen_recording", "5") == 5


@pytest.mark.asyncio
async def test_ios_handlers_with_fake_driver():
    from pymobile_mcp.drivers.base import DeviceInfo, ScreenSize
    from pymobile_mcp.tools.android import configure_android_tools_for_tests, reset_android_tools_for_tests
    actions = []
    class FakeIOS:
        async def connect(self, capabilities=None): pass
        async def get_screen_size(self): return ScreenSize(390, 844, 3)
        async def tap(self, x, y): actions.append((x, y))
    configure_android_tools_for_tests(lambda: [DeviceInfo("ios-1", "iPhone", "ios", "real", "17", "online")], lambda _: FakeIOS())
    try:
        assert (await call_tool("mobile_get_screen_size", {"device": "ios-1"}))[0].text == "Screen size is 390x844 pixels"
        await call_tool("mobile_click_on_screen_at_coordinates", {"device": "ios-1", "x": 1, "y": 2})
        assert actions == [(1.0, 2.0)]
    finally:
        reset_android_tools_for_tests()


def test_parse_wda_source_maps_elements():
    from pymobile_mcp.drivers.ios import parse_wda_source

    elements = parse_wda_source(
        {
            "type": "XCUIElementTypeApplication",
            "rect": {"x": 0, "y": 0, "width": 390, "height": 844},
            "children": [
                {
                    "type": "XCUIElementTypeButton",
                    "label": "Continue",
                    "name": "continue",
                    "rawIdentifier": "btn.continue",
                    "isVisible": "1",
                    "rect": {"x": 5, "y": 6, "width": 7, "height": 8},
                    "children": [],
                }
            ],
        }
    )
    assert len(elements) == 1
    assert elements[0].label == "Continue"
    assert elements[0].identifier == "btn.continue"
    assert elements[0].rect.width == 7


@pytest.mark.asyncio
async def test_ios_parity_tools_return_approved_recording_exception():
    from pymobile_mcp.drivers.base import DeviceInfo
    from pymobile_mcp.drivers.ios import IOSDriver
    from pymobile_mcp.tools.android import configure_android_tools_for_tests, reset_android_tools_for_tests
    class FakeWda:
        def is_running(self): return True
    configure_android_tools_for_tests(lambda: [DeviceInfo("ios-1", "iPhone", "ios", "real", "17", "online")], lambda device: IOSDriver(device, wda=FakeWda()))
    try:
        result = await call_tool("mobile_start_screen_recording", {"device": "ios-1", "output": "/tmp/ios-contract.mp4"})
        assert result.isError is None
        assert result[0].text == "iOS screen recording is not available through pure pymobiledevice3/WDA yet. Please fix the issue and try again."
    finally:
        reset_android_tools_for_tests()


def test_no_go_ios_dependency():
    runtime = "\n".join(path.read_text() for path in Path("src/pymobile_mcp/drivers").rglob("*.py"))
    assert "import go_ios" not in runtime and "from go_ios" not in runtime
    assert "mobilecli" not in runtime
    assert "GO_IOS_PATH" not in runtime


@pytest.mark.asyncio
async def test_ios_system_helpers_with_fake_driver():
    from pymobile_mcp.drivers.base import DeviceInfo
    from pymobile_mcp.tools.android import configure_android_tools_for_tests, reset_android_tools_for_tests
    actions = []
    class FakeIOS:
        async def connect(self, capabilities=None): pass
        async def press_button(self, button): actions.append(("button", button))
        async def open_url(self, url): actions.append(("url", url))
    configure_android_tools_for_tests(lambda: [DeviceInfo("ios-1", "iPhone", "ios", "real", "17", "online")], lambda _: FakeIOS())
    try:
        assert (await call_tool("mobile_press_button", {"device": "ios-1", "button": "HOME"}))[0].text == "Pressed the button: HOME"
        assert (await call_tool("mobile_open_url", {"device": "ios-1", "url": "https://example.com"}))[0].text == "Opened URL: https://example.com"
        assert len(actions) == 2
    finally:
        reset_android_tools_for_tests()


@pytest.mark.asyncio
async def test_ios_app_lifecycle_with_fake_driver():
    from pymobile_mcp.drivers.base import AppInfo, DeviceInfo
    from pymobile_mcp.tools.android import configure_android_tools_for_tests, reset_android_tools_for_tests
    actions = []
    class FakeIOS:
        async def connect(self, capabilities=None): pass
        async def list_apps(self): return [AppInfo("com.example.app", "Example")]
        async def launch_app(self, package_name, locale=None): actions.append(("launch", package_name))
    configure_android_tools_for_tests(lambda: [DeviceInfo("ios-1", "iPhone", "ios", "real", "17", "online")], lambda _: FakeIOS())
    try:
        assert (await call_tool("mobile_list_apps", {"device": "ios-1"}))[0].text == "Found these apps on device: Example (com.example.app)"
        assert (await call_tool("mobile_launch_app", {"device": "ios-1", "packageName": "com.example.app"}))[0].text == "Launched app com.example.app"
        assert actions == [("launch", "com.example.app")]
    finally:
        reset_android_tools_for_tests()


@pytest.mark.asyncio
async def test_ios_crash_tools_with_fake_driver():
    from pymobile_mcp.drivers.base import DeviceInfo
    from pymobile_mcp.tools.android import configure_android_tools_for_tests, reset_android_tools_for_tests
    class FakeIOS:
        async def connect(self, capabilities=None): pass
        async def list_crashes(self): return [{"id": "SpringBoard.ips", "name": "SpringBoard.ips"}]
        async def get_crash(self, crash_id): return f"ios-crash:{crash_id}"
    configure_android_tools_for_tests(lambda: [DeviceInfo("ios-1", "iPhone", "ios", "real", "17", "online")], lambda _: FakeIOS())
    try:
        assert json.loads((await call_tool("mobile_list_crashes", {"device": "ios-1"}))[0].text)[0]["id"] == "SpringBoard.ips"
        assert (await call_tool("mobile_get_crash", {"device": "ios-1", "id": "SpringBoard.ips"}))[0].text == "ios-crash:SpringBoard.ips"
    finally:
        reset_android_tools_for_tests()


def test_android_dropbox_parser():
    from pymobile_mcp.drivers.android import AndroidDriver

    sample = """
Drop box contents: 2 entries

========================================
2026-07-10 01:17:03 system_app_crash (text, 12 bytes)
hello crash

========================================
2026-07-10 01:17:03 system_app_crash (text, 11 bytes)
second one
"""
    driver = AndroidDriver("emulator-5554")
    entries = driver._parse_dropbox_print(sample)
    assert len(entries) == 2
    assert entries[0]["id"] == "2026-07-10 01:17:03::system_app_crash"
    assert entries[1]["id"] == "2026-07-10 01:17:03::system_app_crash#1"
    assert entries[0]["content"] == "hello crash"


def test_android_dropbox_filters_noise():
    from pymobile_mcp.drivers.android import AndroidDriver

    sample = """
========================================
2026-07-10 01:17:03 system_app_crash (text, 5 bytes)
boom

========================================
2026-07-10 01:17:03 system_server_strictmode (text, 4 bytes)
nope

========================================
2026-07-10 01:17:03 SYSTEM_BOOT (text, 4 bytes)
boot

========================================
2026-07-10 01:17:03 data_app_anr (text, 3 bytes)
anr
"""
    driver = AndroidDriver("emulator-5554")
    entries = driver._parse_dropbox_print(sample)
    tags = [e["tag"] for e in entries]
    assert tags == ["system_app_crash", "data_app_anr"]
    all_entries = driver._parse_dropbox_print(sample, include_all=True)
    assert len(all_entries) == 4

    import os
    os.environ["PYMOBILE_MCP_ANDROID_DROPBOX_ALL"] = "1"
    try:
        env_all = driver._parse_dropbox_print(sample)
        assert len(env_all) == 4
    finally:
        os.environ.pop("PYMOBILE_MCP_ANDROID_DROPBOX_ALL", None)

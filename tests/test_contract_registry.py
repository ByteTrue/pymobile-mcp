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
    assert spec.input_schema["additionalProperties"] is False


@pytest.mark.asyncio
async def test_stub_tools_return_structured_not_implemented_error():
    for name in CORE_TOOL_NAMES:
        spec = next(spec for spec in list_tool_specs() if spec.name == name)
        content = await call_tool(name, _valid_args(spec))
        _assert_error_content(content, "not_implemented", name)


@pytest.mark.asyncio
async def test_registry_validates_invalid_arguments_before_stub():
    missing = _assert_error_content(
        await call_tool("mobile_list_apps", {}),
        "invalid_argument",
        "mobile_list_apps",
        {"missing": ["device"]},
    )

    invalid_enum = _assert_error_content(
        await call_tool("mobile_swipe_on_screen", {"device": "demo", "direction": "diagonal"}),
        "invalid_argument",
        "mobile_swipe_on_screen",
    )
    assert invalid_enum["details"]["field"] == "direction"

@pytest.mark.asyncio
async def test_registered_handler_can_return_success_content():
    async def handler(args):
        return []

    register_tool_handler("mobile_list_apps", handler)
    try:
        content = await call_tool("mobile_list_apps", {"device": "demo"})
        assert content == []
    finally:
        unregister_tool_handler("mobile_list_apps")


@pytest.mark.asyncio
async def test_server_handlers_list_and_call_tools():
    server = PyMobileMCPServer().mcp
    listed = await server.request_handlers[types.ListToolsRequest](types.ListToolsRequest())
    names = [tool.name for tool in listed.root.tools]
    assert names == list(CORE_TOOL_NAMES)
    assert "mobile_get_page_source" not in names
    assert not set(FIXTURE["excluded_tools"]) & set(names)

    called = await server.request_handlers[types.CallToolRequest](
        types.CallToolRequest(
            params=types.CallToolRequestParams(
                name="mobile_list_apps",
                arguments={"device": "demo"},
            )
        )
    )
    payload = _assert_error_content(called.root.content, "not_implemented", "mobile_list_apps")
    assert payload["message"] == "mobile_list_apps is registered but not implemented yet."
    assert called.root.isError is False

    unknown = await server.request_handlers[types.CallToolRequest](
        types.CallToolRequest(
            params=types.CallToolRequestParams(
                name="mobile_get_page_source",
                arguments={},
            )
        )
    )
    unknown_payload = _assert_error_content(
        unknown.root.content,
        "invalid_argument",
        "mobile_get_page_source",
        {"tool": "mobile_get_page_source"},
    )
    assert unknown.root.isError is False
    assert unknown_payload["message"] == "Unknown tool: mobile_get_page_source"


@pytest.mark.asyncio
async def test_server_handlers_validate_required_and_enum_arguments():
    server = PyMobileMCPServer().mcp

    missing = await server.request_handlers[types.CallToolRequest](
        types.CallToolRequest(
            params=types.CallToolRequestParams(
                name="mobile_list_apps",
                arguments={},
            )
        )
    )
    missing_payload = _assert_error_content(
        missing.root.content,
        "invalid_argument",
        "mobile_list_apps",
        {"missing": ["device"]},
    )
    assert missing.root.isError is False

    invalid_enum = await server.request_handlers[types.CallToolRequest](
        types.CallToolRequest(
            params=types.CallToolRequestParams(
                name="mobile_swipe_on_screen",
                arguments={"device": "demo", "direction": "diagonal"},
            )
        )
    )
    enum_payload = _assert_error_content(
        invalid_enum.root.content,
        "invalid_argument",
        "mobile_swipe_on_screen",
    )
    assert invalid_enum.root.isError is False
    assert enum_payload["details"]["field"] == "direction"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("name", "args", "code", "tool", "details"),
    [
        ("mobile_list_apps", {"device": "demo"}, "not_implemented", "mobile_list_apps", {}),
        ("mobile_get_page_source", {}, "invalid_argument", "mobile_get_page_source", {"tool": "mobile_get_page_source"}),
        ("mobile_swipe_on_screen", {"device": "demo", "direction": "diagonal"}, "invalid_argument", "mobile_swipe_on_screen", None),
    ],
)
async def test_registry_and_server_error_envelopes_match(name, args, code, tool, details):
    direct = _assert_error_content(await call_tool(name, args), code, tool, details)

    server = PyMobileMCPServer().mcp
    response = await server.request_handlers[types.CallToolRequest](
        types.CallToolRequest(params=types.CallToolRequestParams(name=name, arguments=args))
    )
    via_server = _assert_error_content(response.root.content, code, tool, details)

    assert response.root.isError is False
    assert via_server == direct


@pytest.mark.asyncio
async def test_stdio_client_can_list_and_call_tools():
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "pymobile_mcp.cli", "run"],
        cwd=str(Path.cwd()),
        env=STDIO_ENV,
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [tool.name for tool in tools.tools]
            assert names == list(CORE_TOOL_NAMES)
            assert "mobile_get_page_source" not in names
            assert not set(FIXTURE["excluded_tools"]) & set(names)

            stub = await session.call_tool("mobile_list_apps", {"device": "demo"})
            stub_payload = json.loads(stub.content[0].text)
            assert stub.isError is False
            assert stub.content[0].type == "text"
            assert stub_payload["code"] == "not_implemented"
            assert stub_payload["tool"] == "mobile_list_apps"

            unknown = await session.call_tool("mobile_get_page_source", {})
            unknown_payload = _assert_error_content(
                unknown.content,
                "invalid_argument",
                "mobile_get_page_source",
                {"tool": "mobile_get_page_source"},
            )
            assert unknown.isError is False
            assert unknown_payload["message"] == "Unknown tool: mobile_get_page_source"

            missing = await session.call_tool("mobile_list_apps", {})
            missing_payload = _assert_error_content(
                missing.content,
                "invalid_argument",
                "mobile_list_apps",
                {"missing": ["device"]},
            )
            assert missing.isError is False
            assert missing_payload["message"] == "Missing required argument(s): device"

            invalid_enum = await session.call_tool("mobile_swipe_on_screen", {"device": "demo", "direction": "diagonal"})
            enum_payload = _assert_error_content(
                invalid_enum.content,
                "invalid_argument",
                "mobile_swipe_on_screen",
            )
            assert invalid_enum.isError is False
            assert enum_payload["details"]["field"] == "direction"

@pytest.mark.asyncio
async def test_unknown_tool_returns_structured_invalid_argument_error():
    payload = _assert_error_content(
        await call_tool("mobile_get_page_source", {}),
        "invalid_argument",
        "mobile_get_page_source",
        {"tool": "mobile_get_page_source"},
    )
    assert payload["message"] == "Unknown tool: mobile_get_page_source"


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
    assert "uiautomator2" not in sys.modules
    assert "pymobiledevice3" not in sys.modules

"""Tool dispatch and structured error conversion."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from mcp.types import TextContent

from pymobile_mcp.errors import DriverError, InvalidArgumentError, NotImplementedToolError, ToolError

from .specs import CORE_TOOL_SPECS, ToolSpec

TOOLS_BY_NAME = {spec.name: spec for spec in CORE_TOOL_SPECS}
ToolHandler = Callable[[dict[str, Any]], Awaitable[Sequence[TextContent]]]
TOOL_HANDLERS: dict[str, ToolHandler] = {}


def list_tool_specs() -> tuple[ToolSpec, ...]:
    return CORE_TOOL_SPECS


def get_tool_spec(name: str) -> ToolSpec:
    try:
        return TOOLS_BY_NAME[name]
    except KeyError as exc:
        raise InvalidArgumentError(name, f"Unknown tool: {name}", {"tool": name}) from exc


def register_tool_handler(name: str, handler: ToolHandler) -> None:
    get_tool_spec(name)
    TOOL_HANDLERS[name] = handler


def unregister_tool_handler(name: str) -> None:
    TOOL_HANDLERS.pop(name, None)


def _validate_args(spec: ToolSpec, args: dict[str, Any]) -> None:
    schema = spec.input_schema
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    missing = sorted(required - set(args))
    if missing:
        raise InvalidArgumentError(spec.name, "Missing required argument(s): " + ", ".join(missing), {"missing": missing})

    if schema.get("additionalProperties") is False:
        extra = sorted(set(args) - set(properties))
        if extra:
            raise InvalidArgumentError(spec.name, "Unknown argument(s): " + ", ".join(extra), {"extra": extra})

    for field, value in args.items():
        allowed = properties.get(field, {}).get("enum")
        if allowed is not None and value not in allowed:
            raise InvalidArgumentError(spec.name, f"Invalid value for {field}: {value}", {"field": field, "allowed": allowed})

async def call_tool(name: str, args: dict[str, Any] | None = None) -> Sequence[TextContent]:
    try:
        spec = get_tool_spec(name)
        arguments = args or {}
        _validate_args(spec, arguments)
        handler = TOOL_HANDLERS.get(name)
        if handler is None:
            raise NotImplementedToolError(name)
        return await handler(arguments)
    except ToolError as exc:
        return [_text(exc.to_json())]
    except Exception as exc:
        return [_text(DriverError(name, str(exc)).to_json())]


def _text(value: str) -> TextContent:
    return TextContent(type="text", text=value)

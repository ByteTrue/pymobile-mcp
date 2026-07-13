"""Tool dispatch and structured error conversion."""

from __future__ import annotations

import os
import json
import math
import re

from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from mcp.types import CallToolResult, ImageContent, TextContent

from pymobile_mcp.errors import DriverError, InvalidArgumentError, NotImplementedToolError, ToolError
from pymobile_mcp.tools.contract import actionable, unexpected

from .specs import CORE_TOOL_SPECS, FLEET_TOOL_SPECS, ToolSpec
from .android import cleanup_temporary_drivers, register_android_handlers
from .fleet import register_fleet_handlers

TOOLS_BY_NAME = {spec.name: spec for spec in (*CORE_TOOL_SPECS, *FLEET_TOOL_SPECS)}
ToolHandler = Callable[[dict[str, Any]], Awaitable[Sequence[TextContent | ImageContent]]]
TOOL_HANDLERS: dict[str, ToolHandler] = {}


class ContractCallToolResult(CallToolResult):
    """CallToolResult with list-like access for the in-process registry API."""

    def __getitem__(self, index: int) -> TextContent | ImageContent:
        return self.content[index]

    def __len__(self) -> int:
        return len(self.content)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, list):
            return self.content == other
        return super().__eq__(other)


def list_tool_specs() -> tuple[ToolSpec, ...]:
    if os.environ.get("MOBILEFLEET_ENABLE") == "1":
        return (CORE_TOOL_SPECS[0], *FLEET_TOOL_SPECS, *CORE_TOOL_SPECS[1:])
    return CORE_TOOL_SPECS


def get_tool_spec(name: str) -> ToolSpec:
    if name in {spec.name for spec in FLEET_TOOL_SPECS} and os.environ.get("MOBILEFLEET_ENABLE") != "1":
        raise InvalidArgumentError(name, f"Unknown tool: {name}", {"tool": name})
    try:
        return TOOLS_BY_NAME[name]
    except KeyError as exc:
        raise InvalidArgumentError(name, f"Unknown tool: {name}", {"tool": name}) from exc


def register_tool_handler(name: str, handler: ToolHandler) -> None:
    if name not in TOOLS_BY_NAME:
        raise InvalidArgumentError(name, f"Unknown tool: {name}", {"tool": name})
    TOOL_HANDLERS[name] = handler


def unregister_tool_handler(name: str) -> None:
    TOOL_HANDLERS.pop(name, None)


register_android_handlers(register_tool_handler)
register_fleet_handlers(register_tool_handler)


def _validation_error(tool: str, issues: dict[str, Any] | list[dict[str, Any]]) -> CallToolResult:
    issue_list = issues if isinstance(issues, list) else [issues]
    message = (
        f"MCP error -32602: Input validation error: Invalid arguments for tool {tool}: "
        f"{json.dumps(issue_list, indent=2)}"
    )
    return _result([TextContent(type="text", text=message)], True)

class _NonFiniteNumber(ValueError):
    def __init__(self, value: float) -> None:
        self.received = "NaN" if math.isnan(value) else "Infinity"

_JS_NUMBER_WHITESPACE = "\u0009\u000a\u000b\u000c\u000d\u0020\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000\ufeff"
_JS_DECIMAL_NUMBER = re.compile(r"[+-]?(?:(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?|Infinity)\Z")
_JS_RADIX_NUMBERS = (
    (re.compile(r"0[xX][0-9a-fA-F]+\Z"), 16),
    (re.compile(r"0[bB][01]+\Z"), 2),
    (re.compile(r"0[oO][0-7]+\Z"), 8),
)

def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _js_array_string(value: list[Any]) -> str:
    def stringify(item: Any) -> str:
        if item is None:
            return ""
        if isinstance(item, list):
            return _js_array_string(item)
        if isinstance(item, bool):
            return "true" if item else "false"
        if isinstance(item, dict):
            return "[object Object]"
        return str(item)

    return ",".join(stringify(item) for item in value)
def _coerce_js_number(value: Any) -> float:
    if value is None:
        number = 0.0
    elif isinstance(value, bool):
        number = 1.0 if value else 0.0
    elif isinstance(value, int):
        try:
            number = float(value)
        except OverflowError:
            raise _NonFiniteNumber(math.inf if value >= 0 else -math.inf) from None
    elif isinstance(value, float):
        number = value
    else:
        if isinstance(value, list):
            text = _js_array_string(value)
        elif isinstance(value, str):
            text = value
        else:
            raise ValueError
        text = text.strip(_JS_NUMBER_WHITESPACE)
        if not text:
            number = 0.0
        elif radix := next(((pattern, base) for pattern, base in _JS_RADIX_NUMBERS if pattern.fullmatch(text)), None):
            number = _coerce_js_number(int(text[2:], radix[1]))
        elif _JS_DECIMAL_NUMBER.fullmatch(text):
            number = float(text)
        else:
            raise ValueError
    if not math.isfinite(number):
        raise _NonFiniteNumber(number)
    return number

def _validate_args(spec: ToolSpec, args: dict[str, Any]) -> tuple[dict[str, Any], CallToolResult | None]:
    properties = spec.input_schema.get("properties", {})
    normalized = {field: value for field, value in args.items() if field in properties}
    issues: list[dict[str, Any]] = []
    for field in spec.input_schema.get("required", []):
        if field not in normalized:
            expected = properties[field].get("type", "string")
            issues.append({"expected": expected, "code": "invalid_type", "path": [field], "message": f"Invalid input: expected {expected}, received undefined"})
    for field, field_schema in properties.items():
        if field not in normalized:
            continue
        value = normalized[field]
        expected_type = field_schema.get("type")
        valid_type = True
        if expected_type == "number":
            try:
                value = _coerce_js_number(value)
            except _NonFiniteNumber as exc:
                issues.append({"expected": "number", "code": "invalid_type", "received": exc.received, "path": [field], "message": "Invalid input: expected number, received number"})
                valid_type = False
            except (TypeError, ValueError):
                issues.append({"expected": "number", "code": "invalid_type", "received": "NaN", "path": [field], "message": "Invalid input: expected number, received NaN"})
                valid_type = False
            if valid_type:
                normalized[field] = int(value) if value.is_integer() else value
                if "minimum" in field_schema and value < field_schema["minimum"]:
                    issues.append({"origin": "number", "code": "too_small", "minimum": field_schema["minimum"], "inclusive": True, "path": [field], "message": f"Too small: expected number to be >={field_schema['minimum']}"})
                if "maximum" in field_schema and value > field_schema["maximum"]:
                    issues.append({"origin": "number", "code": "too_big", "maximum": field_schema["maximum"], "inclusive": True, "path": [field], "message": f"Too big: expected number to be <={field_schema['maximum']}"})
        elif expected_type == "boolean" and not isinstance(value, bool):
            received = _json_type(value)
            issues.append({"expected": "boolean", "code": "invalid_type", "path": [field], "message": f"Invalid input: expected boolean, received {received}"})
            valid_type = False
        elif expected_type == "string" and not isinstance(value, str):
            received = _json_type(value)
            issues.append({"expected": "string", "code": "invalid_type", "path": [field], "message": f"Invalid input: expected string, received {received}"})
            valid_type = False
        allowed = field_schema.get("enum")
        if valid_type and allowed is not None and value not in allowed:
            joined = "|".join(f'"{item}"' for item in allowed)
            issues.append({"code": "invalid_value", "values": allowed, "path": [field], "message": f"Invalid option: expected one of {joined}"})
    return (normalized, _validation_error(spec.name, issues)) if issues else (normalized, None)


async def call_tool(name: str, args: dict[str, Any] | None = None) -> CallToolResult:
    try:
        spec = get_tool_spec(name)
    except InvalidArgumentError:
        return _result([TextContent(type="text", text=f"MCP error -32602: Tool {name} not found")], True)
    arguments, validation_error = _validate_args(spec, args or {})
    if validation_error is not None:
        return validation_error
    try:
        handler = TOOL_HANDLERS.get(name)
        if handler is None:
            raise NotImplementedToolError(name)
        return _result(list(await handler(arguments)))
    except DriverError as exc:
        return _result([unexpected(exc.message)], True)
    except ToolError as exc:
        return _result([actionable(exc.message)])
    except Exception as exc:
        return _result([unexpected(str(exc))], True)
    finally:
        await cleanup_temporary_drivers()


def _result(content: list[TextContent | ImageContent], is_error: bool | None = None) -> ContractCallToolResult:
    return ContractCallToolResult.model_construct(content=content, isError=is_error)
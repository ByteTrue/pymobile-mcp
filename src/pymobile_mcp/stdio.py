"""MCP SDK stdio transport with upstream-compatible raw argument validation."""

from __future__ import annotations

import json
import math
import sys
from contextlib import asynccontextmanager
from io import TextIOWrapper
from typing import Any

import anyio
from mcp import types
from mcp.shared.message import SessionMessage

def _parse_int(value: str) -> int | float:
    try:
        return int(value)
    except ValueError:
        limit = sys.get_int_max_str_digits()
        if limit and len(value.removeprefix("-")) > limit:
            return -math.inf if value.startswith("-") else math.inf
        raise


class _ContractJSONRPCRequest(types.JSONRPCRequest):
    # The SDK re-dumps requests in JSON mode before dispatch; preserve infinities.
    model_config = {**types.JSONRPCRequest.model_config, "ser_json_inf_nan": "constants"}

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


def _argument_error(frame: dict[str, Any]) -> dict[str, Any] | None:
    if frame.get("method") != "tools/call" or "id" not in frame:
        return None
    params = frame.get("params")
    if not isinstance(params, dict) or "arguments" not in params or isinstance(params["arguments"], dict):
        return None
    arguments = params["arguments"]
    received = _json_type(arguments)
    message = json.dumps(
        [{"expected": "record", "code": "invalid_type", "path": ["params", "arguments"], "message": f"Invalid input: expected record, received {received}"}],
        indent=2,
    )
    return {"jsonrpc": "2.0", "id": frame["id"], "error": {"code": -32603, "message": message}}


@asynccontextmanager
async def contract_stdio_server():
    stdin = anyio.wrap_file(TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace"))
    stdout = anyio.wrap_file(TextIOWrapper(sys.stdout.buffer, encoding="utf-8"))
    read_writer, read_stream = anyio.create_memory_object_stream[SessionMessage | Exception](0)
    write_stream, write_reader = anyio.create_memory_object_stream[SessionMessage](0)
    write_lock = anyio.Lock()

    async def write_raw(value: dict[str, Any]) -> None:
        async with write_lock:
            await stdout.write(json.dumps(value, separators=(",", ":")) + "\n")
            await stdout.flush()

    async def stdin_reader() -> None:
        async with read_writer:
            async for line in stdin:
                try:
                    raw = json.loads(line, parse_int=_parse_int)
                    argument_error = _argument_error(raw) if isinstance(raw, dict) else None
                    if argument_error is not None:
                        await write_raw(argument_error)
                        continue
                    message = types.JSONRPCMessage.model_validate(raw)
                    if isinstance(message.root, types.JSONRPCRequest):
                        message = types.JSONRPCMessage.model_construct(
                            root=_ContractJSONRPCRequest.model_validate(raw)
                        )
                    await read_writer.send(SessionMessage(message))
                except Exception as exc:
                    await read_writer.send(exc)

    async def stdout_writer() -> None:
        async with write_reader:
            async for session_message in write_reader:
                async with write_lock:
                    await stdout.write(session_message.message.model_dump_json(by_alias=True, exclude_none=True) + "\n")
                    await stdout.flush()

    async with anyio.create_task_group() as task_group:
        task_group.start_soon(stdin_reader)
        task_group.start_soon(stdout_writer)
        yield read_stream, write_stream

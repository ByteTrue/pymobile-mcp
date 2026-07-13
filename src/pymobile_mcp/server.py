"""MCP stdio server wrapper."""

from __future__ import annotations


from typing import Any

from mcp.server import Server
from .stdio import contract_stdio_server
from mcp.server.models import InitializationOptions
from mcp.types import ServerCapabilities, ToolsCapability

from .tools import call_tool, list_tool_specs


class PyMobileMCPServer:
    def __init__(self) -> None:
        self.mcp = Server("mobile-mcp", version="0.0.1")
        self._register_tools()

    def _register_tools(self) -> None:
        @self.mcp.list_tools()
        async def handle_list_tools() -> list[Any]:
            return [spec.to_mcp_tool() for spec in list_tool_specs()]

        @self.mcp.call_tool(validate_input=False)
        async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> Any:
            return await call_tool(name, arguments or {})

    async def run(self) -> None:
        async with contract_stdio_server() as (read_stream, write_stream):
            await self.mcp.run(read_stream, write_stream, self._initialization_options())

    @staticmethod
    def _initialization_options() -> InitializationOptions:
        return InitializationOptions(
            server_name="mobile-mcp",
            server_version="0.0.1",
            capabilities=ServerCapabilities(tools=ToolsCapability(listChanged=True)),
        )

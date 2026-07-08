"""Command line entrypoint."""

from __future__ import annotations

import argparse
import asyncio

from .server import PyMobileMCPServer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pymobile-mcp")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("run", help="Run the MCP stdio server")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "run":
        asyncio.run(PyMobileMCPServer().run())
        return
    build_parser().print_help()


if __name__ == "__main__":
    main()

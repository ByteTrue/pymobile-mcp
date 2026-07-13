#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_common import StdioProbe, build_upstream, verify_upstream, write_frames, write_json


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Capture pinned mobile-mcp initialize and tools/list raw wire results")
    result.add_argument("--source", required=True)
    result.add_argument("--mode", choices=("default", "fleet"), required=True)
    result.add_argument("--clean-install", action="store_true")
    result.add_argument("--expected-revision", required=True)
    result.add_argument("--expected-lock-sha256", required=True)
    result.add_argument("--expected-node", required=True)
    result.add_argument("--expected-npm", required=True)
    result.add_argument("--timeout", type=float, default=30)
    result.add_argument("--raw-frames", required=True)
    result.add_argument("--output", required=True)
    result.add_argument("--report", required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        provenance = verify_upstream(
            args.source,
            args.expected_revision,
            args.expected_lock_sha256,
            args.expected_node,
            args.expected_npm,
        )
        build_upstream(args.source, args.clean_install)
        env = os.environ.copy()
        env["MOBILEMCP_DISABLE_TELEMETRY"] = "1"
        if args.mode == "fleet":
            env["MOBILEFLEET_ENABLE"] = "1"
        else:
            env.pop("MOBILEFLEET_ENABLE", None)
        probe = StdioProbe(["node", "lib/index.js", "--stdio"], args.source, env, args.timeout)
        try:
            initialize = probe.initialize()
            tools = probe.request(2, "tools/list", {})
        finally:
            probe.close()
        all_frames = [{"protocol_case": "2025-11-25", **frame} for frame in probe.frames]
        protocol_results = {"2025-11-25": initialize}
        for requested in ("2024-11-05", "1900-01-01"):
            protocol_probe = StdioProbe(["node", "lib/index.js", "--stdio"], args.source, env, args.timeout)
            try:
                result = protocol_probe.request(1, "initialize", {"protocolVersion": requested, "capabilities": {}, "clientInfo": {"name": "pymobile-mcp-contract-probe", "version": "1.0.0"}})
            finally:
                protocol_probe.close()
            protocol_results[requested] = result
            all_frames.extend({"protocol_case": requested, **frame} for frame in protocol_probe.frames)
        write_frames(args.raw_frames, all_frames)
        golden = {
            "provenance": {
                **provenance,
                "command": " ".join(sys.argv),
                "env": {"MOBILEMCP_DISABLE_TELEMETRY": "1", "MOBILEFLEET_ENABLE": "1" if args.mode == "fleet" else None},
                "raw_frames": args.raw_frames,
            },
            "mode": args.mode,
            "initialize": initialize,
            "list_tools": tools,
            "initialize_protocols": protocol_results,
        }
        write_json(args.output, golden)
        write_json(args.report, {"status": "passed", "mode": args.mode, "tool_count": len(tools["tools"]), "protocol_cases": protocol_results, "output": args.output, "provenance": provenance})
        print(f"captured {args.mode}: {len(tools['tools'])} tools")
        return 0
    except (FileNotFoundError, TimeoutError) as exc:
        write_json(args.report, {"status": "blocked", "reason": str(exc)})
        print(f"environment blocked: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        write_json(args.report, {"status": "failed", "reason": str(exc)})
        print(f"capture failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

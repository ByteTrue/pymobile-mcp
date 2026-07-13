#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from importlib.metadata import version as distribution_version
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_common import ExceptionBlockedError, StdioProbe, compute_bundle, ledger_sha, load_yaml, write_frames, write_json

sys.path.insert(0, str(Path("tests").resolve()))
from mobile_mcp_scenario_runner import run_stdio_scenarios


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Assert pymobile-mcp raw stdio and scenario parity against pinned upstream goldens")
    result.add_argument("--mode", choices=("default", "fleet"), required=True)
    result.add_argument("--scenarios", required=True)
    result.add_argument("--exceptions", required=True)
    result.add_argument("--bundle-manifest", required=True)
    result.add_argument("--golden", required=True)
    result.add_argument("--calls", required=True)
    result.add_argument("--timeout", type=float, default=30)
    result.add_argument("--raw-frames", required=True)
    result.add_argument("--report", required=True)
    return result


def _exception_report(ledger: dict, dispositions: dict[str, dict]) -> list[dict]:
    return [
        {
            "id": item["id"],
            "approval": item.get("approval"),
            "allowed_case_ids": item.get("allowed_case_ids", []),
            "scope": item.get("scope"),
            "tools": item.get("tools", []),
            "env": item.get("env", {}),
            "platform": item.get("platform"),
            "device_type": item.get("device_type"),
            "case_dispositions": {
                case_id: dispositions.get(case_id, {}).get("disposition", "not_applicable_in_mode")
                for case_id in item.get("allowed_case_ids", [])
            },
        }
        for item in ledger.get("exceptions", [])
    ]
def main() -> int:
    args = parser().parse_args()
    probe = None
    try:
        scenarios = load_yaml(args.scenarios)
        ledger = load_yaml(args.exceptions)
        bundle = compute_bundle(scenarios)
        stored_bundle = json.loads(Path(args.bundle_manifest).read_text())
        if bundle != stored_bundle:
            raise ValueError("deterministic bundle manifest is stale")
        upstream = json.loads(Path(args.golden).read_text())
        call_goldens = json.loads(Path(args.calls).read_text())
        if call_goldens.get("provenance", {}).get("bundle_sha256") != bundle["aggregate_sha256"]:
            raise ValueError("call golden provenance bundle is stale")
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"
        if args.mode == "fleet":
            env["MOBILEFLEET_ENABLE"] = "1"
        else:
            env.pop("MOBILEFLEET_ENABLE", None)
        probe = StdioProbe([sys.executable, "-m", "pymobile_mcp.cli", "run"], Path.cwd(), env, args.timeout)
        initialize = probe.initialize()
        tools = probe.request(2, "tools/list", {})
        mismatches = []
        python_mcp_version = distribution_version("mcp")
        expected_mcp_version = str(scenarios.get("probe", {}).get("python_mcp_version"))
        if python_mcp_version != expected_mcp_version:
            mismatches.append(f"Python MCP version differs: expected {expected_mcp_version}, got {python_mcp_version}")
        if initialize != upstream["initialize"]:
            mismatches.append("InitializeResult differs from upstream golden")
        if tools != upstream["list_tools"]:
            mismatches.append("ListToolsResult differs from upstream golden")
        protocol_frames = []
        for requested in ("2024-11-05", "1900-01-01"):
            protocol_probe = StdioProbe([sys.executable, "-m", "pymobile_mcp.cli", "run"], Path.cwd(), env, args.timeout)
            try:
                actual_protocol = protocol_probe.request(1, "initialize", {"protocolVersion": requested, "capabilities": {}, "clientInfo": {"name": "pymobile-mcp-contract-probe", "version": "1.0.0"}})
            finally:
                protocol_probe.close()
            protocol_frames.extend({"protocol_case": requested, **frame} for frame in protocol_probe.frames)
            if actual_protocol != upstream["initialize_protocols"][requested]:
                mismatches.append(f"initialize protocol negotiation differs for {requested}")
        scenario_result = run_stdio_scenarios(args.mode, args.scenarios, scenarios, call_goldens, ledger, args.timeout)
        mismatches.extend(f"scenario mismatch: {case_id}" for case_id in scenario_result["failed"])
        write_frames(args.raw_frames, [*probe.frames, *protocol_frames, *scenario_result["frames"]])
        approved = [item["id"] for item in ledger.get("exceptions", []) if item.get("approval") == "approved"]
        report = {
            "status": "failed" if mismatches else "passed",
            "mode": args.mode,
            "mismatches": mismatches,
            "tool_count": len(tools.get("tools", [])),
            "bundle": bundle,
            "exception_ledger_sha256": ledger_sha(args.exceptions),
            "approved_exceptions": approved,
            "exceptions": _exception_report(ledger, scenario_result["dispositions"]),
            "python_mcp_version": python_mcp_version,
            "expected_python_mcp_version": expected_mcp_version,
            "scenario_dispositions": scenario_result["dispositions"],
            "raw_stdio_case_count": len(scenario_result["dispositions"]),
            "core_raw_stdio_case_count": scenario_result["core_case_count"],
            "review_raw_stdio_case_count": scenario_result["review_case_count"],
            "contract_case_count_including_wire": scenario_result["core_case_count"] + 4,
            "raw_frame_count": len(scenario_result["frames"]),
        }
        write_json(args.report, report)
        if mismatches:
            print("\n".join(mismatches), file=sys.stderr)
            return 1
        print(f"{args.mode} parity passed: {len(tools['tools'])} tools, {len(scenario_result['dispositions'])} scenarios")
        return 0
    except ExceptionBlockedError as exc:
        write_json(args.report, {"status": "blocked", "reason": str(exc)})
        print(f"environment blocked: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        write_json(args.report, {"status": "blocked", "reason": str(exc)})
        print(f"environment blocked: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        write_json(args.report, {"status": "failed", "reason": str(exc)})
        print(f"contract assertion failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if probe is not None:
            probe.close()


if __name__ == "__main__":
    raise SystemExit(main())

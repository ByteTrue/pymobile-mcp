#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_common import (
    StdioProbe,
    build_upstream,
    compute_bundle,
    load_yaml,
    scenario_cases,
    raw_tool_call,
    verify_upstream,
    write_frames,
    write_json,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Capture source-linked mobile-mcp CallToolResult goldens in a deterministic fake environment")
    result.add_argument("--source", required=True)
    result.add_argument("--expected-revision", required=True)
    result.add_argument("--expected-lock-sha256", required=True)
    result.add_argument("--expected-node", required=True)
    result.add_argument("--expected-npm", required=True)
    result.add_argument("--clean-install", action="store_true")
    result.add_argument("--scenarios", required=True)
    result.add_argument("--bundle-manifest", required=True)
    result.add_argument("--fixture-root", required=True)
    result.add_argument("--node-preload", required=True)
    result.add_argument("--scaling-modes", required=True)
    result.add_argument("--timeout", type=float, default=30)
    result.add_argument("--raw-frames", required=True)
    result.add_argument("--output", required=True)
    result.add_argument("--report", required=True)
    return result


def _put(target: dict, dotted_key: str, value: object) -> None:
    current = target
    parts = dotted_key.split(".")
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value


def _scaling_mode(case: dict) -> str:
    raw = (case.get("fake_setup") or {}).get("preload_mode") or case.get("env_mode") or "no_scaling"
    return {"sips_fallback": "sips_fail_magick", "sips_fail_magick_fail": "scaling_failure"}.get(raw, raw)


def main() -> int:
    args = parser().parse_args()
    probes: list[StdioProbe] = []
    try:
        provenance = verify_upstream(args.source, args.expected_revision, args.expected_lock_sha256, args.expected_node, args.expected_npm)
        build_upstream(args.source, args.clean_install)
        manifest = load_yaml(args.scenarios)
        allowed_scaling = set(args.scaling_modes.split(","))
        golden: dict = {"provenance": {**provenance, "command": " ".join(sys.argv)}, "calls": {}, "errors": {}, "validation": {}}
        all_frames: list[dict] = []
        captured: list[str] = []
        for case in [*scenario_cases(manifest), *manifest.get("review_cases", [])]:
            key = case.get("expected_golden_key")
            if not key:
                continue
            mode = case.get("env_mode") or "default"
            requested_mode = {"sips_fail_magick": "sips_fallback", "sips_fail_magick_fail": "scaling_failure"}.get(_scaling_mode(case), _scaling_mode(case))
            if requested_mode in {"no_scaling", "sips", "imagemagick", "sips_fallback", "scaling_failure"} and requested_mode not in allowed_scaling:
                continue
            env = os.environ.copy()
            env.update({
                "MOBILEMCP_DISABLE_TELEMETRY": "1",
                "MOBILECLI_PATH": str(Path(args.fixture_root).resolve() / "fake-bin" / "mobilecli"),
                "NODE_OPTIONS": f"--require={Path(args.node_preload).resolve()}",
                "PYMOBILE_FIXTURE_ROOT": str(Path(args.fixture_root).resolve()),
                "PYMOBILE_SCENARIO_ID": case["id"],
                "PYMOBILE_SCALING_MODE": _scaling_mode(case),
            })
            if case.get("env", {}).get("MOBILEFLEET_ENABLE") == "1" or case.get("env_mode") == "fleet":
                env["MOBILEFLEET_ENABLE"] = "1"
            else:
                env.pop("MOBILEFLEET_ENABLE", None)
            if mode == "fixed_clock":
                env["PYMOBILE_FIXED_CLOCK"] = "1"
            probe = StdioProbe(["node", str(Path(args.source).resolve() / "lib" / "index.js"), "--stdio"], Path.cwd(), env, args.timeout)
            probes.append(probe)
            probe.initialize()
            request_id = 2
            if case["id"] in {"S-STOP-REC-IOS"}:
                probe.request(request_id, "tools/call", {"name": "mobile_start_screen_recording", "arguments": {"device": "ios-1", "output": "/tmp/mobile-mcp-contract.mp4"}})
                request_id += 1
            probe.send_raw(raw_tool_call(case, request_id))
            response = probe.receive(request_id)
            result = response["result"] if "result" in response else {"jsonrpc_error": response["error"]}
            probe.close()
            all_frames.extend({"case_id": case["id"], **frame} for frame in probe.frames)
            _put(golden, key, result)
            captured.append(case["id"])
        write_frames(args.raw_frames, all_frames)
        bundle = compute_bundle(manifest)
        write_json(args.bundle_manifest, bundle)
        golden["provenance"]["bundle_sha256"] = bundle["aggregate_sha256"]
        golden["provenance"]["raw_frames"] = args.raw_frames
        write_json(args.output, golden)
        write_json(args.report, {"status": "passed", "captured_cases": captured, "count": len(captured), "bundle": bundle, "bundle_sha256": bundle["aggregate_sha256"], "provenance": provenance})
        print(f"captured {len(captured)} upstream call results")
        return 0
    except (FileNotFoundError, TimeoutError) as exc:
        write_json(args.report, {"status": "blocked", "reason": str(exc)})
        print(f"environment blocked: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        write_json(args.report, {"status": "failed", "reason": str(exc)})
        print(f"capture failed: {exc}", file=sys.stderr)
        return 1
    finally:
        for probe in probes:
            probe.close()


if __name__ == "__main__":
    raise SystemExit(main())

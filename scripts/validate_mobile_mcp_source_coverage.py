#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from typing import Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_common import ExceptionBlockedError, compute_bundle, load_yaml, scenario_cases, validate_exception_ledger, verify_upstream, write_json


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Validate pinned source links, scenario coverage, bundle integrity, and exception scope")
    result.add_argument("--source", required=True)
    result.add_argument("--expected-revision", required=True)
    result.add_argument("--scenarios", required=True)
    result.add_argument("--exceptions", required=True)
    result.add_argument("--bundle-manifest", required=True)
    result.add_argument("--timeout", type=float, default=30)
    result.add_argument("--report", required=True)
    return result


def _source_files(source: Path, source_ref: str) -> list[Path]:
    result: list[Path] = []
    for name in re.findall(r"(?:^|;)([\w.-]+\.ts|package\.json):", source_ref):
        candidate = source / (name if name == "package.json" else f"src/{name}")
        result.append(candidate)
    return result


def _referenced_source_lines(scenarios: dict, filename: str) -> set[int]:
    lines: set[int] = set()
    for case in scenario_cases(scenarios):
        for segment in str(case.get("source_ref", "")).split(";"):
            if not segment.startswith(f"{filename}:"):
                continue
            numbers = segment.split(":", 1)[1].split(":", 1)[0]
            for part in numbers.split(","):
                match = re.fullmatch(r"(\d+)(?:-(\d+))?", part)
                if match:
                    start = int(match.group(1))
                    lines.update(range(start, int(match.group(2) or start) + 1))
    return lines


def _nested_arrow_return(lines: list[str], number: int) -> bool:
    for index in range(number - 2, -1, -1):
        previous = lines[index]
        if "=> {" not in previous:
            continue
        indent = len(previous) - len(previous.lstrip("\t"))
        closed = any(
            len(line) - len(line.lstrip("\t")) == indent
            and line.strip().startswith(("});", "};", "}"))
            for line in lines[index + 1 : number - 1]
        )
        if not closed:
            return "async " not in previous
    return False


def source_inventory(source: Path) -> dict[str, list[str]]:
    server_lines = (source / "src/server.ts").read_text().splitlines()
    returns = [
        f"server.ts:{number}"
        for number, line in enumerate(server_lines, 1)
        if 216 <= number <= 841
        and re.search(r"\breturn\b", line)
        and not line.strip().startswith("//")
        and not _nested_arrow_return(server_lines, number)
    ]
    tools = re.findall(r'(?:tool|server\.registerTool)\(\s*\n?\s*"(mobile_[^"]+)"', "\n".join(server_lines))
    schemas = [f"server.ts:{number}" for number, line in enumerate(server_lines, 1) if 216 <= number <= 841 and re.search(r"\bz\.(?:string|boolean|enum|coerce\.number)\b", line)]
    guards = [f"server.ts:{number}" for number, line in enumerate(server_lines, 1) if 154 <= number <= 841 and ("throw new ActionableError" in line or "activeRecordings.has" in line or "!recording" in line)]
    image_lines = (source / "src/image-utils.ts").read_text().splitlines()
    backends = [f"image-utils.ts:{number}" for number, line in enumerate(image_lines, 1) if any(marker in line for marker in ("isSipsInstalled()", "toBufferWithSips()", "toBufferWithImageMagick()", "Image scaling unavailable"))]
    return {"tools": sorted(set(tools)), "returns": returns, "schemas": schemas, "guards": guards, "backends": backends}


def validate_bidirectional_inventory(source: Path, scenarios: dict) -> tuple[dict[str, list[str]], list[str]]:
    inventory = source_inventory(source)
    errors: list[str] = []
    manifest_tools = {case.get("tool") for case in scenario_cases(scenarios) if case.get("tool")}
    missing_tools = set(inventory["tools"]) - manifest_tools
    extra_tools = manifest_tools - set(inventory["tools"]) - {"mobile_not_real"}
    if missing_tools or extra_tools:
        errors.append(f"tool inventory mismatch: missing={sorted(missing_tools)} extra={sorted(extra_tools)}")
    referenced = {name: _referenced_source_lines(scenarios, name) for name in ("server.ts", "image-utils.ts")}
    for group in ("schemas", "guards", "backends"):
        for identity in inventory[group]:
            filename, raw_line = identity.split(":")
            if int(raw_line) not in referenced[filename]:
                errors.append(f"unmapped source identity: {identity}")
    actual_returns = {int(item.split(":")[1]) for item in inventory["returns"]}
    manifest_returns = {
        int(match.group(1))
        for case in scenario_cases(scenarios)
        if (match := re.search(r"return-(\d+)", str(case.get("source_ref", ""))))
    }
    if actual_returns != manifest_returns:
        errors.append(f"return inventory mismatch: source={sorted(actual_returns)} manifest={sorted(manifest_returns)}")
    return inventory, errors


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _called_name(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Call) and _dotted_name(node.func) == name


def _thread_target(call: ast.Call) -> ast.AST | None:
    if _dotted_name(call.func) == "asyncio.to_thread" and call.args:
        return call.args[0]
    return None


def _command_words(call: ast.Call) -> list[str]:
    if not call.args:
        return []
    first = call.args[0]
    nodes = first.elts if isinstance(first, (ast.List, ast.Tuple)) else call.args
    return [node.value for node in nodes if isinstance(node, ast.Constant) and isinstance(node.value, str)]


def _android_backend_call(call: ast.Call) -> bool:
    name = _dotted_name(call.func)
    if name in {"self._adb", "subprocess.Popen"} or name.endswith(".sync.pull"):
        return True
    target = _thread_target(call)
    if isinstance(target, ast.Attribute) and target.attr == "shell":
        receiver = target.value
        if _called_name(receiver, "self._adb") or _called_name(receiver, "adbutils.adb.device"):
            return True
    if not isinstance(call.func, ast.Attribute):
        return False
    receiver = call.func.value
    if _called_name(receiver, "self._adb"):
        return True
    if call.func.attr != "shell":
        return False
    return _dotted_name(receiver) == "adb" or _called_name(receiver, "adbutils.adb.device")


def _ios_backend_call(call: ast.Call) -> bool:
    name = _dotted_name(call.func)
    return name in {"InstallationProxyService", "CrashReportsManager"} or name.startswith("self._client.")


def _ios_simulator_backend_call(call: ast.Call) -> bool:
    name = _dotted_name(call.func)
    if name in {"self._request", "_simctl", "_simctl_json", "start_simctl_recording", "urllib.request.urlopen"}:
        return True
    target = _thread_target(call)
    if target is not None and _dotted_name(target) in {"self._request", "_simctl", "_simctl_json"}:
        return True
    if name not in {"subprocess.run", "subprocess.Popen", "_create_subprocess_exec", "asyncio.create_subprocess_exec"}:
        return False
    return _command_words(call)[:2] == ["xcrun", "simctl"]


def _python_backend_inventory(path: Path, identity: str, matcher: Any) -> list[dict[str, Any]]:
    source = path.read_text()
    tree = ast.parse(source, filename=str(path))
    return [
        {
            "identity": identity,
            "line": node.lineno,
            "source": " ".join((ast.get_source_segment(source, node) or ast.unparse(node)).split()),
        }
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and matcher(node)
    ]


def backend_source_inventory(upstream: Path, repo: Path) -> list[dict[str, Any]]:
    upstream_specs = [
        (upstream / "src/android.ts", "upstream:android.ts", re.compile(r"(?:this\.adb|execFileSync\(getAdbPath)")),
        (upstream / "src/ios.ts", "upstream:ios.ts", re.compile(r"(?:this\.ios|await wda\.|execFileSync\(getGoIosPath)")),
        (upstream / "src/webdriver-agent.ts", "upstream:webdriver-agent.ts", re.compile(r"(?:fetch\(|/actions|/wda/)")),
        (upstream / "src/mobile-device.ts", "upstream:mobile-device.ts", re.compile(r"runCommand\(")),
    ]
    inventory: list[dict[str, Any]] = []
    for path, identity, pattern in upstream_specs:
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if pattern.search(line) and not line.lstrip().startswith("#"):
                inventory.append({"identity": identity, "line": number, "source": line.strip()})
    for relative, identity, matcher in (
        ("android.py", "python:drivers/android.py", _android_backend_call),
        ("ios.py", "python:drivers/ios.py", _ios_backend_call),
        ("ios_simulator.py", "python:drivers/ios_simulator.py", _ios_simulator_backend_call),
    ):
        inventory.extend(_python_backend_inventory(repo / "src/pymobile_mcp/drivers" / relative, identity, matcher))
    return inventory


def backend_inventory_summary(inventory: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in inventory:
        grouped.setdefault(item["identity"], []).append({"line": item["line"], "source": item["source"]})
    return {
        identity: {
            "count": len(entries),
            "sha256": hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        }
        for identity, entries in sorted(grouped.items())
    }


GROUP_RULES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "initialize": ("server.ts", 'name: "mobile-mcp"', ("INIT-DEFAULT", "INIT-FLEET")),
    "default_tool_registration": ("server.ts", '"mobile_list_available_devices"', ("LIST-DEFAULT",)),
    "fleet_tool_registration": ("server.ts", 'MOBILEFLEET_ENABLE === "1"', ("LIST-FLEET", "S-REMOTE-LIST")),
    "actionable_wrapper": ("server.ts", "error instanceof ActionableError", ("E-DEVICE-NOT-FOUND", "E-ACTIONABLE-PASSTHROUGH")),
    "unexpected_wrapper": ("server.ts", "isError: true", ("E-UNEXPECTED-DRIVER",)),
    "screenshot_png": ("server.ts", 'mimeType = "image/png"', ("S-TAKE-PNG",)),
    "screenshot_sips": ("image-utils.ts", "toBufferWithSips", ("S-TAKE-JPEG-SIPS",)),
    "screenshot_imagemagick": ("image-utils.ts", "toBufferWithImageMagick", ("S-TAKE-JPEG-MAGICK",)),
    "screenshot_sips_fallback": ("image-utils.ts", "falling back to ImageMagick", ("S-TAKE-JPEG-SIPS-FALLBACK",)),
    "screenshot_errors": ("server.ts", "Screenshot is invalid", ("E-SCREENSHOT-INVALID", "E-SCREENSHOT-ZERO", "E-SCREENSHOT-SCALING-FAIL")),
    "utils_package_android_launch": ("android.ts", "validatePackageName(packageName)", ("E-INVALID-PACKAGE-ANDROID-LAUNCH",)),
    "utils_package_ios_launch": ("ios.ts", "validatePackageName(packageName)", ("E-INVALID-PACKAGE-IOS-LAUNCH",)),
    "utils_package_android_terminate": ("android.ts", "validatePackageName(packageName)", ("E-INVALID-PACKAGE-ANDROID-TERMINATE",)),
    "utils_package_ios_terminate": ("ios.ts", "validatePackageName(packageName)", ("E-INVALID-PACKAGE-IOS-TERMINATE",)),
    "utils_locale_android_launch": ("android.ts", "validateLocale(locale)", ("E-INVALID-LOCALE-ANDROID-LAUNCH",)),
    "utils_locale_ios_launch": ("ios.ts", "validateLocale(locale)", ("E-INVALID-LOCALE-IOS-LAUNCH",)),
    "utils_extension_save_screenshot": ("utils.ts", "validateFileExtension", ("E-SAVE-BAD-EXTENSION",)),
    "utils_extension_start_recording": ("utils.ts", "validateFileExtension", ("E-START-BAD-EXTENSION",)),
    "utils_output_path_save_screenshot": ("utils.ts", "validateOutputPath", ("E-SAVE-UNSAFE-PATH",)),
    "utils_output_path_start_recording": ("utils.ts", "validateOutputPath", ("E-START-UNSAFE-PATH",)),
    "schema_required": ("server.ts", "device: z.string()", ("E-MISSING-DEVICE",)),
    "schema_object_policy": ("server.ts", "inputSchema: paramsSchema", ("V-EXTRA-FIELD",)),
    "schema_number_coercion": ("server.ts", "z.coerce.number()", ("S-CLICK-COERCE", "E-NONCOERCIBLE-X")),
    "schema_boolean": ("server.ts", "z.boolean()", ("E-WRONG-BOOLEAN",)),
    "schema_enum": ("server.ts", 'z.enum(["up", "down", "left", "right"])', ("E-BAD-DIRECTION",)),
    "schema_min_max": ("server.ts", ".min(1).max(10000)", ("E-LONG-PRESS-ZERO", "E-LONG-PRESS-TOO-HIGH")),
    "guard_mobilecli_available": ("server.ts", "ensureMobilecliAvailable", ("E-MOBILECLI-UNAVAILABLE",)),
    "guard_device_found": ("server.ts", "not found. Use the mobile_list_available_devices", ("E-DEVICE-NOT-FOUND",)),
    "guard_unsafe_url": ("server.ts", "MOBILEMCP_ALLOW_UNSAFE_URLS", ("E-UNSAFE-URL",)),
    "guard_recording_already_active": ("server.ts", "activeRecordings.has(device)", ("E-ALREADY-RECORDING",)),
    "guard_recording_not_active": ("server.ts", "No active recording found", ("E-NO-RECORDING",)),
    "android_physical_public_type_emulator": ("server.ts", 'type: "emulator"', ("S-LIST-DEVICES-ANDROID-PHYSICAL",)),
    "ios_simulator_discovery": ("server.ts", 'type: "simulator"', ("S-LIST-DEVICES-IOS-SIMULATOR",)),
    "ios_simulator_runtime_wda": ("mobile-device.ts", "getScreenSize", ("S-IOS-SIM-SCREEN-SIZE",)),
    "ios_simulator_recording_simctl": ("server.ts", 'args = ["screenrecord"', ("S-START-REC-IOS-SIMULATOR", "S-STOP-REC-IOS-SIMULATOR")),
}


def validate_branch_groups(source: Path, scenarios: dict, case_ids: set[str]) -> tuple[dict[str, list[str]], list[str]]:
    errors: list[str] = []
    coverage: dict[str, list[str]] = {}
    for group in scenarios.get("source_coverage", {}).get("required_groups", []):
        if group == "all_callback_returns":
            mapped = []
            server_lines = (source / "src/server.ts").read_text().splitlines()
            for case in scenario_cases(scenarios):
                match = re.search(r"return-(\d+)", str(case.get("source_ref", "")))
                if match:
                    line = int(match.group(1))
                    if line > len(server_lines) or "return" not in server_lines[line - 1]:
                        errors.append(f"{case['id']}: source return marker line {line} is not an actual return")
                    mapped.append(case["id"])
            if not mapped:
                errors.append("all_callback_returns: no cases mapped")
            coverage[group] = mapped
            continue
        rule = GROUP_RULES.get(group)
        if rule is None:
            errors.append(f"{group}: no validator rule")
            continue
        filename, marker, mapped_ids = rule
        if marker not in (source / "src" / filename).read_text():
            errors.append(f"{group}: branch marker not found: {filename}:{marker}")
        missing = [case_id for case_id in mapped_ids if case_id not in case_ids]
        if missing:
            errors.append(f"{group}: mapped cases missing: {missing}")
        coverage[group] = [case_id for case_id in mapped_ids if case_id in case_ids]
    return coverage, errors


def validate_exception_scope(scenarios: dict, ledger: dict) -> tuple[dict[str, set[str]], list[str]]:
    referenced: dict[str, set[str]] = {}
    for case in scenario_cases(scenarios):
        if case.get("allowed_exception"):
            referenced.setdefault(case["allowed_exception"], set()).add(case["id"])
    try:
        validate_exception_ledger(scenarios, ledger)
    except ExceptionBlockedError:
        raise
    except ValueError as exc:
        return referenced, [str(exc)]
    return referenced, []


def exception_ledger_summary(ledger: dict) -> list[dict]:
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
            "disposition": "approved_exception" if item.get("approval") == "approved" else "blocked",
        }
        for item in ledger.get("exceptions", [])
    ]


def main() -> int:
    args = parser().parse_args()
    try:
        provenance = verify_upstream(args.source, args.expected_revision)
        scenarios = load_yaml(args.scenarios)
        ledger = load_yaml(args.exceptions)
        cases = [*scenarios.get("wire_cases", []), *scenario_cases(scenarios)]
        ids = [case.get("id") for case in cases]
        errors: list[str] = []
        if len(cases) != 91:
            errors.append(f"expected 91 scenarios, found {len(cases)}")
        if len(set(ids)) != len(ids):
            errors.append("scenario ids are not unique")
        source = Path(args.source)
        branch_coverage, branch_errors = validate_branch_groups(source, scenarios, set(ids))
        errors.extend(branch_errors)
        inventory, inventory_errors = validate_bidirectional_inventory(source, scenarios)
        errors.extend(inventory_errors)
        backend_inventory = backend_source_inventory(source, Path.cwd())
        backend_summary = backend_inventory_summary(backend_inventory)
        expected_backend_summary = scenarios.get("source_coverage", {}).get("backend_inventory_manifest", {})
        if backend_summary != expected_backend_summary:
            errors.append(f"backend inventory mismatch: expected={expected_backend_summary} actual={backend_summary}")
        for case in cases:
            case_id = case.get("id", "<missing>")
            if not case.get("source_ref"):
                errors.append(f"{case_id}: missing source_ref")
            for path in _source_files(source, str(case.get("source_ref", ""))):
                if not path.is_file():
                    errors.append(f"{case_id}: missing source file {path}")
            if not case.get("required_disposition"):
                errors.append(f"{case_id}: missing required_disposition")
            if not (case.get("expected") is not None or case.get("expected_golden_key") or case.get("request")):
                errors.append(f"{case_id}: missing expected/golden/request")
        referenced, exception_errors = validate_exception_scope(scenarios, ledger)
        errors.extend(exception_errors)
        current_bundle = compute_bundle(scenarios)
        stored_bundle = json.loads(Path(args.bundle_manifest).read_text())
        if current_bundle != stored_bundle:
            errors.append("deterministic bundle manifest is stale")
        report = {
            "status": "failed" if errors else "passed",
            "scenario_count": len(cases),
            "source_linked_count": sum(bool(case.get("source_ref")) for case in cases),
            "disposition_coverage_percent": 100 if cases and all(case.get("required_disposition") for case in cases) else 0,
            "exception_scope": {key: sorted(value) for key, value in referenced.items()},
            "exceptions": exception_ledger_summary(ledger),
            "required_group_coverage": branch_coverage,
            "source_inventory": inventory,
            "backend_inventory": backend_inventory,
            "backend_inventory_summary": backend_summary,
            "bundle": current_bundle,
            "errors": errors,
            "provenance": provenance,
        }
        write_json(args.report, report)
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        print(f"source coverage passed: {len(cases)} scenarios")
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
        print(f"coverage validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

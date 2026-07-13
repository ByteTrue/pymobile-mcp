from __future__ import annotations

import hashlib
import json
import glob
import platform
import select
import subprocess
import time
from pathlib import Path
from typing import Any

import yaml

PROTOCOL_VERSION = "2025-11-25"
CLIENT_INFO = {"name": "pymobile-mcp-contract-probe", "version": "1.0.0"}


class ExceptionBlockedError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bundle_entries(required_paths: list[str]) -> list[dict[str, str]]:
    files: set[Path] = set()
    for pattern in required_paths:
        matches = [Path(item) for item in glob.glob(pattern, recursive=True)]
        if not matches:
            raise FileNotFoundError(f"bundle input has no matches: {pattern}")
        files.update(path for path in matches if path.is_file())
    return [
        {"path": path.as_posix(), "sha256": sha256_file(path)}
        for path in sorted(files, key=lambda item: item.as_posix())
    ]


def bundle_digest(entries: list[dict[str, str]]) -> str:
    raw = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def compute_bundle(scenarios: dict[str, Any]) -> dict[str, Any]:
    entries = bundle_entries(list(scenarios["oracle_bundle"]["required_paths"]))
    return {"algorithm": scenarios["oracle_bundle"]["algorithm"], "entries": entries, "aggregate_sha256": bundle_digest(entries)}


def write_json(path: str | Path, value: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, allow_nan=False, indent=2, sort_keys=True) + "\n")


def load_yaml(path: str | Path) -> dict[str, Any]:
    value = yaml.safe_load(Path(path).read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected YAML object: {path}")
    return value


def raw_tool_call(case: dict[str, Any], request_id: int) -> str:
    arguments = case["raw_arguments"] if "raw_arguments" in case else case.get("arguments", {})
    raw_integer = case.get("raw_decimal_integer")
    if raw_integer is None:
        frame = {"jsonrpc": "2.0", "id": request_id, "method": "tools/call", "params": {"name": case["tool"], "arguments": arguments}}
        return json.dumps(frame, separators=(",", ":"))
    if not isinstance(arguments, dict):
        raise ValueError("raw_decimal_integer requires object arguments")
    placeholder = "__PYMOBILE_RAW_DECIMAL_INTEGER__"
    arguments = {**arguments, raw_integer["field"]: placeholder}
    frame = {"jsonrpc": "2.0", "id": request_id, "method": "tools/call", "params": {"name": case["tool"], "arguments": arguments}}
    digits = int(raw_integer["digits"])
    token = ("-" if raw_integer.get("negative") else "") + "1" + "0" * (digits - 1)
    return json.dumps(frame, separators=(",", ":")).replace(json.dumps(placeholder), token, 1)


def command_output(command: list[str], cwd: Path | None = None) -> str:
    return subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def verify_upstream(
    source: str | Path,
    expected_revision: str,
    expected_lock_sha256: str | None = None,
    expected_node: str | None = None,
    expected_npm: str | None = None,
) -> dict[str, Any]:
    root = Path(source).resolve()
    revision = command_output(["git", "rev-parse", "HEAD"], root)
    if revision != expected_revision:
        raise ValueError(f"upstream revision mismatch: expected {expected_revision}, got {revision}")
    lock_sha = sha256_file(root / "package-lock.json")
    if expected_lock_sha256 and lock_sha != expected_lock_sha256:
        raise ValueError(f"package-lock sha256 mismatch: expected {expected_lock_sha256}, got {lock_sha}")
    node = command_output(["node", "--version"])
    npm = command_output(["npm", "--version"])
    if expected_node and node != expected_node:
        raise ValueError(f"Node mismatch: expected {expected_node}, got {node}")
    if expected_npm and npm != expected_npm:
        raise ValueError(f"npm mismatch: expected {expected_npm}, got {npm}")
    package = json.loads((root / "package.json").read_text())
    return {
        "source": str(root),
        "git_revision": revision,
        "package_lock_sha256": lock_sha,
        "node_version": node,
        "npm_version": npm,
        "sdk_version": package["dependencies"]["@modelcontextprotocol/sdk"],
        "package_version": package["version"],
        "os": platform.platform(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def build_upstream(source: str | Path, clean_install: bool) -> None:
    root = Path(source).resolve()
    if clean_install:
        subprocess.run(["npm", "ci", "--ignore-scripts"], cwd=root, check=True)
    subprocess.run(["npm", "run", "build"], cwd=root, check=True)


class StdioProbe:
    def __init__(self, command: list[str], cwd: str | Path, env: dict[str, str], timeout: float) -> None:
        self.timeout = timeout
        self.frames: list[dict[str, Any]] = []
        self.process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)

    def send(self, frame: dict[str, Any]) -> None:
        if self.process.stdin is None:
            raise RuntimeError("stdio probe stdin unavailable")
        raw = json.dumps(frame, separators=(",", ":"))
        self.frames.append({"direction": "client_to_server", "frame": frame, "raw": raw})
        self.process.stdin.write(raw + "\n")
        self.process.stdin.flush()

    def send_raw(self, raw: str) -> None:
        def parse_int(value: str) -> int | str:
            try:
                return int(value)
            except ValueError:
                return value

        frame = json.loads(raw, parse_int=parse_int)
        self.frames.append({"direction": "client_to_server", "frame": frame, "raw": raw})
        if self.process.stdin is None:
            raise RuntimeError("stdio probe stdin unavailable")
        self.process.stdin.write(raw + "\n")
        self.process.stdin.flush()

    def receive(self, request_id: int) -> dict[str, Any]:
        if self.process.stdout is None:
            raise RuntimeError("stdio probe stdout unavailable")
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            ready, _, _ = select.select([self.process.stdout], [], [], max(0.0, deadline - time.monotonic()))
            if not ready:
                break
            raw = self.process.stdout.readline()
            if not raw:
                break
            frame = json.loads(raw)
            self.frames.append({"direction": "server_to_client", "frame": frame, "raw": raw.rstrip("\n")})
            if frame.get("id") == request_id:
                return frame
        stderr = ""
        if self.process.poll() is not None and self.process.stderr is not None:
            stderr = self.process.stderr.read()
        raise TimeoutError(f"no response for request {request_id}; stderr={stderr[-2000:]}")

    def request(self, request_id: int, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        frame: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            frame["params"] = params
        self.send(frame)
        response = self.receive(request_id)
        if "error" in response:
            raise RuntimeError(f"{method} failed: {response['error']}")
        return response["result"]

    def initialize(self) -> dict[str, Any]:
        result = self.request(
            1,
            "initialize",
            {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": CLIENT_INFO},
        )
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return result


def write_frames(path: str | Path, frames: list[dict[str, Any]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(json.dumps(frame, sort_keys=True) + "\n" for frame in frames))


def scenario_cases(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        *manifest.get("call_cases", []),
        *manifest.get("validation_and_error_cases", []),
    ]


def exception_map(ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in ledger.get("exceptions", [])}


def validate_exception_ledger(manifest: dict[str, Any], ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = exception_map(ledger)
    referenced: dict[str, set[str]] = {}
    cases = {case["id"]: case for case in scenario_cases(manifest)}
    for case in cases.values():
        exception_id = case.get("allowed_exception")
        if exception_id:
            referenced.setdefault(exception_id, set()).add(case["id"])
    if set(referenced) != set(items):
        raise ValueError(f"exception IDs mismatch: ledger={sorted(items)} scenarios={sorted(referenced)}")
    blocked: list[str] = []
    for exception_id, item in items.items():
        allowed = set(item.get("allowed_case_ids", []))
        if allowed != referenced[exception_id]:
            raise ValueError(f"{exception_id}: allowed_case_ids mismatch")
        approval = item.get("approval")
        if approval in {"pending", "rejected"}:
            blocked.append(f"{exception_id}:{approval}")
        elif approval != "approved":
            raise ValueError(f"{exception_id}: invalid approval {approval!r}")
        tools = set(item.get("tools", []))
        for case_id in allowed:
            case = cases[case_id]
            if case.get("tool") not in tools:
                raise ValueError(f"{exception_id}:{case_id}: tool outside scope")
            for key, value in item.get("env", {}).items():
                if case.get("env", {}).get(key) != value:
                    raise ValueError(f"{exception_id}:{case_id}: env outside scope")
            for key in ("platform", "device_type"):
                if item.get(key) is not None and case.get(key) != item[key]:
                    raise ValueError(f"{exception_id}:{case_id}: {key} outside scope")
    if blocked:
        raise ExceptionBlockedError("exception approval blocked: " + ", ".join(blocked))
    return items


def ledger_sha(path: str | Path) -> str:
    return sha256_file(Path(path))

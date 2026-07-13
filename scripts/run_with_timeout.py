#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_common import write_json


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Run a command with a hard timeout and a machine-readable report")
    result.add_argument("--timeout", type=float, required=True)
    result.add_argument("--report", required=True)
    result.add_argument("command", nargs=argparse.REMAINDER)
    return result


def main() -> int:
    args = parser().parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser().error("a command is required after --")
    started = time.monotonic()
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout, check=False)
    except FileNotFoundError as exc:
        write_json(args.report, {"status": "blocked", "exit_code": 2, "reason": str(exc), "command": command})
        print(str(exc), file=sys.stderr)
        return 2
    except subprocess.TimeoutExpired as exc:
        write_json(
            args.report,
            {
                "status": "blocked",
                "exit_code": 2,
                "reason": f"timed out after {args.timeout}s",
                "command": command,
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
            },
        )
        print(f"timed out after {args.timeout}s", file=sys.stderr)
        return 2
    duration = time.monotonic() - started
    report = {
        "status": "passed" if completed.returncode == 0 else "failed",
        "exit_code": completed.returncode,
        "duration_seconds": round(duration, 3),
        "command": command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    write_json(args.report, report)
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    return 0 if completed.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

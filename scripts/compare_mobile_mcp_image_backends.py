#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageStat
from mcp.types import ImageContent
from pymobile_mcp.tools import contract

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_common import ExceptionBlockedError, compute_bundle, load_yaml, verify_upstream, write_json

SCENARIOS = Path(".codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-scenarios.yaml")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Compare pinned upstream and Python screenshot scaling backends")
    result.add_argument("--source", required=True)
    result.add_argument("--expected-revision", required=True)
    result.add_argument("--expected-lock-sha256", required=True)
    result.add_argument("--expected-node", required=True)
    result.add_argument("--expected-npm", required=True)
    result.add_argument("--bundle-manifest", required=True)
    result.add_argument("--fixture", required=True)
    result.add_argument("--screen-scale", type=float, required=True)
    result.add_argument("--backends", required=True)
    result.add_argument("--psnr-min", type=float, required=True)
    result.add_argument("--timeout", type=float, default=30)
    result.add_argument("--artifact-dir", required=True)
    result.add_argument("--report", required=True)
    return result


def _upstream(source: Path, fixture: Path, width: int, backend: str, output: Path, timeout: float) -> None:
    code = (
        "const fs=require('node:fs');"
        f"const {{Image}}=require({json.dumps(str(source / 'lib/image-utils.js'))});"
        f"const out=Image.fromBuffer(fs.readFileSync({json.dumps(str(fixture))})).resize({width}).jpeg({{quality:75}}).toBuffer();"
        f"fs.writeFileSync({json.dumps(str(output))},out);"
    )
    env = os.environ.copy()
    env["PYMOBILE_SCALING_MODE"] = {"sips_fallback": "sips_fail_magick"}.get(backend, backend)
    env["NODE_OPTIONS"] = f"--require={Path('tests/fixtures/mobile_mcp/fakes/child-process-hook.cjs').resolve()}"
    subprocess.run(["node", "-e", code], env=env, check=True, timeout=timeout)


def _python(fixture: Path, screen_scale: float, backend: str, output: Path, timeout: float) -> None:
    del timeout
    original_available = contract._sips_available
    original_run_sips = contract._run_sips
    original_run_magick = contract._run_magick
    try:
        if backend == "sips":
            contract._run_magick = lambda data, width: (_ for _ in ()).throw(RuntimeError("sips mode must not fall back to ImageMagick"))
        elif backend == "imagemagick":
            contract._sips_available = lambda: False
        elif backend == "sips_fallback":
            contract._run_sips = lambda data, width: (_ for _ in ()).throw(RuntimeError("forced sips failure"))
        else:
            raise ValueError(f"unknown backend mode: {backend}")
        result = contract.screenshot(fixture.read_bytes(), screen_scale)
    finally:
        contract._sips_available = original_available
        contract._run_sips = original_run_sips
        contract._run_magick = original_run_magick
    if not isinstance(result, ImageContent) or result.mimeType != "image/jpeg":
        raise RuntimeError(f"production formatter did not return JPEG for {backend}")
    output.write_bytes(base64.b64decode(result.data))


def _backend_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {"sips": None, "imagemagick": None}
    if contract._sips_available():
        try:
            versions["sips"] = subprocess.run(["/usr/bin/sips", "--version"], capture_output=True, text=True, check=True).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    magick = shutil.which("magick")
    if magick:
        try:
            versions["imagemagick"] = subprocess.run([magick, "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
        except (OSError, subprocess.SubprocessError):
            pass
    return versions


def _require_backends(backends: list[str], versions: dict[str, str | None]) -> None:
    requirements = {
        "sips": ("sips",),
        "imagemagick": ("imagemagick",),
        "sips_fallback": ("sips", "imagemagick"),
    }
    for backend in backends:
        if backend not in requirements:
            raise ValueError(f"unknown backend mode: {backend}")
        missing = [name for name in requirements[backend] if not versions.get(name)]
        if missing:
            raise ExceptionBlockedError(f"{backend} backend unavailable: missing {', '.join(missing)}")


def _psnr(left: Path, right: Path) -> float:
    with Image.open(left) as a, Image.open(right) as b:
        rgb_a = a.convert("RGB")
        rgb_b = b.convert("RGB")
        if rgb_a.size != rgb_b.size:
            return 0.0
        stat = ImageStat.Stat(ImageChops.difference(rgb_a, rgb_b))
        mse = sum(value * value for value in stat.rms) / 3
        return float("inf") if mse == 0 else 20 * math.log10(255 / math.sqrt(mse))


def _json_psnr(value: float) -> float | str:
    return "Infinity" if math.isinf(value) else value


def main() -> int:
    args = parser().parse_args()
    try:
        provenance = verify_upstream(args.source, args.expected_revision, args.expected_lock_sha256, args.expected_node, args.expected_npm)
        stored = json.loads(Path(args.bundle_manifest).read_text())
        current = compute_bundle(load_yaml(SCENARIOS))
        if stored != current:
            raise ValueError("deterministic bundle manifest is stale")
        fixture = Path(args.fixture).resolve()
        with Image.open(fixture) as image:
            target_width = math.floor(image.width / args.screen_scale)
        artifact_dir = Path(args.artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        backends = args.backends.split(",")
        backend_versions = _backend_versions()
        _require_backends(backends, backend_versions)
        results = []
        for backend in backends:
            upstream = artifact_dir / f"upstream-{backend}.jpg"
            python = artifact_dir / f"python-{backend}.jpg"
            _upstream(Path(args.source).resolve(), fixture, target_width, backend, upstream.resolve(), args.timeout)
            _python(fixture, args.screen_scale, backend, python.resolve(), args.timeout)
            with Image.open(upstream) as up, Image.open(python) as py:
                dimensions = list(up.size)
                python_dimensions = list(py.size)
            psnr = _psnr(upstream, python)
            results.append({"backend": backend, "upstream": str(upstream), "python": str(python), "dimensions": dimensions, "python_dimensions": python_dimensions, "psnr_db": psnr})
        errors = [item for item in results if item["dimensions"] != item["python_dimensions"] or item["psnr_db"] < args.psnr_min]
        report_results = [{**item, "psnr_db": _json_psnr(item["psnr_db"])} for item in results]
        report = {"status": "failed" if errors else "passed", "psnr_min": args.psnr_min, "backend_versions": backend_versions, "results": report_results, "bundle": current, "provenance": provenance}
        write_json(args.report, report)
        if errors:
            print(f"image backend mismatch: {errors}", file=sys.stderr)
            return 1
        print(f"image backend parity passed: {len(results)} modes")
        return 0
    except ExceptionBlockedError as exc:
        write_json(args.report, {"status": "blocked", "reason": str(exc), "backend_versions": _backend_versions()})
        print(f"environment blocked: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        write_json(args.report, {"status": "blocked", "reason": str(exc)})
        print(f"environment blocked: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        write_json(args.report, {"status": "failed", "reason": str(exc)})
        print(f"image comparison failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from mobile_mcp_scenario_runner import prepare_scenario
from pymobile_mcp.server import PyMobileMCPServer


async def main() -> None:
    scenarios = yaml.safe_load(Path(os.environ["PYMOBILE_SCENARIOS"]).read_text())
    case_id = os.environ["PYMOBILE_SCENARIO_ID"]
    cases = [*scenarios["call_cases"], *scenarios["validation_and_error_cases"], *scenarios.get("review_cases", [])]
    case = next(item for item in cases if item["id"] == case_id)
    await prepare_scenario(case, scenarios, os.environ.get("PYMOBILE_EFFECT_LOG"))
    await PyMobileMCPServer().run()


if __name__ == "__main__":
    asyncio.run(main())

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ios_live_smoke_support import (
    apps,
    error_text,
    is_locked,
    is_unsupported,
    json_array,
    json_object,
    run_with_timeout,
    saved_path,
    screen_size,
    elements,
)


def _content(text: str):
    return [SimpleNamespace(type="text", text=text)]


def test_parses_mobile_mcp_success_content():
    assert json_object(_content('{"devices":[{"id":"ios-1"}]}')) == {
        "devices": [{"id": "ios-1"}]
    }
    assert screen_size(_content("Screen size is 1179x2556 pixels")) == {
        "width": 1179,
        "height": 2556,
    }
    assert elements(
        _content('Found these elements on screen: [{"coordinates":{"x":1}}]')
    ) == [{"coordinates": {"x": 1}}]
    assert apps(
        _content("Found these apps on device: Settings (com.apple.Preferences)")
    ) == [{"appName": "Settings", "packageName": "com.apple.Preferences"}]
    assert saved_path(_content("Screenshot saved to: tmp-ios.png")) == Path(
        "tmp-ios.png"
    )
    assert json_array(_content('[{"id":"crash-1"}]')) == [{"id": "crash-1"}]
    assert error_text(_content("Pressed the button: HOME")) is None


def test_classifies_actionable_unsupported_and_locked_text():
    actionable = _content("Bad input. Please fix the issue and try again.")
    unsupported = _content(
        'Button "BACK" is not supported on iOS via WDA hardware buttons.. Please fix the issue and try again.'
    )
    locked = _content("Error: iPhone is locked; unlock it to open URLs.")

    assert error_text(actionable) == actionable[0].text
    assert is_unsupported(error_text(unsupported))
    assert is_locked(error_text(locked))


@pytest.mark.asyncio
async def test_timeout_wrapper_blocks_without_a_device(monkeypatch, capsys):
    monkeypatch.setenv("PYMOBILE_MCP_LIVE_TIMEOUT", "0.01")

    async def hangs() -> int:
        await asyncio.sleep(60)
        return 0

    assert await run_with_timeout(hangs) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "blocked"
    assert output["timeout_seconds"] == 0.01

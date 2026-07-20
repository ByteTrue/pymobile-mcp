from pathlib import Path

import pytest


def test_windows_screenshot_without_scaler_returns_png(monkeypatch):
    from pymobile_mcp.tools import contract

    png = Path("tests/fixtures/mobile_mcp/input-1080x2400.png").read_bytes()
    monkeypatch.setattr(contract.platform, "system", lambda: "Windows")
    monkeypatch.setattr(contract.shutil, "which", lambda _name: None)

    assert contract.screenshot(png, 3).mimeType == "image/png"


@pytest.mark.asyncio
async def test_ios_core_smoke_inherits_wda_environment(monkeypatch):
    import ios_pmd3_wda_live_smoke as smoke
    import mcp.client.stdio as stdio

    expected = {
        "PYMOBILE_MCP_WDA_XCTRUNNER": "com.example.CustomRunner.xctrunner",
        "PYMOBILE_MCP_WDA_PORT": "8200",
        "PYMOBILE_MCP_IOS_DEVICE": "ios-gray-device",
    }
    for name, value in expected.items():
        monkeypatch.setenv(name, value)

    class Captured(Exception):
        pass

    def capture(*_args, **kwargs):
        assert kwargs["env"] == {**dict(smoke.os.environ), "PYTHONPATH": "src"}
        raise Captured

    monkeypatch.setattr(stdio, "StdioServerParameters", capture)
    with pytest.raises(Captured):
        await smoke.main()


def test_wda_host_is_not_advertised():
    for path in (
        Path("README.md"),
        Path("docs/regression-checklist.md"),
        Path("tests/ios_pmd3_wda_live_smoke.py"),
    ):
        assert "PYMOBILE_MCP_WDA_HOST" not in path.read_text(), path

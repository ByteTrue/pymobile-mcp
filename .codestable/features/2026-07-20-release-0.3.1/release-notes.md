## v0.3.1

Patch release for gray-test compatibility and packaging polish.

### Fixed

- Windows screenshot capture no longer calls unavailable `os.uname()`; when no scaler is installed, the original PNG is returned.
- iOS core live smoke now forwards parent environment variables to its MCP subprocess, so custom WDA runner, port, and device settings take effect.
- Removed the misleading `PYMOBILE_MCP_WDA_HOST` configuration claim. `PYMOBILE_MCP_WDA_PORT` is the userspace RSD service-client port, not a remote WDA URL.

### Packaging

- Added GPL-3.0 license metadata and PyPI badge/install guidance.
- Published wheel and sdist through GitHub Actions Trusted Publisher with digital attestations.

### Validation

- 110 tests passed locally.
- GitHub CI passed on Python 3.11 and 3.12.
- Wheel/sdist build and Twine checks passed.

Full details: [CHANGELOG.md](https://github.com/ByteTrue/pymobile-mcp/blob/v0.3.1/CHANGELOG.md)

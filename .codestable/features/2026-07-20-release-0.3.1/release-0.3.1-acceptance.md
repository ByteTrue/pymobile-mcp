---
doc_type: feature-acceptance
slug: release-0.3.1
status: passed
created: 2026-07-20
---

# release-0.3.1 Acceptance

## Verdict

**passed / published**

## Release identity

- Release commit: `ef2ea1c422ea52476c4dee1244b92694ab8af8d9`
- `origin/main`: same commit
- Annotated tag: `v0.3.1` → same commit
- GitHub Release: https://github.com/ByteTrue/pymobile-mcp/releases/tag/v0.3.1
- PyPI: https://pypi.org/project/pymobile-mcp/0.3.1/
- Trusted Publisher run: https://github.com/ByteTrue/pymobile-mcp/actions/runs/29729370259

## Validation

- Local full suite: 110 passed.
- GitHub CI Python 3.11/3.12: passed (run 29729303554).
- Build and Twine: wheel + sdist passed.
- PyPI JSON: 0.3.1, wheel + sdist present, GPL-3.0-only metadata and LICENSE present.
- Fresh Python 3.11 install from PyPI: metadata and `__version__` both 0.3.1.
- Fresh `pymobile-mcp --help`: passed.
- GitHub Release is public, non-draft, non-prerelease.

## Residual risk

No core release gap. Real-device gray feedback was acceptance-tested before this release; this release audit does not rerun device live smoke.

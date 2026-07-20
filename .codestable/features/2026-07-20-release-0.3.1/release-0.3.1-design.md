---
doc_type: feature-design
slug: release-0.3.1
status: approved
created: 2026-07-20
nature: non-functional
---

# v0.3.1 patch release

## Goal

Publish the accepted iOS gray-feedback fixes and pending packaging cleanup as `pymobile-mcp 0.3.1`.

## Scope

- Bump `pyproject.toml` and `src/pymobile_mcp/__init__.py` to `0.3.1`.
- Move current Unreleased notes into `0.3.1 — 2026-07-20` and add the three gray-feedback fixes.
- Update README install/release references and regression-checklist header.
- Update the publish workflow's manual-dispatch example/default to `v0.3.1`; tag pushes remain authoritative.
- Build and inspect wheel/sdist, run full tests, independent review, and acceptance.
- Fast-forward `origin/main`, create annotated `v0.3.1`, publish GitHub Release, verify Trusted Publisher and clean-install smoke.

## Non-goals

No runtime change beyond already accepted commit `5ebcf2c`; no dependency, tool schema, oracle, or approved-exception changes.

## Acceptance

- Version metadata agrees on `0.3.1`.
- Full tests and package build pass; wheel/sdist contain expected version and no local artifacts.
- `origin/main`, annotated tag, GitHub Release, workflow, and PyPI all resolve to this release.
- Fresh install reports `0.3.1` and CLI help succeeds.
- Blocked/failed publication is never reported as success.

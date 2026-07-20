---
doc_type: feature-review
slug: release-0.3.1
status: passed
created: 2026-07-20
reviewer: independent-subagent
---

# release-0.3.1 Pre-release Review

## Verdict

**READY** for release.

## Evidence consumed

- Version metadata, changelog, README, regression checklist, publish workflow.
- Full tests: 110 passed.
- Build and Twine checks: wheel + sdist passed.
- Artifact inspection: 0.3.1 metadata, LICENSE, no local cache/egg-info in wheel, corrected README/WDA contract.
- Diff check: passed.

## Findings

- Blocking / important / minor release-metadata defects: 0.
- `Unreleased` is intentionally empty after the release cut.
- Tag, GitHub Release, workflow publication, PyPI index, and clean install remain post-review release steps; they are not pre-release readiness evidence and must not be marked passed before execution.

## Safe order

Release commit → fast-forward main → wait CI → annotated tag → push tag → Trusted Publisher success → GitHub Release/PyPI/clean-install audit.

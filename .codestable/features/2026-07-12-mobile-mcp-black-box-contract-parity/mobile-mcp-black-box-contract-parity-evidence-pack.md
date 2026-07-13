# mobile-mcp-black-box-contract-parity Evidence Pack

## Scope

- Baseline: `4ce5dfcc3cbd932a17c904da72ea53485f37ba3d`.
- Fixed upstream: `mobile-mcp@c5d7d27fd61e4762e15ae4b1c68b6c011be88bb7`.
- Approved exceptions remain exactly `EXC-REMOTE-FLEET-RUNTIME` and `EXC-IOS-SCREEN-RECORDING-RUNTIME`.
- Public runtime and exception scope are unchanged.
- Current lifecycle: `acceptance/ready`; the latest independent review and final QA passed with no blockers. The acceptance report is created and remains `blocked` (not passed): the independent acceptance auditor found 19/19 checks passed, DOD-ACCEPT-001 substantively satisfied, no blocking or important findings, and recommended Accept. User final confirmation is the sole pending item.

## Current Automated Evidence

| ID | Status | Current result | Report |
|---|---|---|---|
| CMD-001 | passed, exit 0 | 107 passed | `evidence/pytest.json` / `evidence/pytest.xml` |
| CMD-002 | passed, exit 0 | exact pinned npm command; 23 tools | `evidence/capture-default.json` |
| CMD-003 | passed, exit 0 | exact pinned npm command; 26 tools | `evidence/capture-fleet.json` |
| CMD-004 | passed, exit 0 | exact pinned npm command; 47 call results; full bundle object | `evidence/capture-calls.json` |
| CMD-005 | passed, exit 0 | default 23 tools / 106 scenarios | `evidence/assert-default.json` |
| CMD-006 | passed, exit 0 | fleet 26 tools / 110 scenarios | `evidence/assert-fleet.json` |
| CMD-007 | passed, exit 0 | 91 source-linked scenarios | `evidence/source-coverage.json` |
| CMD-008 | passed, exit 0 | exact pinned npm command; 3 modes | `evidence/image-backends.json` |

CMD-002/003/004/008 use `npx --yes --package npm@12.0.0 -c`. Current deterministic bundle SHA-256 is `952c55cf10c45ce35857016a70639ea3cc4377b5bea31bd3b30cb57c06a1889c`. The bundle manifest, CMD-004 full bundle report, call-golden provenance, CMD-005/006/007 reports, and CMD-008 report all reference that final bundle.

## TDD Evidence

- Latest RED: the focused live-artifact regression failed on the nonexistent `evidence/images/psnr-sips.json` report (`1 failed`).
- Latest GREEN: all scenario-declared upstream, Python, and consolidated report paths are committed regular files (`1 passed`).
- Full regression: `107 passed`.

## Current Manual / Live Evidence

- LIVE-001 remains **passed**: Android physical, Android emulator, iOS Simulator, and iOS real device; 16/16 feature sub-smokes.
- Android recording live passed.
- iOS Simulator recording live passed.
- iOS real-device recording remains the exact approved exception.
- PI-001 remains **passed**.
- Destructive install/uninstall remains not-authorized/not-run and is not counted as passed.

## Gate Disposition

Implementation verification and final independent QA passed with pytest 107, default 23/106, fleet 26/110, source 91, image 3 modes, artifact regression passed, deterministic bundle `952c55cf10c45ce35857016a70639ea3cc4377b5bea31bd3b30cb57c06a1889c`, preserved LIVE-001 16/16, and preserved PI-001 passed. The latest independent review passed with no blocking or important findings. The lifecycle is `acceptance/ready`; the acceptance report is created and remains blocked/not passed, while the independent acceptance auditor recommends Accept after confirming 19/19 checks and substantive satisfaction of DOD-ACCEPT-001. User final confirmation is the sole pending item.

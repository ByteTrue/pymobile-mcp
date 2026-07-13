# Oracle / Deterministic Bundle Upgrade Playbook

SOP for maintaining or upgrading the pinned `mobile-mcp` black-box oracle.
This document is operational only: **0.3 productize does not upgrade the pin**.

Authoritative command table and provenance live in:

- `.codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/`
- ADR: `.codestable/requirements/adrs/001-black-box-mobile-mcp-wire-contract.md`

## Pin / tool chain (current)

| Item | Value |
|---|---|
| Upstream repo | `mobile-next/mobile-mcp` |
| Git revision | `c5d7d27fd61e4762e15ae4b1c68b6c011be88bb7` (`c5d7d27`) |
| Source tag | `0.0.61` |
| package-lock SHA-256 | `a85bcc836ace219e24e039edab27adb309482961b8f91ab72de0ad2ea01b4ae5` |
| Node | `v24.15.0` |
| npm | `12.0.0` (use `npx --yes --package npm@12.0.0 -c '...'` for capture/image) |
| Deterministic bundle aggregate SHA-256 | `952c55cf10c45ce35857016a70639ea3cc4377b5bea31bd3b30cb57c06a1889c` |
| Bundle manifest | `tests/fixtures/mobile_mcp/bundle-manifest.json` |

### Upstream path env

```bash
export PYMOBILE_MCP_UPSTREAM_SOURCE="/path/to/mobile-mcp-checkout"
# alias accepted by some local docs/tests:
# export MOBILE_MCP_SOURCE="$PYMOBILE_MCP_UPSTREAM_SOURCE"
```

Playbook templates use `"$PYMOBILE_MCP_UPSTREAM_SOURCE"` only. Never hard-code a machine absolute path in this file.

## Exit codes (fail-closed)

| Exit | Meaning |
|---|---|
| `0` | passed |
| `1` | failed / mismatch |
| `2` | environment **blocked** (missing upstream, backend, credentials, etc.) |

Rules:

- **blocked ≠ pass**. Exit `2` never counts as attestation pass.
- Any of CMD-001~008 exit `1` or `2` blocks a pin-upgrade attestation.
- `approved_exception` is a **scoped disposition**, not a free pass:
  - ledger `approval: pending|rejected` → environment blocked (exit `2`)
  - ledger `approval: approved` only allows the listed case IDs / tools / env / platform scope
  - text / `isError` / scope must still match the ledger; mismatch → exit `1`
  - never aggregate “has approved exceptions” into overall pass when other cases fail

## Existing scripts (no new abstraction)

| Script | Role | Takes `--source`? |
|---|---|---|
| `scripts/capture_mobile_mcp_contract.py` | CMD-002/003 initialize + tools/list goldens | yes |
| `scripts/capture_mobile_mcp_calls.py` | CMD-004 CallToolResult / error goldens | yes |
| `scripts/assert_mobile_mcp_contract.py` | CMD-005/006 Python wire assert vs goldens | **no** |
| `scripts/validate_mobile_mcp_source_coverage.py` | CMD-007 source links + ledger scope | yes |
| `scripts/compare_mobile_mcp_image_backends.py` | CMD-008 image backend parity | yes |

Shared helpers (not separate entrypoints): `scripts/contract_common.py`, `scripts/run_with_timeout.py`.

Required flags (from CLI `--help`):

- capture contract: `--source --mode {default,fleet} --expected-revision --expected-lock-sha256 --expected-node --expected-npm --raw-frames --output --report` (+ optional `--clean-install --timeout`)
- capture calls: `--source --expected-revision --expected-lock-sha256 --expected-node --expected-npm --scenarios --bundle-manifest --fixture-root --node-preload --scaling-modes --raw-frames --output --report` (+ optional `--clean-install --timeout`)
- assert: `--mode {default,fleet} --scenarios --exceptions --bundle-manifest --golden --calls --raw-frames --report` (+ optional `--timeout`) — **does not accept `--source`**
- source coverage: `--source --expected-revision --scenarios --exceptions --bundle-manifest --report` (+ optional `--timeout`)
- image backends: `--source --expected-revision --expected-lock-sha256 --expected-node --expected-npm --bundle-manifest --fixture --screen-scale --backends --psnr-min --artifact-dir --report` (+ optional `--timeout`)

## A. No-op maintenance (pin remains `c5d7d27`)

Use when shipping docs/release productize without changing upstream pin.

```bash
# CMD-001 — unit + embedded black-box
PATH=.venv/bin:$PATH python -m pytest

# Bundle must stay clean — do not re-capture without pin change
test -z "$(git status --porcelain -- tests/fixtures/mobile_mcp/bundle-manifest.json)"
```

**Forbidden without an explicit pin-upgrade task:**

- re-running CMD-002~008 capture paths “just in case”
- rewriting wire/call goldens or `bundle-manifest.json`
- changing exception ledger approval or scopes as a side effect

0.3 release gate is: pytest green + clean bundle. That is **not** a full wire re-attestation.

## B. Pin upgrade full re-capture

Only after an approved task that moves the pin off `c5d7d27`.

1. Check out the new upstream revision under `"$PYMOBILE_MCP_UPSTREAM_SOURCE"`.
2. Recompute expected lock SHA / node / npm for that checkout; update pin table + checklist commands together.
3. Run CMD-002 → CMD-003 → CMD-004 → CMD-005 → CMD-006 → CMD-007 → CMD-008 in order.
4. Commit refreshed fixtures, evidence reports, bundle-manifest, scenarios/exceptions as needed.
5. Re-run CMD-001.
6. Treat any exit `2` as blocked attestation; fix env and re-run. Do not ship “mostly green”.

### Command templates (sanitized)

Replace pin constants when upgrading. Paths are repo-relative.

```bash
export PYMOBILE_MCP_UPSTREAM_SOURCE="${PYMOBILE_MCP_UPSTREAM_SOURCE:?set upstream checkout}"
export PIN_REV=c5d7d27fd61e4762e15ae4b1c68b6c011be88bb7
export PIN_LOCK=a85bcc836ace219e24e039edab27adb309482961b8f91ab72de0ad2ea01b4ae5
export PIN_NODE=v24.15.0
export PIN_NPM=12.0.0
FEATURE=.codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity
SCENARIOS=$FEATURE/mobile-mcp-black-box-contract-parity-scenarios.yaml
EXCEPTIONS=$FEATURE/mobile-mcp-black-box-contract-parity-exceptions.yaml
BUNDLE=tests/fixtures/mobile_mcp/bundle-manifest.json
```

#### CMD-002 — capture default

```bash
npx --yes --package npm@12.0.0 -c 'MOBILEMCP_DISABLE_TELEMETRY=1 PATH=.venv/bin:$PATH python scripts/capture_mobile_mcp_contract.py --source "$PYMOBILE_MCP_UPSTREAM_SOURCE" --mode default --clean-install --expected-revision '"$PIN_REV"' --expected-lock-sha256 '"$PIN_LOCK"' --expected-node '"$PIN_NODE"' --expected-npm '"$PIN_NPM"' --timeout 30 --raw-frames .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/evidence/upstream-default.jsonl --output tests/fixtures/mobile_mcp_wire_default.json --report .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/evidence/capture-default.json'
```

#### CMD-003 — capture fleet

```bash
npx --yes --package npm@12.0.0 -c 'MOBILEMCP_DISABLE_TELEMETRY=1 PATH=.venv/bin:$PATH python scripts/capture_mobile_mcp_contract.py --source "$PYMOBILE_MCP_UPSTREAM_SOURCE" --mode fleet --clean-install --expected-revision '"$PIN_REV"' --expected-lock-sha256 '"$PIN_LOCK"' --expected-node '"$PIN_NODE"' --expected-npm '"$PIN_NPM"' --timeout 30 --raw-frames .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/evidence/upstream-fleet.jsonl --output tests/fixtures/mobile_mcp_wire_fleet.json --report .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/evidence/capture-fleet.json'
```

#### CMD-004 — capture calls

```bash
npx --yes --package npm@12.0.0 -c 'MOBILEMCP_DISABLE_TELEMETRY=1 PATH=tests/fixtures/mobile_mcp/fake-bin:.venv/bin:$PATH MOBILECLI_PATH=tests/fixtures/mobile_mcp/fake-bin/mobilecli python scripts/capture_mobile_mcp_calls.py --source "$PYMOBILE_MCP_UPSTREAM_SOURCE" --expected-revision '"$PIN_REV"' --expected-lock-sha256 '"$PIN_LOCK"' --expected-node '"$PIN_NODE"' --expected-npm '"$PIN_NPM"' --clean-install --scenarios .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-scenarios.yaml --bundle-manifest tests/fixtures/mobile_mcp/bundle-manifest.json --fixture-root tests/fixtures/mobile_mcp --node-preload tests/fixtures/mobile_mcp/fakes/child-process-hook.cjs --scaling-modes no_scaling,sips,imagemagick,sips_fallback,scaling_failure --timeout 30 --raw-frames .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/evidence/upstream-calls.jsonl --output tests/fixtures/mobile_mcp_call_results.json --report .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/evidence/capture-calls.json'
```

#### CMD-005 — assert default (no `--source`)

```bash
PATH=.venv/bin:$PATH python scripts/assert_mobile_mcp_contract.py \
  --mode default \
  --scenarios .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-scenarios.yaml \
  --exceptions .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-exceptions.yaml \
  --bundle-manifest tests/fixtures/mobile_mcp/bundle-manifest.json \
  --golden tests/fixtures/mobile_mcp_wire_default.json \
  --calls tests/fixtures/mobile_mcp_call_results.json \
  --timeout 30 \
  --raw-frames .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/evidence/python-default.jsonl \
  --report .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/evidence/assert-default.json
```

#### CMD-006 — assert fleet (no `--source`)

```bash
PATH=.venv/bin:$PATH python scripts/assert_mobile_mcp_contract.py \
  --mode fleet \
  --scenarios .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-scenarios.yaml \
  --exceptions .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-exceptions.yaml \
  --bundle-manifest tests/fixtures/mobile_mcp/bundle-manifest.json \
  --golden tests/fixtures/mobile_mcp_wire_fleet.json \
  --calls tests/fixtures/mobile_mcp_call_results.json \
  --timeout 30 \
  --raw-frames .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/evidence/python-fleet.jsonl \
  --report .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/evidence/assert-fleet.json
```

#### CMD-007 — source coverage

```bash
PATH=.venv/bin:$PATH python scripts/validate_mobile_mcp_source_coverage.py \
  --source "$PYMOBILE_MCP_UPSTREAM_SOURCE" \
  --expected-revision "$PIN_REV" \
  --scenarios .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-scenarios.yaml \
  --exceptions .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/mobile-mcp-black-box-contract-parity-exceptions.yaml \
  --bundle-manifest tests/fixtures/mobile_mcp/bundle-manifest.json \
  --timeout 30 \
  --report .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/evidence/source-coverage.json
```

#### CMD-008 — image backends

```bash
npx --yes --package npm@12.0.0 -c 'MOBILEMCP_DISABLE_TELEMETRY=1 PATH=.venv/bin:$PATH python scripts/compare_mobile_mcp_image_backends.py --source "$PYMOBILE_MCP_UPSTREAM_SOURCE" --expected-revision '"$PIN_REV"' --expected-lock-sha256 '"$PIN_LOCK"' --expected-node '"$PIN_NODE"' --expected-npm '"$PIN_NPM"' --bundle-manifest tests/fixtures/mobile_mcp/bundle-manifest.json --fixture tests/fixtures/mobile_mcp/input-1080x2400.png --screen-scale 3 --backends sips,imagemagick,sips_fallback --psnr-min 35 --timeout 30 --artifact-dir .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/evidence/images --report .codestable/features/2026-07-12-mobile-mcp-black-box-contract-parity/evidence/image-backends.json'
```

#### CMD-001 after refresh

```bash
PATH=.venv/bin:$PATH python -m pytest
```

## C. What to update after a successful pin upgrade

1. Pin constants in this playbook and black-box checklist DoD commands.
2. Wire/call fixtures under `tests/fixtures/`.
3. `tests/fixtures/mobile_mcp/bundle-manifest.json` aggregate + entry hashes.
4. Evidence JSON under the black-box feature `evidence/` directory.
5. Exception ledger only if upstream behavior or project policy genuinely changed (separate review).
6. README / CHANGELOG pin wording when cutting a release that absorbs the new pin.

## D. Dry-run checks (no capture)

```bash
# scripts exist
test -f scripts/capture_mobile_mcp_contract.py
test -f scripts/capture_mobile_mcp_calls.py
test -f scripts/assert_mobile_mcp_contract.py
test -f scripts/validate_mobile_mcp_source_coverage.py
test -f scripts/compare_mobile_mcp_image_backends.py

# playbook documents env, flags, blocked semantics
grep -q PYMOBILE_MCP_UPSTREAM_SOURCE docs/oracle-upgrade-playbook.md
grep -q -- --source docs/oracle-upgrade-playbook.md
grep -q -- --mode docs/oracle-upgrade-playbook.md
grep -q -- --expected-revision docs/oracle-upgrade-playbook.md
grep -q -- --scenarios docs/oracle-upgrade-playbook.md
grep -q -- --bundle-manifest docs/oracle-upgrade-playbook.md
grep -q blocked docs/oracle-upgrade-playbook.md
python -c 'from pathlib import Path; needle="/"+"Users/"; assert needle not in Path("docs/oracle-upgrade-playbook.md").read_text()'  # fails if absolute home paths appear
```

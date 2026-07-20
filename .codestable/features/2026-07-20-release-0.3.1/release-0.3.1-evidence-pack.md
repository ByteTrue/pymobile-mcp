# release-0.3.1 Evidence Pack

## Scope

Patch release metadata for accepted gray-feedback commit `5ebcf2c`, plus the packaging cleanup already on main.

## Validation

- `.venv/bin/python -m pytest -q` → 110 passed.
- `.venv/bin/python -m build` → wheel and sdist built.
- `.venv/bin/python -m twine check dist/*` → both passed.
- Artifact inspection → version 0.3.1, LICENSE present, no egg-info/cache in wheel, README install command and WDA host correction present.
- `git diff --check` → passed.

## Artifacts

- `dist/pymobile_mcp-0.3.1-py3-none-any.whl`
- `dist/pymobile_mcp-0.3.1.tar.gz`

`dist/` is ignored and will not be committed.

## Residual Risks

PyPI publication and clean-index install can only be verified after tag-triggered Trusted Publisher completes. Until then, release status is not passed.

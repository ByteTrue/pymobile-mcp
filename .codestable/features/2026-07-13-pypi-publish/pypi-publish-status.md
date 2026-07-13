---
doc_type: pypi-publish-status
feature: 2026-07-13-pypi-publish
version: 0.3.0
status: published
timestamp: 2026-07-13T22:20:00+08:00
---

# pypi-publish status

```yaml
status: published
version: 0.3.0
reason: "Trusted Publisher OIDC publish succeeded via GitHub Actions workflow publish.yml"
timestamp: 2026-07-13T22:20:00+08:00
evidence: |
  - Pending publisher: project pymobile-mcp, ByteTrue/pymobile-mcp, workflow publish.yml, Environment (Any)
  - Workflow: https://github.com/ByteTrue/pymobile-mcp/actions/runs/29257502460 (success)
  - PyPI JSON: https://pypi.org/pypi/pymobile-mcp/json → version 0.3.0
  - pip index versions pymobile-mcp → Available versions: 0.3.0
  - pip install --dry-run pymobile-mcp==0.3.0 → Would install pymobile-mcp-0.3.0
  - Project page: https://pypi.org/project/pymobile-mcp/
```

## Classification

- published via Trusted Publisher (no long-lived API token)
- optional feature outcome no longer blocked-by-env

# parity-hardening-docs Evidence Pack

## Aggregate commands

1. `python -m pytest`
2. Android live smokes from README (device present on this host)
3. iOS live smokes from README (blocked-by-env, documented)
4. YAML validate + goal consistency gate (if tool available)

## Knowledge candidates (do not auto-write)

- ADR: Android-first pure Python MCP with optional iOS WDA HTTP adapter
- ADR: crash/recording capability boundaries and unsupported_platform policy
- compound: screenrecord stop via device pkill -INT, not only local adb SIGINT
- attention: live smoke may not count skip/no-device as pass

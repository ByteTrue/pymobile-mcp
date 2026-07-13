# PI-001 脱敏证据（passed）

- Observed: `2026-07-13`
- Pi: `0.80.6`
- Project commit at run start: `4ce5dfcc3cbd932a17c904da72ea53485f37ba3d`
- MCP config: command=`<feature-worktree>/.venv/bin/python -m pymobile_mcp.cli run`, cwd=`<feature-worktree>`, env=`NO_PROXY=*`, `directTools=true`; no credentials；设备 ID 脱敏。
- Fresh-session discovery: Pi 在首轮直接暴露 prefixed tools `pymobile_mcp_mobile_*`；未经过 generic `mcp` gateway。

## Direct-tools calls

| Direct tool | Redacted input | Result | MCP disposition |
|---|---|---|---|
| `pymobile_mcp_mobile_list_available_devices` | `{}` | 3 online endpoints：Android physical、Android emulator、iOS Simulator | text content；normal result |
| `pymobile_mcp_mobile_get_screen_size` | `{device: <android-emulator>}` | `Screen size is 1080x2400 pixels` | text content；normal result |
| `pymobile_mcp_mobile_take_screenshot` | `{device: <android-emulator>}` | Pi rendered the real 1080x2400 launcher screenshot as image content | image content；normal result |
| `pymobile_mcp_mobile_press_button` | `{device: <android-emulator>, button: HOME}` | `Pressed the button: HOME` | text content；normal result |
| `pymobile_mcp_mobile_open_url` | `{device: <android-emulator>, url: demo://home}` | `Only http:// and https:// URLs are allowed. Set MOBILEMCP_ALLOW_UNSAFE_URLS=1 to allow other URL schemes.. Please fix the issue and try again.` | actionable text returned normally；`isError` not raised by direct-tool wrapper（与 upstream omitted/false 行为一致） |

## Verdict

**passed**。Fresh Pi session 在第一次 model turn 即自然提供 direct tools；device argument 正常透传；text、image、action 与 actionable-error 路径均可直接使用。没有生成或提交 session HTML、设备序列号或凭据。

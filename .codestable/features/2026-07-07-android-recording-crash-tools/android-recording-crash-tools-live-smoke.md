# android-recording-crash-tools Live Smoke

## Command

```bash
PATH=.venv/bin:$PATH python tests/android_recording_crash_live_smoke.py
```

## Result (2026-07-11)

```json
{
  "status": "passed",
  "device": "emulator-5554",
  "recording_size": 3232,
  "crash": "unsupported_platform"
}
```

## Crash spike

- tombstones / dropbox 无稳定非 root 可读完整 crash 内容
- `dumpsys dropbox` 仅有摘要，不可作为可靠 get_crash 来源
- 因此 Android crash tools 返回 `unsupported_platform`，不伪造成功空列表

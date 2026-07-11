# iOS Screen Recording Spike

Date: 2026-07-11  
Constraint: pure pymobiledevice3 only (no go-ios / mobilecli).

## Candidate path

`pymobiledevice3.remote.core_device.screen_stream.capture_rtp_to_file`
→ `DisplayService` / `com.apple.coredevice.displayservice`
→ raw RTP/HEVC dump (not MP4; needs extra depacketize/transcode).

## Live result on C's iPhone (iOS 26.5.2)

Using existing `UserspaceRsdTunnel` + process tunnel singleton:

```
InvalidServiceError: No such service: com.apple.coredevice.displayservice
```

So the pure userspace RSD path that already powers WDA/UI/app/crash **does not advertise** the coredevice display media-stream service needed for video capture.

## Implications

- Cannot implement `mobile_start/stop_screen_recording` for iOS as a true MP4 path with current stack.
- mobile-mcp reference uses external `mobilecli screenrecord` (go-ios lineage) — out of scope.
- Keep `unsupported_platform` with explicit message (already present).
- Revisit when: developer disk / coredevice display service is available on the same RSD connection, or pmd3 exposes a simpler userspace recorder that writes host MP4 without go-ios.

## Decision

Ship **documented unsupported** with reproducible spike evidence. Do not fake recording or shell out to go-ios.

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

## Live re-check 2026-07-11 (device reconnected)

Device: C’s iPhone / `00008140-0008484C3AC2801C` / iOS 26.5.2  
pmd3: 9.33.1  
Developer Mode: true  
DDI: already mounted (`IsMounted: true`, Personalized DeveloperDiskImage)

### Path A — CoreDevice DisplayService (official pmd3 video stream)

CLI:
```
pymobiledevice3 developer core-device display get-media-support-info --userspace
# ERROR: Failed to start service ... Apple removed this service, or your iOS version does not support it.
```

Userspace RSD peer services (74 total): has several `com.apple.coredevice.*`
(`appservice`, `deviceinfo`, `fileservice`, `diagnosticsservice`, …)
but **no**:
- `com.apple.coredevice.displayservice`
- `com.apple.coredevice.screencaptureservice`

So on this iOS 26.5.2 + userspace RSD, DisplayService is **not advertised**.
Official docs claim userspace supports `display start-video-stream`, but that
depends on the device advertising the service; this device/build does not.

### Path B — WDA `/wda/video/*` (present on installed runner 15.1.3)

```
POST /wda/video/start  -> 200 {startedAt,fps,codec,uuid}
GET  /wda/video        -> 200 same status
POST /wda/video/stop   -> 500 XCTDaemon.ScreenRecordingError Code=2
  "Failed to finalize screen recording."
```

Also observed DTX decode noise while finalizing attachments:
`MissingClassMapping: XCTAttachmentFutureMetadata` / `XCTAttachmentFuture`.

Interpretation: start succeeds (XCTest screen recording begins), finalize/export
to host fails on this stack. Not a usable MP4 pipeline yet.

### Decision (updated)

Still **do not ship** iOS `mobile_*_screen_recording` as supported:
1. CoreDevice display stream: service missing on this OS/RSD.
2. WDA video: start-only; stop/finalize broken.
3. go-ios/mobilecli: out of policy.

Revisit when either:
- `com.apple.coredevice.displayservice` appears on RSD for this device, or
- WDA `/wda/video/stop` returns a media payload without finalize error.

---
doc_type: live-smoke-evidence
feature: 2026-07-07-android-live-ui-slice
status: passed
tested: 2026-07-10
device: emulator-5554
---

# Android live smoke evidence

## Environment

- Device id: `emulator-5554`
- Device name: `sdk_gphone64_arm64`
- Android version: `16`
- Device state: `online`

## Commands

```bash
.venv/bin/python -m pytest
PYMOBILE_MCP_ANDROID_ACTIONS=1 PATH=.venv/bin:$PATH python tests/android_live_smoke.py
```

## Results

- `python -m pytest`: 37 passed.
- live smoke: passed.

```json
{
  "status": "passed",
  "device": "emulator-5554",
  "screen_size": {
    "height": 2400,
    "scale": 1.0,
    "width": 1080
  },
  "element_count": 41,
  "tap": {
    "x": 540.0,
    "y": 163.5
  }
}
```

## Covered MCP path

- `list_tools`: verified `mobile_get_page_source` is not exposed.
- `mobile_list_available_devices`: returned `emulator-5554` as online Android emulator.
- `mobile_get_screen_size`: returned positive width/height.
- `mobile_take_screenshot`: returned MCP image content with `image/png` MIME type.
- `mobile_list_elements_on_screen`: returned elements with `coordinates` fields.
- `mobile_click_on_screen_at_coordinates`: completed at safe search-field coordinate.
- `mobile_double_tap_on_screen`: completed at safe search-field coordinate.
- `mobile_long_press_on_screen_at_coordinates`: completed at safe search-field coordinate.
- `mobile_swipe_on_screen`: completed using default upward swipe.
- `mobile_type_keys`: typed ASCII `pymobile` and submitted Enter.

## Earlier blocked probe

Before the emulator was available, the same smoke script returned:

```json
{
  "status": "blocked",
  "reason": "no authorized Android device",
  "devices": []
}
```

This verifies the no-device path is blocked rather than passed.

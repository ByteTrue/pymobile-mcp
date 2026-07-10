# pymobile-mcp-post-mvp Goal Plan（draft）

## Roadmap

- Roadmap: `.codestable/roadmap/pymobile-mcp-post-mvp/pymobile-mcp-post-mvp-roadmap.md`
- Items: `.codestable/roadmap/pymobile-mcp-post-mvp/pymobile-mcp-post-mvp-items.yaml`

## Feature 执行顺序

| # | Feature slug | 性质 | 一句话交付物 |
|---|---|---|---|
| 1 | ios-live-wda-verification | functional | 真机 iOS core smoke passed + 复跑步骤 |
| 2 | ios-system-helpers-parity | functional | iOS button/url/save_screenshot 实现或 unsupported 证据 |
| 3 | ios-app-lifecycle-pmd3 | functional | iOS app lifecycle 实现或更新后的 unsupported 证据 |
| 4 | crash-tools-real-source | functional | crash list/get 真实现或可复现仍-unsupported spike |

## 前置

- Android MVP 已合入 main：`93641e3`
- iOS 真机验证此前主动搁置；本 roadmap 第一条就是把它打开

## 必跑验证

| ID | 命令 | 核心性 |
|---|---|---|
| CMD-001 | `python -m pytest` | core |
| CMD-IOS-LIVE-001 | `PATH=.venv/bin:$PATH python tests/ios_pmd3_wda_live_smoke.py` | core（有设备时） |
| CMD-IOS-PARITY-001 | `PATH=.venv/bin:$PATH python tests/ios_app_recording_crash_live_smoke.py` | core（app/crash 条目） |
| CMD-ANDROID-CRASH-001 | `PATH=.venv/bin:$PATH python tests/android_recording_crash_live_smoke.py` | core（crash 条目） |

## 状态

- roadmap status: **draft**（待用户确认后 review / goal-package）
- 未生成 feature design / goal-state；确认本规划后再推进

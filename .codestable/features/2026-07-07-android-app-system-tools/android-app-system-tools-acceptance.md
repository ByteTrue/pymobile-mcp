---
doc_type: feature-acceptance
feature: 2026-07-07-android-app-system-tools
status: passed
accepted: 2026-07-11
round: 1
---

# android-app-system-tools 验收报告

## 接口与场景

- [x] list_apps 返回 Android launcher apps
- [x] open_url 默认仅 http(s)；自定义 scheme 需 `MOBILEMCP_ALLOW_UNSAFE_URLS=1`
- [x] press_button / orientation get/set 可用
- [x] save_screenshot 安全路径写入；非法扩展名/越界路径失败
- [x] launch/terminate 可用；install/uninstall 有 destructive annotation 且 live 默认守卫
- [x] recording/crash 未实现

## 证据

- pytest: 38 passed
- live smoke: `android-app-system-tools-live-smoke.md`
- evidence pack: `android-app-system-tools-evidence-pack.md`

## roadmap 回写

- items/roadmap/goal-state 将在 scoped commit 前更新为 done/accepted

## Verdict

- Status: passed

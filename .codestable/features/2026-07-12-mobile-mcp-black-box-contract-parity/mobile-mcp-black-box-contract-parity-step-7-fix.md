# Step 7 窄修复说明

> Historical Step 7 evidence：the device failure/blocker below was resolved by later LIVE-001 evidence；current LIVE-001 remains passed at 16/16. Current lifecycle is `review/ready` after an acceptance-found QA-fix; independent review and QA rerun are pending, and acceptance is not passed.

- 失败退出信号：LIVE-001 Android recording 子项两次 `stop recording failed`，本地文件未生成。
- 诊断：driver 的实际 argv 已是 `adb -s <id> shell screenrecord --time-limit 10 <path>`；独立手工复现返回 exit 218：`ERROR: INVALID_LAYER_STACK, please check your display state.`，remote 文件为 0 bytes。先前 `pkill -l INT` 已更正为 `pkill -INT`，但本次启动在 stop 前即由设备拒绝。
- 窄范围结果：没有继续改 start argv；设备 display/screenrecord 环境阻塞，按 LIVE policy 记录 blocked，不伪装为 pass。
- 替代证据：recording fake scenario、Android driver unit contract、CMD-001/005/006；设备恢复 display state 后重跑 `tests/android_recording_crash_live_smoke.py`。

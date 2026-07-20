---
doc_type: feature-design
slug: ios-gray-feedback
status: approved
created: 2026-07-20
nature: functional
---

# iOS 灰度反馈修复

## 1. 目标

修复灰度用户确认的三个配置/兼容性问题：

1. Windows 调用截图时不得因 `os.uname()` 不存在而失败；无图像缩放后端时应返回原始 PNG。
2. `tests/ios_pmd3_wda_live_smoke.py` 启动 MCP 子进程时必须继承调用方环境，使 `PYMOBILE_MCP_WDA_XCTRUNNER` 等 iOS 配置生效。
3. 文档与 smoke 输出不得把 `PYMOBILE_MCP_WDA_HOST` 描述为可用的远程 WDA 地址；当前实现只通过 userspace RSD 的 service client 使用 WDA 端口。

## 2. 范围

允许修改：

- `src/pymobile_mcp/tools/contract.py`
- `tests/ios_pmd3_wda_live_smoke.py`
- 针对上述回归的测试文件
- `README.md` 与 `docs/regression-checklist.md`
- 本 feature 目录下的 CodeStable 交付物

明确不做：

- 不新增远程 WDA HTTP transport。
- 不移除 `PYMOBILE_MCP_WDA_PORT`；它仍用于 RSD service client 的端口。
- 不顺带统一所有历史 live-smoke 的环境构造。

## 3. 行为契约

### Windows 截图

`_sips_available()` 使用跨平台标准库判断 Darwin；在 Windows 上返回 `False`，不得访问不存在的 `os.uname`。若 ImageMagick 也不存在，`screenshot()` 保持上游既有降级行为，返回 `image/png` 原始截图。

### iOS core live-smoke

MCP 子进程环境以 `os.environ` 为基线，仅覆盖 `PYTHONPATH` 以加载当前源码。至少应保留：

- `PYMOBILE_MCP_WDA_XCTRUNNER`
- `PYMOBILE_MCP_WDA_PORT`
- `PYMOBILE_MCP_IOS_DEVICE`

### WDA 配置说明

- `PYMOBILE_MCP_WDA_XCTRUNNER`：runner bundle id。
- `PYMOBILE_MCP_WDA_PORT`：userspace RSD service client 使用的设备侧 WDA 端口。
- `PYMOBILE_MCP_WDA_HOST`：不受当前驱动支持，不再出现在可配置项或 live-smoke blocked 输出中。

## 4. 验收标准

- Windows 模拟测试证明 `_sips_available()` 不抛异常且截图回退为 PNG。
- iOS core smoke 单测证明 MCP 子进程环境继承自父进程并覆盖源码 `PYTHONPATH`。
- 仓库运行时代码、README、regression checklist 不再宣称 `PYMOBILE_MCP_WDA_HOST` 可用。
- focused tests 与完整 `pytest` 均通过。
- 独立 code review、QA、acceptance 均通过。

---
doc_type: roadmap
slug: pymobile-mcp-android-mvp
status: active
created: 2026-07-07
last_reviewed: 2026-07-07
tags: [mcp, mobile, android, ios, roadmap]
related_requirements: []
related_architecture: []
---

# pymobile-mcp Android-first mobile-mcp parity

## 1. 背景

`pymobile-mcp` 要用 Python + `uiautomator2` + `pymobiledevice3` 重写 `mobile-next/mobile-mcp`。对外 MCP 工具名、输入 schema 和返回语义以 mobile-mcp 源码为准；Kickoff 只保留技术栈背景，不作为额外工具契约来源。

本 roadmap 把完整目标拆成 Android-first 的可恢复路线：先稳定 MCP 工具契约，再做 Android 真机最小闭环，最后补齐 Android 周边、iOS 和 parity hardening。用户已确认首轮验收以 Android 真机 live smoke 为准：`list_devices → screen_size → screenshot → elements → tap/swipe/type`。

## 2. 范围与明确不做

### 本 roadmap 覆盖

- MCP server 能启动并注册 mobile-mcp 源码中的 23 个常驻核心工具契约。
- 所有未实现或当前平台不支持的工具返回稳定结构化错误，不假装成功。
- Android 真机 UI 自动化闭环：发现设备、截图、读取过滤后的 accessibility elements、点击、滑动、输入。
- Android app/system/recording/crash 工具逐步补齐。
- iOS 通过 `pymobiledevice3` 的 tunnel / WDA 链路补齐同一套 driver contract。
- 文档、smoke 测试和 parity 检查，保证后续 feature acceptance 可核验。

### 明确不做

- 不接入 `go-ios` / `mobilecli` 作为运行时依赖；这些只作为 mobile-mcp 行为参考。
- 不实现远程设备池工具：`mobile_list_remote_devices` / `mobile_allocate_remote_device` / `mobile_release_remote_device`，它们在 mobile-mcp 源码中受 `MOBILEFLEET_ENABLE` 控制，不属于本项目首批核心契约。
- 不在首个 Android vertical slice 里实现 iOS、recording、crash、完整 app lifecycle；这些是后续条目。
- 不为单一 driver 先做插件系统或多 adapter 框架；只有 Android/iOS 两个真实 driver，需要新平台时再扩展。
- 不保证非 ASCII Android 输入首轮一定完整支持；先按 `uiautomator2`/ADB 能力实现，发现 devicekit 类依赖再另行沉淀。

### Granularity Gate

| 判断项 | 结论 |
|---|---|
| 为什么不是 single feature | 该需求跨 MCP 协议层、工具契约、Android driver、iOS driver、测试/文档多个独立交付；每块都能独立 design、实现和验证。 |
| 为什么不是 brainstorm | 目标、首轮验收和技术栈已经明确；剩余工作是拆模块、定接口和排依赖。 |
| roadmap 边界 | 本次覆盖从契约骨架到 Android-first parity；远程设备池、Kickoff bonus 扩展和发布运营不纳入。 |
| 最小闭环 | `android-live-ui-slice` 完成后，已连接 Android 真机能通过 MCP 工具完成 `list_devices → screen_size → screenshot → elements → tap/swipe/type`。 |

## 3. 模块拆分（概设）

```text
pymobile-mcp
├── MCP Server / Tool Registry：注册工具、暴露 schema、把 handler 结果转成 MCP content
├── Tool Execution Layer：参数校验、设备选择、错误 envelope、session/recording 状态
├── Driver Contract：Android/iOS 共享的最小设备能力接口和数据结构
├── Android Driver：`uiautomator2` + `adbutils` 实现 Android 真机自动化
├── iOS Driver：`pymobiledevice3` tunnel + WDA client 实现 iOS 自动化
└── Verification / Docs：契约测试、live smoke、README/配置说明
```

### MCP Server / Tool Registry

- **职责**：使用 MCP 官方 SDK 启动 stdio server，注册工具名、title、description、input schema 和 annotations；把工具 handler 的返回值转换为 MCP `TextContent` / `ImageContent`。
- **不做**：不直接调用设备库，不保存设备状态。
- **承载的子 feature**：`contract-registry-scaffold`, `parity-hardening-docs`
- **触碰的现有代码 / 模块**：全新 `src/pymobile_mcp/server.py`、`src/pymobile_mcp/tools/`
- **Depth 判断**：deep。调用方只依赖 MCP tools；具体 driver 和错误处理藏在内部。

### Tool Execution Layer

- **职责**：根据 `device` 参数选择 driver，执行工具 handler，统一成功文本、图片内容和结构化错误；维护需要跨调用的少量状态（例如 screen recording）。
- **不做**：不把每个工具都拆成独立框架层；每个工具只保留最小 handler。
- **承载的子 feature**：全部工具实现条目
- **触碰的现有代码 / 模块**：全新 `src/pymobile_mcp/tools/*.py`、`src/pymobile_mcp/errors.py`
- **Depth 判断**：deep。错误策略、unsupported 平台和 driver lookup 集中在这里，避免散到每个 MCP handler。

### Driver Contract

- **职责**：定义 Android/iOS 都要实现的数据结构、异常和 async 方法；工具层只依赖这个 contract。
- **不做**：不暴露 driver 内部库对象，不把 MCP schema 泄漏进 driver。
- **承载的子 feature**：`contract-registry-scaffold`, `android-live-ui-slice`, `ios-pmd3-wda-core`
- **触碰的现有代码 / 模块**：全新 `src/pymobile_mcp/drivers/base.py`
- **Depth 判断**：deep。设备库替换时影响集中在 driver，不影响工具契约。

### Android Driver

- **职责**：用 `uiautomator2` 执行截图、元素列表（内部可读取 UIAutomator XML）、tap/swipe/type 等 UI 操作；用 `adbutils` 或标准 ADB 发现设备与补齐 app/system/recording/crash 能力。
- **不做**：不依赖 Node mobilecli；不先实现 Android TV 特化路径，除非 mobile-mcp core button enum 需要。
- **承载的子 feature**：`android-live-ui-slice`, `android-app-system-tools`, `android-recording-crash-tools`
- **触碰的现有代码 / 模块**：全新 `src/pymobile_mcp/drivers/android.py`
- **Depth 判断**：deep。Android 设备 quirks 集中在 driver。

### iOS Driver

- **职责**：用 `pymobiledevice3` 建立 userspace tunnel、启动/连接 WDA、执行同一 driver contract；处理 bundle/app lifecycle。
- **不做**：不回退到 go-ios；不把 WDA HTTP 细节暴露给 tools。
- **承载的子 feature**：`ios-pmd3-wda-core`, `ios-app-recording-crash-parity`
- **触碰的现有代码 / 模块**：全新 `src/pymobile_mcp/drivers/ios.py`
- **Depth 判断**：deep，但风险最高；WDA/tunnel 真实行为必须靠 live 或最小 spike 验证。

### Verification / Docs

- **职责**：提供 contract tests、可跳过的 live Android/iOS smoke、README 配置说明和能力状态表。
- **不做**：不搭大型测试框架或设备农场；先用最小 pytest + 手工 smoke 证据。
- **承载的子 feature**：`parity-hardening-docs`
- **触碰的现有代码 / 模块**：`tests/`、`README.md`、可能的 `docs/`
- **Depth 判断**：deep enough。验证入口是后续 acceptance 的恢复锚点。

## 4. 模块间接口契约 / 共享协议（架构层详设）

### 4.1 Tool Registry → Tool Execution

**方向**：MCP Server / Tool Registry → Tool Execution Layer  
**形式**：Python async 函数调用

**契约**：

```python
@dataclass(frozen=True)
class ToolSpec:
    name: str
    title: str
    description: str
    input_schema: dict[str, Any]
    read_only: bool = False
    destructive: bool = False

class ToolHandler(Protocol):
    spec: ToolSpec
    async def __call__(self, args: dict[str, Any]) -> list[McpContent]: ...

McpContent = TextContent | ImageContent
```

**约束**：

- `ToolSpec.name` 是外部契约，feature 内不得随意改名。
- 成功结果尽量对齐 mobile-mcp 文本/图片语义；截图工具返回 image content，其他工具默认 text content。
- handler 抛出的已知业务错误必须转为稳定结构化错误文本，不冒泡成 Python traceback。
- 外部边界是 `ToolSpec + handler`；工具实现可用函数或类，Kickoff 里的“one class per tool”不是硬约束。

**Interface 设计检查**：

- Module / interface：Tool Registry 只知道 `ToolSpec` 和 handler；不关心 Android/iOS。
- Seam placement：seam 放在 handler 调用边界；MCP protocol smoke 可替换 handler，driver tests 可绕过 MCP。
- Depth / locality：MCP SDK 版本变化集中在 registry；设备库变化集中在 driver。
- Dependency strategy：in-process，本地可替换。
- Adapter：无额外 adapter；MCP SDK 本身是边界。

### 4.2 Tool Execution → Driver Contract

**方向**：Tool Execution Layer → Driver Contract  
**形式**：Python async method calls

**契约**：

```python
@dataclass(frozen=True)
class DeviceInfo:
    id: str
    name: str
    platform: Literal["android", "ios"]
    type: Literal["real", "emulator", "simulator"]
    version: str
    state: Literal["online", "offline"]

@dataclass(frozen=True)
class ScreenSize:
    width: int
    height: int
    scale: float = 1.0

@dataclass(frozen=True)
class ScreenElementRect:
    x: int
    y: int
    width: int
    height: int

@dataclass(frozen=True)
class ScreenElement:
    type: str
    rect: ScreenElementRect
    label: str | None = None
    text: str | None = None
    name: str | None = None
    value: str | None = None
    identifier: str | None = None
    focused: bool | None = None

@dataclass(frozen=True)
class AppInfo:
    package_name: str
    app_name: str
    version: str | None = None

class BaseDriver(ABC):
    device_id: str
    platform: Literal["android", "ios"]

    async def connect(self, capabilities: dict[str, Any] | None = None) -> None: ...
    async def disconnect(self) -> None: ...
    async def screenshot(self) -> bytes: ...
    async def get_elements_on_screen(self) -> list[ScreenElement]: ...
    async def get_screen_size(self) -> ScreenSize: ...
    async def tap(self, x: int, y: int) -> None: ...
    async def double_tap(self, x: int, y: int) -> None: ...
    async def long_press(self, x: int, y: int, duration_ms: int = 500) -> None: ...
    async def swipe(self, direction: str, x: int | None = None, y: int | None = None, distance: int | None = None) -> None: ...
    async def send_keys(self, text: str, submit: bool = False) -> None: ...
    async def press_button(self, button: str) -> None: ...
    async def open_url(self, url: str) -> None: ...
    async def get_orientation(self) -> Literal["portrait", "landscape"]: ...
    async def set_orientation(self, orientation: Literal["portrait", "landscape"]) -> None: ...
    async def list_apps(self) -> list[AppInfo]: ...
    async def launch_app(self, package_name: str, locale: str | None = None) -> None: ...
    async def terminate_app(self, package_name: str) -> None: ...
    async def install_app(self, path: str) -> None: ...
    async def uninstall_app(self, package_name: str) -> None: ...
    async def start_recording(self, output: str | None = None, time_limit: int | None = None) -> str: ...
    async def stop_recording(self) -> str: ...
    async def list_crashes(self) -> list[dict[str, Any]]: ...
    async def get_crash(self, crash_id: str) -> str: ...
```

**约束**：

- 所有 driver 方法都是 async；阻塞库调用必须用 `asyncio.to_thread()` 或 executor 包裹。
- driver 抛 `UnsupportedPlatformError` / `NotImplementedToolError` / `DeviceNotFoundError` / `DriverError`，工具层统一转结构化错误。
- `get_elements_on_screen()` 可在 driver 内部读取 Android UIAutomator XML / iOS WDA source 并过滤；raw XML/JSON 不作为 MCP 公开契约。

**Interface 设计检查**：

- Module / interface：driver contract 暴露移动设备能力，不暴露 MCP。
- Seam placement：seam 放在 tool execution 和具体平台库之间；unit tests 可用 fake driver，live smoke 穿真实 driver。
- Depth / locality：uiautomator2 / pymobiledevice3 API 差异藏在 driver 内。
- Dependency strategy：in-process，local-substitutable fake driver；真实设备是 true external。
- Adapter：AndroidDriver 和 IOSDriver 是真实 adapters；不要再加单实现 adapter。

### 4.3 Device Discovery / Driver Factory

**方向**：Tool Execution Layer → DriverFactory → Android/iOS Driver  
**形式**：函数调用 + 进程内缓存

**契约**：

```python
class DeviceManager(Protocol):
    async def list_devices(self) -> list[DeviceInfo]: ...

class DriverFactory:
    async def list_devices(self) -> list[DeviceInfo]: ...
    async def get_driver(self, device_id: str) -> BaseDriver: ...
    async def close_driver(self, device_id: str) -> None: ...
```

**约束**：

- `mobile_list_available_devices` 返回 JSON text：`{"devices": [DeviceInfo...]}`，字段名对齐 mobile-mcp 源码。
- `get_driver()` 找不到设备时抛 `DeviceNotFoundError`，错误 message 指向 `mobile_list_available_devices`。
- 首轮允许按 device_id 懒加载/缓存 driver；只有 recording 这类跨调用状态需要显式 session 状态。

**Interface 设计检查**：

- Module / interface：工具层只传 device id；platform 由 discovery/factory 决定。
- Seam placement：factory 是 platform selection seam。
- Depth / locality：新增平台只影响 discovery/factory/driver。
- Dependency strategy：in-process，Android/iOS managers 可 fake。
- Adapter：真实需要，因为 Android/iOS discovery 来源不同。

### 4.4 公开工具契约

**方向**：MCP client → MCP Server  
**形式**：MCP tool schema + content response

**核心 mobile-mcp 工具集合**：

| Tool | 核心输入 | 首轮状态 |
|---|---|---|
| `mobile_list_available_devices` | none | Android MVP 实现；iOS 后续补齐 |
| `mobile_list_apps` | `device` | Android app/system 条目实现 |
| `mobile_launch_app` | `device`, `packageName`, `locale?` | Android app/system 条目实现 |
| `mobile_terminate_app` | `device`, `packageName` | Android app/system 条目实现 |
| `mobile_install_app` | `device`, `path` | Android app/system 条目实现 |
| `mobile_uninstall_app` | `device`, `bundle_id` | Android app/system 条目实现 |
| `mobile_get_screen_size` | `device` | Android MVP 实现 |
| `mobile_click_on_screen_at_coordinates` | `device`, `x`, `y` | Android MVP 实现 |
| `mobile_double_tap_on_screen` | `device`, `x`, `y` | Android MVP 实现 |
| `mobile_long_press_on_screen_at_coordinates` | `device`, `x`, `y`, `duration?` | Android MVP 实现 |
| `mobile_list_elements_on_screen` | `device` | Android MVP 实现 |
| `mobile_press_button` | `device`, `button` | Android app/system 条目实现 |
| `mobile_open_url` | `device`, `url` | Android app/system 条目实现 |
| `mobile_swipe_on_screen` | `device`, `direction`, `x?`, `y?`, `distance?` | Android MVP 实现 |
| `mobile_type_keys` | `device`, `text`, `submit` | Android MVP 实现 |
| `mobile_save_screenshot` | `device`, `saveTo` | Android app/system 条目实现 |
| `mobile_take_screenshot` | `device` | Android MVP 实现，返回 image content |
| `mobile_set_orientation` | `device`, `orientation` | Android app/system 条目实现 |
| `mobile_get_orientation` | `device` | Android app/system 条目实现 |
| `mobile_start_screen_recording` | `device`, `output?`, `timeLimit?` | recording/crash 条目实现 |
| `mobile_stop_screen_recording` | `device` | recording/crash 条目实现 |
| `mobile_list_crashes` | `device` | recording/crash 条目实现或 unsupported |
| `mobile_get_crash` | `device`, `id` | recording/crash 条目实现或 unsupported |

**Source tree 约束**：raw XML/JSON 仅作为 `mobile_list_elements_on_screen` 的内部实现输入；本项目不公开 `mobile_get_page_source`，以保持和 mobile-mcp 工具集完全一致。

**稳定结构化错误文本**：

```json
{
  "status": "error",
  "code": "not_implemented | unsupported_platform | device_not_found | invalid_argument | driver_error",
  "tool": "mobile_tool_name",
  "message": "human readable message",
  "details": {}
}
```

**约束**：

- 工具名和输入字段优先对齐 `/Users/byte/workspace/forks/mobile-mcp/src/server.ts` 的真实源码，不只按 kickoff 猜。
- `mobile_open_url` 默认只允许 `http://` 和 `https://`；若支持自定义 scheme，沿用 `MOBILEMCP_ALLOW_UNSAFE_URLS=1` 语义。
- `mobile_take_screenshot` 返回 MCP image content；`mobile_save_screenshot` 校验输出扩展名 `.png/.jpg/.jpeg`。
- 所有 host output path（截图、录屏等）默认限制在 cwd / temp 下；需要放宽时另行设计。
- `mobile_type_keys.submit=true` 后必须额外触发 Enter。

### 4.5 共享状态

```python
@dataclass
class ActiveRecording:
    device_id: str
    output_path: str
    started_at: datetime
    backend_handle: Any

active_recordings: dict[str, ActiveRecording]
```

**约束**：

- 每台设备同一时间只允许一个 active recording。
- stop 后必须删除状态；进程异常退出不保证恢复历史 recording。
- 其他工具首轮不需要持久 session 数据，避免过早做状态管理框架。

## 5. 子 feature 清单

1. **contract-registry-scaffold** — 建立 Python 包骨架、MCP stdio server、23 个 mobile-mcp 常驻核心工具的 registry、手写 schema parity fixture 和统一结构化错误；所有工具可被 `list_tools` 看到，未实现时稳定失败。
   - 所属模块：MCP Server / Tool Registry、Tool Execution Layer、Driver Contract
   - 依赖：无
   - 状态：done
   - 对应 feature：2026-07-07-contract-registry-scaffold
   - 备注：不要求真实设备成功；重点是外部契约不再漂移，字段名/必填项/annotations 先被 contract test 固定。

2. **android-live-ui-slice** — 用已连接 Android 真机跑通 `list_devices → screen_size → screenshot → elements → tap/swipe/type`，形成首个真实闭环，并留下最小 smoke 命令/README 当前状态。
   - 所属模块：Android Driver、Tool Execution Layer、Verification / Docs
   - 依赖：`contract-registry-scaffold`
   - 状态：done
   - 对应 feature：2026-07-07-android-live-ui-slice
   - 备注：本条是最小闭环；需要 live smoke 证据。

3. **android-app-system-tools** — 补齐 Android app lifecycle、orientation、button、open_url、save_screenshot 等非 recording 系统工具。
   - 所属模块：Android Driver、Tool Execution Layer
   - 依赖：`android-live-ui-slice`
   - 状态：done
   - 对应 feature：2026-07-07-android-app-system-tools
   - 备注：优先复用 AndroidDriver，不新增工具层分支。

4. **android-recording-crash-tools** — 实现或明确降级 Android screen recording 与 crash report 工具，并保证 unsupported 场景可解释。
   - 所属模块：Android Driver、Tool Execution Layer、Verification / Docs
   - 依赖：`android-live-ui-slice`
   - 状态：done
   - 对应 feature：2026-07-07-android-recording-crash-tools
   - 备注：crash report 的真实来源需在 feature-design 做最小验证；拿不到可靠来源就返回 `unsupported_platform` 并记录。

5. **ios-pmd3-wda-core** — 用 `pymobiledevice3` tunnel + WDA 打通 iOS device discovery、screenshot、elements/source、tap/swipe/type、screen size/orientation。
   - 所属模块：iOS Driver、Driver Contract、Tool Execution Layer
   - 依赖：`contract-registry-scaffold`
   - 状态：done
   - 对应 feature：2026-07-07-ios-pmd3-wda-core
   - 备注：这是最高风险条目；需要先用最小 live/spike 证明 WDA client 调用路径。

6. **ios-app-recording-crash-parity** — 在 iOS core driver 基础上补 app lifecycle、recording/crash 能力或稳定 unsupported 行为。
   - 所属模块：iOS Driver、Tool Execution Layer
   - 依赖：`ios-pmd3-wda-core`
   - 状态：done
   - 对应 feature：2026-07-07-ios-app-recording-crash-parity
   - 备注：不引入 go-ios；如果 `pymobiledevice3` 无直接能力，必须显式记录降级。

7. **parity-hardening-docs** — 收口契约测试、live smoke 文档、README 能力状态表、安装/调试说明和已知限制。
   - 所属模块：Verification / Docs、MCP Server / Tool Registry
   - 依赖：`android-app-system-tools`, `android-recording-crash-tools`, `ios-app-recording-crash-parity`
   - 状态：done
   - 对应 feature：2026-07-07-parity-hardening-docs
   - 备注：验收时对照 mobile-mcp 源码工具 schema 和实际实现生成最终能力矩阵。

**最小闭环**：第 2 条 `android-live-ui-slice` 做完后，可以在用户已连接 Android 真机上通过 MCP 工具完成 `list_devices → screen_size → screenshot → elements → tap/swipe/type`，这是本 roadmap 的第一条可演示端到端路径。

### Goal Coverage Matrix

| Goal / completion signal | Covered by item(s) | Verification entry | Evidence type | Roadmap critical? |
|---|---|---|---|---|
| MCP server 启动后能列出 mobile-mcp 源码中的 23 个常驻核心工具，schema parity fixture 通过，未实现工具稳定结构化失败 | `contract-registry-scaffold` | MCP protocol smoke / `list_tools` / schema fixture / 未实现工具调用 | command output / test | yes |
| Android 真机能完成 `list_devices → screen_size → screenshot → elements → tap/swipe/type`，并留下可复跑 smoke 说明 | `android-live-ui-slice` | live Android smoke，使用已连接真机 | screenshot / command output / README diff / acceptance report | yes |
| Android app/system 工具可用或明确 unsupported | `android-app-system-tools` | Android live smoke + unit tests | command output / test | yes |
| Android recording/crash 工具有可验证实现或稳定降级 | `android-recording-crash-tools` | Android live smoke / unsupported 调用 | command output / test | follow-up |
| iOS core UI 自动化通过 `pymobiledevice3 + WDA` 跑通或给出明确阻塞 | `ios-pmd3-wda-core` | iOS live smoke / spike evidence | command output / acceptance report | yes |
| iOS app/recording/crash parity 完成或稳定降级 | `ios-app-recording-crash-parity` | iOS live smoke / unsupported 调用 | command output / test | follow-up |
| README 说明工具状态、安装方式、live smoke 和限制 | `parity-hardening-docs` | 文档 diff + smoke 命令复核 | diff review / acceptance report | yes |

## 6. 排期思路

先做 `contract-registry-scaffold`，因为工具名、schema 和错误 envelope 是所有后续 feature 的共同约束；再做 `android-live-ui-slice`，用真实设备尽早打穿最窄路径，避免 iOS/WDA 和 recording/crash 风险拖慢第一个可用闭环。Android 周边能力和 iOS 可以在契约稳定后并行设计，但实现上先让 Android MVP 通过，后续再扩大设备矩阵。

### 目标完成信号

- 核心工具 registry 和 schema 可由 MCP client 列出。
- Android 真机 live smoke 能完成已确认的最小闭环。
- Android 与 iOS 的 driver contract 一致；同名工具不会因为平台不同改变入参字段。
- 未实现/不支持能力返回结构化错误，README 能解释当前状态。

### Top 3 风险与缓解

1. **iOS WDA / tunnel API 与 kickoff 伪代码不完全一致**：把 iOS core 单独成条，feature-design 前做最小 spike；失败时不阻塞 Android MVP。
2. **对外契约被 Kickoff bonus 条目带偏**：以源码 `server.ts` 的 23 个常驻核心工具为唯一兼容基准，不公开 `mobile_get_page_source`。
3. **真实设备 live smoke 不稳定**：每条 live feature 必须留下最小可复跑命令/步骤；没有设备时测试可 skip，但 acceptance 不能把 skip 当通过。

### 非显然依赖

- Android 本地需有可用 ADB/uiautomator2 环境和已授权设备。
- iOS 需要可配对设备、可用 WDA、pymobiledevice3 tunnel 权限与签名环境。
- MCP SDK 版本会影响 server/list_tools/call_tool API，contract scaffold 要锁定实际用法。

### 关键假设

- 用户接受 Android-first，不要求首个可交付同时覆盖 iOS。
- 成功输出可尽量贴 mobile-mcp 文本语义，但稳定结构化错误优先于完全复刻 mobile-mcp 的异常文本。
- `mobile_list_elements_on_screen` 是对外元素定位入口；raw source 只在 driver 内部使用。

### 基线与验证入口

- 基础 Python 验证：`python -m pytest`。
- YAML/CodeStable 验证：`python3 .codestable/tools/validate-yaml.py --file .codestable/roadmap/pymobile-mcp-android-mvp/pymobile-mcp-android-mvp-items.yaml --yaml-only`。
- MCP 协议验证：后续 feature 提供最小 client 或 pytest smoke，至少覆盖 `list_tools`、schema parity fixture 和一个 `call_tool`。
- Android live 验证：使用用户已连接真机，按 `mobile_list_available_devices` 返回的 id 执行 screen_size/screenshot/elements/tap/swipe/type；每条 live feature acceptance 必须留下可复跑步骤。
- iOS live 验证：到 `ios-pmd3-wda-core` 时再要求真实设备或明确记录环境缺口。

### 交付物落点

- 源码：`src/pymobile_mcp/server.py`、`src/pymobile_mcp/tools/`、`src/pymobile_mcp/drivers/`。
- 测试：`tests/` 下 unit/contract/live smoke；live smoke 必须可 skip 但不能伪装通过。
- 文档：`android-live-ui-slice` 先补最小 Android MVP 状态/复跑说明；`parity-hardening-docs` 最终补全 README 能力矩阵、安装和调试说明。
- CodeStable：每条 feature acceptance 回写本 roadmap item 状态。

### 知识回写点

- Android 真机调试命令、ADB/uiautomator2 坑点：验证后用 `cs-note` 或 `cs-keep` 沉淀。
- iOS tunnel/WDA 可行路径：如果成功，acceptance 后建议走 `cs-domain` 记录 ADR；如果失败，至少写 compound learning。
- 工具契约对齐经验（mobile-mcp 源码字段、返回语义、与 Python 实现差异）：parity hardening 时写入 README 和可能的 compound 记录。

## 7. 观察项

- Kickoff 曾提到 bonus `mobile_get_page_source`，但 owner 已确认目标是 strict mobile-mcp parity；因此不公开该工具，raw source 只作为元素过滤的内部实现细节。
- `pyproject.toml` 已包含 `pymobiledevice3`（GPL-3.0）并声明项目 GPL-3.0；后续 README 需要保持许可证说明清楚。
- `ocr` 已安装但未配置 LLM；后续 `cs-code-review` 行级增强会降级，不阻塞本 roadmap。

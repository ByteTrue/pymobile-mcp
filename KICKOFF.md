# pymobile-mcp: New Session Kickoff Prompt

Copy the entire content below into a new session.

---

## Task

Implement **pymobile-mcp** — a pure-Python MCP server for mobile device automation, feature-complete aligned with [mobile-next/mobile-mcp](https://github.com/mobile-next/mobile-mcp).

## Tech Stack

| Layer | Library | License |
|---|---|---|
| Android driver | `uiautomator2` (codeskyblue) | MIT |
| iOS device management | `pymobiledevice3` (doronz88) | GPL-3.0 |
| iOS WDA communication | `pymobiledevice3.services.wda.WdaServiceClient` (built-in) | GPL-3.0 |
| MCP protocol | `mcp` (official SDK) | MIT |
| Config | `pyyaml` | MIT |
| Logging | `structlog` | MIT/Apache |
| CLI | `click` | BSD |

## Core Architecture (3-layer)

```
┌─────────────────────────┐
│  server.py              │  MCP Server: tool registration, handler dispatch
├─────────────────────────┤
│  tools/                 │  Tool classes: each MCP tool = one class
│  ├── device_tools.py    │    list_devices, connect, disconnect, info
│  ├── ui_tools.py        │    find_element, click, tap, swipe, screenshot, source
│  ├── app_tools.py       │    list_apps, launch, terminate, install, uninstall
│  ├── system_tools.py    │    press_button, open_url, orientation, recording, crashes
├─────────────────────────┤
│  drivers/               │  Platform abstraction
│  ├── base.py            │    BaseDriver ABC + Element dataclass + exceptions
│  ├── android_driver.py  │    U2AndroidDriver (uiautomator2)
│  ├── ios_driver.py      │    PMD3IOSDriver (pymobiledevice3)
│  └── factory.py         │    DriverFactory.create(platform, device_id)
└─────────────────────────┘
```

## Complete Tool List (23 tools, align with mobile-mcp)

### Device Management (8)
1. `mobile_list_available_devices` — list all Android + iOS devices
2. `mobile_list_apps` — list installed apps
3. `mobile_launch_app` — launch app by package/bundle ID
4. `mobile_terminate_app` — kill app
5. `mobile_install_app` — install .apk/.ipa
6. `mobile_uninstall_app` — uninstall by package/bundle ID
7. `mobile_get_screen_size` — width, height in pixels
8. `mobile_set_orientation` / `mobile_get_orientation` — portrait/landscape

### UI Interaction (10)
9. `mobile_list_elements_on_screen` — accessibility tree as structured list (like mobile-mcp's output)
10. `mobile_click_on_screen_at_coordinates` — tap x,y
11. `mobile_double_tap_on_screen` — double-tap x,y
12. `mobile_long_press_on_screen_at_coordinates` — long press x,y with duration
13. `mobile_swipe_on_screen` — swipe direction or from-to coordinates
14. `mobile_type_keys` — type text into focused element
15. `mobile_press_button` — HOME, BACK, VOLUME_UP, VOLUME_DOWN
16. `mobile_open_url` — open URL in device browser
17. `mobile_take_screenshot` — return base64 PNG
18. `mobile_save_screenshot` — save PNG to file path

### Recording & Crash (5)
19. `mobile_start_screen_recording` — start recording, return immediately
20. `mobile_stop_screen_recording` — stop, save MP4, return path
21. `mobile_list_crashes` — list crash reports on device
22. `mobile_get_crash` — get crash report content by ID

### (bonus)
23. `mobile_get_page_source` — raw XML/JSON page source (when structured list isn't enough)

## BaseDriver ABC — Required Methods

Every method is async. Android and iOS drivers each implement:

```
connect(capabilities) -> None
disconnect() -> None
screenshot() -> bytes (PNG)
get_page_source() -> str (XML)
get_elements_on_screen() -> list[ScreenElement]
get_screen_size() -> ScreenSize
tap(x, y) -> None
double_tap(x, y) -> None
long_press(x, y, duration_ms) -> None
swipe(start_x, start_y, end_x, end_y, duration_ms) -> None
send_keys(text) -> None
press_button(button: str) -> None  # HOME/BACK/VOLUME_UP/VOLUME_DOWN
open_url(url) -> None
get_orientation() -> str  # portrait/landscape
set_orientation(orientation) -> None
list_apps() -> list[AppInfo]
launch_app(package, locale?) -> None
terminate_app(package) -> None
install_app(path) -> None
uninstall_app(package) -> None
start_recording(file_path) -> None
stop_recording() -> str  # returns file path
list_crashes() -> list[CrashInfo]
get_crash(crash_id) -> str
```

## iOS Implementation Notes

iOS uses `pymobiledevice3` for the full lifecycle:

```python
from pymobiledevice3.remote.userspace_tunnel import UserspaceRsdTunnel
from pymobiledevice3.services.wda import WdaServiceClient
from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
from pymobiledevice3.services.dvt.instruments.process_control import ProcessControl

class PMD3IOSDriver(BaseDriver):
    async def connect(self, capabilities):
        # 1. Establish no-root tunnel (UserspaceRsdTunnel)
        # 2. Launch WDA via DVT ProcessControl (or assume pre-installed)
        # 3. Create WdaServiceClient through the tunnel
        # 4. Start WDA session for target bundle_id
        self._tunnel = UserspaceRsdTunnel(serial=self.device_id, autopair=True)
        await self._tunnel.aopen()
        self._rsd = self._tunnel  # RemoteServiceDiscoveryService
        self._wda = WdaServiceClient(self._rsd)
        if bundle_id := capabilities.get("bundleId"):
            await self._wda.start_session(bundle_id)
    
    async def tap(self, x, y):
        # Use WdaServiceClient or direct WDA HTTP
        ...
```

Key advantages over go-ios:
- **No port forwarding needed**: WdaServiceClient routes through the tunnel directly
- **No separate tunnel process**: UserspaceRsdTunnel is in-process, no root needed
- **One Python process**: tunnel + WDA + MCP server all in one

## Android Implementation Notes

Android uses `uiautomator2` directly:

```python
import uiautomator2 as u2

class U2AndroidDriver(BaseDriver):
    async def connect(self, capabilities):
        self._device = u2.connect(self.device_id)
        if pkg := capabilities.get("appPackage"):
            self._device.app_start(pkg, capabilities.get("appActivity"))
    
    async def tap(self, x, y):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._device.click, x, y)
```

All u2 calls are blocking, so wrap in `loop.run_in_executor(None, ...)`.

## Device Discovery

- **Android**: `adb devices` (via `adbutils` or subprocess)
- **iOS**: `pymobiledevice3 usbmux list` (lockdown), and for iOS 17+ `UserspaceRsdTunnel` to discover tunnel-available devices
- Unified return format: `{"id": str, "name": str, "platform": "android"|"ios", "type": "real"|"emulator"|"simulator", "version": str, "state": "online"|"offline"}`

## Project Structure

```
pymobile-mcp/
├── src/pymobile_mcp/
│   ├── __init__.py
│   ├── server.py           # MCP server, tool registration, handler dispatch
│   ├── cli.py              # click CLI: pymobile-mcp run
│   ├── config.py           # YAML config loader
│   ├── drivers/
│   │   ├── __init__.py
│   │   ├── base.py         # BaseDriver ABC, Element, ScreenElement, exceptions
│   │   ├── android.py      # U2AndroidDriver
│   │   ├── ios.py          # PMD3IOSDriver
│   │   └── factory.py      # DriverFactory
│   └── tools/
│       ├── __init__.py
│       ├── base.py         # BaseTool ABC
│       ├── device.py       # list/connect/disconnect/info tools
│       ├── ui.py           # element/click/tap/swipe/screenshot tools
│       ├── app.py          # app management tools
│       └── system.py       # button/orientation/recording/crash tools
├── tests/
├── pyproject.toml
├── README.md
└── LICENSE (GPL-3.0)
```

## MCP Server Setup

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

class PyMobileMCPServer:
    def __init__(self):
        self.mcp = Server("pymobile-mcp")
        self._register_tools()
    
    def _register_tools(self):
        @self.mcp.list_tools()
        async def list_tools():
            return [tool.to_mcp_tool() for tool in self.tools]
        
        @self.mcp.call_tool()
        async def call_tool(name, arguments):
            tool = self._find_tool(name)
            result = await tool.execute(arguments)
            return [types.TextContent(type="text", text=json.dumps(result))]
    
    async def run(self):
        async with stdio_server() as (read, write):
            await self.mcp.run(read, write, self.mcp.create_initialization_options())
```

## Tool Base Class Pattern

```python
class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @property
    @abstractmethod
    def description(self) -> str: ...
    
    @property
    @abstractmethod
    def parameters(self) -> dict: ...  # JSON Schema
    
    @abstractmethod
    async def execute(self, arguments: dict) -> dict: ...
    
    def to_mcp_tool(self) -> types.Tool:
        return types.Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.parameters,
        )
```

## Session Management

- One active session per device (identified by device_id)
- Session = device connection state + optional app session
- Thread-safe with `asyncio.Lock` per session
- Auto-cleanup on disconnect

## Priorities (implementation order)

1. **Project scaffold**: pyproject.toml, cli.py, config.py, base classes
2. **Android driver**: U2AndroidDriver with full ABC implementation
3. **iOS driver**: PMD3IOSDriver with tunnel + WDA + full ABC
4. **Device tools**: list/connect/disconnect/info
5. **UI tools**: elements/screenshot/click/tap/swipe/type
6. **App tools**: list/launch/terminate/install/uninstall
7. **System tools**: button/orientation/recording/crashes
8. **Server integration**: wire everything into MCP server
9. **Tests**: at minimum smoke tests for each driver

## References

- mobile-mcp source: `/Users/byte/workspace/forks/mobile-mcp/src/`
- pymobiledevice3 docs: https://doronz88.github.io/pymobiledevice3/
- uiautomator2 docs: https://github.com/openatx/uiautomator2

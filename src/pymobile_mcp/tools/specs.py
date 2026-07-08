"""mobile-mcp core tool manifest."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


Schema = dict[str, Any]


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    title: str
    description: str
    input_schema: Schema = field(default_factory=dict)
    annotations: dict[str, Any] = field(default_factory=dict)
    content_kind: Literal["text", "image"] = "text"

    def to_mcp_tool(self) -> Any:
        from mcp.types import Tool

        return Tool(
            name=self.name,
            title=self.title,
            description=self.description,
            inputSchema=self.input_schema,
            annotations=self.annotations or None,
        )


def _string(description: str) -> Schema:
    return {"type": "string", "description": description}


def _number(description: str) -> Schema:
    return {"type": "number", "description": description}


def _boolean(description: str) -> Schema:
    return {"type": "boolean", "description": description}


def _enum(values: list[str], description: str) -> Schema:
    return {"type": "string", "enum": values, "description": description}


def _object(properties: dict[str, Schema], required: list[str]) -> Schema:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


DEVICE = _string("The device identifier to use. Use mobile_list_available_devices to find which devices are available to you.")
COORDINATE_TOOLS = {
    "device": DEVICE,
    "x": _number("The x coordinate on the screen, in pixels"),
    "y": _number("The y coordinate on the screen, in pixels"),
}


CORE_TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec(
        "mobile_list_available_devices",
        "List Devices",
        "List all available devices. This includes both physical mobile devices and mobile simulators and emulators. It returns both Android and iOS devices.",
        _object({}, []),
        {"readOnlyHint": True},
    ),
    ToolSpec(
        "mobile_list_apps",
        "List Apps",
        "List all the installed apps on the device",
        _object({"device": DEVICE}, ["device"]),
        {"readOnlyHint": True},
    ),
    ToolSpec(
        "mobile_launch_app",
        "Launch App",
        "Launch an app on mobile device. Use this to open a specific app. You can find the package name of the app by calling list_apps_on_device.",
        _object(
            {
                "device": DEVICE,
                "packageName": _string("The package name of the app to launch"),
                "locale": _string("Comma-separated BCP 47 locale tags to launch the app with (e.g., fr-FR,en-GB)"),
            },
            ["device", "packageName"],
        ),
        {"destructiveHint": True},
    ),
    ToolSpec(
        "mobile_terminate_app",
        "Terminate App",
        "Stop and terminate an app on mobile device",
        _object({"device": DEVICE, "packageName": _string("The package name of the app to terminate")}, ["device", "packageName"]),
        {"destructiveHint": True},
    ),
    ToolSpec(
        "mobile_install_app",
        "Install App",
        "Install an app on mobile device",
        _object(
            {
                "device": DEVICE,
                "path": _string("The path to the app file to install. For iOS simulators, provide a .zip file or a .app directory. For Android provide an .apk file. For iOS real devices provide an .ipa file"),
            },
            ["device", "path"],
        ),
        {"destructiveHint": True},
    ),
    ToolSpec(
        "mobile_uninstall_app",
        "Uninstall App",
        "Uninstall an app from mobile device",
        _object(
            {
                "device": DEVICE,
                "bundle_id": _string("Bundle identifier (iOS) or package name (Android) of the app to be uninstalled"),
            },
            ["device", "bundle_id"],
        ),
        {"destructiveHint": True},
    ),
    ToolSpec(
        "mobile_get_screen_size",
        "Get Screen Size",
        "Get the screen size of the mobile device in pixels",
        _object({"device": DEVICE}, ["device"]),
        {"readOnlyHint": True},
    ),
    ToolSpec(
        "mobile_click_on_screen_at_coordinates",
        "Click Screen",
        "Click on the screen at given x,y coordinates. If clicking on an element, use the list_elements_on_screen tool to find the coordinates.",
        _object(COORDINATE_TOOLS, ["device", "x", "y"]),
        {"destructiveHint": True},
    ),
    ToolSpec(
        "mobile_double_tap_on_screen",
        "Double Tap Screen",
        "Double-tap on the screen at given x,y coordinates.",
        _object(COORDINATE_TOOLS, ["device", "x", "y"]),
        {"destructiveHint": True},
    ),
    ToolSpec(
        "mobile_long_press_on_screen_at_coordinates",
        "Long Press Screen",
        "Long press on the screen at given x,y coordinates. If long pressing on an element, use the list_elements_on_screen tool to find the coordinates.",
        _object({**COORDINATE_TOOLS, "duration": _number("Duration of the long press in milliseconds. Defaults to 500ms.")}, ["device", "x", "y"]),
        {"destructiveHint": True},
    ),
    ToolSpec(
        "mobile_list_elements_on_screen",
        "List Screen Elements",
        "List elements on screen and their coordinates, with display text or accessibility label. Do not cache this result.",
        _object({"device": DEVICE}, ["device"]),
        {"readOnlyHint": True},
    ),
    ToolSpec(
        "mobile_press_button",
        "Press Button",
        "Press a button on device",
        _object(
            {
                "device": DEVICE,
                "button": _string("The button to press. Supported buttons: BACK (android only), HOME, VOLUME_UP, VOLUME_DOWN, ENTER, DPAD_CENTER (android tv only), DPAD_UP (android tv only), DPAD_DOWN (android tv only), DPAD_LEFT (android tv only), DPAD_RIGHT (android tv only)"),
            },
            ["device", "button"],
        ),
        {"destructiveHint": True},
    ),
    ToolSpec(
        "mobile_open_url",
        "Open URL",
        "Open a URL in browser on device",
        _object({"device": DEVICE, "url": _string("The URL to open")}, ["device", "url"]),
        {"destructiveHint": True},
    ),
    ToolSpec(
        "mobile_swipe_on_screen",
        "Swipe Screen",
        "Swipe on the screen",
        _object(
            {
                "device": DEVICE,
                "direction": _enum(["up", "down", "left", "right"], "The direction to swipe"),
                "x": _number("The x coordinate to start the swipe from, in pixels. If not provided, uses center of screen"),
                "y": _number("The y coordinate to start the swipe from, in pixels. If not provided, uses center of screen"),
                "distance": _number("The distance to swipe in pixels. Defaults to 400 pixels for iOS or 30% of screen dimension for Android"),
            },
            ["device", "direction"],
        ),
        {"destructiveHint": True},
    ),
    ToolSpec(
        "mobile_type_keys",
        "Type Text",
        "Type text into the focused element",
        _object(
            {
                "device": DEVICE,
                "text": _string("The text to type"),
                "submit": _boolean("Whether to submit the text. If true, the text will be submitted as if the user pressed the enter key."),
            },
            ["device", "text", "submit"],
        ),
        {"destructiveHint": True},
    ),
    ToolSpec(
        "mobile_save_screenshot",
        "Save Screenshot",
        "Save a screenshot of the mobile device to a file",
        _object(
            {
                "device": DEVICE,
                "saveTo": _string("The path to save the screenshot to. Filename must end with .png, .jpg, or .jpeg"),
            },
            ["device", "saveTo"],
        ),
        {"destructiveHint": True},
    ),
    ToolSpec(
        "mobile_take_screenshot",
        "Take Screenshot",
        "Take a screenshot of the mobile device. Use this to understand what's on screen, if you need to press an element that is available through view hierarchy then you must list elements on screen instead. Do not cache this result.",
        _object({"device": DEVICE}, ["device"]),
        {"readOnlyHint": True},
        "image",
    ),
    ToolSpec(
        "mobile_set_orientation",
        "Set Orientation",
        "Change the screen orientation of the device",
        _object({"device": DEVICE, "orientation": _enum(["portrait", "landscape"], "The desired orientation")}, ["device", "orientation"]),
        {"destructiveHint": True},
    ),
    ToolSpec(
        "mobile_get_orientation",
        "Get Orientation",
        "Get the current screen orientation of the device",
        _object({"device": DEVICE}, ["device"]),
        {"readOnlyHint": True},
    ),
    ToolSpec(
        "mobile_start_screen_recording",
        "Start Screen Recording",
        "Start recording the screen of a mobile device. The recording runs in the background until stopped with mobile_stop_screen_recording. Returns the path where the recording will be saved.",
        _object(
            {
                "device": DEVICE,
                "output": _string("The file path to save the recording to. Filename must end with .mp4. If not provided, a temporary path will be used."),
                "timeLimit": _number("Maximum recording duration in seconds. The recording will stop automatically after this time."),
            },
            ["device"],
        ),
        {"destructiveHint": True},
    ),
    ToolSpec(
        "mobile_stop_screen_recording",
        "Stop Screen Recording",
        "Stop an active screen recording on a mobile device. Returns the file path, size, and approximate duration of the recording.",
        _object({"device": DEVICE}, ["device"]),
        {"destructiveHint": True},
    ),
    ToolSpec(
        "mobile_list_crashes",
        "List Crash Reports",
        "List crash reports available on the device",
        _object({"device": DEVICE}, ["device"]),
        {"readOnlyHint": True},
    ),
    ToolSpec(
        "mobile_get_crash",
        "Get Crash Report",
        "Get the full content of a crash report by its ID. Use mobile_list_crashes to find available crash IDs.",
        _object({"device": DEVICE, "id": _string("The crash report ID to retrieve")}, ["device", "id"]),
        {"readOnlyHint": True},
    ),
)

CORE_TOOL_NAMES = tuple(spec.name for spec in CORE_TOOL_SPECS)

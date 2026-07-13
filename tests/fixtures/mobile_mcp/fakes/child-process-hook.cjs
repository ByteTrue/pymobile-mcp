const child = require("node:child_process");
const fs = require("node:fs");
const { EventEmitter } = require("node:events");
const path = require("node:path");
const Module = require("node:module");

const originalExecFileSync = child.execFileSync;
const originalSpawnSync = child.spawnSync;
const originalExistsSync = fs.existsSync;
const originalStatSync = fs.statSync;
const scenario = process.env.PYMOBILE_SCENARIO_ID || "";
const fixtureRoot = process.env.PYMOBILE_FIXTURE_ROOT || path.resolve("tests/fixtures/mobile_mcp");
const png = () => fs.readFileSync(path.join(fixtureRoot, "input-1080x2400.png"));
const buffer = value => Buffer.isBuffer(value) ? value : Buffer.from(value);
const commandName = command => path.basename(String(command));
const isIos = () => scenario.includes("IOS") && !scenario.includes("SIMULATOR");
const isSim = () => scenario.includes("SIMULATOR");

const originalLoad = Module._load;
Module._load = function(request, parent, isMain) {
  const loaded = originalLoad.apply(this, arguments);
  if (request === "./android" && loaded.AndroidRobot) {
    if (scenario.startsWith("S-TAKE-JPEG")) loaded.AndroidRobot.prototype.getScreenSize = async () => ({ width: 1080, height: 2400, scale: 3 });
    if (scenario === "S-ELEMENTS-TWO") loaded.AndroidRobot.prototype.getElementsOnScreen = async () => ([
      { type: "Button", text: "OK", label: null, name: null, value: "OK", identifier: "ok", rect: { x: 1, y: 2, width: 3, height: 4 }, focused: false },
      { type: "TextField", text: null, label: "Search", name: "search", value: "", identifier: "search", rect: { x: 5, y: 6, width: 7, height: 8 }, focused: true },
    ]);
    if (scenario === "S-LIST-DEVICES-NONEMPTY" && loaded.AndroidDeviceManager) {
      loaded.AndroidDeviceManager.prototype.getConnectedDevicesWithDetails = () => ([{ deviceId: "emulator-5554", name: "Pixel", version: "16", deviceType: "mobile" }]);
    }
  }
  if (request === "./ios" && scenario === "S-LIST-DEVICES-NONEMPTY" && loaded.IosManager) {
    loaded.IosManager.prototype.listDevicesWithDetails = () => ([{ deviceId: "ios-1", deviceName: "iPhone", version: "26.5.2" }]);
  }
  return loaded;
};

function adbOutput(args) {
  const joined = args.join(" ");
  if (args[0] === "devices") {
    if (isIos() || isSim() || scenario === "S-LIST-DEVICES-EMPTY") return "List of devices attached\n\n";
    const id = scenario === "S-LIST-DEVICES-ANDROID-PHYSICAL" ? "R5CT123456" : "emulator-5554";
    return `List of devices attached\n${id}\tdevice\n`;
  }
  if (joined.includes("ro.build.version.release")) return "14\n";
  if (joined.includes("ro.boot.qemu.avd_name")) return scenario === "S-LIST-DEVICES-ANDROID-PHYSICAL" ? "" : "Pixel_8\n";
  if (joined.includes("ro.product.model")) return scenario === "S-LIST-DEVICES-ANDROID-PHYSICAL" ? "Galaxy\n" : "Pixel 8\n";
  if (joined.includes("pm list features")) return "feature:android.hardware.touchscreen\n";
  if (joined.includes("wm size")) return "Physical size: 1080x2400\n";
  if (joined.includes("query-activities")) {
    return scenario === "S-LIST-APPS-TWO" ? "packageName=com.example.one\npackageName=com.example.two\n" : "";
  }
  if (joined.includes("uiautomator dump")) {
    if (scenario === "S-ELEMENTS-TWO") {
      return '<?xml version="1.0"?><hierarchy><node class="android.widget.Button" text="OK" content-desc="Confirm" resource-id="id/ok" bounds="[10,20][110,70]"/><node class="android.widget.TextView" text="Hello" bounds="[0,80][200,120]"/></hierarchy>';
    }
    return '<?xml version="1.0"?><hierarchy></hierarchy>';
  }
  if (joined.includes("screencap -p")) return scenario === "E-SCREENSHOT-INVALID" ? Buffer.from("invalid") : png();
  if (joined.includes("user_rotation")) return "0\n";
  if (joined.includes("SurfaceFlinger --display-id")) return "Display 0\n";
  return "";
}

function mobilecliOutput(args) {
  const joined = args.join(" ");
  if (args.includes("--version")) {
    if (scenario === "E-MOBILECLI-UNAVAILABLE") throw new Error("mobilecli version check failed");
    return "mobilecli version 1.0.0\n";
  }
  if (joined === "remote list-devices") return "remote-ios-1\nremote-android-1\n";
  if (joined.startsWith("remote allocate")) return `allocated-${args.at(-1)}\n`;
  if (joined.startsWith("remote release")) return "released-remote-ios-1\n";
  if (args[0] === "devices") {
    if (!isSim()) return JSON.stringify({ status: "ok", data: { devices: [] } });
    return JSON.stringify({ status: "ok", data: { devices: [{ id: "sim-1", name: "iPhone 16", platform: "ios", type: "simulator", version: "18.0" }] } });
  }
  if (joined.startsWith("device info")) return JSON.stringify({ status: "ok", data: { device: { screenSize: { width: 1179, height: 2556, scale: 3 } } } });
  if (joined.startsWith("apps list")) return JSON.stringify({ status: "ok", data: [] });
  if (joined.startsWith("dump ui")) return JSON.stringify({ status: "ok", data: { elements: [] } });
  if (joined.startsWith("device orientation get")) return JSON.stringify({ status: "ok", data: { orientation: "portrait" } });
  if (joined.startsWith("device crashes list")) return JSON.stringify({ status: "ok", data: [{ processName: "Demo", timestamp: "2026-01-01", id: "crash-1" }] });
  if (joined.startsWith("device crashes get")) return JSON.stringify({ status: "ok", data: { id: "crash-1", content: "crash body" } });
  if (args[0] === "screenshot") return png();
  return "";
}

child.execFileSync = function(command, args = [], options = {}) {
  const name = commandName(command);
  if (name === "adb") return buffer(adbOutput(args));
  if (name === "ios") {
    if (args.includes("version")) return buffer(JSON.stringify({ version: "1.0.0" }));
    if (args.includes("list")) return buffer(JSON.stringify({ deviceList: isIos() ? ["ios-1"] : [] }));
    if (args.includes("info")) return buffer(JSON.stringify({ DeviceName: "iPhone", ProductVersion: "18.0" }));
    return buffer("");
  }
  if (name.includes("mobilecli")) return buffer(mobilecliOutput(args));
  if (name === "magick" && args[0] === "--version") {
    if (["no_scaling"].includes(process.env.PYMOBILE_SCALING_MODE)) throw new Error("magick disabled");
  }
  if (name === "sips" && args[0] === "--version") {
    if (["no_scaling", "imagemagick", "scaling_failure"].includes(process.env.PYMOBILE_SCALING_MODE)) throw new Error("sips disabled");
  }
  return originalExecFileSync.apply(this, arguments);
};

child.spawnSync = function(command, args = [], options = {}) {
  const mode = process.env.PYMOBILE_SCALING_MODE;
  const name = commandName(command);
  if (name === "sips" && mode === "sips_fail_magick") return { status: 1, stdout: Buffer.alloc(0), stderr: buffer("forced sips failure") };
  if (name === "magick" && mode === "scaling_failure") throw new Error("forced ImageMagick failure");
  return originalSpawnSync.apply(this, arguments);
};

class FakeChild extends EventEmitter {
  kill(signal) {
    setImmediate(() => {
      this.emit("close", 0, signal);
      this.emit("exit", 0, signal);
    });
    return true;
}
}
child.spawn = function() { return new FakeChild(); };

fs.existsSync = function(target) {
  if (String(target).endsWith("mobile-mcp-contract.mp4") || String(target).endsWith("sim-recording.mp4")) return true;
  return originalExistsSync.apply(this, arguments);
};
fs.statSync = function(target) {
  if (String(target).endsWith(".mp4")) return { size: 1048576 };
  return originalStatSync.apply(this, arguments);
};

if (process.env.PYMOBILE_FIXED_CLOCK === "1") Date.now = () => 1700000000000;

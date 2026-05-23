# IRIS Snapshot

**Session:** S59 | **Date:** 2026-05-23 | **Branch:** `main` | **Last commit:** 08e4330 — S59: Teensy 4.0 gesture sensor fix — APDS-9960 DEPLOYED+VERIFIED

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## Machine Status

| System | Status |
|---|---|
| SuperMaster Desktop | Canonical repo — S59 committed (08e4330), push pending. |
| Pi4 192.168.1.200 | Operational. S58 DEPLOYED+VERIFIED. assistant.py (f98978a5), base_mount_bridge.py (6bfc3801), core/config.py (ebf1561b) — all md5 verified RAM==SD. [BASE] Teensy 4.0 connected on /dev/ttyACM1. [INFO] Ready. |
| GandalfAI 192.168.1.3 | Operational. iris + iris-kids models current (S48 PT-001). |
| Teensy 4.1 | Firmware REPO-ONLY (af66b24). BL_MAP log curve + idle animations built, flash pending. /dev/ttyACM0 confirmed. |
| Teensy 4.0 (base mount) | DEPLOYED+VERIFIED S59. Gesture sensor (APDS-9960) working — VOL+/VOL-/STOP/LISTEN confirmed on desktop USB. Flashed to Pi4 /dev/ttyACM1 15:08. [BASE] connected confirmed. Servo works (clunky/jerky — tuning pending). |
| Servo Controller (ESP32 DevKit 1C) | TOMBSTONED. PCB destroyed. servo_esp32/ directory removed S58. |
| TTS | Kokoro primary (Docker port 8004), Piper fallback (Wyoming port 10200). |

---

## Active Issues

- **HIGH: Teensy 4.0 servo tuning** — Pan servo works but clunky/jerky. Tune PAN_SPEED, PAN_DEAD_ZONE, FACE_HOLD_MS, FACE_RETURN_MS constants in servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino. Flash after tuning.
- **HIGH: HW-001 — Teensy 4.1 LED jumper cut** — Physical mod only, no software needed.
- **HIGH: Teensy 4.1 firmware flash pending** — af66b24 BL_MAP + idle animations. PlatformIO upload, COM7.
- **MED: Perceived latency** — OLLAMA_KEEP_ALIVE=30m on GandalfAI pending.
- **LOW: RD-011 — APDS-9960 LISTEN proximity trigger** — gesture VOL+/VOL-/STOP verified working S59. LISTEN (proximity hold) not yet verified on live Pi — wave hand near sensor for 1s to test.
- **LOW: RD-003 — Duplicate sleep log** — /home/pi/iris_sleep.log vs /home/pi/logs/iris_sleep.log.

---

## Session Scope

S59: APDS-9960 gesture sensor diagnosed and fixed. Root cause: library init() calls Wire.begin() internally — Teensy 4.0 I2C bus needs 25ms settle before first transaction. Also fixed: enableProximitySensor(false) was silently killing gesture detection. Library patched into lib/ for permanence. REBOOT command + Person Sensor LED disable added. Flashed to Pi4 and verified.

---

## Last Session Changes (S59)

- **`servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`** — Added REBOOT command, Person Sensor LED disable, while(!Serial) boot wait, I2C_SCAN_DIAG flag, raw APDS ID read diagnostic. Removed enableProximitySensor(false) bug. DEPLOYED+VERIFIED.
- **`servo_teensy40/teensy40_base_mount/platformio.ini`** — Removed registry APDS9960 dep; uses local lib/ instead.
- **`servo_teensy40/teensy40_base_mount/lib/SparkFun_APDS9960/`** — NEW. Patched SparkFun APDS9960 library: delay(25) after Wire.begin() in init() for Teensy 4.0 I2C settle.
- **`servo_teensy40/i2c_scanner/`** — NEW. Standalone I2C scanner diagnostic sketch.

## Previous Session Changes (S58)

- **`servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`** — Renamed from IRIS-BaseServoControlViaPerson_Sensor.ino. Fixed: panServo.attach(2), Serial.begin(115200), VOL+/VOL- commands, comment block. Build: SUCCESS.
- **`pi4/hardware/base_mount_bridge.py`** — NEW. DEPLOYED+VERIFIED md5 6bfc3801.
- **`pi4/core/config.py`** — Added BASE_MOUNT_ENABLED, BASE_MOUNT_PORT, BASE_MOUNT_BAUD. DEPLOYED+VERIFIED md5 ebf1561b.
- **`pi4/assistant.py`** — Added BaseMountBridge import + startup block. DEPLOYED+VERIFIED md5 f98978a5.

## Previous Session Changes (S57)

- ESP32 DevKit 1C firmware + Pi4 deploy — superseded/tombstoned in S58.

---

## Known TODO

- **NEXT: Servo tuning** — Tune PAN_SPEED/PAN_DEAD_ZONE/FACE_HOLD_MS/FACE_RETURN_MS in teensy40_base_mount.ino, then re-flash
- HW-001: cut LED/SCK solder jumper on Teensy 4.1 underside
- Flash Teensy 4.1 firmware (PlatformIO upload, env:eyes, COM7, user clicks upload)
- GandalfAI: set OLLAMA_KEEP_ALIVE=30m + restart Ollama service
- RD-011: confirm APDS-9960 LISTEN trigger fires on Teensy 4.0; fix enableProximitySensor() if needed

---

## Do Not Touch Without Explicit Instruction

- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

# IRIS Snapshot

**Session:** S58 | **Date:** 2026-05-23 | **Branch:** `main` | **Last commit:** pending push — S58: Teensy 4.0 base mount controller — firmware built, Pi4 deployed, [BASE] + [INFO] Ready verified

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## Machine Status

| System | Status |
|---|---|
| SuperMaster Desktop | Canonical repo — S58 changes committed locally, push pending. |
| Pi4 192.168.1.200 | Operational. S58 DEPLOYED+VERIFIED. assistant.py (f98978a5), base_mount_bridge.py (6bfc3801), core/config.py (ebf1561b) — all md5 verified RAM==SD. [BASE] Teensy 4.0 connected on /dev/ttyACM1. [INFO] Ready. |
| GandalfAI 192.168.1.3 | Operational. iris + iris-kids models current (S48 PT-001). |
| Teensy 4.1 | Firmware REPO-ONLY (af66b24). BL_MAP log curve + idle animations built, flash pending. /dev/ttyACM0 confirmed. |
| Teensy 4.0 (base mount) | DEPLOYED+VERIFIED S58. teensy40_base_mount.ino built (pio run OK). Plugged into Pi4 /dev/ttyACM1. [BASE] connected confirmed in journalctl. Servo works (clunky/jerky — tuning pending). |
| Servo Controller (ESP32 DevKit 1C) | TOMBSTONED. PCB destroyed. servo_esp32/ directory removed S58. |
| TTS | Kokoro primary (Docker port 8004), Piper fallback (Wyoming port 10200). |

---

## Active Issues

- **HIGH: Teensy 4.0 servo tuning** — Pan servo works but clunky/jerky. Tune PAN_SPEED, PAN_DEAD_ZONE, FACE_HOLD_MS, FACE_RETURN_MS constants in servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino. Flash after tuning.
- **HIGH: HW-001 — Teensy 4.1 LED jumper cut** — Physical mod only, no software needed.
- **HIGH: Teensy 4.1 firmware flash pending** — af66b24 BL_MAP + idle animations. PlatformIO upload, COM7.
- **MED: Perceived latency** — OLLAMA_KEEP_ALIVE=30m on GandalfAI pending.
- **LOW: RD-011 — APDS-9960 proximity LISTEN trigger** — verify on Teensy 4.0 bring-up. May be silently broken (enableProximitySensor(false) but readProximity() called).
- **LOW: RD-003 — Duplicate sleep log** — /home/pi/iris_sleep.log vs /home/pi/logs/iris_sleep.log.

---

## Session Scope

S58: Teensy 4.0 confirmed as final base mount controller (ESP32 abandoned). Firmware renamed + 4 bugs fixed, Pi4 bridge created and wired into assistant.py, stale ESP32/Pico/bak files deleted, IRIS_ARCH.md fully updated, Pi4 deployed + SD persisted + VERIFIED.

---

## Last Session Changes (S58)

- **`servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`** — Renamed from IRIS-BaseServoControlViaPerson_Sensor.ino. Fixed: panServo.attach(2), Serial.begin(115200), VOL+/VOL- commands, comment block. Build: SUCCESS.
- **`servo_teensy40/teensy40_base_mount/platformio.ini`** — monitor_speed=115200 (was 9600).
- **`pi4/hardware/base_mount_bridge.py`** — NEW. BaseMountBridge class: reads /dev/ttyACM1, dispatches VOL+/VOL-/STOP. DEPLOYED+VERIFIED md5 6bfc3801.
- **`pi4/core/config.py`** — Added BASE_MOUNT_ENABLED, BASE_MOUNT_PORT, BASE_MOUNT_BAUD. DEPLOYED+VERIFIED md5 ebf1561b.
- **`pi4/assistant.py`** — Added BaseMountBridge import + startup block. Removed dead start_servo_listener(). DEPLOYED+VERIFIED md5 f98978a5.
- **`pi4/iris_web.py`** — Removed ESP32 references from /api/stop and /api/listen docstrings. REPO-ONLY.
- **`IRIS_ARCH.md`** — System Roles/Architecture tables updated. New Teensy 4.0 pin section. ESP32 servo section deleted.
- **`.claude/settings.local.json`** — PostToolUse hook path fixed to absolute path.
- **Deleted:** servo_esp32/ directory, docs/servo_esp32_wiring.md, docs/servo_esp32_wiring_onenote.html, docs/servo_pico_wiring_onenote.txt, two .bak files.

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

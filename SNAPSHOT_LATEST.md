# IRIS Snapshot

**Session:** S61 | **Date:** 2026-05-23 | **Branch:** `main` | **Last commit:** pending

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## Machine Status

| System | Status |
|---|---|
| SuperMaster Desktop | Canonical repo — S61 committed locally, push pending. |
| Pi4 192.168.1.200 | Operational. S60 still live. S61 REPO-ONLY — deploy pending. iris-web + assistant services running. [INFO] Ready. |
| GandalfAI 192.168.1.3 | Operational. iris + iris-kids models current (S48 PT-001). |
| Teensy 4.1 | Firmware REPO-ONLY (af66b24). BL_MAP log curve + idle animations built, flash pending. /dev/ttyACM0 confirmed. |
| Teensy 4.0 (base mount) | DEPLOYED+VERIFIED S59. Gesture sensor (APDS-9960) working — VOL+/VOL-/STOP/LISTEN confirmed on desktop USB. Flashed to Pi4 /dev/ttyACM1. [BASE] connected confirmed. Servo works (clunky/jerky — tuning pending). |
| Servo Controller (ESP32 DevKit 1C) | TOMBSTONED. PCB destroyed. servo_esp32/ directory removed S58. |
| TTS | Kokoro primary (Docker port 8004), Piper fallback (Wyoming port 10200). |

---

## Active Issues

- **HIGH: Teensy 4.0 servo tuning** — Pan servo works but clunky/jerky. Tune PAN_SPEED, PAN_DEAD_ZONE, FACE_HOLD_MS, FACE_RETURN_MS constants in servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino. Flash after tuning.
- **HIGH: HW-001 — Teensy 4.1 LED jumper cut** — Physical mod only, no software needed.
- **HIGH: Teensy 4.1 firmware flash pending** — af66b24 BL_MAP + idle animations. PlatformIO upload, COM7.
- **MED: Perceived latency** — OLLAMA_KEEP_ALIVE=30m on GandalfAI pending.
- **LOW: RD-011 — APDS-9960 LISTEN proximity trigger** — gesture VOL+/VOL-/STOP verified working S59. LISTEN (proximity hold) not yet verified on live Pi.
- **LOW: RD-003 — Duplicate sleep log** — /home/pi/iris_sleep.log vs /home/pi/logs/iris_sleep.log.

---

## Session Scope

S61: Event log persistence + gesture monitoring. Fixed critical MSG_RE bug (was `assistant|iris.web`, must be `python3` — event log was showing zero events). Added SD daily log reading to /api/logs (30-day history, survives reboots). Added /api/gesture_log endpoint. Added gesture event parsing ([GESTURE] and legacy [BASE] tags). Changed base_mount_bridge.py gesture output to structured [GESTURE] format. Added Gesture log panel to Gestures tab (auto-refresh, date+time display, 200-event history). Added Gesture filter to Logs tab. Added iris_log_export.sh to repo with 30-day retention (was 7). All changes REPO-ONLY — deploy pending.

---

## Last Session Changes (S61)

- **`pi4/iris_web.py`** — Fixed _MSG_RE (`python3[PID]` format). Extracted parse logic to module-level `_parse_event_msg()` + `_sd_events()` helpers. `/api/logs` now merges current journalctl + SD daily logs (30 days, deduped, capped 500). Added `[GESTURE]` + legacy `[BASE]` gesture event parsing. Added `/api/gesture_log` endpoint (200 most-recent gesture events, SD+journal). REPO-ONLY.
- **`pi4/iris_web.html`** — Added `cat-gesture` CSS, `f-gesture` filter CSS. Added Gesture filter button to Logs tab. Added Gesture Event Log card to Gestures tab (auto-refresh 30s, full date+time display, 300px panel). `fetchGestureLog()` / `toggleGestureLogAuto()` JS. `_CAT_LABELS` updated. Tab switch now calls `fetchGestureLog()`. REPO-ONLY.
- **`pi4/hardware/base_mount_bridge.py`** — Gesture dispatch output changed from `[BASE] {line}` to `[GESTURE] gesture={line} action={action}`. Connection/error messages remain `[BASE]`. REPO-ONLY.
- **`pi4/scripts/iris_log_export.sh`** — Added to repo (was Pi4-only). Updated retention: 7 days → 30 days (`tail -n +31`). REPO-ONLY.

## Previous Session Changes (S60)

- **`pi4/hardware/base_mount_bridge.py`** — Config-driven gesture dispatch: reads GESTURE_MAP from iris_config.json on each event. Added LISTEN action (/tmp/iris_manual_listen), SKIP no-op, error handling per action. DEPLOYED+VERIFIED md5 743d1d52.
- **`pi4/iris_web.py`** — Added /api/gesture_config GET/POST endpoint. GET returns GESTURE_MAP + GESTURE_PROXIMITY_THRESHOLD from iris_config.json (defaults if absent). POST validates actions against whitelist, range-clamps threshold, writes via write_cfg(). DEPLOYED+VERIFIED md5 98f84f0f.
- **`pi4/iris_web.html`** — Added Gestures nav tab. Gestures section: four select dropdowns (VOL+/VOL-/STOP/LISTEN gesture keys, actions VOL+/VOL-/STOP/LISTEN/SKIP), proximity threshold range slider 0-255. loadGestureConfig()/saveGestureConfig() JS. DEPLOYED+VERIFIED md5 0a8bdfc7.

## Previous Session Changes (S59)

- **`servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`** — Added REBOOT command, Person Sensor LED disable, while(!Serial) boot wait, I2C_SCAN_DIAG flag, raw APDS ID read diagnostic. Removed enableProximitySensor(false) bug. DEPLOYED+VERIFIED.
- **`servo_teensy40/teensy40_base_mount/platformio.ini`** — Removed registry APDS9960 dep; uses local lib/ instead.
- **`servo_teensy40/teensy40_base_mount/lib/SparkFun_APDS9960/`** — NEW. Patched SparkFun APDS9960 library: delay(25) after Wire.begin() in init() for Teensy 4.0 I2C settle.
- **`servo_teensy40/i2c_scanner/`** — NEW. Standalone I2C scanner diagnostic sketch.

---

## Deploy Checklist (S61 — say DEPLOY)

1. Deploy `pi4/iris_web.py` → `/home/pi/iris_web.py` + persist to SD
2. Deploy `pi4/iris_web.html` → `/home/pi/iris_web.html` + persist to SD
3. Deploy `pi4/hardware/base_mount_bridge.py` → `/home/pi/hardware/base_mount_bridge.py` + persist to SD
4. Deploy `pi4/scripts/iris_log_export.sh` → `/home/pi/scripts/iris_log_export.sh` + persist to SD (updates cron retention from 7→30 days)
5. Restart `iris-web` service
6. Verify: open Logs tab → should show events from SD daily files (not just current boot)
7. Verify: open Gestures tab → Gesture Event Log panel present
8. Trigger a gesture → confirm `[GESTURE]` line appears in Gesture Event Log

---

## Known TODO

- **NEXT: Servo tuning** — Tune PAN_SPEED/PAN_DEAD_ZONE/FACE_HOLD_MS/FACE_RETURN_MS in teensy40_base_mount.ino, then re-flash
- HW-001: cut LED/SCK solder jumper on Teensy 4.1 underside
- Flash Teensy 4.1 firmware (PlatformIO upload, env:eyes, COM7, user clicks upload)
- GandalfAI: set OLLAMA_KEEP_ALIVE=30m + restart Ollama service
- RD-011: confirm APDS-9960 LISTEN trigger fires on Teensy 4.0

---

## Do Not Touch Without Explicit Instruction

- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

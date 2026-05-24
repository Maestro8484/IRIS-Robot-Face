# IRIS Snapshot

**Session:** S61b | **Date:** 2026-05-23 | **Branch:** `main` | **Last commit:** 5af1073 S61b log capture fix

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## WHAT'S NEXT (Priority Queue)

1. **Servo tuning** — Tune PAN_SPEED/PAN_DEAD_ZONE/FACE_HOLD_MS/FACE_RETURN_MS in `teensy40_base_mount.ino`, then reflash. Handoff: `HANDOFF_SERVO_TUNING.md`.
2. **Teensy 4.1 flash** — Sleep animation session in progress (separate). After that session completes: PlatformIO upload, env:eyes, COM7, user clicks upload.
3. **RD-011** — Confirm APDS-9960 LISTEN proximity trigger fires on live Pi4.
4. **RD-003** — Resolve duplicate sleep log (`/home/pi/iris_sleep.log` vs `/home/pi/logs/iris_sleep.log`).

---

## Machine Status

| System | Status |
|---|---|
| SuperMaster Desktop | Canonical repo — S61b committed + pushed to GitHub. |
| Pi4 192.168.1.200 | Operational. S61b DEPLOYED+VERIFIED. iris-web + assistant services running. [INFO] Ready. Event log reads SD history. Cron */5 for log export + GandalfAI scp backup. |
| GandalfAI 192.168.1.3 | Operational. iris + iris-kids models current (S48 PT-001). OLLAMA_KEEP_ALIVE=30m set. C:\IRIS\iris-logs\ receiving Pi4 backups (6 files confirmed 2026-05-23). |
| Teensy 4.1 | Sleep animation update IN PROGRESS (separate session). Base firmware af66b24 (BL_MAP + idle animations). Flash after sleep animation session completes. |
| Teensy 4.0 (base mount) | DEPLOYED+VERIFIED S59. Gesture sensor (APDS-9960) working — VOL+/VOL-/STOP/LISTEN confirmed on desktop USB. Flashed to Pi4 /dev/ttyACM1. [BASE] connected confirmed. Servo works (clunky/jerky — tuning pending). |
| Servo Controller (ESP32 DevKit 1C) | TOMBSTONED. PCB destroyed. servo_esp32/ directory removed S58. |
| TTS | Kokoro primary (Docker port 8004), Piper fallback (Wyoming port 10200). |

---

## Active Issues

- **HIGH: Teensy 4.0 servo tuning** — Pan servo works but clunky/jerky. Tune PAN_SPEED, PAN_DEAD_ZONE, FACE_HOLD_MS, FACE_RETURN_MS constants in servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino. Flash after tuning.
- **HIGH: HW-001 — Teensy 4.1 LED** — DONE. Covered with black electrical tape.
- **HIGH: Teensy 4.1 firmware flash** — Sleep animation update in progress (separate session). Flash after that session completes. PlatformIO upload, env:eyes, COM7, user clicks upload.
- **MED: Perceived latency** — RESOLVED. OLLAMA_KEEP_ALIVE=30m active on GandalfAI.
- **LOW: RD-011 — APDS-9960 LISTEN proximity trigger** — gesture VOL+/VOL-/STOP verified working S59. LISTEN (proximity hold) not yet verified on live Pi.
- **LOW: RD-003 — Duplicate sleep log** — /home/pi/iris_sleep.log vs /home/pi/logs/iris_sleep.log.

---

## Session Scope

S61b: GandalfAI log backup + SLEEP/WAKE gesture actions. iris_log_export.sh now scp's all daily logs to GandalfAI `C:\IRIS\iris-logs\` every 5 min. Pi4 ed25519 key generated + authorized in GandalfAI `C:\ProgramData\ssh\administrators_authorized_keys`. SLEEP/WAKE added as gesture actions in base_mount_bridge.py (sends EYES:SLEEP/EYES:WAKE UDP to CMD_PORT 10500 → full sleep/wake sequence). iris_web.html gesture dropdowns updated with SLEEP/WAKE options. All DEPLOYED+VERIFIED. md5 confirmed RAM=SD.

S61: Event log persistence + gesture monitoring. Fixed critical _MSG_RE bug (was `assistant|iris.web`, actual format is `python3[PID]` — event log was showing zero events). Fixed cron overwrite bug (was `> file --boot`, now `>> file --since=LAST_TS` append mode, 5-min interval). SD daily logs read at `/api/logs` (100MB size-based retention, survives reboots). Added `/api/gesture_log` endpoint. Structured `[GESTURE]` log format in base_mount_bridge.py. Gesture Event Log panel in Gestures tab. Gesture filter in Logs tab. All DEPLOYED+VERIFIED. md5 confirmed for all 4 files (RAM=SD).

---

## Last Session Changes (S61b)

- **`pi4/hardware/base_mount_bridge.py`** — Added SLEEP and WAKE gesture actions: `EYES:SLEEP`/`EYES:WAKE` UDP to CMD_PORT 10500 → full `_do_sleep()`/`_do_wake()` sequences. DEPLOYED+VERIFIED md5 `dc944097`.
- **`pi4/scripts/iris_log_export.sh`** — Added scp backup to GandalfAI `C:\IRIS\iris-logs\` using `/home/pi/.ssh/id_iris_logs` key. Runs every 5 min with the cron. DEPLOYED+VERIFIED md5 `5fe88e7d`.
- **`pi4/iris_web.html`** — SLEEP/WAKE added to `_GESTURE_ACTIONS` array and `_GESTURE_LABELS`. Gesture Event Log hint updated to mention GandalfAI backup. DEPLOYED+VERIFIED md5 `d1c15589` RAM=SD.
- **GandalfAI `C:\IRIS\iris-logs\`** — Directory created. `C:\ProgramData\ssh\administrators_authorized_keys` updated with pi4-iris-logs public key. ICACLs set (SYSTEM:F + Administrators:F, no inheritance). 7 daily log files backed up.
- **Pi4 SSH key** — ed25519 key at `/home/pi/.ssh/id_iris_logs` + `/media/root-ro/home/pi/.ssh/id_iris_logs`. SD-persisted.
- **`C:\Users\SuperMaster\.claude\CLAUDE.md`** — Machine credentials block added (Pi4/GandalfAI/SuperMaster passwords).

## Previous Session Changes (S61)

- **`pi4/iris_web.py`** — Fixed _MSG_RE (`python3[PID]` format). Extracted parse logic to module-level `_parse_event_msg()` + `_sd_events(n_days=3650)` helpers. `/api/logs` merges journalctl + SD daily logs (deduped, capped 500). Added `[GESTURE]` + legacy `[BASE]` gesture parsing. Added `/api/gesture_log` (200 most-recent gesture events). DEPLOYED+VERIFIED md5 0561d413.
- **`pi4/iris_web.html`** — Added `cat-gesture` CSS, `f-gesture` filter. Gesture filter button in Logs tab. Gesture Event Log card in Gestures tab (auto-refresh 30s, date+time, 300px). Updated hint text to "100MB retention". DEPLOYED+VERIFIED md5 84531409.
- **`pi4/hardware/base_mount_bridge.py`** — Output changed from `[BASE] {line}` to `[GESTURE] gesture={line} action={action}`. Connection/error messages remain `[BASE]`. DEPLOYED+VERIFIED md5 30f3e04b.
- **`pi4/scripts/iris_log_export.sh`** — Rewritten: append mode (`>>`), timestamp tracking (`/run/iris_log_last_ts`), 100MB size-cap (oldest files removed). DEPLOYED+VERIFIED md5 47b0959e.
- **`/etc/cron.d/iris-logs`** — Changed from `*/15` to `*/5` (must beat ~35min journald rotation window). DEPLOYED.
- **`pi4/scripts/iris-logs.cron`** — Local repo copy updated to `*/5`.

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

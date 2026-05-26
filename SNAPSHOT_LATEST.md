# IRIS Snapshot

**Session:** S67 | **Date:** 2026-05-26 | **Branch:** `main` | **Last commit:** cb9d3c2

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## WHAT'S NEXT (Priority Queue)

1. **Pi4 deploy — S65/S66/S67 files** — `pi4/iris_post.py`, `pi4/assistant.py`, `pi4/iris_web.py`, `pi4/iris_web.html`, `pi4/core/config.py`, `pi4/scripts/iris_log_export.sh` REPO-ONLY. Single DEPLOY covers S65 sliders + S66 POST + S67 bench persistence. Say DEPLOY when ready.
2. **Servo tuning** — Tune PAN_SPEED/PAN_DEAD_ZONE/FACE_HOLD_MS/FACE_RETURN_MS in `servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`, then reflash.
3. **RD-011** — Confirm APDS-9960 LISTEN proximity trigger fires on live Pi4.
4. **RD-003** — Resolve duplicate sleep log (`/home/pi/iris_sleep.log` vs `/home/pi/logs/iris_sleep.log`).

---

## Machine Status

| System | Status |
|---|---|
| SuperMaster Desktop | Canonical repo — S67 committed. S65/S66/S67 Pi4 files REPO-ONLY pending DEPLOY. |
| Pi4 192.168.1.200 | Operational. S61b DEPLOYED+VERIFIED. iris-web + assistant services running. [INFO] Ready. install_journald.sh run S67 (journald 500MB/1yr). S65/S66/S67 files (iris_post.py, assistant.py, iris_web.py, iris_web.html, config.py, iris_log_export.sh) REPO-ONLY pending DEPLOY. |
| GandalfAI 192.168.1.3 | Operational. iris + iris-kids models current (S48 PT-001). OLLAMA_KEEP_ALIVE=30m set. C:\IRIS\iris-logs\ receiving Pi4 backups (6 files confirmed 2026-05-23). |
| Teensy 4.1 (TeensyEyes + mouth TFT) | DEPLOYED S65 — udev symlink /dev/ttyIRIS_EYES active. S65 cosmic sleep animation flashed (Saturn+Moon+warp+nebula+3-wave mouth+symmetric ZZZ). SLEEP_CFG: handler active. Pi4 slider config files REPO-ONLY. |
| Teensy 4.0 (servo + gesture) | DEPLOYED+VERIFIED S59. APDS-9960 gesture sensor working. Servo pan works (clunky/jerky — tuning pending). /dev/ttyIRIS_SERVO (udev symlink, S63). |
| Servo Controller (ESP32 DevKit 1C) | TOMBSTONED. PCB destroyed. servo_esp32/ directory removed S58. |
| TTS | Kokoro primary (Docker port 8004), Piper fallback (Wyoming port 10200). |

---

## Active Issues

- **MED: Pi4 deploy — S65/S66/S67 files** — iris_post.py (NEW), assistant.py (POST + BENCH_LOG), iris_web.py (/api/post /api/sleep_cfg), iris_web.html (POST card + sleep sliders), config.py (GESTURE_SENSOR_REQUIRED + SLEEP_ANIM_* + BENCH_LOG/SD_BENCH_LOG), iris_log_export.sh (bench JSONL sync) all REPO-ONLY. Single DEPLOY covers all three sessions. GESTURE_SENSOR_REQUIRED=False pending PAJ7620U2 swap.
- **HIGH: Teensy 4.0 servo tuning** — Pan servo works but clunky/jerky. Tune PAN_SPEED, PAN_DEAD_ZONE, FACE_HOLD_MS, FACE_RETURN_MS in servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino. Flash after tuning.
- **HIGH: HW-001 — Teensy 4.1 LED** — DONE. Covered with black electrical tape.
- **MED: Perceived latency** — RESOLVED. OLLAMA_KEEP_ALIVE=30m active on GandalfAI.
- **HIGH: APDS-9960 chip dead (S65)** — I2C no-response confirmed. Person Sensor on same bus/pull-ups/3.3V rail works — bus is healthy. Fault isolated to APDS-9960 chip or its specific wiring. Chip returned 0x0 from ID register (expected 0xAB), then full no-response after reflash. Action: physically reseat or swap APDS-9960 breakout, reflash T4.0, verify gesture events in web UI.
- **LOW: RD-003 — Duplicate sleep log** — /home/pi/iris_sleep.log vs /home/pi/logs/iris_sleep.log.

---

## Session Scope

S67: iris_bench.jsonl SD persistence. `iris_log_export.sh` extended with byte-offset append block: on each 15-min cron run (as root), new records from RAM `/home/pi/logs/iris_bench.jsonl` are appended to SD `/media/root-ro/home/pi/logs/iris_bench.jsonl` using `/run/iris_bench_last_pos` stamp (resets on boot — correct, each boot cycle appends its own records). `config.py` gains `BENCH_LOG` (RAM write path) and `SD_BENCH_LOG` (SD accumulation path). `assistant.py` `_bench_write` uses `BENCH_LOG` constant instead of hardcoded string. `install_journald.sh` run on Pi4 — journald retention extended to 500MB/1 year (S50 pending step). All Pi4 file changes REPO-ONLY pending DEPLOY.

S66: IRIS Power-On Self-Test (POST) — new `pi4/iris_post.py` (5-layer diagnostic: L0 hardware presence, L1 network/services, L2 Teensy display exercise, L3 pipeline smoke, L4 config/persistence). APA102 LEDs cycle through layer colors (cyan/purple/amber/orange/red) during POST; green flash on PASS; red 3× flash + freeze on FAIL. Results logged to `/home/pi/logs/iris_post.log`. assistant.py calls `run_post()` at startup before main loop; FAIL blocks startup (sys.exit 1). iris_web.py `/api/post` route runs POST in background thread; iris_web.html System tab POST card with per-check result table. `GESTURE_SENSOR_REQUIRED=False` added to config.py (flip to True after PAJ7620U2 swap confirmed). All Pi4 files REPO-ONLY pending DEPLOY.

S65: Cosmic sleep animation overhaul — full visual rewrite of GC9A01A eyes and ILI9341 mouth TFT to match HTML v8 mockup (Saturn+Moon+warp particles+nebula+3-wave mouth+symmetric ZZZ). Added SleepCfg struct shared header, 24-field SLEEP_CFG: serial protocol, Pi4 SLEEP_ANIM_* config system, /api/sleep_cfg web route, and Sleep Animation slider card in web UI. Animation speed reduced (SR_FRAME_MS 155ms, speed default 0.85). Firmware flashed to Teensy 4.1. Pi4 files REPO-ONLY pending DEPLOY.

S63: WebUI→Teensy 4.1 connection fix + persistent USB device identity. Root cause was two-part: (1) Teensy 4.0/4.1 USB ports swapped on Pi4 — Linux assigns /dev/ttyACM* by port position, so swapping ports swapped device names. (2) CMD listener forwarded EMOTION:/EYE:/MOUTH: commands while eyesSleeping=true — Teensy firmware processed commands but main loop early-return bypassed display rendering, producing no visible effect. Fix 1: udev rules bind /dev/ttyIRIS_EYES (Teensy 4.1) and /dev/ttyIRIS_SERVO (Teensy 4.0) to hardware serial numbers — survive all port swaps and reboots. Fix 2: CMD listener auto-wakes before forwarding display commands if eyes_sleeping. Also synced SLEEP_CFG_MAP and updated _do_sleep() from deployed S62 state into local repo (S62 had been deployed without local commit).

S61b: GandalfAI log backup + SLEEP/WAKE gesture actions. iris_log_export.sh now scp's all daily logs to GandalfAI `C:\IRIS\iris-logs\` every 5 min. Pi4 ed25519 key generated + authorized in GandalfAI `C:\ProgramData\ssh\administrators_authorized_keys`. SLEEP/WAKE added as gesture actions in base_mount_bridge.py (sends EYES:SLEEP/EYES:WAKE UDP to CMD_PORT 10500 → full sleep/wake sequence). iris_web.html gesture dropdowns updated with SLEEP/WAKE options. All DEPLOYED+VERIFIED. md5 confirmed RAM=SD.

S61: Event log persistence + gesture monitoring. Fixed critical _MSG_RE bug (was `assistant|iris.web`, actual format is `python3[PID]` — event log was showing zero events). Fixed cron overwrite bug (was `> file --boot`, now `>> file --since=LAST_TS` append mode, 5-min interval). SD daily logs read at `/api/logs` (100MB size-based retention, survives reboots). Added `/api/gesture_log` endpoint. Structured `[GESTURE]` log format in base_mount_bridge.py. Gesture Event Log panel in Gestures tab. Gesture filter in Logs tab. All DEPLOYED+VERIFIED. md5 confirmed for all 4 files (RAM=SD).

---

## Last Session Changes (S65)

- **`src/sleep_cfg.h`** (NEW) — Minimal shared struct header: `SleepCfg` (25 fields) + `extern SleepCfg sleepCfg`. Allows mouth_tft.cpp to access sleepCfg without pulling in GC9A01A_t3n.h (header conflict with ILI9341).
- **`src/sleep_renderer.h`** (FULL REWRITE) — Cosmic sleep animation v3: Saturn (rings, bands, specular), Moon (crescent, glow), 48 warp particles (LFSR-seeded), nebula overlay, starfield. ZZZ removed from eyes (moved to mouth). SR_FRAME_MS=155ms, speed=0.85. Moon: top-right eye (175,48) / top-left eye (65,48). Saturn: bottom-left eye (55,185) / bottom-right eye (185,185).
- **`src/mouth_tft.cpp`** — `mouthSleepFrame()` rewritten: symmetric ZZZ pairs (3 sizes, sinusoidal drift, cyan), 3-wave band (y=76..162, blue+purple+teal, primary+0.35x secondary harmonic), cy oscillation capped ±14px for SWSPI band constraint.
- **`src/main.cpp`** — SERIAL_BUF_SIZE 32→40. SLEEP_CFG: command handler added: parses `key=value`, maps all 24 SleepCfg fields from Pi4 serial.
- **`pi4/core/config.py`** — 24 SLEEP_ANIM_* constants added (speed, star*, shoot*, warp*, moon*, saturn*, nebula*, wave*, mouth*, zzz*). All added to `_OVERRIDABLE` + `_TYPE_COERCE` with slider range bounds.
- **`pi4/iris_web.py`** — `/api/sleep_cfg` GET/POST route: GET returns 24 current values keyed by short name; POST maps to SLEEP_ANIM_* and writes via `write_cfg()`.
- **`pi4/iris_web.html`** — Sleep Animation card: 4 `<details>` groups (Stars & Warps, Shooting Stars, Objects, Mouth), 24 sliders, `_buildSaSliders()` / `_saCfgSend()` (180ms debounce) / `_loadSaSliders()`. Sleep tab button wired: `_saTabHook()` loads sliders on first click.

**Status:** Firmware FLASHED (Teensy 4.1, env:eyes, COM7). Pi4 files REPO-ONLY pending DEPLOY.

## Previous Session Changes (S63)

- **`pi4/scripts/99-iris-teensy.rules`** — NEW FILE. udev rules: /dev/ttyIRIS_EYES → Teensy 4.1 (serial 13625440), /dev/ttyIRIS_SERVO → Teensy 4.0 (serial 12763490). DEPLOYED to /etc/udev/rules.d/99-iris-teensy.rules + udevadm reload.
- **`pi4/core/config.py`** — TEENSY_PORT → "/dev/ttyIRIS_EYES", BASE_MOUNT_PORT → "/dev/ttyIRIS_SERVO". DEPLOYED+VERIFIED.
- **`pi4/assistant.py`** — (1) CMD listener auto-wake: if state.eyes_sleeping and EMOTION:/EYE:/MOUTH: command, calls _do_wake() before forwarding. (2) SLEEP_CFG_MAP dict synced from deployed S62 state. (3) _do_sleep() pushes SLEEP_CFG: parameters to Teensy on sleep entry. (4) BaseMountBridge call: passes leds arg. DEPLOYED (CMD listener patch only; full file sync REPO-ONLY pending full deploy).
- **`docs/sysmap.json`** — serial.device → ttyIRIS_EYES, pico_serial replaced with teensy40_serial + udev_rules section, servo_pico node renamed to teensy40 with correct Teensy 4.0 hardware. cmd_listener.notes updated.
- **`IRIS_ARCH.md`** — USB Device Identity section added. All /dev/ttyACM* references updated to ttyIRIS_EYES/ttyIRIS_SERVO. Serial Ownership Rule updated with auto-wake note.

## Previous Session Changes (S61b)

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

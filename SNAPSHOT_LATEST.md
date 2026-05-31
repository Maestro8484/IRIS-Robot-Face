# IRIS Snapshot

**Session:** S84 | **Date:** 2026-05-31 | **Branch:** `main` | **Last commit:** (S84 uncommitted)

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## WHAT'S NEXT (Priority Queue)

1. **Flash TS40-S1 firmware** — GY-PAJ7620 replacement sensor arrived (S83). GESTURE_MOUNT_DEGREES set to 0 (right side up). Build clean (env:teensy40). Upload via PlatformIO. Verify: `PAJ7620U2 0x73 ACK=YES` + `init=OK` in boot DIAG, single-fire gestures with `SUPPRESSED` on rapid repeats, face tracking + PAN unchanged.
2. **Deploy S83 Pi4 changes (after Pi4 bootloop resolved)** — `pi4/assistant.py` STOP UDP fix + `pi4/iris_web.html` gesture tab cleanup. REPO-ONLY pending bootloop fix in separate session.
3. **Set GESTURE_SENSOR_REQUIRED=True** — After flash + gesture verify, deploy to Pi4: `pi4/core/config.py` GESTURE_SENSOR_REQUIRED → True, restart service, confirm POST 22/22.
4. **RD-003** — Resolve duplicate sleep log (`/home/pi/iris_sleep.log` vs `/home/pi/logs/iris_sleep.log`).

---

## Machine Status

| System | Status |
|---|---|
| SuperMaster Desktop | Canonical repo — S81 REPO-ONLY (uncommitted). S80: Workbench Phase 1 VERIFIED. S81: Workbench Phase 2 AI analysis layer + pt001_17 modelfile fix. |
| IRIS Workbench | Phase 2 AI analysis layer live. Launch: `start_workbench.bat`. **Set ANTHROPIC_KEY in workbench.js line 5** to enable Run AI Analysis. pt001_17 modelfile fix DEPLOYED+VERIFIED — goodnight few-shot confirmed in ollama show iris. Fixture corrections pending user confirmation after AI analysis run. |
| Pi4 192.168.1.200 | Operational. S82: iris_config.json restored + atomic write hardening deployed. flask-cors installed + persisted to SD. iris_post.py L4 JSONDecodeError FAIL→WARN. POST 21/22 PASS. assistant + iris-web active. WebUI http://192.168.1.200:5000/ → 200. |
| GandalfAI 192.168.1.3 | Operational. **S81: iris rebuilt** — goodnight few-shot added (pt001_17 fix). S77 base: qwen2.5vl:32b-q4_K_M, persona sharpened. OLLAMA_KEEP_ALIVE=30m set. C:\IRIS\iris-logs\ receiving Pi4 backups. |
| Teensy 4.1 (TeensyEyes + mouth TFT) | DEPLOYED S65 — udev symlink /dev/ttyIRIS_EYES active. S65 cosmic sleep animation flashed. **S79 REPO-ONLY** — nordicBlue polarDist fix (_60_0→_69_0), strikingBlue new eye (index 7). Build clean (env:eyes). Pending user PlatformIO upload. |
| Teensy 4.0 (servo + gesture) | S69 FLASHED+INSTALLED. DS3218MG MS24 confirmed installed. **S83: GY-PAJ7620 replacement sensor arrived. GESTURE_MOUNT_DEGREES reset to 0 (right side up). Pending user PlatformIO flash** (env:teensy40). Firmware REPO-ONLY: TS40-S1 + TS40-S2 + S75 + S83 orientation fix. Person Sensor + servo pan operational on live S69 firmware. |
| Servo Controller (ESP32 DevKit 1C) | TOMBSTONED. PCB destroyed. servo_esp32/ directory removed S58. |
| TTS | Kokoro primary (Docker port 8004), Piper fallback (Wyoming port 10200). |

---

## Active Issues

- **HW-004 RESOLVED S83** — GY-PAJ7620 replacement arrived. GESTURE_MOUNT_DEGREES=0 in firmware. Pending flash to confirm `ACK=YES` + `init=OK` at 0x73. See WHAT'S NEXT #1.
- **HIGH: HW-001 — Teensy 4.1 LED** — DONE. Covered with black electrical tape.
- **MED: Perceived latency** — RESOLVED. OLLAMA_KEEP_ALIVE=30m active on GandalfAI.
- **LOW: RD-003 — Duplicate sleep log** — /home/pi/iris_sleep.log vs /home/pi/logs/iris_sleep.log.
- ~~LOW: Workbench /api/rebuild_model credential config pending~~ — RESOLVED S80. .iris_secrets + sshpass deployed+persisted. Rebuild verified end-to-end.
- **LOW: fixture corrections pending** — pt001_08/09 expected_emotion corrections not yet applied to pt001_cases.json. Awaiting user confirmation after AI analysis run in workbench.
- **RESOLVED S73: Sleep/webui bridge** — udev rules lost on Pi4 reboot (S63 deploy never persisted to SD). Now persisted. TeensyBridge drop-logging added.

---

## Session Scope

S84: ANGRY emotion for insults (modelfile), joke repertoire (20 jokes, insult-first delivery), loud-sound STOP threshold in audio_io.py (LOUD_STOP_THRESHOLD=9000 — instant STOP on shout/clap, no Whisper wait). IRIS Workbench: Latency Bench, POST/Diag, Feature Setup tabs fully implemented. All REPO-ONLY.

S83: STOP command fix + GY-PAJ7620 sensor orientation reset + WebUI gesture cleanup. `pi4/assistant.py`: STOP UDP now sets `_stop_playback` (was falling through to teensy.send_command). `paj7620.h`: GESTURE_MOUNT_DEGREES 270→0 (new board is right side up). `pi4/iris_web.html`: dead LISTEN row removed, STOP label updated to "swipe left or right". `docs/sysmap.json`: part + orientation updated. All REPO-ONLY — Pi4 deploy deferred pending bootloop fix; firmware pending user PlatformIO flash.

S79b: Pi4 deploy — iris_web.html (Striking Blue button) + iris_log_export.sh (SD bench append removed). SD was 100% full (iris_bench.jsonl 24GB); truncated + fixed. SD now 19% used. md5 verified RAM=SD. DEPLOYED+VERIFIED.

S79: nordicBlue iris size fix + new StrikingBlue eye (REPO-ONLY). Root cause of nordicBlue appearing smaller than hazel: S76 bumped irisRadius 60→69 in EyeDefinition but left the polarDist include and table reference pointing at `polarDist_240_125_60_0` (the old 60px table). Fix: two-line change in `nordicBlue.h` to use `polarDist_240_125_69_0`. New eye: `strikingBlue` (index 7) — 512×128 iris texture (vivid azure/cerulean with 42-spoke radial fiber pattern, warm amber sunflower ring near pupil, deep navy limbal ring), nordicBlue sclera (less visible veins), nordicBlue eyelids. Generated via `resources/eyes/240x240/strikingBlue/gen_iris.py` + `tablegen.py`. `src/config.h`: array 7→8, index 7 added. `src/main.cpp`: EYE_IDX_STRIKINGBLUE=7, COUNT 7→8. `pi4/iris_web.html`: button 7 added (REPO-ONLY). Build clean. Flash: 1.498MB.

S78: Persona/drift test harness (REPO-ONLY). New `tools/persona_harness/` — `run_harness.py`, `scorer.py`, `tts_client.py`, `turn_scripts/starter.txt`. Reuses production `extract_emotion_from_reply` + `clean_llm_reply` + `IntentRouter` via pi4/ sys.path injection. Verified run: 37 turns (31 LLM, 6 router-intercepted), 4 flags, drift=MEDIUM. Notable: T36 "As an AI, I don't feel anything" RLHF tell in multi-turn — candidate for next modelfile NEVER-say block. Kokoro endpoint verified: `POST /v1/audio/speech`, OpenAI-compatible, `input`+optional `voice`/`speed`/`response_format`/`stream`. TTS integration ready (wired, not exercised this session). No production files touched.

S77: qwen2.5vl model swap + adult persona sharpening. `iris_modelfile.txt`: FROM qwen2.5vl:32b-q4_K_M, stop `<|im_end|>`, temp 0.92; proactive-opinion + blunt paragraphs; EMOTIONAL STATE section rewritten (proactive character over defensive composure); sharper few-shot + new GENUINE OPINIONS block; 7 new NEVER-say RLHF tells. `iris-kids_modelfile.txt`: model swap + stop token + temp 0.88 only (kids persona unchanged). Both SFTP'd to GandalfAI and rebuilt via `ollama create` on qwen2.5vl. Smoke-tested 5/5 (Ollama REST API): adversarial→AMUSED, opinion→ANGRY no-hedge, time→NEUTRAL, "delete you"→AMUSED, vision→read "HELLO IRIS". Zero RLHF boilerplate; vision intact. gemma3:27b-it-qat retained as rollback. DEPLOYED+VERIFIED.

S75: Pan servo stutter fix + smoothing. `pan_servo.h`: `PAN_MIN` 65.0, `PAN_MAX` 115.0, `PAN_TRACK_SPEED` 8.0 deg/sec (new), `PAN_FILTER_ALPHA` 0.15 (new). `pan_servo.cpp`: `updatePanFromFace` — `isMoving()` guard removed (continuous target chase), `startEaseToD` replaced with `startEaseTo(filteredPan, PAN_TRACK_SPEED)` (constant angular velocity), `EASE_LINEAR` set per-call, low-pass `filteredPan` filter damps direction reversal momentum (~130ms time constant). `updatePanIdle` — `detach()` when within 1° of center (releases holding torque, eliminates lock/echo resonance), re-attach before idle-return move, `EASE_CUBIC_IN_OUT` explicit per-call. `handleSerialPanCmd` — PAN command uses `startEaseTo` + re-attach guard. Build clean. REPO-ONLY pending user flash.

S69: PAJ7620U2 + DS3218MG firmware + docs. teensy40_base_mount.ino fully rewritten (commits 35ffaf3→bf304a8): APDS-9960 removed, PAJ7620U2 bare I2C driver (bank 0/1 init, reg 0x43 bit-correct per datasheet p.24, GESTURE_MOUNT_DEGREES 270 for 90° CCW mount), touch3 LISTEN/STOP (pin 15, T3, 1s threshold), DS3218MG constants (PAN_SPEED 0.02, PAN_DEAD_ZONE 5.0, FACE_RETURN_MS 6000), SERIAL_DIAG hardened (pajOk in telemetry, raw gest byte, CODEX wrappers). platformio.ini: APDS9960 lib dep removed. README.md updated. sysmap.json: full PAJ7620U2 patch set (reg 0x43 bit table, rotation table for 0/90/180/270°, GESTURE_MOUNT_DEGREES ref, touch3 constants, pin 15 added). IRIS_ARCH.md: Teensy 4.0 pin section rewritten with PAJ7620U2 quick-reference and rotation table; "Pending Hardware" section removed. CHANGELOG.md: S69 fully documented. CLAUDE.md: CHANGELOG enforcement rules added. REPO-ONLY — firmware pending user PlatformIO upload.

S68: Docs-only audit and correction pass. Servo subsystem (Teensy 4.0) fully documented in IRIS_ARCH.md: System Roles/Architecture tables enhanced, firmware file/ServoEasing/autonomy/power-toggle added to T4.0 pin section, Serial Protocol section extended with T4.0 one-way serial, Repo Structure updated, Env Quick Ref updated, PAJ7620U2 pending hardware section added, stale /dev/ttyACM0 reference corrected. SNAPSHOT/HANDOFF updated. ROADMAP pruned: HW-002/RD-009/RD-010/RD-011 (ESP32, tombstoned) removed, HW-001 closed, HW-003 PAJ7620U2 added. CHANGELOG gains servo controller evolution history. Memory files corrected (flash workflow memories updated to Teensy 4.1, new project_servo_controller_hardware.md created). Commit cf0b17b.

S67: iris_bench.jsonl SD persistence. `iris_log_export.sh` extended with byte-offset append block: on each 15-min cron run (as root), new records from RAM `/home/pi/logs/iris_bench.jsonl` are appended to SD `/media/root-ro/home/pi/logs/iris_bench.jsonl` using `/run/iris_bench_last_pos` stamp (resets on boot — correct, each boot cycle appends its own records). `config.py` gains `BENCH_LOG` (RAM write path) and `SD_BENCH_LOG` (SD accumulation path). `assistant.py` `_bench_write` uses `BENCH_LOG` constant instead of hardcoded string. `install_journald.sh` run on Pi4 — journald retention extended to 500MB/1 year (S50 pending step). All Pi4 file changes REPO-ONLY pending DEPLOY.

S66: IRIS Power-On Self-Test (POST) — new `pi4/iris_post.py` (5-layer diagnostic: L0 hardware presence, L1 network/services, L2 Teensy display exercise, L3 pipeline smoke, L4 config/persistence). APA102 LEDs cycle through layer colors (cyan/purple/amber/orange/red) during POST; green flash on PASS; red 3× flash + freeze on FAIL. Results logged to `/home/pi/logs/iris_post.log`. assistant.py calls `run_post()` at startup before main loop; FAIL blocks startup (sys.exit 1). iris_web.py `/api/post` route runs POST in background thread; iris_web.html System tab POST card with per-check result table. `GESTURE_SENSOR_REQUIRED=False` added to config.py (flip to True after PAJ7620U2 swap confirmed). All Pi4 files REPO-ONLY pending DEPLOY.

S65: Cosmic sleep animation overhaul — full visual rewrite of GC9A01A eyes and ILI9341 mouth TFT to match HTML v8 mockup (Saturn+Moon+warp particles+nebula+3-wave mouth+symmetric ZZZ). Added SleepCfg struct shared header, 24-field SLEEP_CFG: serial protocol, Pi4 SLEEP_ANIM_* config system, /api/sleep_cfg web route, and Sleep Animation slider card in web UI. Animation speed reduced (SR_FRAME_MS 155ms, speed default 0.85). Firmware flashed to Teensy 4.1. Pi4 files REPO-ONLY pending DEPLOY.

S63: WebUI→Teensy 4.1 connection fix + persistent USB device identity. Root cause was two-part: (1) Teensy 4.0/4.1 USB ports swapped on Pi4 — Linux assigns /dev/ttyACM* by port position, so swapping ports swapped device names. (2) CMD listener forwarded EMOTION:/EYE:/MOUTH: commands while eyesSleeping=true — Teensy firmware processed commands but main loop early-return bypassed display rendering, producing no visible effect. Fix 1: udev rules bind /dev/ttyIRIS_EYES (Teensy 4.1) and /dev/ttyIRIS_SERVO (Teensy 4.0) to hardware serial numbers — survive all port swaps and reboots. Fix 2: CMD listener auto-wakes before forwarding display commands if eyes_sleeping. Also synced SLEEP_CFG_MAP and updated _do_sleep() from deployed S62 state into local repo (S62 had been deployed without local commit).

S61b: GandalfAI log backup + SLEEP/WAKE gesture actions. iris_log_export.sh now scp's all daily logs to GandalfAI `C:\IRIS\iris-logs\` every 5 min. Pi4 ed25519 key generated + authorized in GandalfAI `C:\ProgramData\ssh\administrators_authorized_keys`. SLEEP/WAKE added as gesture actions in base_mount_bridge.py (sends EYES:SLEEP/EYES:WAKE UDP to CMD_PORT 10500 → full sleep/wake sequence). iris_web.html gesture dropdowns updated with SLEEP/WAKE options. All DEPLOYED+VERIFIED. md5 confirmed RAM=SD.

S61: Event log persistence + gesture monitoring. Fixed critical _MSG_RE bug (was `assistant|iris.web`, actual format is `python3[PID]` — event log was showing zero events). Fixed cron overwrite bug (was `> file --boot`, now `>> file --since=LAST_TS` append mode, 5-min interval). SD daily logs read at `/api/logs` (100MB size-based retention, survives reboots). Added `/api/gesture_log` endpoint. Structured `[GESTURE]` log format in base_mount_bridge.py. Gesture Event Log panel in Gestures tab. Gesture filter in Logs tab. All DEPLOYED+VERIFIED. md5 confirmed for all 4 files (RAM=SD).

---

## Codex Audit Review (2026-05-29) — Claude-verified

Codex secondary-coder session (CDX-1..CDX-5) reviewed and accepted. Doc-audit items are now current and verified against source: `ROADMAP.md` / `docs/iris_issue_log.md` status pass (CDX-1), `CHANGELOG.md` backfill (CDX-2, all cited commits confirmed), `docs/sysmap.json` + `IRIS_ARCH.md` consistency incl. `SR_FRAME_MS`=155 and refreshed `config.py` constants (CDX-3), `README.md` audit (CDX-4), and `tests/` pytest scaffold (CDX-5, suite now 67 passed after `test_negative` correction). `docs/sysmap.json` is tracked (commit `f740844`). All REPO-ONLY. No protected files touched.

---

## Last Session Changes (S76)

**Part A — Emotion-driven speech animation (Pi4, DEPLOYED+VERIFIED):**

Root cause: `play_pcm_speaking()` used hardcoded HAPPY-dominant frames regardless of emotion; no hold before animation start; `restore_mouth_idx` always 0 (NEUTRAL). Emotion mouth was never visible during speech, and SLEEPY/SAD pupil ratios persisted through talking.

- `pi4/hardware/audio_io.py` — `_EMOTION_SPEAK_FRAMES` dict (9 emotions), `emotion` parameter, 350ms pre-animation hold, restores to caller-supplied `restore_mouth_idx`.
- `pi4/assistant.py` — `_current_emotion` tracking; `EMOTION:NEUTRAL` before speech (alert pupils during talking); per-emotion `play_pcm_speaking` call; `emit_emotion` re-emitted after speech. Follow-up loop updated.
- Deployed, md5 verified RAM=SD (`audio_io.py` `3cef28168156bebc19c3f99a9807290c`, `assistant.py` `3317358a1e8406c75dce5cc642bff5b0`). POST 21/22 PASS.

**Part C — nordicBlue iris radius (REPO-ONLY, firmware build clean):**

- `src/eyes/240x240/nordicBlue.h` — `irisRadius` 60 → 69, `pupilMin` 0.21 → 0.25. Matches hazel. `pio run -e eyes` [SUCCESS]. User must flash via PlatformIO upload (env:eyes).

---

## Prior Session Changes (S75)

**Root cause:** Pan servo had two distinct problems. First: `isMoving()` guard in tracking branch blocked new commands while the servo was moving — face movement produced jump-wait-jump stutter. Second: `startEaseToD(angle, 100ms)` used fixed duration regardless of distance, giving inconsistent angular velocity. Direction reversals (face crossing center) sent hard opposite commands that the top-heavy load could not follow symmetrically — momentum carried the head through center while the servo tried to reverse, causing visible jerk on one axis.

- **`servo_teensy40/teensy40_base_mount/pan_servo.h`** — Constants updated: `PAN_MIN` 65.0 (was 45.0 via S70), `PAN_MAX` 115.0 (was 135.0 via S70). New: `PAN_TRACK_SPEED` 8.0 deg/sec (speed-based move), `PAN_FILTER_ALPHA` 0.15 (low-pass weight). `PAN_SPEED` 0.02 retained with legacy annotation.
- **`servo_teensy40/teensy40_base_mount/pan_servo.cpp`** — Four behavioral changes: (1) `updatePanFromFace()`: `isMoving()` guard removed — servo continuously chases face target; `startEaseToD` replaced with `startEaseTo(filteredPan, PAN_TRACK_SPEED)` (constant 8 deg/sec); `EASE_LINEAR` set before each tracking call. (2) Low-pass filter `filteredPan` (`static float`, seeded to `desiredPan` at setup) applied to servo command — direction reversals ease over ~130ms rather than snapping, damping momentum asymmetry in the top-heavy mount. (3) `updatePanIdle()`: `panServo.detach()` when within 1° of center and not moving — releases DS3218MG holding torque, eliminates lock/echo resonance; `EASE_CUBIC_IN_OUT` set explicitly before each idle-return call; re-attach before `startEaseToD`. (4) `handleSerialPanCmd()`: PAN command uses `startEaseTo(angle, PAN_TRACK_SPEED)`; re-attach guard added.

**Build:** `pio run env:teensy40` — [SUCCESS] 48616 bytes flash, no warnings.

**Status:** REPO-ONLY — firmware pending user PlatformIO flash.

---

## Previous Session Changes (S74)

**Root cause:** GandalfAI `iris` model was running the `iris-kids` SYSTEM prompt — playful/expressive persona, no voice-interface constraints — instead of the adult SYSTEM prompt. Produced stage directions and ellipsis in TTS. `clean_llm_reply()` stripped `*` chars individually but left action-phrase text intact. GandalfAI clone was at S61b (12 sessions behind S73).

- **`pi4/services/llm.py` — `clean_llm_reply()`** — Three new regex passes: strip `*multi-word*` / `_multi-word_` blocks entirely; collapse `\.{2,}` to `.`. DEPLOYED+VERIFIED. md5 RAM=SD `e9e7e770c8f99597a492fd1ebeddaccd`.
- **`ollama/iris_modelfile.txt` — HOW YOU SPEAK** — Expanded from format checklist to full voice/character framework. GandalfAI `iris` model rebuilt. DEPLOYED+VERIFIED: adult SYSTEM + PT-001 + expanded HOW YOU SPEAK confirmed via `ollama show iris --modelfile`.

**Verification:** Pi4 active. POST L2 emotion sweep + EYES:SLEEP/WAKE passing. GandalfAI: adult persona + expanded HOW YOU SPEAK confirmed. **Live behavior confirmed by user — responses clean, adult dry persona active, no stage directions or ellipsis in TTS output.**

---

## Previous Session Changes (S73)

**Root cause:** `/etc/udev/rules.d/99-iris-teensy.rules` was deployed to Pi4 RAM overlay in S63 but never persisted to SD. Pi4 rebooted ~19:04 MDT 2026-05-28 — rules vanished, `/dev/ttyIRIS_EYES` symlink gone. TeensyBridge silently failed (serial port missing). Sleep cron (21:00) and webui sleep button both sent correct UDP — LEDs responded (direct Python path), Teensy displays never received commands.

- **`/etc/udev/rules.d/99-iris-teensy.rules`** — Redeployed from repo. `/dev/ttyIRIS_EYES -> ttyACM1` confirmed. DEPLOYED+VERIFIED.
- **`/media/root-ro/etc/udev/rules.d/99-iris-teensy.rules`** — NEW. First-time SD persistence. md5 verified. Survives all reboots.
- **`pi4/hardware/teensy_bridge.py`** — Docstring corrected (4.0→4.1, ttyACM0→ttyIRIS_EYES). `_open()` logs failure instead of silent None. `send_command()`/`send_emotion()` log `DROP` when port is not open. DEPLOYED+VERIFIED. md5 RAM=SD.

**Verification:** TeensyBridge reconnected within 5s of udev trigger. POST 21/22 PASS AUTHORIZED. Teensy confirmed EYES:SLEEP + starfield in journal.

---

## Previous Session Changes (TS40-S1)

- **`servo_teensy40/teensy40_base_mount/person_sensor.h` / `.cpp`** — NEW. Person Sensor driver: `setupPersonSensor()`, `pollPersonSensor()` → `PersonResult {ok, faceVisible, faceCenterX, confidence, isFacing}`. Codex-hardened decode bounds checking preserved exactly. `ok` flag preserves the original short-read early-return (pan held).
- **`servo_teensy40/teensy40_base_mount/pan_servo.h` / `.cpp`** — NEW. ServoEasing wrapper: `setupPanServo()`, `updatePanFromFace()`, `updatePanIdle()`, `handleSerialPanCmd()`. All PAN_* / FACE_* constants + `desiredPan` here. `ServoEasing.hpp` included in this TU only.
- **`servo_teensy40/teensy40_base_mount/diag.h`** — NEW. `DIAG_PRINT/PRINTLN/PRINTF` macros gated on SERIAL_DIAG. paj7620.* NOT refactored to use it (deferred).
- **`servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`** — Reduced to orchestration (345→94 lines). Phantom touch3 code removed (capTouch, pollTouch3, TOUCH3_* defines, header comments — pin 15 hardware never installed, S69 hallucination). No constant or logic change beyond touch3 removal.
- **`docs/sysmap.json` / `IRIS_ARCH.md` / `servo_teensy40/README.md`** — touch3 / pin 15 references removed. LISTEN kept (gesture action / web UI paths).

**Status:** REPO-ONLY — firmware pending user PlatformIO flash.

---

## Previous Session Changes (TS40-S2)

- **`servo_teensy40/teensy40_base_mount/paj7620.h`** — NEW. PAJ7620U2 public header: `SERIAL_DIAG`, `PAJ7620_ADDR`, `GESTURE_MOUNT_DEGREES`, `GESTURE_DEBOUNCE_MS=400`, `GESTURE_COOLDOWN_MS=200`, `extern bool pajOk`, `paj7620Init()`, `pollGesture()`.
- **`servo_teensy40/teensy40_base_mount/paj7620.cpp`** — NEW. Full PAJ7620U2 driver + debounce state machine: first-poll discard, 200ms global cooldown, 400ms per-gesture debounce, SERIAL_DIAG suppression logging. Emit block unchanged.
- **`servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`** — Stripped: all PAJ7620 code moved to paj7620.cpp/h. Added `#include "paj7620.h"`.
- **`docs/sysmap.json`** — `tunable_constants`: `GESTURE_DEBOUNCE_MS` + `GESTURE_COOLDOWN_MS` added.

---

## Earlier Session Changes (S72)

- **`servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`** — `pollGesture()` emit block: FORWARD/BACKWARD/CW/CCW now emit Serial commands (were silently ignored). Header updated. REPO-ONLY pending flash.
- **`pi4/hardware/base_mount_bridge.py`** — 4 new gesture keys in `_DEFAULT_GESTURE_MAP`. MUTE action added (get/set_volume toggle). `_mute_restore` state added.
- **`pi4/iris_web.py`** — `_DEFAULT_GESTURE_MAP` + `_VALID_GESTURE_ACTIONS` extended (SLEEP/WAKE/MUTE). GET merges defaults with stored config (new keys always get defaults). `_BASE_GEST_RE` updated for new gesture strings.
- **`pi4/iris_web.html`** — Gestures tab: APDS-9960→PAJ7620U2 throughout; proximity threshold removed; 4 new gesture rows (FORWARD/BACKWARD/CW/CCW); MUTE added to actions; gesture log `requestAnimationFrame` scroll fix (newest at top reliable); empty-state hint updated.
- **`IRIS_ARCH.md`** — Serial command table + command mapping + serial protocol block: all 8 gestures documented. Pin 2: servo model → DS3218MG MS24.
- **`servo_teensy40/README.md`** — Servo model → DS3218MG MS24.
- **`docs/servo_teensy40_wiring.md`** — Servo model → DS3218MG MS24.
- **`docs/sysmap.json`** — command_map: all 8 gestures. servo/gpio/tunable_constants: MS24, capTouch, PAN_MIN/MAX, S70 easing API.

**Status:** Firmware REPO-ONLY (pending user flash). Pi4 files DEPLOYED+VERIFIED.

**Deploy fix:** `BaseMountBridge.__init__` gained `leds=None` parameter — live `assistant.py` passes `(_bm_cfg, leds)` which would have caused a TypeError crash on startup without this fix.

---

## Previous Session Changes (S70)

- **`servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`** — ServoEasing async API. `PAN_MIN 45.0` / `PAN_MAX 135.0` defines added. All `constrain()` calls updated to PAN_MIN/PAN_MAX. setup(): `panServo.write()` cast removed, `panServo.setEasingType(EASE_CUBIC_IN_OUT)` + `enableServoEasingInterrupt()` added. Tracking branch: `setEasingType(EASE_CUBIC_OUT)` + `write()` replaced with `if (!panServo.isMoving()) { panServo.startEaseToD(desiredPan, 100); }`. Return-to-center branch: same pattern. PAN command handler: `toFloat()`, PAN_MIN/MAX, `startEaseToD`. PAN? query added (returns `getCurrentAngle()`). Build: clean (ServoEasing 3.6.0, `setUpdateInterval` absent — library default 20ms used). REPO-ONLY pending user flash.

**Status:** REPO-ONLY. No Pi4 changes. No GandalfAI changes.

---

## Previous Session Changes (S69)

- **`servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`** — FULL REWRITE (commits 35ffaf3→bf304a8). APDS-9960 driver removed (SparkFun include, apdsOk, prox LISTEN logic, raw ID read). PAJ7620U2 bare I2C driver added: paj_write/paj_read helpers; paj7620Init() (bank 0/1 config tables, 700ms wakeup settle, ACK confirm); pollGesture() reads reg 0x43 bit-correct per datasheet p.24 (bit3=UP/0x08, bit2=DOWN/0x04, bit1=RIGHT/0x02, bit0=LEFT/0x01); GESTURE_MOUNT_DEGREES 270 (90° CCW mount) maps phys UP=0x01/DOWN=0x02/LEFT=0x04/RIGHT=0x08. Physical UP→VOL+, DOWN→VOL-, LEFT/RIGHT→STOP. SERIAL_DIAG: pajOk in periodic telemetry, raw gest byte on detect, CODEX wrappers all blocks. Touch3 LISTEN: pollTouch3() pin 15 (T3), TOUCH3_THRESH=1500, short tap→STOP, hold 1s→LISTEN. DS3218MG constants: PAN_SPEED 0.02, PAN_DEAD_ZONE 5.0, FACE_RETURN_MS 6000. REPO-ONLY pending flash.
- **`servo_teensy40/teensy40_base_mount/platformio.ini`** — Removed stale SparkFun APDS9960 lib_deps comment. Platform URL auto-updated by PlatformIO. REPO-ONLY.
- **`servo_teensy40/README.md`** — Updated hardware list (PAJ7620U2, DS3218MG, touch3 pin 15, /dev/ttyIRIS_SERVO). Removed stale "new firmware to be written" note. REPO-ONLY.
- **`IRIS_ARCH.md`** — Architecture table Teensy 4.0 row updated (PAJ7620U2, touch3). Pin section rewritten: pin 15 added, I2C devices updated, serial command table adds LISTEN. PAJ7620U2 quick-reference section added with reg 0x43 bit layout table + rotation table for all 4 mount angles + command mapping. Touch3 constants table added. "Pending Hardware — PAJ7620U2" section removed. Repo Structure .ino comment updated. Serial Protocol Teensy 4.0 block updated.
- **`CLAUDE.md`** — CHANGELOG same-session enforcement rule added (Hard Rules + Documentation rules).
- **`docs/sysmap.json`** (local-only, gitignored) — Full PAJ7620U2 patch: pin 15 added to gpio, PAJ7620U2 sensor block (reg 0x43 bit table, rotation table, command map, replaced field), TOUCH3_PIN/TOUCH3_THRESH/TOUCH3_HOLD_MS in tunable_constants, gpio pin notes updated.
- **`CHANGELOG.md`** — S69 entry fully documented including all sub-commits, correct bit layout, GESTURE_MOUNT_DEGREES.

- **Build fix** — `touchRead()` declared in `cores/teensy4/core_pins.h` but never implemented in PlatformIO Teensy 4.x framework (only `teensy3/touch.c` exists). First call ever in this codebase (S69 `pollTouch3()`). Fixed with `capTouch(pin)`: discharge pin LOW, float INPUT_DISABLE, read ADC. Returns 0-1023. TOUCH3_THRESH changed from 1500 → 100.

**Status:** All REPO-ONLY. No Pi4 changes. No GandalfAI changes. Teensy 4.0 firmware pending user PlatformIO upload (env:teensy40). Build confirmed clean (6415676).

## Previous Session Changes (S65)

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

- **NEXT: Flash Teensy 4.0** — PAJ7620U2 firmware REPO-ONLY S69. PlatformIO upload env:teensy40. Verify DIAG output + gesture events. Tune TOUCH3_THRESH and PAN constants per hardware behavior.
- HW-001: cut LED/SCK solder jumper on Teensy 4.1 underside
- Flash Teensy 4.1 firmware (PlatformIO upload, env:eyes, COM7, user clicks upload)
- GandalfAI: set OLLAMA_KEEP_ALIVE=30m + restart Ollama service

---

## Do Not Touch Without Explicit Instruction

- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

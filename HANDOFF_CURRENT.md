<!-- Short session-start handoff only. Do not expand. Operational rules are in CLAUDE.md. -->

# IRIS Handoff — Current

## Session Startup Order

1. `git status` — branch must be `main`; tree must be clean.
2. Read `CLAUDE.md` — operating rules and hard constraints.
3. Read `SNAPSHOT_LATEST.md` — verified machine state and active issues.
4. Read this file — next-work pointer.
5. Read `IRIS_ARCH.md` — only when architecture, pins, services, or deploy details are needed.

## Source of Truth

`C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face`

GitHub is a secondary mirror. Local state outranks it until explicitly synced.

## Production Baseline

| System | State |
|---|---|
| Pi4 | Operational — assistant.py, intent_router.py, iris_web.py deployed and persisted. |
| GandalfAI | Operational — gemma3:27b-it-qat, Kokoro TTS (Docker port 8004), iris model current. |
| Teensy 4.1 | Operational — eye movement suspended during TTS. |
| Teensy 4.0 | REPO-ONLY S69 — PAJ7620U2 firmware written (GESTURE_MOUNT_DEGREES 270, reg 0x43 bit-correct per datasheet), pending user PlatformIO upload (env:teensy40). DS3218MG constants set. Touch3 LISTEN pin 15. /dev/ttyIRIS_SERVO. |
| STT / TTS | Whisper (GandalfAI) / Kokoro primary, Piper fallback (Wyoming port 10200). |
| Wakeword | `hey_jarvis` (production). Experimental wakewords require explicit user approval, live Pi4 state confirmation, clean process restart, and one-model-at-a-time testing. Failed experiment names are in `CHANGELOG.md`. |

## Navigation

- `SNAPSHOT_LATEST.md` — current verified state, active issues, last session changes.
- `ROADMAP.md` — all forward-looking tasks with full spec per item.
- `CHANGELOG.md` — completed sessions and batches.

## Deployment Gates

- Pi4 and GandalfAI mutations require explicit user authorization.
- GandalfAI model rebuilds require explicit `DEPLOY`.
- Pi4 persistence: direct `/media/root-ro` remount only — see `CLAUDE.md`.

## Next Work — *** DO THIS FIRST ***

**Flash Teensy 4.0 — PAJ7620U2 firmware REPO-ONLY S69**

PAJ7620U2 bare I2C driver written and committed. APDS-9960 fully removed. DS3218MG constants set. GESTURE_MOUNT_DEGREES 270 (sensor mounted 90° CCW) — change to 0 if mounting normally. Reg 0x43 bit map confirmed correct per datasheet p.24.

Steps:
1. Disconnect Teensy 4.0 from Pi4 USB. Connect to SuperMaster USB.
2. Open `servo_teensy40/teensy40_base_mount/` in PlatformIO. Click Upload (env:teensy40).
3. Open serial monitor at 115200. Confirm:
   - `DIAG: PAJ7620U2 0x73 ACK=YES`
   - `DIAG: PAJ7620U2 init=OK`
   - `DIAG: touch3=NNN` each second (NNN=baseline, touched≈3000+; tune TOUCH3_THRESH default 1500)
4. Swipe gestures in physical UP/DOWN/LEFT/RIGHT directions. Verify VOL+/VOL-/STOP in serial output.
   - If gestures fire wrong commands, change `GESTURE_MOUNT_DEGREES` (0/90/180/270) and reflash.
5. Reconnect to Pi4 USB. Confirm `/dev/ttyIRIS_SERVO` present.
6. Tune TOUCH3_THRESH (default 1500) based on observed baseline vs. touched values.
7. Tune PAN_SPEED/PAN_DEAD_ZONE per DS3218MG servo behavior — see HANDOFF_SERVO_TUNING.md.
8. After confirmed working: set `GESTURE_SENSOR_REQUIRED = True` in `pi4/core/config.py` and DEPLOY to Pi4.

### Deploy state (current)
- `servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino` — REPO-ONLY S69 (pending user PlatformIO upload)
- `servo_teensy40/teensy40_base_mount/platformio.ini` — REPO-ONLY S69
- `servo_teensy40/README.md` — REPO-ONLY S69
- `IRIS_ARCH.md` — REPO-ONLY S69 (PAJ7620U2 quick-ref + rotation table added)
- `CHANGELOG.md` — REPO-ONLY S69
- `CLAUDE.md` — REPO-ONLY S69
- `docs/sysmap.json` — LOCAL-ONLY (gitignored) S69 full PAJ7620U2 patch
- `src/sleep_cfg.h`, `src/sleep_renderer.h`, `src/mouth_tft.cpp`, `src/main.cpp` — FLASHED (Teensy 4.1 S65)
- `pi4/iris_post.py` — DEPLOYED+VERIFIED S67 (POST 21/22 PASS)
- `pi4/core/config.py` — DEPLOYED+VERIFIED S67
- `pi4/assistant.py` — DEPLOYED+VERIFIED S67
- `pi4/iris_web.py` — DEPLOYED+VERIFIED S67
- `pi4/iris_web.html` — DEPLOYED+VERIFIED S67
- `pi4/scripts/iris_log_export.sh` — DEPLOYED+VERIFIED S67
- S65/S66/S67/S68 commits pushed to GitHub. S69 pending push.

### Other pending
- **RD-003** — Duplicate sleep log cleanup (low priority)

---

## S58 — Teensy 4.0 Base Mount Controller (REPO-ONLY)

**Status:** REPO-ONLY. All files committed locally. Pi4 deploy and firmware flash pending user DEPLOY command.

**Changes:**
- `servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino` — renamed from IRIS-BaseServoControlViaPerson_Sensor. Fixed: pin 2, baud 115200, VOL+/VOL-, base_mount_bridge.py comment reference.
- `servo_teensy40/teensy40_base_mount/platformio.ini` — monitor_speed 115200.
- `pi4/hardware/base_mount_bridge.py` — NEW. Daemon thread reads /dev/ttyACM1 at 115200, dispatches VOL+/VOL-/STOP. (Note: /dev/ttyACM1 was replaced by /dev/ttyIRIS_SERVO udev symlink in S63.)
- `pi4/core/config.py` — BASE_MOUNT_ENABLED, BASE_MOUNT_PORT, BASE_MOUNT_BAUD added.
- `pi4/assistant.py` — BaseMountBridge import + conditional startup after TeensyBridge init.
- `IRIS_ARCH.md` — Teensy 4.0 pin section added, System Roles and Architecture tables updated.

**Rollback (Pi4 files, if deployed):**
```bash
git checkout -- pi4/assistant.py pi4/core/config.py
# Remove base_mount_bridge.py from Pi4, then persist and restart service
```

---

## S48 — NUM_PREDICT Removal + PT-001 Few-Shot Adversarial Examples

**Status:** Task 1 DEPLOYED+VERIFIED. Task 2 REPO-ONLY (main modelfile only).

**Changes:**
- `/home/pi/iris_config.json` — `NUM_PREDICT: 200` removed. Persisted to SD (md5 match). assistant.py restarted — `[INFO] Ready.` Tiered classifier now controls response length.
- `ollama/iris_modelfile.txt` — PT-001 few-shot block (8 examples) added after ANGRY rule, before NEVER say block.

**Model rebuild:** DEPLOYED — iris and iris-kids rebuilt on GandalfAI.

**Rollback (iris_modelfile.txt):**
```bash
git checkout -- ollama/iris_modelfile.txt
# Then rebuild: cd C:\IRIS\IRIS-Robot-Face && git pull && ollama create iris -f "C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt"
```

---

## S47 — RD-002 AMUSED Emotion — FULLY DEPLOYED

**Status:** DEPLOYED across all targets (2026-05-03). Pending: live behavior verification.

**Commit:** 734149a (pushed 2026-05-03)

**Changes deployed:**
- `pi4/core/config.py` — AMUSED added to VALID_EMOTIONS and MOUTH_MAP (→ index 2, smirk). Pi4 live, md5 verified.
- `pi4/hardware/led.py` — AMUSED: sinusoidal breathe, amber [255,160,0], floor=10 peak=80 period=1.5s gamma=1.8 duration=3s. Pi4 live, md5 verified.
- `src/main.cpp` — AMUSED added to EmotionID enum, emotionTable, parseEmotion. Firmware flashed to Teensy 4.1 (2026-05-03).
- `pi4/iris_web.html` — AMUSED button added to Emotion Test grid. Pi4 live.
- `ollama/iris-kids_modelfile.txt` — AMUSED added to valid emotion list. iris-kids model rebuilt on GandalfAI.

**Rollback:**
```bash
git checkout -- pi4/core/config.py pi4/hardware/led.py pi4/iris_web.html src/main.cpp
# Then redeploy previous Pi4 files and reflash prior firmware if already deployed/uploaded
```

---

## S46 — WoL Acknowledgement Beep — Deployed

**Status:** Complete and deployed to Pi4.

**Commit:** `2e96703` — S46: Add WoL acknowledgement beep (play_wol_beep)

**Deployment:**
- `pi4/assistant.py` copied to `/home/pi/assistant.py`, persisted to `/media/root-ro/home/pi/assistant.py`
- `pi4/hardware/audio_io.py` copied to `/home/pi/hardware/audio_io.py`, persisted to `/media/root-ro/home/pi/hardware/audio_io.py`
- MD5 verified: RAM and SD layers match for both files
- `assistant` service restarted — `active (running)`, `[INFO] Ready.` confirmed

**Behavior added:**
- When GandalfAI is offline and a WoL packet is sent, an ascending 2-tone beep (660 Hz → 880 Hz, ~360 ms) plays immediately on Pi4 speakers
- No beep when GandalfAI is already up
- `ensure_gandalf_up` gains optional `pa=None` parameter; both call sites pass `pa`

**Rollback:**
```bash
sudo cp /home/pi/assistant.py.s46bak /home/pi/assistant.py
sudo cp /home/pi/hardware/audio_io.py.s46bak /home/pi/hardware/audio_io.py
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
sudo cp /home/pi/hardware/audio_io.py /media/root-ro/home/pi/hardware/audio_io.py
sudo chown pi:pi /media/root-ro/home/pi/assistant.py /media/root-ro/home/pi/hardware/audio_io.py
sync && sudo mount -o remount,ro /media/root-ro
sudo systemctl restart assistant
```

---

## RD-001 Option 1 — Deployed

**Status:** Complete and deployed to Pi4.

**Commit:** `54d576c` — Add main-loop STOP phrase gate

**Deployment:**
- `pi4/assistant.py` was copied to Pi4 runtime path: `/home/pi/assistant.py`
- File was persisted to SD via: `/media/root-ro/home/pi/assistant.py`
- MD5 verification confirmed runtime and persisted copies matched.
- `assistant` service was restarted.
- Runtime file confirmed to contain "Main-loop STOP phrase".

**Behavior added:**
- Main loop now checks `STOP_PHRASES` after Whisper transcript normalization and before router/hallucination handling.
- Matching is boundary-aware:
  - exact STOP phrase match, or
  - STOP phrase followed by a space
- Avoids false matches such as "stopwatch", "quietly", and "cancelled".

**Known limitation:**
- This does not fix cases where Whisper hallucinates "stop" into unrelated text.
- True pre-STT abort handling still requires a future local keyword spotting/lightweight local ASR task.

**Runtime status:**
- Pi4 is live on `assistant.py` from commit `54d576c`.
- Verbal testing still pending.

**Test checklist:**
- wakeword -> "stop" should return to idle
- wakeword -> "stop talking" should return to idle
- wakeword -> "quiet please" should return to idle
- wakeword -> "cancel that" should return to idle
- wakeword -> "stopwatch" should NOT trigger STOP gate
- wakeword -> "turn red" should continue normal routing
- wakeword -> "tell me a joke" should continue normal routing

**Rollback:**
```bash
sudo cp /tmp/assistant.py.bak /home/pi/assistant.py
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
sudo chown pi:pi /media/root-ro/home/pi/assistant.py
sudo chmod 644 /media/root-ro/home/pi/assistant.py
sync && sudo mount -o remount,ro /media/root-ro
sudo systemctl restart assistant
```

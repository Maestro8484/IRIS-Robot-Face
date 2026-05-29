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
| Teensy 4.0 | S69 FLASHED+INSTALLED. DS3218MG MS24 confirmed installed. PAJ7620U2 on I2C bus. Touch3=T3 pad. S70+S72 REPO-ONLY: ServoEasing async, PAN_MIN/MAX, PAN?, all 8 PAJ7620U2 gestures (FORWARD/BACKWARD/CW/CCW). Pending user flash. Pi4 bridge/web REPO-ONLY pending DEPLOY. |
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

**Flash S70 firmware — ServoEasing async + PAN_MIN/MAX + PAN? query**

Build clean. Click Upload in PlatformIO IDE (env:teensy40). Then verify via serial at 115200:

1. Send `PAN 45` — servo moves smoothly to 45° limit (not snap).
2. Send `PAN 135` — servo moves smoothly to 135° limit.
3. Send `PAN?` — returns `PAN=<float>` (live angle from ServoEasing).
4. Wave hand in front of Person Sensor — pan tracks smoothly, no snapping.
5. Remove hand — servo holds ~6s then drifts smoothly back toward 90°.
6. Try `PAN 0` or `PAN 180` — should clamp to 45/135 (PAN_MIN/PAN_MAX enforced).

**DEPLOYMENT EXPLICITLY DELAYED** — Do not flash until gesture sensor issues from initial hardware install are resolved in a dedicated session.

After gesture issues resolved: flash S70, verify PAN limits + smooth motion, tune constants, then set `GESTURE_SENSOR_REQUIRED = True` in `pi4/core/config.py` and DEPLOY to Pi4.

### Deploy state (current)
- `servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino` — REPO-ONLY S72 (S69 on hardware; S70+S72 pending user flash)
- `servo_teensy40/teensy40_base_mount/platformio.ini` — FLASHED S69
- `servo_teensy40/README.md` — REPO-ONLY S72
- `IRIS_ARCH.md` — REPO-ONLY S72
- `docs/servo_teensy40_wiring.md` — REPO-ONLY S72
- `pi4/hardware/base_mount_bridge.py` — DEPLOYED+VERIFIED S72 (4 new gesture defaults, MUTE action, leds=None fix)
- `pi4/iris_web.py` — DEPLOYED+VERIFIED S72 (new gesture keys + MUTE in validator)
- `pi4/iris_web.html` — DEPLOYED+VERIFIED S72 (Gestures tab: PAJ7620U2 full, log inversion fix)
- `CHANGELOG.md` — REPO-ONLY S71
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

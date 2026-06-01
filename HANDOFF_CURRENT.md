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
| GandalfAI | Operational — **iris + iris-kids on qwen2.5vl:32b-q4_K_M (S77)**, Kokoro TTS (Docker port 8004). gemma3:27b-it-qat retained as rollback. |
| Teensy 4.1 | Operational — eye movement suspended during TTS. |
| Teensy 4.0 | S69 FLASHED+INSTALLED. DS3218MG MS24 confirmed installed. PAJ7620U2 on I2C bus. REPO-ONLY (pending user flash): S70 ServoEasing async + PAN_MIN/MAX + PAN?, S72 all 8 gestures, TS40-S2 gesture debounce, TS40-S1 full modular split + phantom touch3 removal. Pi4 bridge/web DEPLOYED S72. |
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

**OPEN ISSUE — T41 displays black: `DROP EYES:WAKE -- port not open`**

Teensy 4.1 serial connection dropped during S94. Multiple service restarts + T40 reflash events likely caused the bridge to lose the port. The serial number issue (udev swap) was fixed — T41 is confirmed as serial 12763490, T40 as 13625440.

**First thing next session:**
1. `ls -la /dev/ttyIRIS_EYES` — should point to ttyACM1
2. `sudo systemctl restart assistant`
3. `journalctl -u assistant -f` — watch for `[EYES] Teensy connected on /dev/ttyIRIS_EYES`
4. If still `DROP`: power-cycle T41 USB cable on Pi4, then restart assistant
5. If still failing after power cycle: check `lsusb | grep -i teensy` — T41 may need full power cycle

**S94 completed work:**
- Gestures: all 8 verified. RIGHT→WAKE, CW→MUTE, CCW→SKIP. APA102 LED feedback live.
- udev serial fix: T41=12763490, T40=13625440. RAM+SD persisted. All docs updated.
- GESTURE_SENSOR_REQUIRED=True deployed. POST 20/23 PASS.

**LAN flash scripts (no USB cable move needed going forward):**
- `.\scripts\Flash T41 Eyes.bat` — double-click to build + flash T41
- `.\scripts\Flash T40 Servo.bat` — double-click to build + flash T40
- `.\scripts\setup_ssh_keys.ps1` — run once for passwordless SSH (already done if SSH keys work)

**S90 DEPLOYED+VERIFIED (2026-05-31):**
- `pi4/iris_web.py` — Modularized. log_parser import, CSS/JS routes. md5 RAM=SD=`2e66e9920983e2b5328e304fdc56b738`
- `pi4/iris_web.html` — Trimmed (no inline CSS/JS). md5 RAM=SD=`bcfde07a6d1695fee74e880327fff628`
- `pi4/iris_web.css` — NEW. Extracted CSS. md5 RAM=SD=`be0509cb3e47464f12ee8afa0f25d2d4`
- `pi4/iris_web.js` — NEW. Extracted JS. md5 RAM=SD=`3602026caaf32e0989b4d540d197a120`
- `pi4/log_parser.py` — NEW. Extracted log parser. md5 RAM=SD=`252007ea3b48e1fde1c9edecb460d2a6`

**S89 DEPLOYED+VERIFIED (2026-05-31):**
- `pi4/core/config.py` — DEPLOYED+VERIFIED S88. GESTURE_SENSOR_REQUIRED=False (boot loop fix). md5 RAM=SD=`7bb5ad9f725eefd33ac95d6be0af3580`
- `pi4/assistant.py` — DEPLOYED. md5 RAM=SD=`19c852a908780c4bb1fe629f304b110e`
- `pi4/iris_web.py` — (superseded by S90 above)
- `pi4/iris_web.html` — (superseded by S90 above)
- `iris_config.json` — Restored to valid JSON. iris_config.json had been zeroed to 0 bytes (WinSCP direct edit accident); restored to default emotion map content. RAM=SD md5=`eda5cd406e441009677b0c460cdae8d9`.
- `src/mouth_tft.cpp` — REPO-ONLY. SILLY mouth index 9 — **requires user PlatformIO flash env:eyes**
- `src/mouth_tft.h` — REPO-ONLY.
- `resources/mouth_expressions/catalog.md` — LOCAL only.

**DEPLOYED S83+S84 (2026-05-31 session):**
- `pi4/assistant.py` — DEPLOYED+VERIFIED. STOP UDP fix live. md5 RAM=SD=`14f2028f6bc451e5bc4fd127aa6c285b`
- `pi4/hardware/audio_io.py` — DEPLOYED+VERIFIED. LOUD_STOP_THRESHOLD=9000 live. md5 RAM=SD=`b8751ee19374c606014a0b099f9079d5`
- `pi4/iris_web.html` — DEPLOYED+VERIFIED. Gesture tab cleanup live. md5 RAM=SD=`706a03aa1b510fbc8c0a1a8dcbde05d2`
- `ollama/iris_modelfile.txt` — DEPLOYED+VERIFIED. iris rebuilt on GandalfAI. ANGRY insults + 20-joke repertoire live.

**Next: Flash Teensy 4.0 — still REPO-ONLY:**
1. Build clean (env:teensy40). Click Upload in PlatformIO IDE.
2. Verify: `PAJ7620U2 0x73 ACK=YES` + `init=OK` at boot DIAG.
3. Test: LEFT or RIGHT swipe → STOP, UP → VOL+, DOWN → VOL-.
4. After verify: set `GESTURE_SENSOR_REQUIRED=True` in `pi4/core/config.py`, deploy to Pi4, confirm POST 22/22.

**IRIS Workbench Phase 2 — immediate actions:**
1. Open `tools/workbench/workbench.js`, set `ANTHROPIC_KEY` on line 5 to your Anthropic API key.
2. Run `start_workbench.bat`. Open http://localhost:8080.
3. Click "Run All" to run harness (gets fresh results; Phase 1 log was a browser download).
4. Click "Run AI Analysis" — wait 15-20s for Claude to evaluate the 5 failures.
5. Review verdict cards: confirm FIXTURE_WRONG / MODEL_WRONG for pt001_08, 09, 12, 13, 17.
6. If AI confirms pt001_08 / pt001_09 as FIXTURE_WRONG: report to Claude Code for fixture correction.
   Claude Code will write confirmed corrections to tools/workbench/fixtures/pt001_cases.json.
7. Rebuild iris model on GandalfAI to apply pt001_17 goodnight fix:
   `ollama create iris -f C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt`
   Or use Rebuild Model button in the workbench.
8. Re-run harness and confirm pt001_17 now passes (expected: NEUTRAL "Night.").
9. Update tools/workbench/analysis/phase2_analysis.md with actual AI analysis verdicts.

**Fixture corrections pending confirmation (do not apply until AI analysis reviewed):**
```
pt001_08: NEUTRAL -> AMUSED (if AI confirms FIXTURE_WRONG)
pt001_09: NEUTRAL -> AMUSED (if AI confirms FIXTURE_WRONG)
pt001_12: keep NEUTRAL (MODEL_WRONG — CURIOUS tag drift)
pt001_13: keep NEUTRAL (MODEL_WRONG — verbatim few-shot content, wrong tag)
```

**IRIS Workbench Phase 3 — next session (after Phase 2 analysis complete):**
Latency benchmarker: Tab 2 mechanical layer (Latency Bench), per-case latency tracking,
compare panel (before/after model rebuild), histogram or sparkline display.

---

**[HW-004 RESOLVED S83] GY-PAJ7620 replacement sensor arrived. Firmware orientation reset to 0°.**

Sensor is seated: VIN→3.3V, GND, SDA→pin 18, SCL→pin 19. Firmware updated (GESTURE_MOUNT_DEGREES=0). Flash TS40-S1 firmware and verify:
1. Open serial monitor (115200 baud) within 8s of power cycle.
2. Confirm `DIAG: PAJ7620U2 0x73 ACK=YES` and `DIAG: PAJ7620U2 init=OK`.
3. Test gestures: LEFT or RIGHT swipe → STOP, UP → VOL+, DOWN → VOL-.

---

**Flash TS40-S1 firmware — full modular split + phantom touch3 removal (after sensor confirmed on I2C)**

Build clean (verify no link errors — `ServoEasing.hpp` now lives only in `pan_servo.cpp`). Click Upload in PlatformIO IDE (env:teensy40). Then verify via serial at 115200:

1. Open serial monitor (115200 baud). Confirm boot DIAG: servo center=90, Person Sensor 0x62 ACK, PAJ7620U2 0x73 ACK + init OK.
2. Confirm there are **NO** `DIAG: touch3=` lines (phantom touch pad code removed).
3. Wave hand UP once — exactly one `VOL+`. Wait 1s, wave again — one more `VOL+`. Rapid repeats within 400ms → `SUPPRESSED debounce`.
4. Wave UP then immediately DOWN — second shows `SUPPRESSED cooldown` (200ms global window).
5. Wave all 8 directions (UP, DOWN, LEFT, RIGHT, FORWARD, BACKWARD, CW, CCW) — each fires exactly once per swipe.
6. Send `PAN 65` / `PAN 115` / `PAN?` — servo responds at 8 deg/sec (S75 limits: 65–115).
7. Person Sensor face tracking + center-return behave exactly as before flash.

**Contains:** S70 (ServoEasing async + PAN_MIN/MAX + PAN?) + S72 (all 8 gestures) + TS40-S2 (debounce) + TS40-S1 (modular split, touch3 removal).

After flash verified: set `GESTURE_SENSOR_REQUIRED = True` in `pi4/core/config.py` and DEPLOY to Pi4.

### Deploy state (current)
- `/etc/udev/rules.d/99-iris-teensy.rules` — DEPLOYED+VERIFIED S73. Also persisted to SD at `/media/root-ro/etc/udev/rules.d/99-iris-teensy.rules`. md5 verified.
- `pi4/hardware/teensy_bridge.py` — DEPLOYED+VERIFIED S73 (drop logging + docstring fix). md5 RAM=SD.
- `pi4/services/llm.py` — DEPLOYED+VERIFIED S74 (clean_llm_reply: stage direction strip + ellipsis collapse). md5 RAM=SD `e9e7e770c8f99597a492fd1ebeddaccd`.
- `pi4/hardware/audio_io.py` — DEPLOYED+VERIFIED S76 (emotion-driven speech animation: _EMOTION_SPEAK_FRAMES, emotion param, 350ms hold, restore_mouth_idx). md5 RAM=SD `3cef28168156bebc19c3f99a9807290c`.
- `pi4/assistant.py` — DEPLOYED+VERIFIED S76 (_current_emotion tracking, EMOTION:NEUTRAL before speech, per-emotion play_pcm_speaking, post-speech emit_emotion re-emit, follow-up loop updated). md5 RAM=SD `3317358a1e8406c75dce5cc642bff5b0`.
- `src/eyes/240x240/nordicBlue.h` — REPO-ONLY S79 (polarDist fix: `polarDist_240_125_60_0` → `polarDist_240_125_69_0` in both #include and EyeDefinition. This was root cause of iris appearing smaller than hazel despite S76 radius bump). User must flash via PlatformIO upload (env:eyes).
- `src/eyes/240x240/strikingBlue.h` — REPO-ONLY S79 (new eye index 7, generated by tablegen.py from resources/eyes/240x240/strikingBlue/). User must flash via PlatformIO upload (env:eyes).
- `src/config.h` — REPO-ONLY S79 (strikingBlue include added, array 7→8, index 7 entry added).
- `src/main.cpp` — REPO-ONLY S79 (EYE_IDX_STRIKINGBLUE=7, EYE_IDX_COUNT 7→8).
- `pi4/iris_web.html` — DEPLOYED+VERIFIED S79 (button 7 “Striking Blue” added to eye grid). md5 `9be10b546c579dc571d0c85008fffdcc` RAM=SD.
- `pi4/scripts/iris_log_export.sh` — DEPLOYED+VERIFIED S79b (SD bench JSONL append block removed — was causing unbounded SD growth, 24GB in 3 weeks). md5 `5fe88e7d8a8ca01c7fba2af8e001e9a1` RAM=SD.
- `ollama/iris_modelfile.txt` — DEPLOYED+VERIFIED S84. iris rebuilt on GandalfAI. ANGRY insults + joke repertoire live. Confirmed: `findstr ANGRY JOKES` shows lines 90,98,103,108,113,143,215.
- `pi4/hardware/audio_io.py` — DEPLOYED+VERIFIED S84. LOUD_STOP_THRESHOLD=9000. md5 RAM=SD=`b8751ee19374c606014a0b099f9079d5`.
- `tools/workbench/` — LOCAL S84 (3 new workbench tabs: Latency Bench, POST/Diag, Feature Setup). Runs on SuperMaster via start_workbench.bat.
- `pi4/assistant.py` — DEPLOYED+VERIFIED S83. STOP UDP fix live. md5 RAM=SD=`14f2028f6bc451e5bc4fd127aa6c285b`.
- `pi4/iris_web.html` — DEPLOYED+VERIFIED S83. Gesture tab cleanup live (LISTEN removed, STOP label updated). md5 RAM=SD=`706a03aa1b510fbc8c0a1a8dcbde05d2`.
- `servo_teensy40/teensy40_base_mount/paj7620.h` — REPO-ONLY S83 (GESTURE_MOUNT_DEGREES 270→0 for new GY-PAJ7620 replacement board). Pending user PlatformIO flash.
- `servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino` — REPO-ONLY TS40-S1 + S83 (S69 on hardware; S83: LISTEN removed from header comment; pending user flash)
- `servo_teensy40/teensy40_base_mount/person_sensor.h` — REPO-ONLY TS40-S1 (new file)
- `servo_teensy40/teensy40_base_mount/person_sensor.cpp` — REPO-ONLY TS40-S1 (new file)
- `servo_teensy40/teensy40_base_mount/pan_servo.h` — REPO-ONLY S75 (PAN_MIN=65, PAN_MAX=115, PAN_TRACK_SPEED=8.0 deg/sec, PAN_FILTER_ALPHA=0.15)
- `servo_teensy40/teensy40_base_mount/pan_servo.cpp` — REPO-ONLY S75 (startEaseTo speed-based, isMoving guard removed, EASE_LINEAR tracking, low-pass filteredPan, detach-at-idle torque release)
- `servo_teensy40/teensy40_base_mount/diag.h` — REPO-ONLY TS40-S1 (new file)
- `servo_teensy40/teensy40_base_mount/paj7620.h` — REPO-ONLY TS40-S2 (new file)
- `servo_teensy40/teensy40_base_mount/paj7620.cpp` — REPO-ONLY TS40-S2 (new file)
- `servo_teensy40/teensy40_base_mount/platformio.ini` — FLASHED S69
- `servo_teensy40/README.md` — REPO-ONLY TS40-S1 (touch3 line removed, modular note)
- `IRIS_ARCH.md` — REPO-ONLY TS40-S1 (pin 15 / touch3 removed, LISTEN kept)
- `docs/servo_teensy40_wiring.md` — REPO-ONLY S72
- `pi4/hardware/base_mount_bridge.py` — DEPLOYED+VERIFIED S72 (4 new gesture defaults, MUTE action, leds=None fix)
- `pi4/iris_web.py` — DEPLOYED+VERIFIED S88. S87 emotion_map int-cast fix + [EMAP] debug. md5 RAM=SD=`49e798af34d0efd0469938c68133f67a`.
- `pi4/iris_web.html` — DEPLOYED+VERIFIED S72 (Gestures tab: PAJ7620U2 full, log inversion fix)
- `CHANGELOG.md` — REPO-ONLY TS40-S1
- `CLAUDE.md` — REPO-ONLY S69
- `docs/sysmap.json` — NOW TRACKED (un-gitignored TS40-S1). TS40-S1 edits: touch3 constants/pin 15 removed.
- `src/sleep_cfg.h`, `src/sleep_renderer.h`, `src/mouth_tft.cpp`, `src/main.cpp` — FLASHED (Teensy 4.1 S65)
- `pi4/iris_post.py` — DEPLOYED+VERIFIED S82 (L4 JSONDecodeError FAIL→WARN — corrupt config no longer blocks boot). md5 RAM=SD `7db8ccfe9f1802f0addbd2a601da5cd0`.
- `pi4/core/config.py` — DEPLOYED+VERIFIED S67
- `pi4/assistant.py` — DEPLOYED+VERIFIED S67
- `pi4/iris_web.py` — DEPLOYED+VERIFIED S67
- `pi4/iris_web.html` — DEPLOYED+VERIFIED S67
- `pi4/scripts/iris_log_export.sh` — DEPLOYED+VERIFIED S67
- S65/S66/S67/S68 commits pushed to GitHub. S69 pending push.

### Other pending
- **RD-003** — Duplicate sleep log cleanup (low priority)
- **Codex review carry-forward** — `tests/test_integration_smoke.py` is a legacy standalone import-time script, excluded from pytest collection by `pytest.ini`. Convert to pytest or retire in a future task. (All other Codex CDX-1..CDX-5 Open Questions resolved — see CHANGELOG "Claude Review of Codex Session — 2026-05-29".)

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

---

## S88 cont. — Stale comment + dead code cleanup (REPO-ONLY, pending deploy)

**Status:** DEPLOYED+VERIFIED — 2026-05-31. MD5 RAM=SD confirmed. Service restarted and logs verified.

**Files changed:**
- `pi4/assistant.py` — call site `return_to_sleep()` replaced with `_do_sleep(teensy, leds)`
- `pi4/hardware/base_mount_bridge.py` — fallback port `/dev/ttyACM1` → `/dev/ttyIRIS_SERVO`

**DEPLOY (after verification passes):**

```bash
# Pi4 deploy — assistant.py
sudo cp /home/pi/assistant.py /home/pi/assistant.py.s88commentfix.bak
# sftp_write pi4/assistant.py → /tmp/assistant.py, then:
sudo cp /tmp/assistant.py /home/pi/assistant.py
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
sudo chown pi:pi /media/root-ro/home/pi/assistant.py
sudo chmod 644 /media/root-ro/home/pi/assistant.py
sync
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/assistant.py /media/root-ro/home/pi/assistant.py

# Pi4 deploy — base_mount_bridge.py
sudo cp /home/pi/hardware/base_mount_bridge.py /home/pi/hardware/base_mount_bridge.py.s88commentfix.bak
# sftp_write pi4/hardware/base_mount_bridge.py → /tmp/base_mount_bridge.py, then:
sudo cp /tmp/base_mount_bridge.py /home/pi/hardware/base_mount_bridge.py
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/hardware/base_mount_bridge.py /media/root-ro/home/pi/hardware/base_mount_bridge.py
sudo chown pi:pi /media/root-ro/home/pi/hardware/base_mount_bridge.py
sudo chmod 644 /media/root-ro/home/pi/hardware/base_mount_bridge.py
sync
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/hardware/base_mount_bridge.py /media/root-ro/home/pi/hardware/base_mount_bridge.py

# Restart service
sudo systemctl restart assistant
journalctl -u assistant -n 20 --no-pager
```

**Verify in logs:**
- `[INFO] TTS        : Kokoro @ 192.168.1.3:8004` appears
- `[INFO] Base mount :` appears
- `[INFO] Ready.` appears
- No `NameError` or `return_to_sleep` references

**CHANGELOG status after deploy:** Change `REPO-ONLY` → `DEPLOYED`. Add md5 hashes.

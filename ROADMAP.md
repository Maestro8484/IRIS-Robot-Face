<!-- Forward-looking work only. Do not add completed items. Completed history is in CHANGELOG.md. -->

# IRIS Roadmap

All items below are active or queued. Completed work is in `CHANGELOG.md`.

---

## PT-001 — Few-Shot Adversarial Examples in Modelfiles

**Status:** DEPLOYED (S48) — both modelfiles updated, both models rebuilt on GandalfAI. Verification (live adversarial testing) pending.

**Goal:** Teach IRIS to handle negative-language inputs (insults, identity challenges, dismissals) with consistent AMUSED/NEUTRAL responses via few-shot examples. Examples provide concrete in-context demonstrations to reinforce the persona prose already in the EMOTIONAL STATE AND EXPRESSION section.

**Implemented (S48):**
- `ollama/iris_modelfile.txt` — 8 few-shot examples added after ANGRY emotion rule, before NEVER say block. Covers: direct insults (AMUSED + brief redirect), identity challenges ("You're ChatGPT", "You're just an AI" → AMUSED), dismissals ("Shut up", "Go away" → NEUTRAL + one-word hold).

**Remaining (requires authorization):**
- `ollama/iris-kids_modelfile.txt` — Needs kid-appropriate version: same AMUSED structure but warmer tone with playful redirect (not dry economy). Assessment complete; edit awaiting user approval.
- Model rebuild on GandalfAI: `ollama create iris` and `ollama create iris-kids` after kids edit approved.

**Deployment gate:** GandalfAI — requires explicit `DEPLOY`. Run `git pull` on GandalfAI repo at `C:\IRIS\IRIS-Robot-Face\`, then `ollama create` from that path.

**Rollback:**
```bash
git checkout -- ollama/iris_modelfile.txt ollama/iris-kids_modelfile.txt
# Rebuild from prior commit on GandalfAI if models already rebuilt.
```

**Files:** `ollama/iris_modelfile.txt`, `ollama/iris-kids_modelfile.txt`

---

## RD-001 — Stop/Cancel Pre-STT Intercept

**Status:** Complete — Option 1 (post-STT STOP phrase gate) deployed to Pi4 (commit 54d576c, 2026-05-02). Pre-STT RMS intercept (Option 2) deferred — not required.

**Problem:** Whisper hallucinates on very short post-wakeword audio (< ~0.5s). Single-word utterances like "stop" are transcribed as unrelated phrases. The intent router then classifies the hallucinated text rather than the intended command, causing IRIS to respond incorrectly instead of aborting.

**Goal:** For post-wakeword audio bursts below an RMS or duration threshold, route directly to a local keyword match ("stop", "quiet", "cancel") without invoking Whisper. If matched, execute the command. If not matched, fall through to Whisper normally.

**Impact:** IRIS will reliably respond to short abort commands mid-interaction, improving trust and responsiveness during real household use.

**Risk:** Threshold tuning — too aggressive a gate will skip legitimate short utterances. Threshold must be validated on real household audio before deployment.

**Deployment gate:** Pi4 — requires explicit user authorization. No GandalfAI changes needed.

**Rollback:** Revert the changed Pi4 files to prior commit and redeploy to Pi4.

**Files:** `pi4/assistant.py`, possibly `pi4/services/stt.py`; `pi4/core/intent_router.py` only if command routing is changed.

---

## RD-002 — AMUSED Emotion: Full Implementation

**Status:** FULLY DEPLOYED (2026-05-03) — Pi4, Teensy 4.1, GandalfAI iris-kids all live.

**Decision:** Full implementation chosen over removal. AMUSED = dry amusement at teasing, insults, or identity challenges — distinct from CONFUSED (genuinely baffling input).

**Implemented (S47):**
- `pi4/core/config.py` — AMUSED added to VALID_EMOTIONS; MOUTH_MAP → index 2 (smirk/CURIOUS expression)
- `pi4/hardware/led.py` — AMUSED: sinusoidal breathe, amber [255,160,0], floor=10, peak=80, period=1.5s, gamma=1.8, duration=3s (special case in show_emotion)
- `src/main.cpp` — AMUSED added to EmotionID enum (=8), emotionTable ({0.55f, false, 3000}), parseEmotion
- `pi4/iris_web.html` — AMUSED button added to Emotion Test grid
- `ollama/iris_modelfile.txt` — AMUSED already present and correctly described; no change needed
- `ollama/iris-kids_modelfile.txt` — AMUSED added to valid emotion list

---

## RD-003 — Duplicate Sleep Log Cleanup

**Status:** Open — Low priority

**Problem:** `/home/pi/iris_sleep.log` (Pi4 root home) may duplicate `/home/pi/logs/iris_sleep.log`. Duplicate logs waste space and create ambiguity when diagnosing sleep/wake issues.

**Goal:** Confirm which log is actively written by the current sleep/wake system. If duplicate, remove the stale path and update any log-reading references to point to the canonical location.

**Impact:** Cleaner diagnostics. Less ambiguity when tracing sleep-related bugs.

**Risk:** Low — log file only. No runtime behavior changes unless a log reader references the stale path.

**Deployment gate:** Pi4 — requires explicit user authorization. Use standard `/media/root-ro` persistence pattern documented in `CLAUDE.md`.

**Rollback:** Restore deleted log file, symlink, or path reference from prior commit or Pi4 backup if any log reader depends on the removed path.

**Files:** Pi4 runtime only — `/home/pi/iris_sleep.log`, `/home/pi/logs/iris_sleep.log`, relevant `pi4/` sleep/wake scripts if they reference the log path.

---

## RD-004 — Teensy Hardware/Firmware Pass (Batch 2)

**Status:** Open — blocked until Pi4 runtime is stable

**Problem:** Teensy 4.1 firmware has known candidate hardening items that have not been addressed: sleep render pointer guards, serial overflow discard-and-log, and potential mouth command gating during sleep.

**Goal:** Implement Batch 2 hardening scope after confirming Pi4 runtime stability. Each Teensy change must be a separate firmware commit and a separate PlatformIO build.

**Impact:** More robust embedded behavior — prevents display corruption during unexpected state transitions and overflow conditions. Improves IRIS's reliability as a persistent display device.

**Risk:** Firmware changes are harder to roll back than Python changes. Each Teensy change must be independently validated before proceeding to the next.

**Deployment gate:** Firmware only — user uploads via PlatformIO. No Pi4 or GandalfAI deployment needed for firmware-only changes.

**Rollback:** Re-flash prior firmware build via PlatformIO.

**Files:** `src/main.cpp`, possibly new Teensy utility files. Do not touch `src/eyes/EyeController.h` without explicit instruction.

---

## RD-005 — GandalfAI Inference Settings Review

**Status:** Open — low priority, post-Batch D

**Problem:** Current inference settings (temperature, num_ctx, etc.) have not been reviewed since gemma3:27b-it-qat was adopted. Defaults may not be optimal for IRIS's conversational persona and latency targets.

**Goal:** Audit `ollama/iris_modelfile.txt` PARAMETER block. Validate temperature (currently 0.82), num_ctx (currently ≤ 4096 per VRAM constraint), and any other relevant parameters. Adjust and rebuild iris model if warranted.

**Impact:** May improve response quality, character consistency, or latency. Risk of regression if changes are not validated against real household use.

**Risk:** Parameter changes require iris model rebuild on GandalfAI. A poorly chosen temperature or context window can degrade persona quality or increase latency.

**Deployment gate:** GandalfAI — requires explicit `DEPLOY`. Do not raise num_ctx above 4096 (VRAM constraint: Kokoro ~2GB + gemma3:27b-it-qat ~14.1GB = ~16.1GB of 24GB).

**Rollback:** Revert `ollama/iris_modelfile.txt` to prior commit. Rebuild iris model on GandalfAI.

**Files:** `ollama/iris_modelfile.txt`

---

## RD-006 — Custom Wakeword Experiment (Future)

**Status:** Open — deferred, no active timeline

**Problem:** The production wakeword (`hey_jarvis`) is functional but not IRIS-specific. A custom wakeword trained on real household voice samples would improve ownership and recognition accuracy.

**Goal:** When ready, run a new experiment using real household voice samples, single-model training, and live Pi4 validation before any production deployment. Prior experiments (details in `CHANGELOG.md`) did not meet production reliability requirements.

**Impact:** A reliable custom wakeword would complete IRIS's identity as a self-contained robot assistant with a distinct name.

**Risk:** Real-world reliability is difficult to achieve. Prior experiments failed. Do not deploy any experimental wakeword to production without explicit user approval, live Pi4 state confirmation, clean process restart, and one-model-at-a-time testing.

**Deployment gate:** Pi4 — requires explicit user authorization. One wakeword model tested at a time.

**Rollback:** Restore `hey_jarvis` configuration on Pi4 and restart wakeword service.

**Files:** Pi4 wakeword configuration scripts. `iris_config.json` is protected — do not touch without explicit instruction.

---

## RD-007 — Bench Trend Viewer in iris_web

**Status:** Open — deferred, blocked on JSONL data accumulation (deploy S50 first)

**Problem:** `iris_bench.jsonl` (added S50) stores per-turn timing data but is only readable via SSH. The existing Bench tab in the web UI shows current-session timings from journald only. No trend view exists.

**Goal:** Add a new panel or sub-tab in the Bench page that reads `iris_bench.jsonl`, parses all records, and displays a trend chart (e.g., `total_ms` over time, with `gandalf_was_cold` flagged). Allow filtering by route, date range. Minimum viable: table view of last 25 records with stage columns.

**Impact:** User can identify latency trends and outliers without SSH. Can compare slow-turn data across days/weeks.

**Risk:** iris_web.py runs as root on Pi4 overlayfs. Reading a log file is low-risk. Chart rendering likely needs a JS library (Chart.js) loaded from CDN or bundled.

**Blocked on:** S50 deploy so `iris_bench.jsonl` has data to read. At least ~1 week of normal use (~25-35 turns) recommended before building the viewer.

**Deployment gate:** Pi4 — iris_web.py + iris_web.html. Standard `/media/root-ro` persist pattern.

**Files:** `pi4/iris_web.py` (`/api/bench_jsonl` endpoint), `pi4/iris_web.html` (Bench tab panel).

---

## HW-001 — Teensy 4.1 Activity LED Suppression (Pin 13 / SPI SCK conflict)

**Status:** DEFERRED — blocked on power distribution PCB rewiring.

**Priority:** HIGH — LED is visibly distracting during normal operation.

**Problem:** Teensy 4.1 pin 13 is simultaneously the built-in activity LED and the SPI SCK line for the GC9A01A eye displays. The eye render loop runs at ~60fps, keeping SPI active continuously. The SCK toggling causes the LED to glow solid during all eye operation. Software suppression (`pinMode(13, OUTPUT); digitalWrite(13, LOW)`) has no effect — the SPI hardware peripheral immediately reclaims pin 13 control.

**Fix:** Cut the LED/SCK solder jumper on the underside of the Teensy 4.1 board. This disconnects the LED pad from pin 13 without affecting SPI function. One-time physical mod, ~10 seconds with a hobby knife.

**Blocked on:** The Teensy 4.1 is header-soldered onto the main power supply distribution PCB. Accessing the underside of the Teensy (where the solder jumper sits) requires desoldering it from the PCB headers, or doing the cut in-situ with limited clearance. The power distribution PCB is scheduled for a large rewiring — cut the LED jumper during that work before re-seating the Teensy.

**No code change required.** The two-line stub (`pinMode(13, OUTPUT); digitalWrite(13, LOW)`) was added and then removed in S54 — confirmed ineffective.

**Files:** None (hardware-only fix).

---

## HW-002 — Servo Pico USB Flash Inaccessible (Power Distribution PCB)

**Status:** DEFERRED — blocked on power distribution PCB rewiring.

**Priority:** HIGH — improved servo tracking code (confidence gate, dead zone, face-lost return) is REPO-ONLY and cannot be flashed until resolved.

**Problem:** The Raspberry Pi Pico (servo pan/tilt controller) is header-soldered onto the main power supply distribution PCB. Two hardware issues block USB flashing:

1. **RUN pin miswired to enclosure on/off switch** — The switch pulls the RUN pin (physical pin 30) to GND when ON, holding the Pico in hard reset. The Pico only runs when the switch is OFF. Correct wiring: the switch belongs in the VSYS (pin 39) power input line. RUN should be left unconnected; the internal pullup holds it high.

2. **BOOTSEL button physically inaccessible** — The Pico is soldered to the PCB with components around it. The BOOTSEL button cannot be reached. Attempted workaround: use the RUN switch as a reset trigger while holding BOOTSEL — Windows Device Manager briefly refreshed (USB handshake partially detected) but no RPI-RP2 mass storage drive appeared. WinUSB driver for RP2040 BOOTSEL mode likely also needs to be installed via Zadig.

**Current state:** Servo tracking (face detection, pan/tilt) IS functional on the old firmware. Improved code in `servo_pico/IRIS-BaseServoControlViaPerson_Sensor.ino` (commit `c37f148`) is REPO-ONLY.

**Fix during PCB rewiring:**
1. Move the on/off switch wire from RUN (pin 30) to the VSYS (pin 39) power input line.
2. Leave RUN unconnected.
3. If RPI-RP2 drive still does not appear: install WinUSB driver for RP2040 BOOTSEL via [Zadig](https://zadig.akeo.ie) — Options → List All Devices → select "RP2 Boot" → install WinUSB.
4. Flash `servo_pico/IRIS-BaseServoControlViaPerson_Sensor.ino` — Arduino IDE (board: Raspberry Pi Pico, Earle Philhower RP2040 core) or PlatformIO (`upload_protocol = picotool`).
5. Verify: smooth pan/tilt tracking, no jitter on small movements, back-of-head or low-confidence detections ignored, face-lost → holds 2.5s → slow center drift after 8s.

**Blocked on:** Same power distribution PCB rewiring event as HW-001. Do both fixes in the same work session.

**Files:** `servo_pico/IRIS-BaseServoControlViaPerson_Sensor.ino` (REPO-ONLY, commit `c37f148`).

---

## RD-009 — Pico W USB Serial Touch Sensor Integration

**Status:** PLANNED — full spec in `review/HANDOFF_PICO_WIFI_TOUCH.md`.

**Priority:** HIGH

**Summary:** Add two additional TTP223B touch sensors to the Pico W. Pico communicates with Pi4 via USB serial (micro-USB → Pi4 USB port) — no WiFi needed.

- **Touch 1 (GPIO 15, existing):** Servo enable/disable toggle.
- **Touch 2 (GPIO 13, physical pin 17):** Hold to change volume; hold again reverses direction. Sends `VOL_UP` / `VOL_DOWN` over serial every 200ms while held.
- **Touch 3 (GPIO 14, physical pin 19):** Short tap = `STOP` (interrupt TTS). Long hold >1s = `LISTEN` (trigger wakeword+mic without speaking).

**Architecture:** Pico W USB CDC serial → `/dev/ttyACM0` on Pi4 → background listener thread in assistant.py dispatches commands. Same pattern as existing TeensyBridge.

**Pico W board power:** Pi4 USB powers the Pico board. Servo still needs its own 5V rail.

**Implementation order:**
1. Read assistant.py in full — understand TeensyBridge pattern, TTS stop, volume, listen trigger.
2. Add Touch 2/3 + `Serial.println()` commands to Pico W sketch. Flash via Windows COM10.
3. Add pico_listener thread to assistant.py, wired to existing volume/stop/listen mechanisms.
4. Deploy assistant.py to Pi4 per standard persist protocol.
5. Verify: `ls /dev/ttyACM0` on Pi4, tail logs, test each touch.

**Files:** `servo_pico/.../IRIS-BaseServoControlViaPerson_Sensor.ino`, `pi4/assistant.py`, `pi4/iris_web.py` (only if routes missing), `docs/sysmap.json`, `IRIS_ARCH.md`.

# IRIS Robot Face — Handoff Snapshot
**Date:** 2026-03-27 (session 2, evening)**Branch:** iris-ai-integration
**Last commits:** `0bb76e6` (sleep fix), `34815b6` (prev snapshot)

---

## System Architecture

| Component | Hardware | Role |
|---|---|---|
| Teensy 4.0 | USB serial `/dev/ttyACM0` | Eye renderer, mouth matrix, person sensor |
| Pi4 | 192.168.1.200 | Voice assistant, wakeword, LLM bridge |
| Gandalf (workstation) | 192.168.1.3 | Ollama LLM (`jarvis`/`jarvis-kids`), Whisper STT, Piper TTS |
| GC9A01A 1.28" TFTs (×2) | SPI | Left/right eye displays (240×240) |
| MAX7219 32×8 matrix | SPI | Mouth expressions |
| Person Sensor | I2C | Face detection + tracking |
| APA102 RGB LEDs (×3) | SPI | Emotion status indicator |

**Pi4 SSH:** `ssh pi@192.168.1.200` (password: `ohs`) — overlayFS read-only SD, always persist changes:
```bash
sudo mount -o remount,rw /media/root-ro
cp /home/pi/<file> /media/root-ro/home/pi/<file>
sudo mount -o remount,ro /media/root-ro
# verify: md5sum /home/pi/<file> && md5sum /media/root-ro/home/pi/<file>
```

---

## Serial Protocol

**Pi4 → Teensy:**
- `EMOTION:HAPPY/NEUTRAL/CURIOUS/ANGRY/SLEEPY/SURPRISED/SAD/CONFUSED`
- `EYES:SLEEP` — activate starfield + snore mouth
- `EYES:WAKE` — restore normal eye rendering
- `EYE:n` — switch eye definition (0–6)
- `MOUTH:n` — set mouth pattern index (0–8)

**Teensy → Pi4:**
- `FACE:1` — face detected
- `FACE:0` — face lost

**Architecture rule:** Only `assistant.py`'s `TeensyBridge` owns `/dev/ttyACM0`. All other processes (cron, web UI) send commands via UDP to `127.0.0.1:10500` → `start_cmd_listener()`.

---

## Sleep State Machine

**Source of truth:** `/tmp/iris_sleep_mode` flag file

**Sleep entry paths:**
1. Cron 9PM → `iris_sleep.py` → UDP EYES:SLEEP → CMD listener → Teensy + sets `_eyes_sleeping=True` + creates flag
2. Voice: "close your eyes" → EYES:SLEEP sent, `_eyes_sleeping=True` set, flag created
3. Web UI → `iris_web.py` → UDP EYES:SLEEP → CMD listener (same path as #1)

**Wake entry paths:**
1. Wakeword during sleep → handler checks `os.path.exists('/tmp/iris_sleep_mode')` → EYES:WAKE + MOUTH:0 + removes flag + "Good morning."
2. Voice: "wake your eyes" → EYES:WAKE + `_eyes_sleeping=False` + removes flag
3. Any voice interaction while `_eyes_sleeping=True` → auto-wake
4. Cron 7:30AM → `iris_wake.py` → UDP EYES:WAKE → CMD listener

**Crontab (pi user):**
```
0 21 * * * /usr/bin/python3 /home/pi/iris_sleep.py >> /var/log/iris_sleep.log 2>&1
30 7 * * * /usr/bin/python3 /home/pi/iris_wake.py >> /var/log/iris_sleep.log 2>&1
```

---

## Key Files

### Teensy Firmware (PlatformIO)
| File | Purpose |
|---|---|
| `src/main.cpp` | Main loop: serial handler, person sensor, sleep/wake dispatch |
| `src/eyes/EyeController.h` | Eye motion, eyelid tracking, setTargetPosition fix |
| `src/mouth.h` | MAX7219 mouth patterns + sleep/snore animation |
| `src/sleep_renderer.h` | Deep space starfield renderer for both TFTs |
| `src/config.h` | Eye definition array (indices 0–6) |
| `src/eyes/240x240/nordicBlue.h` | Default eye (squint=1.0) |
| `src/eyes/240x240/hazel.h` | Eye index 3 (squint=1.0) |
| `src/eyes/240x240/bigBlue.h` | Eye index 6 (squint=1.0) |

**Eye index map:**
- 0 = nordicBlue (default), 1 = flame (ANGRY), 2 = hypnoRed (CONFUSED)
- 3 = hazel, 4 = blueFlame1, 5 = dragon, 6 = bigBlue

### Pi4 Files
| File | Purpose |
|---|---|
| `/home/pi/assistant.py` | Main voice assistant (1605 lines) |
| `/home/pi/iris_sleep.py` | Cron sleep script (UDP, no direct serial) |
| `/home/pi/iris_wake.py` | Cron wake script (UDP, no direct serial) |
| `/home/pi/iris_web.py` | Flask web UI (port 5000) |
| `/home/pi/iris_config.json` | Runtime config overrides (loaded at startup) |
| `/home/pi/iris_web.html` | Web UI frontend |

### Gandalf (192.168.1.3) — No changes this session
- Ollama models: `jarvis` (adult), `jarvis-kids` (kids mode)
- Wyoming Whisper STT: port 10300
- Wyoming Piper TTS: port 10200

---

## Changes This Session

### Committed `0bb76e6`
1. **`src/main.cpp`** — Removed 5 `[TRK]` debug serial prints (tracking diagnosis, no longer needed)
2. **`src/mouth.h`** — Sleep intensity `0x02 → 0x04` (~13% → ~28% brightness, was too dim)
3. **`pi4/iris_sleep.py`** — Switched from direct serial to UDP (`127.0.0.1:10500`). Previously conflicted with TeensyBridge; likely caused Pi hang.
4. **`pi4/iris_wake.py`** — Same UDP switch.
5. **`assistant.py` CMD listener** — Now syncs `_eyes_sleeping` flag and `/tmp/iris_sleep_mode` when forwarding `EYES:SLEEP`/`EYES:WAKE`. Previously state was desynchronized between cron-triggered and voice-triggered sleep paths.

### Pending commit (this snapshot session)
6. **`src/eyes/240x240/nordicBlue.h`** — `squint 0.5 → 1.0`. At center gaze, upper lid drops from row 90 to row 60 (from 37% → 25% display coverage), matching iris top edge for a wide-awake appearance. Math: `iy = 120 - iris.radius*squint`; `upperQ = (upperClosed - iy)/(upperClosed - upperOpen)`.
7. **`src/eyes/240x240/hazel.h`** — Same squint fix.
8. **`src/eyes/240x240/bigBlue.h`** — Same squint fix.
9. **`assistant.py`** — `set_volume(110)` added to `main()` startup.
10. **`/home/pi/iris_config.json`** — `OWW_THRESHOLD: 0.85` (was 0.75), `VOL_MAX: 110` (was 127). Persisted to SD.

---

## Current Known Issues / TODO

### HIGH PRIORITY
- [ ] **Person sensor brief eye-open during sleep** — When person sensor detects a face during sleep mode, user reports one eye briefly opens then the other (sequential update artifact?). Firmware sleep guard `if (!eyesSleeping)` is correct. Add `[SLEEP]` debug serial output in `loop()` to confirm `eyesSleeping=true` when person sensor fires. Possible cause: `updateChangedAreasOnly(false)` + `fillScreen` skipping partial render in some edge case. Could also be cosmetic — `renderSleepFrame` updates left then right sequentially with no buffer swap.
- [ ] **"10-min re-sleep" root cause unconfirmed** — No code timer found. Cron only fires at 9PM/7:30AM. Prior theory: Piper TTS in old iris_sleep.py was blocking, causing iris_sleep.py process to appear hung → Pi appeared hung. UDP fix eliminates serial conflict. If re-sleep recurs, add `[SLEEP]` serial logging to Teensy to capture any stray EYES:SLEEP commands.

### MEDIUM PRIORITY
- [ ] **APA102 indigo breathe animation during sleep** — Not implemented. LED stays in last emotion color during sleep. Add `leds.show_sleep()` call to wakeword sleep handler and CMD listener EYES:SLEEP path. Color: indigo (0x4B, 0x00, 0x82) pulsing.
- [ ] **`nordicBlue/config.eye` pupil sync** — The `.h` has min=0.21, max=0.47 (−15% from generated values) but `config.eye` still has min=0.25, max=0.55. Running `genall.py` would overwrite the manual edit. Either update `config.eye` to match or add a post-gen fixup step. Same for hazel, bigBlue.
- [ ] **`EMOTION:CONFUSED` not in assistant.py emotion→serial map** — The Teensy handles it (swaps to hypnoRed eye) but assistant.py never sends it. Add to `VALID_EMOTIONS` and `MOUTH_MAP`.
- [ ] **`MOUTH:n` not sent alongside `EMOTION:n`** — `emit_emotion()` sends `EMOTION:X` + `MOUTH:MOUTH_MAP[X]` separately. Currently works but the mouth map could be more expressive. Review mouth pattern assignments.

### LOW PRIORITY
- [ ] **`EYE:n` commands from assistant.py** — Currently only accessible from web UI. Add voice trigger: "switch to hazel eyes", etc.
- [ ] **Go public on GitHub** — Strip ElevenLabs API key from `iris_web.py` and `assistant.py` before making repo public.

---

## Local TTS Consideration (Piper vs Mixtral-based micro-LLM)

**Current TTS stack:**
- Main responses: ElevenLabs API (cloud, high quality, `eleven_turbo_v2_5`)
- Sleep/wake announcements: Wyoming Piper local (`en_US-ryan-high.onnx`) on Gandalf

**Option A — Piper (recommended, already installed):**
- Model: `en_US-ryan-high.onnx` or `en_US-lessac-high.onnx`
- Latency: ~200ms on Gandalf (already wired as Wyoming service on port 10200)
- Already used for "Good morning." / "Goodnight." via subprocess in iris_sleep/wake.py
- assistant.py has full Wyoming Piper client code (`synthesize()`) — just change `ELEVENLABS_ENABLED=false` in iris_config.json to fall back to Piper for all responses

**Option B — Kokoro TTS (new, high quality, local):**
- ~82M parameter model, runs well on CPU/GPU
- Install: `pip install kokoro-onnx`; model download ~300MB
- Comparable quality to ElevenLabs at lower latency than current cloud round-trip
- Not yet integrated; would require new `synthesize_kokoro()` function + fallback logic

**Option C — Mistral/Llama micro-LLM for TTS preprocessing:**
- Using a tiny model (e.g., `smollm2:135m` on Ollama) to preprocess LLM replies before TTS — remove markdown, expand abbreviations, improve prosody hints
- Would reduce ElevenLabs "robotic" artifacts on long responses
- Trivial to add: one Ollama call before `synthesize(reply)` with a cleanup prompt

**Recommendation:** Try `ELEVENLABS_ENABLED=false` first via web UI to test Piper quality. If acceptable, disable ElevenLabs permanently (saves API cost). Kokoro is worth evaluating when Gandalf has spare cycles.

---

## Flash Workflow

```bash
cd C:/Users/SuperMaster/Documents/PlatformIO/IRIS-Robot-Face
pio run -t upload    # build + trigger upload dialog
# press PROG button on Teensy when prompted
# test: open serial monitor at 115200
```

## Pi4 Restart

```bash
sudo systemctl restart assistant
# or full reboot:
sudo reboot
```

---

## Audit Results (This Session)

### Firmware — No Critical Issues Found
- `main.cpp` EYES:SLEEP/WAKE handlers: correct — `updateChangedAreasOnly(false/true)` bracketing prevents SPI DMA lockup
- `EyeController.h::setTargetPosition()`: eyeOldX/Y seed fix is correct — smoothstep interpolation correctly seeds from current interpolated position
- `renderSleepFrame()`: correct guard structure — `if (eyesSleeping) { render; return; }` prevents eye engine from running
- `mouth.h::mouthSetSleepIntensity()`: brightness now 0x04 (~28%) — correct for visibility
- `personSensor` block: `reportFaceState()` called unconditionally (correct — needed for FACE:1/0 serial output), tracking inside `if (!eyesSleeping)` guard (correct)
- Serial buffer: 32 bytes max command length — adequate for all current commands
- No watchdog timer, no sleep inactivity timer in Teensy firmware

### Pi4 — No Critical Issues Found
- `iris_sleep.py`/`iris_wake.py`: UDP path eliminates serial race with TeensyBridge
- CMD listener: `_eyes_sleeping` + flag file now in sync for all paths
- `_context_watchdog`: 300s timeout clears conversation only, does NOT trigger EYES:SLEEP — confirmed safe
- `wait_for_wakeword_or_button()`: sleep-mode check at line ~1381 correct — checks flag file, sends EYES:WAKE, removes flag, plays "Good morning.", continues
- `iris_config.json`: OWW_THRESHOLD=0.85, VOL_MAX=110, persisted to SD
- ElevenLabs API key in plaintext: `sk_752184d377335347d38c185ba56a1bebe9deba4da50ce082` — **must remove before public GitHub**

### Gandalf — Not Accessed This Session
- No changes. Ollama models `jarvis`/`jarvis-kids` unchanged.
- Wyoming services (Whisper/Piper) running as systemd services.

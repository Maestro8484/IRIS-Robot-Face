# IRIS Robot Face — Handoff Snapshot
**Date:** 2026-04-03
**Session:** 1
**Branch:** `main`
**Last commit:** `51e4bd3` (fix: show_sleep wiring, state.eyes_sleeping reset, NUM_PREDICT 120, iris_sleep canonical, ELEVENLABS default False)
**Repo:** `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face`

---

## HOW TO RESUME

Open Claude Code in the IRIS repo directory. The SessionStart hook auto-loads SNAPSHOT_LATEST.md.
If context seems missing: `python3 .claude/hooks/session_start.py`

---

## 1. SYSTEM ARCHITECTURE

| System | IP | Credentials | Role |
|---|---|---|---|
| Pi4 (IRIS / Jarvis) | 192.168.1.200 | pi / ohs | Voice pipeline, LEDs, camera, Teensy serial |
| GandalfAI | 192.168.1.3 | gandalf / 5309 | Ollama LLM, Whisper STT, Piper TTS, Chatterbox TTS, RTX 3090 |
| Desktop PC | 192.168.1.103 | SuperMaster | PlatformIO firmware, VS Code, Claude Desktop |
| Teensy 4.0 | USB → /dev/ttyACM0 on Pi4 | N/A | Dual GC9A01A 1.28" round TFT eyes, MAX7219 mouth |
| Synology NAS | 192.168.1.102 | Master / Gateway!7007 | SSH port 2233. Backup: \\192.168.1.102\BACKUPS\IRIS-Robot-Face\ |

**Claude Desktop MCP filesystem scope:** `C:\Users\SuperMaster`
**SSH MCP tools:** `ssh-pi4` (192.168.1.200), `ssh-gandalf` (192.168.1.3), `ssh` (NAS, port 2233)
**SSH auth:** Pi4 uses **password auth only** — key auth fails. Always connect with `username: pi`, `password: ohs`.
**GandalfAI:** Windows machine. No `df`, `head`, `grep` — use PowerShell / findstr / dir equivalents.

---

## 2. PROJECT STATUS

**Firmware:** Flashed 2026-03-29. Sleep fully working. drawChar recursion fixed. 7-eye system. Face tracking working. **PENDING FLASH (next session): mouth.h normal intensity→0x01, PersonSensor LED disabled, sleep_renderer.h starfield boost — require USB firmware flash.**
**Sleep display:** Starfield + ZZZ animation on both TFTs confirmed working.
**Sleep LEDs:** APA102 dim indigo breathe on EYES:SLEEP. peak=26 (~10% of 255), global_bright=0xFF, floor=3. LED_SLEEP_* constants in config.py. show_sleep() now wired into CMD listener. Restores idle on EYES:WAKE. **DEPLOYED this session.**
**Mouth during sleep:** Snore animation, intensity 0x01 (~10%). Working.
**Wake from webui:** Working. Cron sleep: 9PM/7:30AM UDP path. False wakeword during cron window now ignored (button-only override).
**Voice pipeline (assistant.py):** Operational. Modular (hardware/, core/, services/, state/).
**TTS routing:** Chatterbox (primary) → ElevenLabs (disabled via iris_config.json) → Piper (fallback).
**Chatterbox server:** Running on GandalfAI. Web UI confirmed accessible at http://192.168.1.3:8004.
**Jarvis modelfile:** Updated with PARALINGUISTIC TAGS section. `ollama create jarvis` completed.
**ElevenLabs:** Disabled — `ELEVENLABS_ENABLED=False` in `/home/pi/iris_config.json` AND now default False in config.py.
**Web UI:** Chatterbox-first Voice tab live. EYE:n switching (0–6), Sleep/Wake buttons, live state polling. Port 5000.
**Face tracking:** Working. setTargetPosition seed fix in EyeController.h.
**NUM_PREDICT:** 120 in iris_config.json (overrides config.py default of 150).

---

## 3. CLAUDE CODE INFRASTRUCTURE

### Slash Commands
| Command | File | Purpose |
|---|---|---|
| `/flash` | `.claude/commands/flash.md` | Local USB flash via PlatformIO |
| `/flash-remote` | `.claude/commands/flash-remote.md` | Remote flash via Pi4 SSH |
| `/deploy` | `.claude/commands/deploy.md` | Persist Pi4 files through overlayfs to SD |
| `/snapshot` | `.claude/commands/snapshot.md` | Generate end-of-session snapshot |
| `/eye-edit` | `.claude/commands/eye-edit.md` | Eye config edit + genall.py + pupil re-apply workflow |

### iris-snapshot GitHub repo
- **Repo:** `https://github.com/Maestro8484/iris-snapshot` (private)
- **Local:** `C:/Users/SuperMaster/Documents/PlatformIO/iris-snapshot/`
- **Raw URL:** `https://raw.githubusercontent.com/Maestro8484/iris-snapshot/main/SNAPSHOT_latest.md`

### Pi4 Sudoers (all persisted to SD)
- `/etc/sudoers.d/iris_service` — passwordless sudo for systemctl stop/start/restart/status assistant
- Pi4 `pi` user has general passwordless sudo (standard Raspberry Pi default)

### Software Bootloader Entry (Teensy in enclosure)
```bash
python3 -c "import serial, time; s=serial.Serial('/dev/ttyACM0',134); time.sleep(0.5); s.close()"
```

---

## 4. CHATTERBOX TTS

### GandalfAI Setup
- **Repo cloned:** `C:\Users\gandalf\Chatterbox-TTS-Server` (devnen/Chatterbox-TTS-Server)
- **Conda env:** `chatterbox` (Python 3.12) at `C:\Users\gandalf\miniconda3\envs\chatterbox\`
- **Launch script:** `C:\Users\gandalf\Chatterbox-TTS-Server\run_server.bat`
- **Install log:** `C:\Users\gandalf\chatterbox_server.log`
- **Model:** Chatterbox Turbo (set in `config.yaml`: `repo_id: chatterbox-turbo`)
- **Exaggeration:** 0.45 (updated in `config.yaml` from 1.3; also passed per-request via /tts endpoint)
- **Port:** 8004 — Windows Firewall rule added: "Chatterbox TTS 8004"
- **requirements file used:** `requirements-nvidia.txt` (cu121, correct for RTX 3090 / Ampere)
  - Do NOT use `requirements-nvidia-cu128.txt` — that's for Blackwell RTX 5000 series only
- **Status:** Server confirmed running. Web UI accessible at http://192.168.1.3:8004.

### Monitoring / Restarting
```
# Check install progress / server log (on Gandalf or via SSH):
type C:\Users\gandalf\chatterbox_server.log

# If server is not running, restart:
wmic process call create "cmd /c C:\Users\gandalf\Chatterbox-TTS-Server\run_server.bat"

# Verify listening:
netstat -an | findstr 8004
```

### Voice Clone — PENDING UPLOAD
- Reference audio on desktop: `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face\voice_preview_snarky james bond.wav` (24.5s, stereo, 48kHz)
- Also present as `iris_voice.wav` in project root (untracked, do not commit)
- **Action required:** Go to http://192.168.1.3:8004 → Reference Audio tab → upload, rename to `iris_voice.wav`
- Pi4 config constant: `CHATTERBOX_VOICE = "iris_voice.wav"` (exact filename, with extension)

### Pi4 TTS Endpoint Used
```
POST http://192.168.1.3:8004/tts
{
  "text": "...",
  "voice_mode": "clone",
  "reference_audio_filename": "iris_voice.wav",
  "exaggeration": 0.45,
  "output_format": "wav"
}
```
Server returns 24kHz WAV → miniaudio resamples to 22050 Hz s16le PCM for the pipeline.

### Jarvis Modelfile (Paralinguistic Tags)
Added `PARALINGUISTIC TAGS` section between EMOTIONAL EXPRESSION and HARD RULES in `C:\Users\gandalf\jarvis_modelfile.txt`. Tags: `[chuckle]`, `[sigh]`, `[laugh]`, `[gasp]`. Use 0–2 per response, never in technical/factual answers. `ollama create jarvis` ran successfully.

### Jarvis / Jarvis-Kids — Base Model & Keep-Alive
- Both `jarvis` and `jarvis-kids` modelfiles rebuilt **FROM `gemma3:27b-it-qat`**.
- `jarvis-kids` modelfile: **`num_predict 120`** added (caps reply length for kids mode).
- **`OLLAMA_KEEP_ALIVE=20m`** environment variable set on GandalfAI — models stay warm for 20 minutes.

---

## 5. REPO STRUCTURE

```
IRIS-Robot-Face/
  src/
    main.cpp                    -- serial parsing, emotion/tracking/sleep logic
    config.h                    -- eye definitions array (7 eyes), display pins
    sleep_renderer.h            -- deep space starfield (SR_FRAME_MS=150)
    TeensyEyes.ino              -- upstream eye engine (DO NOT MODIFY)
    displays/GC9A01A_Display.h  -- display driver + fillBlack + getDriver()
    eyes/EyeController.h        -- eye movement/blink/pupil (setTargetPosition seed fix)
    eyes/240x240/               -- nordicBlue/flame/hypnoRed/hazel/blueFlame1/dragon/bigBlue .h
    sensors/PersonSensor.h/.cpp
    mouth.h                     -- MAX7219 32x8 + mouthSleepFrame() + intensity helpers
  scripts/
    patch_gc9a01a.py            -- PlatformIO pre-build; re-applies drawChar fix
  pi4/ (mirrors /home/pi/ on Pi4, all persisted to SD):
    assistant.py                -- voice pipeline, TeensyBridge, CMD listener
    core/config.py              -- all config constants + iris_config.json override loader
    services/tts.py             -- TTS: Chatterbox primary → ElevenLabs → Piper fallback
    hardware/teensy_bridge.py   -- single serial owner of /dev/ttyACM0
    hardware/led.py             -- APA102 driver (show_sleep() + _write brightness param)
    iris_config.json            -- runtime overrides: OWW_THRESHOLD, ELEVENLABS_ENABLED, CHATTERBOX_ENABLED, NUM_PREDICT
    iris_sleep.py               -- cron 9PM: UDP EYES:SLEEP+MOUTH:8, writes /tmp/iris_sleep_mode, Piper "Goodnight."
    iris_wake.py                -- cron 7:30AM: UDP EYES:WAKE
    iris_web.py                 -- web UI Flask (port 5000) + /api/chatterbox_voices route
    iris_web.html               -- web UI: Chatterbox-first Voice tab
  C:\Users\gandalf\ (GandalfAI):
    Chatterbox-TTS-Server/      -- devnen/Chatterbox-TTS-Server clone
    jarvis_modelfile.txt        -- jarvis Ollama modelfile (base: gemma3:27b-it-qat, paralinguistic tags)
    jarvis_kids_modelfile.txt   -- jarvis-kids Ollama modelfile (base: gemma3:27b-it-qat, num_predict 120)
```

---

## 6. PLATFORM

```ini
[env:eyes]
platform = https://github.com/platformio/platform-teensy.git
board = teensy40
framework = arduino
monitor_speed = 115200
build_flags = -std=gnu++17 -O2 -D TEENSY_OPT_SMALLEST_CODE
extra_scripts = pre:scripts/patch_gc9a01a.py
```

---

## 7. KEY FILE STATE

### Eye index map
```
0 = nordicBlue  (default idle)
1 = flame       (ANGRY)
2 = hypnoRed    (CONFUSED)
3 = hazel
4 = blueFlame1
5 = dragon
6 = bigBlue
```

### Pupil values — manual edits (re-apply after genall.py)
| Eye | pupil.min | pupil.max |
|---|---|---|
| nordicBlue | 0.21 | 0.47 |
| hazel | 0.25 | 0.47 |
| bigBlue | 0.24 | 0.50 |
| hypnoRed | 0.25 | 0.50 |

### core/config.py — Key constants
```python
CHATTERBOX_BASE_URL     = "http://192.168.1.3:8004"
CHATTERBOX_VOICE        = "iris_voice.wav"
CHATTERBOX_EXAGGERATION = 0.45
CHATTERBOX_ENABLED      = True
ELEVENLABS_ENABLED      = False   # default now False; iris_config.json also sets False
NUM_PREDICT             = 150     # overridden to 120 by iris_config.json
LED_SLEEP_PEAK          = 26
LED_SLEEP_FLOOR         = 3
LED_SLEEP_PERIOD        = 8.0
LED_SLEEP_BRIGHT        = 0xFF
```
All Chatterbox, ElevenLabs, NUM_PREDICT, and LED_SLEEP_* constants are in `_OVERRIDABLE`.

### iris_config.json on Pi4 (current)
```json
{
  "OWW_THRESHOLD": 0.9,
  "ELEVENLABS_ENABLED": false,
  "CHATTERBOX_ENABLED": true,
  "NUM_PREDICT": 120
}
```

### `src/main.cpp` — Key constants
```cpp
FACE_LOST_TIMEOUT_MS = 5000 | FACE_COOLDOWN_MS = 30000
ANGRY_EYE_DURATION_MS = 9000 | CONFUSED_EYE_DURATION_MS = 7000
EYE_IDX_DEFAULT=0, ANGRY=1, CONFUSED=2, COUNT=7
```

---

## 8. SERIAL PROTOCOL

**Pi4 → Teensy:**
```
EMOTION:NEUTRAL/HAPPY/CURIOUS/ANGRY/SLEEPY/SURPRISED/SAD/CONFUSED
EYES:SLEEP / EYES:WAKE
EYE:n          -- switch default eye (0–6)
MOUTH:x        -- set mouth expression
```
**Teensy → Pi4:** `FACE:1` / `FACE:0`
**Rule:** Only `assistant.py` TeensyBridge owns `/dev/ttyACM0`. Everything else uses UDP → `127.0.0.1:10500`.

---

## 9. SLEEP STATE MACHINE

```
EYES:SLEEP: eyesSleeping=true, blankDisplays(), mouthSetSleepIntensity(0x01),
            sleepRendererInit(), leds.show_sleep()
loop() while sleeping: processSerial(), renderSleepFrame(), mouthSleepFrame(), return
EYES:WAKE:  eyesSleeping=false, mouthRestoreIntensity(0x01), setEyeDefinition(saved),
            applyEmotion(NEUTRAL), show_idle_for_mode(leds)
```
**Note:** Both sleep and wake matrix intensity are 0x01. Only bitmap content differs.
**drawChar fix:** `srDrawZzz()` calls 6-param drawChar. GC9A01A_t3n wrapper was recursive.
Fixed to call 7-param Adafruit_GFX version. Auto-applied by `scripts/patch_gc9a01a.py`.

### Pi4 sleep flow (wired as of this session)
- **CMD listener** (web UI / iris_sleep.py UDP): EYES:SLEEP → `state.eyes_sleeping=True`, write `/tmp/iris_sleep_mode`, **`leds.show_sleep()`**
- **CMD listener** (web UI / iris_wake.py UDP): EYES:WAKE → `state.eyes_sleeping=False`, remove flag, **`show_idle_for_mode(leds)`**
- **Voice command** EYES:SLEEP: sets state, sends Teensy command (no LED call — show_idle_for_mode handles transition)
- **Wakeword during sleep**: removes `/tmp/iris_sleep_mode`, **`state.eyes_sleeping=False`**, sends EYES:WAKE + MOUTH:0, speaks "Good morning.", show_idle_for_mode

---

## 10. CHANGES THIS SESSION (2026-04-03 S1)

### FIX 1 — `pi4/hardware/led.py`
- Added `from core.config import (LED_SLEEP_PEAK, LED_SLEEP_FLOOR, LED_SLEEP_PERIOD, LED_SLEEP_BRIGHT,)` import
- Updated `_write(self, pixels)` → `_write(self, pixels, brightness=0xFF)` — brightness byte now per-call
- Added `show_sleep()` method: very dim indigo breathe, uses LED_SLEEP_* constants, passes `brightness=LED_SLEEP_BRIGHT` to `_write`
- **Deployed + persisted to SD** — md5 verified

### FIX 2 — `pi4/assistant.py` CMD listener LED wiring
- `start_cmd_listener(teensy)` → `start_cmd_listener(teensy, leds)` (signature + call site at ~line 420)
- EYES:SLEEP handler: added `leds.show_sleep()` after `/tmp/iris_sleep_mode` flag write
- EYES:WAKE handler: added `show_idle_for_mode(leds)` after flag removal
- **Deployed + persisted to SD** — md5 verified

### FIX 3 — `pi4/assistant.py` wakeword-during-sleep state reset
- Wakeword-during-sleep handler (~line 458): added `state.eyes_sleeping = False` immediately before `teensy.send_command('EYES:WAKE')`
- Prevents state desync when wakeword triggers wake from sleep
- `state_manager.py` already had `eyes_sleeping: bool = False` — no change needed

### FIX 4 — `pi4/core/config.py`
- `ELEVENLABS_ENABLED = True` → `ELEVENLABS_ENABLED = False`
- Safety net: iris_config.json already overrides to false on Pi4

### FIX 5 — Pi4 `iris_config.json`
- Added `"NUM_PREDICT": 120` (was only in jarvis-kids modelfile; now also applied to adult model queries)
- `NUM_PREDICT` was already in `_OVERRIDABLE` — no config.py change needed
- **Persisted to SD** — md5 verified

### FIX 6 — `pi4/iris_sleep.py` canonical version
- Merged repo version (Piper TTS call) with Pi4 live version (imports CMD_PORT from core.config)
- Now: imports CMD_PORT from core.config, sends UDP EYES:SLEEP + MOUTH:8, writes `/tmp/iris_sleep_mode`, calls Piper TTS "Goodnight."
- **Deployed + persisted to SD** — md5 verified

### Previous session changes (2026-04-02 S3) — STILL PENDING DEPLOY
- **`src/mouth.h`** — Normal matrix intensity 0x01 (was 0x05). **PENDING FIRMWARE FLASH**
- **`src/main.cpp`** — PersonSensor green LED disabled. **PENDING FIRMWARE FLASH**
- **`src/sleep_renderer.h`** — Starfield intensity boost. **PENDING FIRMWARE FLASH**
- **`pi4/hardware/led.py`** — 10% APA102 values. **DEPLOYED this session (FIX 1)**

---

## 11. CURRENT KNOWN ISSUES / TODO

### HIGH
- **Firmware flash required** — `src/mouth.h` (normal intensity 0x01), `src/main.cpp` (PersonSensor LED off), `src/sleep_renderer.h` (starfield boost) are edited but not yet flashed. Flash via PlatformIO USB (`/flash` command) before verifying changes take effect.
- **Voice clip not uploaded** — `iris_voice.wav` must be uploaded to http://192.168.1.3:8004 → Reference Audio tab before Chatterbox can clone the IRIS voice. File at `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face\iris_voice.wav`.
- **End-to-end not tested** — Full pipeline (wake → STT → LLM with tags → Chatterbox → ReSpeaker) not verified with voice clone.

### MEDIUM
- **Smoke test sleep LED** — `EYES:SLEEP` via web UI should now trigger indigo breathe (`leds.show_sleep()`). Not yet manually verified this session. Test by: web UI Sleep button → confirm LEDs go dim indigo. Web UI Wake button → confirm idle cyan resumes.
- **Matrix brightness awake == sleep** — After S3, both mouthRestoreIntensity and mouthSetSleepIntensity use 0x01 (pending firmware flash). No brightness difference between sleep and awake mouth. Raise mouthRestoreIntensity to 0x02 or 0x03 if awake expressions look too dim.
- **Exaggeration tuning** — 0.45 starting point. Tune after first live voice test.
- **Paralinguistic tag rendering** — Verify Chatterbox Turbo renders `[chuckle]` etc. as sounds, not text.

### LOW
- **`iris_voice.wav`** in project root — untracked binary, do not commit. Add to `.gitignore`.
- **`_decode_assistant.py` and `REFACTOR_VISUAL.md`** — untracked files in project root. Review/clean up.
- **`IRIS_AUDIT_2026-04-03.md`** — untracked file in project root. Review/commit or delete.
- **Chatterbox server auto-start on Gandalf boot** — not yet configured.
- **Piper TTS fallback** — audio quality mismatch. Acceptable for now.

---

## 12. FLASH / DEPLOY COMMANDS

```bash
# Pi4 persist a file to SD:
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/<file> /media/root-ro/home/pi/<file>
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/<file> /media/root-ro/home/pi/<file>

# Pi4 restart assistant:
sudo systemctl restart assistant
journalctl -u assistant -n 30 --no-pager

# Teensy bootloader (no PROG button needed):
python3 -c "import serial, time; s=serial.Serial('/dev/ttyACM0',134); time.sleep(0.5); s.close()"
```

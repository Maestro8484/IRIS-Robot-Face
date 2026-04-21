# IRIS Robot Face — Handoff Snapshot
**Date:** 2026-04-02
**Session:** 3
**Branch:** `main`
**Last commit:** `2e60677` (Rebuild jarvis/jarvis-kids on gemma3:27b-it-qat, add num_predict to kids)
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

**Firmware:** Flashed 2026-03-29. Sleep fully working. drawChar recursion fixed. 7-eye system. Face tracking working. **PENDING FLASH (this session): APA102 already at 10% in led.py (Pi4 deploy needed); mouth.h normal intensity→0x01, PersonSensor LED disabled, sleep_renderer.h starfield boost — require USB firmware flash.**
**Sleep display:** Starfield + ZZZ animation on both TFTs confirmed working.
**Sleep LEDs:** APA102 dim indigo breathe on EYES:SLEEP. peak=26 (~10% of 255), global_bright=0xFF, floor=3. Restores idle on EYES:WAKE. (config.py constants, not led.py literals)
**Mouth during sleep:** Snore animation, intensity 0x01 (~10%). Working.
**Wake from webui:** Working. Cron sleep: 9PM/7:30AM UDP path. False wakeword during cron window now ignored (button-only override).
**Voice pipeline (assistant.py):** Operational. Modular (hardware/, core/, services/, state/).
**TTS routing:** Chatterbox (primary) → ElevenLabs (disabled via iris_config.json) → Piper (fallback).
**Chatterbox server:** Running on GandalfAI. Web UI confirmed accessible at http://192.168.1.3:8004.
**Jarvis modelfile:** Updated with PARALINGUISTIC TAGS section. `ollama create jarvis` completed.
**ElevenLabs:** Disabled — `ELEVENLABS_ENABLED=False` in `/home/pi/iris_config.json`. Out of credits (subscription active).
**Web UI:** Chatterbox-first Voice tab live. EYE:n switching (0–6), Sleep/Wake buttons, live state polling. Port 5000.
**Face tracking:** Working. setTargetPosition seed fix in EyeController.h.

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

### Jarvis / Jarvis-Kids — Base Model & Keep-Alive (2026-04-02 S2)
- Both `jarvis` and `jarvis-kids` modelfiles rebuilt **FROM `gemma3:27b-it-qat`** (previously different base).
- `jarvis-kids` modelfile: **`num_predict 120`** added (caps reply length for kids mode).
- **`OLLAMA_KEEP_ALIVE=20m`** environment variable set on GandalfAI — models stay warm for 20 minutes after last use instead of default 5m.

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
  /home/pi/ (Pi4, all persisted to SD):
    assistant.py                -- voice pipeline, TeensyBridge, CMD listener
    core/config.py              -- all config constants + iris_config.json override loader
    services/tts.py             -- TTS: Chatterbox primary → ElevenLabs → Piper fallback
    hardware/teensy_bridge.py   -- single serial owner of /dev/ttyACM0
    hardware/led.py             -- APA102 driver (10% brightness — PENDING DEPLOY)
    iris_config.json            -- runtime overrides: {"ELEVENLABS_ENABLED": false}
    iris_sleep.py / iris_wake.py -- 9PM/7:30AM cron (UDP only)
    iris_web.py                 -- web UI Flask (port 5000) + /api/chatterbox_voices route
    iris_web.html               -- web UI: Chatterbox-first Voice tab
  C:\Users\gandalf\ (GandalfAI):
    Chatterbox-TTS-Server/      -- devnen/Chatterbox-TTS-Server clone
    Chatterbox-TTS-Server/run_server.bat  -- install + start script
    jarvis_modelfile.txt        -- jarvis Ollama modelfile (base: gemma3:27b-it-qat, paralinguistic tags)
    jarvis_kids_modelfile.txt   -- jarvis-kids Ollama modelfile (base: gemma3:27b-it-qat, num_predict 120)
    chatterbox_server.log       -- install + server log
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

### core/config.py — Chatterbox constants
```python
CHATTERBOX_BASE_URL     = "http://192.168.1.3:8004"
CHATTERBOX_VOICE        = "iris_voice.wav"
CHATTERBOX_EXAGGERATION = 0.45
CHATTERBOX_ENABLED      = True
```
All four are in `_OVERRIDABLE` (can be overridden via iris_config.json / web UI).

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
**Note:** After S3 changes, both sleep and wake matrix intensity are 0x01. Only bitmap content differs.

**drawChar fix:** `srDrawZzz()` calls 6-param drawChar. GC9A01A_t3n wrapper was recursive.
Fixed to call 7-param Adafruit_GFX version. Auto-applied by `scripts/patch_gc9a01a.py`.

---

## 10. CHANGES THIS SESSION (2026-04-02 S3)

- **`pi4/hardware/led.py`** — All APA102 brightness values reduced to ~10% of original:
  - `show_idle`: peak 65→7, floor 3→1
  - `show_idle_kids`: peak 62→6, floor 3→1
  - `show_wake`: (80,80,80)→(8,8,8)
  - `show_recording`: (120,0,0)→(12,0,0)
  - `show_thinking`: (0,0,100)→(0,0,10)
  - `show_speaking`: (0,80,0)→(0,8,0)
  - `show_error`: (120,0,0)→(12,0,0)
  - `show_followup`: range max 60→9
  - `show_ptt`: (80,60,0)→(8,6,0)
  - `show_kids_mode_on/off`: 100→10 on all channels
  - `_EMOTION_LED` table: all r/g/b values scaled to ~10% of original
  - `show_emotion` surprise flash: (120,120,120)→(12,12,12); cyan steps range(3,81,3)→range(1,9,1)
  - **PENDING DEPLOY to Pi4** — `led.py` written in repo, not yet pushed to `/home/pi/hardware/led.py`

- **`src/mouth.h`** — Normal matrix intensity reduced to 10%:
  - `mouthInit()`: `0x0A, 0x05` → `0x0A, 0x01` (comment updated)
  - `mouthRestoreIntensity()`: `0x05` → `0x01`
  - `mouthSetSleepIntensity()` unchanged (already `0x01`)
  - **PENDING FIRMWARE FLASH** — manual USB flash required

- **`src/main.cpp`** — PersonSensor green status LED disabled:
  - Added `personSensor.enableLED(false)` after `personSensor.enableID(false)` in `setup()` (~line 291)
  - Uses `Reg::DebugMode` register in PersonSensor API
  - **PENDING FIRMWARE FLASH** — manual USB flash required

### Previous session changes (2026-04-02 S2) — carried forward
- **`assistant.py` (root)** — `git rm`'d. Canonical version is `pi4/assistant.py`.
- **jarvis + jarvis-kids modelfiles** — Both rebuilt FROM `gemma3:27b-it-qat`. `jarvis-kids` gained `num_predict 120`. `OLLAMA_KEEP_ALIVE=20m` set on GandalfAI.
- **Pi4 `services/tts.py`** — Synced. Markdown/speech-marker strip block in `synthesize()`.
- **`src/sleep_renderer.h`** — Starfield intensity boost (4 changes). **Requires firmware flash.**

### Previous session changes (2026-04-01) — carried forward
- Pi4 `assistant.py` — Cron sleep window guard. Persisted.
- Pi4 `core/config.py` — `LED_SLEEP_PEAK=26`, `LED_SLEEP_FLOOR=3`, `LED_SLEEP_BRIGHT=0xFF`. Persisted.

---

## 11. CURRENT KNOWN ISSUES / TODO

### HIGH
- **`led.py` deploy to Pi4** — `pi4/hardware/led.py` has 10% APA102 values but NOT yet deployed to `/home/pi/hardware/led.py`. Must `/deploy` or manually SCP+persist before changes take effect. Until deployed, live APA102 remains at original brightness.
- **Firmware flash required** — `src/mouth.h` (normal intensity 0x01) and `src/main.cpp` (PersonSensor LED off) and `src/sleep_renderer.h` (starfield boost from S2) are edited but not yet flashed. Flash via PlatformIO USB before verifying changes.
- **Voice clip not uploaded** — `iris_voice.wav` must be uploaded to http://192.168.1.3:8004 → Reference Audio tab before Chatterbox can clone the IRIS voice. File is at `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face\iris_voice.wav` on desktop.
- **End-to-end not tested** — Full pipeline (wake → STT → LLM with tags → Chatterbox → ReSpeaker) not verified.

### MEDIUM
- **Matrix brightness awake == sleep** — After S3, both mouthRestoreIntensity and mouthSetSleepIntensity use 0x01. No brightness difference between sleep and awake mouth. If the awake expressions look too dim, raise mouthRestoreIntensity to 0x02 or 0x03.
- **Exaggeration tuning** — 0.45 starting point. Tune after first live voice test.
- **Paralinguistic tag rendering** — Verify Chatterbox Turbo renders `[chuckle]` etc. as sounds, not text.

### LOW
- **`iris_voice.wav`** in project root — untracked binary, do not commit. Add to `.gitignore`.
- **`_decode_assistant.py` and `REFACTOR_VISUAL.md`** — untracked files in project root. Review/clean up.
- **Chatterbox server auto-start on Gandalf boot** — not yet configured.
- **Piper TTS fallback** — audio quality mismatch. Acceptable for now.

---

## 12. FLASH / DEPLOY COMMANDS

```bash
# Pi4 deploy led.py (persist to SD):
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/hardware/led.py /media/root-ro/home/pi/hardware/led.py
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/hardware/led.py /media/root-ro/home/pi/hardware/led.py

# Pi4 restart assistant:
sudo systemctl restart assistant
journalctl -u assistant -n 30 --no-pager

# Teensy bootloader (no PROG button needed):
python3 -c "import serial, time; s=serial.Serial('/dev/ttyACM0',134); time.sleep(0.5); s.close()"
```

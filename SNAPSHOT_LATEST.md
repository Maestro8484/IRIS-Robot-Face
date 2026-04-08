# IRIS Robot Face — Handoff Snapshot
**Date:** 2026-04-08
**Session:** 4
**Branch:** `main`
**Last commit:** `3ceff67` (feat: ILI9341 backlight PWM on pin 14)
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

**Firmware:** Flashed 2026-04-03. mouth.h normal intensity 0x01, PersonSensor green LED disabled, sleep_renderer.h starfield boost — all confirmed flashed.
**Sleep display:** Starfield + ZZZ animation on both TFTs confirmed working.
**Sleep LEDs:** APA102 dim indigo breathe on EYES:SLEEP. peak=26 (~10% of 255), global_bright=0xFF, floor=3. LED_SLEEP_* constants in config.py. show_sleep() wired into CMD listener. Restores idle on EYES:WAKE. Deployed S1.
**Mouth during sleep:** Snore animation, intensity 0x01 (~10%). Working.
**Wake from webui:** Working. Cron sleep: 9PM/7:30AM UDP path. False wakeword during cron window now ignored (button-only override).
**Voice pipeline (assistant.py):** Operational. Modular (hardware/, core/, services/, state/).
**TTS routing:** Chatterbox (primary) → ElevenLabs (disabled via iris_config.json) → Piper (fallback).
**Chatterbox server:** Running on GandalfAI. Web UI confirmed accessible at http://192.168.1.3:8004.
**Jarvis modelfile:** Updated with PARALINGUISTIC TAGS section. `ollama create jarvis` completed.
**ElevenLabs:** Disabled — `ELEVENLABS_ENABLED=False` in `/home/pi/iris_config.json` AND default False in config.py.
**Web UI:** Chatterbox-first Voice tab live. EYE:n switching (0–6), Sleep/Wake buttons, live state polling. Port 5000.
**Face tracking:** Working. setTargetPosition seed fix in EyeController.h.
**NUM_PREDICT:** 120 in iris_config.json (overrides config.py default of 150).
**Cron sleep/wake:** HARDENED this session. Single user crontab, ALSA_CARD env, correct log paths, duplicate /etc/cron.d/iris removed. In-script logging to /home/pi/logs/. Persisted to SD.

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

### Voice Clone — UPLOADED
- `iris_voice.wav` uploaded to http://192.168.1.3:8004 → Reference Audio tab. Confirmed filename: `iris_voice.wav`.
- Source file: `voice_preview_snarky james bond.wav` (24.5s, stereo, 48kHz) on desktop PC.
- Pi4 config constant: `CHATTERBOX_VOICE = "iris_voice.wav"` (exact filename, with extension)
- End-to-end voice clone not yet verified live.

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
    mouth_tft.cpp/.h            -- ILI9341 TFT mouth driver; BL on pin 14, PWM via analogWrite
  scripts/
    patch_gc9a01a.py            -- PlatformIO pre-build; re-applies drawChar fix
  pi4/ (mirrors /home/pi/ on Pi4, all persisted to SD):
    assistant.py                -- voice pipeline, TeensyBridge, CMD listener
    core/config.py              -- all config constants + iris_config.json override loader
    services/tts.py             -- TTS: Chatterbox primary → ElevenLabs → Piper fallback
    hardware/teensy_bridge.py   -- single serial owner of /dev/ttyACM0
    hardware/led.py             -- APA102 driver (show_sleep() + _write brightness param)
    iris_config.json            -- runtime overrides: OWW_THRESHOLD, ELEVENLABS_ENABLED, CHATTERBOX_ENABLED, NUM_PREDICT
    iris_sleep.py               -- cron 9PM: in-script logging, UDP EYES:SLEEP+MOUTH:8, /tmp flag, Piper (try/except)
    iris_wake.py                -- cron 7:30AM: in-script logging, UDP EYES:WAKE+MOUTH:0, CMD_PORT from core.config
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

### ILI9341 TFT mouth pin map (mouth_tft.cpp)
```
Pin  4 = RST
Pin  5 = MOSI (bit-bang SPI)
Pin  6 = SCK  (bit-bang SPI)
Pin  7 = CS
Pin  8 = DC
Pin 14 = BL   (PWM: 220 boot/wake, 40 sleep, level*17 for MOUTH:n intensity)
```

### Cron entries (Pi4 user crontab — as of S2)
```
0 21 * * * ALSA_CARD=seeed2micvoicec /usr/bin/python3 /home/pi/iris_sleep.py >> /home/pi/logs/iris_sleep.log 2>&1
30 7 * * * ALSA_CARD=seeed2micvoicec /usr/bin/python3 /home/pi/iris_wake.py >> /home/pi/logs/iris_wake.log 2>&1
0 3 * * 0 sudo /bin/bash /home/pi/iris_backup.sh
```
**Note:** `/etc/cron.d/iris` has been removed — it was firing a duplicate iris_sleep.py at 9PM that logged to /var/log/ (permission denied, silent failure).

### Pi4 log files
```
/home/pi/logs/iris_sleep.log  -- sleep cron output (in-script redirect + crontab >>)
/home/pi/logs/iris_wake.log   -- wake cron output (in-script redirect + crontab >>)
/home/pi/iris_sleep.log       -- OLD log location (pre-S2, can be deleted)
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

### Pi4 sleep flow
- **CMD listener** (web UI / iris_sleep.py UDP): EYES:SLEEP → `state.eyes_sleeping=True`, write `/tmp/iris_sleep_mode`, **`leds.show_sleep()`**
- **CMD listener** (web UI / iris_wake.py UDP): EYES:WAKE → `state.eyes_sleeping=False`, remove flag, **`show_idle_for_mode(leds)`**
- **Voice command** EYES:SLEEP: sets state, sends Teensy command (no LED call — show_idle_for_mode handles transition)
- **Wakeword during sleep**: removes `/tmp/iris_sleep_mode`, **`state.eyes_sleeping=False`**, sends EYES:WAKE + MOUTH:0, speaks "Good morning.", show_idle_for_mode

### Cron sleep verification (2026-04-03 21:00)
Journal confirmed at 21:00:01: `[CMD] -> teensy: EYES:SLEEP`, `[EYES] >> EYES:SLEEP`, `[CMD] -> teensy: MOUTH:8`. Sleep DID work. Root cause of reported failure was pre-FIX6 iris_sleep.py (no CMD_PORT import). The duplicate cron entry in /etc/cron.d/iris was also firing, logging to /var/log/ (silently failing — no write permission for pi).

---

## 10. COMPLETED THIS SESSION (2026-04-03 S1–S3)

| Item | Status |
|---|---|
| led.py show_sleep() added + wired into CMD listener | Done S1 |
| assistant.py CMD listener leds wired (EYES:SLEEP/WAKE) | Done S1 |
| assistant.py wakeword-during-sleep state.eyes_sleeping reset | Done S1 |
| core/config.py ELEVENLABS_ENABLED default → False | Done S1 |
| iris_config.json NUM_PREDICT=120 added | Done S1 |
| iris_sleep.py canonical (CMD_PORT import, logging, Piper try/except) | Done S1+S2 |
| iris_wake.py hardened (CMD_PORT import, logging) | Done S2 |
| Cron hardened (ALSA_CARD env, correct log paths, /etc/cron.d/iris removed) | Done S2 |
| Firmware flashed: mouth.h 0x01, PersonSensor LED off, starfield boost | Done S2 |
| iris_voice.wav uploaded to Chatterbox | Done S2 |
| ILI9341 backlight PWM — pin 14, 220 boot/wake, 40 sleep, level*17 intensity | Done S4 |

---

## 11. CURRENT KNOWN ISSUES / TODO

### HIGH
- **End-to-end not tested** — iris_voice.wav uploaded. Run live wakeword test, confirm Chatterbox renders cloned voice through speakers.
- **Reciprocal listening broken — `implies_followup()` detection gap.** IRIS asks a question then appends a trailing sentence; `implies_followup()` returns False because reply doesn't end with `?`; mic never opens. Fix: (1) add modelfile hard rule "If your response contains a question, it must be the final sentence" — try first, lower risk. (2) If insufficient, also broaden `implies_followup()` to match `?` anywhere in reply[-80:].
- **Piper not installed as standalone binary** — `/usr/local/bin/piper` and `/home/pi/piper/` missing on Pi4. iris_sleep.py "Goodnight" silently fails (non-blocking, sleep still activates). Wakeword-during-sleep "Good morning" in assistant.py also uses bash piper subprocess — likely also failing silently. Fix: route both through Wyoming Piper on GandalfAI port 10200 (already used by services/tts.py) rather than installing local binary.

### MEDIUM
- **Smoke test sleep LED** — Verify web UI Sleep button triggers indigo breathe. Wake button restores idle cyan.
- **Matrix brightness awake == sleep** — mouthRestoreIntensity and mouthSetSleepIntensity both 0x01 (now flashed). If awake expressions look too dim after live testing, raise mouthRestoreIntensity to 0x02 or 0x03.
- **Exaggeration tuning** — 0.45 starting point. Tune after first live voice test.
- **Paralinguistic tag rendering** — Verify Chatterbox Turbo renders `[chuckle]` etc. as sounds, not literal text.

### LOW
- **Untracked files in project root** — `iris_voice.wav`, `_decode_assistant.py`, `REFACTOR_VISUAL.md`, `IRIS_AUDIT_2026-04-03.md`. Add wav to `.gitignore`, review/delete or commit the others.
- **Old log file** — `/home/pi/iris_sleep.log` (root level, pre-S2) is stale. Delete after confirming `/home/pi/logs/iris_sleep.log` is active.
- **Chatterbox auto-start on Gandalf boot** — not configured.
- **OWW_THRESHOLD** — live Pi4 = 0.9 (iris_config.json), config.py default = 0.85. Confirm intended value and sync whichever is wrong.

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

# Crontab — overlayfs blocks crontab -e; write directly:
sudo bash -c 'cat > /var/spool/cron/crontabs/pi << EOF
<entries>
EOF'
sudo mount -o remount,rw /media/root-ro
sudo cp /var/spool/cron/crontabs/pi /media/root-ro/var/spool/cron/crontabs/pi
sudo mount -o remount,ro /media/root-ro
sudo md5sum /var/spool/cron/crontabs/pi /media/root-ro/var/spool/cron/crontabs/pi
```

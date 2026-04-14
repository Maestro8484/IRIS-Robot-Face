# IRIS Robot Face — Handoff Snapshot
**Date:** 2026-04-14
**Session:** 16
**Branch:** `main`
**Last commit:** 34f9456 — docs: update snapshot - main branch consolidated, GandalfAI Claude Desktop, docker compose centralized, pending items logged
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
| GandalfAI (Claude Desktop) | 192.168.1.3 | gandalf / 5309 | Claude Desktop + MCP installed (S14). Local filesystem MCP scope: `C:\Users\gandalf\` ONLY — `C:\docker\` and `C:\IRIS\` are NOT in MCP scope. Use Bash tool for all C:\docker\ and C:\IRIS\ operations. |
| Teensy 4.1 | USB → Desktop PC | N/A | Dual GC9A01A 1.28" round TFT eyes + ILI9341 2.8" TFT mouth |
| Synology NAS | 192.168.1.102 | Master / Gateway!7007 | SSH port 2233. Backup: \\192.168.1.102\BACKUPS\IRIS-Robot-Face\ |

**SSH MCP tools:** `ssh-pi4` (192.168.1.200), `ssh-gandalf` (192.168.1.3), `ssh` (NAS, port 2233)
**SSH auth:** Pi4 uses **password auth only** — key auth fails. Always connect with `username: pi`, `password: ohs`.
**GandalfAI:** Windows machine. No `df`, `head`, `grep` — use PowerShell / findstr / dir equivalents.
**GandalfAI MCP scope correction (S16):** filesystem MCP only covers `C:\Users\gandalf\`. All `C:\IRIS\`, `C:\docker\` file reads/writes must go through the Bash tool.

---

## 2. GANDALFAI FILE LAYOUT (as of S16 — CENTRALIZATION COMPLETE)

All IRIS-related files on GandalfAI now live under `C:\IRIS\`:

```
C:\IRIS\
  docker\
    docker-compose.yml        -- CANONICAL compose file (was C:\docker\docker-compose.yml)
    whisper\                  -- whisper model cache (migrated from C:\docker\whisper\)
    piper\                    -- piper data (migrated from C:\docker\piper\)
  chatterbox\
    config.yaml               -- Chatterbox config (last_chunk_size: 300)
    reference_audio\
      iris_voice.wav          -- CONFIRMED PRESENT
    voices\                   -- predefined voices
    model_cache\              -- empty (model downloads on first start)
    logs\
    outputs\
  ollama\
    jarvis_modelfile.txt      -- UPDATED (S16 edits applied, model rebuilt)
    jarvis-kids_modelfile.txt -- UPDATED (S16 edits applied, model rebuilt)
  backup\
    docker-compose.yml.bak    -- original pre-migration backup
```

**Old locations (DO NOT USE for new work — originals left intact for stability):**
- `C:\docker\docker-compose.yml.pre-iris.bak` — archived
- `C:\docker\whisper\`, `C:\docker\piper\` — originals still present, safe to delete next session
- `C:\Users\gandalf\Chatterbox-TTS-Server\` — original still present, safe to delete next session
- `C:\Users\gandalf\jarvis_modelfile.txt`, `jarvis-kids_modelfile.txt` — originals still present

**HF cache:** `C:\Users\gandalf\.cache\huggingface` — intentionally NOT moved, stays in user profile.

---

## 3. PROJECT STATUS

**Firmware:** Build clean 2026-04-11 (S9). NOT YET FLASHED — pending physical T4.1 swap. T4.0 last confirmed working state: eca1627.
**Person Sensor tracking:** CONFIRMED WORKING. Stock chrismiller code. Sensor physically mounted right-side-up. `is_facing && conf > 60`, 70ms poll, 120ms animation, stock coordinate formula. Eye tracks face laterally and vertically.
**Sleep display:** Starfield + ZZZ animation on both TFTs confirmed working.
**Sleep LEDs:** APA102 dim indigo breathe on EYES:SLEEP. peak=26, global_bright=0xFF, floor=3.
**Mouth during sleep:** Snore animation. TFT stays blank. BL dims to 40/255.
**Wake from webui:** Working. Cron sleep 9PM/7:30AM UDP path. False wakeword during cron window ignored (button-only override).
**Voice pipeline (assistant.py):** Operational. Modular (hardware/, core/, services/, state/).
**TTS routing:** Chatterbox (primary) → ElevenLabs (disabled) → Piper (fallback).
**Chatterbox server:** Running on GandalfAI at http://192.168.1.3:8004. Now serving from `C:\IRIS\docker\docker-compose.yml`.
**ElevenLabs:** Disabled — `ELEVENLABS_ENABLED=False` in iris_config.json and config.py.
**Web UI:** Chatterbox-first Voice tab live. EYE:n switching (0–6), Sleep/Wake buttons, live state polling. Port 5000.
**NUM_PREDICT:** 120 in iris_config.json.
**Cron sleep/wake:** HARDENED. Single user crontab, ALSA_CARD env, correct log paths.
**ILI9341 TFT mouth:** Library switched to KurtE/ILI9341_t3n (auto-detects SPI bus from pin numbers). CS=36, DC=8, RST=4, MOSI=35, SCK=37 → SPI2. Build confirmed clean. Physical verification pending T4.1 swap.
**Flash workflow:** MANUAL ONLY — user clicks PlatformIO upload button, Teensy USB → Desktop PC. Claude runs `pio run` only.
**Ollama models:** `jarvis` and `jarvis-kids` both rebuilt fresh as of S16 with updated modelfiles.

---

## 4. CLAUDE CODE INFRASTRUCTURE

### Slash Commands
| Command | File | Purpose |
|---|---|---|
| `/flash` | `.claude/commands/flash.md` | Local USB flash via PlatformIO |
| `/flash-remote` | `.claude/commands/flash-remote.md` | Remote flash via Pi4 SSH (software bootloader confirmed) |
| `/deploy` | `.claude/commands/deploy.md` | Persist Pi4 files through overlayfs to SD |
| `/snapshot` | `.claude/commands/snapshot.md` | Generate end-of-session snapshot |
| `/eye-edit` | `.claude/commands/eye-edit.md` | Eye config edit + genall.py + pupil re-apply workflow |

### iris-snapshot GitHub repo
- **Repo:** `https://github.com/Maestro8484/iris-snapshot` (private)
- **Local:** `C:/Users/SuperMaster/Documents/PlatformIO/iris-snapshot/`
- **Raw URL:** `https://raw.githubusercontent.com/Maestro8484/iris-snapshot/main/SNAPSHOT_latest.md`

### Pi4 Sudoers (persisted to SD)
- `/etc/sudoers.d/iris_service` — passwordless sudo for systemctl stop/start/restart/status assistant

### Software Bootloader Entry (Teensy — confirmed working, no PROG button needed)
```bash
python3 -c "import serial, time; s=serial.Serial('/dev/ttyACM0',134); time.sleep(0.5); s.close()"
```

---

## 5. TEENSY 4.1 COMPLETE PIN ASSIGNMENT

### Eye displays (GC9A01A, config.h)
| GPIO | Signal | Wire | Device | Bus |
|---|---|---|---|---|
| 0 | CS | Yellow | Left eye | SPI1 |
| 2 | DC | Blue | Left eye | SPI1 |
| 3 | RST | Brown | Left eye | SPI1 |
| 26 | MOSI | Green | Left eye | SPI1 hw |
| 27 | SCK | Orange | Left eye | SPI1 hw |
| 10 | CS | Yellow | Right eye | SPI0 |
| 9 | DC | Blue | Right eye | SPI0 |
| — | RST | — | Right eye | -1 (no pin) |
| 11 | MOSI | Green | Right eye | SPI0 hw |
| 13 | SCK | Orange | Right eye | SPI0 hw |

### Person Sensor (I2C) — mounted RIGHT-SIDE-UP
| GPIO | Signal | Wire |
|---|---|---|
| 18 | SDA | Blue |
| 19 | SCL | Yellow |

### ILI9341 TFT Mouth (hardware SPI2 — T4.1)
| GPIO | Signal | Wire | Bus |
|---|---|---|---|
| 35 | MOSI | Gray | SPI2 hw |
| 37 | SCK | Green | SPI2 hw |
| 36 | CS | Blue | SPI2 |
| 8 | DC | Purple | — |
| 4 | RST | Brown | — |
| 14 | BL | Orange | PWM: 220 boot/wake, 40 sleep |

> Free pins: 5, 6, 7, 15–17, 20–25, 28–33, 38–55 (T4.1 extended)
> MAX7219 matrix uses 5/6/7 (DATA/CLK/CS) — see mouth.h.

---

## 6. MOUTH TFT STATUS — BUILD CLEAN, FLASH PENDING

**Library:** `moononournation/GFX Library for Arduino @ ^1.4.9` — Arduino_GFX SWSPI (bit-bang).
Same library as confirmed-working T4.0 commit 732b069 on main. Pins moved from 5/6/7 → 35/37/36.

```cpp
// Bit-bang SPI: MOSI=35, SCK=37, CS=36, DC=8, RST=4, BL=14
_bus = new Arduino_SWSPI(MOUTH_TFT_DC, MOUTH_TFT_CS,
                          MOUTH_TFT_SCK, MOUTH_TFT_MOSI, -1);
_tft = new Arduino_ILI9341(_bus, MOUTH_TFT_RST, 3);  // rotation=3 (landscape flipped)
```

> No DMA, no hardware SPI — zero conflict with GC9A01A_t3n on SPI0/SPI1.

---

## 7. CHATTERBOX TTS

- **Server:** GandalfAI — now containerized at `C:\IRIS\docker\docker-compose.yml`, port 8004
- **Config:** `C:\IRIS\chatterbox\config.yaml` — `last_chunk_size: 300` (updated S16)
- **Model:** Chatterbox Turbo, exaggeration 0.45
- **Voice:** `iris_voice.wav` — CONFIRMED PRESENT at `C:\IRIS\chatterbox\reference_audio\iris_voice.wav`
- **Endpoint:** `POST http://192.168.1.3:8004/tts` — `voice_mode: clone`, `reference_audio_filename: iris_voice.wav`
- **Confirmed working** post sleep/wake (S15). HTTP 200 confirmed S16.
- **Healthcheck note:** Docker healthcheck reports `unhealthy` when GPU is busy inferring (curl times out during generation). This is a false negative — container is operational. HTTP 200 on direct poll confirms health.

---

## 8. OLLAMA MODELS (as of S16)

### jarvis (adult Jarvis persona)
- **File:** `C:\IRIS\ollama\jarvis_modelfile.txt`
- **Base:** `gemma3:27b-it-qat`
- **Key params:** `num_predict 120`, `temperature 0.7`, `num_ctx 8192`
- **S16 changes applied:**
  - RESPONSE STYLE: "Keep all responses under **2 sentences and under 30 words** unless the question genuinely requires more detail. When in doubt, say less."
  - HARD RULES appended: "Never volunteer the current date, time, or location in a response unless the user explicitly asked for it."

### jarvis-kids (Leo & Mae persona)
- **File:** `C:\IRIS\ollama\jarvis-kids_modelfile.txt`
- **Base:** `gemma3:27b-it-qat`
- **Key params:** `num_predict 120`, `temperature 0.90`, `num_ctx 8192`
- **S16 changes applied:**
  - SAFETY section appended: "Never volunteer the current date, time, or location in a response unless the user explicitly asked for it."

Both models rebuilt with `ollama create` — confirmed `success`, new layer hashes written.

---

## 9. REPO STRUCTURE

```
IRIS-Robot-Face/
  src/
    main.cpp                    -- serial parsing, emotion/tracking/sleep logic
    config.h                    -- eye definitions array (7 eyes), display pins
    sleep_renderer.h            -- deep space starfield (SR_FRAME_MS=150)
    displays/GC9A01A_Display.h  -- display driver
    eyes/EyeController.h        -- eye movement/blink/pupil (setTargetPosition seed fix intact)
    eyes/240x240/               -- nordicBlue/flame/hypnoRed/hazel/blueFlame1/dragon/bigBlue .h
    sensors/PersonSensor.h/.cpp -- I2C face detection (SAMPLE_TIME_MS=70, conf>60, is_facing)
    mouth_tft.cpp/.h            -- ILI9341 TFT mouth driver (Arduino_GFX SWSPI bit-bang)
  pi4/                          -- mirrors /home/pi/ on Pi4
```

---

## 10. PLATFORM

```ini
[env:eyes]
platform = https://github.com/platformio/platform-teensy.git
board = teensy41
framework = arduino
monitor_speed = 115200
build_flags = -std=gnu++17 -O2 -D TEENSY_OPT_SMALLEST_CODE
lib_deps =
  https://github.com/PaulStoffregen/Wire
  https://github.com/PaulStoffregen/ST7735_t3
  https://github.com/mjs513/GC9A01A_t3n
  moononournation/GFX Library for Arduino @ ^1.4.9
```

---

## 11. KEY FILE STATE

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
ELEVENLABS_ENABLED      = False
NUM_PREDICT             = 150     # overridden to 120 by iris_config.json
LED_SLEEP_PEAK          = 26
LED_SLEEP_FLOOR         = 3
LED_SLEEP_PERIOD        = 8.0
LED_SLEEP_BRIGHT        = 0xFF
```

### iris_config.json on Pi4 (current)
```json
{
  "OWW_THRESHOLD": 0.9,
  "ELEVENLABS_ENABLED": false,
  "CHATTERBOX_ENABLED": true,
  "NUM_PREDICT": 120
}
```

### src/main.cpp — Key constants
```cpp
FACE_LOST_TIMEOUT_MS = 5000 | FACE_COOLDOWN_MS = 30000
ANGRY_EYE_DURATION_MS = 9000 | CONFUSED_EYE_DURATION_MS = 7000
EYE_IDX_DEFAULT=0, ANGRY=1, CONFUSED=2, COUNT=7
```

### Person Sensor tracking (CONFIRMED WORKING — do not change)
```cpp
// PersonSensor.h
SAMPLE_TIME_MS = 70

// main.cpp loop — stock chrismiller
if (face.is_facing && face.box_confidence > 60) { ... }
float targetX = -((box_left + width/2) / 127.5 - 1.0)
float targetY =  ((box_top + height/3) / 127.5 - 1.0)
eyes->setTargetPosition(targetX, targetY);  // default 120ms duration
// autoMove re-enables after FACE_LOST_TIMEOUT_MS via timeSinceFaceDetectedMs()
// Sensor physically mounted RIGHT-SIDE-UP — stock formula is correct
```

### Cron entries (Pi4 user crontab)
```
0 21 * * * ALSA_CARD=seeed2micvoicec /usr/bin/python3 /home/pi/iris_sleep.py >> /home/pi/logs/iris_sleep.log 2>&1
30 7 * * * ALSA_CARD=seeed2micvoicec /usr/bin/python3 /home/pi/iris_wake.py >> /home/pi/logs/iris_wake.log 2>&1
0 3 * * 0 sudo /bin/bash /home/pi/iris_backup.sh
```

---

## 12. SERIAL PROTOCOL

**Pi4 → Teensy:**
```
EMOTION:NEUTRAL/HAPPY/CURIOUS/ANGRY/SLEEPY/SURPRISED/SAD/CONFUSED
EYES:SLEEP / EYES:WAKE
EYE:n              -- switch default eye (0–6)
MOUTH:x            -- set mouth expression (0–8)
MOUTH_INTENSITY:n  -- set backlight level (0–15)
```
**Teensy → Pi4:** `FACE:1` / `FACE:0`
**Rule:** Only TeensyBridge owns `/dev/ttyACM0`. Everything else uses UDP → `127.0.0.1:10500`.

---

## 13. SLEEP STATE MACHINE

```
EYES:SLEEP: eyesSleeping=true, blankDisplays(), mouthSetSleepIntensity(),
            sleepRendererInit(), leds.show_sleep()
loop() while sleeping: processSerial(), renderSleepFrame(), mouthSleepFrame(), return
EYES:WAKE:  eyesSleeping=false, mouthRestoreIntensity(), setEyeDefinition(saved),
            applyEmotion(NEUTRAL), show_idle_for_mode(leds)
```

---

## 14. CHANGES THIS SESSION (S16 — 2026-04-14)

**GandalfAI C:\IRIS\ Centralization — COMPLETE**
- Created directory tree: `C:\IRIS\docker\`, `C:\IRIS\chatterbox\{reference_audio,voices,model_cache,logs,outputs}`, `C:\IRIS\ollama\`, `C:\IRIS\backup\`
- Robocopy (non-destructive, sources intact): `C:\docker\whisper` → `C:\IRIS\docker\whisper` (17 files, 3.0 GB), `C:\docker\piper` → `C:\IRIS\docker\piper` (29 files, 928 MB)
- Robocopy Chatterbox dirs: `reference_audio` (3 files, 5.9 MB), `voices` (28 files, 19.5 MB), `logs` (1 file), `model_cache` (empty), `outputs` (empty)
- Flat file copies: `config.yaml`, `jarvis_modelfile.txt`, `jarvis-kids_modelfile.txt`, `docker-compose.yml.bak`
- Wrote new `C:\IRIS\docker\docker-compose.yml` with all volume paths updated to `C:\IRIS\*` (HF cache left in user profile)
- Stopped old containers from `C:\docker\docker-compose.yml`, brought up from `C:\IRIS\docker\docker-compose.yml`
- Archived: `C:\docker\docker-compose.yml` → `C:\docker\docker-compose.yml.pre-iris.bak`
- All 5 containers verified: wyoming-whisper Up, wyoming-piper Up, open-webui healthy, watchtower healthy, chatterbox HTTP 200 (healthcheck `unhealthy` is false negative — GPU busy during curl timeout)

**Chatterbox config.yaml:**
- `last_chunk_size`: 120 → **300** at `C:\IRIS\chatterbox\config.yaml`

**Modelfile edits + ollama rebuild:**
- `C:\IRIS\ollama\jarvis_modelfile.txt`: RESPONSE STYLE sentence limit tightened (2 sentences / 30 words); HARD RULES appended date/time/location rule
- `C:\IRIS\ollama\jarvis-kids_modelfile.txt`: SAFETY section appended date/time/location rule
- `ollama create jarvis` — success (new layer sha: be12af6...)
- `ollama create jarvis-kids` — success (new layer sha: e94160f...)

**MCP scope clarification:**
- GandalfAI Claude Desktop filesystem MCP is scoped to `C:\Users\gandalf\` ONLY (not `C:\docker\` as previously documented). All `C:\IRIS\` and `C:\docker\` operations require Bash tool.

---

## 15. CURRENT KNOWN ISSUES / TODO

### HIGH
- **Mouth TFT expressions not yet smoke-tested beyond NEUTRAL** — confirm all 8 expressions (HAPPY, CURIOUS, ANGRY, SLEEPY, SURPRISED, SAD, CONFUSED) render correctly via `MOUTH:n` commands from Pi4.
- **End-to-end voice not tested** — iris_voice.wav confirmed present. Run live wakeword test, confirm Chatterbox renders cloned voice correctly.
- **implies_followup() gap** — IRIS doesn't reopen mic when LLM appends trailing sentence after `?`. Fix: modelfile hard rule first, then broaden reply[-80:] check.
- **Piper not installed as standalone binary** — iris_sleep.py "Goodnight" and wakeword-during-sleep "Good morning" silently fail. Route both through Wyoming Piper on GandalfAI port 10200.

### MEDIUM
- **Clean up old GandalfAI source locations** — Next session: after confirming stability, delete originals:
  - `C:\docker\whisper\`, `C:\docker\piper\` (data migrated to `C:\IRIS\docker\`)
  - `C:\Users\gandalf\Chatterbox-TTS-Server\` (migrated to `C:\IRIS\chatterbox\`)
  - `C:\Users\gandalf\jarvis_modelfile.txt`, `jarvis-kids_modelfile.txt` (migrated to `C:\IRIS\ollama\`)
- **Smoke test sleep LED** — Verify web UI Sleep button triggers indigo breathe. Wake restores idle cyan.
- **Exaggeration tuning** — 0.45 starting point. Tune after first live voice test.
- **Paralinguistic tag rendering** — Verify Chatterbox Turbo renders [chuckle] etc. as sounds, not literal text.
- **Chatterbox healthcheck fix** — `curl -f http://localhost:8000/` times out while GPU is busy. Either increase timeout in compose healthcheck or change to a lightweight `/health` endpoint. Currently harmless but noisy.
- **Chatterbox auto-start on Gandalf boot** — not configured. Currently requires manual `docker compose up` after reboot (compose file is now at `C:\IRIS\docker\docker-compose.yml`).

### LOW
- **Untracked files in project root** — iris_voice.wav, _decode_assistant.py, REFACTOR_VISUAL.md, IRIS_AUDIT_2026-04-03.md. Add wav to .gitignore, review/delete or commit others.
- **Old log file** — /home/pi/iris_sleep.log (root level, pre-S2) stale.
- **OWW_THRESHOLD** — Pi4 live = 0.9, config.py default = 0.85. Confirm intended value.

---

## 16. FLASH / DEPLOY COMMANDS

```bash
# Pi4 persist a file to SD:
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/<file> /media/root-ro/home/pi/<file>
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/<file> /media/root-ro/home/pi/<file>

# Pi4 restart assistant:
sudo systemctl restart assistant
journalctl -u assistant -n 30 --no-pager

# FLASH: Claude runs `pio run` only. User clicks PlatformIO upload. Teensy USB → Desktop PC.
# NEVER remote flash, NEVER transfer hex, NEVER run teensy_loader_cli.

# Bring up GandalfAI containers (after reboot or manual down):
docker compose -f C:\IRIS\docker\docker-compose.yml up -d
```

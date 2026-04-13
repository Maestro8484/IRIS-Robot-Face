# IRIS Robot Face — Handoff Snapshot
**Date:** 2026-04-12
**Session:** 15
**Branch:** `main` (refactor/modular-assistant merged into main — now on main)
**Last commit:** cb58fe0 — chore: S14 pre-migration snapshot update — GandalfAI Claude Desktop, centralization planned
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
| GandalfAI (Claude Desktop) | 192.168.1.3 | gandalf / 5309 | Claude Desktop + MCP installed (S14). Local filesystem MCP — direct access to C:\Users\gandalf\ and C:\docker\ (no SMB/SSH needed). |
| Teensy 4.1 | USB → Desktop PC | N/A | Dual GC9A01A 1.28" round TFT eyes + ILI9341 2.8" TFT mouth |
| Synology NAS | 192.168.1.102 | Master / Gateway!7007 | SSH port 2233. Backup: \\192.168.1.102\BACKUPS\IRIS-Robot-Face\ |

**Claude Desktop MCP filesystem scope:** `C:\Users\SuperMaster` (Desktop PC). GandalfAI Claude Desktop MCP scope: `C:\Users\gandalf\` and `C:\docker\` (direct access, no SMB/SSH needed — confirmed S15).
**SSH MCP tools:** `ssh-pi4` (192.168.1.200), `ssh-gandalf` (192.168.1.3), `ssh` (NAS, port 2233)
**Centralization plan:** Move primary Claude Code + MCP dev environment to GandalfAI (RTX 3090, always-on). C:\IRIS\ centralization plan approved but NOT YET EXECUTED — all GandalfAI files still at current locations.
**SSH auth:** Pi4 uses **password auth only** — key auth fails. Always connect with `username: pi`, `password: ohs`.
**GandalfAI:** Windows machine. No `df`, `head`, `grep` — use PowerShell / findstr / dir equivalents.

---

## 2. PROJECT STATUS

**Firmware:** Build clean 2026-04-11 (S9). NOT YET FLASHED — pending physical T4.1 swap. T4.0 last confirmed working state: eca1627.
**Person Sensor tracking:** CONFIRMED WORKING. Stock chrismiller code. Sensor physically mounted right-side-up. `is_facing && conf > 60`, 70ms poll, 120ms animation, stock coordinate formula. Eye tracks face laterally and vertically.
**Sleep display:** Starfield + ZZZ animation on both TFTs confirmed working.
**Sleep LEDs:** APA102 dim indigo breathe on EYES:SLEEP. peak=26, global_bright=0xFF, floor=3.
**Mouth during sleep:** Snore animation. TFT stays blank. BL dims to 40/255.
**Wake from webui:** Working. Cron sleep 9PM/7:30AM UDP path. False wakeword during cron window ignored (button-only override).
**Voice pipeline (assistant.py):** Operational. Modular (hardware/, core/, services/, state/).
**TTS routing:** Chatterbox (primary) → ElevenLabs (disabled) → Piper (fallback).
**Chatterbox server:** Running on GandalfAI at http://192.168.1.3:8004.
**ElevenLabs:** Disabled — `ELEVENLABS_ENABLED=False` in iris_config.json and config.py.
**Web UI:** Chatterbox-first Voice tab live. EYE:n switching (0–6), Sleep/Wake buttons, live state polling. Port 5000.
**NUM_PREDICT:** 120 in iris_config.json.
**Cron sleep/wake:** HARDENED. Single user crontab, ALSA_CARD env, correct log paths.
**ILI9341 TFT mouth:** Library switched to KurtE/ILI9341_t3n (auto-detects SPI bus from pin numbers). CS=36, DC=8, RST=4, MOSI=35, SCK=37 → SPI2. Build confirmed clean. Physical verification pending T4.1 swap.
**Flash workflow:** MANUAL ONLY — user clicks PlatformIO upload button, Teensy USB → Desktop PC. Claude runs `pio run` only.

---

## 3. CLAUDE CODE INFRASTRUCTURE

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

## 4. TEENSY 4.1 COMPLETE PIN ASSIGNMENT

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

### Free pins (T4.1)
5, 6, 7 (MAX7219), 15, 16, 17, 20, 21, 22, 23, 24, 25, 28, 29, 30, 31, 32, 33
Plus T4.1 extra: 38–41 (bottom header), 42–55 (extended pins)

---

## 5. MOUTH TFT STATUS — BUILD CLEAN, FLASH PENDING

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

## 6. CHATTERBOX TTS

- **Server:** GandalfAI `C:\Users\gandalf\Chatterbox-TTS-Server`, conda env `chatterbox`, port 8004
- **Model:** Chatterbox Turbo, exaggeration 0.45
- **Voice:** `iris_voice.wav` uploaded, confirmed filename
- **Endpoint:** `POST http://192.168.1.3:8004/tts` — `voice_mode: clone`, `reference_audio_filename: iris_voice.wav`
- **Confirmed working** post sleep/wake (S15). Root cause of prior failure: was running via `docker run` with `deploy.resources` GPU path instead of `runtime: nvidia` — fixed in consolidated compose.
- **PENDING:** `config.yaml` `last_chunk_size` change from 120 → 300 not yet applied.

---

## 7. REPO STRUCTURE

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
    mouth_tft.cpp/.h            -- ILI9341 TFT mouth driver (ILI9341_t3 hardware SPI2)
  pi4/                          -- mirrors /home/pi/ on Pi4
```

---

## 8. PLATFORM

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

## 9. KEY FILE STATE

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

## 10. SERIAL PROTOCOL

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

## 11. SLEEP STATE MACHINE

```
EYES:SLEEP: eyesSleeping=true, blankDisplays(), mouthSetSleepIntensity(),
            sleepRendererInit(), leds.show_sleep()
loop() while sleeping: processSerial(), renderSleepFrame(), mouthSleepFrame(), return
EYES:WAKE:  eyesSleeping=false, mouthRestoreIntensity(), setEyeDefinition(saved),
            applyEmotion(NEUTRAL), show_idle_for_mode(leds)
```

---

## 12. CHANGES THIS SESSION (S14 — 2026-04-12)

**S9 (2026-04-11):**
- Teensy 4.0 → Teensy 4.1 migration — `platformio.ini` board changed to `teensy41`
- Mouth TFT migrated from bit-bang to hardware SPI2 — replaced Arduino_GFX + Arduino_SWSPI with ILI9341_t3
- New mouth pins: MOSI=35, SCK=37, CS=36 (all SPI2); DC=8, RST=4, BL=14 unchanged
- Old bit-bang TFT pins freed; MAX7219 matrix retains 5/6/7 (DATA/CLK/CS)
- `paulstoffregen/ILI9341_t3` added to lib_deps; build confirmed clean

**S10 (2026-04-12):**
- Removed stale libs from `platformio.ini`: Adafruit BusIO, Adafruit GFX Library, Adafruit ILI9341, moononournation/GFX Library for Arduino
- Updated Section 4 pin table with confirmed wire colors and Right eye RST=-1
- Resolved wire color conflict note (confirmed: pin 2=Blue/left-eye-DC, pin 5=MAX7219-DATA; pin 0=Yellow/left-eye-CS, pin 8=Purple/mouth-DC)
- Build clean post lib_deps cleanup. Flash still pending physical T4.1 swap.
- Work on branch `feat/teensy41-spi2-mouth` — do NOT merge to main until flash confirmed.

**S11 (2026-04-12):**
- `platformio.ini`: replaced `adafruit/Adafruit BusIO`, `adafruit/Adafruit GFX Library`, `adafruit/Adafruit ILI9341` with `paulstoffregen/ILI9341_t3`
- `src/mouth_tft.cpp`: include changed to `<ILI9341_t3.h>`, instance type changed to `ILI9341_t3`, constructor changed to `ILI9341_t3 _tft(CS, DC, RST, MOSI, SCK)`
- Build confirmed clean: `[SUCCESS] Took 6.57 seconds`

**S12 (2026-04-12):**
- Root cause: `paulstoffregen/ILI9341_t3` silently ignores MOSI/SCK pin args on T4.x — always drives SPI0 (pins 11/13), never SPI2. Display backlight worked but controller never initialized.
- Fix: replaced with `KurtE/ILI9341_t3n` which auto-detects SPI bus from pin numbers passed to constructor.
- `platformio.ini`: `paulstoffregen/ILI9341_t3` → `https://github.com/KurtE/ILI9341_t3n`
- `src/mouth_tft.cpp`: `#include <ILI9341_t3n.h>`, instance type `ILI9341_t3n`. Constructor signature identical.
- Build confirmed clean: `[SUCCESS] Took 6.58 seconds` — `ILI9341_t3n @ sha.c2376f9` linked.
- T4.1 SPI bus allocation now clean: SPI0=right eye, SPI1=left eye, SPI2=mouth. No rewiring needed.
- RESULT: Bootloop on flash — static global ILI9341_t3n ctor runs before setup(), hard faults on SPI2 peripheral init.

**S13 (2026-04-12):**
- Root cause: static global object constructor for ILI9341_t3n executes before setup() on T4.x, hard faulting during SPI2 init. All displays dead + bootloop.
- Fix: heap-allocate `_tft` in `mouthTFTInit()` (same pattern as eye displays via `new` in `initEyes()`).
- `src/mouth_tft.cpp`: `static ILI9341_t3n *_tft = nullptr;` — `new ILI9341_t3n(...)` called at top of `mouthTFTInit()`. All `_tft.` → `_tft->`. Null guards added to all public API functions.
- Build confirmed clean: `[SUCCESS] Took 6.58 seconds`.
- RESULT: Bootloop on flash — ILI9341_t3n DMA static state conflicts with GC9A01A_t3n at startup.
- Fix (S14): Reverted to Arduino_GFX SWSPI (same library as confirmed-working T4.0 commit 732b069 on main).
  - `platformio.ini`: `KurtE/ILI9341_t3n` → `moononournation/GFX Library for Arduino @ ^1.4.9`
  - `src/mouth_tft.cpp`: include → `<Arduino_GFX_Library.h>`, heap-allocate `_bus` (Arduino_SWSPI) + `_tft` (Arduino_ILI9341) in `mouthTFTInit()`. Pins unchanged: MOSI=35, SCK=37, CS=36, DC=8, RST=4, BL=14.
  - Bit-bang on T4.1 pins 35/37/36 — no DMA, no hardware SPI conflict.
  - Build confirmed clean: `[SUCCESS] Took 7.89 seconds` — GFX Library for Arduino @ 1.6.5 linked.

**S14 (2026-04-12):**
- Pre-migration checklist session. No firmware changes.
- Claude Desktop installed on GandalfAI (192.168.1.3). Planned centralization of IRIS dev environment to GandalfAI.
- Fixed snapshot rotation discrepancy: Section 5 corrected to `rotation=3` (matches actual code).
- `MOUTH_TFT_HANDOFF.md` committed (stale — documents S11 attempt history, not current state).

**S15 (2026-04-12):**
- `refactor/modular-assistant` branch merged to `main`. Repo now on `main`.
- GandalfAI Claude Desktop confirmed installed with local filesystem MCP (direct access `C:\Users\gandalf\`, `C:\docker\` — no SMB/SSH needed).
- GandalfAI Docker Compose consolidated: `docker-compose.wyoming.yml` + `docker-compose.voice.yml` → `C:\docker\docker-compose.yml` (name: gandalf).
  - Includes: wyoming-whisper, wyoming-piper, chatterbox, open-webui, watchtower.
  - All GPU services use `runtime: nvidia`. open-webui uses named external volume.
- Chatterbox confirmed working post sleep/wake. Root cause: was `docker run` with `deploy.resources` GPU path instead of `runtime: nvidia` — fixed in new compose.
- **PENDING items (not yet done):**
  1. `C:\IRIS\` directory centralization — GandalfAI files still at: `C:\docker\`, `C:\Users\gandalf\Chatterbox-TTS-Server\`, `C:\Users\gandalf\jarvis_modelfile.txt`
  2. jarvis modelfile edits not yet applied — two queued changes:
     - RESPONSE STYLE: "Keep all responses under 2 sentences and under 30 words unless the question genuinely requires detail. When in doubt, say less."
     - HARD RULES append: "Never volunteer the current date, time, or location in a response unless the user explicitly asked for it."
  3. Chatterbox `config.yaml` `last_chunk_size`: 120 → 300 not yet applied

---

## 13. CURRENT KNOWN ISSUES / TODO

### HIGH
- **Mouth TFT expressions not yet smoke-tested beyond NEUTRAL** — confirm all 8 expressions (HAPPY, CURIOUS, ANGRY, SLEEPY, SURPRISED, SAD, CONFUSED) render correctly via `MOUTH:n` commands from Pi4.
- **End-to-end voice not tested** — iris_voice.wav uploaded. Run live wakeword test, confirm Chatterbox renders cloned voice.
- **implies_followup() gap** — IRIS doesn't reopen mic when LLM appends trailing sentence after `?`. Fix: modelfile hard rule first, then broaden reply[-80:] check.
- **Piper not installed as standalone binary** — iris_sleep.py "Goodnight" and wakeword-during-sleep "Good morning" silently fail. Route both through Wyoming Piper on GandalfAI port 10200.

### MEDIUM
- **Smoke test sleep LED** — Verify web UI Sleep button triggers indigo breathe. Wake restores idle cyan.
- **Exaggeration tuning** — 0.45 starting point. Tune after first live voice test.
- **Paralinguistic tag rendering** — Verify Chatterbox Turbo renders [chuckle] etc. as sounds, not literal text.

### MEDIUM — GandalfAI / Infrastructure
- **C:\IRIS\ centralization (APPROVED, NOT DONE)** — Move all GandalfAI IRIS-related files to `C:\IRIS\`. Current locations: `C:\docker\docker-compose.yml`, `C:\Users\gandalf\Chatterbox-TTS-Server\`, `C:\Users\gandalf\jarvis_modelfile.txt`.
- **jarvis modelfile edits (QUEUED, NOT APPLIED):**
  1. RESPONSE STYLE rule: responses under 2 sentences / 30 words unless detail required.
  2. HARD RULE: never volunteer date/time/location unprompted.
- **Chatterbox config.yaml last_chunk_size (QUEUED):** 120 → 300.

### LOW
- **Untracked files in project root** — iris_voice.wav, _decode_assistant.py, REFACTOR_VISUAL.md, IRIS_AUDIT_2026-04-03.md. Add wav to .gitignore, review/delete or commit others.
- **Old log file** — /home/pi/iris_sleep.log (root level, pre-S2) stale.
- **Chatterbox auto-start on Gandalf boot** — not configured.
- **OWW_THRESHOLD** — Pi4 live = 0.9, config.py default = 0.85. Confirm intended value.

---

## 14. FLASH / DEPLOY COMMANDS

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
```

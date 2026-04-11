# IRIS Robot Face — Handoff Snapshot
**Date:** 2026-04-10
**Session:** 7
**Branch:** `main`
**Last commit:** `f7b6921` (docs: snapshot S6 update — mouth TFT Arduino_GFX confirmed working)
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
| Teensy 4.0 | USB → /dev/ttyACM0 on Pi4 | N/A | Dual GC9A01A 1.28" round TFT eyes + ILI9341 2.8" TFT mouth |
| Synology NAS | 192.168.1.102 | Master / Gateway!7007 | SSH port 2233. Backup: \\192.168.1.102\BACKUPS\IRIS-Robot-Face\ |

**Claude Desktop MCP filesystem scope:** `C:\Users\SuperMaster`
**SSH MCP tools:** `ssh-pi4` (192.168.1.200), `ssh-gandalf` (192.168.1.3), `ssh` (NAS, port 2233)
**SSH auth:** Pi4 uses **password auth only** — key auth fails. Always connect with `username: pi`, `password: ohs`.
**GandalfAI:** Windows machine. No `df`, `head`, `grep` — use PowerShell / findstr / dir equivalents.

---

## 2. PROJECT STATUS

**Firmware:** Flashed 2026-04-10 (S7). Person Sensor tracking — aggressive lock-on, no politeness.
**Person Sensor tracking:** CONFIRMED WORKING. `[PS] face 0 conf=99 facing=1` visible in journal. Removed `is_facing` gate, threshold 60→25, poll 70→50ms.
**Sleep display:** Starfield + ZZZ animation on both TFTs confirmed working.
**Sleep LEDs:** APA102 dim indigo breathe on EYES:SLEEP. peak=26 (~10% of 255), global_bright=0xFF, floor=3. LED_SLEEP_* constants in config.py. show_sleep() wired into CMD listener. Restores idle on EYES:WAKE. Deployed S1.
**Mouth during sleep:** Snore animation (mouth_tft.cpp mouthSleepFrame no-op — TFT stays blank during sleep). BL dims to 40/255 via analogWrite.
**Wake from webui:** Working. Cron sleep: 9PM/7:30AM UDP path. False wakeword during cron window now ignored (button-only override).
**Voice pipeline (assistant.py):** Operational. Modular (hardware/, core/, services/, state/).
**TTS routing:** Chatterbox (primary) → ElevenLabs (disabled via iris_config.json) → Piper (fallback).
**Chatterbox server:** Running on GandalfAI. Web UI confirmed accessible at http://192.168.1.3:8004.
**Jarvis modelfile:** Updated with PARALINGUISTIC TAGS section. `ollama create jarvis` completed.
**ElevenLabs:** Disabled — `ELEVENLABS_ENABLED=False` in `/home/pi/iris_config.json` AND default False in config.py.
**Web UI:** Chatterbox-first Voice tab live. EYE:n switching (0–6), Sleep/Wake buttons, live state polling. Port 5000.
**Face tracking:** WORKING + AGGRESSIVE. setTargetPosition seed fix in EyeController.h. is_facing gate removed. conf threshold 25. Poll 50ms.
**NUM_PREDICT:** 120 in iris_config.json (overrides config.py default of 150).
**Cron sleep/wake:** HARDENED. Single user crontab, ALSA_CARD env, correct log paths, duplicate /etc/cron.d/iris removed.
**ILI9341 TFT mouth:** WORKING. Arduino_GFX + Arduino_SWSPI confirmed. NEUTRAL cyan slightly upward-curved expression visible on boot. Flashed and verified 2026-04-08.
**flash-remote skill:** UPDATED — software bootloader entry confirmed working (no PROG button needed).

---

## 3. CLAUDE CODE INFRASTRUCTURE

### Slash Commands
| Command | File | Purpose |
|---|---|---|
| `/flash` | `.claude/commands/flash.md` | Local USB flash via PlatformIO |
| `/flash-remote` | `.claude/commands/flash-remote.md` | Remote flash via Pi4 SSH (software bootloader — no PROG button needed) |
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

### Software Bootloader Entry (Teensy in enclosure — CONFIRMED WORKING)
```bash
python3 -c "import serial, time; s=serial.Serial('/dev/ttyACM0',134); time.sleep(0.5); s.close()"
```
No PROG button required. Re-enumerates as HalfKay (`16c0:0478`) reliably.

---

## 4. TEENSY 4.0 COMPLETE PIN ASSIGNMENT

### Eye displays (GC9A01A, config.h)
| Pin | Signal | Device | Wire Color |
|---|---|---|---|
| 0 | CS | Left eye (SPI1) | Yellow |
| 2 | DC | Left eye (SPI1) | Blue |
| 3 | RST | Left eye (SPI1) | Brown |
| 9 | DC | Right eye (SPI0) | — |
| 10 | CS | Right eye (SPI0) | — |
| 11 | MOSI | Right eye (SPI0 hardware) | — |
| 13 | SCK | Right eye (SPI0 hardware) | — |
| 26 | MOSI | Left eye (SPI1 hardware) | — |
| 27 | SCK | Left eye (SPI1 hardware) | — |

### Person Sensor (I2C)
| Pin | Signal | Device | Wire Color |
|---|---|---|---|
| 18 | SDA | Person Sensor | — |
| 19 | SCL | Person Sensor | — |

### ILI9341 TFT Mouth (mouth_tft.cpp, bit-bang SPI)
| Pin | Signal | Device | Wire Color |
|---|---|---|---|
| 4 | RST | Mouth TFT | Green |
| 5 | MOSI / DIN | Mouth TFT | Blue* |
| 6 | SCK / CLK | Mouth TFT | Purple |
| 7 | CS | Mouth TFT | Gray |
| 8 | DC | Mouth TFT | Yellow* |
| 14 | BL (backlight) | Mouth TFT LED | White |
| 3.3V | VCC | Mouth TFT | Red |
| GND | GND | Mouth TFT | Black |

> **Wire color conflict to resolve:** Pin 2 (Left eye DC) and Pin 5 (Mouth MOSI) are both noted as Blue. Pin 0 (Left eye CS) and Pin 8 (Mouth DC) are both noted as Yellow. Confirm actual wire colors on bench and update snapshot accordingly.

### Free pins (confirmed unallocated)
15, 16, 17, 20, 21, 22, 23, 24, 25, 28, 29, 30, 31, 32, 33

---

## 5. MOUTH TFT STATUS — CONFIRMED WORKING

**Library:** `moononournation/GFX Library for Arduino@^1.4.9` via `Arduino_SWSPI` + `Arduino_ILI9341`
**Confirmed:** NEUTRAL cyan upward-curved expression visible on boot. Flashed 2026-04-08.

**src/mouth_tft.cpp constructor:**
```cpp
#include <Arduino_GFX_Library.h>
static Arduino_DataBus *_bus = new Arduino_SWSPI(
    MOUTH_TFT_DC, MOUTH_TFT_CS, MOUTH_TFT_SCK, MOUTH_TFT_MOSI, -1);
static Arduino_ILI9341 *_tft = new Arduino_ILI9341(_bus, MOUTH_TFT_RST, 1 /*rotation*/);
```

**Pending cleanup:** `adafruit/Adafruit ILI9341@^1.5.10` still in platformio.ini — unused, can be removed.

---

## 6. CHATTERBOX TTS

### GandalfAI Setup
- **Repo cloned:** `C:\Users\gandalf\Chatterbox-TTS-Server` (devnen/Chatterbox-TTS-Server)
- **Conda env:** `chatterbox` (Python 3.12) at `C:\Users\gandalf\miniconda3\envs\chatterbox\`
- **Launch script:** `C:\Users\gandalf\Chatterbox-TTS-Server\run_server.bat`
- **Model:** Chatterbox Turbo (`repo_id: chatterbox-turbo` in config.yaml)
- **Exaggeration:** 0.45
- **Port:** 8004

### Voice Clone
- `iris_voice.wav` uploaded to Chatterbox Web UI. Confirmed filename: `iris_voice.wav`.
- Pi4 config: `CHATTERBOX_VOICE = "iris_voice.wav"`

### Pi4 TTS Endpoint
```
POST http://192.168.1.3:8004/tts
{ "text": "...", "voice_mode": "clone", "reference_audio_filename": "iris_voice.wav",
  "exaggeration": 0.45, "output_format": "wav" }
```

---

## 7. REPO STRUCTURE

```
IRIS-Robot-Face/
  src/
    main.cpp                    -- serial parsing, emotion/tracking/sleep logic
    config.h                    -- eye definitions array (7 eyes), display pins
    sleep_renderer.h            -- deep space starfield (SR_FRAME_MS=150)
    displays/GC9A01A_Display.h  -- display driver + fillBlack + getDriver()
    eyes/EyeController.h        -- eye movement/blink/pupil (do NOT break setTargetPosition seed fix)
    eyes/240x240/               -- nordicBlue/flame/hypnoRed/hazel/blueFlame1/dragon/bigBlue .h
    sensors/PersonSensor.h/.cpp -- I2C face detection (SAMPLE_TIME_MS=50, conf threshold=25)
    mouth.h                     -- MAX7219 stub (superseded by mouth_tft — not included)
    mouth_tft.cpp               -- ILI9341 TFT mouth driver (Arduino_GFX SWSPI)
    mouth_tft.h                 -- public API: mouthTFTInit, mouthTFTShow, intensity helpers
  scripts/
    patch_gc9a01a.py            -- PlatformIO pre-build; re-applies drawChar fix
  pi4/ (mirrors /home/pi/ on Pi4):
    assistant.py / core/ / services/ / hardware/ / state/
    iris_config.json            -- runtime overrides
    iris_sleep.py / iris_wake.py / iris_web.py / iris_web.html
```

---

## 8. PLATFORM

```ini
[env:eyes]
platform = https://github.com/platformio/platform-teensy.git
board = teensy40
framework = arduino
monitor_speed = 115200
build_flags = -std=gnu++17 -O2 -D TEENSY_OPT_SMALLEST_CODE
extra_scripts = pre:scripts/patch_gc9a01a.py
lib_deps =
  https://github.com/PaulStoffregen/Wire
  https://github.com/PaulStoffregen/ST7735_t3
  https://github.com/mjs513/GC9A01A_t3n
  adafruit/Adafruit BusIO @ ^1.14.1
  adafruit/Adafruit GFX Library@^1.11.3
  adafruit/Adafruit ILI9341@^1.5.10
  moononournation/GFX Library for Arduino@^1.4.9
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

### src/sensors/PersonSensor.h — Tracking constants (S7)
```cpp
SAMPLE_TIME_MS = 50   // was 70 — tightened for faster gaze updates
```

### src/main.cpp — Person Sensor tracking loop (S7)
```cpp
// is_facing check REMOVED — track any face regardless of orientation
// confidence threshold: 25 (was 60)
// debug: [PS] face N conf=X facing=Y printed every read
if (face.box_confidence > 25) { ... }
```

### mouth_tft.cpp — Pin map and backlight
```
Pin  4 = RST
Pin  5 = MOSI (bit-bang SPI)  [Blue*]
Pin  6 = SCK  (bit-bang SPI)  [Purple]
Pin  7 = CS                   [Gray]
Pin  8 = DC                   [Yellow*]
Pin 14 = BL   (PWM: 220 boot/wake, 40 sleep, level*17 for MOUTH_INTENSITY cmd)
* Wire color conflict — see Section 4 note
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
EYE:n          -- switch default eye (0–6)
MOUTH:x        -- set mouth expression (0–8)
MOUTH_INTENSITY:n  -- set backlight level (0–15)
```
**Teensy → Pi4:** `FACE:1` / `FACE:0`
**Rule:** Only `assistant.py` TeensyBridge owns `/dev/ttyACM0`. Everything else uses UDP → `127.0.0.1:10500`.

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

## 12. CHANGES THIS SESSION (S7 — 2026-04-10)

### Person Sensor tracking — aggressive lock-on
- **`src/sensors/PersonSensor.h:65`** — `SAMPLE_TIME_MS` 70 → **50ms** (tighter poll)
- **`src/main.cpp:325`** — removed `face.is_facing &&` gate (was politeness logic added in prior session)
- **`src/main.cpp:325`** — confidence threshold `> 60` → **`> 25`**
- **`src/main.cpp`** — added `[PS] face N conf=X facing=Y` debug print per face per read cycle
- Flashed via software bootloader (Pi4 ssh) — no PROG button needed. Verified in journal: `[PS] face 0 conf=99 facing=1` visible.

### flash-remote skill updated
- **`.claude/commands/flash-remote.md`** — replaced "Physical PROG button required" with confirmed software bootloader entry. Step 5 updated to use python3 serial trick. `16c0:0478` confirmed.

---

## 13. CURRENT KNOWN ISSUES / TODO

### HIGH
- **Mouth TFT expressions not yet smoke-tested beyond NEUTRAL** — confirm all 8 expressions (HAPPY, CURIOUS, ANGRY, SLEEPY, SURPRISED, SAD, CONFUSED) render correctly via `MOUTH:n` commands from Pi4.
- **End-to-end voice not tested** — iris_voice.wav uploaded. Run live wakeword test, confirm Chatterbox renders cloned voice.
- **implies_followup() gap** — IRIS doesn't reopen mic when LLM appends trailing sentence after `?`. Fix: modelfile hard rule first, then broaden reply[-80:] check.
- **Piper not installed as standalone binary** — iris_sleep.py "Goodnight" and wakeword-during-sleep "Good morning" silently fail. Route both through Wyoming Piper on GandalfAI port 10200.

### MEDIUM
- **Smoke test sleep LED** — Verify web UI Sleep button triggers indigo breathe. Wake restores idle cyan.
- **Matrix brightness** — mouthRestoreIntensity and mouthSetSleepIntensity both 0x01 (now ILI9341 BL 220/40). Verify awake expressions not too dim after live test.
- **Wire color conflict** — Pin 2 and Pin 5 both Blue; Pin 0 and Pin 8 both Yellow. Confirm bench colors, update snapshot.
- **Exaggeration tuning** — 0.45 starting point. Tune after first live voice test.
- **Paralinguistic tag rendering** — Verify Chatterbox Turbo renders [chuckle] etc. as sounds, not literal text.
- **Remove Adafruit ILI9341 from platformio.ini** — unused after Arduino_GFX confirmed working; remove to keep build clean.
- **Tracking tuning** — conf threshold=25 is aggressive; may track partial/side faces. Tune up if false-lock becomes an issue. `facing=` is still printed so easy to correlate.

### LOW
- **Untracked files in project root** — iris_voice.wav, _decode_assistant.py, REFACTOR_VISUAL.md, IRIS_AUDIT_2026-04-03.md. Add wav to .gitignore, review/delete or commit others.
- **Old log file** — /home/pi/iris_sleep.log (root level, pre-S2) stale. Delete after confirming /home/pi/logs/iris_sleep.log active.
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

# Teensy software bootloader (no PROG button — CONFIRMED WORKING):
python3 -c "import serial, time; s=serial.Serial('/dev/ttyACM0',134); time.sleep(0.5); s.close()"

# Remote flash full sequence (from desktop):
# 1. pio run  (builds .pio/build/eyes/firmware.hex)
# 2. python3 paramiko sftp.put firmware.hex pi@192.168.1.200:/tmp/iris_firmware.hex
# 3. ssh pi@192.168.1.200 "sudo systemctl stop assistant"
# 4. ssh pi@192.168.1.200 "python3 -c \"import serial,time;s=serial.Serial('/dev/ttyACM0',134);time.sleep(0.5);s.close()\""
# 5. ssh pi@192.168.1.200 "sudo teensy_loader_cli --mcu=TEENSY40 -w -v /tmp/iris_firmware.hex"
# 6. ssh pi@192.168.1.200 "sudo systemctl start assistant"
```

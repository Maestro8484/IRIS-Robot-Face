# IRIS Robot Face — Updated Snapshot
**Date:** 2026-03-24 (updated, reflects both today's review session and Claude Code session)
**For use in:** Claude Desktop Chat or Claude Code tab
**Repo:** `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face` | branch: `iris-ai-integration`

Paste this at the start of a new session. Then say what you want to work on.

---

## 1. SYSTEM ARCHITECTURE

| System | IP | Credentials | Role |
|---|---|---|---|
| Pi4 (IRIS / Jarvis) | 192.168.1.200 | pi / ohs | Voice pipeline, LEDs, camera, Teensy serial |
| GandalfAI | 192.168.1.3 | gandalf / 5309 | Ollama LLM (gemma3:27b), Whisper STT, Piper TTS, RTX 3090 |
| Desktop PC | 192.168.1.103 | SuperMaster | PlatformIO firmware, VS Code, Claude Desktop |
| Teensy 4.0 | USB → /dev/ttyACM0 | N/A | Dual GC9A01A 1.28" round TFT eyes, emotion rendering |

**Claude Desktop MCP filesystem scope:** `C:\Users\SuperMaster`
**SSH tools:** `ssh-pi4` (192.168.1.200), `ssh-gandalf` (192.168.1.3)

---

## 2. PROJECT STATUS

**Firmware:** Fully operational. Flashed and confirmed working.
**Serial protocol:** Operational — EMOTION:x, EYES:SLEEP/WAKE, FACE:1/FACE:0.
**fillBlack async fix:** Confirmed present in `GC9A01A_Display.h`. Note: `asyncUpdates` is currently `false` in `config.h` for both displays, so this is defensive but inactive.
**Eye system:** nordicBlue (default) + flame (ANGRY), both rendering correctly.
**Voice pipeline (assistant.py):** Operational on Pi4. ElevenLabs Starter tier active.

---

## 3. REPO STRUCTURE

```
IRIS-Robot-Face/
  src/
    main.cpp                    -- serial parsing, emotion/tracking/sleep logic
    config.h                    -- eye definitions, display pins, global pointers
    TeensyEyes.ino              -- upstream eye engine (DO NOT MODIFY)
    displays/
      GC9A01A_Display.h         -- display driver + fillBlack async fix
    eyes/
      eye_params.h              -- eye parameter structs
      240x240/
        nordicBlue.h            -- generated eye header (nordicBlue)
        flame.h                 -- generated eye header (flame)
        polarDist_240_*.cpp/h   -- polar distortion tables
    sensors/
      PersonSensor.h            -- I2C face/person sensor
      LightSensor.h             -- ambient light sensor
    util/
      logging.h                 -- DumpMemoryInfo, debug macros
  resources/
    eyes/240x240/
      nordicBlue/config.eye     -- JSON eye config (edit here for pupil/eyelid tweaks)
      flame/config.eye          -- flame eye config
      nordicBlue - Copy/        -- backup of nordicBlue before edits
      hazel - Copy/             -- hazel backup (not used in firmware)
  servo_teensy/
    servo_teensy.ino            -- standalone Pico servo sketch (not deployed yet)
  platformio.ini
```

---

## 4. PLATFORM

```ini
[env:eyes]
platform = https://github.com/platformio/platform-teensy.git
board = teensy40
framework = arduino
monitor_speed = 115200
build_flags = -std=gnu++17 -O2
lib_deps =
  PaulStoffregen/Wire
  PaulStoffregen/ST7735_t3
  mjs513/GC9A01A_t3n
  adafruit/Adafruit BusIO
  adafruit/Adafruit GFX Library
```

**Flash:** PlatformIO Upload / `pio run -t upload`
**Serial monitor:** 115200 baud
**Teensy USB port on Pi4:** `/dev/ttyACM0`

---

## 5. KEY FILE STATE (as of 2026-03-24 review)

### `src/config.h`
```cpp
// Eye definitions array:
// [0] = nordicBlue (both L+R) -- default
// [1] = flame (both L+R)      -- ANGRY only

GC9A01A_Config eyeInfo[] = {
    // CS  DC  MOSI SCK  RST ROT MIRROR  USE_FB  ASYNC
    {0,   2,  26,  27,  3,  0,  true,   true,   false},  // Left
    {10,  9,  11,  13, -1,  0,  false,  true,   false},  // Right
};

constexpr uint32_t SPI_SPEED{20'000'000};
constexpr int8_t BLINK_PIN{-1};
constexpr int8_t JOYSTICK_X_PIN{-1};
constexpr int8_t JOYSTICK_Y_PIN{-1};
constexpr int8_t LIGHT_PIN{-1};
constexpr bool USE_PERSON_SENSOR{true};
```
**Note:** `asyncUpdates = false` -- frame buffer is used but DMA async is off.

### `src/displays/GC9A01A_Display.h` — fillBlack fix
```cpp
void fillBlack() {
    uint32_t timeout = millis() + 200;
    while (display->asyncUpdateActive() && millis() < timeout) { delay(1); }
    display->fillScreen(0x0000);
    display->updateScreen();
}
```
Status: **confirmed present and correct**. Defensive since async is off, but harmless.

### `src/main.cpp` — key constants
```cpp
TRACKING_WINDOW_MS    = 15000   // face tracking active after non-NEUTRAL emotion
FACE_LOST_TIMEOUT_MS  =  5000   // stop tracking if face gone this long
FACE_COOLDOWN_MS      = 30000   // cooldown before re-enabling tracking
ANGRY_EYE_DURATION_MS =  9000   // flame eye hold before auto-revert to nordicBlue
EYE_IDX_DEFAULT = 0             // nordicBlue
EYE_IDX_ANGRY   = 1             // flame
SERIAL_BUF_SIZE = 32
```

### Emotion table (`main.cpp`)
| Emotion | pupilRatio | doBlink | maxGazeMs |
|---|---|---|---|
| NEUTRAL | 0.40 | false | 3000 |
| HAPPY | 0.75 | true | 1500 |
| CURIOUS | 0.60 | false | 4000 |
| ANGRY | 0.15 | false | 800 |
| SLEEPY | 0.85 | true | 5000 |
| SURPRISED | 0.95 | true | 600 |
| SAD | 0.25 | true | 4000 |

### `resources/eyes/240x240/nordicBlue/config.eye` (current values)
```json
{
  "name"      : "nordicBlue",
  "radius"    : 125,
  "backColor" : 0,
  "pupil"     : { "color": 0, "min": 0.25, "max": 0.55 },
  "iris"      : { "texture": "iris.png", "radius": 64 },
  "sclera"    : { "texture": "sclera.png" },
  "eyelid"    : { "color": 0, "upperFilename": "upper.png", "lowerFilename": "lower.png" }
}
```
**Note:** Pupil NOT yet shrunk. Eyelid droop NOT yet adjusted. `nordicBlue - Copy/` is the safe backup.

---

## 6. SERIAL PROTOCOL

**Pi4 → Teensy:**
```
EMOTION:NEUTRAL\n     -- idle, locks tracking, autoMove on
EMOTION:HAPPY\n
EMOTION:CURIOUS\n
EMOTION:ANGRY\n       -- flame eyes, 9s auto-revert to nordicBlue
EMOTION:SLEEPY\n
EMOTION:SURPRISED\n
EMOTION:SAD\n
EYES:SLEEP\n          -- both displays black, rendering halted
EYES:WAKE\n           -- restore nordicBlue, resume, apply NEUTRAL
```

**Teensy → Pi4:**
```
FACE:1\n    -- face detected (30s cooldown between sends)
FACE:0\n    -- face lost
```

---

## 7. ASSISTANT.PY KEY CONFIG (Pi4)

```python
GANDALF             = "192.168.1.3"
ELEVENLABS_API_KEY  = "sk_752184d377335347d38c185ba56a1bebe9deba4da50ce082"
ELEVENLABS_VOICE_ID = "90eMKEeSf5nhJZMJeeVZ"   # updated 2026-03-24
ELEVENLABS_MODEL    = "eleven_turbo_v2_5"
ELEVENLABS_ENABLED  = True
OLLAMA_MODEL_ADULT  = "jarvis"
OLLAMA_MODEL_KIDS   = "jarvis-kids"
VISION_MODEL        = "jarvis"
WAKE_WORD           = "hey_jarvis"
OWW_THRESHOLD       = 0.7
TEENSY_PORT         = "/dev/ttyACM0"
TEENSY_BAUD         = 115200
BUTTON_PIN          = 17
```

**Audio chain:** LLM → ElevenLabs/Piper TTS → play_pcm() 3.0x gain → wm8960 HAT → PAM8403 amp → 2× 3W speakers
**ALSA:** Speaker=120, HP=120, DC/AC=5 | pyaudio device index: **6** (NOT 0)
**Pop fix:** 80ms silence padding on ElevenLabs output.

---

## 8. EMOTION → LED MAPPING (assistant.py)

| Emotion | LED color | Period |
|---|---|---|
| NEUTRAL | Cyan breathe | 5.0s |
| HAPPY | Warm yellow | 3.0s |
| CURIOUS | Bright cyan | 3.5s |
| ANGRY | Red | 2.0s |
| SLEEPY | Dim purple | 6.0s |
| SURPRISED | White flash | 0.3s |
| SAD | Dim blue | 6.0s |

LED breathing: `floor=3, peak=65, period=5.0s`, gamma 1.8

---

## 9. PI4 OVERLAYFS — CRITICAL

SD is read-only. All SSH writes go to RAM and are wiped on reboot.

**Persist any file:**
```bash
sudo mount -o remount,rw /media/root-ro
cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
```

---

## 10. WHAT HAPPENED IN RECENT CLAUDE SESSIONS

### Session: "review IRIS robot face assistant code" (2026-03-24 earlier)
- Reviewed `assistant.py` on Pi4 for correctness — no code changes made
- Reviewed Teensy firmware: `main.cpp`, `config.h`, `GC9A01A_Display.h`
- Confirmed `fillBlack()` async fix is present and correct
- Noted `asyncUpdates = false` in config — fix is defensive, displays not actually async
- Generated `SNAPSHOT_2026-03-24-CHAT.md` and `SNAPSHOT_2026-03-24-CODE.md` (now committed)
- Updated `.gitignore` to exclude `.claude/worktrees/` artifacts
- Committed all pending work as "Current working build - March 2026" (commit `684de14`)
- Archived previous snapshots (3/16, 3/17, 3/21, 3/21b, 3/22, 3/22b) into repo
- Backed up nordicBlue eye to `nordicBlue - Copy/` and hazel to `hazel - Copy/`

### This session (2026-03-24 current)
- Generated this updated consolidated snapshot (`SNAPSHOT_2026-03-24-UPDATED.md`)
- Updated `ELEVENLABS_VOICE_ID` → `90eMKEeSf5nhJZMJeeVZ` in `/home/pi/assistant.py`
- Persisted assistant.py to SD (`/media/root-ro/home/pi/assistant.py`), md5 verified match
- Restarted assistant.service — confirmed active (PID 4576)
- Compiled and uploaded firmware to Teensy 4.0 via `pio run -t upload` — build SUCCESS (19.29s)
  - Teensy Loader launched; user pressed PROG button to complete flash
- Marked completed: Pico servo deploy, Physical base redesign, ElevenLabs voice update

---

## 11. PENDING ITEMS (prioritized)

| Priority | Item | Details |
|---|---|---|
| 1 | **Pupil size shrink** | Megan feedback: too large/unsettling. Reduce `max` from 0.55 → ~0.40, `min` from 0.25 → ~0.18 in `nordicBlue/config.eye`. Rerun `genall.py` to regenerate `nordicBlue.h`, then recompile + reflash. Backup exists at `nordicBlue - Copy/`. |
| 2 | **Eyelid droop fix** | Upper eyelid droops too much. Edit `upper.png` in nordicBlue (or adjust eyelid params if supported). Rerun `genall.py`, reflash. |
| 3 | **Go public on GitHub** | Repo currently private. Go public when ready to post YouTube/Reddit/Hackster. |
| ✅ | ~~New ElevenLabs voice~~ | Updated to voice ID `90eMKEeSf5nhJZMJeeVZ` in `assistant.py`. Persisted to SD. Service restarted 2026-03-24. |
| ✅ | ~~Pico servo deploy~~ | Physical pan servo wired and deployed. Completed 2026-03-24. |
| ✅ | ~~Physical base redesign~~ | Entirely remade. Completed 2026-03-24. |

---

## 12. QUICK REFERENCE

**Restart Jarvis (Pi4):**
```bash
pkill -f assistant.py; sleep 1; nohup python3 -u /home/pi/assistant.py > /dev/null 2>&1 < /dev/null &
```

**Persist assistant.py to SD:**
```bash
sudo mount -o remount,rw /media/root-ro && cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py && sudo mount -o remount,ro /media/root-ro && md5sum /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
```

**Live log:**
```bash
journalctl -u assistant -f | grep -v "ALSA\|Jack\|pulse\|seeed\|pcm\|conf\|hdmi\|usb\|modem\|JackShm\|server"
```

**GandalfAI VRAM:**
```bash
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader
```

**Rebuild Ollama models (GandalfAI):**
```
ollama create jarvis -f "C:\Users\gandalf\jarvis_modelfile.txt"
ollama create jarvis-kids -f "C:\Users\gandalf\jarvis-kids_modelfile.txt"
```

**Git commit and push (Desktop):**
```powershell
cd "C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face"
git add -A
git commit -m "describe what changed"
git push origin HEAD
```

**Eye config workflow (nordicBlue tweak):**
1. Edit `resources/eyes/240x240/nordicBlue/config.eye`
2. Run `python resources/eyes/240x240/genall.py` to regenerate `nordicBlue.h`
3. PlatformIO Upload
4. Test via serial monitor 115200

---

## 13. HOME LAB NETWORK

| Host | IP | Credentials |
|---|---|---|
| GandalfAI | 192.168.1.3 | gandalf / 5309 |
| Pi4 IRIS/Jarvis | 192.168.1.200 | pi / ohs |
| Pi5 Batocera | 192.168.1.67 | root / linux |
| Proxmox | 192.168.1.5 | root |
| Home Assistant | 192.168.1.22 | root / ohs |
| Synology NAS | 192.168.1.102 | -- |
| Desktop PC | 192.168.1.103 | SuperMaster |

---

## 14. NOTES FOR CLAUDE CODE

- Do NOT modify `TeensyEyes.ino` — upstream engine, changes conflict
- Eye appearance: edit `resources/eyes/240x240/nordicBlue/config.eye`, regenerate header
- Emotion/serial/tracking logic: `src/main.cpp`
- Display driver: `src/displays/GC9A01A_Display.h`
- The `.claude/` directory is in `.gitignore` — worktrees go there, don't fight it
- After any firmware change: PlatformIO Upload → serial monitor test at 115200

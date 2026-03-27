# IRIS Robot Face — Claude Code Snapshot
**Date:** 2026-03-24
**For use in:** Claude Desktop Code tab
**Repo path:** `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face`

Paste this at the start of a Claude Code session. Then say what you want to change.

---

## PROJECT SUMMARY

Teensy 4.0 firmware for IRIS robot face. Two GC9A01A round TFT displays (1.28") driven by TeensyEyes animated eye engine. Custom emotion system driven by serial commands from Pi4 voice assistant.

**Status:** Fully operational. fillBlack async fix deployed and confirmed.

---

## REPO STRUCTURE

```
IRIS-Robot-Face/
  src/
    main.cpp                    -- main loop, serial parsing, emotion/tracking logic
    config.h                    -- eye definitions, display pins, global pointers
    TeensyEyes.ino              -- eye rendering engine (do not modify)
    displays/
      GC9A01A_Display.h         -- display driver, fillBlack async fix lives here
    eyes/
      eye_params.h              -- eye parameter structs
    sensors/
      PersonSensor.h            -- I2C person/face sensor
      LightSensor.h             -- ambient light
    util/
      logging.h                 -- debug macros
  platformio.ini                -- board: teensy40, framework: arduino, C++17
```

---

## PLATFORM

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

**Flash command:** PlatformIO: Upload (or `pio run -t upload`)
**Serial monitor:** 115200 baud
**USB port on Pi4:** `/dev/ttyACM0`

---

## SERIAL PROTOCOL (Pi4 -> Teensy)

```
EMOTION:NEUTRAL\n    -- default idle state
EMOTION:HAPPY\n
EMOTION:CURIOUS\n
EMOTION:ANGRY\n      -- swaps to flame eyes for 9s then auto-reverts
EMOTION:SLEEPY\n
EMOTION:SURPRISED\n
EMOTION:SAD\n
EYES:SLEEP\n         -- blank both displays, halt rendering
EYES:WAKE\n          -- restore nordicBlue, resume rendering
```

**Teensy -> Pi4:**
```
FACE:1\n    -- face locked/detected
FACE:0\n    -- face lost
```

---

## EYE DEFINITIONS (config.h)

- Index 0: `nordicBlue` -- default, all emotions except ANGRY
- Index 1: flame -- ANGRY only, auto-reverts after 9000ms

**Eye config files:** JSON in `resources/` directory (edit for eyelid droop, pupil size, etc.)

---

## KEY CONSTANTS (main.cpp)

```cpp
TRACKING_WINDOW_MS   = 15000   // face tracking active after non-NEUTRAL emotion
FACE_LOST_TIMEOUT_MS = 5000    // stop tracking after face gone this long
FACE_COOLDOWN_MS     = 30000   // cooldown before re-enabling tracking
ANGRY_EYE_DURATION_MS = 9000   // flame eye hold time
EYE_IDX_DEFAULT = 0            // nordicBlue
EYE_IDX_ANGRY   = 1            // flame
```

---

## PENDING FIRMWARE TASKS

| Priority | Task | Details |
|---|---|---|
| 1 | Eyelid droop fix | Reduce upper eyelid droop in nordicBlue config.eye JSON -- no recompile needed |
| 2 | fillBlack verify | Confirm async fix is in latest build (should be -- check GC9A01A_Display.h) |
| 3 | Pupil size tweak | Megan feedback: pupils too large, unsettling. Shrink in nordicBlue eye config |

---

## GIT WORKFLOW

**Before making changes -- always commit current state first:**
```powershell
cd "C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face"
git add -A
git commit -m "working build before [describe what you're about to change]"
git push origin HEAD
```

**Branch:** `iris-ai-integration`
**Remote:** `origin` → `https://github.com/Maestro8484/IRIS-Robot-Face.git` (private)

---

## NOTES FOR CLAUDE CODE

- Do NOT modify `TeensyEyes.ino` -- it's the upstream eye engine, changes will conflict
- Eye appearance changes go in `resources/*.eye` JSON files or `config.h` eye definitions
- Emotion/serial/tracking logic lives in `main.cpp`
- Display driver changes go in `displays/GC9A01A_Display.h`
- After any change: PlatformIO Upload, then test via serial monitor at 115200
- The `.claude/` directory is in .gitignore -- worktrees go there, don't fight it

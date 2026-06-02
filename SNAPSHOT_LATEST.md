# IRIS Snapshot

**Session:** S96 | **Date:** 2026-06-01 | **Branch:** `main` | **Last commit:** S96

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## WHAT'S NEXT (Priority Queue)

1. **Flash T41** — S95 firmware REPO-ONLY. `pio run -e eyes` then PlatformIO upload. Verify `[VER] firmware=S95` in journal. Verify eyes track faces after flash.
2. **Deploy Pi4 web files** — `pi4/iris_web.html` + `pi4/iris_web.js` (Striking Blue EYE:7→EYE:6, 3 locations). REPO-ONLY.
3. **RD-003** — Duplicate sleep log: `/home/pi/iris_sleep.log` vs `/home/pi/logs/iris_sleep.log`.

---

## Machine Status

| System | Status |
|---|---|
| Pi4 192.168.1.200 | Operational. assistant.service active. POST 20/23 PASS WARN:3 FAIL:0. |
| GandalfAI 192.168.1.3 | Operational. iris model qwen2.5vl:32b-q4_K_M (S77). Kokoro TTS port 8004. |
| Teensy 4.1 (eyes+mouth) | Bridge connected. Displays showing. S96 firmware REPO-ONLY — flash required to fix LED + tracking. |
| Teensy 4.0 (servo+gesture) | FLASHED S93+S94. All 8 gestures VERIFIED. GESTURE_MAP live. APA102 LED feedback active. udev serial corrected (T40=13625440). |
| TTS | Kokoro primary (Docker 8004), Piper fallback (Wyoming 10200). |

---

## Active Issues

- **HIGH: T41 tracking + LED** — S96 fix REPO-ONLY. Root cause: no delay after setMode caused enableLED write to be dropped → DebugMode=1 → sensor contention → intermittent face data → eyes wander. Fix: delay(200) after setMode, re-confirm enableLED on first read, 400kHz I2C, confidence threshold 60→40. Flash required.
- **LOW: iris_web.html + iris_web.js deploy pending** — EYE:6 fix (3 locations). REPO-ONLY.
- **LOW: RD-003** — Duplicate sleep log paths.

---

## Session Scope

S96: PersonSensor LED + tracking root-cause fix. 400kHz I2C, delay(200) after setMode, re-confirm enableLED on first read, confidence 60→40. FIRMWARE_VERSION S95→S96. Flash required.

---

## Do Not Touch

- `iris_config.json` — gesture map + emotion map live config
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

---

## Last Session Changes (S96)

- **`src/main.cpp` setup** — `Wire.setClock(400000)` after Wire.begin(). `delay(200)` after setMode before enableLED.
- **`src/main.cpp` loop** — One-shot re-call of `enableLED(false)` on first successful read (`personSensorLEDConfirmed` flag).
- **`src/main.cpp` loop** — `box_confidence` threshold lowered 60 → 40.
- **`src/config.h:7`** — `FIRMWARE_VERSION` S95 → S96.

**Status:** REPO-ONLY. Flash T41 to deploy.

---

## Previous Session Changes (S94 / S94b)

- S94: PAJ7620U2 gesture remap, APA102 LED feedback, udev serial fix (T41=12763490, T40=13625440). All gestures VERIFIED.
- S94b: udev serial correction documented, SD persisted.

# IRIS Snapshot

**Session:** S95 | **Date:** 2026-06-01 | **Branch:** `main` | **Last commit:** bcec2db (S94 snapshot)

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
| Teensy 4.1 (eyes+mouth) | Bridge reconnected (user direct USB flash + replug). Displays showing. Person sensor LED on, tracking not working — S95 fix REPO-ONLY. Flash required. |
| Teensy 4.0 (servo+gesture) | FLASHED S93+S94. All 8 gestures VERIFIED. GESTURE_MAP live. APA102 LED feedback active. udev serial corrected (T40=13625440). |
| TTS | Kokoro primary (Docker 8004), Piper fallback (Wyoming 10200). |

---

## Active Issues

- **HIGH: T41 tracking broken** — `is_facing` condition was too strict; eyes rarely tracked. S95 fix in repo — flash required. Also: `enableLED` ordering fixed (mode→LED instead of LED→mode).
- **LOW: iris_web.html + iris_web.js deploy pending** — EYE:6 fix (3 locations). REPO-ONLY.
- **LOW: RD-003** — Duplicate sleep log paths.

---

## Session Scope

S95: PersonSensor tracking fix — removed `is_facing` requirement, reordered `enableLED` after `setMode`, reverted param rename. FIRMWARE_VERSION S91→S95. Flash required.

---

## Do Not Touch

- `iris_config.json` — gesture map + emotion map live config
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

---

## Last Session Changes (S95)

- **`src/sensors/PersonSensor.h:141`** — Parameter name `disabled` → `enabled`. Semantic fix only.
- **`src/main.cpp:381-383`** — Reordered: `setMode(Continuous)` before `enableLED(false)`. LED setting now survives mode switch.
- **`src/main.cpp:408`** — Removed `is_facing &&` from tracking condition. Eyes track any face with `box_confidence > 60`.
- **`src/config.h:7`** — `FIRMWARE_VERSION` S91 → S95.

**Status:** REPO-ONLY. Flash T41 to deploy.

---

## Previous Session Changes (S94 / S94b)

- S94: PAJ7620U2 gesture remap, APA102 LED feedback, udev serial fix (T41=12763490, T40=13625440). All gestures VERIFIED.
- S94b: udev serial correction documented, SD persisted.

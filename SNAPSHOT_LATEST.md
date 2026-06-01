# IRIS Snapshot

**Session:** S94 | **Date:** 2026-06-01 | **Branch:** `main` | **Last commit:** 0b805ca

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## WHAT'S NEXT (Priority Queue)

1. **URGENT: Fix T41 displays** — `DROP EYES:WAKE -- port not open`. Bridge lost T41 serial after repeated service restarts. Steps: `ls -la /dev/ttyIRIS_EYES` → `sudo systemctl restart assistant` → watch for `[EYES] Teensy connected`. If still failing: power-cycle T41 USB cable on Pi4.
2. **Deploy Pi4 web files** — `pi4/iris_web.html` + `pi4/iris_web.js` (Striking Blue EYE:7→EYE:6, 3 locations). REPO-ONLY.
3. **RD-003** — Duplicate sleep log: `/home/pi/iris_sleep.log` vs `/home/pi/logs/iris_sleep.log`.

---

## Machine Status

| System | Status |
|---|---|
| Pi4 192.168.1.200 | Operational. assistant.service active. POST 20/23 PASS WARN:3 FAIL:0. |
| GandalfAI 192.168.1.3 | Operational. iris model qwen2.5vl:32b-q4_K_M (S77). Kokoro TTS port 8004. |
| Teensy 4.1 (eyes+mouth) | **DISPLAYS BLACK** — `DROP EYES:WAKE -- port not open`. Bridge lost port after S94 service restarts. udev serial corrected (T41=12763490). Power-cycle USB + restart assistant. |
| Teensy 4.0 (servo+gesture) | FLASHED S93+S94. All 8 gestures VERIFIED. GESTURE_MAP live. APA102 LED feedback active. udev serial corrected (T40=13625440). |
| TTS | Kokoro primary (Docker 8004), Piper fallback (Wyoming 10200). |

---

## Active Issues

- **HIGH: T41 port not open** — `[EYES] DROP EYES:WAKE -- port not open`. Restart assistant; power-cycle T41 USB if needed.
- **LOW: iris_web.html + iris_web.js deploy pending** — EYE:6 fix (3 locations). REPO-ONLY.
- **LOW: RD-003** — Duplicate sleep log paths.

---

## Session Scope

S94: PAJ7620U2 gesture orientation verify + full remap (RIGHT→WAKE, CW→MUTE, CCW→SKIP) + APA102 LED gesture feedback + udev serial number correction (T41/T40 swapped since S63).

---

## Do Not Touch

- `iris_config.json` — gesture map + emotion map live config
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

---

## Last Session Changes (S94 / S94b)

- **`servo_teensy40/teensy40_base_mount/paj7620.cpp`** — RIGHT gesture emits `"RIGHT"` (was `"STOP"`). FLASHED S94.
- **`pi4/hardware/led.py`** — `show_gesture(action)` added to APA102. Transient color flash per action (green=VOL+, red=VOL-, white=STOP, blue=LISTEN, cyan=WAKE, amber=SLEEP, magenta=MUTE, yellow=SKIP). md5=`91360ee95d0d23d7c6307e07397ddc00` RAM=SD.
- **`pi4/hardware/base_mount_bridge.py`** — `self._leds` stored; `show_gesture()` called on dispatch. md5=`999544f7a4bad17c5dc86bdb848b8de3` RAM=SD.
- **`/home/pi/iris_config.json`** — `GESTURE_MAP` added: RIGHT→WAKE, FORWARD→LISTEN, BACKWARD→SLEEP, CW→MUTE, CCW→SKIP. md5=`755336185f765814496eb3fe5511c7ab` RAM=SD.
- **`pi4/core/config.py`** — `GESTURE_SENSOR_REQUIRED = True`. md5=`2a8fd5d2019a2666901d67a3ec7babff` RAM=SD.
- **`pi4/scripts/99-iris-teensy.rules`** — Serial numbers corrected: T41=12763490→ttyIRIS_EYES, T40=13625440→ttyIRIS_SERVO. md5=`83ca06eac9ee3afcf89753b8aa33405a` RAM=SD.
- **`IRIS_ARCH.md` + `docs/sysmap.json`** — USB serial table corrected throughout.

**Gesture verification (live journal):** RIGHT→WAKE ✓, LEFT→STOP ✓, UP→VOL+ ✓, DOWN→VOL- ✓, FORWARD→LISTEN ✓, BACKWARD→SLEEP ✓, CW→MUTE ✓, CCW→SKIP ✓.

---

## Previous Session Changes (S92/S93)

- S93: `GESTURE_MOUNT_DEGREES` 0→180 (JST connector left). T40 reflashed.
- S92: LAN flash scripts (`Flash T41 Eyes.bat`, `Flash T40 Servo.bat`). Both Teensys reflashed.

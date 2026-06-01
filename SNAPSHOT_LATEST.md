# IRIS Snapshot

**Session:** S94 | **Date:** 2026-06-01 | **Branch:** `main` | **Last commit:** pending

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## WHAT'S NEXT (Priority Queue)

1. **URGENT: Fix T41 display — `DROP EYES:WAKE -- port not open`** — Bridge lost T41 serial connection. Steps: (a) `ls -la /dev/ttyIRIS_EYES` confirms symlink exists; (b) `sudo systemctl restart assistant`; (c) check journal for `[EYES] Teensy connected on /dev/ttyIRIS_EYES`; (d) if still failing, power-cycle T41 USB.
2. **Deploy Pi4 web files** — `pi4/iris_web.html` + `pi4/iris_web.js` (EYE:6 fix, 3 locations). REPO-ONLY.
3. **RD-003** — Duplicate sleep log: `/home/pi/iris_sleep.log` vs `/home/pi/logs/iris_sleep.log`.

---

## Machine Status

| System | Status |
|---|---|
| Pi4 192.168.1.200 | Operational. S87+S87c+S87d deployed (emotion_map fix, IDLE buttons, firmware version POST check). iris_web.html md5=c5aad687, iris_post.py md5=18748f34. |
| GandalfAI 192.168.1.3 | Operational. iris model: ANGRY insult + 20-joke repertoire (S84). |
| Teensy 4.1 (eyes+mouth) | FLASHED S92. **DISPLAYS BLACK** — T41 port not open (`DROP EYES:WAKE -- port not open`). udev serial swap corrected S94 (T41=12763490). Serial port may have disconnected after multiple service restarts. Restart assistant + check `/dev/ttyIRIS_EYES` symlink. |
| Teensy 4.0 (servo+gesture) | FLASHED S92+S93+S94. All 8 gestures verified live. GESTURE_MAP: RIGHT→WAKE, CW→MUTE, CCW→SKIP. GESTURE_SENSOR_REQUIRED=True. APA102 LED gesture feedback active. POST 20/23 PASS AUTHORIZED. |
| TTS | Kokoro primary (Docker 8004), Piper fallback (Wyoming 10200). |

---

## Active Issues

- **LOW: iris_web.html + iris_web.js Pi4 deploy pending** — Striking Blue EYE:7→EYE:6 (3 locations). REPO-ONLY.
- **LOW: RD-003** — Duplicate sleep log paths.

---

## Last Session Changes (S87–S87d / S92)

- `src/mouth_tft.cpp` — `_draw_silly()` open-mouth redesign: upper lip arc (cy=-10 r=170), dark interior, tongue body+tip, lower lip arc (cy=115 r=55) drawn AFTER tongue. `_draw_silly_retracted()` for TONGUE_WAG. Anim 6=TONGUE_WAG (2s auto-trigger, 6×300ms), anim 7=BOING. `mouthTFTShow(9)` calls `mouthIdleStart()`. FLASHED.
- `src/config.h` — `FIRMWARE_VERSION[] = "S87b"` added. FLASHED.
- `src/main.cpp` — Boot prints `[VER] IRIS-EYES firmware=S87b built=<date>`. `VERSION` serial command handler added. FLASHED.
- `pi4/iris_web.html` — IDLE:START / IDLE:STOP buttons added to TFT Mouth card. DEPLOYED md5=c5aad687 RAM=SD.
- `pi4/iris_web.py` — `api_emotion_map` try/except hardening + `[EMAP]` debug log. DEPLOYED md5=6ae14e67 RAM=SD.
- `pi4/iris_post.py` — `l2_firmware_version()` added: greps journal for `[VER] IRIS-EYES`, reports PASS with version string or WARN if unversioned. DEPLOYED md5=18748f34 RAM=SD.
- `CLAUDE.md` — Hard rule added: update `FIRMWARE_VERSION` in `src/config.h` before every flash; verify `journalctl | grep VER` after.

## S91/S92 post-flash fixes (same session)

- `pi4/iris_web.html` — Striking Blue eye grid button: `EYE:7` → `EYE:6`. Default-eye selector option: `value="7"` → `value="6"`. REPO-ONLY (deploy to Pi4).
- `pi4/iris_web.js` — `_EYE_OPT` array: `[7,'7 - Striking Blue']` → `[6,'6 - Striking Blue']`. REPO-ONLY (deploy to Pi4).
- `src/config.h` — `FIRMWARE_VERSION` updated `"S87b"` → `"S91"` (takes effect at next flash). REPO-ONLY.

## Previous Session Changes (S91)

- `src/main.cpp` — Person Sensor timing fix: `while (millis() < 1500)` before I2C probe, 5-attempt retry loop. Root cause: Pi4 holds port open → Serial wait skipped → sensor not ready. FLASHED.
- `pi4/core/config.py` — `DEFAULT_EYE_IDX` range `(0,7)` → `(0,6)`. REPO-ONLY (pending deploy).

---

## Do Not Touch (protected files)

- `iris_config.json` (Pi4 live config — edit only via web UI or /api endpoints)
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`
- `pi4/hardware/alsa-init.sh`

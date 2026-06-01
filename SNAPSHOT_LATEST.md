# IRIS Snapshot

**Session:** S92 | **Date:** 2026-06-01 | **Branch:** `main` | **Last commit:** 8761174

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## WHAT'S NEXT (Priority Queue)

1. **Reconnect Teensy 4.1 USB to Pi4** — post-flash cable is still on SuperMaster. After reconnect: `journalctl -u assistant | grep VER` should show `[VER] IRIS-EYES firmware=S87b built=Jun  1 2026`. Also verify SILLY face (MOUTH:9), TONGUE_WAG (Start Idle → wait 2s), Person Sensor detected in log.
2. **Fix WebUI EYE:7 → EYE:6 for Striking Blue** — S89 firmware moved strikingBlue to index 6, but iris_web.html still sends `EYE:7`. Update button + default-eye selector. Deploy to Pi4.
3. **Update FIRMWARE_VERSION tag** — current value `"S87b"` in `src/config.h` but firmware includes S89 (bigBlue removal) + S91 (Person Sensor fix). Update to `"S91"` before next flash.
4. **Flash Teensy 4.0 (env:teensy40)** — GY-PAJ7620 orientation (GESTURE_MOUNT_DEGREES=0). Verify `PAJ7620U2 0x73 ACK=YES` + gestures fire.
5. **Set GESTURE_SENSOR_REQUIRED=True** — after T40 flash verified.
6. **RD-003** — Duplicate sleep log: `/home/pi/iris_sleep.log` vs `/home/pi/logs/iris_sleep.log`.

---

## Machine Status

| System | Status |
|---|---|
| Pi4 192.168.1.200 | Operational. S87+S87c+S87d deployed (emotion_map fix, IDLE buttons, firmware version POST check). iris_web.html md5=c5aad687, iris_post.py md5=18748f34. |
| GandalfAI 192.168.1.3 | Operational. iris model: ANGRY insult + 20-joke repertoire (S84). |
| Teensy 4.1 (eyes+mouth) | FLASHED this session — S87+S89+S91 combined build (SILLY mouth, TONGUE_WAG, versioning, bigBlue removed, Person Sensor fix). USB disconnected from Pi4 (reconnect needed). |
| Teensy 4.0 (servo+gesture) | S69 firmware LIVE. GY-PAJ7620 orientation fix REPO-ONLY (S83). |
| TTS | Kokoro primary (Docker 8004), Piper fallback (Wyoming 10200). |

---

## Active Issues

- **HIGH: Teensy 4.1 USB not connected to Pi4** — cable on SuperMaster post-flash. Reconnect + verify `[VER]` in journal before IRIS is operational.
- **MED: iris_web.html + iris_web.js EYE:7 fix needs Pi4 deploy** — Striking Blue index corrected to 6 in all three places (eye grid button, default-eye-sel option, `_EYE_OPT` array). REPO-ONLY. Deploy iris_web.html + iris_web.js to Pi4.
- **LOW: Gesture sensor** — T40 not flashed. Gestures won't fire until T40 flashed.
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

# IRIS Snapshot

**Session:** S87 | **Date:** 2026-05-31 | **Branch:** `main` | **Last commit:** ebf000b

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## WHAT'S NEXT (Priority Queue)

1. **Flash Teensy 4.1 (env:eyes)** — S87 firmware ready. `pio run -e eyes` builds clean. Upload via PlatformIO, then physically verify: `MOUTH:9` shows open mouth + flat tongue, tongue wags 2s after SILLY shown.
2. **Deploy iris_web.py to Pi4** — S87 emotion_map int-cast fix + `[EMAP]` debug logging. After deploy: SSH verify `cat /home/pi/iris_config.json | python3 -m json.tool` shows EMOTION_MOUTH_MAP + EMOTION_EYE_MAP keys after Save Mapping.
3. **Flash Teensy 4.0 (env:teensy40)** — GY-PAJ7620 orientation (GESTURE_MOUNT_DEGREES=0). Verify `PAJ7620U2 0x73 ACK=YES` + `init=OK` + gestures fire.
4. **Set GESTURE_SENSOR_REQUIRED=True** — After T40 flash verified, deploy to Pi4, confirm POST 22/22.
5. **RD-003** — Duplicate sleep log: `/home/pi/iris_sleep.log` vs `/home/pi/logs/iris_sleep.log`.

---

## Machine Status

| System | Status |
|---|---|
| Pi4 192.168.1.200 | Operational. S87 iris_web.py fix REPO-ONLY (not yet deployed). |
| GandalfAI 192.168.1.3 | Operational. iris model: ANGRY insult + 20-joke repertoire (S84). |
| Teensy 4.1 (eyes+mouth) | S65 firmware LIVE. S87 SILLY redesign + animation REPO-ONLY — needs flash. |
| Teensy 4.0 (servo+gesture) | S69 firmware LIVE. GY-PAJ7620 orientation fix REPO-ONLY (S83). |
| TTS | Kokoro primary (Docker 8004), Piper fallback (Wyoming 10200). |

---

## Active Issues

- **MED: SILLY mouth not yet flashed** — S87 redesigned `_draw_silly()` + TONGUE_WAG are REPO-ONLY. Flash env:eyes and physically verify.
- **MED: Emotion mapping save fix not deployed** — `api_emotion_map` try/except fix + `[EMAP]` debug logging in iris_web.py is REPO-ONLY.
- **LOW: Teensy 4.0 flash pending** — GY-PAJ7620 GESTURE_MOUNT_DEGREES=0 (S83). Flash env:teensy40.
- **LOW: RD-003** — Duplicate sleep log paths.

---

## Last Session Changes (S87)

- `src/mouth_tft.cpp:157` — Replaced `_draw_silly()`: old ellipse tongue (invisible) → open-mouth design (upper lip arc cy=-10 r=170, dark interior fillRect 50,100,220,75, lower lip arc cy=220 r=145, tongue body fillRect 105,148,110,68, tip fillCircle 160,216,42, groove).
- `src/mouth_tft.cpp:157` — Added `_draw_silly_retracted()`: identical to `_draw_silly()` but tongue body raised 15px (y=163 h=53) for TONGUE_WAG alternation.
- `src/mouth_tft.cpp:37` — Added `_sillyShownMs` static; `mouthTFTShow(9)` sets it to `millis()`.
- `src/mouth_tft.cpp` — Idle engine: anim 6 = TONGUE_WAG (2s auto-trigger after idx 9; 6×300ms half-cycles, 3 full wags); anim 7 = BOING (surprised→neutral 600ms). `_idleRestore`/`mouthIdleStop` updated for anims 6+7. Weighted pick expanded random(10)→random(11) with BOING as rare slot.
- `pi4/iris_web.py:842` — `api_emotion_map` POST: replaced silent-fail int-comprehension with explicit try/except loop + `[EMAP]` print debug. REPO-ONLY.

## Previous Session Changes (S85+S86 condensed)

- Added SILLY mouth idx 9 + emotion display mapping WebUI. DEPLOYED S85.
- S86 hotfix: iris_config.json 0-byte restored, iris-web.service restarted, workbench.js Anthropic key scrubbed.

---

## Do Not Touch (protected files)

- `iris_config.json` (Pi4 live config — edit only via web UI or /api endpoints)
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`
- `pi4/hardware/alsa-init.sh`

# IRIS Snapshot

**Session:** S90 | **Date:** 2026-05-31 | **Branch:** `main` | **Last commit:** 0fd774f

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## WHAT'S NEXT (Priority Queue)

1. **Flash Teensy 4.1 (env:eyes)** — S87+S89 firmware ready (bigBlue removed, SILLY redesign). `pio run -e eyes` builds clean. Upload via PlatformIO. After flash: verify `MOUTH:9` shows open mouth + tongue, EYE:6 now shows Striking Blue (not bigBlue), web UI eye buttons updated.
2. **Is Person Sensor on Teensy 4.1?** — T41 serial shows `[DBG] No Person Sensor found`. If PS is ONLY on T40 now, set `USE_PERSON_SENSOR{false}` in `src/config.h` to stop failed init. Clarify with user.
3. **Flash Teensy 4.0 (env:teensy40)** — GY-PAJ7620 orientation (GESTURE_MOUNT_DEGREES=0). Verify `PAJ7620U2 0x73 ACK=YES` + `init=OK` + gestures fire.
4. **Set GESTURE_SENSOR_REQUIRED=True** — After T40 flash verified, deploy to Pi4, confirm POST 22/22.
5. **RD-003** — Duplicate sleep log: `/home/pi/iris_sleep.log` vs `/home/pi/logs/iris_sleep.log`.

---

## Machine Status

| System | Status |
|---|---|
| Pi4 192.168.1.200 | Operational. S90 webserver modularized: iris_web split to .html/.css/.js + log_parser.py. DEPLOYED+VERIFIED. |
| GandalfAI 192.168.1.3 | Operational. iris model: ANGRY insult + 20-joke repertoire (S84). |
| Teensy 4.1 (eyes+mouth) | S65 firmware LIVE. S87+S89 (SILLY + bigBlue removal) REPO-ONLY — needs flash. |
| Teensy 4.0 (servo+gesture) | S69 firmware LIVE. GY-PAJ7620 orientation fix REPO-ONLY (S83). Gesture sensor not working until T40 flashed. |
| TTS | Kokoro primary (Docker 8004), Piper fallback (Wyoming 10200). LOUD_STOP_THRESHOLD raised to 25000 — TTS cutoff fixed. |

---

## Active Issues

- **MED: Teensy 4.1 flash needed** — S87+S89 firmware (SILLY mouth, bigBlue removed, strikingBlue→index 6) REPO-ONLY. Flash env:eyes.
- **MED: Person Sensor on T41?** — T41 serial shows `[DBG] No Person Sensor found`. If PS is T40-only, set `USE_PERSON_SENSOR{false}` in config.h.
- **LOW: Gesture sensor** — T40 not flashed (GESTURE_MOUNT_DEGREES=0 REPO-ONLY). Gestures won't fire until T40 flashed.
- **LOW: RD-003** — Duplicate sleep log paths.

---

## Last Session Changes (S90)

- `pi4/iris_web.py` — Modularized: log parsing block extracted to `log_parser.py`, dead `TEENSY_PORT`/`TEENSY_BAUD` constants removed, `CSS_FILE`/`JS_FILE` paths + `/iris_web.css` and `/iris_web.js` routes added. DEPLOYED+VERIFIED. md5 RAM=SD=`2e66e9920983e2b5328e304fdc56b738`.
- `pi4/iris_web.html` — Inline CSS/JS removed; replaced with `<link href="/iris_web.css">` and `<script src="/iris_web.js">`. DEPLOYED+VERIFIED. md5 RAM=SD=`bcfde07a6d1695fee74e880327fff628`.
- `pi4/iris_web.css` — New file: extracted CSS from iris_web.html. DEPLOYED+VERIFIED. md5 RAM=SD=`be0509cb3e47464f12ee8afa0f25d2d4`.
- `pi4/iris_web.js` — New file: extracted JavaScript from iris_web.html (both script blocks combined). DEPLOYED+VERIFIED. md5 RAM=SD=`3602026caaf32e0989b4d540d197a120`.
- `pi4/log_parser.py` — New file: journal + SD log parsing extracted from iris_web.py. DEPLOYED+VERIFIED. md5 RAM=SD=`252007ea3b48e1fde1c9edecb460d2a6`.

## Previous Session Changes (S89)

- `pi4/core/config.py` — `LOUD_STOP_THRESHOLD=25000` (was 9000, below speaker bleed 9k-18k RMS). `DEFAULT_EYE_IDX=0` added. Both in `_OVERRIDABLE`. DEPLOYED+VERIFIED. md5=`d9f05e676ee9002c624a263d1d26d0cb`.
- `pi4/hardware/audio_io.py` — `LOUD_STOP_THRESHOLD` imported from config. DEPLOYED+VERIFIED. md5=`55c9951011f012e8145cfbf26475a1f7`.
- `pi4/iris_post.py` — `l2_display()` restores `EYE:0` + `MOUTH_INTENSITY:3` after display cycle. Fixes bigBlue eye every boot. DEPLOYED+VERIFIED. md5=`5d17ce3d26fe8535507d93bc04bab107`.
- `pi4/assistant.py` — Sends `EYE:{DEFAULT_EYE_IDX}` after POST. DEPLOYED+VERIFIED. md5=`14e52ac97726248da9a73730951656d0`.
- `pi4/iris_web.py` — Event log capped 500→200. DEPLOYED+VERIFIED. md5=`1e4d11b86cfbc12f41741f6f04482f46`.
- `pi4/iris_web.html` — Event log newest-first. bigBlue button removed. Default eye selector added. DEPLOYED+VERIFIED. md5=`4ce6513b5bac57ed469e3e1413cc3b44`.
- `src/config.h` — bigBlue removed (size 8→7), strikingBlue→index 6. REPO-ONLY.
- `src/main.cpp` — `EYE_IDX_BIGBLUE` removed, `EYE_IDX_STRIKINGBLUE=6`, `EYE_IDX_COUNT=7`. REPO-ONLY.

## Previous Session Changes (S88)

- `pi4/core/config.py:54` — `GESTURE_SENSOR_REQUIRED` reverted `True` → `False`. DEPLOYED+VERIFIED. md5=`7bb5ad9f725eefd33ac95d6be0af3580`.
- `pi4/iris_post.py` — POST verdict hardened. DEPLOYED+VERIFIED. md5 RAM=SD=`4dc66141988ec2c8090cfaf655484ebf`.
- `pi4/iris_web.py` — S87 emotion_map int-cast fix. DEPLOYED+VERIFIED. md5 RAM=SD=`49e798af34d0efd0469938c68133f67a`.

## Previous Session Changes (S87)

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

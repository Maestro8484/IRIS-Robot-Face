# IRIS Snapshot

**Session:** S86 | **Date:** 2026-05-31 | **Branch:** `main` | **Last commit:** 310614f

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## WHAT'S NEXT (Priority Queue)

1. **S87 MAIN TASK — TFT mouth animation overhaul** — See full brief below.
2. **Flash Teensy 4.1 (env:eyes)** — After mouth redesign is done. Build clean, upload via PlatformIO. Verify `MOUTH:9` shows correct silly face.
3. **Flash Teensy 4.0 (env:teensy40)** — GY-PAJ7620 orientation (GESTURE_MOUNT_DEGREES=0). Verify `PAJ7620U2 0x73 ACK=YES` + `init=OK` + gestures fire.
4. **Set GESTURE_SENSOR_REQUIRED=True** — After T40 flash verified, deploy to Pi4, confirm POST 22/22.
5. **RD-003** — Duplicate sleep log: `/home/pi/iris_sleep.log` vs `/home/pi/logs/iris_sleep.log`.

---

## S87 TASK BRIEF — Mouth Animation + SILLY Redesign

### Problem 1: SILLY mouth (index 9) is broken

`_draw_silly()` in `src/mouth_tft.cpp` draws a hot-pink ellipse (center y=183, ry=36,
so y=147–219) but the smile arc bottom is also at ~y=150. The tongue overlaps the smile
arc interior and does not visibly protrude. The expression looks wrong.

**Fix needed in `src/mouth_tft.cpp` `_draw_silly()`:**
- Draw a clearly OPEN mouth: upper lip arc + filled dark interior + lower lip line
- Tongue must protrude visibly BELOW the lower lip (below y=180+)
- Wide flat tongue shape (not a circle) — cartoon-style, like a dog panting
- Reference: https://www.vecteezy.com/free-vector/cartoon-mouth-emotion (search "tongue")
- The TFT is 320×240 landscape, ILI9341 rotation 3

**Good cartoon tongue-out geometry (rough guide):**
```
Upper lip arc:  _arc(160, -10, 170, 0.52f, 2.62f, MTFT_YELLOW, 12)
Mouth interior: _tft->fillRect(50, 100, 220, 75, 0x3000)  // dark red gap
Lower lip:      _arc(160, 220, 145, 3.62f, 5.66f, MTFT_YELLOW, 12)
Tongue body:    fillRect(105, 148, 110, 68, MTFT_TONGUE)  // wide flat slab
Tongue tip:     fillCircle(160, 216, 42, MTFT_TONGUE)     // rounded tip
Tongue groove:  fillRect(157, 152, 6, 62, 0xC000)         // center line
```
MTFT_TONGUE = 0xFB36 (hot pink) — already defined.

### Problem 2: No animation support

All current mouth expressions are static single-frame draws. The user wants animated
expressions — tongue wag, blinking open/close, etc. — similar to GIF/Lottie style.

The `mouthIdleTick()` system in `mouth_tft.cpp` already has a frame timer and phase
state. The idle animations (BREATHE, TWITCH, YAWN etc.) use this loop.

**Animation approach: extend the idle anim engine with new anim IDs:**
- Anim 6 = TONGUE_WAG: alternate between tongue extended (idx 9) and slight retract
  (redraw tongue 15px shorter), period ~600ms, runs for 3 cycles then restores
- Anim 7 = BOING: draw surprised oval (idx 5), shrink it 3 frames to neutral, BL pulse
- Each new anim needs a phase/timer entry in `mouthIdleTick()`

The mouthTFTShow() call for idx 9 should also automatically trigger TONGUE_WAG when
called from idle context (i.e. after 2s of no commands, start wagging).

**Reference for animated mouth styles:**
- https://lottiefiles.com/free-animations/mouth — browse for tongue/silly/happy loops
- The TFT renders at ~4-8 fps via bit-bang SPI so animation must be coarse (200ms+ frames)

### Problem 3: iris_config.json emotion mapping "appears blank" in WinSCP

**This is a filesystem layer confusion, not a save bug.** WinSCP connects to Pi4 as user
`pi` and shows `/home/pi/iris_config.json` which IS the live RAM file. The emotion_map
values SHOULD appear there after Save Mapping + Persist to SD.

However — verify the /api/emotion_map POST actually reaches write_cfg:
- Check `pi4/iris_web.py` route `api_emotion_map` — the `int(v)` cast in the list
  comprehension will raise if `v` is already an int (e.g. `int(0)` is fine, but check
  for edge cases). Add `try/except` around the cast if needed.
- After saving, SSH into Pi4: `cat /home/pi/iris_config.json | python3 -m json.tool`
  to verify EMOTION_MOUTH_MAP and EMOTION_EYE_MAP keys are present.
- If they're missing: add `print("[EMAP] write_cfg patch:", ...)` logging to debug.

---

## Machine Status

| System | Status |
|---|---|
| Pi4 192.168.1.200 | Operational. S85+S86 DEPLOYED+VERIFIED. iris-web.service running with /api/emotion_map live. iris_config.json restored (was 0-byte S86). md5 RAM=SD=eda5cd406e441009677b0c460cdae8d9. |
| GandalfAI 192.168.1.3 | Operational. iris model: ANGRY insult + 20-joke repertoire (S84). qwen2.5vl:32b-q4_K_M. |
| Teensy 4.1 (eyes+mouth) | S65 firmware LIVE. SILLY mouth (index 9) REPO-ONLY — not yet flashed (redesign needed first). nordicBlue polarDist fix + strikingBlue also REPO-ONLY (S79). |
| Teensy 4.0 (servo+gesture) | S69 firmware LIVE. GY-PAJ7620 orientation fix REPO-ONLY (S83). |
| TTS | Kokoro primary (Docker 8004), Piper fallback (Wyoming 10200). |

---

## Active Issues

- **MED: SILLY mouth (index 9) renders incorrectly** — tongue overlaps smile arc interior, not visible as protruding. Fix `_draw_silly()` before flashing.
- **MED: Emotion mapping save unverified** — user reports iris_config.json "appears blank". Needs SSH verification + possible /api/emotion_map debug logging.
- **LOW: Teensy 4.1 flash pending** — S79 nordicBlue fix + strikingBlue + S85 SILLY mouth all REPO-ONLY. Flash env:eyes after SILLY redesign complete.
- **LOW: Teensy 4.0 flash pending** — GY-PAJ7620 GESTURE_MOUNT_DEGREES=0 (S83). Flash env:teensy40.
- **LOW: RD-003** — Duplicate sleep log paths.

---

## Last Session Changes (S85+S86)

- `src/mouth_tft.cpp` — Added SILLY mouth index 9 (`_draw_silly()`), MTFT_TONGUE=0xFB36, bounds check 8→9. REPO-ONLY.
- `src/mouth_tft.h` — Comment updated (9=SILLY). REPO-ONLY.
- `pi4/core/config.py` — Added `EMOTION_EYE_MAP` dict; `EMOTION_MOUTH_MAP`/`EMOTION_EYE_MAP` applied from iris_config.json. DEPLOYED.
- `pi4/assistant.py` — `emit_emotion()` now sends `EYE:n` before `EMOTION:x` when EMOTION_EYE_MAP has non-(-1) entry. DEPLOYED.
- `pi4/iris_web.py` — `/api/emotion_map` GET+POST endpoint. DEPLOYED.
- `pi4/iris_web.html` — Emotion Display Mapping card (9-emotion table, eye+mouth dropdowns, Test/Save buttons), SILLY button in TFT Mouth grid, `loadEmotionMap()` on init. DEPLOYED.
- `resources/mouth_expressions/catalog.md` — GIF/Lottie reference catalog. LOCAL.
- S86 hotfix: iris_config.json 0-byte restored, iris-web.service restarted, workbench.js Anthropic key scrubbed + gitignored.

## Do Not Touch (protected files)

- `iris_config.json` (Pi4 live config — edit only via web UI or /api endpoints)
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`
- `pi4/hardware/alsa-init.sh`

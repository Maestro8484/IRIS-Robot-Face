# Eye Jitter During TTS — Handoff (S100b, 2026-06-02)

## Status: OPEN — partial fix deployed, wrong assumption

## What was reported

Eyes are jerky/wonky when IRIS is speaking (TTS playback). Happens every response.

---

## What was tried (S100b) and why it didn't work

**Theory**: Person Sensor polling at 15-30Hz feeds `setTargetPosition(x, y)` with noisy
face-detection coordinates → eye jitter at sensor rate.

**Fix applied**:
- `src/main.cpp` — added `eyesSpeaking` flag. `EYES:SPEAKING` serial command sets flag +
  calls `eyes->setAutoMove(true)`, blocking Person Sensor position updates during speech.
  `EYES:SPEAKING:STOP` clears flag.
- `pi4/hardware/audio_io.py` — `play_pcm_speaking()` sends `EYES:SPEAKING` before audio
  starts and `EYES:SPEAKING:STOP` after.

**Confirmed working** (from journal):
```
[EYES] << [VER] IRIS-EYES firmware=S100 built=Jun  2 2026
[EYES] >> EYES:SPEAKING
[EYES] << [DBG] EYES:SPEAKING -- tracking suspended, autoMove on
[EYES] >> EYES:SPEAKING:STOP
[EYES] << [DBG] EYES:SPEAKING:STOP -- tracking resumed
```

**Why jitter persists**: `eyes->setAutoMove(true)` enables the EyeController's autonomous
wander algorithm. That algorithm itself produces visually erratic movement — we replaced
sensor-noise jitter with auto-wander jitter. Wrong tradeoff.

---

## Correct approach for new session

**Goal**: eyes visually stable/calm during TTS, not tracking, not wandering.

### Option A — Lock to last-known position (minimal change, try first)

When `EYES:SPEAKING` fires, do NOT call `eyes->setAutoMove(true)`. Just block the
Person Sensor → `setTargetPosition` path. Eyes freeze at their current target position
(wherever they were looking when speech started). Looks natural — IRIS looks at the
person while speaking. No sudden wander.

Change in `src/main.cpp` processSerial EYES:SPEAKING handler:
```cpp
} else if (strcmp(serialBuf, "EYES:SPEAKING") == 0) {
  lastCommandMs = millis();
  eyesSpeaking  = true;
  // Do NOT call setAutoMove(true) — let eyes hold last position
  Serial.println("[DBG] EYES:SPEAKING -- tracking frozen at last position");
```

No other change needed. `EYES:SPEAKING:STOP` clears the flag, Person Sensor tracking
resumes naturally on next read.

### Option B — Lock eyes to straight-ahead (if Option A still jitters)

When `EYES:SPEAKING` fires, call `eyes->setAutoMove(false)` and
`eyes->setTargetPosition(0.0f, 0.0f)` once to point eyes straight forward. Stable, clean,
makes sense visually (looking "at" the audience while speaking).

```cpp
} else if (strcmp(serialBuf, "EYES:SPEAKING") == 0) {
  lastCommandMs = millis();
  eyesSpeaking  = true;
  eyes->setAutoMove(false);
  eyes->setTargetPosition(0.0f, 0.0f);
  Serial.println("[DBG] EYES:SPEAKING -- eyes locked center");
```

### Option C — Read EyeController.h to understand autoMove (before trying A or B)

`src/eyes/EyeController.h` is in the "do not MODIFY" list but is READ-ONLY accessible.
Read it before implementing to understand what autoMove actually does internally and
whether there's a lower-cost way to freeze movement.

---

## If Option A/B don't help: mouth SWSPI blocking theory

**Secondary suspect**: `mouthTFTShow()` is called via blocking SWSPI after `renderFrame()`
in each loop. If SWSPI takes 20-40ms per call and fires every MOUTH_RENDER_MIN_MS=75ms,
it delays the start of the NEXT renderFrame() by 20-40ms. This shifts eye frame timing
irregularly (loop = 155ms eye + 30ms mouth = 185ms when mouth fires, 155ms when not).
The irregular frame cadence can look like jitter even with stable position targets.

To test: temporarily raise `MOUTH_RENDER_MIN_MS` to 150ms in `src/main.cpp` line ~127
and see if jitter improves. If yes, mouth SWSPI is the culprit.

---

## Files to read before starting

| File | Why |
|---|---|
| `src/main.cpp` | Current EYES:SPEAKING implementation (lines ~111-125 flag decl, ~279-292 handlers, ~415-425 tracking block) |
| `src/eyes/EyeController.h` | Read-only: understand setAutoMove, setTargetPosition internals |
| `pi4/hardware/audio_io.py` | `play_pcm_speaking` — EYES:SPEAKING wrapper at line ~318 |
| `src/config.h` | FIRMWARE_VERSION = S100 (must bump before each flash) |

## Files that must NOT be modified

- `src/eyes/EyeController.h` (protected — read only)
- `src/TeensyEyes.ino` (protected)
- `iris_config.json` (protected)

---

## Current state

| Component | State |
|---|---|
| Firmware | S100 flashed (T41), EYES:SPEAKING handler present |
| `pi4/hardware/audio_io.py` | DEPLOYED+PERSISTED, md5=43c36c1d |
| `src/main.cpp` | EYES:SPEAKING sets autoMove=true (this is the bug) |
| FIRMWARE_VERSION | S100 in config.h — bump to S100c before next flash |

## Deploy path after firmware fix

1. Edit `src/config.h` → bump FIRMWARE_VERSION (e.g. "S100c")
2. `pio run -e eyes` — verify BUILD SUCCESS
3. User flashes via PlatformIO upload (env:eyes) OR `scripts\Flash T41 Eyes.bat`
4. Verify in journal: `journalctl -u assistant | grep -E "VER|SPEAKING"`

## Rollback

```bash
git checkout -- src/main.cpp src/config.h
# pio run -e eyes, user flashes
# audio_io.py still sends EYES:SPEAKING but firmware ignores it — safe
```

---

## Session close summary (S100b)

- EYES:SPEAKING firmware command: working
- Person Sensor suppression during TTS: working  
- Root cause misidentified: autoMove=true is itself the jitter source
- Fix: change EYES:SPEAKING to freeze position, not wander

# Eye Jitter / Stutter During TTS — Handoff (S100c, 2026-06-02)

## Status: OPEN — cause identified, fix not yet applied

---

## Symptom history

**Original report:** Eyes jerky/wonky while IRIS speaks.

**After S100b/S100c flash:** Eyes no longer jitter from sensor noise, but now show
"laggy eyelids opening/closing like stop-animation" during TTS. Same session, different
cause now dominating.

---

## Root cause (confirmed)

Two causes were fixed or confirmed in S100b/S100c:

### Cause 1 — Person Sensor tracking noise: FIXED ✓
Person Sensor called `setTargetPosition(x,y)` at 15-30Hz with noisy face detection
coordinates during TTS. Fixed by `eyesSpeaking` flag in firmware (S100). Person
Sensor position updates suppressed during `EYES:SPEAKING`. Confirmed working:
```
[EYES] << [DBG] EYES:SPEAKING -- tracking frozen at last position
[EYES] << [DBG] EYES:SPEAKING:STOP -- tracking resumed
```

### Cause 2 — Mouth SWSPI blocking eye render loop: ACTIVE (current symptom)
`mouthTFTShow()` uses **software SPI (bit-banged)**. Each call blocks the CPU for an
estimated 30-80ms. During TTS, `play_pcm_speaking` sends `MOUTH:n` commands at
**120ms intervals** (8Hz). The firmware renders those via `mouthTFTShow()` rate-limited
to every 75ms (`MOUTH_RENDER_MIN_MS`). The eye render loop runs at ~155ms per frame
(`SR_FRAME_MS`). When a mouth update fires, the loop looks like:

```
Normal loop:   renderFrame(~114ms) = 114ms total
Mouth update:  renderFrame(~114ms) + mouthTFTShow(~30-80ms) = 144-194ms total
```

This irregular cadence (sometimes 114ms, sometimes 194ms) disrupts the EyeController's
internal eyelid/pupil animation timing → stop-motion eyelid effect at ~8fps artifact rate.

Before Cause 1 was fixed, the sensor-noise jitter was the dominant visible artifact.
After fixing Cause 1, Cause 2 became fully visible.

---

## The fix (Pi4 only — NO firmware flash required)

### Option A: Reduce mouth animation rate in play_pcm_speaking (try first)

**File:** `pi4/hardware/audio_io.py` — function `play_pcm_speaking` (~line 318)

Change mouth animation interval from 120ms to 500ms:
```python
# Current (8Hz — too fast, causes render disruption):
while not stop_evt.wait(0.12):

# Fix (2Hz — much less disruptive):
while not stop_evt.wait(0.50):
```

This reduces `mouthTFTShow()` calls from ~8/sec to ~2/sec during TTS.
Eye render cadence disruption drops from every 2-3 frames to every 8-10 frames.
Mouth animation still visible but much smoother overall.

Deploy: standard Pi4 sftp + SD persist + `systemctl restart assistant`.
No firmware flash needed.

### Option B: No mouth animation during TTS (cleanest)

Send one mouth-open frame at start of speech, hold it, restore at end.
Remove the cycling thread entirely from `play_pcm_speaking`:

```python
def play_pcm_speaking(pcm_bytes, pa, teensy, emotion='NEUTRAL',
                      restore_mouth_idx=0, rate=48000):
    speak_idx = _EMOTION_SPEAK_FRAMES.get(emotion.upper(),
                                           _EMOTION_SPEAK_FRAMES['NEUTRAL'])[0]
    teensy.send_command("EYES:SPEAKING")
    teensy.send_command(f"MOUTH:{speak_idx}")   # set mouth open, hold it
    time.sleep(0.05)
    was_interrupted = play_pcm(pcm_bytes, pa, rate)
    teensy.send_command(f"MOUTH:{restore_mouth_idx}")
    teensy.send_command("EYES:SPEAKING:STOP")
    return was_interrupted
```

Zero mouth updates during playback = zero mouthTFTShow() disruption = smooth eyes.
Trade-off: mouth stays static instead of animating. Likely acceptable.

### Option C: Raise MOUTH_RENDER_MIN_MS in firmware (if Pi4 fix insufficient)

`src/main.cpp` line ~127:
```cpp
static constexpr uint32_t MOUTH_RENDER_MIN_MS = 75;   // current — too fast
static constexpr uint32_t MOUTH_RENDER_MIN_MS = 200;  // try this
```

Reduces actual TFT update rate from 13Hz max to 5Hz max even if Pi4 sends faster.
**Requires firmware flash.** Do Option A or B first.

---

## Recommended approach for new session

1. Try **Option A** first (one-line change, no flash, easiest to test).
2. If still visible: try **Option B** (slightly more code, cleanest fix).
3. If still visible: check `src/mouth_tft.cpp` to measure actual SWSPI blocking time.
4. If blocking time is severe (>60ms): raise `MOUTH_RENDER_MIN_MS` (Option C, flash needed).

---

## Current state going into new session

| Component | State |
|---|---|
| Firmware T41 | S100c flashed — EYES:SPEAKING working, autoMove NOT set (freeze at last pos) |
| `pi4/hardware/audio_io.py` | DEPLOYED. `play_pcm_speaking` sends EYES:SPEAKING + animates MOUTH at 120ms. md5=43c36c1d |
| Eye jitter (Person Sensor) | FIXED — eyesSpeaking flag blocks tracking during TTS |
| Eye stop-motion (mouth SWSPI) | ACTIVE — mouth animation at 8Hz disrupts eye render cadence |

## Files for new session

| File | Why |
|---|---|
| `pi4/hardware/audio_io.py` | **Edit this first** — `play_pcm_speaking` mouth animation rate |
| `src/main.cpp` | Context only — `MOUTH_RENDER_MIN_MS` at ~line 127 if needed |
| `src/mouth_tft.cpp` | Read to measure SWSPI blocking if needed |

## Protected files (read only, do NOT edit)
- `src/eyes/EyeController.h`
- `src/TeensyEyes.ino`
- `iris_config.json`

## Deploy path
```bash
# Pi4 only (Option A or B):
# 1. Edit pi4/hardware/audio_io.py locally
# 2. python -c "import paramiko; ..." SFTP to Pi4
# 3. sudo cp to /media/root-ro + md5 verify
# 4. sudo systemctl restart assistant
# 5. Test: say hey jarvis, ask a question, watch eyes during response
```

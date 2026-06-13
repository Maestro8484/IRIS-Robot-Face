# Handoff — RD-033: Teensy 4.1 Person Sensor face-tracking NOT sustained  ⚠️ TOP PRIORITY

> **Deferred out of the S131 session (which closed RD-031/032).** This is the #1 remaining item.
> **Recommended model: OPUS** — firmware + hardware reasoning + delicate observe-iterate tracking debug
> with the operator at the bench. Tracking is a regression-prone path; do not rush a blind reflash.

---

## Symptom (operator-confirmed S130 — authoritative)

The Person Sensor **IS detecting** and the eyes **DO acquire/lock onto a face** — but **tracking is not
sustained: the gaze drops/redirects after ~0.5 s.** The operator confirms this exact "brief lock then lose"
has **recurred multiple times after code changes**. This is a **tracking-SUSTAINMENT bug, not a detection
failure.**

Do NOT re-litigate detection from `FACE:` journal counts — they are unreliable here: `FACE:1`/`FACE:0` are
rate-limited (`FACE_COOLDOWN_MS`) and **have no Pi4 consumer** (the bridge now suppresses nothing relevant,
but nothing acts on them either). Diagnose from **observed eye behavior + added serial debug**, not log counts.

## Session-start protocol (per CLAUDE.md)
1. `git status` — branch `main`, tree clean. Last relevant commit: **S131 `dd57f50`**.
2. Read `CLAUDE.md`, first 50 lines of `SNAPSHOT_LATEST.md` (Active Issues has the RD-033 summary), this file.
3. **Live firmware may be S130 or S131** depending on whether the operator flashed S131 (RD-031). Confirm with
   `journalctl -u assistant | grep VER` → `[VER] IRIS-EYES firmware=S1??`. The `[SR]` log gate (S131) does
   not affect tracking; ignore it here.
4. **Before any reflash, add serial debug FIRST** (memory `feedback_dont_push_unverified_tracking` — multiple
   blind flashes were wasted in a prior tracking session). Build (`pio run -e eyes`), bump `FIRMWARE_VERSION`,
   operator flashes via `scripts\flash_t41.ps1`.
5. **Scope discipline** (memory `feedback_no_scope_creep_firmware`): touch only the tracking path. **`src/eyes/EyeController.h`
   is a PROTECTED file** (CLAUDE.md "Do Not Touch") — edit only with explicit operator OK in the session.

## The code (read these in full before changing anything)

All in `src/main.cpp` unless noted. Line numbers are as of S131 `dd57f50`.

### Tracking loop — `loop()` [src/main.cpp:417-442](../src/main.cpp#L417)
```cpp
if (!eyesSleeping && hasPersonSensor() && personSensor.read()) {     // only on NEW I2C data
    int maxSize = 0; person_sensor_face_t maxFace{};
    for (i in faces) {
        if (face.is_facing && face.box_confidence > 60) {            // <-- confidence/facing gate
            size = w*h; if (size > maxSize) { maxSize=size; maxFace=face; }
        }
    }
    reportFaceState(maxSize > 0);                                    // sends FACE:1/0 + mouthGreet()
    if (!eyesSpeaking) {
        if (maxSize > 0) {
            eyes->setAutoMove(false);
            eyes->setTargetPosition(targetX, targetY);               // track
        } else if (personSensor.timeSinceFaceDetectedMs() > FACE_LOST_TIMEOUT_MS  // 5000ms
                   && !eyes->autoMoveEnabled()) {
            eyes->setAutoMove(true);                                 // resume wander
        }
    }
}
```

### `reportFaceState()` [src/main.cpp:346-361](../src/main.cpp#L346) — **prime suspect**
On the rising edge (face newly present) it sends `FACE:1` **and calls `mouthGreet()` (line 354, RD-030 #3,
added S130)**. `mouthGreet()` lives in `src/mouth_tft.cpp` and does a **blocking SWSPI redraw** of the mouth
TFT. If that blocks the loop for ~100 ms+ (or runs a multi-frame animation that starves the eye engine), the
eyes stall right at acquisition → reads as a tracking drop. **The symptom appearing/recurring "after code
changes" lines up with the S130 greet addition.** First experiment: gate/defer `mouthGreet()` during active
tracking (e.g. skip it while a face is present, or only greet from a true idle/at-rest state) and see if
sustainment returns.

### `FACE_LOST_TIMEOUT_MS` [src/main.cpp:40](../src/main.cpp#L40) = 5000 ms
Re-enables autoMove (wander) only after 5 s of no face. A **0.5 s** redirect is too fast to be this path —
**unless** `timeSinceFaceDetectedMs()` is miscomputed, OR the eye engine has its own internal idle/wander
timer that overrides `setTargetPosition` independent of `autoMove`. Verify what actually moves the eyes at
0.5 s.

### `setTargetPosition()` / seeding — `src/eyes/EyeController.h` (PROTECTED)
Prior fix `ed8fa41` seeded `eyeOldX=eyeX` on motion restart (see memory `project_tracking_eyecontroller_fix`
+ issue log 2026-03-27). Confirm that fix is intact and that nothing re-seeds from a stale origin on each new
target. **Read-only unless the operator authorizes editing this file.**

### PersonSensor driver — `src/sensors/PersonSensor.{h,cpp}`
Check `read()` cadence, `timeSinceFaceDetectedMs()`, and the `is_facing`/`box_confidence > 60` gate
[main.cpp:426](../src/main.cpp#L426): a momentary confidence dip below 60 or `is_facing=false` for one frame
makes `maxSize=0` → `FACE:0` + `faceWasPresent=false`, and the next frame re-fires `FACE:1` + `mouthGreet()`.
Rapid confidence flicker → repeated greet calls → repeated blocking redraws → stutter that looks like "lose
the face." Consider hysteresis (lower the threshold / require N consecutive misses before declaring lost).

## Candidate mechanisms (rank to test)
1. **`mouthGreet()` blocking SWSPI redraw in the FACE:1 path** (S130 addition) — gate/defer it during tracking. **Test first.**
2. **Confidence/`is_facing` flicker** dropping `maxSize` to 0 for a frame → FACE:0/FACE:1 thrash + greet replay. Add hysteresis.
3. **Eye-engine internal idle/wander timer** overriding `setTargetPosition` faster than `FACE_LOST_TIMEOUT_MS` (look inside EyeController for any auto-recenter/idle logic, read-only).
4. **`setTargetPosition` seeding** regression (protected file; verify ed8fa41 intact).

## Diagnostic plan (serial debug BEFORE reflash)
Add a default-gated debug print in `loop()` (one line per person-sensor read, NOT per loop iteration — respect
memory `feedback_no_unbounded_logging`/RD-031; gate behind a compile flag like `DEBUG_FACE`, default off):
`numFaces, maxSize, box_confidence, is_facing, targetX/Y, eyes->autoMoveEnabled(), eyesSpeaking,
timeSinceFaceDetectedMs()` — plus `mouthGreet()` entry/exit `millis()` to measure its block time. Bump
`FIRMWARE_VERSION`, flash, sit in front of IRIS, and watch which value changes at the moment the gaze
redirects (~0.5 s). That pinpoints the mechanism before any fix. Keep `DEBUG_FACE` off in the shipping build.

## Deploy / flash workflow
- Firmware is **REPO-ONLY** at session close. Build: `pio run -e eyes`. Operator flashes via
  `scripts\flash_t41.ps1` (Teensy is enclosure-mounted; Pi4 holds the USB, baud-reset bootloader — see memory
  `feedback_teensy_flash_workflow`/`feedback_flash_workflow`). Claude builds + bumps `FIRMWARE_VERSION`, then STOPS.
- After flash, confirm `[VER] IRIS-EYES firmware=S1??` in `journalctl -u assistant | grep VER`.

## Rollback
Revert the tracking-path edits + `FIRMWARE_VERSION`, reflash the prior build. If EyeController.h was touched,
`git checkout -- src/eyes/EyeController.h` and reflash.

## Status terminology
Firmware stays REPO-ONLY until the operator flashes; don't mark VERIFIED without the operator observing
sustained tracking at the bench. Update CHANGELOG.md before closing.

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

---

## Autonomous prep — S132 (2026-06-13, build ready)

**Diagnosis from full code review:**

| Candidate | Finding |
|---|---|
| `EyeController.h setTargetPosition` seeding (`ed8fa41`) | **INTACT** — lines 518-529 seed `eyeOldX/Y` from current interpolated position before any new target. No regression. |
| Internal wander timer override | **ELIMINATED** — `applyAutoMove()` returns early when `!autoMove && !inMotion`. No rogue saccade fires while tracking. |
| `mouthGreet()` BOING blocking | **PRIMARY — CONFIRMED.** Three synchronous SWSPI `fillScreen+draw` calls in the 0–600 ms window directly follow face acquisition. See below. |
| `box_confidence` / `is_facing` flicker | **SECONDARY** — a single low-confidence frame zeros `maxSize`, resets `faceWasPresent`, and starves a tracking update. Compounds primary. |

**Why mouthGreet is the primary suspect:**

When `mouthGreet()` fires (only when `_idleActive && _idleAnim==0xFF`), it calls `mouthTFTShow(5)` which:
1. `_tft->fillScreen(MTFT_BLACK)` — clears the full 320×240 display over bit-bang SPI
2. `_draw_surprised()` — 314 `fillRect` SWSPI calls

This runs **synchronously inside `reportFaceState()`**, BEFORE `setTargetPosition()` is called — so the
very first target command is delayed by the SWSPI block. The BOING animation then fires two more blocking
redraws via `mouthIdleTick()`:
- T≈300ms: `mouthTFTShow(0)` (phase 2 transition)
- T≈600ms: `mouthApplyIdleTint()` (restore)

Total loop disruption window: **0–600 ms = exactly the observed ~0.5 s drop**.

**S132 implements `DEBUG_FACE` instrumentation. The firmware is built and REPO-ONLY.**

---

### Bench checklist — operator steps to flash + diagnose

**1. Flash S132 firmware:**
```powershell
# On SuperMaster, in the repo directory:
.\scripts\flash_t41.ps1
# Wait for: [VER] IRIS-EYES firmware=S132 built=Jun 13 2026
# Verify in journalctl:
# ssh pi@192.168.1.200 "journalctl -u assistant | grep VER"
```

**2. Enable `DEBUG_FACE` build (to observe the drop):**

The shipped S132 build has `DEBUG_FACE=0` (production-safe). To get the debug prints, rebuild with the
flag enabled:
```cpp
// In src/main.cpp, change line:
#define DEBUG_FACE 0
// to:
#define DEBUG_FACE 1
// Then rebuild: pio run -e eyes
// Then reflash: .\scripts\flash_t41.ps1
```
Or add `-DDEBUG_FACE=1` to `platformio.ini` `build_flags` for the eyes env temporarily.

**3. Watch the serial output when you sit in front of IRIS:**
```bash
ssh pi@192.168.1.200 "journalctl -u assistant -f" | grep "DBG-F\|FACE:"
```
Or open a serial terminal on `/dev/ttyIRIS_EYES` at 115200 on the Pi4 (while bridge is stopped):
```bash
# Stop the bridge temporarily for raw serial:
sudo systemctl stop assistant
minicom -D /dev/ttyIRIS_EYES -b 115200
# Then restart: sudo systemctl start assistant
```

**4. What to observe at the ~0.5 s drop moment:**

| `[DBG-F]` field | What it tells you |
|---|---|
| `greet block_ms=NNN` | **Primary confirmation.** If NNN > 100ms, `mouthGreet()` is blocking the loop at acquisition; disable/gate greet during tracking to fix. |
| `mxSz=0` after a run of `mxSz>0` | **Confidence flicker.** Face disappeared for one read; add hysteresis (require N consecutive misses). |
| `aM=1` while face is present | `autoMove` re-enabled prematurely — `FACE_LOST_TIMEOUT_MS` path firing. Should not occur at 0.5 s. |
| `conf=NN` fluctuating around 60 | Confidence on the threshold; lower gate to 50 or add hysteresis. |
| `tLost=NN` large while `mxSz>0` | `lastDetectionTimeMs` not resetting for the qualifying face — PersonSensor bug. |
| `spk=1` | `eyesSpeaking=true` — tracking suppressed for TTS. Expected during speech. |

**5. Expected output for the mouthGreet primary mechanism:**
```
FACE:1
[DBG-F] greet block_ms=250          <-- ~100-400ms blocking here is the bug
[DBG-F] nF=1 mxSz=1234 conf=180 fac=1 tX=0.12 tY=-0.05 aM=0 spk=0 tLost=0
[DBG-F] nF=1 mxSz=1198 conf=175 fac=1 tX=0.11 tY=-0.04 aM=0 spk=0 tLost=70
[DBG-F] nF=1 mxSz=1210 conf=178 fac=1 tX=0.13 tY=-0.03 aM=0 spk=0 tLost=140
... (tracking reads, face holds)
[DBG-F] greet block_ms≈0 (not printed)   <-- BOING phase 2 at ~300ms blocks mouthIdleTick
[DBG-F] nF=1 mxSz=0 conf=180 fac=1 ...  <-- <-- if THIS appears, it's confidence flicker
```

**6. Proposed fix (test after confirming `block_ms` > 50ms):**

In `reportFaceState()`, gate `mouthGreet()` to skip if face was recently present OR is currently
being tracked. Simplest version — don't greet if face was recently present within the cooldown window
(it's already debounced by `FACE_COOLDOWN_MS=30s`, but the root issue is the greet blocking the
loop at ALL). Consider: defer the greet via a non-blocking flag that fires the BOING from
`mouthIdleTick` on the next iteration AFTER `setTargetPosition()` has already been called.

**7. If `mxSz` stays consistently > 0 and `greet block_ms` is small:**
→ The primary hypothesis is wrong. Look for `aM=1` (wander re-enabled early) or check
`EyeController.h` for any per-frame override of the target position.

**Rollback:** `git checkout -- src/main.cpp src/config.h && pio run -e eyes && .\scripts\flash_t41.ps1`

# IRIS Servo Tuning Handoff

**Target file:** `servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`
**Lines:** 39–44 (constants block)
**Task:** Tune pan servo behavior — currently clunky/jerky when tracking faces.

---

## Current Constants (as of S61b)

```cpp
#define PAN_SPEED     0.04      // multiplier: faceCenterX offset → servo degrees/step
#define PAN_DEAD_ZONE 2.0       // degrees — ignore movements smaller than this
#define FACE_HOLD_MS   2500     // ms to hold position after face lost before returning
#define FACE_RETURN_MS 8000     // ms after face lost to begin return-to-center sweep
```

## How They Work

- **PAN_SPEED** — scales `(faceCenterX - 128) * PAN_SPEED` into a pan delta each loop. Higher = more aggressive tracking, more jerk. Lower = sluggish but smooth.
- **PAN_DEAD_ZONE** — threshold in degrees below which small deltas are ignored. Prevents micro-jitter when face is near center. Higher = more stable center, less responsive to small offsets.
- **FACE_HOLD_MS** — after face disappears, hold the last known position for this long (natural dwell).
- **FACE_RETURN_MS** — after this time with no face, begin sweeping back to 90° center.

## Observed Problem

Pan servo works but is clunky/jerky. Likely causes:
1. PAN_SPEED too high — large steps each poll (poll interval = PERSON_SENSOR_DELAY = 50ms)
2. PAN_DEAD_ZONE too low — jittering on small sensor noise
3. ServoEasing speed/easing type may need adjustment

## Suggested Tuning Approach

Start conservative, flash, observe live, iterate:

| Parameter | Current | Try First | Notes |
|---|---|---|---|
| PAN_SPEED | 0.04 | 0.02 | Halve it — smoother steps |
| PAN_DEAD_ZONE | 2.0 | 5.0 | Bigger dead zone = less jitter |
| FACE_HOLD_MS | 2500 | 2500 | Keep for now |
| FACE_RETURN_MS | 8000 | 6000 | Slightly snappier return |

Also check: what easing type is set on `panServo`? Look for `panServo.setEasingType()` in setup(). `EASE_LINEAR` is jerkiest. `EASE_QUADRATIC_IN_OUT` or `EASE_SINE_IN_OUT` will smooth movement.

## Flash Workflow

**CRITICAL:** Teensy 4.0 is inside the IRIS enclosure. Flash via PlatformIO Upload button ONLY.
- Never instruct the user to press the PROG button
- Claude runs `pio run` (build only), then STOPS
- User clicks the Upload button in PlatformIO IDE
- Board: Teensy 4.0, env: `teensy40_base_mount` (check platformio.ini)
- Connected to desktop USB (not Pi4 during flash)

## After Flashing

Reconnect to Pi4 /dev/ttyACM1 and confirm in iris-web Gestures tab:
- `[BASE] Teensy 4.0 connected on /dev/ttyACM1` in logs
- Gesture events still dispatching correctly

## Rollback

Previous constants are documented above. Revert the four `#define` lines and reflash.

## Related Files

- `servo_teensy40/teensy40_base_mount/platformio.ini`
- `servo_teensy40/teensy40_base_mount/lib/SparkFun_APDS9960/` (local patched library — do not remove)
- `pi4/hardware/base_mount_bridge.py` (Pi4 side — no changes needed for tuning)

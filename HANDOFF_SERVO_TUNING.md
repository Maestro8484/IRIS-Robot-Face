# IRIS Servo Tuning Handoff

**Target file:** `servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`
**Lines:** constants block at top of file
**Task:** Tune pan servo behavior for DS3218MG. Replace APDS-9960 driver with PAJ7620U2.

**Hardware:**
- Teensy 4.0 — handles pan servo + PAJ7620U2 gesture sensor + Person Sensor face tracking
- NOT Teensy 4.1 (that is TeensyEyes + mouth TFT only)
- Servo: Miuzei DS3218MG Digital Servo, 25kg, 0.16s/60deg, metal gear, pin 2
- Gesture sensor: PAJ7620U2 (HiLetgo), I2C 0x73, pins 18/19 shared bus
- APDS-9960 (0x39) is confirmed dead (S66). Do not reference it anywhere.

---

## Current Constants (as of S[next] starting values for DS3218MG)

```cpp
#define PAN_SPEED     0.02      // DS3218MG starting value — halved from prior 0.04
#define PAN_DEAD_ZONE 5.0       // degrees — widened from 2.0 for DS3218MG inertia
#define FACE_HOLD_MS   2500     // ms to hold position after face lost before returning
#define FACE_RETURN_MS 6000     // ms after face lost to begin return-to-center (was 8000)
```

Easing: `EASE_CUBIC_OUT` tracking, `EASE_SINE_OUT` return. Do not change easing type without user instruction.

---

## How They Work

- **PAN_SPEED** — scales `(faceCenterX - 128) * PAN_SPEED` into a pan delta each loop. Higher = more aggressive tracking, more jerk. Lower = sluggish but smooth.
- **PAN_DEAD_ZONE** — threshold in degrees below which small deltas are ignored. Prevents micro-jitter when face is near center.
- **FACE_HOLD_MS** — after face disappears, hold the last known position for this long.
- **FACE_RETURN_MS** — after this time with no face, begin drifting back to 90 center.

---

## DS3218MG Tuning Notes

DS3218MG is heavier and faster-response than the prior servo. Starting conservative:
- If tracking is still jerky after flash: reduce PAN_SPEED to 0.015, increase PAN_DEAD_ZONE to 7.0
- If tracking is sluggish: increase PAN_SPEED to 0.025
- Iterate one constant at a time. Reflash after each change.

---

## PAJ7620U2 Driver Notes

- I2C address: 0x73
- Wire: pins 18/19 (shared bus with Person Sensor 0x62)
- INT pin: unconnected, polling mode
- No proximity channel. LISTEN trigger is touch3 only.
- Gesture output contract (must not change — base_mount_bridge.py depends on these):
    UP    -> Serial.println("VOL+")
    DOWN  -> Serial.println("VOL-")
    LEFT  -> Serial.println("STOP")
    RIGHT -> Serial.println("STOP")
- Library: confirm PlatformIO registry name before writing. If no suitable library,
  implement bare I2C init (write 0xEF 0x00, then 0xEF 0x01, load bank1 config registers)
  and gesture result read from register 0x43.

---

## Flash Workflow

**CRITICAL:** Teensy 4.0 is connected to Pi4 via USB (/dev/ttyIRIS_SERVO). During flash it must be connected to SuperMaster desktop USB instead.
- Claude runs `pio run` (build only) in env `teensy40` — then STOPS
- User clicks the Upload button in PlatformIO IDE
- Board: Teensy 4.0, env: `teensy40` (see platformio.ini)
- After flash: reconnect to Pi4 USB. Confirm `/dev/ttyIRIS_SERVO` present.
- Confirm in assistant logs: `[BASE] Teensy 4.0 connected on /dev/ttyIRIS_SERVO`

## Verification After Flash

1. PlatformIO build: no errors
2. I2C scan via SERIAL_DIAG output: 0x73 ACKs, 0x62 ACKs
3. Swipe UP/DOWN/LEFT/RIGHT: correct serial output in VS Code terminal at 115200
4. Pan servo tracks face without jitter at new constants
5. LISTEN fires on touch3 long hold

## Rollback

```
git checkout -- servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino
git checkout -- servo_teensy40/teensy40_base_mount/platformio.ini
```
Reflash prior firmware via PlatformIO upload.

## Related Files

- `servo_teensy40/teensy40_base_mount/platformio.ini`
- `docs/servo_teensy40_wiring.md`
- `docs/sysmap.json` (teensy40 node)
- `pi4/hardware/base_mount_bridge.py` (Pi4 side — no changes needed for sensor swap or tuning)

# ESP32 + Gesture Sensor — Bringup Findings
Date: 2026-05-22 | Session S58

---

## System Flow Summary (what should happen)

```
APDS-9960 gesture → ESP32 firmware (pin 21/22 I2C)
                  → Serial.println("VOL_UP" | "VOL_DOWN" | "STOP" | "LISTEN")
                  → USB-UART (CH340) → Pi4 /dev/ttyUSB0
                  → assistant.py start_servo_listener() thread
                  → handle_volume_command / _stop_playback / /tmp/iris_manual_listen

Person Sensor 0x62 → ESP32 firmware (same I2C bus)
                   → face center X → panServo.write(pin 13)
```

---

## Issue 1 — CRITICAL: ESP32 not appearing on Pi4 USB (root cause for all missing commands)

**Evidence (live Pi4):**
```
$ lsusb
Bus 001 Device 003: ID 16c0:0483 Teensyduino Serial   ← only Teensy
(no CH340 / CP2102 entries)

$ ls /dev/ttyUSB*
(nothing — /dev/ttyUSB0 does not exist)
```
Assistant.py servo_listener is retrying every 5s indefinitely. `ch341.ko.xz` driver
module is present on the Pi4 but not loaded because no CH340 device has ever connected.

**Root cause:** Almost certainly a **charge-only USB cable** between ESP32 and Pi4.
A charge-only cable has VCC/GND wires but no D+/D- data lines. The ESP32 gets 5V
(confirming why the Person Sensor LED lights up) but the CH340 USB-UART bridge
never enumerates on the USB bus.

**Fix:**
1. Swap the USB cable for a confirmed data-capable cable.
2. After plugging in, run on Pi4: `lsusb | grep -i ch34`
   - Should show: `1a86:7523 QinHeng Electronics HL-340 USB-Serial adapter`
3. Then: `ls /dev/ttyUSB*` should show `/dev/ttyUSB0`
4. Tail journal: `journalctl -u assistant -f` — should show `[SERVO] Connected on /dev/ttyUSB0`

---

## Issue 2 — FIRMWARE BUG: APDS-9960 gesture + proximity register conflict

**Location:** `servo_esp32/IRIS-BaseServoControlViaPerson_Sensor/IRIS-BaseServoControlViaPerson_Sensor.ino` lines 67-73

**Code (as flashed):**
```cpp
apds.enableGestureSensor(true);    // writes PGCONF, PPULSE, GCONF registers
apds.enableProximitySensor(false); // overwrites same PGCONF + PPULSE registers
```

`enableProximitySensor()` overwrites PGAIN and LED pulse count settings that
`enableGestureSensor()` already configured. This can prevent gesture interrupts
from firing. Additionally, `readProximity(proxVal)` on line 93 reads the PDATA
register — but when the gesture engine is running, PDATA is consumed by the gesture
FIFO pipeline and does not reliably reflect actual proximity.

This is the pre-existing RD-011 flag in SNAPSHOT_LATEST.md.

**Fix (to apply before next flash):**
- Remove `apds.enableProximitySensor(false)` from setup(). Gesture engine handles
  proximity internally for its near-threshold detection.
- Remove the proximity-hold LISTEN block in pollGesture() entirely, OR reimplement
  LISTEN using gesture engine's built-in near detection rather than PDATA polling.
- The simplest reliable approach: gestures only (UP/DOWN/LEFT/RIGHT), drop LISTEN
  via proximity. Can be added back properly later.

---

## Issue 3 — Servo not moving

Two possible sub-causes. Address in order:

**3a. Servo 5V rail toggle switch (hardware — check first)**
The HANDOFF checklist item was: `[ ] Servo: PWM signal → pin 13, 5V → servo rail (toggle switch), GND`
If the toggle switch supplying 5V to the servo rail is in the OFF position,
the servo has no power and will not move even with valid PWM signal on pin 13.
Action: verify switch is ON and servo rail measures ~5V.

**3b. Person Sensor I2C not returning data (need serial monitor to confirm)**
The loop() guard:
```cpp
int available = Wire.requestFrom(PERSON_SENSOR_I2C_ADDRESS, PS_EXPECTED_BYTES); // 18 bytes
if (available < PS_EXPECTED_BYTES) {
    delay(PERSON_SENSOR_DELAY);
    return;   // ← servo write never reached
}
```
If the Person Sensor I2C read fails (returns < 18 bytes), the entire servo tracking
section is skipped every loop iteration. The LED on the Person Sensor is autonomous
(built-in sensor firmware) — it lights up regardless of whether the ESP32 is
successfully reading I2C data. So the LED is not proof that I2C is working.

To diagnose: open Serial Monitor on SuperMaster (COM13, 9600 baud). At startup you
should see either "WARN: APDS-9960 not found" or nothing (success). If I2C reads
are failing, you will see only the gesture warn and the loop silently returning.
Add a debug print to confirm (see below).

---

## Recommended Next Actions (in order)

1. **Swap USB cable** (charge-only → data cable). Verify `/dev/ttyUSB0` appears.
   This unblocks ALL gesture commands to Pi4.

2. **Open Serial Monitor on SuperMaster (COM13, 9600)** while ESP32 is live.
   Check for "WARN: APDS-9960 not found" at startup. Watch for any gesture output.

3. **Check servo 5V toggle switch** — confirm it's ON, servo rail has voltage.

4. **Fix firmware** (apply before next flash):
   - Remove `apds.enableProximitySensor(false)` from setup()
   - Remove or guard the `readProximity` LISTEN block
   - Optionally add debug prints for I2C byte count and face detection

5. **Re-flash** (PlatformIO upload, user clicks upload button, COM13).

6. After all above: tail Pi4 logs and trigger gestures to verify full chain.

---

## Code Status

| Component | Status |
|---|---|
| ESP32 firmware | FLASHED (S57) — has firmware bug in APDS setup |
| Pi4 assistant.py | DEPLOYED (S57) — servo_listener correct, waiting for /dev/ttyUSB0 |
| USB serial link | BROKEN — no /dev/ttyUSB0, likely charge-only cable |
| Servo | NOT VERIFIED — needs toggle switch check + serial monitor |
| APDS gestures | NOT VERIFIED — firmware bug + USB link both broken |

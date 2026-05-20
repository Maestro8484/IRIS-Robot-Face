# Handoff: Pico W USB Serial Touch Sensor Integration

**Date:** 2026-05-20
**From:** Claude Code session (servo-pico hardware/code work)
**To:** New Claude Code session
**Priority:** HIGH — Pico W reflashed and working, USB serial touch feature is next step

---

## Architecture decision: USB Serial, not WiFi

Pico W micro-USB → Pi4 USB port. Pico sends one-line commands over USB CDC serial.
Pi4 assistant.py runs a background thread reading `/dev/ttyACM0`.

**Why USB serial over WiFi:**
- No credentials, no network dependency, no HTTP latency
- ~1ms command delivery vs 50-200ms HTTP round trip
- Pi4 USB powers the Pico — no separate 5V supply needed for the board itself
- Code on Pico side: `Serial.println("VOL_UP")` — nothing else required
- Same pattern as Teensy↔Pi4 serial bridge already in use

**Flash workflow note:** Pico can only be connected to ONE USB host at a time.
- To flash from Windows: unplug from Pi4, plug into Windows PC (COM10)
- For runtime use: plug into Pi4 USB port
- No conflict during normal operation — only matters when reflashing

---

## Current State (as of this handoff)

### What is deployed and working
- Pico W freshly flashed (bare board, not yet reinstalled in enclosure)
- Sketch: `servo_pico/IRIS-BaseServoControlViaPerson_Sensor/IRIS-BaseServoControlViaPerson_Sensor.ino`
- Core: Earle Philhower RP2040 (rp2040 architecture) — NOT the Mbed core
- Libraries: Wire (built-in), ServoEasing (Philhower)
- Board: Raspberry Pi Pico W — flash via Windows COM10

### What the sketch currently does
- Pan servo (GPIO 0) tracks faces via Person Sensor I2C (GPIO 6/7)
- Confidence gate (boxConfidence ≥ 60, isFacing == true) before acting
- Dead zone (PAN_DEAD_ZONE = 2.0°) suppresses micro-jitter
- Face lost: holds position 2500ms, drifts back to center after 8000ms
- Touch 1 (GPIO 15, physical pin 20): tap toggles servo tracking on/off. Starts disabled at boot.
- No touch 2/3, no serial commands yet

### Pending hardware work (HW-002 — deferred to PCB rewiring)
- RUN pin (physical 30) currently miswired to on/off switch — disconnect, leave unconnected
- On/off switch moving to servo 5V rail (cuts servo power only, Pico keeps running on USB)
- Hardware-only, no code impact

---

## Task: Add Two New Touch Sensors + USB Serial IRIS Integration

### Hardware — new touch sensors

All three TTP223B sensors grouped on physically adjacent pins:

| Physical pin | GPIO | Signal | Function |
|---|---|---|---|
| 17 | 13 | Touch 2 OUT | Volume hold-toggle (hold = increase, hold again = decrease) |
| 18 | GND | GND | Touch 2 GND |
| 19 | 14 | Touch 3 OUT | TTS interrupt (tap) / wakeword+mic trigger (hold >1s) |
| 20 | 15 | Touch 1 OUT | Servo enable/disable (existing) |
| 21 | GND | GND | Shared GND for Touch 1 + Touch 3 |

Power for all TTP223B sensors: 3V3 OUT (physical pin 36).
Pico board power: Pi4 USB (VSYS fed via micro-USB, no separate 5V supply needed).
Servo power: still needs its own 5V rail (servos exceed USB current budget).

### Behavior spec

**Touch 2 — Volume (GPIO 13)**
- Hold: volume changes continuously while held, tick every 200ms
- Release then hold again: direction reverses
- Direction state persists until next press reverses it
- Serial command per tick: `VOL_UP` or `VOL_DOWN`

**Touch 3 — TTS interrupt / wakeword (GPIO 14)**
- Short tap (<1s): interrupt current TTS output → serial command `STOP`
- Long hold (≥1s): trigger listen cycle without speaking wakeword → serial command `LISTEN`

---

## Implementation — Pico W sketch changes

### Additions to .ino

```cpp
#define TOUCH2_PIN 13
#define TOUCH3_PIN 14
```

In setup():
```cpp
  pinMode(TOUCH2_PIN, INPUT);
  pinMode(TOUCH3_PIN, INPUT);
  // Serial.begin(9600) already present — used for USB CDC to Pi4
```

In loop() — add after existing touch 1 block:
```cpp
  // Touch 2 — volume hold-toggle
  static bool lastTouch2    = false;
  static bool volIncreasing = true;
  static unsigned long lastVolTickMs = 0;
  bool touch2 = digitalRead(TOUCH2_PIN);
  if (touch2 && !lastTouch2) volIncreasing = !volIncreasing;
  if (touch2 && (millis() - lastVolTickMs > 200)) {
    lastVolTickMs = millis();
    Serial.println(volIncreasing ? "VOL_UP" : "VOL_DOWN");
  }
  lastTouch2 = touch2;

  // Touch 3 — TTS interrupt / wakeword
  static bool lastTouch3 = false;
  static unsigned long touch3PressMs = 0;
  bool touch3 = digitalRead(TOUCH3_PIN);
  if (touch3 && !lastTouch3) touch3PressMs = millis();
  if (!touch3 && lastTouch3) {
    unsigned long held = millis() - touch3PressMs;
    Serial.println(held < 1000 ? "STOP" : "LISTEN");
  }
  lastTouch3 = touch3;
```

---

## Implementation — Pi4 side

### Step 1: Identify serial port

When Pico W is plugged into Pi4 USB, it appears as `/dev/ttyACM0` (or `ttyACM1` if something else is on ACM0). Verify on Pi4:
```bash
ls /dev/ttyACM*
```

### Step 2: Verify what Pi4 endpoints/mechanisms already exist

**Before writing any new Pi4 code**, read these files:
- `pi4/assistant.py` — check for: volume control, TTS stop mechanism, manual listen trigger
- `pi4/iris_web.py` — check for: `/api/volume` route, any stop/listen routes

Do NOT assume these exist. If they do, wire the serial listener to call them. If they don't, add them.

### Step 3: Add serial listener thread to assistant.py

Add a background thread that reads from `/dev/ttyACM0` and dispatches commands.
The TeensyBridge pattern already in assistant.py is the reference — follow the same structure.

```python
# Conceptual outline only — read actual assistant.py before writing
import serial, threading

PICO_PORT = '/dev/ttyACM0'
PICO_BAUD = 9600

def pico_listener():
    try:
        ser = serial.Serial(PICO_PORT, PICO_BAUD, timeout=1)
        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line == 'VOL_UP':
                adjust_volume(+5)
            elif line == 'VOL_DOWN':
                adjust_volume(-5)
            elif line == 'STOP':
                stop_tts()
            elif line == 'LISTEN':
                trigger_listen()
    except Exception as e:
        log(f"[PICO] serial error: {e}")

threading.Thread(target=pico_listener, daemon=True).start()
```

**Key constraint:** `stop_tts()` and `trigger_listen()` must be thread-safe. Check how TeensyBridge handles this in the existing code and follow the same pattern exactly.

### Step 4: Volume control implementation

Check iris_config.json for current VOL_MAX. Volume control likely calls `amixer` or `pactl` on Pi4.
Find how the existing Web UI volume control works (if it exists) and reuse that function — do not write a new one.

---

## Implementation order

1. Read `pi4/assistant.py` in full — understand TeensyBridge thread pattern, TTS stop, volume, listen trigger.
2. Read `pi4/iris_web.py` — check for existing volume/stop/listen routes.
3. Write Pico W sketch additions (touch 2/3 + serial commands) — simple, no Pi4 needed yet.
4. Flash Pico W (disconnect from Pi4, plug into Windows COM10, upload, reconnect to Pi4).
5. Add pico_listener thread to assistant.py, wiring to existing mechanisms.
6. Deploy assistant.py to Pi4 per standard persist protocol. Restart assistant service.
7. Test: plug Pico into Pi4, verify `ls /dev/ttyACM0`, tail assistant logs, test each touch.

---

## Files to touch

| File | Change |
|---|---|
| `servo_pico/.../IRIS-BaseServoControlViaPerson_Sensor.ino` | Add TOUCH2_PIN, TOUCH3_PIN, serial commands |
| `pi4/assistant.py` | Add pico_listener thread, wire to volume/stop/listen |
| `pi4/iris_web.py` | Add routes only if missing and needed |
| `docs/sysmap.json` | Add GPIO 13/14 to servo_pico gpio section |
| `IRIS_ARCH.md` | Update servo section: USB serial link, 3 touch sensors |
| `SNAPSHOT_LATEST.md` | Update after deploy |

---

## SSH / deploy reference
- Pi4 SSH: `ssh pi@192.168.1.200`, password `ohs` — password auth only, key auth fails
- Pi4 persist pattern: copy to `/home/pi/`, then remount rw and copy to `/media/root-ro/home/pi/`, md5 verify, remount ro, restart `assistant` service
- See `CLAUDE.md` for full persist command sequence

## Do not touch
- Teensy 4.1 firmware
- GandalfAI models
- Pi4 sleep/wake/TTS pipeline beyond the specific stop/listen hooks
- `iris_config.json` unless volume implementation requires it

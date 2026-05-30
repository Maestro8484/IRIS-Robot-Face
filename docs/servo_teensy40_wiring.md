# IRIS Base Mount Controller — Wire & Pin Mapping
**Last updated:** 2026-05-29 (S75: servo control constants updated; PAJ7620U2 dead HW-004, GY-PAJ7620 replacement pending install)
**Board:** Teensy 4.0
**Status:** CURRENT — active board

---

## Board History (do not re-litigate)

| Iteration | Board | Outcome |
|---|---|---|
| 1 | Raspberry Pi Pico (original) | Failed — wiring/board issues, standalone only |
| 2 | Raspberry Pi Pico W | Failed — Pi4 interface unreliable |
| 3 | Teensy 4.0 (first attempt) | Abandoned mid-attempt |
| 4 | ESP32 DevKit1C | Failed — clone board, chronic flakiness |
| 5 | ESP32-C3 XIAO | Rejected — insufficient clean GPIO for task |
| 6 | Waveshare ESP32-S3-Zero | Rejected — manual BOOT button required every flash |
| 7 (current) | Teensy 4.0 | Confirmed. Auto-reset, known toolchain, sufficient GPIO |

The PCB from iteration 4 was physically destroyed. This is a clean build.

---

## Teensy 4.0 Signal Pins

| Pin | Wire color | Device / Label | Notes |
|---|---|---|---|
| 2 | Yel/Org | Pan servo PWM | panServo.attach(2) — hardware PWM, no conflicts |
| 18 | Blue | SDA — I2C shared bus | Wire default SDA (fixed pin on Teensy 4.0) |
| 19 | Yellow | SCL — I2C shared bus | Wire default SCL (fixed pin on Teensy 4.0) |

---

## I2C Device Map (shared bus, Wire pins 18/19)

| Device | Address | Notes |
|---|---|---|
| Person Sensor (Useful Sensors) | 0x62 | Face detection, mounted right-side-up |
| GY-PAJ7620 (replacement) | 0x73 | Gesture sensor — **HW-004: current HiLetgo PAJ7620U2 dead** (ACK=NO, reflow failed). GY-PAJ7620 replacement on order. Seats identically — same address, same wiring. INT unconnected (polling mode). |

APDS-9960 (0x39) confirmed dead S66 — removed and replaced with PAJ7620U2 (HiLetgo).
HiLetgo PAJ7620U2 confirmed dead S69 — ACK=NO, I2C scan shows 0x73 absent, reflow attempted and failed.
GY-PAJ7620 replacement module on order — seats identically at 0x73 on same SDA/SCL wiring.

No address conflict between 0x62 and 0x73. Both on same SDA/SCL lines.

**Required:** 4.7K pullup resistor from SDA to 3.3V. 4.7K pullup resistor from SCL to 3.3V.
Internal Teensy pullups are insufficient for two devices.

---

## Power Pins

| Pin label | Wire color | Device / Label | Notes |
|---|---|---|---|
| micro-USB | — | Pi4 USB port | Board power + USB CDC serial comms |
| 3.3V | Red/Orange | Sensor VCC bus | Person Sensor VCC + GY-PAJ7620 VCC (module has onboard regulator on some variants — confirm 3.3V on VIN pin) |
| GND | Black | Main GND bus | Sensor GND + servo signal GND + servo supply GND |

---

## Person Sensor Breakout — Pin to Wire

Address 0x62. Shares I2C bus with PAJ7620U2.

| Board Pin | Wire | To |
|---|---|---|
| VCC | Solid orange | Teensy 4.0 3.3V pin |
| GND | Blue/white stripe | Teensy 4.0 GND pin |
| SDA | Solid blue | Teensy 4.0 pin 18 (SDA) |
| SCL | Yellow | Teensy 4.0 pin 19 (SCL) |

---

## GY-PAJ7620 Breakout — Pin to Wire

**HW-004 STATUS:** HiLetgo PAJ7620U2 (original) confirmed dead — ACK=NO on I2C scan, reflow attempted, 0x73 absent from bus. Physically still seated. GY-PAJ7620 replacement module on order.

Address 0x73. INT unconnected (polling mode). Keep clear line of sight to sensor window.
Seats identically to the dead HiLetgo PAJ7620U2 — no rewiring required on install.
VIN is 3.3V (GY-PAJ7620 module has onboard LDO — connect VIN, not VCC, if the board has both; confirm pinout on delivery).

| Board Pin | Wire | To | Notes |
|---|---|---|---|
| VIN | Solid orange | Teensy 4.0 3.3V pin | Some GY modules label this VCC — confirm before powering |
| GND | Blue/white stripe | Teensy 4.0 GND pin | |
| SDA | Solid blue | Teensy 4.0 pin 18 (SDA) | Parallel with Person Sensor SDA |
| SCL | Blue/white stripe | Teensy 4.0 pin 19 (SCL) | Parallel with Person Sensor SCL |
| INT | — | Unconnected | Using polling mode |

**Install checklist (future session):**
1. Remove dead HiLetgo PAJ7620U2. Seat GY-PAJ7620 identically.
2. Power cycle. Open serial monitor within 8s.
3. Confirm `DIAG: PAJ7620U2 0x73 ACK=YES` and `DIAG: PAJ7620U2 init=OK`.
4. Then flash TS40-S1 firmware (see HANDOFF_CURRENT.md).

---

## Pan Servo — DS3218MG (Miuzei)

Replaces prior servo. Same pin, same power rail.

| Spec | Value |
|---|---|
| Model | Miuzei DS3218MG Digital Servo MS24 |
| Torque | 25kg/cm |
| Speed | 0.16s/60deg at 6V |
| Gears | Metal |
| Signal pin | Teensy 4.0 pin 2 (PWM) |
| Power | External 5V rail (toggle switch on enclosure) |
| Range | 0-180 deg, center 90 |

---

## Power Distribution

| Rail | Source | Destination | Switch |
|---|---|---|---|
| USB (board power) | Pi4 USB port | Teensy micro-USB | None — always live |
| 3.3V (sensors) | Teensy 3.3V pin | Person Sensor VCC, PAJ7620U2 VCC | None |
| 5V (servo) | External 5V supply | Servo VCC | Physical toggle switch on enclosure |
| GND | Teensy GND pin | Sensor GND, servo signal GND, servo supply GND | None |

Physical toggle cuts servo 5V only. Teensy stays live on Pi4 USB at all times.
Do not power servo from Teensy rail.

---

## USB Serial Commands (Teensy 4.0 to Pi4)

All 8 gesture commands dispatched via `hardware/base_mount_bridge.py`. Default Pi4 actions are configurable per-gesture in `iris_config.json` (GESTURE_MAP) via the web UI Gestures tab.

| GY-PAJ7620 gesture (physical) | Serial command | Default Pi4 action |
|---|---|---|
| Swipe UP | `VOL+\n` | Volume up |
| Swipe DOWN | `VOL-\n` | Volume down |
| Swipe LEFT | `STOP\n` | Interrupt current TTS playback |
| Swipe RIGHT | `STOP\n` | Interrupt current TTS playback |
| Push toward sensor | `FORWARD\n` | LISTEN (activate listen mode) |
| Pull away from sensor | `BACKWARD\n` | SLEEP |
| Clockwise wrist rotation | `CW\n` | VOL+ |
| Counter-clockwise rotation | `CCW\n` | VOL- |

Pi4 serial port: `/dev/ttyIRIS_SERVO` at 115200 baud (udev symlink — hardware serial 12763490).
Teensy 4.1 display controller owns `/dev/ttyIRIS_EYES` (hardware serial 13625440).
Pi4 handler: `hardware/base_mount_bridge.py` daemon thread in `assistant.py`.
Valid configurable actions: VOL+, VOL-, STOP, LISTEN, SLEEP, WAKE, MUTE, SKIP.

---

## Servo Control Notes

- Pan only (rotation). No tilt.
- Center position: 90 degrees
- Clamp range: `PAN_MIN` 65° – `PAN_MAX` 115° (software constrained)
- ServoEasing library: dual easing — `EASE_LINEAR` for face tracking (set per-call), `EASE_CUBIC_IN_OUT` for idle center-return (set per-call)
- Tracking API: `startEaseTo(filteredPan, PAN_TRACK_SPEED)` — constant 8 deg/sec, no `isMoving()` guard (servo continuously chases face)
- Low-pass filter: `filteredPan` (alpha=0.15) smooths direction reversals over ~130ms; damps momentum asymmetry in top-heavy mount
- Torque release: `panServo.detach()` when within 1° of center at idle — releases DS3218MG holding torque; re-attach before next move
- Return-to-center: `startEaseToD(desiredPan, 100)` with `isMoving()` guard; triggers after `FACE_RETURN_MS` (6000ms) face-lost
- Tuning constants (pan_servo.h): `PAN_TRACK_SPEED` 8.0, `PAN_FILTER_ALPHA` 0.15, `PAN_DEAD_ZONE` 5.0, `FACE_HOLD_MS` 2500, `FACE_RETURN_MS` 6000

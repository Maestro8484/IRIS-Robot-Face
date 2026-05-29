# IRIS Base Mount Controller — Wire & Pin Mapping
**Last updated:** 2026-05-28 (DS3218MG confirmed installed; ServoEasing async API notes updated to S70)
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
| PAJ7620U2 (HiLetgo) | 0x73 | Gesture sensor — replaces dead APDS-9960 (S66). INT unconnected. |

APDS-9960 (0x39) confirmed dead S66 — I2C no-response, 0x0 from ID register. Physically removed and replaced with PAJ7620U2.

No address conflict. Both devices on same SDA/SCL lines.

**Required:** 4.7K pullup resistor from SDA to 3.3V. 4.7K pullup resistor from SCL to 3.3V.
Internal Teensy pullups are insufficient for two devices.

---

## Power Pins

| Pin label | Wire color | Device / Label | Notes |
|---|---|---|---|
| micro-USB | — | Pi4 USB port | Board power + USB CDC serial comms |
| 3.3V | Red/Orange | Sensor VCC bus | Person Sensor VCC + PAJ7620U2 VCC |
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

## PAJ7620U2 Breakout (HiLetgo) — Pin to Wire

Address 0x73. INT unconnected (polling mode). Keep clear line of sight to sensor window.
Replaces APDS-9960 on same physical I2C bus wiring. VCC is 3.3V (module has onboard regulator on some variants — confirm 3.3V on VCC pin before wiring).

| Board Pin | Wire | To | Notes |
|---|---|---|---|
| VCC | Solid orange | Teensy 4.0 3.3V pin | |
| GND | Blue/white stripe | Teensy 4.0 GND pin | |
| SDA | Solid blue | Teensy 4.0 pin 18 (SDA) | Parallel with Person Sensor SDA |
| SCL | Blue/white stripe | Teensy 4.0 pin 19 (SCL) | Parallel with Person Sensor SCL |
| INT | — | Unconnected | Using polling mode |

---

## Pan Servo — DS3218MG (Miuzei)

Replaces prior servo. Same pin, same power rail.

| Spec | Value |
|---|---|
| Model | Miuzei DS3218MG Digital Servo |
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

| PAJ7620U2 input | Serial command | Pi4 behavior |
|---|---|---|
| Swipe UP | VOL+\n | Volume up |
| Swipe DOWN | VOL-\n | Volume down |
| Swipe LEFT | STOP\n | Interrupt current TTS playback |
| Swipe RIGHT | STOP\n | Interrupt current TTS playback |

Pi4 serial port: `/dev/ttyIRIS_SERVO` at 115200 baud (USB CDC, udev symlink — hardware serial 12763490).
Teensy 4.1 display controller owns `/dev/ttyIRIS_EYES`.
Pi4 handler: `hardware/base_mount_bridge.py` daemon thread in `assistant.py`.

LISTEN trigger: capacitive touch3 only (no proximity channel on PAJ7620U2).
Short tap (<1s) = STOP. Long hold (>=1s) = LISTEN.

---

## Servo Control Notes

- Pan only (rotation). No tilt.
- Center position: 90 degrees
- Clamp range: PAN_MIN 45° – PAN_MAX 135° (software constrained via constants)
- ServoEasing library: EASE_CUBIC_IN_OUT (single easing type, set once at setup)
- Motion API: `startEaseToD(target, 100)` — async, non-blocking 100ms move
- `isMoving()` guard: new move only issued when servo is not already in motion
- Return-to-center: same async pattern; triggers after FACE_RETURN_MS (6000ms) face-lost

# IRIS Base Mount Controller — Wire & Pin Mapping
**Last updated:** 2026-05-23 (planning session — Teensy 4.0 confirmed final board)
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
| APDS-9960 | 0x39 | Gesture sensor — polling mode, INT unconnected |

No address conflict. Both on same SDA/SCL lines.

**Required:** 4.7K pullup resistor from SDA to 3.3V. 4.7K pullup resistor from SCL to 3.3V.
Solder one leg of each resistor to 3.3V rail, other leg to the respective bus line.
Internal Teensy pullups are insufficient for two devices.

---

## Power Pins

| Pin label | Wire color | Device / Label | Notes |
|---|---|---|---|
| micro-USB | — | Pi4 USB port | Board power + USB CDC serial comms |
| 3.3V | Red/Orange | Sensor VCC bus | Person Sensor VCC + APDS-9960 VCC + APDS-9960 VL |
| GND | Black | Main GND bus | Sensor GND + servo signal GND + servo supply GND |

---

## Person Sensor Breakout — Pin to Wire

Address 0x62. Shares I2C bus with APDS-9960.

| Board Pin | Wire | To |
|---|---|---|
| VCC | Solid orange | Teensy 4.0 3.3V pin |
| GND | Blue/white stripe | Teensy 4.0 GND pin |
| SDA | Solid blue | Teensy 4.0 pin 18 (SDA) |
| SCL | Yellow | Teensy 4.0 pin 19 (SCL) |

---

## APDS-9960 Breakout — Pin to Wire

Address 0x39. INT unconnected (polling mode). Keep clear line of sight to the two IR emitters on the board.

| Board Pin | Wire | To | Notes |
|---|---|---|---|
| VCC | Solid orange | Teensy 4.0 3.3V pin | Twist with VL at Teensy end |
| VL | Solid orange | Teensy 4.0 3.3V pin | Twist with VCC at Teensy end |
| GND | Blue/white stripe | Teensy 4.0 GND pin | |
| SDA | Solid blue | Teensy 4.0 pin 18 (SDA) | Parallel with Person Sensor SDA |
| SCL | Blue/white stripe | Teensy 4.0 pin 19 (SCL) | Parallel with Person Sensor SCL |
| INT | — | Unconnected | |

---

## Power Distribution

| Rail | Source | Destination | Switch |
|---|---|---|---|
| USB (board power) | Pi4 USB port | Teensy micro-USB | None — always live |
| 3.3V (sensors) | Teensy 3.3V pin | Person Sensor VCC, APDS-9960 VCC+VL | None |
| 5V (servo) | External 5V supply | Servo VCC | Physical toggle switch on enclosure |
| GND | Teensy GND pin | Sensor GND, servo signal GND, servo supply GND | None |

Physical toggle cuts servo 5V only. Teensy stays live on Pi4 USB at all times.
Do not power servo from Teensy rail.

---

## USB Serial Commands (Teensy 4.0 → Pi4)

| APDS-9960 input | Serial command | Pi4 behavior |
|---|---|---|
| Swipe UP | VOL+\n | Volume up |
| Swipe DOWN | VOL-\n | Volume down |
| Swipe LEFT | STOP\n | Interrupt current TTS playback |
| Swipe RIGHT | STOP\n | Interrupt current TTS playback |

Pi4 serial port: `/dev/ttyIRIS_SERVO` at 115200 baud (USB CDC, udev symlink S63 — hardware serial 12763490).
Teensy 4.1 display controller owns `/dev/ttyIRIS_EYES`.
Pi4 handler: `hardware/base_mount_bridge.py` daemon thread in `assistant.py`.

**Note:** APDS-9960 chip confirmed dead S66 (I2C no-response, 0x0 from ID register). PAJ7620U2 replacement (0x73) received, pending enclosure access and wiring.

---

## Servo Control Notes

- Pan only (rotation). No tilt.
- Center position: 90 degrees
- Clamp range: 45–135 degrees
- Smooth incremental movement toward target each loop iteration — no snapping
- Center on face lost — do not hold last position or sweep


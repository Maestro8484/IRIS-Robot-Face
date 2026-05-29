# IRIS Base Mount Controller — Teensy 4.0 Firmware

**Board:** Teensy 4.0 (iteration 7 — current active board)
**Status:** Active. DS3218MG installed and operational. Firmware current as of S70 (ServoEasing async, PAN_MIN/MAX, PAN? query).

## Hardware

- Pan servo: Miuzei DS3218MG MS24 Digital Servo (25kg metal gear), pin 2 (hardware PWM), shared I2C bus with Person Sensor
- I2C SDA: pin 18 (Wire default, shared bus)
- I2C SCL: pin 19 (Wire default, shared bus)
- Person Sensor: addr 0x62
- PAJ7620U2 gesture sensor (HiLetgo): addr 0x73 — replaces dead APDS-9960 (S66)
- Touch3 LISTEN/STOP: pin 15 (T3 capacitive)
- Pi4 comms: USB CDC serial at 115200 baud (/dev/ttyIRIS_SERVO)
- Servo power: external 5V supply (not from Teensy rail)

## Wiring reference

docs/servo_teensy40_wiring_onenote.html

## Firmware

`teensy40_base_mount/teensy40_base_mount.ino` — current firmware. Build with PlatformIO env `teensy40`, user performs upload.

See `docs/servo_teensy40_wiring.md` for full pin/wiring/power detail.

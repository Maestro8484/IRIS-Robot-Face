# IRIS Base Mount Controller — Teensy 4.0 Firmware

**Board:** Teensy 4.0 (iteration 7 — current active board)
**Status:** Active. New firmware to be written here by Claude Code.

## Hardware

- Pan servo: pin 2 (hardware PWM)
- I2C SDA: pin 18 (Wire default, shared bus)
- I2C SCL: pin 19 (Wire default, shared bus)
- Person Sensor: addr 0x62
- APDS-9960 gesture sensor: addr 0x39
- Pi4 comms: USB CDC serial at 115200 baud (/dev/ttyACM1)
- Servo power: external 5V supply (not from Teensy rail)

## Wiring reference

docs/servo_teensy40_wiring_onenote.html

## Note on existing .ino file

IRIS-BaseServoControlViaPerson_Sensor.ino in this directory is from an earlier
Teensy 4.0 attempt. Claude Code will rewrite it as part of the base mount
controller implementation task. Do not flash the existing file.

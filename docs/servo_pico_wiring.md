# Servo Pico W — Wire & Pin Mapping
**Last updated:** 2026-05-20 (S55, RD-009 iteration 4)
**Board:** Raspberry Pi Pico W | USB connector at top | Left side = pins 1–20 | Right side = pins 21–40

---

## Left Side — Signal Pins (USB end at top, going down)

| Phys Pin | GPIO    | Wire color | Device / Label                        | Notes                                      |
|----------|---------|-----------|---------------------------------------|--------------------------------------------|
| 1        | 0       | Yel/Org   | Pan servo PWM                         | panServo.attach(0)                         |
| 9        | 6       | Blue      | SDA — I2C Person Sensor               | Wire.setSDA(6)                             |
| 10       | 7       | Yellow    | SCL — I2C Person Sensor               | Wire.setSCL(7)                             |
| 17       | 13      | —         | Button 2 — Volume (terminal A)        | active-low INPUT_PULLUP; terminal B to GND |
| 19       | 14      | —         | Button 3 — TTS/Wakeword (terminal A)  | active-low INPUT_PULLUP; terminal B to GND |
| 20       | 15      | —         | Button 1 — Reserved (terminal A)      | wired, unassigned in firmware              |

---

## Right Side — Power Pins (USB end at top, going down)

| Phys Pin | GPIO    | Wire color | Device / Label                        | Notes                                               |
|----------|---------|-----------|---------------------------------------|-----------------------------------------------------|
| 21       | GND     | —         | Button GND bus                        | shared GND terminal for all 3 button terminal B's   |
| 30       | RUN     | —         | DISCONNECTED                          | HW-002: was on/off switch — leave floating          |
| 36       | 3V3 OUT | —         | (unused — no TTP223B VCC needed)      | available for future use                            |
| 38       | GND     | —         | Main GND bus                          | PCB ground terminal                                 |
| 39       | VSYS    | —         | 5V power in                           | from servo 5V supply rail via PCB screw terminal    |

---

## Button Wiring (each momentary pushbutton)

```
Pico GPIO pin ── Terminal A ──[BUTTON]── Terminal B ── GND bus
```

- No resistors needed — Pico internal pull-up handles it
- Pressed = GPIO pulled LOW = detected as active
- All terminal B's share a single GND bus (pin 21 or pin 38)

---

## Power Distribution

| Rail         | Source                        | Destination                        | Switch                                          |
|--------------|-------------------------------|------------------------------------|-------------------------------------------------|
| 5V (VSYS)    | Servo supply PCB terminal     | Pico pin 39 (VSYS)                 | None — Pico always live when supply connected   |
| 5V (servo)   | Same servo supply terminal    | Servo power wire                   | Physical toggle on enclosure (5V+ to servo 5V+) |
| GND          | Pico pins 21 + 38             | Servo GND, button GNDs, GND bus    | None                                            |
| USB          | Pi4 USB → Pico micro-USB      | Pico board power + serial comms    | None — runtime connection                       |

**Key point:** Physical toggle cuts servo 5V only. Pico stays live on Pi4 USB.
Button 1 (GPIO 15) is reserved — wired but no firmware action assigned.

---

## USB Serial Commands (Pico → Pi4)

| Button  | Action          | Serial command | Pi4 behavior                        |
|---------|----------------|----------------|-------------------------------------|
| Button 2 | Short press    | VOL_UP / VOL_DOWN | amixer volume ±5 (direction toggles each press) |
| Button 2 | Hold           | VOL_UP / VOL_DOWN every 200ms | continuous volume change    |
| Button 3 | Short tap <1s  | STOP           | interrupt current TTS playback      |
| Button 3 | Hold ≥1s       | LISTEN         | trigger listen cycle (no wakeword)  |
| Button 1 | any            | (none)         | reserved                            |

---

## Build / Design Iteration History

### Iteration 1 — Initial prototype
- Pan + tilt dual servos, Person Sensor I2C, Pico W on WiFi → Pi4 HTTP
- No buttons, no centralized PCB, loose wiring, power switch on RUN pin

### Iteration 2 — Tilt removed, first button added
- Pan servo only, one TTP223B capacitive sensor (GPIO 15) for servo enable/disable toggle
- WiFi retained, RUN pin still on switch (HW-002 open)

### Iteration 3 — Three TTP223B sensors, WiFi HTTP comms
- Touch 2 (GPIO 13) and Touch 3 (GPIO 14) added on adjacent pins
- Volume and TTS/wakeword via HTTP calls to Pi4 web API
- Capacitive sensing through 5.8mm acrylic ruled out — too thick, unreliable without copper foil extension

### Iteration 4 — Momentary pushbuttons, USB serial, simplified power (current)
**Design principle:** Eliminate every dependency that isn't strictly necessary.
- TTP223B capacitive sensors replaced with standard momentary pushbuttons (threaded mount, laser-cut panel)
- WiFi removed entirely — USB CDC serial replaces all HTTP (VOL_UP, VOL_DOWN, STOP, LISTEN)
- Buttons wired active-low with INPUT_PULLUP — no external resistors, no VCC wire needed
- Pico powered by Pi4 USB (VSYS) — board always live, zero extra wiring to Pi4
- Servo 5V isolated: physical toggle on enclosure between supply 5V+ and servo 5V+
- RUN pin disconnected (HW-002 resolved)
- Button 1 (GPIO 15) reserved — physical switch handles servo enable/disable
- All connections centralized on PCB protoboard with screw terminals

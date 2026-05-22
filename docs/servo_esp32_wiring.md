# Servo Controller — Wire & Pin Mapping
**Last updated:** 2026-05-21 (S57, iteration 6)
**Board:** ESP32 DevKit 1C / ESP32-WROOM-32 (replacing Teensy 4.0 — final board choice)

---

## ESP32 Signal Pins

| Pin# | Wire color | Device / Label                        | Notes                                      |
|------|-----------|---------------------------------------|--------------------------------------------|
| 13   | Yel/Org   | Pan servo PWM                         | panServo.attach(13)                        |
| 21   | Blue      | SDA — I2C shared bus                  | Wire.begin(21, 22)                         |
| 22   | Yellow    | SCL — I2C shared bus                  | Wire.begin(21, 22)                         |

> GPIO 13 safe for servo PWM — not a strapping pin on ESP32-WROOM-32.
> Avoid for servo: GPIO 0 (BOOT), 2, 12, 15 (strapping pins, affect boot mode).

---

## Previous Board (Teensy 4.0 — replaced S57)

| Pin# | Wire color | Device / Label                        | Notes                                      |
|------|-----------|---------------------------------------|--------------------------------------------|
| 9    | Yel/Org   | Pan servo PWM                         | panServo.attach(9)                         |
| 18   | Blue      | SDA — I2C shared bus                  | Wire default SDA (Teensy 4.0 fixed)        |
| 19   | Yellow    | SCL — I2C shared bus                  | Wire default SCL (Teensy 4.0 fixed)        |

---

## Previous Board (Pico W — dead, iteration 4)

| Phys Pin | GPIO    | Wire color | Device / Label                        | Notes                                      |
|----------|---------|-----------|---------------------------------------|--------------------------------------------|
| 1        | 0       | Yel/Org   | Pan servo PWM                         | panServo.attach(0)                         |
| 9        | 6       | Blue      | SDA — I2C Person Sensor               | Wire.setSDA(6)                             |
| 10       | 7       | Yellow    | SCL — I2C Person Sensor               | Wire.setSCL(7)                             |
| 14       | 10      | —         | Button 2 — Volume (terminal A)        | active-low INPUT_PULLUP; terminal B to GND |
| 15       | 11      | —         | Button 3 — TTS/Wakeword (terminal A)  | active-low INPUT_PULLUP; terminal B to GND |
| 16       | 12      | —         | Button 1 — Reserved (terminal A)      | wired, unassigned in firmware              |

---

## ESP32 DevKit 1C Power Pins

| Pin label | Wire color | Device / Label                        | Notes                                               |
|-----------|-----------|---------------------------------------|-----------------------------------------------------|
| micro-USB | —         | Pi4 USB → ESP32                       | Board power + USB-UART serial comms                 |
| 3V3       | Red       | Sensor VCC bus                        | Person Sensor VCC + APDS-9960 VCC                   |
| GND       | Black     | Main GND bus                          | Sensor GND + servo GND                              |

**Key point:** Physical toggle cuts servo 5V only. ESP32 stays live on Pi4 USB.

---

## Power Distribution

| Rail         | Source                        | Destination                        | Switch                                          |
|--------------|-------------------------------|------------------------------------|-------------------------------------------------|
| 3.3V (sensor)| ESP32 3V3 pin                 | Person Sensor VCC, APDS-9960 VCC   | None                                            |
| 5V (servo)   | Servo supply PCB terminal     | Servo power wire                   | Physical toggle on enclosure (5V+ to servo 5V+) |
| GND          | ESP32 GND pin                 | Servo GND, sensor GND bus          | None                                            |
| USB          | Pi4 USB → ESP32 micro-USB     | ESP32 board power + serial comms   | None — runtime connection                       |

---

## USB Serial Commands (ESP32 → Pi4)

| APDS-9960 input        | Serial command | Pi4 behavior                        |
|------------------------|----------------|-------------------------------------|
| UP gesture             | VOL_UP         | set_volume(+5)                      |
| DOWN gesture           | VOL_DOWN       | set_volume(-5)                      |
| LEFT / RIGHT gesture   | STOP           | interrupt current TTS playback      |
| Proximity > 150 held 1s| LISTEN         | trigger listen cycle (no wakeword)  |

Pi4 serial port: `/dev/ttyUSB0` at 9600 baud (CH340/CP2102 USB-UART bridge on DevKit).

---

## Build / Design Iteration History

### Iteration 6 — ESP32 DevKit 1C (current)
**2026-05-21 S57** — Teensy 4.0 replaced with ESP32 DevKit 1C (ESP32-WROOM-32, COM13).
- Platform: `espressif32` / board: `esp32dev` in platformio.ini
- Wire.begin(21, 22) — explicit SDA/SCL for ESP32
- panServo.attach(13) — GPIO 13, not a strapping pin
- USB-UART bridge → /dev/ttyUSB0 on Pi4 (vs /dev/ttyACM1 for Teensy CDC)
- APDS-9960 gesture commands unchanged: VOL_UP, VOL_DOWN, STOP, LISTEN
- Pi4 assistant.py SERVO_PORT updated to /dev/ttyUSB0

### Iteration 5 — Teensy 4.0 (replaced by iteration 6)
**2026-05-21 S56** — Pico W dead (hardware failure, no USB enumeration). Replaced with Teensy 4.0.
- Platform: `teensy` / board: `teensy40`
- Wire.setSDA/SCL removed — Teensy 4.0 fixed I2C pins (18=SDA, 19=SCL)
- panServo.attach(9)
- USB CDC serial → /dev/ttyACM1 on Pi4

### Iteration 4 — Momentary pushbuttons, USB serial, simplified power
**Design principle:** Eliminate every dependency that isn't strictly necessary.
- TTP223B capacitive sensors replaced with standard momentary pushbuttons
- WiFi removed entirely — USB CDC serial replaces all HTTP (VOL_UP, VOL_DOWN, STOP, LISTEN)
- Buttons wired active-low with INPUT_PULLUP
- Pico powered by Pi4 USB (VSYS)
- Servo 5V isolated: physical toggle on enclosure
- RUN pin disconnected

### Iteration 3 — Three TTP223B sensors, WiFi HTTP comms
- Touch 2 (GPIO 13) and Touch 3 (GPIO 14) added
- Volume and TTS/wakeword via HTTP calls to Pi4 web API
- Capacitive sensing through 5.8mm acrylic ruled out

### Iteration 2 — Tilt removed, first button added
- Pan servo only, one TTP223B capacitive sensor (GPIO 15) for servo enable/disable toggle
- WiFi retained, RUN pin still on switch

### Iteration 1 — Initial prototype
- Pan + tilt dual servos, Person Sensor I2C, Pico W on WiFi → Pi4 HTTP
- No buttons, no centralized PCB, loose wiring, power switch on RUN pin

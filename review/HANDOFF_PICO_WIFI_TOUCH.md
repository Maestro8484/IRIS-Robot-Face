# Handoff: Pico W WiFi Touch Sensor Integration

**Date:** 2026-05-20
**From:** Claude Code session (servo-pico hardware/code work)
**To:** New Claude Code session
**Priority:** HIGH — Pico W reflashed and working, WiFi touch feature is next step

---

## Current State (as of this handoff)

### What is deployed and working
- Pico W freshly flashed (bare board, not yet reinstalled in enclosure)
- Sketch: `servo_pico/IRIS-BaseServoControlViaPerson_Sensor/IRIS-BaseServoControlViaPerson_Sensor.ino`
- Core: Earle Philhower RP2040 (rp2040 architecture) — NOT the Mbed core
- Libraries: Wire (built-in), ServoEasing (Philhower)
- Board: Raspberry Pi Pico W on COM10

### What the sketch currently does
- Pan servo (GPIO 0) tracks faces via Person Sensor I2C (GPIO 6/7)
- Confidence gate (boxConfidence ≥ 60, isFacing == true) before acting
- Dead zone (PAN_DEAD_ZONE = 2.0°) suppresses micro-jitter
- Face lost: holds position 2500ms, then drifts back to center after 8000ms
- Touch 1 (GPIO 15, physical pin 20): tap to toggle servo tracking on/off. Starts disabled at boot.
- No WiFi code yet

### Pending hardware work (HW-002 — deferred to PCB rewiring)
- RUN pin (physical 30) currently miswired to on/off switch — disconnect it, leave unconnected
- On/off switch moving to servo 5V rail (cuts servo power only, Pico keeps running)
- These are hardware-only changes, no code impact

---

## Task: Add Two New Touch Sensors + WiFi IRIS Integration

### Hardware — new touch sensors

All three TTP223B sensors grouped on physically adjacent pins:

| Physical pin | GPIO | Signal | Function |
|---|---|---|---|
| 17 | 13 | Touch 2 OUT | Volume hold-toggle (hold = increase, hold again = decrease) |
| 18 | GND | GND | Touch 2 GND |
| 19 | 14 | Touch 3 OUT | TTS interrupt OR wakeword+mic trigger |
| 20 | 15 | Touch 1 OUT | Servo enable/disable (existing) |
| 21 | GND | GND | Shared GND for Touch 1 + Touch 3 |

Power for all TTP223B sensors: 3V3 OUT (physical pin 36).

### Behavior spec

**Touch 2 — Volume (GPIO 13)**
- Hold sensor: volume increases continuously while held
- Release, then hold again: direction reverses (now decreasing)
- Release again: stops
- Direction toggle persists across holds until direction reverses again
- Rate: increment every ~200ms while held, step size TBD (suggest 5% per tick)
- Sends HTTP request to Pi4 web API on each tick

**Touch 3 — TTS interrupt / wakeword (GPIO 14)**
- Short tap: interrupt current TTS output (stop mid-speech)
- Hold (>1s): activate wakeword+mic (trigger listen cycle without speaking wakeword)
- Sends HTTP request to Pi4 on each event

### WiFi architecture

Pico W connects to local WiFi and sends HTTP POST/GET requests to Pi4 (192.168.1.200).
Pi4 web server (iris_web.py) runs on port 5000.

**Before implementing Pico W WiFi client side, verify these Pi4 endpoints exist:**

| Function | Expected endpoint | Verify in iris_web.py |
|---|---|---|
| Volume up/down | `POST /api/volume` with `{"delta": +5}` or `{"delta": -5}` | Check iris_web.py for volume route |
| TTS interrupt | `POST /api/stop` or similar | Check assistant.py for stop mechanism |
| Wakeword trigger | `POST /api/listen` or similar | Check assistant.py for manual listen trigger |

**If endpoints don't exist, they must be added to Pi4 iris_web.py / assistant.py first (Pi4 deploy required), then Pico W WiFi client side.**

### Implementation order

1. **Verify Pi4 API endpoints** — read iris_web.py and assistant.py. Do NOT assume endpoints exist.
2. **Add missing Pi4 endpoints if needed** — deploy to Pi4 per standard persist protocol.
3. **Add WiFi + touch code to Pico W sketch** — see code outline below.
4. **Flash Pico W** — board is on COM10, Philhower core, Pico W board selected. After first Philhower flash, subsequent uploads are one-click (no BOOTSEL needed).
5. **Verify behavior** — servo still tracks, volume responds, TTS interrupts cleanly.

---

## Code outline for Pico W sketch additions

Add to top of sketch:
```cpp
#include <WiFi.h>
#include <HTTPClient.h>

const char* WIFI_SSID     = "YOUR_SSID";
const char* WIFI_PASSWORD = "YOUR_PASSWORD";
const char* PI4_BASE_URL  = "http://192.168.1.200:5000";

#define TOUCH2_PIN 13   // volume hold-toggle
#define TOUCH3_PIN 14   // TTS interrupt / wakeword trigger
```

Add in setup() after existing pinMode:
```cpp
  pinMode(TOUCH2_PIN, INPUT);
  pinMode(TOUCH3_PIN, INPUT);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  // non-blocking — servo runs immediately, WiFi connects in background
  // send requests only when WiFi.status() == WL_CONNECTED
```

Touch 2 logic (volume hold-toggle) in loop():
```cpp
  static bool lastTouch2    = false;
  static bool volIncreasing = true;
  static unsigned long touch2HeldMs = 0;
  static unsigned long lastVolTickMs = 0;

  bool touch2 = digitalRead(TOUCH2_PIN);
  if (touch2 && !lastTouch2) {
    touch2HeldMs = millis();
    volIncreasing = !volIncreasing;   // reverse direction on each new hold
  }
  if (touch2 && (millis() - lastVolTickMs > 200)) {
    lastVolTickMs = millis();
    // send HTTP volume delta
    int delta = volIncreasing ? 5 : -5;
    sendVolume(delta);
  }
  lastTouch2 = touch2;
```

Touch 3 logic (TTS interrupt / wakeword) in loop():
```cpp
  static bool lastTouch3 = false;
  static unsigned long touch3PressMs = 0;

  bool touch3 = digitalRead(TOUCH3_PIN);
  if (touch3 && !lastTouch3) touch3PressMs = millis();
  if (!touch3 && lastTouch3) {
    unsigned long held = millis() - touch3PressMs;
    if (held < 1000) sendStop();        // short tap = interrupt TTS
    else             sendListen();      // long hold = trigger wakeword
  }
  lastTouch3 = touch3;
```

Helper functions (add before loop()):
```cpp
void sendVolume(int delta) {
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient http;
  http.begin(String(PI4_BASE_URL) + "/api/volume");
  http.addHeader("Content-Type", "application/json");
  http.POST("{\"delta\":" + String(delta) + "}");
  http.end();
}

void sendStop() {
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient http;
  http.begin(String(PI4_BASE_URL) + "/api/stop");
  http.POST("");
  http.end();
}

void sendListen() {
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient http;
  http.begin(String(PI4_BASE_URL) + "/api/listen");
  http.POST("");
  http.end();
}
```

**Note:** HTTP requests are synchronous and block for ~50-200ms. Monitor whether this delays servo tracking noticeably. If so, move HTTP calls to second core (RP2040 has two cores — `setup1()`/`loop1()` in Philhower).

---

## Files to touch this session

| File | Change |
|---|---|
| `servo_pico/IRIS-BaseServoControlViaPerson_Sensor/IRIS-BaseServoControlViaPerson_Sensor.ino` | Add WiFi, Touch 2, Touch 3 |
| `pi4/iris_web.py` | Add /api/volume, /api/stop, /api/listen if missing |
| `pi4/assistant.py` | Add stop/listen trigger hooks if missing |
| `docs/sysmap.json` | Add GPIO 13/14 to servo_pico gpio section |
| `IRIS_ARCH.md` | Update servo section: WiFi, 3 touch sensors |
| `SNAPSHOT_LATEST.md` | Update Servo Pico status |

---

## Credentials / network
- Pi4: 192.168.1.200, port 5000 (iris_web.py)
- WiFi SSID/password: user to supply — do not hardcode in repo, use a `#define` at top of sketch with a note to fill in before flash, or read from a config file on flash storage
- SSH to Pi4: password auth only (pi/ohs) — key auth does not work on this setup

---

## Do not touch
- Teensy 4.1 firmware (separate system, unrelated)
- GandalfAI models
- Pi4 assistant.py sleep/wake/TTS pipeline beyond the stop/listen hooks
- `iris_config.json` unless explicitly required

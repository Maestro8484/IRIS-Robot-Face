# IRIS Snapshot

**Session:** S56 | **Date:** 2026-05-21 | **Branch:** `main` | **Last commit:** `af66b24` — servo-pico: Pico W I2C fix, APDS-9960 gesture replaces buttons

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## Machine Status

| System | Status |
|---|---|
| SuperMaster Desktop | Canonical repo — 2 commits ahead of origin. Claude Desktop, filesystem MCP, SSH MCP active. |
| Pi4 192.168.1.200 | Operational (S54 state). RD-009 Pi4 changes REPO-ONLY — assistant.py (pico_listener thread), iris_web.py (/api/stop, /api/listen), wakeword.py (manual listen flag). **Deploy pending after hardware rewiring.** |
| GandalfAI 192.168.1.3 | Operational. iris + iris-kids models current (S48 PT-001). |
| Teensy 4.1 | Firmware REPO-ONLY (`4e7c61b`). BL_MAP log curve + idle animations built, **flash pending** (PlatformIO upload). |
| Servo Controller | REPO-ONLY — **Pico W dead (hardware failure, no USB enumeration).** Replaced with Teensy 4.0 (COM11). Firmware updated: Wire.begin() fixed pins 18/19, panServo.attach(9). platformio.ini → teensy40. Flash pending. |
| TTS | Kokoro primary (Docker port 8004), Piper fallback (Wyoming port 10200). |
| Web UI | Operational. S53 DEPLOYED. md5 iris_web.py `5fc8b075`, iris_web.html `7d3a63f6`. |

---

## Active Issues

- **HIGH: HW-001 — Teensy 4.1 LED** — Pin 13 = SPI SCK for eye displays; LED glows solid during operation. Fix: cut solder jumper on Teensy underside. Blocked on power distribution PCB rewiring (Teensy header-soldered to PCB). See ROADMAP HW-001.
- **HIGH: HW-002 — Full enclosure rewiring in progress** — All hardware being rewired before next power-on. RUN pin: disconnect (leave floating). On/off switch: move to servo 5V rail. Momentary buttons (GPIO 13/14/15): wire active-low to GND. See docs/servo_pico_wiring.md for full pin map.
- **HIGH: Teensy firmware flash pending** — S54 firmware built and committed but not flashed. BL_MAP curve + idle animations inactive until PlatformIO upload.
- **MED: Perceived latency** — Bench JSONL live (S50). Pending: OLLAMA_KEEP_ALIVE=30m on GandalfAI.
- **LOW: "stop" Whisper hallucination** — post-STT gate deployed (RD-001). Residual edge cases remain.
- **LOW: Duplicate sleep log** — /home/pi/iris_sleep.log may duplicate /home/pi/logs/iris_sleep.log (RD-003).

---

## Session Scope

S55: RD-009 — Pico W USB serial touch integration. WiFi removed, momentary buttons replace TTP223B, pico_listener thread added to assistant.py. Session closed pending full hardware rewiring.

---

## Last Session Changes (S55)

- **`servo_pico/.../IRIS-BaseServoControlViaPerson_Sensor.ino`** — WiFi/HTTP stripped entirely. USB CDC serial replaces all Pi4 comms (VOL_UP, VOL_DOWN, STOP, LISTEN). TTP223B → momentary pushbuttons: INPUT_PULLUP, !digitalRead(). servoEnabled variable and Touch 1 toggle logic removed (physical switch handles servo power). Touch 1 (GPIO 15) reserved in firmware.
- **`pi4/assistant.py`** — `start_pico_listener()` daemon thread added. Reads /dev/ttyACM1 at 9600 baud. Dispatches: VOL_UP/DOWN → set_volume(), STOP → _stop_playback.set(), LISTEN → /tmp/iris_manual_listen.
- **`pi4/iris_web.py`** — `/api/stop` (STOP_PLAYBACK via UDP) and `/api/listen` (writes /tmp/iris_manual_listen) routes added.
- **`pi4/services/wakeword.py`** — /tmp/iris_manual_listen flag check in wait loop; treats as button trigger.
- **`docs/servo_pico_wiring.md`** — Full pin map, power distribution, button wiring, iteration 4 design history.
- **`docs/servo_pico_wiring_onenote.html`** — OneNote-ready browser-paste version of wiring tables.

## Previous Session Changes (S54)

- `src/mouth_tft.cpp` — BL_MAP log curve, idle animation engine (6 anims).
- `src/main.cpp` — IDLE_AUTO_MS=120s, mouthIdleTick() in loop.
- `pi4/core/config.py` — MOUTH_INTENSITY_IDLE=3. Pi4 DEPLOYED+VERIFIED.

---

## Known TODO

- **BLOCKED: Full enclosure hardware rewiring in progress** — do not power on until complete. See docs/servo_pico_wiring.md.
- After rewiring: flash Pico W (Arduino IDE, Philhower core, COM10), plug into Pi4 USB, verify /dev/ttyACM1, deploy assistant.py, test buttons.
- Flash Teensy firmware (PlatformIO upload). Verify: sleep=dark, idle=dim L3, wakeword=bright, post-speech=dim.
- HW-001: cut LED solder jumper on Teensy underside during PCB rewiring.
- OLLAMA_KEEP_ALIVE=30m on GandalfAI.
- PT-001: live adversarial verification.
- RD-007: Bench trend viewer (needs ~1 week bench data first).

---

## Do Not Touch Without Explicit Instruction

- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

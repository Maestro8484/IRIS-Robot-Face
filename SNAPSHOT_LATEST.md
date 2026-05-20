# IRIS Snapshot

**Session:** S54 | **Date:** 2026-05-19 | **Branch:** `main` | **Last commit:** `af6167c` — S54: remove LED stub, defer HW-001

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## Machine Status

| System | Status |
|---|---|
| SuperMaster Desktop | Canonical repo — pushed `af6167c`. Claude Desktop, filesystem MCP, SSH MCP active. |
| Pi4 192.168.1.200 | Operational. S54(D) DEPLOYED: assistant.py + config.py (MOUTH_INTENSITY_IDLE=3). md5 verified, SD persisted, assistant running. |
| GandalfAI 192.168.1.3 | Operational. iris + iris-kids models current (S48 PT-001). |
| Teensy 4.1 | Firmware REPO-ONLY (`4e7c61b`). BL_MAP log curve + idle animations built, **flash pending** (PlatformIO upload). |
| Servo Pico | REPO-ONLY — `c37f148` servo improvements committed (confidence gate, dead zone, face-lost return). **Flash blocked by HW-002** (BOOTSEL inaccessible, RUN miswired to switch). Tracking functional on old firmware. |
| TTS | Kokoro primary (Docker port 8004), Piper fallback (Wyoming port 10200). |
| Web UI | Operational. S53 DEPLOYED. md5 iris_web.py `5fc8b075`, iris_web.html `7d3a63f6`. |

---

## Active Issues

- **HIGH: HW-001 — Teensy 4.1 LED** — Pin 13 = SPI SCK for eye displays; LED glows solid during operation. Fix: cut solder jumper on Teensy underside. Blocked on power distribution PCB rewiring (Teensy header-soldered to PCB). See ROADMAP HW-001.
- **HIGH: HW-002 — Servo Pico flash blocked** — BOOTSEL button inaccessible (Pico header-soldered to PCB). RUN pin miswired to enclosure on/off switch (pulls RUN low when ON = hard reset). Improved servo code REPO-ONLY. Fix during PCB rewiring: move switch to VSYS line, leave RUN unconnected, install WinUSB driver via Zadig, flash `servo_pico/IRIS-BaseServoControlViaPerson_Sensor.ino`. See ROADMAP HW-002.
- **HIGH: Teensy firmware flash pending** — S54 firmware built and committed but not flashed. BL_MAP curve + idle animations inactive until PlatformIO upload.
- **MED: Perceived latency** — Bench JSONL live (S50). Pending: OLLAMA_KEEP_ALIVE=30m on GandalfAI.
- **LOW: "stop" Whisper hallucination** — post-STT gate deployed (RD-001). Residual edge cases remain.
- **LOW: Duplicate sleep log** — /home/pi/iris_sleep.log may duplicate /home/pi/logs/iris_sleep.log (RD-003).

---

## Session Scope

S54: RD-008 mouth TFT overhaul — BL log curve (A), color confirm (B), idle animations (C), Pi4 idle dimming (D). LED pin13 stub added then removed; deferred as HW-001.

---

## Last Session Changes (S54)

- **`src/mouth_tft.cpp`** — `BL_MAP[16]` log curve replaces `level*17` linear map. `_currentBLLevel` + `_currentMouthIdx` state tracking. `MTFT_AMBER=0xFD20` constant. Idle engine: 6 anims (BREATHE/DRIFT/TWITCH/BLINK/YAWN/SIDESMIRK), millis-based, interruptible via `mouthIdleStop()`.
- **`src/mouth_tft.h`** — `mouthIdleStart/Stop/Tick/IsActive` declarations.
- **`src/main.cpp`** — `lastCommandMs` + `IDLE_AUTO_MS=120s`. `mouthIdleStop()` on all MOUTH/EMOTION/EYES commands. `IDLE:START`/`IDLE:STOP` serial handlers. `mouthIdleTick()` in non-sleep loop. LED stub added then removed (HW-001).
- **`pi4/core/config.py`** — `MOUTH_INTENSITY_IDLE=3`, registered in `_OVERRIDABLE` + `_TYPE_COERCE`.
- **`pi4/assistant.py`** — Wakeword → `MOUTH_INTENSITY_AWAKE` before STT. End of LLM+TTS+followup → `MOUTH_INTENSITY_IDLE`.
- Pi4 md5 verified (`config` `535d62b3`, `assistant` `259dd0a1`). Persisted. Service running.
- Sub-task B (colors): already implemented in prior session — confirmed correct, no changes needed.

## Previous Session Changes (S53)

- Bench tab: 20-cycle history, To First Word column, expanded headers, full trigger name, color coding.
- DEPLOYED. md5 iris_web.py `5fc8b075`, iris_web.html `7d3a63f6`.

---

## Known TODO

- Flash Teensy firmware (PlatformIO upload). Verify: sleep=dark, idle=dim L3, wakeword=bright, post-speech=dim.
- HW-001: cut LED solder jumper during PCB rewiring.
- HW-002: move Pico RUN switch wire to VSYS, install Zadig WinUSB driver, flash servo_pico code.
- OLLAMA_KEEP_ALIVE=30m on GandalfAI.
- PT-001: live adversarial verification.
- RD-007: Bench trend viewer (needs ~1 week bench data first).

---

## Do Not Touch Without Explicit Instruction

- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

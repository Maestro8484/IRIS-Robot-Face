# IRIS Architecture Reference

> Architecture, pins, constants, deploy commands, and system ownership reference.
> Load on demand. Do not duplicate every detail into snapshots.

---

## Documentation Purpose

IRIS documentation is an AI-readable operational control layer.

These files are written not only for human reference, but to enable trusted AI agents to safely inspect, modify, deploy, and validate changes across multiple systems:

- SuperMaster Windows desktop
- Raspberry Pi 4 runtime node
- GandalfAI inference workstation
- Teensy 4.1 firmware target
- GitHub remote mirror

Documentation must prioritize clarity, execution accuracy, environment awareness, and safe automation over narrative style.

---

## Authority Model

Canonical source of truth:
`C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face`

This is the local repository on SuperMaster desktop.

GitHub is a secondary mirror and backup. It may lag local state until explicitly committed and pushed.

Operational priority:
1. Local repo files on SuperMaster
2. Local git state on SuperMaster
3. Live system checks on Pi4 / GandalfAI / Teensy
4. GitHub remote after fetch/compare

---

## Engineering Governance - MAD Loop

MAD Loop = Multi-Agent Adversarial Dev Loop.

IRIS uses a human-governed multi-agent engineering workflow where multiple AI systems independently analyze, critique, and refine changes before deployment.

Purpose:
- Reduce regression risk
- Catch false assumptions
- Improve reliability
- Safely manage a distributed system spanning Pi4, GandalfAI, Teensy 4.1, and overlayfs constraints

Standard Flow:
1. Claude Chat planning review
2. ChatGPT independent critique
3. Optional Codex repo-wide audit
4. Consolidated implementation scope
5. Claude Code execution
6. Human hardware validation
7. Documentation update

Final authority belongs to the human operator.

---

## System Roles

| System | Role |
|---|---|
| SuperMaster Desktop | Command/control node, Claude Desktop, local repo, VS Code, PlatformIO, git |
| Pi4 | Voice pipeline orchestration, wakeword, mic/audio, LEDs, camera, web UI, cron sleep/wake, Teensy serial bridge |
| GandalfAI | Ollama LLM, Modelfiles, Whisper STT, Kokoro TTS (primary), Piper TTS (fallback), Chatterbox (rollback only), RTX 3090 inference |
| Teensy 4.1 (display controller) | Embedded controller for eyes, mouth, sleep renderer, person sensor integration, serial protocol |
| Teensy 4.0 (base mount controller) | Pan servo: runs autonomously from Person Sensor face data (ServoEasing). PAJ7620U2 gesture sensor (I2C 0x73, replaces dead APDS-9960 S66, polling reg 0x43). USB-CDC serial to Pi4 /dev/ttyIRIS_SERVO, one-way (Teensy→Pi4: VOL+/VOL-/STOP/LISTEN; Pi4 sends nothing). Physical power toggle on enclosure rear. Firmware: servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino (modular: paj7620.*, person_sensor.*, pan_servo.*, diag.h). |
| Servo Controller (ESP32 DevKit 1C) | TOMBSTONED — replaced by Teensy 4.0 base mount controller |
| GitHub | Secondary mirror, backup, version history, sharing remote |

---

## Active Architecture Principle

All heavy AI compute runs on GandalfAI.
Pi4 remains the orchestrator and hardware-facing runtime node.
Teensy 4.1 remains the embedded display controller.
SuperMaster remains the source/control workstation.

---

## Current High-Level Pipeline

Wakeword / button:
Pi4 OpenWakeWord or GPIO button

STT:
Pi4 sends recorded audio to Wyoming Whisper on GandalfAI

LLM:
Pi4 streams prompt/context to Ollama on GandalfAI (`stream_ollama`, stream=True).
Tokens are buffered and split on sentence boundaries (.!?); the leading
`[EMOTION:X]` tag is extracted from the first tokens, then each complete sentence
is yielded cleaned (`clean_llm_reply`) and ready for TTS.

TTS (streaming, S116):
For each sentence chunk as it arrives, Pi4 requests Kokoro TTS (primary) or Piper
fallback on GandalfAI and enqueues the PCM. TTS for sentence N+1 overlaps playback
of sentence N. (Per-sentence dispatch also avoids feeding Kokoro one huge multi-
minute input on long replies.)

Playback (streaming, S116):
A background player (`play_pcm_stream` in `hardware/audio_io.py`) pulls PCM blobs
from the queue and plays them back-to-back through wm8960 — first audio begins on
the first sentence while later sentences are still generating. One `EYES:SPEAKING`
setup, one continuous mouth animation, and one interrupt listener span the whole
utterance. STOP is honored per sentence dispatch and per playback slice; the
emotion tag still drives the face on the first chunk. The blocking single-call
path (`play_pcm_speaking`) is retained for quips, RPQR, reflex/utility/command/
vision replies, and the follow-up loop.

Face:
Pi4 sends serial commands to Teensy 4.1 through single-owner TeensyBridge

---

## Pi4 Overlayfs Deployment Principle

Pi4 uses overlayfs. Writes to `/home/pi` go to RAM layer unless persisted.

Use direct `/media/root-ro` remount method only:

```bash
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/<file> /media/root-ro/home/pi/<file>
sudo chown pi:pi /media/root-ro/home/pi/<file>
sudo chmod 644 /media/root-ro/home/pi/<file>
sync
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/<file> /media/root-ro/home/pi/<file>
```

Do not use `overlayroot-chroot` unless independently verified.

Reason:
During Batch 1A, `overlayroot-chroot cp` produced an MD5 mismatch because source and destination resolved to the same effective path. Direct `/media/root-ro` remount method is the current verified persistence path.

---

## USB Device Identity — udev Rules

Teensy devices are identified by hardware USB serial number, not port position.

| Symlink | Serial | Device |
|---|---|---|
| `/dev/ttyIRIS_EYES` | `13625440` | Teensy 4.1 (eyes + TFT mouth) |
| `/dev/ttyIRIS_SERVO` | `12763490` | Teensy 4.0 (servo + gesture) |

Rules file: `/etc/udev/rules.d/99-iris-teensy.rules` (repo: `pi4/scripts/99-iris-teensy.rules`)
Reload: `sudo udevadm control --reload-rules && sudo udevadm trigger`
Get serial for new device: `udevadm info -a -n /dev/ttyACMx | grep 'ATTRS{serial}'`

**HARD RULE: Never hardcode `/dev/ttyACM*` in code, config, or commands. Always use `/dev/ttyIRIS_EYES` or `/dev/ttyIRIS_SERVO`.** ttyACM assignments are port-position-based and change when USB ports are swapped (confirmed failure S63).

---

## Serial Ownership Rule

Only `hardware/teensy_bridge.py` owns `/dev/ttyIRIS_EYES`.

Everything else must communicate through:
UDP -> `127.0.0.1:10500` -> assistant command listener -> TeensyBridge

Do not open Teensy serial from web routes, cron scripts, or helper scripts.

CMD listener auto-wake (S63): if `state.eyes_sleeping` is True and an EMOTION:, EYE:, or MOUTH: command arrives via UDP, `_do_wake()` is called before forwarding the command. This prevents display commands from silently failing while eyes are sleeping.

---

## Current Batch Roadmap

### Batch 1A - Complete
Wakeword runtime survival and anti-hang hardening.

### Batch 1B - Complete
Sleep/wake authority unification.

### Batch 1C - Complete
Reliability hygiene (all items closed):
- SPEAKER_VOLUME persistence — done via web UI + alsactl store
- TTS hard-cap at sentence boundary
- Config validation/coercion for iris_config.json
- Safe temp files (mkstemp)
- LLM stream warning (rate-limited)
- Dynamic response-length classification: SHORT/MEDIUM/LONG/MAX tiers
- Sleep greeting via Piper routing — deferred (LOW-LOW priority; Kokoro is primary)

### Batch 2
Teensy hardware/firmware hardening.

### Batch 3
GandalfAI personality/pipeline/model behavior.

---

## Documentation Layering

| File | Purpose |
|---|---|
| `HANDOFF_CURRENT.md` | Current truth, roadmap, session startup state |
| `CLAUDE.md` | Agent operating rules and deployment rules |
| `SNAPSHOT_LATEST.md` | Current machine status, active issues, immediate handoff |
| `IRIS_ARCH.md` | System architecture, ownership, deployment principles |
| `AGENTS.md` | Codex and general agent rules |

---

## System Status - Active Issues

| Item | Status | Notes |
|---|---|---|
| Wake word (hey_jarvis) | **WORKING** - confirmed S23 2026-04-18 | OWW score=1.000, full pipeline fires |
| Mic capture (wm8960 LINPUT1) | **WORKING** - confirmed S23 | Input boost switches required; now in alsa-init.sh |
| STT -> LLM -> TTS -> audio output | **WORKING** - confirmed S23 | Full pipeline: Whisper->Ollama iris->Kokoro->speakers |
| Mouth TFT animation | **WORKING** - confirmed S29 | MOUTH:0-8 cycling during speech. BL on GPIO 5, web UI intensity control working. |
| Sleep/wake cron (9PM/7:30AM) | Working but **REBOOT-FRAGILE** | Piper missing at /usr/local/bin/piper - sleep wakeword says nothing |
| ALSA state on reboot | **HARDENED S23** | alsa-init.sh now sets all 6 critical switches explicitly |
| GandalfAI reboot | **FRAGILE** | Kokoro docker must be started manually after reboot (`docker compose up -d`) |
| Teensy flash (mouthSleepFrame) | **DONE** - confirmed by user, S27 | Firmware live on /dev/ttyIRIS_EYES (was /dev/ttyACM0 pre-S63 udev rules) |
| Mouth smoke test | **DONE** - confirmed by user, S27 | MOUTH:0-8 via UDP 127.0.0.1:10500 confirmed |

### Reboot survival checklist
On Pi4 reboot: alsa-init.sh runs automatically (hardened S23) - mic + speakers restore without manual intervention.
On GandalfAI reboot: run `docker compose -f C:\IRIS\docker\docker-compose.yml up -d` manually - Kokoro does not auto-start.
On both rebooting simultaneously: GandalfAI must be up before assistant.py finishes boot or it will WoL-wait.

---

## System Architecture

| System | IP | Credentials | Role |
|---|---|---|---|
| Pi4 (IRIS) | 192.168.1.200 | pi / &lt;password&gt; | Voice pipeline, LEDs, camera, Teensy serial |
| GandalfAI | 192.168.1.3 | gandalf / &lt;password&gt; | Ollama LLM, Whisper STT, Piper TTS, Kokoro TTS, RTX 3090 |
| Desktop PC | 192.168.1.103 | SuperMaster / &lt;password&gt; | PlatformIO firmware, VS Code, Claude Desktop. OpenSSH server enabled S29 - Claude can ssh_exec PowerShell commands and run git directly. |
| Teensy 4.1 | USB -> Desktop PC | N/A | Dual GC9A01A 1.28" round TFT eyes + ILI9341 2.8" TFT mouth |
| Teensy 4.0 | USB -> Pi4 (/dev/ttyIRIS_SERVO) | N/A | Base mount controller: pan servo (ServoEasing, autonomous), Person Sensor (0x62), PAJ7620U2 gesture sensor (0x73, I2C, replaces dead APDS-9960 S66). Physical power toggle on enclosure rear. |
| Synology NAS | 192.168.1.102 | Master / &lt;password&gt; | SSH port 2233. Backup: \\192.168.1.102\BACKUPS\IRIS-Robot-Face\ |

**SSH MCP tools:** `ssh-pi4` (192.168.1.200), `ssh-gandalf` (192.168.1.3), `ssh` (SuperMaster 192.168.1.103, PowerShell). NAS SSH: port 2233 - connect via ssh MCP with explicit host override. Credentials in CLAUDE.md (user-level, not committed).
**SSH auth Pi4:** Password auth only - key auth fails.
**SSH auth GandalfAI:** see CLAUDE.md
**GandalfAI:** Windows machine. No `df`, `head`, `grep` - use PowerShell / findstr / dir equivalents.
**GandalfAI MCP scope:** filesystem MCP only covers `C:\Users\gandalf\`. All `C:\IRIS\`, `C:\docker\` via SSH sftp_write or ssh_exec.

---

## GandalfAI File Layout

```
C:\IRIS\
  docker\
    docker-compose.yml          -- iris stack (pipeline: whisper, piper, kokoro)
    docker-compose.gandalf.yml  -- gandalf stack (utility: open-webui, watchtower)
    whisper\                    -- whisper model cache
    piper\                      -- piper data
  chatterbox\
    config.yaml                 -- last_chunk_size: 300
    reference_audio\iris_voice.wav
    voices\
    model_cache\
  backup\
    docker-compose.yml.bak
```

Ollama modelfiles (canonical in repo):
- `ollama/iris_modelfile.txt` - adult IRIS persona (mistral-small3.2:24b)
- `ollama/iris-kids_modelfile.txt` - kids IRIS persona (mistral-small3.2:24b)

HF cache: `C:\Users\gandalf\.cache\huggingface` - stays in user profile, intentionally not moved.

---

## Teensy 4.1 Pin Assignment

### Eye displays (GC9A01A, config.h)

| GPIO | Signal | Device | Bus |
|---|---|---|---|
| 0 | CS | Left eye | SPI1 |
| 2 | DC | Left eye | SPI1 |
| 3 | RST | Left eye | SPI1 |
| 26 | MOSI | Left eye | SPI1 hw |
| 27 | SCK | Left eye | SPI1 hw |
| 10 | CS | Right eye | SPI0 |
| 9 | DC | Right eye | SPI0 |
| - | RST | Right eye | -1 (no pin) |
| 11 | MOSI | Right eye | SPI0 hw |
| 13 | SCK | Right eye | SPI0 hw |

### Person Sensor I2C - mounted RIGHT-SIDE-UP

| GPIO | Signal |
|---|---|
| 18 | SDA |
| 19 | SCL |

### ILI9341 TFT Mouth (hardware SPI2)

| GPIO | Signal | Notes |
|---|---|---|
| 35 | MOSI | SPI2 hw |
| 37 | SCK | SPI2 hw |
| 36 | CS | - |
| 8 | DC | - |
| 4 | RST | - |
| 5 | BL | PWM: 220 boot/wake, 8 sleep - reassigned S29 from GPIO 14 |

> Free pins: 6, 7, 15-17, 20-25, 28-33, 38-55 (T4.1 extended)
> Pins 6/7 were legacy MAX7219 matrix (removed hardware). Now free.
> GPIO 5 now assigned to ILI9341 BL.
> GPIO 3 RST Dupont female recrimped S29 after wire snip during enclosure work.
> Teensy is enclosure-mounted. RESET and PROG buttons are NOT accessible. All resets via software bootloader entry only.

---

## Teensy 4.0 Pin Assignment — Base Mount Controller

**Firmware:** `servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`
**Wiring reference:** `docs/servo_teensy40_wiring.md` — complete pin-to-wire map with wire colors, I2C device addresses, power distribution.
**Library:** ServoEasing (pan servo smooth motion control)
**Autonomy:** Pan servo runs autonomously from Person Sensor face detection — Pi4 sends no commands to this board.
**Serial direction:** One-way Teensy→Pi4 only. Teensy sends VOL+/VOL-/STOP/LISTEN/FORWARD/BACKWARD/CW/CCW on PAJ7620U2 gesture events. Pi4 handler: `pi4/hardware/base_mount_bridge.py`. Only `base_mount_bridge.py` owns `/dev/ttyIRIS_SERVO`.
**Power toggle:** Physical switch on enclosure rear controls servo 5V rail. Pi4 USB power is unaffected.

Connected: USB to Pi4 (`/dev/ttyIRIS_SERVO` — separate from Teensy 4.1 on `/dev/ttyIRIS_EYES`)
Powered: Pi4 USB port

| GPIO | Signal | Device | Notes |
|---|---|---|---|
| 2  | Pan servo PWM | Miuzei DS3218MG MS24 Digital Servo | `panServo.attach(2)`, external 5V rail, shared I2C bus with Person Sensor |
| 18 | SDA (Wire default) | Person Sensor 0x62 + PAJ7620U2 0x73 | Shared I2C bus, external 4.7K pullups |
| 19 | SCL (Wire default) | Person Sensor 0x62 + PAJ7620U2 0x73 | Shared I2C bus, external 4.7K pullups |

I2C pullups: 4.7K resistor SDA→3.3V, 4.7K resistor SCL→3.3V (external, required)
Servo power: external 5V supply, physical toggle switch on enclosure
Sensors: 3.3V from Teensy 3.3V pin

USB Serial commands (Teensy 4.0 → Pi4):

| Command | Trigger | Default Pi4 action |
|---|---|---|
| `VOL+` | PAJ7620U2 swipe UP (physical) | volume up |
| `VOL-` | PAJ7620U2 swipe DOWN (physical) | volume down |
| `STOP` | PAJ7620U2 swipe LEFT or RIGHT | UDP STOP to 127.0.0.1:10500 |
| `LISTEN` | gesture action (configurable, e.g. FORWARD) / web UI | activate listen mode |
| `FORWARD` | PAJ7620U2 push toward sensor | LISTEN (configurable via web UI) |
| `BACKWARD` | PAJ7620U2 pull away from sensor | SLEEP (configurable via web UI) |
| `CW` | PAJ7620U2 clockwise wrist rotation | VOL+ (configurable via web UI) |
| `CCW` | PAJ7620U2 counter-clockwise rotation | VOL- (configurable via web UI) |

Actions: VOL+, VOL-, STOP, LISTEN, SLEEP, WAKE, MUTE, SKIP — configurable per gesture in IRIS Control Panel → Gestures tab.

---

### PAJ7620U2 Gesture Sensor Quick-Reference

**I2C address:** `0x73`  **Init:** bank 0 (29 writes) + bank 1 (20 writes), 700 µs wakeup settle required before config writes  **Polling:** Register Bank 0, `0x43` (IntFlag_1) — read each loop, clear on read

#### Register 0x43 — IntFlag_1 raw bit layout (datasheet v1.5 p.24)

| Bit | Mask | Gesture |
|---|---|---|
| 0 | 0x01 | Left |
| 1 | 0x02 | Right |
| 2 | 0x04 | Down |
| 3 | 0x08 | Up |
| 4 | 0x10 | Forward |
| 5 | 0x20 | Backward |
| 6 | 0x40 | Clockwise |
| 7 | 0x80 | Counter-Clockwise |

#### Mount orientation remapping (`GESTURE_MOUNT_DEGREES` define in firmware)

Physical gesture direction depends on how the sensor is mounted. Change `#define GESTURE_MOUNT_DEGREES` to one of `0 / 90 / 180 / 270`. A `#error` fires at compile time for any other value.

| Mount rotation | Phys UP | Phys DOWN | Phys LEFT | Phys RIGHT |
|---|---|---|---|---|
| 0° (label up, standard) | 0x08 | 0x04 | 0x01 | 0x02 |
| 90° CW | 0x02 | 0x01 | 0x08 | 0x04 |
| 180° (upside-down) | 0x04 | 0x08 | 0x02 | 0x01 |
| 270° CW / 90° CCW | 0x01 | 0x02 | 0x04 | 0x08 |

**Current install:** `GESTURE_MOUNT_DEGREES 270` (sensor rotated 90° CCW relative to viewer)

**Sensor axis → command mapping (all orientations):**
- Physical UP → `VOL+`
- Physical DOWN → `VOL-`
- Physical LEFT → `STOP`
- Physical RIGHT → `STOP`
- FORWARD (push toward sensor) → `FORWARD` (default action: LISTEN)
- BACKWARD (pull away from sensor) → `BACKWARD` (default action: SLEEP)
- CW (clockwise rotation) → `CW` (default action: VOL+)
- CCW (counter-clockwise rotation) → `CCW` (default action: VOL-)

All 8 gesture command strings are dispatched via `base_mount_bridge.py`. Actions are configurable per-gesture in `iris_config.json` GESTURE_MAP (web UI: Gestures tab).

**INT pin:** Not connected — firmware uses polling mode only. INT wiring not required.

---

## Repo Structure

```
IRIS-Robot-Face/
  src/
    main.cpp                    -- serial parsing, emotion/tracking/sleep logic
    config.h                    -- eye definitions array (7 eyes), display pins
    sleep_renderer.h            -- deep space starfield (SR_FRAME_MS=155)
    displays/GC9A01A_Display.h  -- display driver
    eyes/EyeController.h        -- eye movement/blink/pupil (setTargetPosition seed fix intact)
    eyes/240x240/               -- nordicBlue/flame/hypnoRed/hazel/blueFlame1/dragon/bigBlue .h
    sensors/PersonSensor.h/.cpp -- I2C face detection (SAMPLE_TIME_MS=70, conf>60, is_facing)
    mouth_tft.cpp/.h            -- ILI9341 TFT mouth driver (KurtE/ILI9341_t3n, SPI2)
  pi4/                          -- mirrors /home/pi/ on Pi4
    assistant.py                -- THIN orchestrator (~340 lines)
    services/tts.py             -- Kokoro->Piper routing (Chatterbox rollback only; ElevenLabs removed S20)
    services/stt.py             -- Wyoming Whisper STT (data_length payload parser)
    services/vision.py          -- camera capture + vision query
    services/llm.py             -- stream_ollama(), ask_ollama(), emotion extraction, reply cleaning
    services/wakeword.py        -- OWW + GPIO button handler
    hardware/audio_io.py        -- PCM playback, record, beep, interrupt detection
    hardware/led.py             -- APA102 driver
    hardware/teensy_bridge.py   -- single serial owner of /dev/ttyIRIS_EYES
    hardware/io.py              -- GPIO helpers
    state/state_manager.py      -- StateManager: conversation_history, kids_mode, eyes_sleeping
    core/config.py              -- all constants; iris_config.json override loader
    iris_web.py                 -- Flask web panel (serves iris_web.html fresh per-request)
    iris_web.html               -- Web UI (ElevenLabs removed S18, MAX7219/matrix refs removed S21)
    iris_sleep.py               -- cron sleep script
    iris_wake.py                -- cron wake script
  servo_teensy40/
    teensy40_base_mount/
      teensy40_base_mount.ino   -- orchestration: setup/loop (modules: paj7620.*, person_sensor.*, pan_servo.*, diag.h)
      platformio.ini            -- env:t40, board teensy40, monitor_speed 115200
  ollama/
    iris_modelfile.txt          -- adult IRIS persona (mistral-small3.2:24b) -- canonical
    iris-kids_modelfile.txt     -- kids IRIS persona (mistral-small3.2:24b) -- canonical
```

---

## PlatformIO

```ini
[env:eyes]
platform = https://github.com/platformio/platform-teensy.git
board = teensy41
framework = arduino
monitor_speed = 115200
build_flags = -std=gnu++17 -O2 -D TEENSY_OPT_SMALLEST_CODE
lib_deps =
  https://github.com/PaulStoffregen/Wire
  https://github.com/PaulStoffregen/ST7735_t3
  https://github.com/mjs513/GC9A01A_t3n
  KurtE/ILI9341_t3n
```

---

## Eye Index Map

```
0 = nordicBlue  (default idle)
1 = flame       (ANGRY)
2 = hypnoRed    (CONFUSED)
3 = hazel
4 = blueFlame1
5 = dragon
6 = bigBlue
```

### Pupil values - re-apply manually after every genall.py run

| Eye | pupil.min | pupil.max |
|---|---|---|
| nordicBlue | 0.21 | 0.47 |
| hazel | 0.25 | 0.47 |
| bigBlue | 0.24 | 0.50 |
| hypnoRed | 0.25 | 0.50 |

---

## Key Constants

### core/config.py (as of TS40-S1 — TTS stack changed from Chatterbox to Kokoro primary at S38)

```python
WHISPER_PORT           = 10300
PIPER_PORT             = 10200
OLLAMA_PORT            = 11434
OWW_PORT               = 10400
CMD_PORT               = 10500
OLLAMA_MODEL_ADULT      = "iris"
OLLAMA_MODEL_KIDS       = "iris-kids"
VISION_MODEL            = "iris"
OWW_THRESHOLD           = 0.90
KOKORO_BASE_URL         = "http://192.168.1.3:8004"
KOKORO_VOICE            = "bm_lewis"
KOKORO_ENABLED          = True
KOKORO_SPEED            = 1.0
CHATTERBOX_BASE_URL     = "http://192.168.1.3:8004"
CHATTERBOX_VOICE        = "iris_voice.wav"
CHATTERBOX_EXAGGERATION = 0.45
CHATTERBOX_ENABLED      = True     # rollback only; Kokoro is primary
TEENSY_PORT             = "/dev/ttyIRIS_EYES"
BASE_MOUNT_PORT         = "/dev/ttyIRIS_SERVO"
GESTURE_SENSOR_REQUIRED = False    # flip after PAJ7620U2 replacement is verified
NUM_PREDICT             = 300      # legacy fallback; tier values below are primary
NUM_PREDICT_SHORT       = 120
NUM_PREDICT_MEDIUM      = 350
NUM_PREDICT_LONG        = 700
NUM_PREDICT_MAX         = 1200
LED_SLEEP_PEAK          = 26
LED_SLEEP_FLOOR         = 3
LED_SLEEP_PERIOD        = 8.0
LED_SLEEP_BRIGHT        = 0xFF
```

### iris_config.json on Pi4

Protected live override file. Keys override `core/config.py` only if listed in `_OVERRIDABLE`; unknown keys are silently ignored. `NUM_PREDICT` is legacy fallback only. `ELEVENLABS_ENABLED` was removed in S20 — if present it is ignored and safe to delete.

### src/main.cpp key constants

```
FACE_LOST_TIMEOUT_MS=5000 | FACE_COOLDOWN_MS=30000
ANGRY_EYE_DURATION_MS=9000 | CONFUSED_EYE_DURATION_MS=7000
EYE_IDX_DEFAULT=0, ANGRY=1, CONFUSED=2, COUNT=7
```

### Ollama models (as of S119b)

- `iris:latest` - mistral-small3.2:24b, num_predict 800, temperature 0.75, num_ctx 6144
- `iris-kids:latest` - mistral-small3.2:24b, num_predict 800, temperature 0.75, num_ctx 6144
- Stop tokens: `[INST]`, `[/INST]`, `</s>`, `User:` (Mistral/few-shot bleed protection)
- VRAM: Kokoro ~2GB + mistral-small3.2:24b ~15GB = ~17GB total. Headroom ~7GB on RTX 3090 (24GB). 100% GPU.
- GandalfAI env required: `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0` (set S39, machine-level).

---

## Cron Entries (Pi4 user crontab)

```
0 21 * * * ALSA_CARD=seeed2micvoicec /usr/bin/python3 /home/pi/iris_sleep.py >> /home/pi/logs/iris_sleep.log 2>&1
30 7 * * * ALSA_CARD=seeed2micvoicec /usr/bin/python3 /home/pi/iris_wake.py >> /home/pi/logs/iris_wake.log 2>&1
0 3 * * 0 sudo /bin/bash /home/pi/iris_backup.sh
```

---

## Serial Protocol

**Pi4 -> Teensy:**
```
EMOTION:NEUTRAL/HAPPY/CURIOUS/ANGRY/SLEEPY/SURPRISED/SAD/CONFUSED
EYES:SLEEP / EYES:WAKE
EYE:n              -- switch default eye (0-6)
MOUTH:x            -- set mouth expression (0-8)
MOUTH_INTENSITY:n  -- set backlight level (0-15)
```

**Teensy 4.1 -> Pi4:** `FACE:1` / `FACE:0`
**Rule:** Only TeensyBridge owns `/dev/ttyIRIS_EYES`. Everything else uses UDP -> `127.0.0.1:10500`. Never use `/dev/ttyACM*` directly.

---

**Teensy 4.0 -> Pi4 (one-way, `/dev/ttyIRIS_SERVO`, 115200 baud):**
```
VOL+     -- volume up          (PAJ7620U2: physical swipe UP)
VOL-     -- volume down        (PAJ7620U2: physical swipe DOWN)
STOP     -- stop playback      (PAJ7620U2: swipe LEFT or RIGHT)
LISTEN   -- activate listen    (gesture action / web UI; e.g. FORWARD default)
FORWARD  -- push toward sensor (PAJ7620U2 extended gesture)
BACKWARD -- pull away          (PAJ7620U2 extended gesture)
CW       -- clockwise rotation (PAJ7620U2 extended gesture)
CCW      -- counter-clockwise  (PAJ7620U2 extended gesture)
```
All 8 commands are dispatched via `base_mount_bridge.py`. Actions configurable via GESTURE_MAP in `iris_config.json` (web UI: Gestures tab). Only `base_mount_bridge.py` owns `/dev/ttyIRIS_SERVO`. Pi4 never sends commands to Teensy 4.0 — serial is one-way.
See "PAJ7620U2 Gesture Sensor Quick-Reference" section for register 0x43 bit layout and mount rotation table.

---

## Sleep State Machine

```
EYES:SLEEP: eyesSleeping=true, blankDisplays(), mouthSetSleepIntensity(),
            sleepRendererInit(), leds.show_sleep()
loop() while sleeping: processSerial(), renderSleepFrame(), mouthSleepFrame(), return
EYES:WAKE:  eyesSleeping=false, mouthRestoreIntensity(), setEyeDefinition(saved),
            applyEmotion(NEUTRAL), show_idle_for_mode(leds)
```

---

## Slash Commands

| Command | File | Purpose |
|---|---|---|
| `/flash` | `.claude/commands/flash.md` | Local USB flash via PlatformIO |
| `/flash-remote` | `.claude/commands/flash-remote.md` | Remote flash via Pi4 SSH (software bootloader) |
| `/deploy` | `.claude/commands/deploy.md` | Persist Pi4 files through overlayfs to SD |
| `/snapshot` | `.claude/commands/snapshot.md` | Generate end-of-session snapshot |
| `/eye-edit` | `.claude/commands/eye-edit.md` | Eye config edit + genall.py + pupil re-apply |

---

## Deploy / Flash Commands

```bash
# Pi4 SSH (host=192.168.1.200, user=pi, pass=ohs):
# Root-owned files: write to /tmp via sftp_write, then:
sudo cp /tmp/<file> /home/pi/<file>
# Persist to SD:
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/<file> /media/root-ro/home/pi/<file>
sudo chown pi:pi /media/root-ro/home/pi/<file>
sudo chmod 644 /media/root-ro/home/pi/<file>
sync
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/<file> /media/root-ro/home/pi/<file>
# Restart service:
sudo systemctl restart assistant
journalctl -u assistant -n 30 --no-pager

# FLASH: Claude runs `pio run` only. User clicks PlatformIO upload. Teensy USB -> Desktop PC (COM7).
# NEVER remote flash. NEVER transfer hex. NEVER run teensy_loader_cli.
# Physical access: Teensy is enclosure-mounted. RESET and PROG buttons are NOT accessible.
# All resets must be done via software bootloader entry (run on Pi4):
python3 -c "import serial, time; s=serial.Serial('/dev/ttyIRIS_EYES',134); time.sleep(0.5); s.close()"
# Serial monitoring: Teensy on COM7 when connected to desktop. Use VS Code terminal (not PlatformIO serial monitor - it locks the port).

# GandalfAI containers (after reboot or manual down):
docker compose -f C:\IRIS\docker\docker-compose.yml up -d
docker compose -f C:\IRIS\docker\docker-compose.gandalf.yml up -d

# Rebuild Ollama models after modelfile change:
ollama create iris -f C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt
ollama create iris-kids -f C:\IRIS\IRIS-Robot-Face\ollama\iris-kids_modelfile.txt
ollama list  # confirm timestamp

# Ollama smoke test (REST API - do NOT use ollama run over SSH, it's interactive):
curl -s http://localhost:11434/api/generate -d "{\"model\":\"iris\",\"prompt\":\"hello\",\"stream\":false}" | python -c "import sys,json; r=json.load(sys.stdin); print(r['response'])"
```

---

## Eye Editing Workflow

1. Edit `resources/eyes/240x240/<eye>/config.eye`
2. Run `python resources/eyes/240x240/genall.py` to regenerate `.h` files
3. Re-apply pupil values manually to nordicBlue.h, hazel.h, bigBlue.h (genall.py resets them)
4. PlatformIO upload

---

## iris-snapshot GitHub Repo

- **Repo:** `https://github.com/Maestro8484/iris-snapshot` (private)
- **Local:** `C:/Users/SuperMaster/Documents/PlatformIO/iris-snapshot/`
- **Pi4 Sudoers:** `/etc/sudoers.d/iris_service` - passwordless sudo for systemctl stop/start/restart/status assistant

---

## Operational Notes - Hard-Won Lessons

> These are confirmed failure patterns and non-obvious system behaviors. Do not remove. Update in place when superseded.

### GandalfAI - Wake on LAN
- MAC: `A4:BB:6D:CA:83:20`
- WoL triggered from Pi4 via assistant.py before Ollama polling begins.

### GandalfAI - VRAM Pressure
- Kokoro ~2GB + mistral-small3.2:24b ~15GB = ~17GB baseline. RTX 3090 = 24GB. Headroom ~7GB (S119b). 100% GPU.
- iris/iris-kids model base is mistral-small3.2:24b (Pixtral vision baked in). num_ctx 6144 unified (text+vision).
- OLLAMA_FLASH_ATTENTION=1 and OLLAMA_KV_CACHE_TYPE=q8_0 are required (set machine-level S39).
- Chrome, Claude Desktop, and any other GPU app all consume additional VRAM.
- Close Chrome and Claude Desktop during inference-heavy sessions.

### GandalfAI - PowerShell Ampersand Rule
- String operations involving URLs containing `&` must NOT be done inline in PowerShell.
- Pattern: write a Python script via `sftp_write`, execute it via `ssh_exec`, then restart the service.
- Inline PS string handling of `&` in URLs causes silent failures.

### GandalfAI - Chatterbox Parameters (Rollback Reference — Kokoro is primary since S38)
- `speed_factor=1.0`, `temperature=0.8`
- Values of `speed_factor=1.05` / `temperature=0.89` caused muffled output -- revert immediately if degradation observed.
- Reference audio: `C:\IRIS\chatterbox\reference_audio\iris_voice.wav`

### Pi4 - overlayfs Mental Model
- Filesystem has a glass panel in front of it. All writes go to RAM layer and are wiped on reboot.
- `overlayroot-chroot` opens a side door to write directly to SD.
- `/boot/firmware` is a separate locked cabinet -- needs its own `remount,rw` even inside chroot.
- Always `md5sum` verify RAM layer and SD layer match after every write. No exceptions.
- Config: `/etc/overlayroot.local.conf`. Do NOT use `raspi-config nonint do_overlayfs` -- unreliable.

### Pi4 - api_persist_config Ownership Bug
- Any route doing `sudo cp` to `iris_config.json` must immediately follow with `sudo chown pi:pi /home/pi/iris_config.json`.
- Ownership corruption silently breaks the entire assistant pipeline on next deploy.
- Root cause of April 16-18 failure cascade (S22B post-mortem).

### Pi4 - SSH Auth
- Password auth currently used. Credential stored out-of-band; do not commit it to repo. Key-based auth is not configured and fails.
- Claude MCP tool: `ssh-pi4`. Bash syntax only.

### Pi4 - iris_config.json Override Behavior
- Keys are only applied at runtime if they appear in `core/config.py`'s `_OVERRIDABLE` list.
- Unknown keys are silently ignored -- no error, no effect. (`ELEVENLABS_ENABLED` was a legacy key removed S20.)

### Ollama - Model Name History
- Models were renamed from `jarvis` / `jarvis-kids` (mistral-small3.2:24b) to `iris` / `iris-kids` (gemma3:12b) between S18-S22B.
- Always confirm current model names via `ollama list` before any Ollama work. Never assume from memory.
- Any modelfile referencing old household names or lacking paralinguistic tags is stale -- delete, do not edit.

---

## Operational Reference (moved from CLAUDE.md)

### Environment Quick Reference

| Machine | IP | Auth | Role |
|---|---|---|---|
| SuperMaster Desktop | 192.168.1.103 | SuperMaster/ohs | Control node, Claude Desktop, local repo, VS Code, PlatformIO, git |
| Pi4 | 192.168.1.200 | pi/ohs | Runtime orchestration, wakeword, audio, web UI, cron, serial bridge - ssh-pi4 MCP |
| GandalfAI | 192.168.1.3 | gandalf/5309 | Ollama, Whisper, Kokoro TTS (primary), Piper TTS (fallback), Chatterbox (rollback only), RTX 3090 inference - ssh-gandalf MCP |
| Teensy 4.1 | USB -> Desktop PC (COM7) | N/A | Embedded display controller (eyes + mouth) — flash via PlatformIO |
| Teensy 4.0 | USB -> Pi4 (/dev/ttyIRIS_SERVO) | N/A | Servo base mount controller — autonomous, no Pi4 commands in |

Pi4 live mirror:
`pi4/` in repo maps to `/home/pi/` on Pi4.

GandalfAI:
Use PowerShell syntax. No bash, grep, df, or head. Use PowerShell equivalents.
Filesystem MCP scope: `C:\Users\gandalf\` only. `C:\IRIS\` and `C:\docker\` via ssh_exec or sftp_write.

Firmware:
Claude may run `pio run`. User performs PlatformIO upload unless explicitly directed otherwise. Never remote flash unless an approved workflow says so.

---

### VRAM (GandalfAI)

Kokoro ~2GB + mistral-small3.2:24b ~15GB = ~17GB. RTX 3090 = 24GB. Headroom ~7GB (S119b). 100% GPU.
- Close Chrome and Claude Desktop during inference-heavy sessions.

---

### Pi4 Persistence

Pi4 uses overlayfs. Writes go to RAM layer unless persisted to SD.

Use direct `/media/root-ro` remount method only.

Do not use `overlayroot-chroot` unless explicitly re-verified.

Canonical persistence pattern:
```bash
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/<file> /media/root-ro/home/pi/<file>
sudo chown pi:pi /media/root-ro/home/pi/<file>
sudo chmod 644 /media/root-ro/home/pi/<file>
sync
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/<file> /media/root-ro/home/pi/<file>
```

For executable scripts:
```bash
sudo chmod 755 /media/root-ro/home/pi/<script>.py
```

Every Pi4 file write must include:
- RAM layer update
- SD layer persistence
- md5 verification
- service restart if needed
- log check

No exceptions.

---

### Git / Snapshot Rules (Condensed)

`main` only. GitHub is secondary mirror. Claude never pushes unless explicitly authorized. `SNAPSHOT_LATEST.md` records current machine status and issues. `HANDOFF_CURRENT.md` records authoritative workflow and roadmap.

---

### MAD Loop - Required Change Workflow

MAD Loop = Multi-Agent Adversarial Dev Loop.

Use for all non-trivial changes:

Plan -> ChatGPT Review -> Optional Codex Audit -> Final Handoff -> Claude Code Implementation -> Human Validation -> Documentation Update

Rules:
- One batch per session.
- Minimal diffs.
- Preserve working behavior unless behavior is the bug.
- Include rollback steps.
- Test before next batch.
- Do not stack unverified changes.
- Human operator has final authority.

---

### Batch Model

Current hardening sequence:
- Batch 1A = runtime survival / wakeword anti-crash and anti-hang
- Batch 1B = sleep/wake authority and state consistency
- Batch 1C = reliability hygiene and diagnostics
- Batch 2 = Teensy hardware/firmware pass
- Batch 3 = GandalfAI personality/pipeline pass

Future batches may supersede this order only after review.

---

### Handoff Template

```text
Task: [one sentence]
Environment: Pi4 | GandalfAI | Firmware | SuperMaster
Files: [only files read or modified]
Issue ref: [from Active Issues or HANDOFF_CURRENT]

Change spec:
[file]: [specific change]

Verify:
[one pass/fail outcome]

Rollback:
[exact revert method]

Commit:
"[message]"

After commit:
run snapshot/docs update if required, then print push command for user.
```

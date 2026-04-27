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
| GandalfAI | Ollama LLM, Modelfiles, Whisper STT, Piper TTS, Chatterbox TTS, RTX 3090 inference |
| Teensy 4.1 | Embedded controller for eyes, mouth, sleep renderer, person sensor integration, serial protocol |
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
Pi4 sends prompt/context to Ollama on GandalfAI

TTS:
Pi4 requests Chatterbox primary or Piper fallback on GandalfAI

Playback:
Pi4 plays PCM through wm8960 audio output

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

## Serial Ownership Rule

Only `hardware/teensy_bridge.py` owns `/dev/ttyACM0`.

Everything else must communicate through:
UDP -> `127.0.0.1:10500` -> assistant command listener -> TeensyBridge

Do not open Teensy serial from web routes, cron scripts, or helper scripts.

---

## Current Batch Roadmap

### Batch 1A - Complete
Wakeword runtime survival and anti-hang hardening.

### Batch 1B - Complete
Sleep/wake authority unification.

### Batch 1C - Next
Reliability hygiene:
- sleep greeting through Wyoming Piper
- volume persistence
- TTS hard-cap
- config validation
- safe temp files
- LLM stream warning
- dead-code cleanup only if verified

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
| STT -> LLM -> TTS -> audio output | **WORKING** - confirmed S23 | Full pipeline: Whisper->Ollama iris->Chatterbox->speakers |
| Mouth TFT animation | **WORKING** - confirmed S29 | MOUTH:0-8 cycling during speech. BL on GPIO 5, web UI intensity control working. |
| Sleep/wake cron (9PM/7:30AM) | Working but **REBOOT-FRAGILE** | Piper missing at /usr/local/bin/piper - sleep wakeword says nothing |
| ALSA state on reboot | **HARDENED S23** | alsa-init.sh now sets all 6 critical switches explicitly |
| GandalfAI reboot | **FRAGILE** | Chatterbox docker must be started manually after reboot (`docker compose up -d`) |
| Teensy flash (mouthSleepFrame) | **DONE** - confirmed by user, S27 | /dev/ttyACM0 present, firmware live |
| Mouth smoke test | **DONE** - confirmed by user, S27 | MOUTH:0-8 via UDP 127.0.0.1:10500 confirmed |

### Reboot survival checklist
On Pi4 reboot: alsa-init.sh runs automatically (hardened S23) - mic + speakers restore without manual intervention.
On GandalfAI reboot: run `docker compose -f C:\IRIS\docker\docker-compose.yml up -d` manually - Chatterbox does not auto-start.
On both rebooting simultaneously: GandalfAI must be up before assistant.py finishes boot or it will WoL-wait.

---

## System Architecture

| System | IP | Credentials | Role |
|---|---|---|---|
| Pi4 (IRIS) | 192.168.1.200 | pi / &lt;password&gt; | Voice pipeline, LEDs, camera, Teensy serial |
| GandalfAI | 192.168.1.3 | gandalf / &lt;password&gt; | Ollama LLM, Whisper STT, Piper TTS, Kokoro TTS, RTX 3090 |
| Desktop PC | 192.168.1.103 | SuperMaster / &lt;password&gt; | PlatformIO firmware, VS Code, Claude Desktop. OpenSSH server enabled S29 - Claude can ssh_exec PowerShell commands and run git directly. |
| Teensy 4.1 | USB -> Desktop PC | N/A | Dual GC9A01A 1.28" round TFT eyes + ILI9341 2.8" TFT mouth |
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
    docker-compose.yml          -- iris stack (pipeline: whisper, piper, chatterbox)
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
- `ollama/iris_modelfile.txt` - adult IRIS persona (gemma3:27b-it-qat)
- `ollama/iris-kids_modelfile.txt` - kids IRIS persona (gemma3:27b-it-qat)

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

## Repo Structure

```
IRIS-Robot-Face/
  src/
    main.cpp                    -- serial parsing, emotion/tracking/sleep logic
    config.h                    -- eye definitions array (7 eyes), display pins
    sleep_renderer.h            -- deep space starfield (SR_FRAME_MS=150)
    displays/GC9A01A_Display.h  -- display driver
    eyes/EyeController.h        -- eye movement/blink/pupil (setTargetPosition seed fix intact)
    eyes/240x240/               -- nordicBlue/flame/hypnoRed/hazel/blueFlame1/dragon/bigBlue .h
    sensors/PersonSensor.h/.cpp -- I2C face detection (SAMPLE_TIME_MS=70, conf>60, is_facing)
    mouth_tft.cpp/.h            -- ILI9341 TFT mouth driver (KurtE/ILI9341_t3n, SPI2)
  pi4/                          -- mirrors /home/pi/ on Pi4
    assistant.py                -- THIN orchestrator (~340 lines)
    services/tts.py             -- Chatterbox->Piper only (ElevenLabs removed S20)
    services/stt.py             -- Wyoming Whisper STT (data_length payload parser)
    services/vision.py          -- camera capture + vision query
    services/llm.py             -- stream_ollama(), ask_ollama(), emotion extraction, reply cleaning
    services/wakeword.py        -- OWW + GPIO button handler
    hardware/audio_io.py        -- PCM playback, record, beep, interrupt detection
    hardware/led.py             -- APA102 driver
    hardware/teensy_bridge.py   -- single serial owner of /dev/ttyACM0
    hardware/io.py              -- GPIO helpers
    state/state_manager.py      -- StateManager: conversation_history, kids_mode, eyes_sleeping
    core/config.py              -- all constants; iris_config.json override loader
    iris_web.py                 -- Flask web panel (serves iris_web.html fresh per-request)
    iris_web.html               -- Web UI (ElevenLabs removed S18, MAX7219/matrix refs removed S21)
    iris_sleep.py               -- cron sleep script
    iris_wake.py                -- cron wake script
  ollama/
    iris_modelfile.txt          -- adult IRIS persona (gemma3:12b) -- canonical
    iris-kids_modelfile.txt     -- kids IRIS persona (gemma3:12b) -- canonical
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

### core/config.py (as of S20)

```python
OLLAMA_MODEL_ADULT      = "iris"
OLLAMA_MODEL_KIDS       = "iris-kids"
VISION_MODEL            = "iris"
OWW_THRESHOLD           = 0.90
CHATTERBOX_BASE_URL     = "http://192.168.1.3:8004"
CHATTERBOX_VOICE        = "iris_voice.wav"
CHATTERBOX_EXAGGERATION = 0.45
CHATTERBOX_ENABLED      = True
NUM_PREDICT             = 150     # overridden to 120 by iris_config.json
LED_SLEEP_PEAK          = 26
LED_SLEEP_FLOOR         = 3
LED_SLEEP_PERIOD        = 8.0
LED_SLEEP_BRIGHT        = 0xFF
```

### iris_config.json on Pi4 (current)

```json
{ "OWW_THRESHOLD": 0.9, "CHATTERBOX_ENABLED": true, "NUM_PREDICT": 120 }
```

Note: `ELEVENLABS_ENABLED` was removed in S20 — if present in iris_config.json it is silently ignored and safe to delete.

### src/main.cpp key constants

```
FACE_LOST_TIMEOUT_MS=5000 | FACE_COOLDOWN_MS=30000
ANGRY_EYE_DURATION_MS=9000 | CONFUSED_EYE_DURATION_MS=7000
EYE_IDX_DEFAULT=0, ANGRY=1, CONFUSED=2, COUNT=7
```

### Ollama models (as of S39)

- `iris:latest` - gemma3:27b-it-qat, num_predict 800, temperature 0.82, num_ctx 4096
- `iris-kids:latest` - gemma3:27b-it-qat, num_predict 800, temperature 0.90, num_ctx 4096
- Stop token: `<end_of_turn>` (gemma family)
- VRAM: Kokoro ~2GB + gemma3:27b-it-qat ~14.1GB = ~16.1GB total. Headroom ~7.9GB on RTX 3090 (24GB).
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

**Teensy -> Pi4:** `FACE:1` / `FACE:0`
**Rule:** Only TeensyBridge owns `/dev/ttyACM0`. Everything else uses UDP -> `127.0.0.1:10500`.

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
python3 -c "import serial, time; s=serial.Serial('/dev/ttyACM0',134); time.sleep(0.5); s.close()"
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
- Kokoro ~2GB + gemma3:27b-it-qat ~14.1GB = ~16.1GB baseline. RTX 3090 = 24GB. Headroom ~7.9GB.
- OLLAMA_FLASH_ATTENTION=1 and OLLAMA_KV_CACHE_TYPE=q8_0 are required at 27b scale (set machine-level S39).
- Chrome, Claude Desktop, and any vision model all consume additional VRAM.
- Close Chrome and Claude Desktop during inference-heavy sessions — headroom is tight at ~2.2GB when models are warm.
- Do not raise `num_ctx` above 4096.

### GandalfAI - PowerShell Ampersand Rule
- String operations involving URLs containing `&` must NOT be done inline in PowerShell.
- Pattern: write a Python script via `sftp_write`, execute it via `ssh_exec`, then restart the service.
- Inline PS string handling of `&` in URLs causes silent failures.

### GandalfAI - Chatterbox Parameters (Baseline)
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

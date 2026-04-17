# IRIS Architecture Reference

> Read on demand only. Do not load at session start.
> Update this file directly when hardware changes. Do not duplicate in snapshots.

---

## System Architecture

| System | IP | Credentials | Role |
|---|---|---|---|
| Pi4 (IRIS) | 192.168.1.200 | pi / ohs | Voice pipeline, LEDs, camera, Teensy serial |
| GandalfAI | 192.168.1.3 | gandalf / 5309 | Ollama LLM, Whisper STT, Piper TTS, Chatterbox TTS, RTX 3090 |
| Desktop PC | 192.168.1.103 | SuperMaster | PlatformIO firmware, VS Code, Claude Desktop |
| Teensy 4.1 | USB → Desktop PC | N/A | Dual GC9A01A 1.28" round TFT eyes + ILI9341 2.8" TFT mouth |
| Synology NAS | 192.168.1.102 | Master / Gateway!7007 | SSH port 2233. Backup: \\192.168.1.102\BACKUPS\IRIS-Robot-Face\ |

**SSH MCP tools:** `ssh-pi4` (192.168.1.200), `ssh-gandalf` (192.168.1.3), `ssh` (NAS, port 2233)
**SSH auth Pi4:** Password auth only — key auth fails.
**SSH auth GandalfAI:** `gandalf / 5309`
**GandalfAI:** Windows machine. No `df`, `head`, `grep` — use PowerShell / findstr / dir equivalents.
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
- `ollama/iris_modelfile.txt` — adult IRIS persona (gemma3:12b)
- `ollama/iris-kids_modelfile.txt` — kids IRIS persona (gemma3:12b)

HF cache: `C:\Users\gandalf\.cache\huggingface` — stays in user profile, intentionally not moved.

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
| — | RST | Right eye | -1 (no pin) |
| 11 | MOSI | Right eye | SPI0 hw |
| 13 | SCK | Right eye | SPI0 hw |

### Person Sensor I2C — mounted RIGHT-SIDE-UP

| GPIO | Signal |
|---|---|
| 18 | SDA |
| 19 | SCL |

### ILI9341 TFT Mouth (hardware SPI2)

| GPIO | Signal | Notes |
|---|---|---|
| 35 | MOSI | SPI2 hw |
| 37 | SCK | SPI2 hw |
| 36 | CS | — |
| 8 | DC | — |
| 4 | RST | — |
| 14 | BL | PWM: 220 boot/wake, 40 sleep |

> Free pins: 5, 6, 7, 15–17, 20–25, 28–33, 38–55 (T4.1 extended)
> Pins 5/6/7 were legacy MAX7219 matrix (removed hardware). Now free.

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
    services/tts.py             -- Chatterbox→Piper only (ElevenLabs removed S20)
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
    iris_modelfile.txt          -- adult IRIS persona (gemma3:12b) — canonical
    iris-kids_modelfile.txt     -- kids IRIS persona (gemma3:12b) — canonical
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

### Pupil values — re-apply manually after every genall.py run

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

Note: `ELEVENLABS_ENABLED` key may still exist — config loader silently ignores unknown keys.

### src/main.cpp key constants

```
FACE_LOST_TIMEOUT_MS=5000 | FACE_COOLDOWN_MS=30000
ANGRY_EYE_DURATION_MS=9000 | CONFUSED_EYE_DURATION_MS=7000
EYE_IDX_DEFAULT=0, ANGRY=1, CONFUSED=2, COUNT=7
```

### Ollama models (as of S20)

- `iris:latest` — gemma3:12b, num_predict 120, temperature 0.7, num_ctx 4096
- `iris-kids:latest` — gemma3:12b, num_predict 120, temperature 0.90, num_ctx 4096
- Stop token: `<end_of_turn>` (gemma family)
- VRAM: Chatterbox ~4.5GB + gemma3:12b ~7GB = ~11.5GB total. Headroom ~12.5GB on RTX 3090 (24GB).

---

## Cron Entries (Pi4 user crontab)

```
0 21 * * * ALSA_CARD=seeed2micvoicec /usr/bin/python3 /home/pi/iris_sleep.py >> /home/pi/logs/iris_sleep.log 2>&1
30 7 * * * ALSA_CARD=seeed2micvoicec /usr/bin/python3 /home/pi/iris_wake.py >> /home/pi/logs/iris_wake.log 2>&1
0 3 * * 0 sudo /bin/bash /home/pi/iris_backup.sh
```

---

## Serial Protocol

**Pi4 → Teensy:**
```
EMOTION:NEUTRAL/HAPPY/CURIOUS/ANGRY/SLEEPY/SURPRISED/SAD/CONFUSED
EYES:SLEEP / EYES:WAKE
EYE:n              -- switch default eye (0–6)
MOUTH:x            -- set mouth expression (0–8)
MOUTH_INTENSITY:n  -- set backlight level (0–15)
```

**Teensy → Pi4:** `FACE:1` / `FACE:0`
**Rule:** Only TeensyBridge owns `/dev/ttyACM0`. Everything else uses UDP → `127.0.0.1:10500`.

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
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/<file> /media/root-ro/home/pi/<file>
# Restart service:
sudo systemctl restart assistant
journalctl -u assistant -n 30 --no-pager

# FLASH: Claude runs `pio run` only. User clicks PlatformIO upload. Teensy USB → Desktop PC.
# NEVER remote flash. NEVER transfer hex. NEVER run teensy_loader_cli.
# Software bootloader entry (Teensy in enclosure, no PROG button):
python3 -c "import serial, time; s=serial.Serial('/dev/ttyACM0',134); time.sleep(0.5); s.close()"

# GandalfAI containers (after reboot or manual down):
docker compose -f C:\IRIS\docker\docker-compose.yml up -d
docker compose -f C:\IRIS\docker\docker-compose.gandalf.yml up -d

# Rebuild Ollama models after modelfile change:
ollama create iris -f C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt
ollama create iris-kids -f C:\IRIS\IRIS-Robot-Face\ollama\iris-kids_modelfile.txt
ollama list  # confirm timestamp

# Ollama smoke test (REST API — do NOT use ollama run over SSH, it's interactive):
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
- **Pi4 Sudoers:** `/etc/sudoers.d/iris_service` — passwordless sudo for systemctl stop/start/restart/status assistant

# IRIS System Inventory
**Generated:** S50-planning | 2026-05-19 | Source: IRIS_ARCH.md, IRIS_CONFIG_MAP.md, servo_teensy/*.ino

---

## Nodes

| Node | IP | OS | SSH Tool | Role |
|---|---|---|---|---|
| SuperMaster | 192.168.1.103 | Windows | `ssh` (PowerShell) | Repo, PlatformIO, Claude Desktop |
| Pi4 | 192.168.1.200 | Linux | `ssh-pi4` (bash) | Runtime, audio, web UI, serial bridge |
| GandalfAI | 192.168.1.3 | Windows | `ssh-gandalf` (PowerShell) | Ollama, Whisper, Kokoro, Piper, RTX 3090 |
| Teensy 4.1 | USB COM7 | — | PlatformIO (user upload) | Eye TFTs, mouth TFT, Person Sensor |
| Servo Controller (Teensy 4.0) | USB → Pi4 /dev/ttyACM1 | — | PlatformIO (user upload, COM11) | Pan servo, Person Sensor + APDS-9960 gesture, USB CDC serial to Pi4 |
| NAS | 192.168.1.102 | Synology | `ssh` port 2233 | Backup target |

> Pi4 SSH: password auth only. Key auth fails. GandalfAI: PowerShell only, no bash/grep/df/head.
> GandalfAI filesystem MCP scope: `C:\Users\gandalf\` only. Use ssh_exec or sftp_write for `C:\IRIS\`, `C:\docker\`.

---

## Services and Ports

| Service | Host | Port | Protocol | Type | Notes |
|---|---|---|---|---|---|
| assistant.py | Pi4 | — | — | systemd | Main voice pipeline |
| iris-web (Flask) | Pi4 | 5000 | HTTP | systemd | Web UI at http://192.168.1.200:5000 |
| cmd_listener | Pi4 | 10500 | UDP | in-process | Web UI + cron command bridge. Only path to Teensy for non-bridge code. |
| wyoming-openwakeword | Pi4 | 10400 | TCP | subprocess | Launched by assistant.py. Restarts with assistant. |
| ollama | GandalfAI | 11434 | HTTP | Windows service | Models: iris, iris-kids (gemma3:27b-it-qat) |
| kokoro-tts | GandalfAI | 8004 | HTTP | Docker | Primary TTS. Does NOT auto-start on reboot. |
| wyoming-whisper | GandalfAI | 10300 | TCP | Docker | STT: faster-whisper-large-v3-turbo |
| wyoming-piper | GandalfAI | 10200 | TCP | Docker | TTS fallback: en_US-ryan-high |

> Kokoro manual start after GandalfAI reboot: `docker compose -f C:\IRIS\docker\docker-compose.yml up -d`

---

## Key File Paths

| Logical Name | Node | Path |
|---|---|---|
| Repo root | SuperMaster | `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face` |
| Pi4 mirror (repo) | — | `pi4/` maps 1:1 to `/home/pi/` |
| Runtime home | Pi4 | `/home/pi/` |
| SD layer | Pi4 | `/media/root-ro/home/pi/` |
| iris_config.json | Pi4 | `/home/pi/iris_config.json` |
| logs dir | Pi4 | `/home/pi/logs/` |
| intent log | Pi4 | `/home/pi/logs/iris_intent.log` |
| bench log | Pi4 | `/home/pi/logs/iris_bench.jsonl` |
| conversation log | Pi4 | `/home/pi/logs/conversations.jsonl` |
| sleep state flag | Pi4 | `/tmp/iris_sleep_mode` |
| alsa-init | Pi4 | `/home/pi/alsa-init.sh` (protected) |
| Teensy serial | Pi4 | `/dev/ttyACM0` (TeensyBridge owner only) |
| Iris modelfile | GandalfAI | `C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt` |
| Kids modelfile | GandalfAI | `C:\IRIS\IRIS-Robot-Face\ollama\iris-kids_modelfile.txt` |
| Docker compose (iris stack) | GandalfAI | `C:\IRIS\docker\docker-compose.yml` |
| sysmap.json | SuperMaster | `docs/sysmap.json` (gitignored, local only) |

---

## Pi4 Protected Files (do not touch without explicit instruction)

`/home/pi/iris_config.json` | `/home/pi/alsa-init.sh` | `src/TeensyEyes.ino` | `src/eyes/EyeController.h`

---

## Pi4 Cron Schedule

| Time | Script | Log |
|---|---|---|
| 21:00 daily | `/home/pi/iris_sleep.py` | `/home/pi/logs/iris_sleep.log` |
| 07:30 daily | `/home/pi/iris_wake.py` | `/home/pi/logs/iris_wake.log` |
| 03:00 Sunday | `/home/pi/iris_backup.sh` | — |

---

## GPIO: Teensy 4.1

| Pin | Signal | Device | Bus | Notes |
|---|---|---|---|---|
| 0 | CS | Left eye GC9A01A | SPI1 | |
| 2 | DC | Left eye GC9A01A | SPI1 | |
| 3 | RST | Left eye GC9A01A | SPI1 | Dupont recrimped S29 |
| 26 | MOSI | Left eye GC9A01A | SPI1 hw | |
| 27 | SCK | Left eye GC9A01A | SPI1 hw | |
| 10 | CS | Right eye GC9A01A | SPI0 | |
| 9 | DC | Right eye GC9A01A | SPI0 | |
| 11 | MOSI | Right eye GC9A01A | SPI0 hw | |
| 13 | SCK | Right eye GC9A01A | SPI0 hw | |
| 35 | MOSI | Mouth ILI9341 | SPI2 hw | |
| 37 | SCK | Mouth ILI9341 | SPI2 hw | |
| 36 | CS | Mouth ILI9341 | SPI2 | |
| 8 | DC | Mouth ILI9341 | SPI2 | |
| 4 | RST | Mouth ILI9341 | SPI2 | |
| 5 | BL (PWM) | Mouth ILI9341 | — | 220 awake, 8 sleep. Reassigned from GPIO 14 in S29. |
| 18 | SDA | Person Sensor I2C | I2C | Mounted RIGHT-SIDE-UP |
| 19 | SCL | Person Sensor I2C | I2C | |

> Free pins: 6, 7, 15-17, 20-25, 28-33, 38-55. Pins 6/7 are legacy MAX7219 (hardware removed).
> RESET and PROG buttons NOT accessible (enclosure-mounted). All resets via software bootloader.

---

## GPIO: Servo Controller (Teensy 4.0)

| Pin | Signal | Device | Notes |
|---|---|---|---|
| 9 | PWM | Pan servo SG90 | panServo.attach(9) |
| 18 | SDA | I2C shared bus | Wire default SDA. Person Sensor 0x62 + APDS-9960 0x39 |
| 19 | SCL | I2C shared bus | Wire default SCL |

> Source: `servo_teensy40/IRIS-BaseServoControlViaPerson_Sensor/IRIS-BaseServoControlViaPerson_Sensor.ino`
> Board: Teensy 4.0 (replaced Pico W S56 — hardware failure). PlatformIO: env:teensy40, platform teensy.
> USB CDC serial → Pi4 /dev/ttyACM1 at 9600 baud. Pi4 assistant.py start_servo_listener() reads commands.
> Servo 5V rail is independent (physical toggle switch). Board powered via Pi4 USB.

---

## iris_config.json Overridable Keys

| Key | Default | Range | Restart? | UI Tab |
|---|---|---|---|---|
| RECORD_SECONDS | 10 | 1-60 | No | Audio |
| SILENCE_SECS | 1.5 | 0.1-10.0 | No | Audio |
| SILENCE_RMS | 300 | 50-5000 | No | Audio |
| KIDS_RECORD_SECONDS | 14 | 1-60 | No | Audio |
| KIDS_SILENCE_SECS | 3.5 | 0.1-15.0 | No | Audio |
| KIDS_SILENCE_RMS | 150 | 50-5000 | No | Audio |
| OWW_THRESHOLD | 0.90 | 0.5-1.0 | No | Wake Word |
| OWW_DRAIN_SECS | 0.15 | 0.05-1.0 | No | Wake Word |
| KOKORO_ENABLED | true | — | No | Voice |
| KOKORO_VOICE | bm_lewis | — | No | Voice |
| KOKORO_SPEED | 1.0 | 0.5-2.0 | No | Voice |
| FOLLOWUP_TIMEOUT | 2 | 1-60 | No | Conversation |
| KIDS_FOLLOWUP_TIMEOUT | 15 | 1-120 | No | Conversation |
| FOLLOWUP_MAX_TURNS | 3 | 1-20 | No | Conversation |
| CONTEXT_TIMEOUT_SECS | 300 | 30-3600 | No | Conversation |
| NUM_PREDICT_SHORT | 120 | 10-2000 | No | Conversation |
| NUM_PREDICT_MEDIUM | 350 | 10-2000 | No | Conversation |
| NUM_PREDICT_LONG | 700 | 10-2000 | No | Conversation |
| NUM_PREDICT_MAX | 1200 | 10-2000 | No | Conversation |
| TTS_MAX_CHARS | 900 | 100-4000 | No | Conversation |
| OLLAMA_MODEL_ADULT | iris | — | No | Gandalf AI |
| OLLAMA_MODEL_KIDS | iris-kids | — | No | Gandalf AI |
| MOUTH_INTENSITY_AWAKE | 8 | 0-15 | No | Sleep |
| MOUTH_INTENSITY_SLEEP | 1 | 0-15 | No | Sleep |
| LED_SLEEP_PEAK | 26 | 0-255 | Yes | Sleep |
| LED_SLEEP_FLOOR | 3 | 0-255 | Yes | Sleep |
| LED_SLEEP_PERIOD | 8.0 | 0.5-30.0 | Yes | Sleep |
| LED_IDLE_PEAK | 65 | 0-255 | Yes | Lights |
| LED_IDLE_FLOOR | 3 | 0-255 | Yes | Lights |
| LED_IDLE_PERIOD | 5.0 | 0.5-30.0 | Yes | Lights |
| LED_KIDS_PEAK | 62 | 0-255 | Yes | Lights |
| LED_KIDS_PERIOD | 4.0 | 0.5-30.0 | Yes | Lights |
| SPEAKER_VOLUME | 121 | 60-127 | No | System |
| VOL_MAX | 127 | 60-127 | No | System |

> Stale keys (delete from iris_config.json if present): `MOUTH_INTENSITY`, `ELEVENLABS_ENABLED`, `NUM_PREDICT`

---

## Hardcoded Constants (core/config.py)

| Constant | Value | Notes |
|---|---|---|
| SAMPLE_RATE | 16000 Hz | |
| CHANNELS | 2 | Stereo required by wm8960 |
| CHUNK | 1024 | |
| OWW_PORT | 10400 | |
| WHISPER_PORT | 10300 | |
| PIPER_PORT | 10200 | |
| OLLAMA_PORT | 11434 | |
| CMD_PORT | 10500 | UDP, localhost only |
| SLEEP_WINDOW_START | 21 (9PM) | Cron-driven |
| SLEEP_WINDOW_END | 8 (8AM) | Cron-driven |
| WOL_BOOT_TIMEOUT | 120s | |
| VISION_MODEL | iris | |
| PIPER_VOICE | en_US-ryan-high | Fallback TTS voice |

---

## Ollama Models

| Model | Base | num_ctx | temperature | Stop token |
|---|---|---|---|---|
| iris | gemma3:27b-it-qat | 4096 (hard max) | 0.82 | `<end_of_turn>` |
| iris-kids | gemma3:27b-it-qat | 4096 (hard max) | 0.90 | `<end_of_turn>` |

> VRAM: Kokoro 2GB + model 14.1GB = 16.1GB of 24GB. Headroom 7.9GB.
> Required env: `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`
> Drift check: `ollama show iris --modelfile` on GandalfAI. Compare SYSTEM block to repo. Check for PT-001 few-shot block.

---

## Eye Index Map

| Index | Eye | Trigger |
|---|---|---|
| 0 | nordicBlue | Default idle |
| 1 | flame | ANGRY (auto-reverts 9s) |
| 2 | hypnoRed | CONFUSED (auto-reverts 7s) |
| 3 | hazel | Web UI / EYE:3 |
| 4 | blueFlame1 | Web UI / EYE:4 |
| 5 | dragon | Web UI / EYE:5 |
| 6 | bigBlue | Web UI / EYE:6 |

---

## Deploy Status

| System | Status | Last Verified | Notes |
|---|---|---|---|
| Pi4 | — | — | Update from SNAPSHOT_LATEST.md |
| GandalfAI | — | — | Update from SNAPSHOT_LATEST.md |
| Teensy 4.1 | — | — | Update from SNAPSHOT_LATEST.md |
| Servo Controller (Teensy 4.0) | REPO-ONLY | — | Flash + rewire pending (HW-002) |

---

## Pi4 Persistence Pattern (required for every file deploy)

```bash
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/<file> /media/root-ro/home/pi/<file>
sudo chown pi:pi /media/root-ro/home/pi/<file>
sudo chmod 644 /media/root-ro/home/pi/<file>
sync
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/<file> /media/root-ro/home/pi/<file>
```

> Never use overlayroot-chroot (MD5 mismatch confirmed Batch 1A).
> Always chown after any sudo cp to iris_config.json (S22B failure cascade).

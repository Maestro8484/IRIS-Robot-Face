# IRIS Robot Face — Handoff Snapshot
**Date:** 2026-04-17
**Session:** 20
**Branch:** `main`
**Last commit:** 192e6a0 — fix: remove ElevenLabs, fix CLAUDE.md model refs, tighten iris-kids no-markdown
**Repo:** `C:\IRIS\IRIS-Robot-Face`

---

## HOW TO RESUME

Open Claude Code in the IRIS repo directory. The SessionStart hook auto-loads SNAPSHOT_LATEST.md.
If context seems missing: `python3 .claude/hooks/session_start.py`

---

## 1. SYSTEM ARCHITECTURE

| System | IP | Credentials | Role |
|---|---|---|---|
| Pi4 (IRIS) | 192.168.1.200 | pi / ohs | Voice pipeline, LEDs, camera, Teensy serial |
| GandalfAI | 192.168.1.3 | gandalf / 5309 | Ollama LLM, Whisper STT, Piper TTS, Chatterbox TTS, RTX 3090 |
| Desktop PC | 192.168.1.103 | SuperMaster | PlatformIO firmware, VS Code, Claude Desktop |
| GandalfAI (Claude Desktop) | 192.168.1.3 | gandalf / 5309 | Claude Desktop + MCP installed (S14). Local filesystem MCP scope updated S17: now covers `C:\Users\gandalf\`, `C:\IRIS\`, `C:\docker\`, `G:\`. Claude Desktop can read all IRIS project files directly. |
| Teensy 4.1 | USB → Desktop PC | N/A | Dual GC9A01A 1.28" round TFT eyes + ILI9341 2.8" TFT mouth |
| Synology NAS | 192.168.1.102 | Master / Gateway!7007 | SSH port 2233. Backup: \\192.168.1.102\BACKUPS\IRIS-Robot-Face\ |

**SSH MCP tools:** `ssh-pi4` (192.168.1.200), `ssh-gandalf` (192.168.1.3), `ssh` (NAS, port 2233)
**SSH auth Pi4:** Password auth only — key auth fails. Pi4 IP confirmed 192.168.1.200.
**SSH auth GandalfAI:** `gandalf / 5309` — confirmed working S20 via mcp__ssh-gandalf__ssh_connect.
**GandalfAI:** Windows machine. No `df`, `head`, `grep` — use PowerShell / findstr / dir equivalents.
**GandalfAI MCP scope:** filesystem MCP only covers `C:\Users\gandalf\`. All `C:\IRIS\`, `C:\docker\` file reads/writes must go through SSH sftp_write or ssh_exec.

---

## 2. GANDALFAI FILE LAYOUT

All IRIS-related files on GandalfAI now live under `C:\IRIS\`:

```
C:\IRIS\
  docker\
    docker-compose.yml          -- iris stack (pipeline: whisper, piper, chatterbox)
    docker-compose.gandalf.yml  -- gandalf stack (utility: open-webui, watchtower)
    whisper\                    -- whisper model cache
    piper\                      -- piper data
  chatterbox\
    config.yaml                 -- Chatterbox config (last_chunk_size: 300)
    reference_audio\
      iris_voice.wav            -- CONFIRMED PRESENT
    voices\                     -- predefined voices
    model_cache\
    logs\
    outputs\
  backup\
    docker-compose.yml.bak      -- original pre-migration backup
```

**Ollama modelfiles (in repo — canonical):**
- `C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt` — adult IRIS persona (gemma3:12b)
- `C:\IRIS\IRIS-Robot-Face\ollama\iris-kids_modelfile.txt` — kids IRIS persona (gemma3:12b)

**Stale/archived (do not use):**
- `C:\docker\docker-compose.yml.pre-iris.bak` — old monolithic gandalf-IRIS stack (do not restart)
- `C:\docker\whisper\`, `C:\docker\piper\` — originals still present, safe to delete
- `C:\Users\gandalf\Chatterbox-TTS-Server\` — original still present, safe to delete

**HF cache:** `C:\Users\gandalf\.cache\huggingface` — intentionally NOT moved, stays in user profile.

---

## 3. PROJECT STATUS

**Firmware:** Build clean 2026-04-11 (S9). T4.1 swap: complete. Firmware: flashed and confirmed. Physical build: laser cut / 3D printed enclosure complete, renovated and installed.
**Person Sensor tracking:** CONFIRMED WORKING. Stock chrismiller code. Sensor physically mounted right-side-up. `is_facing && conf > 60`, 70ms poll, 120ms animation, stock coordinate formula.
**Sleep display:** Starfield + ZZZ animation on both TFTs confirmed working.
**Sleep LEDs:** APA102 dim indigo breathe on EYES:SLEEP. peak=26, global_bright=0xFF, floor=3.
**Mouth during sleep:** Snore animation. TFT stays blank. BL dims to 40/255.
**Wake from webui:** Working. Cron sleep 9PM/7:30AM UDP path. False wakeword during cron window ignored (button-only override).
**Voice pipeline (assistant.py):** Operational. Modular (hardware/, core/, services/, state/).
**TTS routing:** Chatterbox (primary) → Piper (fallback). ElevenLabs fully removed S20.
**TTS truncation:** `_truncate_for_tts()` active in tts.py — caps Chatterbox input at 220 chars at last sentence boundary.
**Chatterbox server:** Running on GandalfAI at http://192.168.1.3:8004. Stack: `C:\IRIS\docker\docker-compose.yml`.
**Web UI:** Chatterbox-first Voice tab live. EYE:n switching (0–6), Sleep/Wake buttons, live state polling. Port 5000. ElevenLabs references fully purged (S18).
**NUM_PREDICT:** 120 in iris_config.json.
**Cron sleep/wake:** HARDENED. Single user crontab, ALSA_CARD env, correct log paths.
**ILI9341 TFT mouth:** Library switched to KurtE/ILI9341_t3n. CS=36, DC=8, RST=4, MOSI=35, SCK=37 → SPI2. Build confirmed clean. Flashed and installed — physical smoke test pending.
**Flash workflow:** MANUAL ONLY — user clicks PlatformIO upload button. Claude runs `pio run` only.
**Ollama models:** `iris` + `iris-kids` on gemma3:12b. Rebuilt S19 (rename) and S20 (iris-kids no-asterisk).
**OWW_THRESHOLD:** 0.90 in config.py. iris_config.json also has 0.9 — consistent.

---

## 4. CLAUDE CODE INFRASTRUCTURE

### Slash Commands
| Command | File | Purpose |
|---|---|---|
| `/flash` | `.claude/commands/flash.md` | Local USB flash via PlatformIO |
| `/flash-remote` | `.claude/commands/flash-remote.md` | Remote flash via Pi4 SSH (software bootloader confirmed) |
| `/deploy` | `.claude/commands/deploy.md` | Persist Pi4 files through overlayfs to SD |
| `/snapshot` | `.claude/commands/snapshot.md` | Generate end-of-session snapshot |
| `/eye-edit` | `.claude/commands/eye-edit.md` | Eye config edit + genall.py + pupil re-apply workflow |

### iris-snapshot GitHub repo
- **Repo:** `https://github.com/Maestro8484/iris-snapshot` (private)
- **Local:** `C:/Users/SuperMaster/Documents/PlatformIO/iris-snapshot/`

### Pi4 Sudoers (persisted to SD)
- `/etc/sudoers.d/iris_service` — passwordless sudo for systemctl stop/start/restart/status assistant

### Software Bootloader Entry (Teensy — confirmed working, no PROG button needed)
```bash
python3 -c "import serial, time; s=serial.Serial('/dev/ttyACM0',134); time.sleep(0.5); s.close()"
```

---

## 5. TEENSY 4.1 COMPLETE PIN ASSIGNMENT

### Eye displays (GC9A01A, config.h)
| GPIO | Signal | Wire | Device | Bus |
|---|---|---|---|---|
| 0 | CS | Yellow | Left eye | SPI1 |
| 2 | DC | Blue | Left eye | SPI1 |
| 3 | RST | Brown | Left eye | SPI1 |
| 26 | MOSI | Green | Left eye | SPI1 hw |
| 27 | SCK | Orange | Left eye | SPI1 hw |
| 10 | CS | Yellow | Right eye | SPI0 |
| 9 | DC | Blue | Right eye | SPI0 |
| — | RST | — | Right eye | -1 (no pin) |
| 11 | MOSI | Green | Right eye | SPI0 hw |
| 13 | SCK | Orange | Right eye | SPI0 hw |

### Person Sensor (I2C) — mounted RIGHT-SIDE-UP
| GPIO | Signal | Wire |
|---|---|---|
| 18 | SDA | Blue |
| 19 | SCL | Yellow |

### ILI9341 TFT Mouth (hardware SPI2 — T4.1)
| GPIO | Signal | Wire | Bus |
|---|---|---|---|
| 35 | MOSI | Gray | SPI2 hw |
| 37 | SCK | Green | SPI2 hw |
| 36 | CS | Blue | SPI2 |
| 8 | DC | Purple | — |
| 4 | RST | Brown | — |
| 14 | BL | Orange | PWM: 220 boot/wake, 40 sleep |

> Free pins: 5, 6, 7, 15–17, 20–25, 28–33, 38–55 (T4.1 extended)
> MAX7219 matrix uses 5/6/7 (DATA/CLK/CS) — see mouth.h.

---

## 6. MOUTH TFT STATUS — BUILD CLEAN, FLASHED AND CONFIRMED

**Library:** `moononournation/GFX Library for Arduino @ ^1.4.9` — Arduino_GFX SWSPI (bit-bang).

```cpp
// Bit-bang SPI: MOSI=35, SCK=37, CS=36, DC=8, RST=4, BL=14
_bus = new Arduino_SWSPI(MOUTH_TFT_DC, MOUTH_TFT_CS,
                          MOUTH_TFT_SCK, MOUTH_TFT_MOSI, -1);
_tft = new Arduino_ILI9341(_bus, MOUTH_TFT_RST, 3);  // rotation=3 (landscape flipped)
```

> No DMA, no hardware SPI — zero conflict with GC9A01A_t3n on SPI0/SPI1.

---

## 7. CHATTERBOX TTS

- **Server:** GandalfAI — containerized at `C:\IRIS\docker\docker-compose.yml`, port 8004
- **Config:** `C:\IRIS\chatterbox\config.yaml` — `last_chunk_size: 300`
- **Model:** Chatterbox Turbo, exaggeration 0.45
- **Voice:** `iris_voice.wav` — CONFIRMED PRESENT at `C:\IRIS\chatterbox\reference_audio\iris_voice.wav`
- **Endpoint:** `POST http://192.168.1.3:8004/tts` — `voice_mode: clone`, `reference_audio_filename: iris_voice.wav`
- **Input truncation:** `_truncate_for_tts(max_chars=220)` applied in tts.py before Chatterbox call.
- **Healthcheck note:** Docker healthcheck reports `unhealthy` when GPU is busy inferring (curl times out during generation). This is a false negative — container is operational.

---

## 8. OLLAMA MODELS (as of S20)

### iris (adult persona)
- **Ollama model name:** `iris:latest`
- **File:** `C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt` (in repo — canonical)
- **Base:** `gemma3:12b` — ~7GB VRAM, stop token `<end_of_turn>`
- **Key params:** `num_predict 120`, `temperature 0.7`, `num_ctx 4096`
- **Identity:** IRIS — Schmidt household AI, dry wit, direct, no sycophancy, no em dashes
- **Smoke test S19:** `[EMOTION:NEUTRAL]` on own line, plain spoken reply, under 2 sentences ✓

### iris-kids (Leo & Mae persona)
- **Ollama model name:** `iris-kids:latest`
- **File:** `C:\IRIS\IRIS-Robot-Face\ollama\iris-kids_modelfile.txt` (in repo — canonical)
- **Base:** `gemma3:12b` — ~7GB VRAM, stop token `<end_of_turn>`
- **Key params:** `num_predict 120`, `temperature 0.90`, `num_ctx 4096`
- **Identity:** Playful, goofy, reciprocal conversation, always redirects with something fun
- **Smoke test S20:** `[EMOTION:HAPPY]` ✓, playful reply ✓, turned question back ✓, asterisks still present (see Known Issues)
- **Rebuilt S20** with strengthened no-asterisk constraint (3 locations in system prompt)

### VRAM budget (RTX 3090, 24GB)
- Chatterbox Turbo: ~4.5GB resident
- gemma3:12b at num_ctx 4096: ~7GB
- Combined: ~11.5GB — **~12.5GB headroom** (well within safe zone)

### LLM call flow
- **Main path:** `stream_ollama()` in `pi4/services/llm.py` — streams tokens, extracts `[EMOTION:X]` tag early
- **Follow-up / vision path:** `ask_ollama()` — blocking single call, same emotion extraction
- **Rebuild after modelfile change:** `ollama create iris -f C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt`

### Other models on GandalfAI disk (not active)
`gemma3:27b-it-qat` (16GB), `gemma3:12b` (8GB base), `gemma3:27b-voice` (17GB), `llama3.1:8b` (4GB), `mistral-small3.2:24b` (15GB), `mistral:7b-instruct-q4_K_M` (4GB), `gpt-oss:20b` (13GB), `qwen2.5-coder:14b` (9GB), `deepseek-r1:14b` (9GB)

---

## 9. REPO STRUCTURE

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
    mouth_tft.cpp/.h            -- ILI9341 TFT mouth driver (Arduino_GFX SWSPI bit-bang)
  pi4/                          -- mirrors /home/pi/ on Pi4
    assistant.py                -- THIN orchestrator. No weather/briefing/person-recog.
    services/tts.py             -- Chatterbox→Piper only (ElevenLabs removed S20)
    services/vision.py          -- ask_vision() includes person ID in prompt
    services/llm.py             -- stream_ollama(), extract_emotion_from_reply(), clean_llm_reply()
    state/state_manager.py      -- StateManager: conversation_history, kids_mode, eyes_sleeping only
    core/config.py              -- all constants; iris_config.json override loader (EL constants removed S20)
    iris_web.py                 -- Flask web panel (ElevenLabs removed S18)
    iris_web.html               -- Web UI (ElevenLabs card removed S18)
  ollama/
    iris_modelfile.txt          -- adult IRIS persona (gemma3:12b) — canonical
    iris-kids_modelfile.txt     -- kids IRIS persona (gemma3:12b) — canonical, no-asterisk hardened S20
```

---

## 10. PLATFORM

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
  moononournation/GFX Library for Arduino @ ^1.4.9
```

---

## 11. KEY FILE STATE

### Eye index map
```
0 = nordicBlue  (default idle)
1 = flame       (ANGRY)
2 = hypnoRed    (CONFUSED)
3 = hazel
4 = blueFlame1
5 = dragon
6 = bigBlue
```

### Pupil values — manual edits (re-apply after genall.py)
| Eye | pupil.min | pupil.max |
|---|---|---|
| nordicBlue | 0.21 | 0.47 |
| hazel | 0.25 | 0.47 |
| bigBlue | 0.24 | 0.50 |
| hypnoRed | 0.25 | 0.50 |

### core/config.py — Key constants (as of S20)
```python
OLLAMA_MODEL_ADULT      = "iris"
OLLAMA_MODEL_KIDS       = "iris-kids"
VISION_MODEL            = "iris"
OWW_THRESHOLD           = 0.90
CHATTERBOX_BASE_URL     = "http://192.168.1.3:8004"
CHATTERBOX_VOICE        = "iris_voice.wav"
CHATTERBOX_EXAGGERATION = 0.45
CHATTERBOX_ENABLED      = True
# ELEVENLABS_* constants removed S20
NUM_PREDICT             = 150     # overridden to 120 by iris_config.json
LED_SLEEP_PEAK          = 26
LED_SLEEP_FLOOR         = 3
LED_SLEEP_PERIOD        = 8.0
LED_SLEEP_BRIGHT        = 0xFF
```

### iris_config.json on Pi4 (current)
```json
{
  "OWW_THRESHOLD": 0.9,
  "CHATTERBOX_ENABLED": true,
  "NUM_PREDICT": 120
}
```
Note: `ELEVENLABS_ENABLED` key removed from iris_config.json is not urgent — config loader will silently ignore unknown keys. Clean up opportunistically.

### src/main.cpp — Key constants
```cpp
FACE_LOST_TIMEOUT_MS = 5000 | FACE_COOLDOWN_MS = 30000
ANGRY_EYE_DURATION_MS = 9000 | CONFUSED_EYE_DURATION_MS = 7000
EYE_IDX_DEFAULT=0, ANGRY=1, CONFUSED=2, COUNT=7
```

### Person Sensor tracking (CONFIRMED WORKING — do not change)
```cpp
SAMPLE_TIME_MS = 70
if (face.is_facing && face.box_confidence > 60) { ... }
float targetX = -((box_left + width/2) / 127.5 - 1.0)
float targetY =  ((box_top + height/3) / 127.5 - 1.0)
eyes->setTargetPosition(targetX, targetY);  // 120ms duration
// Sensor physically mounted RIGHT-SIDE-UP — stock formula is correct
```

### Cron entries (Pi4 user crontab)
```
0 21 * * * ALSA_CARD=seeed2micvoicec /usr/bin/python3 /home/pi/iris_sleep.py >> /home/pi/logs/iris_sleep.log 2>&1
30 7 * * * ALSA_CARD=seeed2micvoicec /usr/bin/python3 /home/pi/iris_wake.py >> /home/pi/logs/iris_wake.log 2>&1
0 3 * * 0 sudo /bin/bash /home/pi/iris_backup.sh
```

---

## 12. SERIAL PROTOCOL

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

## 13. SLEEP STATE MACHINE

```
EYES:SLEEP: eyesSleeping=true, blankDisplays(), mouthSetSleepIntensity(),
            sleepRendererInit(), leds.show_sleep()
loop() while sleeping: processSerial(), renderSleepFrame(), mouthSleepFrame(), return
EYES:WAKE:  eyesSleeping=false, mouthRestoreIntensity(), setEyeDefinition(saved),
            applyEmotion(NEUTRAL), show_idle_for_mode(leds)
```

---

## 14. CHANGES THIS SESSION (S20 — 2026-04-17)

**Task 1 — Remove ElevenLabs from tts.py:**
- Removed `ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL, ELEVENLABS_ENABLED` from import
- Removed entire `_synthesize_elevenlabs()` function (~47 lines)
- Removed `if ELEVENLABS_ENABLED:` branch in `synthesize()`
- Updated module docstring and `synthesize()` docstring: "CB → Piper only"
- Deployed to Pi4 `/home/pi/services/tts.py`, persisted to SD, md5: `420d24fbb0985df9ec42c7810fec910d` ✓

**Task 2 — Remove ElevenLabs from config.py:**
- Removed `# ── ElevenLabs TTS` block: `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `ELEVENLABS_MODEL`, `ELEVENLABS_ENABLED`
- Removed `"ELEVENLABS_VOICE_ID", "ELEVENLABS_MODEL", "ELEVENLABS_ENABLED"` from `_OVERRIDABLE`
- Deployed to Pi4 `/home/pi/core/config.py`, persisted to SD, md5: `38c66d3f39539feebaf0b03dc6244f4f` ✓
- `sudo systemctl restart assistant` → `[INFO] Ready.` confirmed, no ElevenLabs refs in startup log ✓

**Task 3 — Fix CLAUDE.md LLM section:**
- Machine rules Ollama line: updated `jarvis`/`jarvis-kids`/`mistral-small3.2:24b` → `iris`/`iris-kids`/`gemma3:12b`
- Replaced entire LLM Model Selection section: removed mistral-small3.2:24b analysis, model criteria table, multi-family stop token list
- New section: gemma3:12b current model, ~7GB VRAM, ~11.5GB combined, ~12.5GB headroom, `<end_of_turn>` stop token, smoke test criteria includes "no asterisks"

**Task 4 — Tighten iris-kids no-markdown:**
- `iris-kids_modelfile.txt`: Added to HOW YOU TALK: "no *word* formatting of any kind"
- Added new `FORMATTING -- NEVER BREAK` section: "Never use asterisks. Never use *word* or **word** emphasis."
- Added absolute rule at very top of SYSTEM prompt (first line): "FORMATTING RULE -- ABSOLUTE, NO EXCEPTIONS: Never use asterisks..."
- Rebuilt `iris-kids` on GandalfAI twice (after each constraint addition) — success both times
- Smoke test result: gemma3:12b still outputs `*you*` and `*actual*` despite all constraints
- **Finding:** gemma3:12b has deeply embedded `*word*` emphasis behavior; system prompt cannot fully suppress it
- **Mitigation confirmed:** `tts.py` line 183 `re.sub(r'\*+', '', text)` strips all asterisks before TTS — voice output is clean

**Not touched:** `src/` firmware, `iris_config.json`, `alsa-init.sh`, `iris_sleep.py`, `iris_wake.py`, `assistant.py`

---

## 15. CURRENT KNOWN ISSUES / TODO

### HIGH
- **Mouth smoke test** — Never confirmed post-installation. Must verify: `MOUTH:0` through `MOUTH:8` via UDP `127.0.0.1:10500` on Pi4 → TeensyBridge → serial → TFT renders expressions. Do this before any further firmware work.

### MEDIUM
- **iris-kids asterisk in responses (accepted behavior)** — gemma3:12b uses `*word*` emphasis regardless of system prompt. Three-location constraint is in place. tts.py strips asterisks before TTS (line 183). Voice output is clean. Web UI shows raw response with asterisks — cosmetic only. No further action unless web UI display becomes a concern.
- **iris_config.json stale key** — `ELEVENLABS_ENABLED` key may still exist in iris_config.json on Pi4. Config loader silently ignores unknown keys, so harmless. Clean up next time the file is touched.
- **Clean up old GandalfAI source locations** — After confirming stability:
  - `C:\docker\whisper\`, `C:\docker\piper\` (data migrated to `C:\IRIS\docker\`)
  - `C:\Users\gandalf\Chatterbox-TTS-Server\` (migrated to `C:\IRIS\chatterbox\`)
- **Smoke test sleep LED** — Verify web UI Sleep button triggers indigo breathe. Wake restores idle cyan.
- **Exaggeration tuning** — 0.45 starting point. Tune after first live voice test.
- **Chatterbox healthcheck fix** — `curl -f http://localhost:8000/` times out while GPU is busy inferring. Currently harmless but noisy.
- **Chatterbox auto-start on Gandalf boot** — not configured. Requires manual `docker compose up` after reboot.
- **TTS truncation threshold tuning** — 220 chars is a starting point. Monitor real responses.
- **Piper standalone routing for Goodnight/Good morning** — iris_sleep.py "Goodnight" and wakeword-during-sleep "Good morning" silently fail if Wyoming Piper on GandalfAI:10200 is down.

### LOW
- **Untracked files in project root** — iris_voice.wav, _decode_assistant.py, REFACTOR_VISUAL.md, IRIS_AUDIT_2026-04-03.md. Add wav to .gitignore, review/delete or commit others.
- **Old log file** — /home/pi/iris_sleep.log (root level, pre-S2) stale.

---

## 16. WORKFLOW RULES

- Claude Chat = diagnosis, log reading, planning only. No file writes, no SSH command chains.
- Claude Code = all file writes, SSH chains, implementation, service restarts.
- Every Code session opens with: read CLAUDE.md, confirm live state matches declared state, report any drift before acting.
- One session, one concern. State the single goal at session open.
- Smoke test mouth TFT before any further firmware or voice pipeline work.
- Mouth smoke test route: Pi4 SSH -> send `MOUTH:0` through `MOUTH:8` via UDP `127.0.0.1:10500` -> TeensyBridge -> `/dev/ttyACM0` -> Teensy renders on TFT.
- Flash rule: Claude runs `pio run` only. User clicks PlatformIO upload. Never remote flash.
- Canonical Pi4 source: `pi4/assistant.py` only. Never read or write root-level `assistant.py`.
- Every Code session ends with: `git add -A && git commit && git push`, then `/snapshot`.
- **GandalfAI SSH:** use `mcp__ssh-gandalf__ssh_connect` with host=192.168.1.3, user=gandalf, pass=5309. `ollama run` is interactive — use REST API instead: `curl -s http://localhost:11434/api/generate -d '{"model":"...","prompt":"...","stream":false}'`

---

## 17. FLASH / DEPLOY COMMANDS

```bash
# Pi4 SSH (via mcp__ssh-pi4__ssh_connect host=192.168.1.200, user=pi, pass=ohs):
# Write file via sftp_write, then persist:
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/<file> /media/root-ro/home/pi/<file>
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/<file> /media/root-ro/home/pi/<file>

# Pi4 restart assistant:
sudo systemctl restart assistant
journalctl -u assistant -n 30 --no-pager

# FLASH: Claude runs `pio run` only. User clicks PlatformIO upload. Teensy USB → Desktop PC.
# NEVER remote flash, NEVER transfer hex, NEVER run teensy_loader_cli.

# Bring up GandalfAI containers (after reboot or manual down):
docker compose -f C:\IRIS\docker\docker-compose.yml up -d
docker compose -f C:\IRIS\docker\docker-compose.gandalf.yml up -d

# Rebuild iris model after modelfile change:
ollama create iris -f C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt
ollama create iris-kids -f C:\IRIS\IRIS-Robot-Face\ollama\iris-kids_modelfile.txt
ollama list  # confirm timestamp

# Ollama smoke test (REST API — do NOT use ollama run over SSH, it's interactive and times out):
curl -s http://localhost:11434/api/generate -d "{\"model\":\"iris-kids\",\"prompt\":\"<question>\",\"stream\":false}" | python -c "import sys,json; r=json.load(sys.stdin); print(r['response'])"
```

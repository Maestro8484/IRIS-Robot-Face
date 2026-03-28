# IRIS Robot Face — Handoff Snapshot
**Date:** 2026-03-28c
**Branch:** `iris-ai-integration`
**Last commits:** `0bb76e6` (sleep fix), `34815b6` (prev snapshot)
**Repo:** `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face`

Paste this at the start of a new Claude Code session, then say what you want to work on.
Or: the SessionStart hook loads it automatically.

---

## HOW TO RESUME

Open Claude Code in the IRIS repo directory. The SessionStart hook auto-loads this file.
If context seems missing: `python3 .claude/hooks/session_start.py`

---

## 1. SYSTEM ARCHITECTURE

| System | IP | Credentials | Role |
|---|---|---|---|
| Pi4 (IRIS / Jarvis) | 192.168.1.200 | pi / ohs | Voice pipeline, LEDs, camera, Teensy serial |
| GandalfAI | 192.168.1.3 | gandalf / 5309 | Ollama LLM (jarvis/jarvis-kids), Whisper STT, Piper TTS, RTX 3090 |
| Desktop PC | 192.168.1.103 | SuperMaster | PlatformIO firmware, VS Code, Claude Desktop |
| Teensy 4.0 | USB → /dev/ttyACM0 on Pi4 | N/A | Dual GC9A01A 1.28" round TFT eyes, MAX7219 mouth |
| Synology NAS | 192.168.1.102 | Master / Gateway!7007 | SSH port 2233. Backup path: \\192.168.1.102\BACKUPS\IRIS-Robot-Face\ |

**Claude Desktop MCP filesystem scope:** `C:\Users\SuperMaster`
**SSH MCP tools:** `ssh-pi4` (192.168.1.200), `ssh-gandalf` (192.168.1.3), `ssh` (NAS, port 2233)

---

## 2. PROJECT STATUS

**Firmware:** Fully operational. 7-eye system. Sleep starfield renderer. Face tracking working. squint=1.0 on nordicBlue/hazel/bigBlue.
**Serial protocol:** EMOTION:x, EYES:SLEEP/WAKE, EYE:n (0–6), FACE:1/0, MOUTH:x.
**Eye system:** 7 eyes. nordicBlue=default, flame=ANGRY, hypnoRed=CONFUSED.
**Pupil sizes:** −15% applied directly to nordicBlue.h, hazel.h, bigBlue.h. config.eye NOT yet synced.
**Voice pipeline (assistant.py):** Operational. ElevenLabs Starter tier active. 1605 lines.
**Web UI:** EYE:n switching (0–6), Sleep/Wake buttons. Port 5000.
**Sleep mode:** Cron 9PM/7:30AM. UDP path (no serial conflict). Flag file `/tmp/iris_sleep_mode`.
**Sleep display:** Deep space starfield on both TFTs ~15fps.
**Mouth during sleep:** Snore breathing animation, 0x04 brightness (~28%).
**Vision:** Pi camera (imx708), rpicam-still --immediate, retry logic, sent to jarvis on Gandalf.
**Face tracking:** Working. setTargetPosition seed fix in EyeController.h.

---

## 3. CLAUDE CODE INFRASTRUCTURE

### Slash Commands
| Command | File | Purpose |
|---|---|---|
| `/flash` | `.claude/commands/flash.md` | Local USB flash via PlatformIO |
| `/flash-remote` | `.claude/commands/flash-remote.md` | Remote flash via Pi4 SSH (PROG button still required) |
| `/deploy` | `.claude/commands/deploy.md` | Persist Pi4 files through overlayfs to SD |
| `/snapshot` | `.claude/commands/snapshot.md` | Generate end-of-session snapshot |

### Hooks
| Hook | File | Trigger | What it does |
|---|---|---|---|
| SessionStart | `.claude/hooks/session_start.py` | Every session open | Auto-loads latest SNAPSHOT_*.md into context |
| PostToolUse | `.claude/hooks/post_tool_use_build_check.py` | After any Write/Edit to src/ | Runs `pio run` compile check, blocks agent on failure |

Both hooks wired in `.claude/settings.local.json`.

### Pi4 Sudoers (all persisted to SD, md5 verified)
- `/etc/sudoers.d/teensy_loader` — passwordless sudo for teensy_loader_cli
- `/etc/sudoers.d/iris_service` — passwordless sudo for systemctl stop/start/restart/status assistant
- `/etc/sudoers.d/iris_backup` — passwordless sudo for mount/umount/mount.cifs
- `/etc/udev/rules.d/49-teensy.rules` — udev rules for HalfKay + serial
- `teensy-loader-cli` at `/usr/bin/teensy_loader_cli`

---

## 4. NAS BACKUP

**Method:** CIFS mount (`//192.168.1.102/BACKUPS` → `/mnt/nas`) + tar directly to mount
**Script:** `/home/pi/iris_backup.sh` (persisted to SD, md5 verified)
**NAS dest:** `/mnt/nas/IRIS-Robot-Face/` → `\\192.168.1.102\BACKUPS\IRIS-Robot-Face\`
**Cron:** Sunday 3AM — `0 3 * * 0 sudo /bin/bash /home/pi/iris_backup.sh`
**Log:** `/home/pi/logs/iris_backup.log`
**Keeps:** Last 4 `pi4-iris-*.tar.gz`, auto-prunes older
**Current backups on NAS:**
- `pi4-jarvis-2026-03-25.tar.gz` (1.3GB) — prior manual backup
- `pi4-iris-2026-03-28.tar.gz` (1.1GB) — first automated run, confirmed OK

**Run manually:**
```bash
sudo bash /home/pi/iris_backup.sh
```

**Full crontab:**
```
0 21 * * * /usr/bin/python3 /home/pi/iris_sleep.py >> /var/log/iris_sleep.log 2>&1
30 7 * * * /usr/bin/python3 /home/pi/iris_wake.py >> /var/log/iris_sleep.log 2>&1
0 3 * * 0 sudo /bin/bash /home/pi/iris_backup.sh
```

---

## 5. REPO STRUCTURE

```
IRIS-Robot-Face/
  src/
    main.cpp                    -- serial parsing, emotion/tracking/sleep logic
    config.h                    -- eye definitions array (7 eyes), display pins
    sleep_renderer.h            -- deep space starfield (renderSleepFrame, sleepRendererInit)
    TeensyEyes.ino              -- upstream eye engine (DO NOT MODIFY)
    displays/
      GC9A01A_Display.h         -- display driver + fillBlack + getDriver() accessor
      GC9A01A_Display.cpp
    eyes/
      EyeController.h           -- eye movement/blink/pupil (setTargetPosition seed fix)
      eye_params.h
      240x240/
        nordicBlue.h            -- pupil −15% (min 0.21, max 0.47), squint=1.0
        flame.h                 -- ANGRY emotion eye
        hypnoRed.h              -- CONFUSED emotion eye
        hazel.h                 -- pupil −15% (min 0.26, max 0.60), squint=1.0
        blueFlame1.h
        dragon.h
        bigBlue.h               -- pupil −15% (min 0.26, max 0.60), squint=1.0
    sensors/
      PersonSensor.h / .cpp
      LightSensor.h
    util/
      logging.h
    mouth.h                     -- MAX7219 32x8 driver + mouthSleepFrame() + intensity helpers
  pi4/
    iris_sleep.py               -- 9PM cron sleep script (UDP)
    iris_wake.py                -- 7:30AM cron wake script (UDP)
  .claude/
    commands/                   -- flash, flash-remote, deploy, snapshot
    hooks/                      -- session_start.py, post_tool_use_build_check.py
    settings.local.json         -- hook wiring + bash permissions
  ollama/
    jarvis_modelfile.txt
    jarvis-kids_modelfile.txt
  resources/
    eyes/240x240/
      nordicBlue/config.eye     -- pupil values NOT synced to .h edits (pending)
  platformio.ini
  CLAUDE.md
```

---

## 6. PLATFORM

```ini
[env:eyes]
platform = https://github.com/platformio/platform-teensy.git
board = teensy40
framework = arduino
monitor_speed = 115200
build_flags = -std=gnu++17 -O2
lib_deps =
  PaulStoffregen/Wire
  PaulStoffregen/ST7735_t3
  mjs513/GC9A01A_t3n
  adafruit/Adafruit BusIO
  adafruit/Adafruit GFX Library
```

---

## 7. KEY FILE STATE

### Eye index map
```
0 = nordicBlue  (default idle)
1 = flame       (ANGRY emotion swap)
2 = hypnoRed    (CONFUSED emotion swap)
3 = hazel
4 = blueFlame1
5 = dragon
6 = bigBlue
```

### `src/main.cpp` — Key constants
```cpp
FACE_LOST_TIMEOUT_MS     =  5000
FACE_COOLDOWN_MS         = 30000
SERIAL_BUF_SIZE          =    32
ANGRY_EYE_DURATION_MS    =  9000
CONFUSED_EYE_DURATION_MS =  7000
EYE_IDX_DEFAULT          =     0
EYE_IDX_ANGRY            =     1
EYE_IDX_CONFUSED         =     2
EYE_IDX_COUNT            =     7
```

### Emotion table
| Emotion | pupilRatio | doBlink | maxGazeMs |
|---|---|---|---|
| NEUTRAL | 0.40 | false | 3000 |
| HAPPY | 0.75 | true | 1500 |
| CURIOUS | 0.60 | false | 4000 |
| ANGRY | 0.15 | false | 800 |
| SLEEPY | 0.85 | true | 5000 |
| SURPRISED | 0.95 | true | 600 |
| SAD | 0.25 | true | 4000 |
| CONFUSED | 0.70 | true | 2000 |

---

## 8. SERIAL PROTOCOL

**Pi4 → Teensy:**
```
EMOTION:NEUTRAL/HAPPY/CURIOUS/ANGRY/SLEEPY/SURPRISED/SAD/CONFUSED
EYES:SLEEP     -- sleep renderer starts, mouth snore animation
EYES:WAKE      -- restore eye, apply NEUTRAL, restore mouth intensity
EYE:n          -- switch default eye to index n (0–6)
MOUTH:x        -- set mouth expression (0=NEUTRAL ... 8=SLEEP/OFF)
```

**Teensy → Pi4:**
```
FACE:1    -- face detected (30s cooldown, fires during sleep too)
FACE:0    -- face lost
```

**Rule:** Only `assistant.py` TeensyBridge owns `/dev/ttyACM0`. Everything else uses UDP → `127.0.0.1:10500`.

---

## 9. ASSISTANT.PY KEY CONFIG (Pi4)

```python
GANDALF             = "192.168.1.3"
ELEVENLABS_API_KEY  = "sk_752184d377335347d38c185ba56a1bebe9deba4da50ce082"
ELEVENLABS_VOICE_ID = "90eMKEeSf5nhJZMJeeVZ"
ELEVENLABS_MODEL    = "eleven_turbo_v2_5"
ELEVENLABS_ENABLED  = True
OLLAMA_MODEL_ADULT  = "jarvis"
OLLAMA_MODEL_KIDS   = "jarvis-kids"
VISION_MODEL        = "jarvis"
WAKE_WORD           = "hey_jarvis"
OWW_THRESHOLD       = 0.85
TEENSY_PORT         = "/dev/ttyACM0"
TEENSY_BAUD         = 115200
BUTTON_PIN          = 17
CAMERA_ENABLED      = True
CAMERA_WIDTH        = 1024
CAMERA_HEIGHT       = 768
CAMERA_TIMEOUT      = 5000
VOL_MAX             = 110
```

**Audio:** LLM → ElevenLabs/Piper → play_pcm() 3.0x gain → wm8960 HAT → PAM8403 → 2× 3W speakers
**ALSA:** Speaker=120, HP=120, DC/AC=5 | pyaudio device index: **6** (NOT 0)
**Pop fix:** 80ms silence padding on ElevenLabs output.

---

## 10. PI4 OVERLAYFS

SD is read-only. All SSH writes go to RAM, wiped on reboot. Always use `/deploy` or persist manually.

```bash
sudo mount -o remount,rw /media/root-ro
cp /home/pi/<file> /media/root-ro/home/pi/<file>
sudo mount -o remount,ro /media/root-ro
sudo md5sum /home/pi/<file> /media/root-ro/home/pi/<file>
```

---

## 11. PENDING ITEMS

| Priority | Item | Details |
|---|---|---|
| HIGH | **Person sensor brief eye-open during sleep** | [SLEEP] debug serial added to firmware. Guard logic confirmed correct. Capture serial output when face detected during sleep to determine source (Pi4 sending command vs display artifact). |
| HIGH | **"10-min re-sleep" root cause unconfirmed** | UDP fix removes serial conflict theory. If recurs, capture [SLEEP] serial log. |
| MED | **APA102 indigo breathe during sleep** | On EYES:SLEEP: set LEDs to indigo breathe (floor=1, peak=6, period=8s, sine, RGB=(20,0,40)). Add to CMD listener + wakeword sleep handler in assistant.py. |
| MED | **config.eye pupil sync** | nordicBlue/hazel/bigBlue config.eye have old values. Update before next genall.py run: nordicBlue min=0.21/max=0.47, hazel/bigBlue min=0.26/max=0.60. |
| MED | **EMOTION:CONFUSED missing from assistant.py** | Add to VALID_EMOTIONS, MOUTH_MAP, emit_emotion(). |
| MED | **MOUTH:n not sent alongside EMOTION:n** | emit_emotion() should send MOUTH:MOUTH_MAP[X] alongside EMOTION:X. |
| LOW | **EYE:n voice trigger** | Currently web UI only. Add voice: "switch to hazel eyes", etc. |
| LOW | **Go public on GitHub** | Strip ElevenLabs API key from iris_web.py and assistant.py first. |

### Completed 2026-03-28
- [x] Citadel L3/L4 infrastructure: /flash-remote, /deploy, /snapshot commands
- [x] SessionStart + PostToolUse hooks wired
- [x] teensy-loader-cli + sudoers + udev on Pi4, persisted to SD
- [x] NAS backup: CIFS tar to \\192.168.1.102\BACKUPS\IRIS-Robot-Face\, weekly cron, keeps 4
- [x] iris_backup.sh persisted to SD, first run confirmed (1.1GB)
- [x] Backup path updated to IRIS-Robot-Face subdir, script updated + re-persisted

---

## 12. WHAT HAPPENED IN RECENT SESSIONS

### 2026-03-27 (session 1)
- Fixed EYES:SLEEP Teensy freeze: updateChangedAreasOnly(true) SPI DMA lockup (commit `173b485`)
- Fixed vision capture: --immediate flag, retry, stderr parsing
- Fixed face tracking: setTargetPosition eyeOldX/Y seed fix (commit `ed8fa41`)

### 2026-03-27 (session 2)
- Removed [TRK] debug prints (commit `0bb76e6`)
- mouthInit brightness 0x01 → 0x05
- [SLEEP] debug serial added to person sensor block
- iris_sleep/wake.py → UDP path; CMD listener state sync
- squint 0.5 → 1.0 on nordicBlue/hazel/bigBlue
- set_volume(110) at startup; OWW_THRESHOLD=0.85, VOL_MAX=110

### 2026-03-28 (Claude Desktop)
- Citadel L3/L4 Claude Code infrastructure built and wired
- Remote flash via Pi4 SSH configured (teensy-loader-cli, sudoers, udev)
- NAS backup automated via CIFS, path \\192.168.1.102\BACKUPS\IRIS-Robot-Face\
- All Pi4 changes persisted to SD, md5 verified

---

## 13. QUICK REFERENCE

**Restart assistant:**
```bash
sudo systemctl restart assistant
```

**Persist assistant.py:**
```bash
sudo mount -o remount,rw /media/root-ro && cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py && sudo mount -o remount,ro /media/root-ro && sudo md5sum /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
```

**Live log:**
```bash
journalctl -u assistant -f | grep -v "ALSA\|Jack\|pulse\|seeed\|pcm\|conf\|hdmi\|usb\|modem\|JackShm\|server"
```

**Manual backup:**
```bash
sudo bash /home/pi/iris_backup.sh
```

**Flash remote:**
1. `pio run` on desktop
2. `scp .pio/build/eyes/firmware.hex pi@192.168.1.200:/tmp/iris_firmware.hex`
3. `ssh pi@192.168.1.200 "sudo systemctl stop assistant"`
4. Press PROG on Teensy
5. `ssh pi@192.168.1.200 "sudo teensy_loader_cli --mcu=TEENSY40 -w -v /tmp/iris_firmware.hex"`
6. `ssh pi@192.168.1.200 "sudo systemctl start assistant"`

**GandalfAI VRAM:**
```bash
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader
```

---

## 14. HOME LAB NETWORK

| Host | IP | Credentials | Notes |
|---|---|---|---|
| GandalfAI | 192.168.1.3 | gandalf / 5309 | RTX 3090, Ollama, Whisper, Piper |
| Pi4 IRIS/Jarvis | 192.168.1.200 | pi / ohs | SSH port 22 |
| Pi5 Batocera | 192.168.1.67 | root / linux | |
| Proxmox | 192.168.1.5 | root | |
| Home Assistant | 192.168.1.22 | root / ohs | port 8123 |
| Synology NAS | 192.168.1.102 | Master / Gateway!7007 | SSH port 2233. Backups: \\192.168.1.102\BACKUPS\IRIS-Robot-Face\ |
| Desktop PC | 192.168.1.103 | SuperMaster | |

---

## 15. CLAUDE CODE RULES

- Do NOT modify `TeensyEyes.ino`
- Eye appearance: edit config.eye → genall.py → re-apply −15% pupil to nordicBlue/hazel/bigBlue
- Emotion/serial/tracking: `src/main.cpp`
- Display driver: `src/displays/GC9A01A_Display.h`
- Eye controller: `src/eyes/EyeController.h`
- After any src/ change: PostToolUse hook auto-runs compile check
- After any src/ change requiring flash: `/flash` (local) or `/flash-remote` (Pi4 SSH + PROG)
- Pi4 overlayfs: always use `/deploy` after SSH edits, verify md5
- End of session: run `/snapshot`

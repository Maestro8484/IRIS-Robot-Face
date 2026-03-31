# IRIS Robot Face — Handoff Snapshot
**Date:** 2026-03-28e
**Branch:** `iris-ai-integration`
**Last commit:** `09ef2fb` (snapshot session). Uncommitted changes in working copy — see §12.
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
| Synology NAS | 192.168.1.102 | Master / Gateway!7007 | SSH port 2233. Backup: \\192.168.1.102\BACKUPS\IRIS-Robot-Face\ |

**Claude Desktop MCP filesystem scope:** `C:\Users\SuperMaster`
**SSH MCP tools:** `ssh-pi4` (192.168.1.200), `ssh-gandalf` (192.168.1.3), `ssh` (NAS, port 2233)

---

## 2. PROJECT STATUS

**Firmware:** Flashed this session (sleep fix). 7-eye system. Face tracking working. squint=1.0 on nordicBlue/hazel/bigBlue.
**Serial protocol:** EMOTION:x, EYES:SLEEP/WAKE, EYE:n (0–6), FACE:1/0, MOUTH:x.
**Eye system:** 7 eyes. nordicBlue=default, flame=ANGRY, hypnoRed=CONFUSED.
**Pupil sizes (THIS SESSION):** bigBlue min=0.24/max=0.50, hazel min=0.25/max=0.47, hypnoRed min=0.25/max=0.50, nordicBlue min=0.21/max=0.47. All applied directly to .h files.
**Voice pipeline (assistant.py):** Operational. ElevenLabs Starter tier active. ~1605 lines.
**Web UI:** EYE:n switching (0–6), Sleep/Wake buttons with live state polling. Port 5000.
**Sleep mode:** Cron 9PM/7:30AM. UDP path (no serial conflict). Flag file `/tmp/iris_sleep_mode`.
**Sleep display:** Deep space starfield on both TFTs ~6.7fps (SR_FRAME_MS=150).
**Mouth during sleep:** Snore breathing animation, 0x04 brightness (~28%), throttled to 50ms.
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
| `/eye-edit` | `.claude/commands/eye-edit.md` | Eye config edit + genall.py + pupil re-apply workflow |

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
**NAS dest:** `\\192.168.1.102\BACKUPS\IRIS-Robot-Face\`
**Cron:** Sunday 3AM — `0 3 * * 0 sudo /bin/bash /home/pi/iris_backup.sh`
**Run manually:** `sudo bash /home/pi/iris_backup.sh`

---

## 5. REPO STRUCTURE

```
IRIS-Robot-Face/
  src/
    main.cpp                    -- serial parsing, emotion/tracking/sleep logic
    config.h                    -- eye definitions array (7 eyes), display pins
    sleep_renderer.h            -- deep space starfield (SR_FRAME_MS=150, heartbeat)
    TeensyEyes.ino              -- upstream eye engine (DO NOT MODIFY)
    displays/
      GC9A01A_Display.h         -- display driver + fillBlack + getDriver() accessor
      GC9A01A_Display.cpp
    eyes/
      EyeController.h           -- eye movement/blink/pupil (setTargetPosition seed fix)
      240x240/
        nordicBlue.h            -- pupil min=0.21 max=0.47, squint=1.0
        flame.h                 -- ANGRY emotion eye
        hypnoRed.h              -- pupil min=0.25 max=0.50
        hazel.h                 -- pupil min=0.25 max=0.47, squint=1.0
        blueFlame1.h
        dragon.h
        bigBlue.h               -- pupil min=0.24 max=0.50, squint=1.0
    sensors/
      PersonSensor.h / .cpp
    mouth.h                     -- MAX7219 32x8 driver + mouthSleepFrame() + intensity helpers
  pi4/
    iris_sleep.py               -- 9PM cron sleep script (UDP)
    iris_wake.py                -- 7:30AM cron wake script (UDP)
  .claude/
    commands/                   -- flash, flash-remote, deploy, snapshot, eye-edit
    hooks/                      -- session_start.py, post_tool_use_build_check.py
    settings.local.json
  resources/eyes/240x240/      -- config.eye files (NOT synced to .h edits — pending)
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

### Pupil values — manual edits (NOT in config.eye)
| Eye | File | pupil.min | pupil.max |
|---|---|---|---|
| nordicBlue | src/eyes/240x240/nordicBlue.h | 0.21 | 0.47 |
| hazel | src/eyes/240x240/hazel.h | 0.25 | 0.47 |
| bigBlue | src/eyes/240x240/bigBlue.h | 0.24 | 0.50 |
| hypnoRed | src/eyes/240x240/hypnoRed.h | 0.25 | 0.50 |

Re-apply these after any `genall.py` run. Search for `PupilParams` in each `.h`.

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
FACE:1    -- face detected (30s cooldown)
FACE:0    -- face lost
[SR] frame=N  -- sleep renderer heartbeat every 10 frames (~1.5s)
```

**Rule:** Only `assistant.py` TeensyBridge owns `/dev/ttyACM0`. Everything else uses UDP → `127.0.0.1:10500`.

---

## 9. SLEEP STATE MACHINE

```
EYES:SLEEP received (processSerial):
  eyesSleeping = true
  angryEyeActive = confusedEyeActive = false
  displayLeft/Right → updateChangedAreasOnly(false)   ← full-frame path for sleep renderer
  blankDisplays()         ← fillScreen(BLACK) + updateScreen() on both, drains any pending SPI
  mouthSetSleepIntensity()  ← 0x04 (~28%)
  sleepRendererInit()       ← reset ring/star/frame state
  "[DBG] EYES:SLEEP -- starfield starting"

loop() while sleeping:
  processSerial()           ← always runs (commands still received)
  personSensor.read() SKIPPED   ← guarded with !eyesSleeping (I2C off during heavy SPI)
  renderSleepFrame()        ← throttled SR_FRAME_MS=150ms; full-frame to both TFTs
    "[SR] frame=N" every 10 frames ← heartbeat confirms renderer alive
  mouthSleepFrame()         ← throttled 50ms (snore animation)
  return                    ← eye engine skipped

EYES:WAKE received:
  eyesSleeping = false
  displayLeft/Right → updateChangedAreasOnly(true)   ← back to dirty-rect mode
  mouthRestoreIntensity()   ← 0x05 (~33%)
  setEyeDefinition(saved)   ← restore eye
  applyEmotion(NEUTRAL)
  "[DBG] EYES:WAKE -- displays restored"
```

**Key insight:** `updateScreen()` in GC9A01A_t3n is fully synchronous (no DMA). Full-frame write = 57600×2 bytes at 20MHz ≈ 46ms per display ≈ 92ms per render. This is why SR_FRAME_MS=150: it gives ~58ms free time per cycle for processSerial/mouth without blocking.

---

## 10. ASSISTANT.PY KEY CONFIG (Pi4)

```python
GANDALF             = "192.168.1.3"
ELEVENLABS_VOICE_ID = "90eMKEeSf5nhJZMJeeVZ"
ELEVENLABS_MODEL    = "eleven_turbo_v2_5"
ELEVENLABS_ENABLED  = True
OLLAMA_MODEL_ADULT  = "jarvis"
OLLAMA_MODEL_KIDS   = "jarvis-kids"
WAKE_WORD           = "hey_jarvis"
OWW_THRESHOLD       = 0.85
TEENSY_PORT         = "/dev/ttyACM0"
TEENSY_BAUD         = 115200
VOL_MAX             = 110
```

**Note:** ElevenLabs API key is in assistant.py plaintext — do NOT include in snapshots or commits.

**Audio:** LLM → ElevenLabs/Piper → play_pcm() 3.0x gain → wm8960 HAT → PAM8403 → 2× 3W speakers
**ALSA:** Speaker=120, HP=120, DC/AC=5 | pyaudio device index: **6** (NOT 0)
**Pop fix:** 80ms silence padding on ElevenLabs output.

---

## 11. PI4 OVERLAYFS

SD is read-only. All SSH writes go to RAM, wiped on reboot. Always use `/deploy` or persist manually.

```bash
sudo mount -o remount,rw /media/root-ro
cp /home/pi/<file> /media/root-ro/home/pi/<file>
sudo mount -o remount,ro /media/root-ro
sudo md5sum /home/pi/<file> /media/root-ro/home/pi/<file>
```

---

## 12. CHANGES THIS SESSION

### Firmware (not yet committed)

**`src/eyes/240x240/bigBlue.h`** (line 5306 — PupilParams):
- `{ 0, 0, 0.3, 0.7 }` → `{ 0, 0, 0.24, 0.50 }` (−20% from original 0.3/0.7 → rounded to user spec)

**`src/eyes/240x240/hazel.h`** (line 9303 — PupilParams):
- `{ 0, 0, 0.3, 0.7 }` → `{ 0, 0, 0.25, 0.47 }` (user-specified absolute values)

**`src/eyes/240x240/hypnoRed.h`** (line 5547 — PupilParams):
- `{ 162, 0, 0.3, 0.4 }` → `{ 162, 0, 0.25, 0.50 }` (user-specified absolute values; max expanded)

**`.claude/commands/eye-edit.md`** — Updated manual pupil table to reflect final values (committed in 09ef2fb).

**`src/main.cpp`** — Sleep unresponsiveness fix (flashed this session):
- Added `static uint32_t srMouthLastMs = 0;` (line ~111) — mouth throttle state
- Person sensor guard: `if (hasPersonSensor() && personSensor.read())` → `if (!eyesSleeping && hasPersonSensor() && personSensor.read())` — skips I2C during sleep's heavy SPI load
- Cleaned dead code: removed `if (eyesSleeping && maxSize > 0)` debug block and redundant `if (!eyesSleeping)` inner guard (both unreachable with outer `!eyesSleeping`)
- Sleep block: added 50ms mouth throttle — `if (nowMs2 - srMouthLastMs >= 50) { mouthSleepFrame(); srMouthLastMs = nowMs2; }`

**`src/sleep_renderer.h`** — Sleep unresponsiveness fix (flashed this session):
- `SR_FRAME_MS`: 66 → 150 (15fps → ~6.7fps); keeps loop() free ~58ms between renders for processSerial
- Added heartbeat after `srFrameCount++`: `if ((srFrameCount % 10) == 0) Serial.print("[SR] frame="); Serial.println(srFrameCount);`

### Pi4 Web UI (persisted to SD this session)

**`/home/pi/iris_web.py`** — Added sleep control endpoints:
- `SLEEP_FLAG = "/tmp/iris_sleep_mode"`
- `GET /api/sleep_state` — returns `{"sleeping": bool}`
- `POST /api/sleep` — calls `send_teensy("EYES:SLEEP")`, creates flag file
- `POST /api/wake` — calls `send_teensy("EYES:WAKE")`, removes flag file
- `/api/status` now returns `sleeping` field

**`/home/pi/iris_web.html`** — Eyes tab sleep panel:
- Full sleep control panel with live state dot (indigo glow when sleeping)
- `.btn-sleep` / `.btn-wake` buttons
- `pollSleepState()` every 5s, `updateSleepUI(sleeping)` updates header badge + panel
- System tab shows sleep state field

---

## 13. PENDING ITEMS

### HIGH
- **Sleep fix needs field test** — Flashed but not confirmed working. Key test: activate sleep via web UI, watch serial for `[SR] frame=10`, `[SR] frame=20`, etc. If heartbeats continue but IRIS unresponsive to commands, hang is in processSerial() or mouthSleepFrame(). If heartbeats stop, crash is inside renderSleepFrame() (one of the SPI write calls). Report exact last output.
- **Uncommitted working-copy changes need commit** — src/eyes/240x240/bigBlue.h, hazel.h, hypnoRed.h, src/main.cpp, src/sleep_renderer.h. Run:
  ```bash
  git add src/eyes/240x240/bigBlue.h src/eyes/240x240/hazel.h src/eyes/240x240/hypnoRed.h src/main.cpp src/sleep_renderer.h
  git commit -m "Fix sleep unresponsiveness, reduce frame rate, throttle mouth; reduce pupil sizes"
  ```
- **Wakeword false-trigger during sleep** — assistant.py wakeword-during-sleep handler (line ~1389) does NOT set `_eyes_sleeping = False`. If wakeword triggers, it sends EYES:WAKE but `_eyes_sleeping` stays True in assistant.py, desyncing state from Teensy. Fix: add `_eyes_sleeping = False` in that branch and remove flag file.

### MEDIUM
- **iris_web.py send_teensy() verification** — Confirm whether `send_teensy()` in iris_web.py routes via UDP (port 10500) or attempts direct serial. If direct serial, it conflicts with TeensyBridge; should use `socket.sendto(cmd.encode(), ('127.0.0.1', 10500))` pattern.
- **APA102 indigo breathe during sleep** — On EYES:SLEEP: LEDs to indigo breathe (floor=1, peak=6, period=8s, sine, RGB=(20,0,40)). Add to CMD listener + wakeword sleep handler in assistant.py.
- **config.eye pupil sync** — nordicBlue/hazel/bigBlue/hypnoRed config.eye have old values. Update before next genall.py run (see §7 pupil table).
- **EMOTION:CONFUSED missing from assistant.py** — Add to VALID_EMOTIONS, MOUTH_MAP, emit_emotion().
- **MOUTH:n not sent alongside EMOTION:n** — emit_emotion() should send MOUTH:MOUTH_MAP[X] alongside EMOTION:X.

### LOW
- **EYE:n voice trigger** — Currently web UI only. Add voice: "switch to hazel eyes", etc.
- **Untracked files to commit** — AUDIT_2026-03-27.md, SNAPSHOT_2026-03-28*.md, replacements.txt:
  ```bash
  git add AUDIT_2026-03-27.md SNAPSHOT_2026-03-28*.md replacements.txt SNAPSHOT_2026-03-28e.md
  git commit -m "Add 2026-03-28 audits, snapshots, replacements"
  ```

---

## 14. SLEEP CRASH DIAGNOSIS LOG (for next session)

**What was confirmed:**
- `updateScreen()` in GC9A01A_t3n is fully synchronous — no DMA, confirmed from library source
- `asyncUpdates = false` for both displays (config.h lines 59-60)
- Wire I2C library has 50ms built-in timeout — not the cause of infinite hang
- EyeController.h has no hardware timers or background callbacks
- EYE_DURATION_MS=10000 constant defined but UNUSED in code — not the cause
- `fillBlack()` properly waits for async before writing (moot with async=false)
- Both displays on different SPI buses (SPI0/SPI1) — no bus sharing conflict
- `pending_rx_count` is uint8_t — wraps to 0 after exactly 57600 increments (57600 % 256 = 0)
- `waitTransmitComplete()` loops on pending_rx_count; could theoretically hang if RXMSK set, but RXMSK is not set in normal sync write path

**Root cause NOT conclusively identified through static analysis.** Best hypotheses:
1. **SPI state accumulation:** Full-frame updateScreen (57600 pixels at 20MHz ≈ 46ms) leaves pending_rx_count in indeterminate state. When maybeUpdateTCR() fires a DC-state change, waitTransmitComplete() may spin longer than expected. Reduced frame rate (SR_FRAME_MS=150) gives SPI more idle time between bursts.
2. **I2C interference:** personSensor.read() on I2C during heavy 20MHz SPI — even with 50ms Wire timeout, I2C retries every 70ms during rendering. Now skipped entirely during sleep.
3. **mouthSleepFrame() saturation:** At 0 throttle, bit-bang SPI ran every ~2ms (every loop), preventing serial processing between renders. Now 50ms throttle.

**Next debug step if sleep still crashes:** Watch serial for `[SR] frame=N` heartbeats. If they stop at a specific count, the crash is inside renderSleepFrame(). Add `Serial.flush()` calls before/after each major rendering step (fillScreen, fillCircle batch, updateScreen) to pinpoint exact hang point.

---

## 15. WHAT HAPPENED IN RECENT SESSIONS

### 2026-03-28e (this session)
- Diagnosed sleep unresponsiveness: exhaustive static analysis of GC9A01A_t3n library (updateScreen, waitFifoNotFull, waitTransmitComplete, pending_rx_count), Wire library (50ms timeout confirmed), EyeController (no timers), PersonSensor (I2C polling every 70ms)
- Pupil reductions: bigBlue 0.24/0.50, hazel 0.25/0.47, hypnoRed 0.25/0.50 (all in .h files)
- Web UI sleep infrastructure added (iris_web.py endpoints + iris_web.html panel), persisted to Pi4 SD
- Sleep fix flashed: personSensor skipped during sleep, mouthSleepFrame 50ms throttle, SR_FRAME_MS 66→150, [SR] heartbeat every 10 frames

### 2026-03-28d
- Snapshot-only session. Carried-forward uncommitted changes: [SLEEP] debug in main.cpp, mouthInit intensity fix, CLAUDE.md updates.

### 2026-03-27 (session 2)
- Removed [TRK] debug prints; iris_sleep/wake.py → UDP; squint 0.5→1.0; volume/OWW threshold set.

### 2026-03-27 (session 1)
- Fixed EYES:SLEEP Teensy freeze: updateChangedAreasOnly DMA lockup.
- Fixed vision capture and face tracking (setTargetPosition seed fix, commit ed8fa41).

---

## 16. QUICK REFERENCE

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

**Commit this session's changes:**
```bash
git add src/eyes/240x240/bigBlue.h src/eyes/240x240/hazel.h src/eyes/240x240/hypnoRed.h src/main.cpp src/sleep_renderer.h
git commit -m "Fix sleep unresponsiveness, reduce frame rate, throttle mouth; reduce pupil sizes"
git add AUDIT_2026-03-27.md SNAPSHOT_2026-03-28*.md replacements.txt SNAPSHOT_2026-03-28e.md
git commit -m "Add 2026-03-28 audits, snapshots, replacements"
```

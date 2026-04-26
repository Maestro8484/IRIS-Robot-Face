# IRIS Robot Face — Handoff Snapshot
**Date:** 2026-03-29b
**Branch:** `refactor/modular-assistant`
**Last commit:** `7a6ab8c` (docs: add 2026-03-29 snapshot)
**Repo:** `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face`

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

**Firmware:** Flashed 2026-03-29 (session 2). Sleep fully working. drawChar recursion fixed. 7-eye system. Face tracking working.
**Sleep display:** Starfield + ZZZ animation on both TFTs confirmed working. CONFIRMED via journal at 08:23/08:24.
**Sleep LEDs:** APA102 now switches to dim indigo breathe (floor=1, peak=8, 8s period) on EYES:SLEEP. Restores idle on EYES:WAKE.
**Mouth during sleep:** Snore animation, intensity 0x01 (very dim). Working.
**Wake from webui:** Working. iris_web.py already used UDP correctly. Sleep/wake cycle reliable.
**Voice pipeline (assistant.py):** Operational. ElevenLabs Starter. Modular (hardware/, core/, services/, state/).
**Web UI:** EYE:n switching (0–6), Sleep/Wake buttons, live state polling. Port 5000.
**Face tracking:** Working. setTargetPosition seed fix in EyeController.h.
**Cron sleep:** 9PM/7:30AM. UDP path. Log: /home/pi/iris_sleep.log.

---

## 3. CLAUDE CODE INFRASTRUCTURE

### Slash Commands
| Command | File | Purpose |
|---|---|---|
| `/flash` | `.claude/commands/flash.md` | Local USB flash via PlatformIO |
| `/flash-remote` | `.claude/commands/flash-remote.md` | Remote flash via Pi4 SSH (software 134-baud bootloader entry works — Teensy in enclosure) |
| `/deploy` | `.claude/commands/deploy.md` | Persist Pi4 files through overlayfs to SD |
| `/snapshot` | `.claude/commands/snapshot.md` | Generate end-of-session snapshot |
| `/eye-edit` | `.claude/commands/eye-edit.md` | Eye config edit + genall.py + pupil re-apply workflow |

### Hooks
| Hook | File | Trigger | What it does |
|---|---|---|---|
| SessionStart | `.claude/hooks/session_start.py` | Every session open | Auto-loads latest SNAPSHOT_*.md into context |
| PostToolUse | `.claude/hooks/post_tool_use_build_check.py` | After any Write/Edit to src/ | Runs `pio run` compile check, blocks agent on failure |

### Pi4 Sudoers (all persisted to SD)
- `/etc/sudoers.d/teensy_loader` — passwordless sudo for teensy_loader_cli
- `/etc/sudoers.d/iris_service` — passwordless sudo for systemctl stop/start/restart/status assistant
- `/etc/sudoers.d/iris_backup` — passwordless sudo for mount/umount/mount.cifs
- `/etc/udev/rules.d/49-teensy.rules` — udev rules for HalfKay + serial
- `/usr/bin/teensy_loader_cli` — persisted to SD

### Software Bootloader Entry (Teensy in enclosure — no PROG button access)
```bash
# 134-baud magic triggers HalfKay bootloader — no physical button needed
python3 -c "import serial, time; s=serial.Serial('/dev/ttyACM0',134); time.sleep(0.5); s.close()"
# Verify: lsusb | grep -i teensy  → expect 16c0:0478
```

---

## 4. NAS BACKUP

**Method:** CIFS mount (`//192.168.1.102/BACKUPS` → `/mnt/nas`) + tar directly to mount
**Script:** `/home/pi/iris_backup.sh` (persisted to SD, md5 verified)
**Cron:** Sunday 3AM. Run manually: `sudo bash /home/pi/iris_backup.sh`

---

## 5. REPO STRUCTURE

```
IRIS-Robot-Face/
  src/
    main.cpp                    -- serial parsing, emotion/tracking/sleep logic
    config.h                    -- eye definitions array (7 eyes), display pins
    sleep_renderer.h            -- deep space starfield (SR_FRAME_MS=150)
    TeensyEyes.ino              -- upstream eye engine (DO NOT MODIFY)
    displays/GC9A01A_Display.h  -- display driver + fillBlack + getDriver()
    eyes/EyeController.h        -- eye movement/blink/pupil (setTargetPosition seed fix)
    eyes/240x240/               -- nordicBlue/flame/hypnoRed/hazel/blueFlame1/dragon/bigBlue .h
    sensors/PersonSensor.h/.cpp
    mouth.h                     -- MAX7219 32x8 + mouthSleepFrame() + intensity helpers
  scripts/
    patch_gc9a01a.py            -- PlatformIO pre-build; re-applies drawChar fix after .pio deletion
  /home/pi/ (Pi4, all persisted to SD):
    assistant.py                -- voice pipeline, TeensyBridge, CMD listener (leds now threaded in)
    hardware/teensy_bridge.py   -- single serial owner of /dev/ttyACM0
    hardware/led.py             -- APA102 driver; show_sleep() added (dim indigo breathe)
    iris_sleep.py               -- 9PM cron (UDP only)
    iris_wake.py                -- 7:30AM cron (UDP only)
    iris_web.py                 -- web UI Flask (port 5000); send_teensy() already used UDP
  .claude/commands/             -- flash, flash-remote, deploy, snapshot, eye-edit
  .claude/hooks/                -- session_start.py, post_tool_use_build_check.py
  resources/eyes/240x240/       -- config.eye files (NOT synced to .h manual edits)
```

---

## 6. PLATFORM

```ini
[env:eyes]
platform = https://github.com/platformio/platform-teensy.git
board = teensy40
framework = arduino
monitor_speed = 115200
build_flags = -std=gnu++17 -O2 -D TEENSY_OPT_SMALLEST_CODE
extra_scripts = pre:scripts/patch_gc9a01a.py
lib_deps =
  https://github.com/PaulStoffregen/Wire
  https://github.com/PaulStoffregen/ST7735_t3
  https://github.com/mjs513/GC9A01A_t3n
  adafruit/Adafruit BusIO @ ^1.14.1
  adafruit/Adafruit GFX Library@^1.11.3
```

`scripts/patch_gc9a01a.py` runs before every build and patches `.pio/libdeps/eyes/GC9A01A1_t3n/src/GC9A01A_t3n.h` line 443 — changes the 6-param `drawChar` wrapper to call `drawChar(x,y,c,col,bg,size,size)` (7-param) instead of recursing.

---

## 7. KEY FILE STATE

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

### Pupil values — manual edits (NOT in config.eye — re-apply after genall.py)
| Eye | pupil.min | pupil.max |
|---|---|---|
| nordicBlue | 0.21 | 0.47 |
| hazel | 0.25 | 0.47 |
| bigBlue | 0.24 | 0.50 |
| hypnoRed | 0.25 | 0.50 |

### `src/main.cpp` — Key constants
```cpp
FACE_LOST_TIMEOUT_MS = 5000 | FACE_COOLDOWN_MS = 30000
ANGRY_EYE_DURATION_MS = 9000 | CONFUSED_EYE_DURATION_MS = 7000
EYE_IDX_DEFAULT=0, ANGRY=1, CONFUSED=2, COUNT=7
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
EYES:SLEEP     -- blank displays, start starfield+ZZZ, snore mouth, dim LEDs
EYES:WAKE      -- restore eye, NEUTRAL emotion, restore mouth intensity, restore LEDs
EYE:n          -- switch default eye (0–6)
MOUTH:x        -- set mouth expression
```

**Teensy → Pi4:**
```
FACE:1 / FACE:0           -- person sensor (30s cooldown)
[DBG] EYES:SLEEP -- displays blanked
[DBG] EYES:SLEEP -- starfield starting
[DBG] EYES:WAKE -- displays restored
[DBG] EMOTION cmd: X -> id=N
```

**Rule:** Only `assistant.py` TeensyBridge owns `/dev/ttyACM0`. Everything else uses UDP → `127.0.0.1:10500`.

---

## 9. SLEEP STATE MACHINE

```
EYES:SLEEP received:
  eyesSleeping = true
  blankDisplays()           ← fillScreen(BLACK) + updateScreen() Path B
  mouthSetSleepIntensity()  ← 0x01 (very dim)
  sleepRendererInit()
  leds.show_sleep()         ← dim indigo breathe (floor=1, peak=8, 8s) [Pi4 side]
  "[DBG] EYES:SLEEP -- displays blanked"
  "[DBG] EYES:SLEEP -- starfield starting"

loop() while sleeping:
  processSerial()           ← always runs
  personSensor.read() SKIPPED  ← guarded by !eyesSleeping
  renderSleepFrame()        ← SR_FRAME_MS=150ms, starfield+ZZZ on both TFTs
  mouthSleepFrame()         ← 50ms throttle, snore animation
  return                    ← eye engine skipped

EYES:WAKE received:
  eyesSleeping = false
  mouthRestoreIntensity()   ← 0x05
  setEyeDefinition(saved)
  applyEmotion(NEUTRAL)
  show_idle_for_mode(leds)  ← restores idle LED animation [Pi4 side]
  "[DBG] EYES:WAKE -- displays restored"
```

**Critical — drawChar recursion fix:**
`srDrawZzz()` calls `drawChar(cx, cy, 'Z', col, SR_BLACK, sz)` (6-param).
GC9A01A_t3n.h inline wrapper was calling itself (infinite recursion → stack overflow → hang).
Fixed: wrapper now calls `drawChar(x, y, c, color, bg, size, size)` (7-param Adafruit_GFX).
Fix auto-applied by `scripts/patch_gc9a01a.py` before every build. Also in `.pio/` already.

**Critical — EYES:SLEEP startup timing:**
Teensy needs ~15-20s after reboot before it reliably processes EYES:SLEEP.
If Teensy is stuck in sleep from a previous session, send EYES:WAKE first before EYES:SLEEP.
The 9PM cron runs at a fixed time — if IRIS just rebooted within 15s of 9PM, SLEEP command is lost (rare).

---

## 10. APA102 LED STATE MACHINE

```python
idle         → show_idle()       cyan breathe, peak=65, 5s
kids mode    → show_idle_kids()  yellow breathe, peak=62, 4s
wakeword     → show_wake()       white solid
recording    → show_recording()  red solid
thinking     → show_thinking()   blue chase
speaking     → show_speaking()   green solid
sleep        → show_sleep()      indigo breathe, floor=1, peak=8, 8s  ← NEW
error        → show_error()      red flash x6
followup     → show_followup()   purple pulse
```

Transitions:
- EYES:SLEEP CMD → `leds.show_sleep()`
- EYES:WAKE CMD → `show_idle_for_mode(leds)`
- Wakeword during sleep → `show_idle_for_mode(leds)` (after wake sequence)

---

## 11. ASSISTANT.PY KEY CONFIG (Pi4)

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
**ALSA:** Speaker=120, HP=120, DC/AC=5 | pyaudio device index: **6**

---

## 12. PI4 OVERLAYFS

SD is read-only. All SSH writes go to RAM, wiped on reboot. Always use `/deploy` or persist manually.

```bash
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/<file> /media/root-ro/home/pi/<file>
sudo mount -o remount,ro /media/root-ro
sudo md5sum /home/pi/<file> /media/root-ro/home/pi/<file>
```

---

## 13. CHANGES THIS SESSION (2026-03-29 session 2)

### Pi4 — `/home/pi/hardware/led.py` (persisted, md5 verified)
- Added `show_sleep()` method: very dim indigo breathe, floor=1, peak=8, 8s period
  `self._write([(int(v*0.5), 0, int(v))] * self.n)` — R=half, G=0, B=full for indigo

### Pi4 — `/home/pi/assistant.py` (persisted, md5 verified)
- `start_cmd_listener(teensy)` → `start_cmd_listener(teensy, leds)` — leds threaded in
- EYES:SLEEP handler: added `leds.show_sleep()`
- EYES:WAKE handler: added `show_idle_for_mode(leds)`
- Call site at line 422 updated: `start_cmd_listener(teensy, leds)`

### Firmware — rebuilt + reflashed (2026-03-29 session 2)
- `scripts/patch_gc9a01a.py` applied drawChar fix before build
- Verified: `drawChar(x, y, c, color, bg, size, size)` at line 443 of GC9A01A_t3n.h
- Flash confirmed via paramiko SFTP + teensy_loader_cli; software 134-baud bootloader entry used
- Post-flash test (direct serial): EYES:SLEEP → both DBG lines confirmed
- Post-flash test (via assistant): full sleep/wake cycle confirmed working at 08:23–08:24

### Pi4 — `libusb-0.1-4` (persisted to SD, from previous session in this context)
- Library files + dpkg info + dpkg status stanza all persisted to /media/root-ro

---

## 14. PENDING ITEMS

### MEDIUM

- **EYES:SLEEP startup timing** — 9PM cron sends UDP immediately. If IRIS rebooted within ~15s of 9PM, command is lost. Fix: add `sleep 20` to top of `iris_sleep.py`.
- **config.eye pupil sync** — nordicBlue/hazel/bigBlue/hypnoRed config.eye have old values. Update before next `genall.py` run.
- **EMOTION:CONFUSED missing from assistant.py** — Add to VALID_EMOTIONS, MOUTH_MAP, emit_emotion().
- **MOUTH:n not sent alongside EMOTION:n** — emit_emotion() already sends it (line 158: `teensy.send_command(f"MOUTH:{MOUTH_MAP.get(emotion, 0)}")`). Verify MOUTH_MAP is complete.

### LOW

- **EYE:n voice trigger** — web UI only currently.
- **Untracked files** — REFACTOR_VISUAL.md, _decode_assistant.py: commit when convenient.

---

## 15. FLASH WORKFLOW (Pi4 SSH remote)

```bash
# 1. Build (patch script auto-applies drawChar fix)
cd C:/Users/SuperMaster/Documents/PlatformIO/IRIS-Robot-Face && pio run

# 2. Upload hex via paramiko (scp doesn't work — no pubkey auth from desktop)
python3 -c "
import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.200', username='pi', password='ohs')
ssh.open_sftp().put('.pio/build/eyes/firmware.hex', '/tmp/iris_firmware.hex')
ssh.close(); print('done')
"

# 3. Stop assistant
ssh pi@192.168.1.200 "sudo systemctl stop assistant"  # (use MCP ssh if pubkey fails)

# 4. Software bootloader entry
# Via MCP SSH: python3 -c "import serial,time; s=serial.Serial('/dev/ttyACM0',134); time.sleep(0.5); s.close()"
# Verify: lsusb | grep -i teensy  → 16c0:0478

# 5. Flash
# Via MCP SSH: sudo teensy_loader_cli --mcu=TEENSY40 -w -v /tmp/iris_firmware.hex

# 6. Start assistant
# Via MCP SSH: sudo systemctl start assistant

# 7. IMPORTANT: Wait 15-20s, then send EYES:WAKE before EYES:SLEEP if Teensy may be in sleep state
```

---

## 16. PI4 QUICK COMMANDS

```bash
# Restart assistant
sudo systemctl restart assistant

# Watch live logs
journalctl -u assistant -f --no-pager | grep -v "ALSA\|Jack\|pulse\|seeed\|pcm\|conf\|hdmi\|modem"

# Test sleep/wake
python3 -c "import socket; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.sendto(b'EYES:WAKE',('127.0.0.1',10500))"
python3 -c "import socket; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.sendto(b'EYES:SLEEP',('127.0.0.1',10500))"

# Direct serial diagnostic (assistant must be stopped)
python3 -c "
import serial, time
s = serial.Serial('/dev/ttyACM0', 115200, timeout=0.5, dsrdtr=False, rtscts=False)
time.sleep(0.2); s.write(b'EMOTION:NEUTRAL\n'); s.flush()
deadline = time.time()+5
while time.time()<deadline:
    l=s.readline()
    if l: print('GOT:', l.decode(errors='ignore').strip())
s.close()
"

# Persist file to SD
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/<file> /media/root-ro/home/pi/<file>
sudo mount -o remount,ro /media/root-ro
sudo md5sum /home/pi/<file> /media/root-ro/home/pi/<file>
```

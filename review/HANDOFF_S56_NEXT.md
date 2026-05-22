# IRIS — Session Handoff S56 → Next Session
**Date:** 2026-05-21 | **Branch:** main | **Last commit:** ca4c395

Copy-paste this entire file into a new Claude Code session.

---

## Session Start Block

```
Branch: main
Last commit: ca4c395 — S56: servo controller — Teensy 4.0 replaces dead Pico W
Working tree: clean (verify with git status before proceeding)
Task: HW-002 — Flash Teensy 4.0 servo controller + deploy assistant.py to Pi4
Files to modify: pi4/assistant.py (deploy only — no code changes), pi4/services/wakeword.py (confirm deployed)
Risk: assistant.py rename (start_pico_listener → start_servo_listener) must match deployed file exactly
Rollback: git checkout ca4c395~1 -- pi4/assistant.py && redeploy
```

---

## What Happened in S56

- Pico W (previous servo controller) confirmed dead — no USB enumeration on Pi4 or Windows.
- Replaced with Teensy 4.0 (COM11 on Windows, data cable confirmed working).
- Firmware updated for Teensy 4.0: `Wire.begin()` (fixed I2C pins 18/19), `panServo.attach(9)`.
- `platformio.ini` updated: `env:teensy40`, `platform = teensy`, `board = teensy40`.
- `pi4/assistant.py`: `start_pico_listener()` renamed to `start_servo_listener()`, `[PICO]` log prefix → `[SERVO]`, `PICO_PORT/PICO_BAUD` → `SERVO_PORT/SERVO_BAUD`.
- `pi4/iris_web.py`: docstrings updated — Pico W → Teensy 4.0.
- All docs updated: `IRIS_ARCH.md`, `ROADMAP.md`, `docs/IRIS_INVENTORY.md`, `docs/servo_pico_wiring.md`, `SNAPSHOT_LATEST.md`, `HANDOFF_CURRENT.md`.
- All changes REPO-ONLY — nothing deployed to Pi4 yet.

---

## Current System State

| System | Status |
|---|---|
| Pi4 | Operational — assistant.py has OLD code (`start_pico_listener`, `[PICO]`). Deploy needed. |
| Teensy 4.1 (eyes) | Operational — /dev/ttyACM0 |
| Teensy 4.0 (servo) | NOT YET WIRED OR FLASHED — REPO-ONLY. COM11 on Windows. |
| GandalfAI | Operational |
| Servo | Not moving — Teensy 4.0 not yet wired to servo or sensors |

---

## Required Pre-Flight (before any action)

1. `git status` — must be main, clean tree
2. Read `SNAPSHOT_LATEST.md` lines 1–50
3. Read `HANDOFF_CURRENT.md`
4. Read `IRIS_ARCH.md` section "Servo Pan Controller — Teensy 4.0"
5. SSH Pi4 (`ssh-pi4` MCP, 192.168.1.200, pi/ohs, password auth only) — confirm `/dev/ttyACM0` exists, `/dev/ttyACM1` absent

---

## Task: HW-002 — Flash + Rewire + Deploy

### Step 1 — Hardware (user action, before Claude does anything)

Rewire PCB for Teensy 4.0:

| Wire | From | To |
|---|---|---|
| Servo PWM signal | Teensy 4.0 pin 9 | Servo yellow/orange |
| I2C SDA | Teensy 4.0 pin 18 | Person Sensor SDA + APDS-9960 SDA |
| I2C SCL | Teensy 4.0 pin 19 | Person Sensor SCL + APDS-9960 SCL |
| Sensor VCC | Teensy 4.0 3.3V pin | Person Sensor VCC + APDS-9960 VCC |
| GND | Teensy 4.0 GND | Sensor GND bus |
| USB | Teensy 4.0 micro-USB | Pi4 USB port (data cable — confirmed working) |
| Servo 5V | Toggle switch output | Servo red wire (unchanged) |
| Servo GND | Supply GND | Servo black wire (unchanged) |

Also: cut HW-001 LED/SCK solder jumper on Teensy 4.1 underside while PCB is open.

### Step 2 — Flash Teensy 4.0 (user action)

1. Open PlatformIO → `servo_pico/IRIS-BaseServoControlViaPerson_Sensor`
2. Select environment `env:teensy40`
3. Claude runs: `cd "C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face\servo_pico\IRIS-BaseServoControlViaPerson_Sensor" && pio run`
4. User clicks **Upload** in PlatformIO (Teensy 4.0 on COM11)
5. Confirm orange LED steady on Teensy 4.0 after flash

### Step 3 — Verify Teensy 4.0 on Pi4 (Claude runs via ssh-pi4)

```bash
ls /dev/ttyACM*
# Expected: /dev/ttyACM0 (Teensy 4.1) and /dev/ttyACM1 (Teensy 4.0)

timeout 10 cat /dev/ttyACM1
# Expected: WARN: APDS-9960 not found (if sensor not yet wired)
# OR: normal polling output if sensors are wired
```

### Step 4 — Deploy assistant.py to Pi4

**File:** `pi4/assistant.py` (REPO-ONLY — `start_servo_listener`, `[SERVO]` prefix)
**Pi4 path:** `/home/pi/assistant.py`

Standard persist protocol:
```bash
# Claude writes file via sftp, then:
sudo cp /tmp/assistant.py /home/pi/assistant.py
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
sudo chown pi:pi /media/root-ro/home/pi/assistant.py
sudo chmod 644 /media/root-ro/home/pi/assistant.py
sync
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
sudo systemctl restart assistant
journalctl -u assistant -n 30 --no-pager
```

Also check `pi4/services/wakeword.py` — confirm `/tmp/iris_manual_listen` flag check is present (was confirmed in S55 but not deployed this session).

### Step 5 — Verify

```bash
# SSH Pi4 — tail logs and trigger gestures on APDS-9960
journalctl -u assistant -f
# Expected log lines:
# [SERVO] Connected on /dev/ttyACM1
# [SERVO] VOL_UP (on UP gesture)
# [SERVO] STOP (on LEFT/RIGHT gesture)
# [SERVO] LISTEN (on proximity hold)
```

---

## Other Pending Work (do not start without user instruction)

### Teensy 4.1 Firmware Flash (separate task)
- Commit: `af66b24` — BL_MAP log curve + idle animations — REPO-ONLY
- Flash via PlatformIO upload (main project, `env:eyes`, user clicks upload)
- Teensy 4.1 USB → SuperMaster (COM7)
- Verify: sleep=dark, idle=dim L3, wakeword=bright, post-speech=dim

### GandalfAI (separate task)
- Set `OLLAMA_KEEP_ALIVE=30m` on GandalfAI + restart Ollama service

### HW-001 — Teensy 4.1 LED jumper cut
- Physical mod only. No code. Do during PCB open session for HW-002 rewiring.

---

## Key References

| File | Purpose |
|---|---|
| `IRIS_ARCH.md` | System architecture, all machine credentials, pin tables, deploy commands |
| `docs/servo_pico_wiring.md` | Teensy 4.0 wiring iteration 5 pin table |
| `docs/IRIS_INVENTORY.md` | Node list, GPIO tables, service ports, key file paths |
| `ROADMAP.md` | HW-002, HW-001, RD-009 full specs |
| `pi4/assistant.py` | `start_servo_listener()` at line ~164; called in `main()` at line ~396 |
| `pi4/services/wakeword.py` | `/tmp/iris_manual_listen` flag check |
| `pi4/iris_web.py` | `/api/stop`, `/api/listen` routes |

---

## System Credentials (do not commit — from IRIS_ARCH.md)

| System | IP | Auth | MCP tool |
|---|---|---|---|
| Pi4 | 192.168.1.200 | pi / ohs (password only, key auth fails) | ssh-pi4 |
| GandalfAI | 192.168.1.3 | gandalf / 5309 | ssh-gandalf (PowerShell) |
| SuperMaster | 192.168.1.103 | SuperMaster / ohs | ssh (PowerShell) |

---

## Session Close Requirements (for next Claude session)

Per `CLAUDE.md`:
```
Repo status:
GitHub status:
Pi4 live status:
Teensy 4.1 firmware status:
Teensy 4.0 (servo) firmware status:
GandalfAI model status:
Live IRIS behavior right now:
Remaining steps before user-visible behavior changes:
```

Pi4 deploy checklist (every file change):
- [ ] RAM layer updated
- [ ] SD layer persisted via /media/root-ro
- [ ] md5 verified (RAM == SD)
- [ ] Service restarted
- [ ] Logs checked post-restart

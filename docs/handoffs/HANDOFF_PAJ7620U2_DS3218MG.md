IRIS project. Claude Code on SuperMaster Desktop.
Filesystem MCP active. SSH MCP active (ssh-pi4, ssh-gandalf).

Repo: C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face
GitHub is secondary mirror. Local repo is always source of truth.

Read CLAUDE.md first. It contains all session rules, hard constraints,
pre-flight format, deploy gates, and protected files. Do not proceed
without reading it.

Read the minimum files the task requires. State which files you read
and why. If broader context is needed, name the files and justify
before reading them.

TASK:
Replace dead APDS-9960 gesture sensor driver with PAJ7620U2 in the Teensy 4.0
base mount firmware, and tune pan servo constants for DS3218MG. Update all
affected docs. Deploy firmware build is REPO-ONLY (user performs PlatformIO
upload). No Pi4 or GandalfAI changes required.

LIKELY FILES:
(hints only -- read before editing, never write from memory)
- servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino  (primary)
- servo_teensy40/teensy40_base_mount/platformio.ini
- servo_teensy40/README.md
- docs/servo_teensy40_wiring.md
- docs/sysmap.json  (apply patch from docs/sysmap_patch_2026-05-27.md)
- HANDOFF_SERVO_TUNING.md

CONTEXT:
Hardware state confirmed 2026-05-27:
- APDS-9960 (0x39): confirmed dead (S66). I2C no-response, 0x0 from ID register.
  Physically removed. Remove all driver code, SparkFun_APDS9960 library, and
  every reference to APDS-9960 or 0x39 from firmware and platformio.ini.
- PAJ7620U2 (HiLetgo, 0x73): physically installed on same I2C bus
  (Teensy 4.0 pins 18/19, shared with Person Sensor 0x62). INT unconnected.
  Polling mode. Confirm I2C ACK at 0x73 before writing driver.
- DS3218MG (Miuzei, 25kg metal gear): installed on pin 2, same external 5V rail.
- Gesture serial output contract is fixed -- base_mount_bridge.py on Pi4 depends
  on these exact strings, do not change them:
    UP    -> Serial.println("VOL+")
    DOWN  -> Serial.println("VOL-")
    LEFT  -> Serial.println("STOP")
    RIGHT -> Serial.println("STOP")
- PAJ7620U2 has no proximity channel. Remove PROX_LISTEN_THRESHOLD, PROX_HOLD_MS,
  and all proximity LISTEN logic. LISTEN is touch3 only (already in firmware).
- DS3218MG starting constants:
    PAN_SPEED      0.02   (was 0.04)
    PAN_DEAD_ZONE  5.0    (was 2.0)
    FACE_HOLD_MS   2500   (unchanged)
    FACE_RETURN_MS 6000   (was 8000)
  Easing: keep EASE_CUBIC_OUT tracking, EASE_SINE_OUT return.
- SERIAL_DIAG: leave at 1. User sets to 0 after hardware confirmed stable.
- PAJ7620U2 library: confirm exact PlatformIO registry name before writing
  platformio.ini. If no suitable library found, implement bare I2C init
  (write 0xEF 0x00, then 0xEF 0x01, load bank1 config registers per datasheet)
  and gesture result read from register 0x43.
- docs/sysmap_patch_2026-05-27.md: contains 6 targeted field-level patches for
  sysmap.json. Apply all of them this session.

ENVIRONMENT:
- Claude Desktop chat (filesystem MCP + ssh-pi4 MCP available)
- Repo: C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face
- Pi4: 192.168.1.200 (deploy target — deploy is part of task completion; say REPO-ONLY to defer)
- GandalfAI: 192.168.1.3 (models/TTS — model rebuilds deploy automatically; say REPO-ONLY to defer)
DISCOVERY PHASE (read minimum to complete task):
1. SNAPSHOT_LATEST.md first 80 lines — always
2. HANDOFF_CURRENT.md — always. If any files are marked REPO-ONLY for Pi4 or
   GandalfAI, list them and deploy them before starting new work unless user
   says REPO-ONLY or SKIP.
3. CLAUDE.md — always
4. Task-relevant source files only
5. docs/MAESTRO_QUICKREF.md — only if file mapping unclear
6. docs/iris_issue_log.md — only if similar issue suspected
ON DEMAND (not by default):
- docs/sysmap.json: ports, IPs, GPIO pins, file paths, config key defaults — read this BEFORE IRIS_ARCH.md or IRIS_CONFIG_MAP.md for any lookup task
- IRIS_ARCH.md: only if architectural reasoning, pipeline design, or failure mode context needed — not for lookups
- IRIS_CONFIG_MAP.md: only if sysmap.json does not contain the config detail needed
- docs/servo_teensy40_wiring.md: required for this task
- HANDOFF_SERVO_TUNING.md: required for this task
- README.md: never
- Old snapshots/handoffs: never
SKIP DISCOVERY IF:
- User says SKIP / GO / JUST DO IT
- User provides file:line reference
IMPLEMENTATION:
- Read live files before editing — never write from memory
- Group related edits, apply atomically
- State deploy scope after each change: REPO-ONLY / Pi4 / Teensy / GandalfAI
SESSION CLOSE:
- Before ending, state how many files are REPO-ONLY for Pi4 or GandalfAI.
- If any remain REPO-ONLY, state why (user deferred, hardware unavailable, etc.)
  and carry forward in HANDOFF_CURRENT.md.
- Update HANDOFF_CURRENT.md and SNAPSHOT_LATEST.md to reflect actual deploy state.
- Do not mark any change DEPLOYED unless it was deployed this session.
- Teensy firmware changes are always REPO-ONLY at session close; user performs
  PlatformIO upload. Note this explicitly in session close report.
INTERACTION:
- No preamble, no trailing summaries
- No em dashes, no AI filler
- No explanations unless asked
DO NOT:
- Hardcode /dev/ttyACM* in any code, config, Pi4 command, or doc — use /dev/ttyIRIS_EYES (Teensy 4.1) or /dev/ttyIRIS_SERVO (Teensy 4.0)
- Push to GitHub without explicit PUSH command
- Modify protected files (iris_config.json, alsa-init.sh, TeensyEyes.ino, EyeController.h) without explicit instruction
- Read git history unless merge conflict suspected
- Start new feature work on top of undeployed Pi4/GandalfAI changes without
  explicit user acknowledgment that stacking is intentional

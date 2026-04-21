# IRIS Robot Face — Claude Code Rules

## What this is
A production hardware-integrated AI system. Changes here affect physical hardware running in a home with two children. Read the current state before touching anything. Verify before acting. When uncertain, stop and ask.

Session start: read SNAPSHOT_LATEST.md (auto-loaded by hook). If missing, run `python3 .claude/hooks/session_start.py`. Then run `git pull origin main`.

> **Claude Chat vs Claude Code tool scope:** Claude Chat (claude.ai) has filesystem MCP scoped to `C:\Users\SuperMaster\` and ssh-pi4/ssh-gandalf MCP tools for live SSH access. Claude Code (Desktop) has the same MCP tools plus full repo write access. Claude Chat is used for planning, diagnosis, and targeted live fixes (e.g. iris_config.json). Claude Code handles all multi-step implementation, firmware builds, and deployments. When in doubt: Chat = read + plan, Code = write + deploy.

> **Snapshot gitignore history:** SNAPSHOT*.md was gitignored until S26 (2026-04-20). User-confirmed task completions between sessions were not persisted to git during that period. Snapshot is authoritative from S27 forward. If a task seems stale or contradicted by live system state, verify against the live system rather than trusting older snapshot entries.

---

## System architecture

Three machines. Each has a defined role. Work stays within that role.

**Pi4 (192.168.1.200, pi/ohs)**
Runs the voice pipeline via `assistant.py`. The Pi4 is a thin orchestrator: it captures audio, detects the wakeword via OWW, records speech, sends it to GandalfAI for STT and LLM, receives the reply, drives Teensy serial and APA102 LEDs, and plays audio back. All intelligence and inference lives on GandalfAI. Pi4 Python source lives in `pi4/` in this repo, mirroring `/home/pi/` exactly. The Pi4 SD card is overlayfs-protected -- every file write needs to go to both the RAM layer and the SD layer, with md5 verification.

**GandalfAI (192.168.1.3, gandalf/5309)**
Windows machine. Runs Ollama (LLM inference), Wyoming Whisper (STT, port 10300), Wyoming Piper (TTS fallback, port 10200), and Chatterbox (primary TTS, port 8004) via Docker. RTX 3090 (24GB VRAM). Canonical LLM modelfiles are in `ollama/` in this repo. Deploy by writing the modelfile and running `ollama create`. GandalfAI uses PowerShell -- no bash, no grep, no df, no head. Use sftp_write for multi-line file writes. filesystem MCP covers `C:\Users\gandalf\` only; use ssh_exec for `C:\IRIS\` and `C:\docker\`.

**SuperMaster Desktop (192.168.1.103)**
Firmware builds and git push only. PlatformIO runs here. Claude runs `pio run`. User clicks upload. Git push to origin runs here and only here -- never from GandalfAI or any other machine.

**Teensy 4.1 (USB to SuperMaster)**
Drives dual GC9A01A eye TFTs and ILI9341 mouth TFT. Receives serial commands from Pi4 via TeensyBridge. Firmware source in `src/`. Claude builds only -- user flashes manually via PlatformIO upload button.

---

## VRAM budget (GandalfAI RTX 3090, 24GB)

Chatterbox holds ~4.5GB resident. Current LLM is gemma3:12b at ~7GB (num_ctx 4096). Combined ~11.5GB, leaving ~12.5GB headroom. Headroom below 4GB causes inference stalls -- pipeline appears dead after wakeword with no audio output. Do not increase num_ctx above 4096. When evaluating a model change, verify the combined VRAM budget fits with at least 4GB headroom. Stop token for gemma family: `<end_of_turn>`. After any modelfile change, rebuild both `iris` and `iris-kids` and smoke test before considering the task done.

Smoke test: `[EMOTION:x]` tag on first line, response completes without mid-sentence cutoff, plain sentences, no markdown.

---

## Git and snapshot discipline

`main` is the only branch. No feature branches, no worktrees, no Claude-created branches under any circumstances. Session start: verify `git branch --show-current` outputs `main`. If not, fix it before proceeding.

`SNAPSHOT_LATEST.md` is the single source of truth for current system state. It is tracked in git. One file, no dated variants, updated once at session close via `/snapshot`.

Session end sequence:
1. State what changed, what did not, any new risks.
2. `git add -A && git commit -m "[message]"`
3. Run `/snapshot`
4. `git add SNAPSHOT_LATEST.md && git commit -m "snapshot: S##"`
5. Tell user to run `git push origin main` from SuperMaster Desktop.

> **Git push rule — ABSOLUTE:** All `git push` commands originate from SuperMaster Desktop PC only. Claude Code never pushes autonomously. Claude Chat cannot push (no git execution). At every session end, Claude must explicitly prompt: "Ready to push — run this in PowerShell on SuperMaster:" followed by the exact command. Do not assume the push happened. If the user has not confirmed the push, the session is not closed.

> **Doc update confirmation rule:** At the end of any session where SNAPSHOT_LATEST.md, IRIS_ARCH.md, or CLAUDE.md were modified — whether by Claude Code, Claude Chat via filesystem MCP, or manually — Claude must ask: "Docs updated. Have you pushed to origin?" before closing. If the user has not explicitly confirmed a push in the current session, prompt for it. Claude Chat sessions that modify docs via filesystem MCP must flag this explicitly since they cannot push themselves.

---

## Pre-flight (run at every session start, output before touching anything)

> Branch: [current branch -- must be main]
> Last commit: [hash + message]
> Working tree: [clean / dirty -- if dirty, stop and tell user]
> Task this session: [one sentence]
> Files to be modified: [explicit list]
> Files NOT touched: [everything else relevant]
> Risk: [what could break]
> Rollback: [how to undo]

Wait for user confirmation before proceeding. If the working tree is dirty, do not proceed until the user commits or explicitly clears it.

---

## Session discipline

One task per session. State it at the top. Do not fix other things noticed along the way -- log them to the snapshot instead. No file writes without showing the plan first. Read the live file before writing it -- never write from memory or a reconstructed version. Return full files, not snippets.

Files that require explicit user instruction before touching: `iris_config.json`, `alsa-init.sh`, `src/TeensyEyes.ino`, `src/eyes/EyeController.h`.

---

## Pi4 file locations

All Pi4 Python source is edited in `pi4/` in this repo. The `pi4/` directory mirrors `/home/pi/` exactly. Read from `pi4/`, deploy to `/home/pi/`, persist to `/media/root-ro/home/pi/`, verify with md5sum.

| Repo | Pi4 |
|---|---|
| `pi4/assistant.py` | `/home/pi/assistant.py` |
| `pi4/core/config.py` | `/home/pi/core/config.py` |
| `pi4/services/tts.py` | `/home/pi/services/tts.py` |
| `pi4/services/stt.py` | `/home/pi/services/stt.py` |
| `pi4/services/wyoming.py` | `/home/pi/services/wyoming.py` |
| `pi4/services/wakeword.py` | `/home/pi/services/wakeword.py` |
| `pi4/services/llm.py` | `/home/pi/services/llm.py` |
| `pi4/services/vision.py` | `/home/pi/services/vision.py` |
| `pi4/hardware/audio_io.py` | `/home/pi/hardware/audio_io.py` |
| `pi4/hardware/led.py` | `/home/pi/hardware/led.py` |
| `pi4/hardware/teensy_bridge.py` | `/home/pi/hardware/teensy_bridge.py` |
| `pi4/hardware/io.py` | `/home/pi/hardware/io.py` |
| `pi4/state/state_manager.py` | `/home/pi/state/state_manager.py` |
| `pi4/iris_sleep.py` | `/home/pi/iris_sleep.py` |
| `pi4/iris_wake.py` | `/home/pi/iris_wake.py` |

The SD layer at `/media/root-ro` is read-only by default. Remount with `sudo mount -o remount,rw /media/root-ro` before writing. `/tmp/iris_sleep_mode` is intentionally volatile -- do not persist it.

---

## Firmware

`src/TeensyEyes.ino` is upstream engine -- do not modify. `src/eyes/EyeController.h` contains a setTargetPosition seed fix -- do not break it. After any `src/` change, run `pio run` and tell the user to click upload. Software bootloader entry when Teensy is in enclosure:
```
python3 -c "import serial, time; s=serial.Serial('/dev/ttyACM0',134); time.sleep(0.5); s.close()"
```

See IRIS_ARCH.md for pin assignments, eye index, and mouth TFT wiring.

---

## Handoff template (Claude Chat -> Claude Code)

**Task:** [One sentence.]
**Environment:** [Pi4 | GandalfAI | Firmware | Multi]
**Files:** [Only files being read or modified]
**Issue ref:** [Active Issues label from SNAPSHOT_LATEST.md]

**Change spec:**
[filepath]: [what changes -- specific function or behavior, not architecture summary]

**Verify:** [One observable pass/fail outcome]
**Commit:** "[message]"
**After commit:** Run /snapshot. Tell user to git push from SuperMaster.

One environment per session. If a task spans more than two files across different subsystems, split it and say so.

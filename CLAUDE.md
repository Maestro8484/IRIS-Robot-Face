# IRIS Robot Face — Claude Code Rules

## Session start
The SessionStart hook auto-loads SNAPSHOT_LATEST.md before every session.
If context seems missing, run: `python3 .claude/hooks/session_start.py`

You are working on a production hardware-integrated AI system. Mistakes here break
physical hardware and require SSH recovery. Read before acting.

---

## Branch discipline — HARD RULE, NO EXCEPTIONS
Always work on `main` directly. No feature branches. No Claude-created branches. No worktrees.
NEVER run git checkout -b, git switch -c, or any command that creates a branch or worktree.
NEVER create a branch or worktree autonomously for any reason.

Session start mandatory check:
  git branch --show-current   <- must output exactly: main
  If NOT main: git checkout main, delete wrong branch, report to user, wait for confirmation.
  git worktree list           <- must show only the main worktree
  If any claude/* worktrees exist: git worktree remove --force <path>, git worktree prune

## Git discipline
Session start: git pull origin main
Session end: git add -A && git commit && git push origin main (push requires user confirmation)

---

## Pre-flight (mandatory at every session start -- output this before touching anything)

> Branch: [current branch]
> Last commit: [hash + message]
> Working tree: [clean / dirty -- if dirty STOP and tell user]
> Task this session: [one sentence]
> Files to be modified: [explicit list]
> Files NOT touched: [everything else relevant]
> Risk: [what could break]
> Rollback: [how to undo]

Do not proceed until user confirms. If working tree is dirty, do not proceed until user commits or explicitly clears it.

---

## Hard rules -- no exceptions
- ONE task per session. No opportunistic fixes. No "while I'm in here" changes.
- No refactoring unless the session task IS refactoring -- state it explicitly upfront.
- No file writes without showing the plan first and getting user confirmation.
- git push requires explicit user confirmation before running.
- Never touch these files without explicit user instruction:
  - iris_config.json
  - alsa-init.sh
  - Any file not directly named in the confirmed task scope

---

## Machine rules
SuperMaster: firmware builds and PlatformIO only. Claude runs pio run only. User clicks upload. Never remote flash.
GandalfAI: pi4/ and snapshot work only. Never touch src/ firmware files. No pio commands. No firmware builds.
GandalfAI filesystem MCP: C:\Users\gandalf\ only. Use Bash tool for C:\IRIS\ and C:\docker\.
GandalfAI: PowerShell only. No grep/df/head. Heredocs unreliable -- use sftp_write for multi-line files.
Ollama models: `jarvis` and `jarvis-kids` -- both built on `mistral-small3.2:24b` Q4_K_M (24B params, 14GB disk, 17.1GB VRAM). Canonical modelfiles in `ollama/` in this repo. To rebuild: `ollama create jarvis -f C:\IRIS\IRIS-Robot-Face\ollama\jarvis_modelfile.txt`

---

## Snapshot discipline
SNAPSHOT_LATEST.md is the single authoritative file.
No dated variants. No lettered variants.
Update once at session close only via /snapshot.
Never update mid-session.

---

## CRITICAL: Pi4 source location

ALL Pi4 Python files are edited in `pi4/` in this repo.
`pi4/` mirrors the Pi4 filesystem at `/home/pi/` exactly.

| Repo path | Pi4 path |
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

**NEVER read from or write to a root-level `assistant.py`. It does not exist.**
**NEVER deploy any Pi4 file that was not explicitly read from `pi4/` this session.**
**NEVER deploy from memory, a snippet, or a reconstructed version.**

---

## Rules
- Do NOT guess pins, ports, device paths, or hardware behavior
- Do NOT refactor multiple systems at once
- Preserve current behavior unless explicitly told to change it
- Only modify files explicitly mentioned in the task
- Return FULL updated files, not partial snippets
- If uncertain, stop and ask instead of guessing

---

## Architecture

`pi4/assistant.py` is a THIN orchestrator only (~340 lines).
All logic lives in modules. Do not inline anything that belongs in a module.

- `pi4/core/config.py` — all constants + iris_config.json override loader
- `pi4/services/stt.py` — Wyoming Whisper STT (`data_length` payload parser -- do not rewrite inline)
- `pi4/services/tts.py` — Chatterbox -> ElevenLabs -> Piper routing
- `pi4/services/wakeword.py` — OWW + GPIO button handler
- `pi4/services/llm.py` — `stream_ollama()` (streaming main path), `ask_ollama()` (followup/vision), emotion tag extraction, reply cleaning
- `pi4/services/vision.py` — camera capture + vision query
- `pi4/hardware/audio_io.py` — PCM playback, record, beep, interrupt detection
- `pi4/hardware/led.py` — APA102 driver
- `pi4/hardware/teensy_bridge.py` — single serial owner of `/dev/ttyACM0`
- `pi4/state/state_manager.py` — runtime state singleton (`state.kids_mode`, `state.eyes_sleeping`, etc.)

Serial owner rule: only TeensyBridge owns `/dev/ttyACM0`. Everything else uses UDP -> `127.0.0.1:10500`.

---

## Deploy workflow

**Always follow this order. Never skip steps.**

1. Read the file from `pi4/` in the repo -- confirm it is correct before touching Pi4
2. Write to `/home/pi/<path>` on Pi4 via SSH
3. Persist to SD:
```bash
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/<file> /media/root-ro/home/pi/<file>
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/<file> /media/root-ro/home/pi/<file>
```
4. Verify md5 matches -- if not, repeat step 3
5. `sudo systemctl restart assistant`
6. `journalctl -u assistant -n 30 --no-pager` -- confirm `[INFO] Ready.` before closing

Or use the `/deploy` command which enforces this sequence.

---

## Pi4 persistence (overlayfs)
- SD is read-only. All SSH writes go to RAM and are wiped on reboot.
- ALWAYS persist after every SSH file write.
- `sudo cp` is required -- files on `/media/root-ro` are root-owned.
- Do NOT persist `/tmp/iris_sleep_mode` -- intentionally volatile.

---

## Firmware rules
- Do NOT modify `TeensyEyes.ino` -- upstream engine, off limits.
- After any `src/` change: run `/flash` (local USB) or `/flash-remote` (Pi4 SSH).
- Software bootloader entry (Teensy in enclosure, no PROG button access):
```bash
python3 -c "import serial, time; s=serial.Serial('/dev/ttyACM0',134); time.sleep(0.5); s.close()"
```

---

## Eye editing workflow
1. Edit `resources/eyes/240x240/<eye>/config.eye`
2. Run `python resources/eyes/240x240/genall.py` to regenerate `.h` files
3. Re-apply pupil values manually to nordicBlue.h, hazel.h, bigBlue.h after every genall.py run
   (genall.py resets them -- manual values are not in config.eye)
4. PlatformIO upload

---

## Serial protocol
- Pi4 -> Teensy: `EMOTION:x`, `EYES:SLEEP`, `EYES:WAKE`, `EYE:n` (0-6), `MOUTH:n`
- Teensy -> Pi4: `FACE:1`, `FACE:0`

---

## Key firmware files
- `src/main.cpp` — serial parsing, emotion, tracking, sleep logic
- `src/eyes/EyeController.h` — eye movement/blink/pupil (do NOT break setTargetPosition seed fix)
- `src/mouth_tft.cpp` / `src/mouth_tft.h` — ILI9341 TFT mouth driver (Arduino_GFX SWSPI bit-bang, T4.1 pins MOSI=35, SCK=37, CS=36, DC=8, RST=4, BL=14)
- `src/sleep_renderer.h` — deep space starfield renderer

---

## Long output
- Snapshots, full file dumps, large summaries -> write to a `.md` file, then summarize inline.
- Never print large content blocks as chat -- truncation loses data.

---

## Workflow rules

- Claude Chat = diagnosis, log reading, planning only. No file writes, no SSH command chains.
- Claude Code = all file writes, SSH chains, implementation, service restarts.
- Every Code session opens with: read CLAUDE.md, confirm live state matches declared state, report any drift before acting.
- One session, one concern. State the single goal at session open.
- Smoke test mouth TFT before any further firmware or voice pipeline work.
- Mouth smoke test route: Pi4 SSH -> send `MOUTH:0` through `MOUTH:8` via UDP `127.0.0.1:10500` -> TeensyBridge -> `/dev/ttyACM0` -> Teensy renders on TFT.
- Flash rule: Claude runs `pio run` only. User clicks PlatformIO upload. Never remote flash.
- Canonical Pi4 source: `pi4/assistant.py` only. Never read or write root-level `assistant.py`.
- SNAPSHOT_LATEST.md and CLAUDE.md must stay identical at all times.
- Every Code session ends with: `git add -A && git commit && git push`, then `/snapshot`.

---

## Session end -- mandatory
1. State explicitly: what was changed, what was NOT changed, any new risks introduced.
2. git add -A && git commit
3. Confirm with user before git push
4. Run /snapshot
5. Final line every session: `git add -A && git commit && git push origin main`
# IRIS Robot Face — Claude Code Rules

## Session start
The SessionStart hook auto-loads the most recent SNAPSHOT_*.md before every session.
If context seems missing, run: `python3 .claude/hooks/session_start.py`

You are working on a production hardware-integrated AI system.

##Rules:
- Do NOT guess pins, ports, device paths, or hardware behavior
- Do NOT refactor multiple systems at once
- Preserve current behavior unless explicitly told to change it
- Only modify files explicitly mentioned
- Return FULL updated files, not partial snippets
- If uncertain, stop and ask instead of guessing

##Architecture direction:
- Single serial owner for Teensy
- Centralized state management
- Modular separation of hardware vs services vs orchestration


## Long output
- Snapshots, full file dumps, large summaries → write to a .md file, then summarize inline.
- Never print large blocks of content as chat text; it will be truncated.

## Firmware rules
- Do NOT modify `TeensyEyes.ino` — upstream engine, off limits.
- After any src/ change: run `/flash` (local USB) or `/flash-remote` (Pi4 SSH, PROG button required).

## Eye editing workflow
1. Edit `resources/eyes/240x240/<eye>/config.eye`
2. Run `python resources/eyes/240x240/genall.py` to regenerate the `.h`
3. **Re-apply -15% pupil values** to nordicBlue.h, hazel.h, bigBlue.h after any genall.py run
4. PlatformIO Upload

## Pi4 persistence (overlayfs)
- SD is read-only. Always persist after SSH edits — use `/deploy`.
- Never leave assistant.py edits in RAM only.

## Serial protocol
- Pi4 → Teensy: `EMOTION:x`, `EYES:SLEEP`, `EYES:WAKE`, `EYE:n` (0–6), `MOUTH:n`
- Teensy → Pi4: `FACE:1`, `FACE:0`
- Only `assistant.py` TeensyBridge owns `/dev/ttyACM0`. All others use UDP → 127.0.0.1:10500.

## Key files
- `src/main.cpp` — serial parsing, emotion, tracking, sleep logic
- `src/eyes/EyeController.h` — eye movement/blink/pupil (DO NOT break setTargetPosition seed fix)
- `/home/pi/assistant.py` — voice pipeline (~1600 lines), TeensyBridge, CMD listener
- Full architecture, pending items, current state: see most recent SNAPSHOT_*.md (auto-loaded)

## End of session
Run `/snapshot` to capture state. The next SessionStart hook picks it up automatically.

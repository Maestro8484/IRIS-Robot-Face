# IRIS PROJECT - AUTHORITATIVE CURRENT STATE

## Session Startup Context

Primary environment:
- SuperMaster Windows desktop is the primary control node.
- Claude Desktop GUI runs on SuperMaster.
- Claude has filesystem MCP access to the local IRIS repository.
- Claude has SSH MCP access to Pi4 and GandalfAI.
- Local git, VS Code, PlatformIO, and repo files are available on SuperMaster.

When starting a new AI session, read in this order:
1. `HANDOFF_CURRENT.md`
2. `CLAUDE.md`
3. `SNAPSHOT_LATEST.md`
4. `IRIS_ARCH.md` only when architecture, deployment, pins, services, or environment details are needed.

Do not rely on prior chat memory. Use local repository files and live system checks as current truth.

---

## Authority Model

Canonical source of truth:
`C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face`

Primary operator node:
SuperMaster desktop with Claude Desktop, filesystem MCP, SSH MCP, local git, VS Code, and PlatformIO.

Secondary mirror:
GitHub remote repository.

GitHub is useful for backup, history, sharing, and recovery, but it may lag local state until explicitly committed and pushed. Local repo state on SuperMaster outranks GitHub unless proven stale.

---

## Systems

- Pi4 = runtime orchestration, assistant loop, wakeword handling, web UI, cron sleep/wake, LEDs, camera, and Teensy serial bridge.
- GandalfAI = Ollama, Modelfiles, personality, Whisper STT, Piper TTS, Chatterbox TTS, and pipeline behavior.
- Teensy 4.1 = embedded display controller for eyes, mouth, sleep renderer, serial protocol, and face behavior.
- SuperMaster desktop = source repository, Claude Desktop, VS Code, PlatformIO, git, and command/control workstation.

---

## Current Status

- Batch 1A complete.
- Batch 1B complete.
- Pi4 operational.
- Wakeword responding.
- Teensy 4.1 operational.
- GandalfAI services active.
- Next target: Batch 1C.

---

## Completed Work

### Batch 1A - Runtime Survival

Goal:
Harden wakeword runtime survival and prevent OpenWakeWord failures from crashing or hanging the assistant.

Implemented:
- OpenWakeWord startup retry/backoff.
- Runtime restart if OpenWakeWord process dies.
- Wakeword socket timeout.
- Wakeword failures return `"error"` instead of silently hanging.
- Main loop skips STT/LLM/TTS when wakeword error occurs.
- Changes deployed, persisted, committed, and pushed.

Do not re-plan or re-do Batch 1A unless explicitly instructed.

### Batch 1B - Sleep/Wake Authority

Goal:
Centralize and harden sleep/wake state handling.

Implemented:
- Canonical `_do_sleep()`.
- Canonical `_do_wake()`.
- Unified sleep/wake entry paths in assistant command listener and wakeword-during-sleep path.
- `/tmp/iris_sleep_mode` synchronized with runtime state.
- `send_command()` and `send_emotion()` return bool status.
- Web sleep/wake routes update mouth intensity.
- `iris_wake.py` clears `/tmp/iris_sleep_mode`.

Do not re-plan or re-do Batch 1B unless explicitly instructed.

---

## Current Roadmap

### Batch 1C - Reliability Hygiene (NEXT)

Primary objectives:
- Route sleep wakeword greeting through Wyoming Piper on GandalfAI instead of broken local `/usr/local/bin/piper`.
- Persist `SPEAKER_VOLUME` across reboot.
- Add TTS hard-cap fallback for long punctuation-free text.
- Add config validation/coercion for `iris_config.json` overrides.
- Replace `tempfile.mktemp()` with `mkstemp()` or another safe temp-file pattern.
- Add malformed Ollama JSON stream warning once per request.
- Remove dead code only if verified unused.
- Add graceful volume subprocess failure handling if still missing.

Likely files:
- `pi4/assistant.py`
- `pi4/iris_web.py`
- `pi4/services/tts.py`
- `pi4/core/config.py`
- `pi4/services/vision.py`
- `pi4/services/llm.py`
- `pi4/hardware/audio_io.py`

### Batch 2 - Teensy Hardware/Firmware Pass

Only after Pi runtime remains stable.

Candidate scope:
- Sleep render pointer guards.
- Serial overflow discard-and-log behavior.
- Gate mouth commands during sleep if still needed.
- ACK/NACK protocol only if justified.
- Any Teensy 4.1 firmware changes must be separate from Pi Python runtime changes.

### Batch 3 - GandalfAI Personality/Pipeline Pass

Scope:
- Ollama Modelfiles.
- Personality and prompt tuning.
- Chatterbox/Piper routing.
- Inference settings.
- Vision prompt behavior.
- Model rebuilds and smoke tests.

---

## Deployment Rule

Pi4 persistence uses the direct `/media/root-ro` remount method only.

Do not use `overlayroot-chroot` unless independently re-verified first.

Canonical Pi4 persistence pattern:
```bash
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/<file> /media/root-ro/home/pi/<file>
sudo chown pi:pi /media/root-ro/home/pi/<file>
sudo chmod 644 /media/root-ro/home/pi/<file>
sync
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/<file> /media/root-ro/home/pi/<file>
```

For executable scripts, use mode `755` instead of `644`.

---

## Engineering Workflow

MAD Loop = Multi-Agent Adversarial Dev Loop.

Standard flow:
1. Claude Chat plans or reviews.
2. ChatGPT critiques and stress-tests the plan.
3. Optional Codex repo-wide audit or dependency review.
4. Human operator selects the safest scope.
5. Claude Chat produces final implementation handoff.
6. Claude Code implements one approved batch.
7. Human validates on real hardware.
8. Docs are updated.

Final authority belongs to the human operator.

---

## Working Rules

- One batch at a time.
- Minimal diffs.
- No broad refactors during reliability hardening.
- Preserve working behavior unless behavior is the bug.
- Test before starting next batch.
- Commit each batch separately.
- Update docs after meaningful changes.
- Full file outputs only when generating docs/config/code for manual replacement.
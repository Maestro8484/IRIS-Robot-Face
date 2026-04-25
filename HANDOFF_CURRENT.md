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
- Batch 1C largely complete (see below -- two items remain).
- Pi4 operational.
- Wakeword responding.
- Teensy 4.1 operational.
- GandalfAI services active.
- Dynamic response-length classification live and verified (S33).

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

### Batch 1C - Reliability Hygiene (MOSTLY COMPLETE)

Completed items:
- ✅ Config validation/coercion for `iris_config.json` (1C-A, 1C-A.2)
- ✅ Graceful volume subprocess failure handling (1C-B)
- ✅ TTS hard-cap fallback at sentence boundary (1C-C); cap raised 220→900 chars (1C-F fix)
- ✅ `mkstemp()` replacing unsafe `mktemp()` in vision.py (1C-E)
- ✅ Rate-limited malformed JSON stream warning in llm.py (1C-E)
- ✅ Dynamic response-length classification: SHORT/MEDIUM/LONG/MAX tiers (1C-F, S33)
  - `classify_response_length()` in `services/llm.py`
  - All tier constants in `core/config.py`, overridable via `iris_config.json`
  - Modelfile num_predict floor 200→800; "default to less" removed
  - Live-tested and confirmed working

Remaining Batch 1C items:
- ❌ Route sleep wakeword greeting through Wyoming Piper (local `/usr/local/bin/piper` is broken)
- ❌ Persist `SPEAKER_VOLUME` across reboot via `iris_config.json` + ALSA state workflow

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
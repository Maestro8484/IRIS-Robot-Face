# IRIS PROJECT - AUTHORITATIVE CURRENT STATE

## Session Startup Context

Primary environment:

- SuperMaster Windows desktop is the primary control node.
- Claude Desktop GUI runs on SuperMaster.
- Claude has filesystem MCP access to the local IRIS repository.
- Claude has SSH MCP access to Pi4 and GandalfAI.
- Local git, VS Code, PlatformIO, and repo files are available on SuperMaster.

When starting a new AI session, use this order:

1. Run `git status`.
2. Read `CLAUDE.md`.
3. Read `SNAPSHOT_LATEST.md`.
4. Read `HANDOFF_CURRENT.md`.
5. Read `IRIS_ARCH.md` only when architecture, deployment, pins, services, or environment details are needed.

Do not rely on prior chat memory. Use local repository files and live system checks as current truth.

---

## Authority Model

Canonical source of truth:

```text
C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face
```

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
- Batch 1C largely complete, with remaining items listed below.
- Pi4 operational.
- Wakeword production baseline restored to `hey_jarvis`.
- Custom wakeword attempt paused after failed real-world testing.
- Teensy 4.1 operational.
- GandalfAI services active.
- Dynamic response-length classification live and verified.

---

## Wakeword Status

Production wakeword:

```text
hey_jarvis
```

Custom wakeword experiment:

- `hey_der_iris` failed real-world reliability.
- `real_quick_iris` failed real-world reliability.
- Both are experimental only.
- Do not redeploy either without explicit user approval, real household voice samples, clean process restart, and one-model-at-a-time testing.

Important:

The wakeword issue is the active priority. Batch 3-A personality tuning is paused until the wakeword baseline and repo state are clean.

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

### S35 - Wakeword Baseline Restoration

Status:

Active current state.

Goal:

Restore `hey_jarvis` as the stable production baseline after failed custom wakeword attempts.

Rules:

- Do not deploy `hey_der_iris`.
- Do not deploy `real_quick_iris`.
- Do not test both custom wakewords simultaneously.
- Preserve scripts and notes as experimental history.
- Confirm live Pi4 state before any future wakeword deployment.

### Batch 1C - Reliability Hygiene

Completed items:

- Config validation/coercion for `iris_config.json`.
- Graceful volume subprocess failure handling.
- TTS hard-cap fallback at sentence boundary.
- `mkstemp()` replacing unsafe `mktemp()` in vision.py.
- Rate-limited malformed JSON stream warning in llm.py.
- Dynamic response-length classification: SHORT/MEDIUM/LONG/MAX tiers.

Remaining Batch 1C items:

- Route sleep wakeword greeting through Wyoming Piper because local `/usr/local/bin/piper` is broken.
- Persist `SPEAKER_VOLUME` across reboot via `iris_config.json` plus ALSA state workflow.

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

### Batch 3-A - Personality: Emotional Volatility Handling

Status:

Paused.

Reason:

Wakeword rollback and repo hygiene take priority.

Category:

GandalfAI / Modelfile only. No Pi4 changes. No firmware changes.

Important deployment gate:

Editing `ollama/iris_modelfile.txt` is local repo work. Running `ollama create` on GandalfAI is a live GandalfAI mutation and requires explicit user authorization using the word `DEPLOY`.

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
- GitHub push is never automatic.
- Pi4 and GandalfAI edits require explicit user authorization.

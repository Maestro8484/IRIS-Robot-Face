# IRIS Snapshot

**Session:** S35 | **Date:** 2026-04-25 | **Branch:** `main` | **Last commit:** 84f0e5d S34: web UI config expansion — OWW_DRAIN_SECS, response tiers, dual mouth intensity, VOL_MAX, stale key cleanup

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.
> Current state and roadmap: see `HANDOFF_CURRENT.md`.

---

## Machine Status

| System | Status |
|---|---|
| SuperMaster Desktop | Canonical local repo. Claude Desktop, filesystem MCP, SSH MCP active. |
| Pi4 192.168.1.200 | Operational. assistant.py running. Production wakeword: hey_jarvis. |
| GandalfAI 192.168.1.3 | Operational. Custom wakeword TFLite models archived as experimental. |
| Teensy 4.1 | Operational. All displays working. S36 firmware change pending (suspend eye movement during TTS). |
| TTS | Chatterbox primary, Piper fallback. |
| Web UI | Operational. Bench tab live. |

---

## Active Issues

- **MED: Piper sleep routing** — local `/usr/local/bin/piper` broken. Sleep wakeword greeting should route through Wyoming Piper on GandalfAI:10200 (Batch 1C).
- **MED: Volume persistence** — SPEAKER_VOLUME may reset on reboot (Batch 1C).
- **LOW: iris_config.json stale keys** — ELEVENLABS_ENABLED and similar ignored keys still present.
- **LOW: root-level stale sleep log** — /home/pi/iris_sleep.log may duplicate /home/pi/logs/iris_sleep.log.

---

## Session Scope

S35: Restore hey_jarvis as production wakeword baseline. Archive hey_der_iris and real_quick_iris as experimental. Commit wakeword documentation and training tooling.

---

## Do Not Touch Without Explicit Instruction

- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

---

## Last Session Changes (S35)

- **Wakeword baseline restored** — Production wakeword is `hey_jarvis`. Custom wakeword attempts (`hey_der_iris`, `real_quick_iris`) failed real-world reliability and are archived as experimental history. Do not redeploy without real household voice samples, clean process restart, and one-model-at-a-time testing.
- **Docs committed** — `HANDOFF_WAKEWORD_DEPLOY.md`, `PRIMER_WAKEWORD_DEPLOY.md`, `WAKEWORD_TRAINING_HANDOFF.md`, `HANDOFF_CURRENT.md`, `PRIMER.md` updated to reflect S35 state.
- **Batch 3-A paused** — Personality tuning paused until wakeword baseline and repo state are clean.
- **S36 pending** — `src/main.cpp` approved change: suspend eye movement during TTS responses. Commit separately.

## Previous Session Changes (S34)

- Web UI config expansion: OWW_DRAIN_SECS, response tiers, dual mouth intensity, VOL_MAX, stale key cleanup.
- GandalfAI TFLite conversion script for custom wakeword models (archived as experimental).
- Pi4 custom wakeword models deployed but wakeword test failed — baseline reversion followed.

---

## Known TODO

- **S36:** Commit `src/main.cpp` — suspend eye movement during TTS responses.
- **Batch 1C:** Piper sleep routing, volume persistence (remaining items).
- **Batch 2:** Teensy hardware/firmware pass — only after Pi runtime stable.
- **Batch 3:** GandalfAI personality/pipeline pass — only after wakeword baseline confirmed clean.

# IRIS Snapshot

**Session:** S39 | **Date:** 2026-04-26 | **Branch:** `main` | **Last commit:** ec2ad32 S39: Batch 3-C upgrade base model gemma3:12b->gemma3:27b-it-qat

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.
> Current state and roadmap: see `HANDOFF_CURRENT.md`.

---

## Machine Status

| System | Status |
|---|---|
| SuperMaster Desktop | Canonical local repo. Claude Desktop, filesystem MCP, SSH MCP active. |
| Pi4 192.168.1.200 | Operational. assistant.py running. Production wakeword: hey_jarvis. |
| GandalfAI 192.168.1.3 | Operational. Custom wakeword TFLite models archived as experimental. |
| Teensy 4.1 | Operational. All displays working. Eye movement suspended during TTS (S36, deployed). |
| TTS | Kokoro primary (Docker, GandalfAI), Piper fallback. Chatterbox replaced S38. |
| Web UI | Operational. Bench tab live. |

---

## Active Issues

- **MED: Piper sleep routing** — local `/usr/local/bin/piper` broken. Sleep wakeword greeting should route through Wyoming Piper on GandalfAI:10200 (Batch 1C).
- **MED: Volume persistence** — SPEAKER_VOLUME may reset on reboot (Batch 1C).
- **LOW: iris_config.json stale keys** — ELEVENLABS_ENABLED and similar ignored keys still present.
- **LOW: root-level stale sleep log** — /home/pi/iris_sleep.log may duplicate /home/pi/logs/iris_sleep.log.

---

## Session Scope

S39: Batch 3-C — upgrade base model gemma3:12b → gemma3:27b-it-qat in both iris and iris-kids Modelfiles. GandalfAI env vars OLLAMA_FLASH_ATTENTION=1 and OLLAMA_KV_CACHE_TYPE=q8_0 set machine-level. Models rebuilt and smoke-tested. VRAM ~16.1GB baseline, ~2.2GB headroom when warm.

---

## Do Not Touch Without Explicit Instruction

- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

---

## Last Session Changes (S39)

- **Batch 3-D** — `ollama/iris_modelfile.txt`: full persona pass. Added AMUSED emotion tag (insults → AMUSED not ANGRY). Added vocal texture line (dry economy, no filler). Added concrete insult response examples. Removed internal contradiction (rude-response line in WHO YOU ARE). Fixed double-negative to active framing. Smoke tests passed across insult, neutral, and curious probes.
- **Batch 3-C** — `ollama/iris_modelfile.txt`, `ollama/iris-kids_modelfile.txt`: FROM gemma3:12b → gemma3:27b-it-qat. GandalfAI env set: OLLAMA_FLASH_ATTENTION=1, OLLAMA_KV_CACHE_TYPE=q8_0 (machine-level, Ollama restarted). Both models rebuilt and smoke-tested. VRAM post-load: 22079 MiB used / 2248 MiB free.

## Previous Session Changes (S38)

- **Batch 3-B** — Chatterbox TTS replaced with Kokoro TTS (Docker). Restore script included.

## Earlier (S37)

- **Batch 3-A** — IRIS persona framing and temperature tuned. Eye movement suspended during TTS responses (S36). Wakeword baseline restored (S35).

---

## Known TODO

- **Batch 1C:** Piper sleep routing, volume persistence (remaining items).
- **Batch 2:** Teensy hardware/firmware pass — only after Pi runtime stable.
- **Batch 3:** GandalfAI personality/pipeline pass in progress. 3-A (persona), 3-B (Kokoro TTS), 3-C (27b model) done. Remaining: vision prompts, inference tuning.

# IRIS Snapshot

**Session:** S41 | **Date:** 2026-04-26 | **Branch:** `main` | **Last commit:** bc707d7 S40: Batch 3-E vision prompt

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.
> Current state and roadmap: see `HANDOFF_CURRENT.md`.

---

## Machine Status

| System | Status |
|---|---|
| SuperMaster Desktop | Canonical local repo. Claude Desktop, filesystem MCP, SSH MCP active. |
| Pi4 192.168.1.200 | Operational. assistant.py running. Production wakeword: hey_jarvis. |
| GandalfAI 192.168.1.3 | Operational. Kokoro TTS (Docker, port 8004). Ollama gemma3:27b-it-qat. |
| Teensy 4.1 | Operational. All displays working. Eye movement suspended during TTS (S36, deployed). |
| TTS | Kokoro primary (Docker, GandalfAI port 8004), Piper fallback (Wyoming port 10200). |
| Web UI | Operational. Bench tab live. |

---

## Active Issues

- **MED: Piper sleep routing** — local `/usr/local/bin/piper` broken. Sleep wakeword greeting should route through Wyoming Piper on GandalfAI:10200 (Batch 1C). LOW-LOW priority — Kokoro is primary TTS.
- **MED: Volume persistence** — SPEAKER_VOLUME may reset on reboot (Batch 1C).
- **LOW: root-level stale sleep log** — /home/pi/iris_sleep.log may duplicate /home/pi/logs/iris_sleep.log.

---

## Session Scope

S41: Repo cleanup sprint. ElevenLabs fully scrubbed from live docs and config. MAX7219/bit-bang stale refs removed. src/mouth.h deleted (dead code). Credentials redacted from public docs. snapshots/ untracked from git. docs/tts-history.md and ollama/README.md created. IRIS-Bench documented. Task 3 (GandalfAI modelfile sync) pending — GandalfAI was offline during session.

---

## Bench / Eval Tooling

**IRIS-Bench** — `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Bench`

Standalone LLM/STT/TTS evaluation harness built via ChatGPT+Claude MAD loop process (not a Claude-only artifact). Not part of the IRIS-Robot-Face PlatformIO project. Not currently version-controlled.

Contents: `run_bench.py`, `iris_bench/` (package), `prompts/`, `results/`, `audio/`, `modelfiles-drafts/`, `config.example.json`, `README.md`

Status: Active. Results stored locally. Separate repo recommended when ready to version-control.

---

## Do Not Touch Without Explicit Instruction

- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

---

## Last Session Changes (S41)

- **ElevenLabs scrub** — All live doc and config refs removed. README, IRIS_ARCH, IRIS_CONFIG_MAP, SNAPSHOT updated. No code references existed (removed ~S20).
- **MAX7219 retire** — `src/mouth.h` deleted (dead file, not included in main.cpp since ILI9341 TFT replaced MAX7219). All stale MAX7219/bit-bang refs in docs updated to ILI9341 TFT.
- **Credential redaction** — IRIS_ARCH.md machine table, WAKEWORD_TRAINING_HANDOFF.md: passwords replaced with `<password>`. tools/iris_dashboard/app.py: PI4_PASS now reads from `os.environ.get("PI4_PASS", "ohs")`.
- **snapshots/ untracked** — Added to .gitignore, removed from git tracking. Historical archives with stale credentials no longer in public HEAD.
- **Config cleanup** — pi4/core/config.py: Chatterbox section marked rollback-only, TTS_MAX_CHARS comment updated, MOUTH_INTENSITY comment updated to ILI9341 TFT.
- **IRIS_CONFIG_MAP** — Kokoro TTS section added as primary. Chatterbox moved to rollback. MAX7219 heading → ILI9341 TFT. ELEVENLABS_ENABLED entry updated to "Removed S20".
- **docs/tts-history.md** — Created: full Phase 1–4 TTS evolution narrative.
- **ollama/README.md** — Created: modelfile inventory and rebuild commands.
- **Task 3 pending** — GandalfAI offline during session. Modelfile sync (local ollama/ vs GandalfAI live files) deferred to next session.

## Previous Session Changes (S40)

- **Camera fix** — Pi4 camera binary confirmed as `rpicam-still`. `/tmp/iris_test.py` line 66 updated. Vision smoke test passed.
- **Batch 3-E** — `ollama/iris_modelfile.txt`: VISION block added (character voice, household recognition, text reading, editorial beat).

---

## Known TODO

- **Task 3 deferred** — Verify GandalfAI live modelfiles match local `ollama/iris_modelfile.txt` and `ollama/iris-kids_modelfile.txt`. Do when GandalfAI is online.
- **Batch 1C:** Piper sleep routing (LOW-LOW), volume persistence.
- **Batch 2:** Teensy hardware/firmware pass — only after Pi runtime stable.
- **Batch 3:** Vision prompts done (3-E). Inference settings review remaining.

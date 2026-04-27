# IRIS Snapshot

**Session:** S43 | **Date:** 2026-04-27 | **Branch:** `main` | **Last commit:** 39247b4 fix: extend spoken_numbers() to handle thousands/millions for TTS

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.
> Current state and roadmap: see `HANDOFF_CURRENT.md`.

---

## Machine Status

| System | Status |
|---|---|
| SuperMaster Desktop | Canonical local repo. Claude Desktop, filesystem MCP, SSH MCP active. |
| Pi4 192.168.1.200 | Operational. assistant.py + intent_router.py deployed, persisted, verified. |
| GandalfAI 192.168.1.3 | Operational. iris model rebuilt with Batch 3-F modelfile (NEVER say block live). |
| Teensy 4.1 | Operational. Eye movement suspended during TTS (S36). |
| TTS | Kokoro primary (Docker, GandalfAI port 8004), Piper fallback (Wyoming port 10200). |
| Web UI | Operational. Bench tab live. |

---

## Active Issues

- **HIGH: "stop" single-word STT failure** — Whisper hallucinates on short single-word utterances. "stop" → transcribed as "What are you doing?" Router classified correctly; STT is the failure point. Needs either (a) pre-STT RMS interrupt shortcut for very short post-wakeword audio or (b) local fast STT fallback for <2-word utterances.
- **MED: LLM personality inconsistency** — Second insult-response in Loop 3 was gemma boilerplate. Root cause: GandalfAI model was stale (multiple batches behind). Model rebuilt S42. Re-test before adding persona work. **Standing rule: any LLM drift = check GandalfAI sync first** (`ollama show iris --modelfile` vs repo). See memory: project_gandalf_modelfile_sync.md.
- **MED: Piper sleep routing** — local `/usr/local/bin/piper` broken. Sleep wakeword greeting routes through Wyoming Piper on GandalfAI:10200. LOW-LOW priority.
- **MED: Volume persistence** — SPEAKER_VOLUME may reset on reboot (Batch 1C).
- **LOW: root-level stale sleep log** — /home/pi/iris_sleep.log may duplicate /home/pi/logs/iris_sleep.log.

---

## Session Scope

S43: TTS number verbalization fix — `spoken_numbers()` extended to handle thousands/millions. Deployed to Pi4. GandalfAI sync documented as standing operational hazard.

---

## Do Not Touch Without Explicit Instruction

- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

---

## Last Session Changes (S43)

- **`pi4/services/tts.py`** — `spoken_numbers()` / `_int_to_words()` extended to handle thousands (< 1M) and millions (< 1B). Removed `<= 999` bailout in catch-all regex. "4210" → "four thousand two hundred ten". Deployed + persisted to Pi4 (md5 verified).
- **Standing rule documented** — LLM personality drift = GandalfAI model stale. Always run `ollama show iris --modelfile` on GandalfAI and compare to repo before adding persona fixes. Three-way desync: SuperMaster / GitHub / GandalfAI running model. Memory updated: `project_gandalf_modelfile_sync.md`.

## Previous Session Changes (S42)

- `pi4/core/intent_router.py` — NEW. 5-layer REFLEX/COMMAND/UTILITY/AMBIGUOUS/LLM classifier. Fail-open on exception.
- `pi4/assistant.py` — single `router.classify()` gate replaces all scattered inline checks.
- `ollama/iris_modelfile.txt` — NEVER say forbidden phrase block appended to SYSTEM.
- GandalfAI — `git pull` + `ollama create iris` run. Loop 3: 4/5 pass live.

---

## Known TODO

- **NEXT — stop shortcut**: investigate pre-STT intercept for very short RMS bursts post-wakeword (< 0.5s audio = likely a single command word). Route directly without Whisper for known short-command RMS signatures, OR add "stop" and close variants to a local keyword list checked before STT.
- **LLM personality re-test:** Say an insult; confirm IRIS responds in character. If boilerplate, check GandalfAI sync before any persona changes.
- **Batch 1C:** Volume persistence, Piper sleep routing (LOW-LOW).
- **Batch 2:** Teensy hardware/firmware pass — only after Pi runtime stable.
- **Batch 3 remaining:** Inference settings review.

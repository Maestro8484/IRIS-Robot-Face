# IRIS Snapshot

**Session:** S44 | **Date:** 2026-04-28 | **Branch:** `main` | **Last commit:** 35d01ba S44: fix intent router RANDOM_NUMBER, follow-up short-reply filter, web UI logs

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.
> Current state and roadmap: see `HANDOFF_CURRENT.md`.

---

## Machine Status

| System | Status |
|---|---|
| SuperMaster Desktop | Canonical local repo. Claude Desktop, filesystem MCP, SSH MCP active. |
| Pi4 192.168.1.200 | Operational. assistant.py + intent_router.py + iris_web.py deployed, persisted, verified. |
| GandalfAI 192.168.1.3 | Operational. iris model rebuilt with Batch 3-F modelfile (NEVER say block live). |
| Teensy 4.1 | Operational. Eye movement suspended during TTS (S36). |
| TTS | Kokoro primary (Docker, GandalfAI port 8004), Piper fallback (Wyoming port 10200). |
| Web UI | Operational. Bench tab live. Logs tab now shows intent routing decisions. |

---

## Active Issues

- **HIGH: "stop" single-word STT failure** — Whisper hallucinates on short single-word utterances. "stop" → transcribed as "What are you doing?" Router classified correctly; STT is the failure point. Needs either (a) pre-STT RMS interrupt shortcut for very short post-wakeword audio or (b) local fast STT fallback for <2-word utterances.
- **MED: LLM personality inconsistency** — Second insult-response in Loop 3 was gemma boilerplate. Root cause: GandalfAI model was stale (multiple batches behind). Model rebuilt S42. Re-test before adding persona work. **Standing rule: any LLM drift = check GandalfAI sync first** (`ollama show iris --modelfile` vs repo). See memory: project_gandalf_modelfile_sync.md.
- **MED: Piper sleep routing** — local `/usr/local/bin/piper` broken. Sleep wakeword greeting routes through Wyoming Piper on GandalfAI:10200. LOW-LOW priority.
- **MED: Volume persistence** — SPEAKER_VOLUME may reset on reboot (Batch 1C).
- **LOW: root-level stale sleep log** — /home/pi/iris_sleep.log may duplicate /home/pi/logs/iris_sleep.log.

---

## Session Scope

S44: Intent router + follow-up loop + web UI log fixes. Three bugs confirmed from live Pi4 logs and fixed.

---

## Do Not Touch Without Explicit Instruction

- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

---

## Last Session Changes (S44)

- **`pi4/core/intent_router.py`** — Added `RANDOM_NUMBER` utility handler (Layer 2). `_RANDOM_RE` catches "pick/tell/give/choose/generate a random number"; `_RANDOM_RANGE_RE` parses optional "between X and Y" range. Answer generated locally via `random.randint` — no LLM, no GandalfAI roundtrip. Deployed + persisted to Pi4 (md5 verified).
- **`pi4/assistant.py`** — Follow-up loop `< 3 words` gate replaced with `_WHISPER_HALLUCINATIONS` set check. Brief valid user replies ("Yes, 54.", "Seven.", "No.") no longer silently dropped after IRIS asks a follow-up question.
- **`pi4/services/llm.py`** — Added `"random number"`, `"pick a random"`, `"tell me a random"`, `"give me a random"`, `"choose a random"`, `"generate a random"`, `"pick a number"`, `"give me a number"` to `_SHORT_PATTERNS`. Ensures SHORT token tier if any variant bypasses the router.
- **`pi4/iris_web.py`** — `/api/logs` now appends last 40 lines of `/home/pi/logs/iris_intent.log` below a separator. Web UI Logs tab shows intent route decisions (`intent=LLM|RANDOM_NUMBER|MATH etc.`) alongside journalctl. Line limit raised from 120 to 150.

## Previous Session Changes (S43)

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

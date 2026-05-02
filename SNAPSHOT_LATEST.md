# IRIS Snapshot

**Session:** S45 | **Date:** 2026-05-02 | **Branch:** `main` | **Last commit:** 103cbcc S45: add docs/iris_issue_log.md -- structured issue/fix history S1-S44

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
- **HIGH: AMUSED emotion — full project removal needed** — AMUSED exists in `ollama/iris_modelfile.txt` valid-values line but is absent from `core/config.py` VALID_EMOTIONS, `hardware/led.py` _EMOTION_LED, and firmware EmotionID enum. LLM emitting [EMOTION:AMUSED] silently falls back to NEUTRAL throughout the stack. Decision: remove AMUSED from modelfile + all code/firmware. Batch D functional task.
- **MED: LLM personality inconsistency** — Standing rule: any LLM drift = check GandalfAI sync first (`ollama show iris --modelfile` vs repo). See memory: project_gandalf_modelfile_sync.md.
- **LOW: root-level stale sleep log** — /home/pi/iris_sleep.log may duplicate /home/pi/logs/iris_sleep.log.

---

## Session Scope

S45: Docs cleanup pass (Batch A). No code changes. 7 doc files updated: Chatterbox→Kokoro primary throughout, gemma3:27b-it-qat references, Teensy 4.1, 7-eye system, Batch 1C closed, SPEAKER_VOLUME resolved, AMUSED removal tracked as Batch D task.

---

## Do Not Touch Without Explicit Instruction

- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

---

## Last Session Changes (S45)

Batch A docs-only cleanup. No code, no deploy, no Pi4/GandalfAI changes.

- **`IRIS_ARCH.md`** — Chatterbox→Kokoro primary throughout; Batch 1C marked Complete; gemma3:27b-it-qat in repo structure; "as of S45" label; reboot checklist updated; Chatterbox section relabeled rollback reference.
- **`README.md`** — Teensy 4.1 (was 4.0); 7-eye table corrected (EYE:0–6, dragon at 5, bigBlue at 6; leopard/snake noted as pending compile); gemma3:27b-it-qat; PROG button note removed (enclosure-mounted); mouth driver corrected to KurtE/ILI9341_t3n hardware SPI2.
- **`CLAUDE.md`** — GandalfAI role updated: Kokoro primary, Piper fallback, Chatterbox rollback only; VRAM numbers updated to Kokoro+gemma3:27b-it-qat baseline.
- **`SNAPSHOT_LATEST.md`** — Updated to S45; Piper routing + Volume persistence removed from active issues (deferred/done); AMUSED gap added as HIGH active issue.
- **`HANDOFF_CURRENT.md`** — Batch 1C marked fully closed; SPEAKER_VOLUME marked DONE; ACK/NACK removed from Batch 2; AMUSED removal added as tracked Batch D task.
- **`docs/iris_issue_log.md`** — SPEAKER_VOLUME marked Fixed; Piper routing updated to Deferred/Closed.
- **`IRIS_CONFIG_MAP.md`** — num_ctx VRAM note updated: Chatterbox→Kokoro, headroom numbers corrected.

## Previous Session Changes (S44)

- **`pi4/core/intent_router.py`** — Added `RANDOM_NUMBER` utility handler (Layer 2).
- **`pi4/assistant.py`** — Follow-up loop `< 3 words` gate replaced with `_WHISPER_HALLUCINATIONS` set check.
- **`pi4/services/llm.py`** — Random-number phrases added to `_SHORT_PATTERNS`.
- **`pi4/iris_web.py`** — `/api/logs` now appends last 40 lines of `iris_intent.log`.

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

- **NEXT — stop shortcut (Batch D)**: pre-STT intercept for very short RMS bursts post-wakeword (< 0.5s audio). Route "stop"/"quiet" directly without Whisper.
- **NEXT — AMUSED removal (Batch D)**: Remove AMUSED from `ollama/iris_modelfile.txt` valid-values line, `pi4/core/config.py` VALID_EMOTIONS, `pi4/hardware/led.py` _EMOTION_LED, and firmware `EmotionID` enum in `src/main.cpp`. Then `ollama create iris` on GandalfAI (requires DEPLOY).
- **LLM personality re-test:** Say an insult; confirm IRIS responds in character. If boilerplate, check GandalfAI sync before any persona changes.
- **Batch 1C:** CLOSED — all items done or deferred.
- **Batch 2:** Teensy hardware/firmware pass — only after Pi runtime stable.
- **Batch 3 remaining:** Inference settings review.

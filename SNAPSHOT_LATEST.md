# IRIS Snapshot

**Session:** S46 | **Date:** 2026-05-03 | **Branch:** `main` | **Last commit:** S46: Add WoL acknowledgement beep (play_wol_beep)

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

S46: UX improvement — WoL acknowledgement beep. When GandalfAI is offline and IRIS sends a Wake-on-LAN packet, a distinctive ascending 2-tone beep (660 Hz → 880 Hz, ~360 ms) now plays immediately so the user knows IRIS acknowledged the wakeword and is waiting for GandalfAI. No change when GandalfAI is already up. 2 files changed, ~15 lines added.

---

## Do Not Touch Without Explicit Instruction

- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

---

## Last Session Changes (S46)

WoL acknowledgement beep. Code only. No deploy, no Pi4/GandalfAI mutations.

- **`pi4/hardware/audio_io.py`** — Added `play_wol_beep(pa)`: ascending 2-tone 660→880 Hz, ~360 ms, exported.
- **`pi4/assistant.py`** — Imported `play_wol_beep`; added `pa=None` param to `ensure_gandalf_up`; beep fires inside function immediately after WoL send; both call sites updated to pass `pa`.
- **`docs/plans/PLAN_WOL_ACK_BEEP.md`** — Plan document created (pre-implementation audit trail).

## Previous Session Changes (S45)

Batch A docs-only cleanup. No code, no deploy, no Pi4/GandalfAI changes.

- **`IRIS_ARCH.md`** — Chatterbox→Kokoro primary throughout; Batch 1C marked Complete; gemma3:27b-it-qat in repo structure; "as of S45" label; reboot checklist updated; Chatterbox section relabeled rollback reference.
- **`README.md`** — Teensy 4.1 (was 4.0); 7-eye table corrected (EYE:0–6, dragon at 5, bigBlue at 6; leopard/snake noted as pending compile); gemma3:27b-it-qat; PROG button note removed (enclosure-mounted); mouth driver corrected to KurtE/ILI9341_t3n hardware SPI2.
- **`CLAUDE.md`** — GandalfAI role updated: Kokoro primary, Piper fallback, Chatterbox rollback only; VRAM numbers updated to Kokoro+gemma3:27b-it-qat baseline.
- **`HANDOFF_CURRENT.md`** — Batch 1C marked fully closed; SPEAKER_VOLUME marked DONE; ACK/NACK removed from Batch 2; AMUSED removal added as tracked Batch D task.
- **`docs/iris_issue_log.md`** — SPEAKER_VOLUME marked Fixed; Piper routing updated to Deferred/Closed.

## Previous Session Changes (S44)

- **`pi4/core/intent_router.py`** — Added `RANDOM_NUMBER` utility handler (Layer 2).
- **`pi4/assistant.py`** — Follow-up loop `< 3 words` gate replaced with `_WHISPER_HALLUCINATIONS` set check.
- **`pi4/services/llm.py`** — Random-number phrases added to `_SHORT_PATTERNS`.
- **`pi4/iris_web.py`** — `/api/logs` now appends last 40 lines of `iris_intent.log`.

## Next Work

See `ROADMAP.md` for full forward-looking task list and item specs.

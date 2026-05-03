<!-- Completed history only. Do not edit prior entries. Append new entries at the bottom. -->

# IRIS Changelog

Entries are in chronological order, oldest first. Active and forward-looking items are in `ROADMAP.md`.

---

## Batch 1A — Runtime Survival

**Status:** Complete

**Goal:** Harden wakeword runtime survival. Prevent OpenWakeWord failures from crashing or hanging the assistant.

Implemented:
- OpenWakeWord startup retry/backoff.
- Runtime restart if OpenWakeWord process dies.
- Wakeword socket timeout.
- Wakeword failures return `"error"` instead of hanging silently.
- Main loop skips STT/LLM/TTS when wakeword error occurs.

Deployed, persisted, committed, and pushed.

---

## Batch 1B — Sleep/Wake Authority

**Status:** Complete

**Goal:** Centralize and harden sleep/wake state handling.

Implemented:
- Canonical `_do_sleep()` and `_do_wake()`.
- Unified sleep/wake entry paths in assistant command listener and wakeword-during-sleep path.
- `/tmp/iris_sleep_mode` synchronized with runtime state.
- `send_command()` and `send_emotion()` return bool status.
- Web sleep/wake routes update mouth intensity.
- `iris_wake.py` clears `/tmp/iris_sleep_mode`.

---

## S35 — Wakeword Baseline Restoration

**Status:** Complete

**Goal:** Restore `hey_jarvis` as the stable production baseline after failed custom wakeword experiments.

Background: Two custom wakewords were trained and tested — `hey_der_iris` and `real_quick_iris`. Both failed real-world reliability testing in a live household environment and were abandoned. Neither should be redeployed without new household voice samples, clean process restart, and one-model-at-a-time testing.

Rules established (permanent):
- Do not deploy `hey_der_iris` or `real_quick_iris` without new voice samples and explicit user approval.
- Do not test both custom wakewords simultaneously.
- Preserve scripts and notes as experimental history only.
- Confirm live Pi4 state before any future wakeword deployment.

---

## Batch 1C — Reliability Hygiene

**Status:** Complete — all items done or explicitly deferred/closed

Implemented:
- Config validation/coercion for `iris_config.json`.
- Graceful volume subprocess failure handling.
- TTS hard-cap fallback at sentence boundary.
- `mkstemp()` replacing unsafe `mktemp()` in `vision.py`.
- Rate-limited malformed JSON stream warning in `llm.py`.
- Dynamic response-length classification: SHORT/MEDIUM/LONG/MAX tiers.
- SPEAKER_VOLUME persistence: web UI volume API calls `alsactl store` and writes `SPEAKER_VOLUME` to `iris_config.json` on every change.

Deferred/closed items:
- Route sleep wakeword greeting through Wyoming Piper — DEFERRED/CLOSED. Kokoro is primary; local Piper binary broken but not worth fixing.

---

## S36 — Suspend Eye Movement During TTS

**Status:** Complete (commit c27517a)

Implemented:
- `src/main.cpp`: Eye movement paused for duration of TTS audio playback, resumed on completion.

---

## S37 / Batch 3-A — Persona Framing + Temperature

**Status:** Complete (commit 8bdf87e)

Implemented:
- `ollama/iris_modelfile.txt`: Replaced explicit EMOTIONAL STATE AND EXPRESSION block with implicit thick-skin/fast-mouth character framing.
- Temperature raised from 0.7 to 0.82.
- iris model rebuilt on GandalfAI. Smoke tests passed.

---

## S38 / Batch 3-B — Kokoro TTS

**Status:** Complete

Implemented:
- Kokoro TTS (Docker, GandalfAI port 8004) replaces Chatterbox as primary TTS.
- Piper (Wyoming port 10200) retained as fallback.
- Chatterbox retained as rollback reference only — not actively used.

---

## S39 / Batch 3-C + 3-D — Model Upgrade + Full Persona Pass

**Status:** Complete

Implemented:
- Batch 3-C: gemma3:12b replaced by gemma3:27b-it-qat on GandalfAI.
- Batch 3-D: Full persona pass — AMUSED tag added to modelfile valid-values line, vocal texture added, insult examples added, contradiction fix applied.
- Standing rule established: IRIS is male. Pronouns: he/him. The name sounds female but is not. Applies to all modelfile edits, persona descriptions, and handoff docs.
- iris model rebuilt on GandalfAI.

---

## S40 / Batch 3-E — Vision Prompt

**Status:** Complete

Implemented:
- Vision prompt behavior configured in `ollama/iris_modelfile.txt`.

---

## S42 / Batch 3-F — Pre-LLM Intent Router

**Status:** Complete

Implemented:
- `pi4/core/intent_router.py` — NEW. 5-layer REFLEX/COMMAND/UTILITY/AMBIGUOUS/LLM classifier. Fail-open on exception.
- `pi4/assistant.py` — single `router.classify()` gate replaces all scattered inline checks.
- `ollama/iris_modelfile.txt` — NEVER say forbidden phrase block appended to SYSTEM.
- GandalfAI — `git pull` + `ollama create iris` run. Live validation: 4/5 pass.

---

## S43 — Spoken Numbers Fix

**Status:** Complete

Implemented:
- `pi4/services/tts.py` — `spoken_numbers()` / `_int_to_words()` extended to handle thousands (< 1M) and millions (< 1B). Removed `<= 999` bailout in catch-all regex. "4210" → "four thousand two hundred ten".
- Deployed and persisted to Pi4 (md5 verified).

Standing rule established: LLM personality drift → check GandalfAI model sync first (`ollama show iris --modelfile` vs repo). Three-way desync is possible: SuperMaster / GitHub / GandalfAI running model.

---

## S44 — RANDOM_NUMBER Handler + Follow-up Filter + Web UI Logs

**Status:** Complete (commit 35d01ba, 2026-04-28)

Implemented:
- `pi4/core/intent_router.py` — `RANDOM_NUMBER` utility handler added to Layer 2. Catches "pick/tell/give/choose/generate a random number" with optional "between X and Y" range. Answered locally via `random.randint` — zero LLM latency.
- `pi4/assistant.py` — Follow-up loop `< 3 words` gate removed. Replaced with `_WHISPER_HALLUCINATIONS` set check. Brief valid replies ("Yes, 54.", "No.", "Seven.") now pass through correctly.
- `pi4/services/llm.py` — Random-number phrases added to `_SHORT_PATTERNS` as LLM-path fallback tier.
- `pi4/iris_web.py` — `/api/logs` appends last 40 lines of `iris_intent.log` so web UI Logs tab shows per-request routing decisions.

---

## S47 — RD-002 AMUSED Emotion Full Implementation

**Status:** Complete in local repo (2026-05-03) — pending Pi4 deploy and firmware upload

**Goal:** Fully implement AMUSED as a first-class emotion across the IRIS stack. Decision changed from removal (prior doc guidance) to full implementation. AMUSED = dry amusement at teasing, insults, or attempts to rattle IRIS — distinct from CONFUSED (genuinely unclear/contradictory input).

Implemented:
- `pi4/core/config.py` — AMUSED added to VALID_EMOTIONS and MOUTH_MAP (→ index 2, reuses CURIOUS/smirk expression). LLM emitting [EMOTION:AMUSED] now passes validation and routes correctly instead of falling back to NEUTRAL.
- `pi4/hardware/led.py` — AMUSED: sinusoidal breathe, amber [255,160,0], floor=10, peak=80, period=1.5s, gamma=1.8, duration=3s. Handled as a special case in show_emotion() (not via _EMOTION_LED dict). Livelier than HAPPY/CURIOUS; distinct from ANGRY.
- `src/main.cpp` — AMUSED added to EmotionID enum (value 8, before EMOTION_COUNT). EmotionParams: {0.55f, false, 3000} — medium pupil, no blink, 3s gaze (dry, steady). AMUSED case added to parseEmotion. Falls to default else branch in applyEmotion — no eye swap, uses default eyes.
- `pi4/iris_web.html` — AMUSED button added to Emotion Test grid.
- PlatformIO build: SUCCESS.
- Python syntax check: OK.
- `ollama/iris_modelfile.txt` — no change; AMUSED already present and correctly described.
- `ollama/iris-kids_modelfile.txt` — AMUSED added to valid emotion list.

---

## S45 — Batch A Docs Cleanup

**Status:** Complete (commit 13c1461, 2026-05-02)

Batch A docs-only cleanup. No code changes, no deploys, no Pi4 or GandalfAI changes. Seven files updated.

- **`IRIS_ARCH.md`** — Chatterbox→Kokoro primary throughout; Batch 1C marked Complete; gemma3:27b-it-qat in repo structure; "as of S45" label; reboot checklist updated; Chatterbox section relabeled rollback reference.
- **`README.md`** — Teensy 4.1 (was 4.0); 7-eye table corrected (EYE:0–6, dragon at 5, bigBlue at 6; leopard/snake noted pending compile); gemma3:27b-it-qat; PROG button note removed (enclosure-mounted); mouth driver corrected to KurtE/ILI9341_t3n hardware SPI2.
- **`CLAUDE.md`** — GandalfAI role updated: Kokoro primary, Piper fallback, Chatterbox rollback only; VRAM numbers updated to Kokoro+gemma3:27b-it-qat baseline.
- **`SNAPSHOT_LATEST.md`** — Updated to S45; Piper routing + Volume persistence removed from active issues; AMUSED gap added as HIGH active issue.
- **`HANDOFF_CURRENT.md`** — Batch 1C marked fully closed; SPEAKER_VOLUME marked DONE; ACK/NACK removed from Batch 2; AMUSED removal added as tracked Batch D task.
- **`docs/iris_issue_log.md`** — SPEAKER_VOLUME marked Fixed; Piper routing updated to Deferred/Closed.
- **`IRIS_CONFIG_MAP.md`** — num_ctx VRAM note updated: Chatterbox→Kokoro, headroom numbers corrected.
- **`docs/iris_issue_log.md`** (commit 103cbcc) — Created. Append-only structured log of all issues/fixes S1–S44, backfilled from git history.

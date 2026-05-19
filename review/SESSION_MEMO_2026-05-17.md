# IRIS Session Memo — Forward Handoff to Sonnet 4.6

**Last updated:** 2026-05-18
**Originally generated:** 2026-05-17 (Opus 4.7)
**Current status:** Post-deploy of latency observability + Kokoro speed work
**Target reader:** New Sonnet 4.6 Claude Desktop chat (default model going forward)

---

## How to use this memo

In a new Claude Desktop chat with **Sonnet 4.6** selected, paste this seed prompt:

```
Read C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face\review\SESSION_MEMO_2026-05-17.md before responding. That memo is the running continuity document for IRIS work across chat sessions. After reading it, confirm continuity and current state, then proceed with: [STATE YOUR NEXT TASK].
```

That single instruction is enough. Sonnet reads this file, has full context, ready for next task.

**Default model going forward: Sonnet 4.6.** Reserve Opus 4.7 only for:
- Multi-file coordinated refactors (e.g., B1 sleep-flag work touching 5 files)
- Complex new feature design from scratch
- Adversarial review / pushback on your own reasoning

Everything else — task selection, handoff generation, doc updates, latency analysis, deploy verification — is Sonnet work.

---

## 1. Project orientation (one-paragraph version)

IRIS is a local AI robot face on Raspberry Pi 4 + Teensy 4.1 + GandalfAI (Windows RTX 3090 PC). Voice pipeline: wakeword → Whisper STT → gemma3:27b-it-qat via Ollama → Kokoro TTS → wm8960 audio out. Local repo at `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face` is source of truth; GitHub is mirror. Pi4 uses overlayfs (writes are RAM-only until persisted to SD). Rules in `CLAUDE.md` — pre-flight checklist, REPO-ONLY default, DEPLOY requires explicit user authorization. Protected files: `iris_config.json`, `alsa-init.sh`, `src/TeensyEyes.ino`, `src/eyes/EyeController.h`. GitHub: https://github.com/Maestro8484/IRIS-Robot-Face.

---

## 2. What the prior Opus session produced

### 2a. Six-task code review (read-only audit)

Output files in `review/`:

- `findings_session_1_pipeline.md` — Pi4 voice pipeline, exception paths, race conditions, router bypasses
- `findings_session_2_config.md` — Config key coverage, chown gaps, startup-only reads, overlayfs persistence
- `findings_session_3_emotions.md` — Emotion system consistency across config.py, led.py, llm.py, main.cpp, docs
- `findings_session_4_router.md` — Intent router pattern coverage, false positives, RANDOM_NUMBER handler
- `findings_session_5_failures.md` — 10 failure scenarios, recovery semantics, user feedback gaps
- `findings_session_6_drift.md` — S45-S49 doc updates, Chatterbox→Kokoro audit, constants cross-reference
- `findings_MASTER.md` — Synthesis with Top 5 priority + implementation sequence in 6 batches

**Severity totals:** 5 HIGH, 16 MED, 26 LOW, 5 informational.

### 2b. Top 5 highest-priority findings (from MASTER)

1. `/api/persist_config` in `pi4/iris_web.py` missing `chown pi:pi` after `sudo cp` — reproduces documented S22B failure cascade
2. `_playback_interrupt_listener` in `pi4/hardware/audio_io.py` leaks `_stop_playback.set()` across utterances — kills next playback
3. `/tmp/iris_sleep_mode` has 4 unsynchronized writers (assistant.py, iris_sleep.py, iris_wake.py, iris_web.py)
4. Both TTS engines (Kokoro + Piper) down → up to 90s of silence with no spoken explanation
5. `_DATE_RE` in intent_router.py matches "what year did X happen" → returns current year for any historical question

### 2c. Implementation sequence (from MASTER Section 3)

| Order | Batch | Files | Top 5 items | Risk | Model |
|---|---|---|---|---|---|
| 1 | A1 — iris_web chown fix | `pi4/iris_web.py` | #1 | Low | Sonnet |
| 2 | A2 — playback interrupt race | `pi4/hardware/audio_io.py` | #2 | Med | Sonnet |
| 3 | A3 — router regex tightening | `pi4/core/intent_router.py` | #5 + 5 LOWs | Med | Sonnet |
| 4 | B1 — sleep-flag single-owner | 5 files | #3 | Med-High | Sonnet/Opus |
| 5 | A4 — TTS fast-fail + audible error | `tts.py`, `audio_io.py` | #4 | Med | Sonnet |
| 6 | C1 — docs refresh | `IRIS_ARCH.md`, `README.md`, `IRIS_CONFIG_MAP.md` | LOW cleanup | None | Haiku |

---

## 3. Tier 1-4 priority reframe (user-experience perspective)

This reranking layers on top of MASTER's severity-based priority. It reflects what the user actually feels during use.

### Tier 1 — Daily user-visible impact

- **A3 router regex tightening.** Only fix that changes what IRIS *says* in normal use. "What year did the Civil War end" currently returns "Today is..." Every historical question is wrong.
- **A4 TTS fast-fail.** Up to 90s silence when both engines down. Worst sit-and-wait UX.

### Tier 2 — Conditional failures

- **A1 iris_web chown.** Dormant until Pi4 reboots. Cheap one-line fix.
- **A2 playback interrupt race.** Rare phantom playback interruptions.

### Tier 3 — Slow-burn / coherence

- **B1 sleep-flag single-owner.** State drift between sleep flag and `state.eyes_sleeping`.
- **D2 + D3 history-pop on LLM/TTS exception.** Long-conversation degradation.

### Tier 4 — Polish, docs, hygiene

- **C1 docs refresh.** Zero user-facing impact. High value for AI handoffs.
- **D1, D4, D5, D6.** Pure code hygiene.

**User-frustration-driven priority:** A3 → A4 → A1 → A2 → everything else.

---

## 4. User's reported pain points (NOT from the review)

### 4a. Wake-to-response lag of 30-40 seconds

Normal warm-path total: ~3-6s. Likely causes for 30-40s:

1. **GandalfAI cold WoL boot** (60-120s). Audible: WoL beep plays.
2. **Ollama model unload after 5-min idle.** Mitigation: `OLLAMA_KEEP_ALIVE=30m` on GandalfAI.
3. **SILENCE_SECS=1.5s.** Mandatory grace. Drop to 0.7s for 0.8s/turn win.
4. **STT/TTS first-call warmups.** 1-3s on first call after Docker restart.

### 4b. Kokoro voice (bm_lewis British male) sounds slow

Mitigation: KOKORO_SPEED config key, recommended starting value 1.15.

---

## 5. Completed work — Latency Observability + Kokoro Speed (DEPLOY phase)

A Claude Code session was authorized to DEPLOY this work. Status of the deployment is the current open question. Implementation spec (whether already present in commits or freshly implemented in the deploy session):

### Code changes
1. **KOKORO_SPEED config key** — added to `core/config.py` defaults, `_OVERRIDABLE`, `_TYPE_COERCE`. Lazy-imported in `tts.py:_synthesize_kokoro()` for restart-free hot reload. Default 1.0, range 0.5-2.0.
2. **[BENCH] log completion** — `assistant.py` emits complete per-turn `[BENCH]` lines: wake_to_record_start_ms, record_duration_ms, stt_ms, router_ms, llm_first_token_ms, llm_total_ms, tts_ms, play_start_ms, total_ms, gandalf_was_cold, model. Existing `iris_web.py /api/bench` parser preserved.
3. **Structured JSONL bench log** — `/home/pi/logs/iris_bench.jsonl` writes one JSON record per turn with stages + transcript + reply_chars + model + gandalf_was_cold + route + interrupted. Atomic append, try/except guarded.
4. **journald retention** — `pi4/etc/journald.iris.conf` (500MB, 1 year) + `pi4/scripts/install_journald.sh` installer. Persisted to `/etc/systemd/journald.conf.d/iris.conf` on Pi4.
5. **Intent log retention** — `core/intent_router.py` `_intent_logger` retention bumped to 365 days.
6. **Documentation** — CHANGELOG.md S50, HANDOFF_CURRENT.md, SNAPSHOT_LATEST.md, ROADMAP.md RD-007 stub, IRIS_CONFIG_MAP.md Voice/TTS table.

### Manual post-deploy actions REQUIRED (user does these in web UI / on GandalfAI)

These cannot be done by Claude Code:

1. ✅ or ❌ — Web UI → Voice tab → KOKORO_SPEED → set **1.15** → Save & Apply → Persist to SD (wait for green).
2. ✅ or ❌ — Web UI → Audio tab → "Wait after silence" → **0.7** (was 1.5) → Save & Apply → Persist to SD.
3. ✅ or ❌ — GandalfAI (manual Windows PowerShell):
   - `[Environment]::SetEnvironmentVariable("OLLAMA_KEEP_ALIVE","30m","Machine")`
   - `Restart-Service Ollama` (or via services.msc)
   - Verify: `ollama show iris` (should respond quickly)

**Next Sonnet chat should ask user to confirm each step is done before claiming the latency work is VERIFIED.**

---

## 6. What remains in the backlog

### Immediate value (user-felt)
- **A3 router regex tightening** — `pi4/core/intent_router.py`. Fixes "what year" false positive + 5 LOW. Sonnet, ~30 min.
- **A4 TTS fast-fail + audible error** — `pi4/services/tts.py`, `pi4/hardware/audio_io.py`. Sonnet, ~30 min.

### Latent risk
- **A1 iris_web chown** — `pi4/iris_web.py`. One-line bash extension. Sonnet, ~15 min.
- **A2 playback interrupt race** — `pi4/hardware/audio_io.py`. Per-playback session token. Sonnet, ~30 min.

### Coordinated refactor
- **B1 sleep-flag single-owner** — 5 files. **Opus** recommended for this one (multi-file coordination). ~60 min.

### Polish
- **C1 docs refresh** — Haiku, ~15 min.
- **D-series cleanup** (D1-D6) — see findings_MASTER.md.

### Open design decisions (Claude Desktop, not Claude Code)
- E1: AMUSED LED auto-off vs continuous breathe
- E2: intent-router.md unimplemented spec items (restart, eye-switch, timer, unit converter) — implement or remove
- E3: iris_web `api_chat` separate-channel design
- E4: follow-up loop inline classification gap

### Future tasks (waiting on data)
- **RD-007: Trend viewer / chart tab in iris_web** reading `iris_bench.jsonl`. After ~1 month of normal use (~100+ turns).

---

## 7. Continuity reminders

### Workflow rules (from CLAUDE.md and WORKFLOW_RULE.md)
- Claude Chat = planning, handoff generation, decisions. Claude Code = implementation.
- Never implement code in chat when Claude Code is available.
- REPO-ONLY unless user says DEPLOY.
- Show diff and wait for approval before any write.
- Status terminology: REPO-ONLY → PUSHED → DEPLOYED → VERIFIED. Nothing is "done" until VERIFIED.

### User preferences
- Verification-first. Assume AI outputs wrong until validated.
- Command-first, structured markdown, minimal explanation unless "explain" requested.
- No em dashes. No AI filler. Direct human tone.
- PowerShell for Windows, local-first solutions, modular scripts.
- For code/implementation/firmware tasks: respond with **"This looks like a Claude Code task. Want me to generate a handoff prompt?"** Do not plan, implement, or read files in chat. If yes, generate minimal handoff (≤400 tokens, no file reads, no architecture restatement).
- Exception: explicit requests for explanation, comparison, or conceptual help → proceed normally.
- **Homelab context**: this is the user's hobby/personal project, mostly working. Move with confidence not caution. 5-min git revert is acceptable failure recovery. Don't over-engineer safety for production-quality deploys when the user is the single operator.

### Model selection guidance for this project
- **Sonnet 4.6 = default** for chat. Handoff generation, task planning, doc updates, deploy verification, conversational analysis.
- **Opus 4.7** only for: multi-file coordinated refactors (B1), complex new feature design, adversarial review.
- **Haiku** for: pure mechanical docs find/replace, simple D-tier cleanup.

### What's on disk vs only in prior chats
**On disk (any Sonnet chat can read):**
- Full repo at `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face\`
- All 7 review files in `review/`
- This memo (`review/SESSION_MEMO_2026-05-17.md`)

**Lost across chats:**
- Conversational reasoning depth
- Handoff prompt texts (unless saved to disk or in CHANGELOG)
- Discussion threads about decisions

### Tracking system
The user manually maintains task status. No automated tracker file is currently in place. Future Sonnet chats can suggest creating one (`review/REVIEW_BACKLOG.md` flat checklist) but don't push it — user has limited time and competing priorities.

---

## 8. Suggested first prompts to Sonnet after seeding

Pick based on current need:

**If verifying that the latency observability deploy actually landed:**
> "Per Section 5 of the memo, the latency observability + Kokoro speed deploy was attempted. Help me build a 2-minute verification checklist I can run from the web UI and a 30-second SSH check from my phone if needed. Output as a numbered list with exact commands."

**If picking the next backlog task:**
> "Per Sections 3 and 6 of the memo, the recommended next task is A3 (router regex tightening). Generate the minimal Claude Code handoff prompt for A3, Sonnet model. Match the format/style of prior handoffs in this project."

**If working on something else:**
> "Context understood. New topic: [your topic]. Proceed normally per the homelab-context note in Section 7."

**If you want to interrogate any specific finding from the review:**
> "Read review/findings_session_N_*.md and walk me through Finding X in plain language including the operational impact."

---

## 9. Doc references for Sonnet (only read on demand)

These exist in the repo and Sonnet should read them as task-driven, not preemptively:

- `CLAUDE.md` — operating rules, hard constraints, session close template
- `docs/sysmap.json` — ports, IPs, GPIO pins, file paths, config defaults. Read this BEFORE IRIS_ARCH.md or IRIS_CONFIG_MAP.md for any lookup task.
- `IRIS_ARCH.md` — only when architectural reasoning, pipeline design, or failure mode context needed. Not for lookups.
- `IRIS_CONFIG_MAP.md` — only if sysmap.json does not contain the config detail needed.
- `HANDOFF_CURRENT.md` — current session pointer (updated each CC session)
- `SNAPSHOT_LATEST.md` — current verified state of all systems
- `CHANGELOG.md` — completed work history
- `ROADMAP.md` — forward-looking tasks with full spec
- `iris_issue_log.md` — append-only issue records
- `intent-router.md` — intent router feature guide
- `MAESTRO_QUICKREF.md` — user's personal quick reference
- `GUIDE-settings.md` — web UI settings explainer

Sonnet: do NOT read all of these in one go. Read only the doc that matches the task at hand.

---

*End memo. Updated 2026-05-18 with deploy status reflection and Sonnet-as-default-model directive.*

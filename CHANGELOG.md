<!-- Completed history only. Do not edit prior entries. Append new entries at the bottom. -->

# IRIS Changelog

Entries are in chronological order, oldest first. Active and forward-looking items are in `ROADMAP.md`.

---

## S113 — qwen3.5:27b Modelfile Swap + GPU Offload Failure (2026-06-09)

**Status:** PARTIAL — models rebuilt, GPU offload failed, Ollama upgrade needed

**Goal:** Swap both iris and iris-kids from qwen2.5vl:32b-q4_K_M to qwen3.5:27b to restore GPU text inference (~40 tok/s expected vs 2.8 tok/s CPU-only on VL base).

**What was done:**

1. **`ollama/iris_modelfile.txt`** — DEPLOYED.
   - `FROM qwen2.5vl:32b-q4_K_M` → `FROM qwen3.5:27b`
   - Added `PARAMETER think false` (disables qwen3.5 thinking mode — required to suppress `<think>` blocks)
   - Stop token `<|im_end|>` confirmed correct for qwen3.5.
   - AMUSED calibration block preserved.

2. **`ollama/iris-kids_modelfile.txt`** — DEPLOYED.
   - `FROM qwen2.5vl:32b-q4_K_M` → `FROM qwen3.5:27b`
   - Added `PARAMETER think false`
   - Stop token `<|im_end|>` confirmed correct.

3. **GandalfAI model rebuild** — DEPLOYED.
   - `qwen3.5:27b` (17GB) confirmed present (pre-pulled by user).
   - `ollama create iris` and `ollama create iris-kids` both succeeded. Fresh timestamps, 21GB each.

4. **`tools/workbench/workbench.js`** — REPO-ONLY (uncommitted).
   - `AbortSignal.timeout(60000)` → `AbortSignal.timeout(90000)` in `runHarness()`
   - Fallback string `"iris (qwen2.5:32b)"` → `"iris"` in `callAnthropicLatencyAnalysis()`

**GPU verification — FAILED:**
- Warm inference: 2.8 tok/s (two runs). Matches CPU inference rate.
- VRAM: 23,799 MiB used of 24,326 MiB — model IS loaded in VRAM.
- GPU utilization: 0% during inference — compute dispatching to CPU.
- Root cause: Ollama 0.24.0's llama.cpp build predates qwen3.5 architecture. Weights load into VRAM but GPU dispatch not supported for this architecture at this engine version.
- Hard stop triggered per task spec.

**Parts D (harness), C (GPU verify beyond stop) not completed.**

**IRIS text queries currently broken — 2.8 tok/s CPU-only on qwen3.5:27b.**

**Next required action:** Upgrade Ollama on GandalfAI to 0.30.0 (0.30.x VL CLIP restriction no longer applies — we are off VL base). User authorized upgrade during session but it was not executed. Run:
```powershell
$env:OLLAMA_VERSION="0.30.0"; irm https://ollama.com/install.ps1 | iex
```
Then re-apply Windows Firewall outbound block for `ollama app.exe`. Rebuild both models. Verify tok/s ≥ 30.

**Rollback (if 0.30.0 also fails GPU dispatch):**
```
git checkout HEAD -- ollama/iris_modelfile.txt ollama/iris-kids_modelfile.txt
# pull qwen2.5:32b if not present, then:
ollama create iris -f C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt
ollama create iris-kids -f C:\IRIS\IRIS-Robot-Face\ollama\iris-kids_modelfile.txt
```

---

## S114 — qwen3.5:27b GPU Fix + think:false Pipeline Patch (2026-06-09)

**Status:** COMPLETE — IRIS fully operational

**Goal:** Fix IRIS text inference (2.8 tok/s CPU-only from S113). Root cause: Ollama 0.24.0 didn't GPU-dispatch qwen3.5:27b. Also add `"think": false` to all Ollama API calls (qwen3.5 thinking model consumes tokens in `thinking` field, leaving `response` empty without it).

**What was done:**

1. **GandalfAI Ollama** — Already at 0.30.7 (no upgrade needed). GPU dispatch confirmed: **35.2 tok/s** on RTX 3090. VRAM: model in VRAM, GPU utilization confirmed.

2. **Modelfiles — `PARAMETER think false` removed** (unsupported in Ollama 0.30.7, caused `ollama create` error with "unknown parameter 'think'"). `"think": false` moved to API request level.
   - `ollama/iris_modelfile.txt` — DEPLOYED+VERIFIED (rebuilt on GandalfAI)
   - `ollama/iris-kids_modelfile.txt` — DEPLOYED+VERIFIED (rebuilt on GandalfAI)

3. **Pi4 pipeline — `"think": False` added to all Ollama callers:**
   - `pi4/assistant.py` — ask_ollama() and warmup call. md5=1c42e3dd707281eaacc2cb2380394743 RAM=SD. DEPLOYED+VERIFIED.
   - `pi4/services/llm.py` — stream_ollama() payload. md5=e93c69c2430415826baeaf05e247c853 RAM=SD. DEPLOYED+VERIFIED.
   - `pi4/iris_post.py` — l3_llm POST test. md5=2bf0723a7f06d8f72896f3178af0e8ec RAM=SD. DEPLOYED+VERIFIED.
   - `pi4/services/vision.py` — ask_vision() /api/generate call. md5=a60ffceaa8364678d2dffd04cbb951fc RAM=SD. DEPLOYED+VERIFIED.

4. **`pi4/core/config.py`** — `VISION_MODEL = "qwen2.5vl:32b-q4_K_M"` → `"iris"`. qwen3.5:27b handles vision natively. md5=f7a143d855a06c9b3fb8292e58ef363c RAM=SD. DEPLOYED+VERIFIED.

5. **`tools/workbench/workbench.js`** — `"think": false` added to both /api/generate calls (harness + latency tester). REPO-ONLY.

**Verification:**
- Pi4 POST: **20/23 PASS, WARN: 3, FAIL: 0** (was 19/23 FAIL: 1 on LLM smoke before iris_post.py patch).
- AMUSED calibration: "You're dumb." → `[EMOTION:AMUSED]` ✓
- GPU inference: 35.2 tok/s ✓ (target ≥30)
- No think block in responses ✓
- **pt001 persona harness: 16/20 PASS (80%)** — target ≥13/20 MET.
  - FAIL: pt001_01 (ANGRY not AMUSED on "You're dumb."), pt001_04 (ANGRY not NEUTRAL on "Shut up."), pt001_18 (CURIOUS not NEUTRAL on motor/servo), pt001_19 (NEUTRAL not AMUSED on sleep advice).

---

## S115 — Intent Router Time Fix + ANGRY Overtrigger Patch (2026-06-09)

**Status:** COMPLETE — DEPLOYED+VERIFIED

**Goal:** (A) Fix "what time is it" routing to LLM (~1434ms) instead of Layer 2 UTILITY (<200ms). (B) Fix "You're dumb." returning [EMOTION:ANGRY] despite S112 AMUSED calibration block. (C) Confirm SILENCE_SECS.

**What was done:**

1. **`pi4/core/intent_router.py`** — `_TIME_RE` pattern fix.
   - Added `what time is it` explicitly at start of pattern (definitive literal match).
   - Added `time please` variant.
   - Root cause: the existing `time is it` substring match and `what time\b` lookahead should theoretically match, but the explicit literal eliminates any runtime ambiguity.
   - md5=ea9e0d82425f76d98053c2b71221ef99 RAM=SD. DEPLOYED+VERIFIED.
   - Verified via `IntentRouter.classify()` on Pi4: `route=UTILITY action=TIME llm=false` in iris_intent.log.

2. **`ollama/iris_modelfile.txt`** — adversarial few-shot ANGRY patch.
   - `FEW-SHOT EXAMPLES - ADVERSARIAL INPUT HANDLING` block, "You're dumb." example: `[EMOTION:ANGRY]` → `[EMOTION:AMUSED]`.
   - The old ANGRY example was winning over the EMOTION CALIBRATION block added in S112.
   - iris rebuilt on GandalfAI. DEPLOYED+VERIFIED.
   - Smoke test: "You're dumb." → `[EMOTION:AMUSED]` confirmed.

3. **VAD check (read-only)** — `SILENCE_SECS=1.2` confirmed in iris_config.json (overrides config.py default of 1.5). No change needed.

**Verification:**
- `what time is it` → intent log: `route=UTILITY | confidence=HIGH | llm=false` ✓
- `what's the time`, `time please` also route UTILITY ✓
- "You're dumb." → `[EMOTION:AMUSED]` on GandalfAI smoke test ✓
- SILENCE_SECS=1.2 confirmed ✓

**Rollback:** `git checkout -- pi4/core/intent_router.py ollama/iris_modelfile.txt` then redeploy intent_router.py and rebuild iris model.

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

---

## Unlabeled session — 2026-05-02 ~20:48–23:18 (RD-001 STOP phrase gate + doc restructure)

**Status:** DEPLOYED to Pi4. No session number was assigned.

**Commits:** `279adb9`, `b00dea9`, `54d576c`, `50b4e52` (retroactively documented S49)

Note: doc commits `279adb9` and `b00dea9` landed ~70 minutes before the code commit `54d576c`. This session had no session close report.

- **`279adb9`** — docs: split IRIS handoff, roadmap, snapshot, and changelog into separate files.
- **`b00dea9`** — docs: organize audits and wakeword import plan.
- **`54d576c`** — `pi4/assistant.py` — `STOP_PHRASES` gate added to main loop after Whisper transcript normalization, before router/hallucination handling. Boundary-aware matching (exact match or phrase-followed-by-space). Avoids false matches on "stopwatch", "quietly", "cancelled". Deployed and persisted to Pi4 (md5 verified). Does not fix Whisper hallucination of "stop" into unrelated text — pre-STT intercept is a future task (RD-001).
- **`50b4e52`** — Update handoff for RD-001 deploy.

---

## S46 — WoL Acknowledgement Beep

**Status:** DEPLOYED+VERIFIED (commit 08c7b60, 2026-05-03)

Session boundary note: commit `abfdb7c` carries an S46 label but its message reads "pre-RD-002 state commit". It was made ~2.5 hours after the S46 deploy and describes setup for S47 (RD-002). The S46 label on that commit is an artifact — its content belongs to S47 prep.

Implemented:
- `pi4/assistant.py` — `play_wol_beep()` added. `ensure_gandalf_up()` gains optional `pa=None` parameter. Ascending 2-tone beep (660 Hz → 880 Hz, ~360 ms) plays on Pi4 speakers when WoL packet is sent and GandalfAI is offline. No beep when GandalfAI is already up.
- `pi4/hardware/audio_io.py` — beep implementation.
- Deployed and persisted to Pi4 (md5 verified). assistant.py restarted — `[INFO] Ready.` confirmed.

---

## S47 — RD-002 AMUSED Emotion Full Implementation

**Status:** FULLY DEPLOYED (2026-05-03). Pi4: config.py, led.py, iris_web.html — md5 verified, assistant active. Teensy 4.1: firmware flashed by user. GandalfAI: iris-kids model rebuilt. Pending: live behavior verification.

**Commits:** `734149a` (implementation, 2026-05-03), `287938d` (docs: add status terminology rule — S47 close activity, committed without S47 label)

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

## S48 — NUM_PREDICT Removal + PT-001 Few-Shot Adversarial Examples

**Status:** Task 1 DEPLOYED+VERIFIED. Task 2 REPO-ONLY.

Implemented:
- **Pi4 `iris_config.json`** — `NUM_PREDICT: 200` key removed. SD persisted (md5 verified). assistant.py restarted — `[INFO] Ready.` Tiered classifier (SHORT=120, MEDIUM=350, LONG=700, MAX=1200) now controls LLM response length.
- **`ollama/iris_modelfile.txt`** — PT-001: 8 few-shot adversarial examples added (insults, identity challenges, NEUTRAL deflections). Inserted after ANGRY emotion rule, before NEVER say block.

Both models rebuilt on GandalfAI. PT-001 DEPLOYED.

---

## S49 — Web UI Rework

**Status:** DEPLOYED to Pi4 (commit `6509cca`, 2026-05-06). Pending: live verification in browser.

Implemented:
- **`pi4/iris_web.py`** — `/api/generate` renamed to `/api/chat` (fixed 404 on all chat sends). `api_chat()` now calls `extract_emotion_from_reply()` + `clean_llm_reply()` before TTS — emotion tags and markdown no longer spoken aloud. New `/api/speak` endpoint for verbatim TTS (bypasses LLM). `/api/logs` rewritten to return structured `{events: [...]}` JSON with category, timestamp, message, detail fields.
- **`pi4/iris_web.html`** — Log tab: raw journalctl dump replaced with categorized event panel + filter bar (All / Wakeword / Heard / Route / LLM / Spoken / STOP / Drift / Errors). Chat tab: verbatim speak mode added. Emotion tag displayed inline. TTS conflict warning note added.

---

## S50 — Perceived Latency Hardening + Observability + Kokoro Speed Control

**Status:** DEPLOYED (commit `bae8da0`, 2026-05-18). Pi4 live, md5 verified, assistant restarted — `[INFO] Ready.` confirmed. Pending: user voice verification + manual post-deploy steps (KOKORO_SPEED dial-in, SILENCE_SECS, OLLAMA_KEEP_ALIVE on GandalfAI).

Goal: Add configurable Kokoro speed, complete bench timing instrumentation, long-retention JSONL bench log, journald retention bump, and intent log retention bump.

Implemented:
- **`pi4/core/config.py`** — `KOKORO_SPEED = 1.0` added; registered in `_OVERRIDABLE` and `_TYPE_COERCE` (float, 0.5–2.0). Web UI can set speed without assistant restart.
- **`pi4/services/tts.py`** — `_synthesize_kokoro()` lazy-imports `KOKORO_SPEED` per call and passes `"speed": KOKORO_SPEED` to Kokoro-FastAPI payload. Re-read on every TTS call — no restart needed after web UI change.
- **`pi4/assistant.py`** — `_bench_write()` helper added. Every turn (REFLEX/COMMAND/UTILITY/LLM) that reaches `play_pcm_speaking` now appends one JSON record to `/home/pi/logs/iris_bench.jsonl`. New bench stages: `wake_to_record_start_ms`, `record_duration_ms`, `router_ms`, `play_start_ms`, `total_ms`, `gandalf_was_cold`, `model`. All existing `[BENCH]` lines supplemented with new `_ms` fields; engine label corrected from "chatterbox" → "kokoro". All bench logging wrapped in try/except.
- **`pi4/core/intent_router.py`** — `backupCount` bumped from 7 to 365 days.
- **`pi4/etc/journald.iris.conf`** (new) — `SystemMaxUse=500M`, `MaxRetentionSec=1year`.
- **`pi4/scripts/install_journald.sh`** (new) — Copies conf to `/etc/systemd/journald.conf.d/iris.conf` and restarts journald. Must be run once after deploy and persisted via overlayfs.
- **`IRIS_CONFIG_MAP.md`** — `KOKORO_SPEED` row added to Kokoro table.
- **`ROADMAP.md`** — RD-007 stub added (bench trend viewer in iris_web).


---

## S51 — Intent Router Regex Hardening

**Status:** DEPLOYED (2026-05-18). Pi4 live, md5 `184e38ae685ce03f00e05cf29b3c0adf` verified at both `/home/pi/core/intent_router.py` and `/media/root-rw/overlay/home/pi/core/intent_router.py`. assistant.py restarted — service active.

**Goal:** Fix 4 false positives in `intent_router.py` identified in `review/findings_session_4_router.md` (Opus 4.7 audit). Primary fix: `_DATE_RE` false positive routing historical year questions to the date handler.

**Changes to `pi4/core/intent_router.py`:**

1. **`_TIME_RE` tightened** — Negative lookahead blocks `(did|was|were|happened)` after `what time` and `what hour`. Also blocks `current time travel`.
2. **`_DATE_RE` tightened** (primary fix) — Negative lookahead blocks `(did|was|were|happened|built|born|died|founded|invented|started|ended)` after `what (year|month|day|date)`. "What year did the Civil War end?" now routes to LLM; "What year is it?" still routes to DATE.
3. **`_KIDS_OFF_RE` tightened** — Removed bare `adult mode` and `normal mode` alternatives (too generic; matched casual speech with no kids-mode intent).
4. **`_random_number_reply`** — `digit` keyword now returns 0–9 range instead of 1–100.
5. **`_layer2_utility` RANDOM_NUMBER** — `payload={"result": reply.rstrip(".")}` added; result now logged in intent log.

**Findings applied:** 4.5 (MED: _DATE_RE historical false positive), 4.7 (LOW: KIDS_OFF bare adult/normal mode), 4.9 (LOW: random number log missing result), 4.10 (LOW: digit range).
**Findings not applied:** 4.6 (volume patterns — too risky without live testing), 4.1/4.2/4.3/4.4/4.8 (out of scope).

**Deploy note:** sftp_write truncates overlayfs writes to `/home/pi/core/` directly. Workaround: sftp_write base64 to `/tmp/` then `mv`. Both `/home/pi/core/` and `/media/root-rw/overlay/home/pi/core/` are the same inode — no separate SD copy step needed after `mv`.

---

## S52 — Web UI: KOKORO_SPEED Slider, Chat TTS Kokoro Force, Vision Demo Panel

**Status:** DEPLOYED (2026-05-18). Pi4 live, md5 verified (`iris_web.py` `59115bdda6f063faffde1f7593f54c61`, `iris_web.html` `e1ddf120dc8d0667544eda105d9cf1ec`), iris-web restarted — Flask serving on 0.0.0.0:5000 confirmed.

**Goal:** Three Web UI improvements — KOKORO_SPEED slider in Voice tab, Kokoro TTS force in chat (bypassing stale module-level import), Vision Demo panel with /api/vision endpoint.

**Changes to `pi4/iris_web.py`:**

- `_speak_worker` rewritten to call Kokoro API directly from live `cfg` dict (`KOKORO_VOICE` + `KOKORO_SPEED`). Piper fallback retained. Root cause fixed: previous code imported `KOKORO_ENABLED` at module level — stale constant caused all chat TTS to fall back to Piper.
- `/api/vision` endpoint added: libcamera-still capture → base64 → Ollama `/api/generate` with `images` field → emotion strip + clean → optional Kokoro speak. Uses `VISION_MODEL` from live cfg.

**Changes to `pi4/iris_web.html`:**

- Voice tab: `KOKORO_SPEED` slider field added (0.5–2.0, step 0.05). Kokoro Web UI link fixed (`/web` suffix). `saveKokoroSettings()` now includes KOKORO_SPEED in the POST to `/api/config`.
- Chat tab: Vision Demo card added — 5 preset prompts, custom input, Kokoro speak toggle, calls `/api/vision`.

**Also this session:** Removed approval gate from `CLAUDE.md` (pre-flight summary + wait-for-confirmation steps eliminated). Commit `bda42c9` pushed.

---

## S53 — Bench Tab: 20-Cycle History, To First Word Column, Expanded Headers

**Status:** DEPLOYED (2026-05-19). Pi4 live, md5 verified (`iris_web.py` `5fc8b075e52bf0dd4bc26f39e507f3dc`, `iris_web.html` `7d3a63f629a5195085a753e93b541cff`), iris-web restarted — Flask serving on 0.0.0.0:5000 confirmed.

**Goal:** Four Bench tab improvements — history depth, new latency column, readable column headers, usability polish.

**Changes to `pi4/iris_web.py`:**
- `api_bench`: cycle limit changed from `[-25:]` to `[-20:]`.

**Changes to `pi4/iris_web.html`:**
- History table now retains and displays last 20 cycles (was 25).
- New column "To First Word": `dur_total − dur_audio` = wakeword to speaker start. Inserted between Playback and End-to-End. Color coded green/amber/red (< 4s / 4–7s / > 7s).
- All 14 column headers expanded to plain English: `trig`→Trigger, `np`→Token Limit, `rec`→Recording, `stt`→Transcription, `ttfc`→1st LLM Chunk, `llm`→LLM Stream, `tts`→TTS Synth, `aud`→Playback, `TOTAL`→End-to-End, `eval/prompt`→Tokens (Eval/Prompt).
- Hint paragraph rewritten to match new column names.
- Transcript column: snippet length 22→45 chars, `min-width:200px / max-width:360px`, full text in `title` tooltip on hover.
- Trigger column: `.slice(0,6)` removed — full trigger name displayed.
- All five `colspan="14"` references updated to `15`.

---

## S54 — RD-008: Mouth TFT Visual Overhaul (BL curve, idle animations, Pi4 dimming)

**Status:** Firmware REPO-ONLY (A+B+C) — flash pending. Pi4 (D) DEPLOYED + VERIFIED.

**Commits:** `4e7c61b` (firmware A+B+C), `bd6598b` (Pi4 D).

### Sub-task A: Backlight PWM log curve

- Replaced linear map (`level*17`) with `BL_MAP[16]` lookup in `mouth_tft.cpp`.
- Curve: `{0,2,4,7,11,16,22,30,40,55,75,100,135,175,210,255}` — low end compressed.
- intensity 0=off, 1=2/255 (nearly dark), 8=40/255 (comfortable), 15=255.
- All four `analogWrite(MOUTH_TFT_BL)` call sites converted. `_currentBLLevel` tracks live state.

### Sub-task B: Mouth bitmap colors

- Colors already implemented in prior session — confirmed correct per spec.
- Added `MTFT_AMBER=0xFD20` constant (reserved for AMUSED; currently reuses CURIOUS smirk index 2).
- Fixed stale comment: BL pin is GPIO 5.

### Sub-task C: Idle animations (Teensy)

Six animations: BREATHE (45s BL sine), DRIFT (20s subtle pulse), TWITCH (smirk 400ms), BLINK (BL-off 150ms), YAWN (surprised oval 600ms + BL bump), SIDESMIRK (smirk 800ms + BL bump).
All millis()-based, no delay(). Interrupted immediately by mouthIdleStop().
IDLE:START / IDLE:STOP serial commands. Auto-start after 120s inactivity.
`mouthIdleTick()` called each non-sleep loop() iteration.

### Sub-task D: Pi4 idle dimming (DEPLOYED)

- `config.py`: `MOUTH_INTENSITY_IDLE=3`, overridable via iris_config.json (int, 0-15).
- `assistant.py`: wakeword → send MOUTH_INTENSITY_AWAKE; end of LLM+TTS+followup → send MOUTH_INTENSITY_IDLE.
- Pi4 md5 verified (config `535d62b3`, assistant `259dd0a1`). SD persisted. Assistant running.

**Remaining:** Flash firmware via PlatformIO upload. Dark-room verify: sleep=dark, idle=dim, wakeword=bright, post-speech=dim.

## servo-pico Pico W update (2026-05-20)

- I2C pins fixed for Pico W: `Wire.setSDA(6)` + `Wire.setSCL(7)` before `Wire.begin()` in setup().
- TTP223B capacitive touch toggle added on GPIO 15 (physical pin 20): single tap enables/disables servo tracking. `servoEnabled` starts `false` (tracking off at boot).
- `sysmap.json` servo_pico section updated: hardware=Pico W, source path corrected, GPIO 14/15 added, tunable constants current.

## Pico W servo-pico overhaul (2026-05-20)

- Switched from Mbed core to Earle Philhower RP2040 core — fixes Wire.setSDA/setSCL and ServoEasing compatibility.
- Removed tilt servo (pan only).
- Added TTP223B touch toggle on GPIO 15 (servo enable/disable, starts disabled).
- I2C explicit pin assignment: Wire.setSDA(6), Wire.setSCL(7) for Pico W.
- Sketch moved to IRIS-BaseServoControlViaPerson_Sensor/ subdir (Arduino IDE requirement).
- Pico W successfully reflashed bare board via BOOTSEL, COM10.
- HW-002 partially resolved: BOOTSEL accessible on bare board. Enclosure wiring (RUN pin, switch) deferred to PCB rewiring.
- RD-009 planned: WiFi touch integration (volume, TTS interrupt, wakeword). Full spec in review/HANDOFF_PICO_WIFI_TOUCH.md.

## Servo Controller Hardware Evolution — Pico W → ESP32 → Teensy 4.0 (S56–S59)

**Summary:** The servo base mount controller went through two board replacements before reaching its current state.

- **Pico W** — Original servo controller. Firmware developed with Earle Philhower RP2040 core + ServoEasing. Had USB enumeration hardware failure (S56) — no USB detected on any port.
- **ESP32 DevKit 1C** (S57) — First replacement board. Firmware rewritten for ESP32 (servo_esp32/ directory). PCB was destroyed during enclosure work (S58) — board tombstoned. servo_esp32/ directory removed.
- **Teensy 4.0** (S58) — Final replacement. Firmware renamed to `servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`. ServoEasing library retained. USB to Pi4 at `/dev/ttyACM1`, later `/dev/ttyIRIS_SERVO` (S63 udev symlinks). DEPLOYED+VERIFIED S59.

Current servo controller is Teensy 4.0. ESP32 and Pico W are tombstoned. All HW-002/RD-009/RD-010/RD-011 roadmap items referencing ESP32 closed (removed from ROADMAP S68 docs pass).

---

## S61 — Event Log Persistence + Gesture Monitoring (2026-05-23)

**Status:** DEPLOYED+VERIFIED. Commits `8ee2519` (S61) + `5af1073` (S61b). All 4 files md5-confirmed RAM=SD. iris-web restarted, /api/logs returning 82 events from SD history on first load.

**Goal:** Ensure all IRIS events survive Pi4 reboots and are reviewable in the web UI. Add a gesture monitoring interface in the Gestures tab. 100MB log retention ("forever or 100MB").

**Root causes fixed:**
1. `_MSG_RE` regex wrong — was `assistant|iris.web`, actual journald format is `python3[PID]`. Event log was silently dropping all events (showed nothing).
2. Cron overwrite bug — `iris_log_export.sh` used `> file` (overwrite) + `--boot`. As journald rotated, each cron run replaced the SD file with progressively fewer events, destroying history. Fixed: append mode + timestamp tracking.
3. Cron interval too slow — was `*/15`, changed to `*/5` (must beat ~35-min journald rotation window).

**Changes:**
- **`pi4/iris_web.py`** — Fixed `_MSG_RE`. Module-level `_parse_event_msg()` + `_sd_events(n_days=3650)`. `/api/logs` merges journalctl + all SD daily logs (deduped, capped 500). Added `[GESTURE]` + legacy `[BASE]` gesture parsing. New `/api/gesture_log` endpoint (200-event gesture history from SD+journal). md5 `0561d413`.
- **`pi4/iris_web.html`** — `cat-gesture` CSS, `f-gesture` filter. Gesture filter button in Logs tab. Gesture Event Log card in Gestures tab (auto-refresh 30s, date+time display, 300px). md5 `84531409`.
- **`pi4/hardware/base_mount_bridge.py`** — Gesture output changed to structured `[GESTURE] gesture={line} action={action}` (was `[BASE] {line}`). Connection/error messages remain `[BASE]`. md5 `30f3e04b`.
- **`pi4/scripts/iris_log_export.sh`** — Rewritten: append mode, timestamp tracking (`/run/iris_log_last_ts`), 100MB size-cap (oldest daily files removed). md5 `47b0959e`.
- **`pi4/scripts/iris-logs.cron`** — Updated `*/15` → `*/5`. `/etc/cron.d/iris-logs` updated on Pi4.

---

## S61b — GandalfAI Log Backup + SLEEP/WAKE Gesture Actions (2026-05-23)

**Status:** DEPLOYED+VERIFIED. All files md5-confirmed RAM=SD.

**Goal:** Persist IRIS logs to GandalfAI (permanent LAN workstation backup). Add SLEEP/WAKE as assignable gesture actions.

**Changes:**
- **`pi4/scripts/iris_log_export.sh`** — Added scp block: copies all daily logs to `gandalf@192.168.1.3:C:/IRIS/iris-logs/` using `/home/pi/.ssh/id_iris_logs` (ed25519, BatchMode). Runs every 5 min with existing cron. md5 `5fe88e7d`.
- **`pi4/hardware/base_mount_bridge.py`** — Added SLEEP and WAKE dispatch cases: send `EYES:SLEEP`/`EYES:WAKE` UDP to CMD_PORT 10500. These trigger the full `_do_sleep()`/`_do_wake()` sequences in assistant.py (starfield eyes, snore mouth, LED dim, /tmp/iris_sleep_mode). md5 `dc944097`.
- **`pi4/iris_web.html`** — SLEEP/WAKE added to `_GESTURE_ACTIONS` + `_GESTURE_LABELS`. Gesture Event Log hint updated to reference GandalfAI backup. md5 `d1c15589`.
- **GandalfAI setup** — `C:\IRIS\iris-logs\` directory created. `C:\ProgramData\ssh\administrators_authorized_keys` configured with pi4-iris-logs public key (Windows OpenSSH admin override). icacls: SYSTEM:F + Administrators:F, no inheritance. 7 daily log files confirmed on GandalfAI.
- **Pi4 SSH key** — ed25519 at `/home/pi/.ssh/id_iris_logs` + `/media/root-ro/home/pi/.ssh/id_iris_logs`. SD-persisted across reboots.

---

## S62 — Sleep Animation Enhancement (2026-05-24)

**Status:** REPO-ONLY. src/main.cpp, mouth_tft.cpp, sleep_renderer.h changed locally. Teensy 4.1 firmware flash pending (user PlatformIO upload, env:eyes, COM7). Pi4 SLEEP_CFG_MAP deployed but Teensy firmware does not yet handle SLEEP_CFG: commands.

**Goal:** Enhance Teensy 4.1 sleep animation — amplified starfield, crescent moon glow, Earth planet, warp streaks. Add SLEEP_CFG: serial command so Pi4 can tune animation parameters without reflash.

**Changes:**
- **`src/sleep_renderer.h`** — Amplified star brightness, crescent moon glow, Earth-like planet, warp streaks animation.
- **`src/mouth_tft.cpp`** — mouthSleepFrame() enhanced.
- **`src/main.cpp`** — SLEEP_CFG: command handler added (parses key=val, updates animation params).
- **`pi4/assistant.py`** — SLEEP_CFG_MAP dict + updated _do_sleep() to push SLEEP_CFG: params on sleep entry. Deployed to Pi4 during S62. Local commit pending.

---

## S63 — WebUI→Teensy Fix + Persistent USB Device Identity (2026-05-25)

**Status:** DEPLOYED (udev rules + config.py + CMD listener auto-wake). Local repo sync complete. Commit pending.

**Goal:** Fix webUI buttons (emotion, eye select, mouth) having no effect on Teensy 4.1 displays. Prevent recurrence via hardware-identity-based USB device naming.

**Root causes:**
1. **USB port swap** — Teensy 4.0 and 4.1 were physically connected to swapped Pi4 USB ports. Linux `/dev/ttyACM*` assignment is port-position-based. Swapping ports meant Teensy 4.1 was on `/dev/ttyACM1` (assigned to base mount) and Teensy 4.0 was on `/dev/ttyACM0` (assigned to eyes). All eye/mouth commands went to the wrong device.
2. **Sleep mode display bypass** — Even after fixing the port swap, EMOTION:/EYE:/MOUTH: commands arrived via CMD listener while `eyesSleeping=true`. Teensy firmware processes these in `processSerial()` but `loop()` returns early when sleeping — the eye engine and mouth TFT never render. Commands silently succeeded at the serial level but produced no visual output. APA LEDs responded because they are driven from Pi4 Python directly, not through the sleep early-return.

**Changes:**
- **`pi4/scripts/99-iris-teensy.rules`** (NEW) — udev rules binding `/dev/ttyIRIS_EYES` to Teensy 4.1 (USB serial 13625440) and `/dev/ttyIRIS_SERVO` to Teensy 4.0 (USB serial 12763490). Survive all port swaps and reboots. DEPLOYED to `/etc/udev/rules.d/99-iris-teensy.rules` + udevadm reload.
- **`pi4/core/config.py`** — `TEENSY_PORT = "/dev/ttyIRIS_EYES"`, `BASE_MOUNT_PORT = "/dev/ttyIRIS_SERVO"`. DEPLOYED+VERIFIED.
- **`pi4/assistant.py`** — CMD listener: auto-wake added (if `state.eyes_sleeping` and EMOTION:/EYE:/MOUTH: command arrives, `_do_wake()` fires before forwarding). Also synced SLEEP_CFG_MAP + updated _do_sleep() + BaseMountBridge leds arg from deployed S62 state (S62 had deployed these without local commit). CMD listener patch DEPLOYED; full file sync REPO-ONLY.
- **`docs/sysmap.json`** — `serial.device` → `/dev/ttyIRIS_EYES`, `pico_serial` replaced with `teensy40_serial` + `udev_rules` section, `servo_pico` node renamed `teensy40` with correct hardware/source/GPIO.
- **`IRIS_ARCH.md`** — USB Device Identity section added. All `/dev/ttyACM*` references updated. Hard rule added: never hardcode `/dev/ttyACM*` in code, config, or commands.

---

## S65 — Cosmic Sleep Animation Overhaul + Web UI Sliders (2026-05-25)

**Status:** Firmware FLASHED (Teensy 4.1, env:eyes, COM7). Pi4 files REPO-ONLY — iris_web.html, iris_web.py, config.py pending DEPLOY.

**Goal:** Rebuild Teensy 4.1 sleep animation to visually match HTML v8 mockup (Saturn+Moon+warp particles+nebula+3-wave mouth+symmetric ZZZ). Add SLEEP_CFG: serial protocol so Pi4 can push 24 animation parameters to Teensy on each sleep entry without reflash. Wire all parameters to live web UI sliders in a new Sleep Animation card.

**Changes:**

- **`src/sleep_cfg.h`** (NEW) — Shared struct header: `SleepCfg` (25 fields: speed, starCount, starBrightMin/Max/TwinkleAmp, shootCount/Speed/Len/Bright, warpCount/Speed/Bright, moonR/Drift, saturnR/Drift, nebulaAlpha, waveAmp0/1/2, waveOscAmp, mouthPulseAlpha, zzzAlpha0/1/2) + `extern SleepCfg sleepCfg`. Solves GC9A01A_t3n.h / ILI9341 header conflict — mouth_tft.cpp includes only this header.

- **`src/sleep_renderer.h`** (FULL REWRITE v3) — Cosmic animation: Saturn with back/front ring scanlines (ellipse math, tilt=0.42, 4 colors), Moon with crescent+glow, 48 warp particles (LFSR-seeded angles/speeds, radial outward motion), starfield (twinkle), nebula overlay. ZZZ removed from eyes (moved to mouth per v8 spec). SR_FRAME_MS=155ms (~6.4fps). Moon top-right/left; Saturn bottom-left/right. `SleepCfg sleepCfg = {.speed=0.85, ...}` defined here (single TU via main.cpp).

- **`src/mouth_tft.cpp`** — `mouthSleepFrame()` fully rewritten: clear ZZZ zone (fillRect 0,4,320,67), draw 3 symmetric Z-pairs per side (6 Z total, sinusoidal Y drift, cyan from sleepCfg.zzzAlpha*), 3-wave band y=76..162 (blue 0x001F, purple 0x780F, teal 0x0318; primary+0.35x secondary at 1.7x freq matching v8 formula). cy oscillation capped ±14px for SWSPI band constraint.

- **`src/main.cpp`** — `SERIAL_BUF_SIZE` 32→40 (accommodates longest SLEEP_CFG: token). Added `SLEEP_CFG:` handler in `processSerial()`: splits on `=`, maps all 24 SleepCfg field names to struct members.

- **`pi4/core/config.py`** — 24 `SLEEP_ANIM_*` constants added with defaults matching v8 spec (speed=0.85, warpCount=12, moonR=28, saturnR=22, etc.). All added to `_OVERRIDABLE` set and `_TYPE_COERCE` dict with type + slider range bounds.

- **`pi4/iris_web.py`** — `_SLEEP_CFG_KEYS` dict (short name → SLEEP_ANIM_* config key). `/api/sleep_cfg` GET: returns 24 current values keyed by short name. POST: maps short keys to SLEEP_ANIM_* and writes via `write_cfg()`.

- **`pi4/iris_web.html`** — Sleep Animation card with 4 `<details>` groups (Stars & Warps, Shooting Stars, Objects, Mouth), 24 sliders. `_buildSaSliders(data)` renders all sliders dynamically. `_saCfgSend(key,val)` debounced 180ms POST to `/api/sleep_cfg`. `_loadSaSliders()` fires GET on first Sleep tab open. Sleep nav button wired: `tab('sleep',this);_saTabHook()`.

**Animation speed:** SR_FRAME_MS=155ms (was 130ms), `speed` default 0.85 (was 1.0). ~17% overall slowdown per user request.

---

## S66 — IRIS Power-On Self-Test (POST) (2026-05-25)

**Status:** REPO-ONLY — Pi4 files pending DEPLOY.

**Goal:** Add a comprehensive 5-layer startup diagnostic that runs automatically at boot and on demand via web UI or SSH. Surfaces hardware faults, service outages, and config drift before any user interaction.

**Changes:**

- **`pi4/iris_post.py`** (NEW) — 5-layer POST sequence implemented as `_POST` class + `run_post(leds, teensy, pa, verbose)` public API. L0: serial /dev/ttyIRIS_EYES open + EMOTION:NEUTRAL, mic wm8960 PyAudio open, rpicam-still test capture, gesture sensor I2C 0x73 smbus probe (WARN or FAIL per GESTURE_SENSOR_REQUIRED). L1: GandalfAI TCP check + WoL if unreachable (polls 5s/120s), Kokoro/Whisper/Piper/OWW TCP connect with retry, Ollama /api/tags model list. L2: MOUTH:0-8 cycle (400ms dwell), EMOTION sweep, EYES:SLEEP/WAKE, EYE index cycle, MOUTH_INTENSITY ramp — all via UDP 10500. L3: intent router "what time is it" → assert ROUTE_UTILITY, Kokoro TTS round-trip, Ollama LLM smoke (model=iris, prompt="hello"), intent log writable check. L4: iris_config.json JSON parse + unknown-key audit vs _OVERRIDABLE, assistant.py RAM vs SD md5, iris_config.json owner pi:pi check. L5 verdict: AUTHORIZED if 0 FAILs, else TTS alert + LED red flash 3×. Log path: /home/pi/logs/iris_post.log. Standalone SSH: `python3 /home/pi/iris_post.py` exits 0/1 by verdict.

- **`pi4/core/config.py`** — `GESTURE_SENSOR_REQUIRED = False` added to Hardware section. Not in _OVERRIDABLE (deploy action, not web UI tunable). Flip to True after PAJ7620U2 I2C swap is confirmed on live hardware.

- **`pi4/assistant.py`** — `run_post(leds=leds, teensy=teensy, pa=pa)` called after OWW starts, before main `while True:` loop. On FAIL verdict: prints blocked message + `sys.exit(1)`. Import wrapped in try/except so a missing iris_post.py does not crash startup.

- **`pi4/iris_web.py`** — `/api/post` GET/POST route. POST: starts `run_post()` in daemon thread (single concurrent run enforced by `_post_running` Event), returns `{"ok":true,"started":true}` immediately. GET: returns `{"running":bool,"result":<last result dict>}`. Module-level `_post_last_result` holds last completed result.

- **`pi4/iris_web.html`** — POST diagnostic card added to System tab (before Config Persistence card). "Run POST Diagnostic" button + status indicator. On trigger: polls `/api/post` GET every 2s. On completion: renders per-check result table (Layer / Check / Result / Detail) with color-coded PASS/WARN/FAIL. `runPost()`, `_pollPost()`, `_renderPostResult()` JS functions added.

---

## S67 — iris_bench.jsonl SD Persistence (2026-05-27)

**Status:** DEPLOYED+VERIFIED

**Goal:** Persist bench log across reboots by appending RAM records to SD layer on each 15-min cron cycle.

**Changes:**

- **`pi4/scripts/iris_log_export.sh`** — Extended with byte-offset append block. On each cron run (as root), new records from RAM `/home/pi/logs/iris_bench.jsonl` are appended to SD `/media/root-ro/home/pi/logs/iris_bench.jsonl` using `/run/iris_bench_last_pos` stamp. Stamp resets on boot — each boot cycle appends its own records.
- **`pi4/core/config.py`** — `BENCH_LOG` (RAM write path) and `SD_BENCH_LOG` (SD accumulation path) constants added.
- **`pi4/assistant.py`** — `_bench_write` uses `BENCH_LOG` constant instead of hardcoded string.
- **`install_journald.sh`** — Run on Pi4. journald retention extended to 500MB / 1 year (S50 pending step completed).

All Pi4 files DEPLOYED+VERIFIED. Commit pushed.

---

## S68 — Docs Audit + Servo Subsystem Documentation (2026-05-27)

**Status:** Complete (docs-only)

**Goal:** Audit and correct all documentation to reflect confirmed hardware state after S59-S67 changes. Document Teensy 4.0 servo subsystem fully in preparation for PAJ7620U2 firmware work.

**Changes:**

- **`IRIS_ARCH.md`** — System Roles and Architecture tables enhanced for Teensy 4.0. T4.0 pin section adds firmware file, ServoEasing, autonomy behavior, and power-toggle notes. Serial Protocol section extended with Teensy 4.0 one-way serial. Repo Structure and Env Quick Ref updated. PAJ7620U2 pending hardware section added. Stale `/dev/ttyACM0` reference corrected.
- **`ROADMAP.md`** — HW-002/RD-009/RD-010/RD-011 (ESP32 tombstoned items) removed. HW-001 closed. HW-003 (PAJ7620U2 swap) added.
- **`CHANGELOG.md`** — Servo controller evolution history added (Pico → Pico W → ESP32 → Teensy 4.0).
- Memory files corrected: flash workflow memories updated to Teensy 4.1; `project_servo_controller_hardware.md` created.
- SNAPSHOT/HANDOFF updated to reflect confirmed state.

Commit cf0b17b pushed.

---

## S69 — PAJ7620U2 Driver + DS3218MG Constants (2026-05-27)

**Status:** FLASHED — Teensy 4.0 firmware flashed. Hardware install pending (PAJ7620U2 not yet wired to I2C bus). Touch3 is pin 15 (T3 pad on Teensy PCB) — no external component.

**Goal:** Replace dead APDS-9960 gesture sensor with PAJ7620U2 bare I2C driver. Tune servo constants for DS3218MG. Add touch3 LISTEN trigger to replace removed proximity channel. Add mount-orientation abstraction.

**Firmware changes (servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino) — commits 35ffaf3 → bf304a8:**

APDS-9960 removed entirely: SparkFun include, apdsOk flag, raw 0x39 ID probe, PROX_LISTEN_THRESHOLD/PROX_HOLD_MS, prox LISTEN logic.

PAJ7620U2 bare I2C driver added:
- `paj_write(reg, val)` / `paj_read(reg)` I2C helpers
- `paj7620Init()` — wakeup sequence (any I2C contact, 700ms settle, ACK confirm), bank 0 (29 reg writes via 0xEF=0x00), bank 1 (20 writes via 0xEF=0x01), back to bank 0, unmask all gestures (0x41=0xFF), gesture mode (0x42=0x01); returns bool
- `pollGesture()` — reads register 0x43 (IntFlag_1) each loop; non-zero = gesture; dispatches via GEST_* macros

Register 0x43 correct bit layout (PAJ7620U2 datasheet v1.5 p.24 — confirmed before wiring):
- Bit 0 (0x01) = Left, Bit 1 (0x02) = Right, Bit 2 (0x04) = Down, Bit 3 (0x08) = Up
- Bit 4 (0x10) = Forward, Bit 5 (0x20) = Backward, Bit 6 (0x40) = CW, Bit 7 (0x80) = CCW

Mount orientation abstraction (`#define GESTURE_MOUNT_DEGREES`):
- Values 0/90/180/270 each compile to the correct GEST_UP/DOWN/LEFT/RIGHT macro mapping
- `#error` fires at compile time for any other value
- **Current setting: 270** (sensor mounted 90° CCW relative to viewer)
- 270° mapping: phys UP=0x01, phys DOWN=0x02, phys LEFT=0x04, phys RIGHT=0x08

Command dispatch: phys UP→`VOL+`, phys DOWN→`VOL-`, phys LEFT or RIGHT→`STOP`; Forward/Backward/CW/CCW ignored

Touch3 LISTEN: `pollTouch3()` on pin 15 (T3 cap pad), `TOUCH3_THRESH=1500`, `TOUCH3_HOLD_MS=1000`. Short tap (release <1s) → `STOP`; hold ≥1s → `LISTEN`. Replaces proximity-LISTEN from removed APDS-9960.

SERIAL_DIAG hardening: CODEX DIAGNOSTIC INSERT wrappers on all diagnostic blocks; pajOk printed in periodic telemetry (`pan=N pajOk=1`); raw gest byte printed on gesture detect; touch3 raw value printed each second for TOUCH3_THRESH tuning.

DS3218MG constants: PAN_SPEED 0.02 (was 0.04), PAN_DEAD_ZONE 5.0 (was 2.0), FACE_RETURN_MS 6000 (was 8000).

Serial contract unchanged: VOL+/VOL-/STOP/LISTEN (no Pi4 side changes required).

**Other changes:**
- **`servo_teensy40/teensy40_base_mount/platformio.ini`** — Removed stale SparkFun APDS9960 lib_deps comment. Platform URL auto-updated by PlatformIO.
- **`servo_teensy40/README.md`** — Hardware list updated (PAJ7620U2 0x73, DS3218MG, touch3 pin 15, /dev/ttyIRIS_SERVO). Stale "new firmware to be written" note removed.
- **`docs/sysmap.json`** (local-only, gitignored) — Full S69 patch set: teensy40.role, gpio pin table (pin 15 touch3 added, pins 18/19 updated), PAJ7620U2 sensor block with register 0x43 bit table + rotation table for all 4 mount angles, GESTURE_MOUNT_DEGREES reference, TOUCH3_PIN/TOUCH3_THRESH/TOUCH3_HOLD_MS constants, servo field, _meta updated.
- **`IRIS_ARCH.md`** — Architecture table Teensy 4.0 row updated (PAJ7620U2, touch3). Teensy 4.0 pin section rewritten: pin 15 added, I2C devices updated, serial command table adds LISTEN, PAJ7620U2 quick-reference section added with reg 0x43 bit table + rotation table for all 4 mount angles + command mapping. "Pending Hardware — PAJ7620U2" section removed. Repo Structure .ino comment updated. Serial Protocol Teensy 4.0 block updated (APDS-9960→PAJ7620U2, LISTEN added).
- **`CLAUDE.md`** — CHANGELOG same-session enforcement rule added to Documentation rules and Hard Rules sections.
- **`docs/handoffs/HANDOFF_PAJ7620U2_DS3218MG.md`** — Session handoff doc committed to repo.
- **`docs/sysmap_patch_2026-05-27.md`** — Patch spec committed for reference.

**Build fix — `touchRead` not implemented in PlatformIO Teensy 4.x framework:**
PlatformIO `framework-arduinoteensy` declares `touchRead()` in `cores/teensy4/core_pins.h` but provides no implementation for Teensy 4.x (implementation only exists in `cores/teensy3/touch.c`). Resulted in linker error: `undefined reference to 'touchRead'`. Fix: added `capTouch(pin)` in the .ino — ADC discharge-float-sample approach (drive LOW, float INPUT_DISABLE, sample ADC). Returns 0–1023 (10-bit). TOUCH3_THRESH updated from 1500 to 100 to match ADC scale. SERIAL_DIAG prints raw capTouch value for threshold tuning.

Commits: 35ffaf3 (initial driver), f31e6ce (SERIAL_DIAG hardening), cb26e7e (reg 0x43 bit map + rotation fix), bf304a8 (GESTURE_MOUNT_DEGREES abstraction), b0f6bcc (doc update: IRIS_ARCH.md, platformio.ini, SNAPSHOT, HANDOFF, CHANGELOG), + touchRead build fix commit.

---

## S70 — ServoEasing Async Smoothing + PAN_MIN/MAX + PAN? Query (2026-05-28)

**Status:** REPO-ONLY — build clean, pending user PlatformIO upload (env:teensy40).

**Goal:** Replace synchronous panServo.write() with ServoEasing interrupt-driven async API, add hard rotation limits, add PAN? angle query command.

**File changed:** `servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`

**Changes:**

1. **Constants block** — `PAN_MIN 45.0` and `PAN_MAX 135.0` added after `FACE_RETURN_MS`. All `constrain()` calls updated from hardcoded `0.0/180.0` to `PAN_MIN/PAN_MAX`.

2. **setup()** — Easing type set once: `panServo.setEasingType(EASE_CUBIC_IN_OUT)`. Interrupt mode enabled: `enableServoEasingInterrupt()`. Initial `write()` cast removed (float arg now passed directly). `setUpdateInterval(20)` omitted — not present in ServoEasing 3.6.0 (library resolved to 3.6.0 from `^3.3.3`); 20ms is the library default (`REFRESH_INTERVAL = 20000µs`).

3. **loop() — tracking branch** — `panServo.setEasingType(EASE_CUBIC_OUT)` removed. `panServo.write((int)desiredPan)` replaced with `if (!panServo.isMoving()) { panServo.startEaseToD(desiredPan, 100); }`.

4. **loop() — return-to-center branch** — `panServo.setEasingType(EASE_SINE_OUT)` removed. `panServo.write((int)desiredPan)` replaced with `if (!panServo.isMoving()) { panServo.startEaseToD(desiredPan, 100); }`.

5. **PAN command handler (SERIAL_DIAG)** — `toInt()` → `toFloat()`, limits updated to `PAN_MIN/PAN_MAX`, `write((int)desiredPan)` → `startEaseToD(desiredPan, 100)` (no isMoving guard — direct command always takes effect).

6. **PAN? query command (SERIAL_DIAG)** — new branch: `cmd == "PAN?"` → `Serial.print("PAN="); Serial.println(panServo.getCurrentAngle());`. Returns live servo position as float.

**Build:** Clean — `pio run -e teensy40` SUCCESS. FLASH/RAM well within Teensy 4.0 limits.

---

## S71 — Servo Docs Update: DS3218MG Confirmed Installed (2026-05-28)

**Status:** Complete (docs-only)

**Goal:** Update documentation to reflect DS3218MG servo confirmed physically installed and operational. Correct stale ServoEasing notes in wiring doc (still referenced old synchronous API). Fix `touchRead` → `capTouch` in IRIS_ARCH.md pin table (S69 build fix never propagated to docs).

**Changes:**

- **`docs/servo_teensy40_wiring.md`** — Servo Control Notes section rewritten: `EASE_CUBIC_OUT tracking / EASE_SINE_OUT return` replaced with S70 API (EASE_CUBIC_IN_OUT, `startEaseToD(target, 100)`, `isMoving()` guard, FACE_RETURN_MS 6000ms). PAN_MIN 45° / PAN_MAX 135° clamp range documented. Last-updated timestamp updated.
- **`IRIS_ARCH.md`** — Pin 15 table row: `touchRead(15)` corrected to `capTouch(15)` with note that `touchRead` is not implemented in Teensy 4.x PlatformIO framework.
- **`servo_teensy40/README.md`** — Status line updated: "Firmware current as of S69" → DS3218MG confirmed installed and operational, firmware current as of S70.

---

## S72 — PAJ7620U2 Full Gesture Expansion + DS3218MG MS24 + Web UI Update (2026-05-28)

**Status:** Pi4 files DEPLOYED+VERIFIED. Firmware REPO-ONLY (pending user flash).

**Goal:** Wire all 8 PAJ7620U2 gesture types to firmware + bridge + web UI. Add MUTE action. Correct servo model to DS3218MG MS24. Fix gesture event log inversion. Update all hardware mapping docs.

**Changes:**

- **`servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`** — `pollGesture()` emit block extended: FORWARD (0x10), BACKWARD (0x20), CW (0x40), CCW (0x80) now emit `Serial.println()` strings (previously silently ignored). File header comment updated to list all 8 commands. REPO-ONLY pending user flash.

- **`pi4/hardware/base_mount_bridge.py`** — `_DEFAULT_GESTURE_MAP` extended: FORWARD→LISTEN, BACKWARD→SLEEP, CW→VOL+, CCW→VOL-. `_mute_restore` module-level state added. `MUTE` action added to `_dispatch()`: toggles between vol=0 and saved restore level using `get_volume`/`set_volume` from `hardware.audio_io`.

- **`pi4/iris_web.py`** — `_BASE_GEST_RE` updated to match FORWARD/BACKWARD/CW/CCW in legacy `[BASE]` log lines. `_DEFAULT_GESTURE_MAP` extended (4 new keys). `_VALID_GESTURE_ACTIONS` extended: SLEEP, WAKE, MUTE added. `api_gesture_config()` GET: now merges stored GESTURE_MAP with defaults so new gesture keys always appear with sensible defaults even if `iris_config.json` was written before S72.

- **`pi4/iris_web.html`** — Gestures card: APDS-9960/ttyACM1 stale refs → PAJ7620U2/ttyIRIS_SERVO; LISTEN label corrected (was "proximity hold" → "touch3 hold, pin 15"); proximity threshold slider removed (APDS-9960 specific); FORWARD/BACKWARD/CW/CCW select rows added with divider. `_GESTURE_KEYS` extended (8 total). `_GESTURE_ACTIONS` extended: MUTE added; SLEEP/WAKE labels shortened. `loadGestureConfig`: proximity threshold DOM refs removed. `saveGestureConfig`: GESTURE_PROXIMITY_THRESHOLD removed from POST body. `fetchGestureLog`: empty-state hint updated (PAJ7620U2); `box.scrollTop=0` replaced with `window.requestAnimationFrame(() => box.scrollTop=0)` to guarantee paint-after-reset for reliable newest-at-top behavior.

- **`IRIS_ARCH.md`** — Serial command table: 4 new rows (FORWARD/BACKWARD/CW/CCW with default actions). "command mapping" section: FORWARD/BACKWARD/CW/CCW described. Serial protocol block: all 8 commands listed. Pin 2 row: servo model updated to Miuzei DS3218MG MS24.

- **`servo_teensy40/README.md`** — Servo model updated to DS3218MG MS24; shared I2C bus with Person Sensor noted.

- **`docs/servo_teensy40_wiring.md`** — Servo model row updated to DS3218MG MS24.

- **`docs/sysmap.json`** (local-only, gitignored) — `serial_commands` updated (8 commands). `servo` field: MS24 added. `gpio` pin 2/15 rows corrected (MS24, capTouch note). `command_map`: all 8 gestures documented with default actions and note on configurability. `tunable_constants`: PAN_MIN/PAN_MAX added; EASING_TRACK/EASING_RETURN replaced with EASING_TYPE/EASING_MOVE_MS (S70 async API).

**Deploy fix — `BaseMountBridge.__init__` signature mismatch:**
Live `assistant.py` calls `BaseMountBridge(_bm_cfg, leds)` (two positional args). S72 `base_mount_bridge.py` `__init__` only accepted `(self, config)`. Fixed by adding `leds=None` parameter. Pi4 RAM and SD updated; md5 verified. Services restarted: assistant POST 21/22 PASS AUTHORIZED, iris-web active.

**Pi4 deploy — md5 verified (RAM = SD):**
- `/home/pi/hardware/base_mount_bridge.py` — a69b1a7c (leds=None fix included)
- `/home/pi/iris_web.py` — 575eabecc5
- `/home/pi/iris_web.html` — d95f9c6461

---

## TS40-S2 — PAJ7620U2 Gesture Debounce + Cooldown State Machine (2026-05-29)

**Status:** REPO-ONLY — firmware pending user PlatformIO flash (env:teensy40).

**Goal:** Eliminate the 3-5× repeat-fire problem where one hand swipe emits multiple gesture commands. Each physical gesture should fire exactly once.

**Changes:**

- **`servo_teensy40/teensy40_base_mount/paj7620.h`** — NEW FILE. Extracts PAJ7620U2 public interface from `.ino` (TS40-S1 refactor + TS40-S2 debounce in one session). Exports: `PAJ7620_ADDR`, `GESTURE_MOUNT_DEGREES`, `GESTURE_DEBOUNCE_MS` (400), `GESTURE_COOLDOWN_MS` (200), `SERIAL_DIAG`, `extern bool pajOk`, `paj7620Init()`, `pollGesture()`.

- **`servo_teensy40/teensy40_base_mount/paj7620.cpp`** — NEW FILE. All PAJ7620U2 driver code: `paj_write`, `paj_read`, `paj7620Init`, `pollGesture` with debounce state machine. Debounce logic in `pollGesture()`: (1) first-poll discard — reads and drops reg 0x43 on first call after init (PAJ7620U2 stale-data hardware behavior); (2) global cooldown — any gesture within `GESTURE_COOLDOWN_MS` of the last fired gesture is suppressed; (3) per-gesture debounce — same gesture within `GESTURE_DEBOUNCE_MS` is suppressed. Suppressed gestures emit `DIAG: PAJ7620 gest=0xNN SUPPRESSED debounce|cooldown` when `SERIAL_DIAG=1`. Emit block and command strings unchanged.

- **`servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`** — Removed: `SERIAL_DIAG` define, `PAJ7620_ADDR` + `GESTURE_MOUNT_DEGREES` + `GEST_*` rotation table, `bool pajOk`, `paj_write`, `paj_read`, `paj7620Init`, `pollGesture`. Added: `#include "paj7620.h"`. Person Sensor, servo, and touch3 code untouched.

- **`docs/sysmap.json`** — `tunable_constants`: `GESTURE_DEBOUNCE_MS` (400) and `GESTURE_COOLDOWN_MS` (200) added with notes.

**Rollback:** `git checkout -- servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino && rm servo_teensy40/teensy40_base_mount/paj7620.h servo_teensy40/teensy40_base_mount/paj7620.cpp`

---

## TS40-S1 — Modular Subsystem Extraction + Phantom Touch3 Removal (2026-05-29)

**Status:** REPO-ONLY — firmware pending user PlatformIO flash (env:teensy40).

**Note on numbering:** Follows TS40-S2 chronologically. TS40-S2 extracted the PAJ7620U2 gesture driver (`paj7620.h/.cpp`); those files are NOT duplicated or modified here. This session completes the modular split of the remaining inline subsystems and removes dead touch-pad code.

**Goal:** Finish the modular refactor of `teensy40_base_mount.ino` and delete the phantom capacitive touch3 code introduced in S69 for hardware that was never wired.

**Phantom hardware removed (S69 hallucination):** S69 added a capacitive touch pad on pin 15 (T3) with `capTouch()` ADC-discharge sampling, `pollTouch3()`, and `TOUCH3_PIN/THRESH/HOLD_MS` constants. The touch pad was never physically installed. All of it is removed: defines, `capTouch()`, `pollTouch3()` + its SERIAL_DIAG block, the `loop()` call, the build-fix comment about `touchRead()` missing from the PlatformIO Teensy 4.x framework, and the header pin/trigger comments. `LISTEN` is preserved as a valid command/action — it has other invocation paths (FORWARD gesture default action, web UI).

**Modules extracted:**

- **`servo_teensy40/teensy40_base_mount/person_sensor.h` / `.cpp`** — NEW. Person Sensor I2C driver: `setupPersonSensor()` (LED-disable register write) and `pollPersonSensor()` returning `PersonResult {ok, faceVisible, faceCenterX, confidence, isFacing}`. Codex-hardened packet decode (header skip, payload/checksum decode, fixed four-face consume, invalid-count rejection, confidence+facing gate) preserved exactly. `ok` field distinguishes a short-read cycle (caller holds pan, matching the original early-return) from a valid no-face read (caller runs idle return). SERIAL_DIAG telemetry preserved.

- **`servo_teensy40/teensy40_base_mount/pan_servo.h` / `.cpp`** — NEW. ServoEasing wrapper: `setupPanServo()`, `updatePanFromFace(faceCenterX)`, `updatePanIdle(faceLostMs)`, `handleSerialPanCmd(cmd)` (PAN/PAN?, SERIAL_DIAG-gated). All constants (PAN_SPEED, PAN_DEAD_ZONE, FACE_HOLD_MS, FACE_RETURN_MS, PAN_MIN, PAN_MAX) and `desiredPan` live here. `ServoEasing.hpp` is now included in this one translation unit only.

- **`servo_teensy40/teensy40_base_mount/diag.h`** — NEW. `DIAG_PRINT/DIAG_PRINTLN/DIAG_PRINTF` macros gated on `SERIAL_DIAG` (defensive `#ifndef`; canonical define stays in paj7620.h per TS40-S2). paj7620.cpp's existing SERIAL_DIAG usage was intentionally NOT refactored to use diag.h — deferred to a future unify pass.

- **`servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`** — Reduced to orchestration only: `setup()` calls each module's setup + `paj7620Init()`, `loop()` parses REBOOT (delegates PAN/PAN? to `handleSerialPanCmd`), calls `pollGesture()`, then dispatches `pollPersonSensor()` results to `updatePanFromFace`/`updatePanIdle`. Boot I2C presence probe and one-time `I2C_SCAN_DIAG` block retained. **345 lines → 94 lines** (header comment 25 lines; orchestration code ~69). No constant changed; no logic changed apart from touch3 removal. Behavior preserved bit-for-bit (one diagnostic-only nuance: the `pan=` field in the rate-limited PS telemetry now reflects the prior cycle's pan target since the pan update moved to the caller — no functional servo change).

**Docs:**
- **`docs/sysmap.json`** — removed `TOUCH3_PIN/THRESH/THRESH_NOTE/HOLD_MS` from `tunable_constants`, pin 15 from `gpio`, touch3 from `behavior`.
- **`IRIS_ARCH.md`** — removed pin 15 row, Touch3 section, and touch3 references from System Roles / Architecture / Repo Structure / Serial Protocol. LISTEN retained (gesture action / web UI paths).
- **`servo_teensy40/README.md`** — removed touch3 hardware line; firmware description updated to note modular layout.
- **`.gitignore`** — removed `docs/sysmap.json` from the ignore list. It had been misfiled under "Generated runtime state," but nothing generates it — it is the hand-maintained primary lookup map (PRIMER.md: read before IRIS_ARCH.md). Being ignored excluded it from version history, GitHub backup, and fresh clones. Now tracked. Contains no credentials (IPs only, already present in tracked IRIS_ARCH.md).

**Rollback:** `git checkout -- servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino docs/sysmap.json IRIS_ARCH.md servo_teensy40/README.md && rm servo_teensy40/teensy40_base_mount/person_sensor.h servo_teensy40/teensy40_base_mount/person_sensor.cpp servo_teensy40/teensy40_base_mount/pan_servo.h servo_teensy40/teensy40_base_mount/pan_servo.cpp servo_teensy40/teensy40_base_mount/diag.h`

---

## HW-004 — PAJ7620U2 Hardware Failure Diagnosis (2026-05-29)

**Status:** BLOCKED — replacement GY-PAJ7620 on order.

**Finding:** PAJ7620U2 gesture sensor confirmed dead. Does not ACK at 0x73 or any valid address (0x13, 0x1B, 0x23, 0x2B, 0x5B, 0x63, 0x6B, 0x73). I2C bus confirmed healthy (Person Sensor at 0x62 responds correctly). VIN=3.3V confirmed with multimeter. SDA/SCL continuity to Teensy pins 18/19 confirmed. Reflow of breakout board header pins attempted — no change. Sensor IC is dead; replacement ordered.

**Diagnostic steps taken:**
- Extended `delay(8000)` boot hold in `setup()` (replacing non-functional `while (!Serial && millis() < 3000)` — Teensy 4.x USB CDC makes `Serial` always truthy, so the original loop was a no-op). Allows serial monitor to connect before boot DIAG lines print.
- Added + used + reverted `I2C_SCAN_DIAG` (full 1–127 address scan 10s after boot). Scan found 0x39, 0x4F, 0x62, 0x79 — all consistent with Person Sensor module internal endpoints + Person Sensor at 0x62. No PAJ7620U2 address present.
- Read PAJ7620U2 datasheet v1.5 sections 5.1.1 (I2C address list) and 6.1.2 (power-on sequence: VBUS before VDD). GY-PAJ7620 5-pin breakout confirmed to tie VBUS internally to VIN — not a wiring issue.
- touch3 idle ADC readings (127–130) confirmed above `TOUCH3_THRESH=100`, causing continuous false LISTEN triggers. Moot — touch3 code fully removed in TS40-S1.

**Changes:**
- **`servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`** — `delay(8000)` boot hold replacing `while (!Serial && millis() < 3000)` no-op. `I2C_SCAN_DIAG` restored to 0 after use.
- **`SNAPSHOT_LATEST.md`** — Teensy 4.0 row updated: HW-004 BLOCKED, sensor dead, replacement on order. Active Issues updated. WHAT'S NEXT gated behind sensor arrival.
- **`HANDOFF_CURRENT.md`** — Next Work pointer updated: BLOCKED on HW-004, sensor replacement steps documented.
- **`docs/iris_issue_log.md`** — HW-004 entry added.

**Next step:** When replacement GY-PAJ7620 arrives, seat identically, confirm `ACK=YES` + `init=OK` at boot, then flash TS40-S1 firmware and verify debounce.

---

## CODEX SECONDARY-CODER SESSION — 2026-05-29

The following CDX-N entries were produced by ChatGPT Codex 5.5 (extra-high
effort) as a secondary coder during a Claude usage gap. All work is
repo-only. Each CDX-N entry was reviewed by Claude Code on session resume;
the review outcome is noted at the end of each entry.

Codex scope was bounded to: doc audits, consistency passes, test stubs.
No firmware. No live system edits. No protected files. No multi-file
contracts.

---

## CDX-1 — ROADMAP + Issue Log Audit Pass (2026-05-29)

**Status:** REPO-ONLY — documentation audit committed locally.

**Scope:** Audited `ROADMAP.md` and `docs/iris_issue_log.md` against `SNAPSHOT_LATEST.md`, `HANDOFF_CURRENT.md`, `CLAUDE.md`, and S60 onward `CHANGELOG.md` entries.

**Changes:**
- **`ROADMAP.md`** — Removed resolved or superseded active items: RD-002 (AMUSED emotion full implementation, completed in S47), HW-001 (Teensy 4.1 LED mitigation accepted in S67), and HW-003 (PAJ7620U2 integration superseded by HW-004 dead-sensor tracking). Updated stale active status labels for RD-001, RD-006, and RD-007 without renumbering any identifiers.
- **`docs/iris_issue_log.md`** — Updated stale Status lines only: RD-002 emotion issue now `Fixed`; single-word STT/pre-STT intercept marked `Deferred` to match current active scope; local Piper TTS routing normalized to `Deferred`.

**Review note:** HW-004 remains untouched and BLOCKED on hardware replacement. RD-003 remains Open.

---

## S60 — Gesture Config Tab Deployment Backfill (2026-05-23)

**Status:** DEPLOYED+VERIFIED. Commits `c853709` (implementation + deploy state) and `eaba946` (snapshot status correction).

**Source:** Recovered from `SNAPSHOT_LATEST.md` S60 prior-session block and commit messages.

**Changes:**
- **`pi4/hardware/base_mount_bridge.py`** — Config-driven gesture dispatch reads `GESTURE_MAP` from `iris_config.json` on each event; LISTEN action creates `/tmp/iris_manual_listen`; SKIP no-op and per-action error handling added.
- **`pi4/iris_web.py`** — `/api/gesture_config` GET/POST endpoint added; validates gesture actions against whitelist, clamps proximity threshold, writes config via `write_cfg()`.
- **`pi4/iris_web.html`** — Gestures tab added with four gesture-action dropdowns and proximity threshold slider.
- **`SNAPSHOT_LATEST.md`** — Updated to mark S60 gesture config tab DEPLOYED+VERIFIED.

---

## S62b — Sleep Animation Tuning Backfill (2026-05-23)

**Status:** REPO-ONLY — sparse record.

**Commit:** `d6c33c6` — `S62b: tune sleep animation — slower pace, shorter trails, no warp streaks`

**Changes:**
- **`src/sleep_renderer.h`** — Tuned S62 sleep animation pacing and visual trail behavior.

**Notes:** Details not recovered from `SNAPSHOT_LATEST.md` prior-session blocks; see commit message and diff for specifics.

---

## S68b — Wiring Doc + Gesture Direction Backfill (2026-05-27)

**Status:** REPO-ONLY — sparse record.

**Commit:** `22437e9` — `S68b: Commit wiring doc + fix gesture directions + wiring doc reference`

**Changes:**
- **`IRIS_ARCH.md`** — Gesture direction and wiring-reference corrections.
- **`docs/servo_teensy40_wiring.md`** — Servo Teensy 4.0 wiring document committed.

**Notes:** Details not recovered from `SNAPSHOT_LATEST.md` prior-session blocks; see commit message and diff for specifics.

---

## Unlabeled — docs/sysmap.json Tracking Backfill (2026-05-29)

**Status:** REPO-ONLY — sparse record.

**Commit:** `f740844` — `Track docs/sysmap.json (remove from .gitignore)`

**Changes:**
- **`.gitignore`** — Removed `docs/sysmap.json` from generated/runtime ignore group.
- **`docs/sysmap.json`** — Added to version history as the hand-maintained primary lookup map.
- **`HANDOFF_CURRENT.md`** — Deploy-state note updated to say `docs/sysmap.json` is now tracked.
- **`CHANGELOG.md`** — Prior TS40-S1 docs note updated to include `.gitignore`.

**Notes:** Commit message is the only available source for this unlabeled commit.

---

## CDX-2 — CHANGELOG Backfill Audit (2026-05-29)

**Status:** REPO-ONLY — documentation audit committed locally.

**Scope:** Compared `git log --oneline -80` against `CHANGELOG.md` labels and commit coverage from S60 onward.

**Backfilled:**
- S60 — commits `c853709`, `eaba946`.
- S62b — commit `d6c33c6`.
- S68b — commit `22437e9`.
- Unlabeled sysmap tracking commit — `f740844`.

**Review note:** Existing entries were not modified. Sparse records are intentionally marked where `SNAPSHOT_LATEST.md` did not describe the session.

---

## CDX-3 — sysmap.json + IRIS_ARCH.md Consistency (2026-05-29)

**Status:** REPO-ONLY — documentation/map consistency pass committed locally.

**Scope:** Cross-checked `docs/sysmap.json` against `IRIS_ARCH.md`, with spot checks against `SNAPSHOT_LATEST.md`, `pi4/core/config.py`, `src/sleep_renderer.h`, and current Teensy 4.0 firmware headers.

**Changes:**
- **`docs/sysmap.json`** — Updated metadata to reflect tracked status (`f740844`), added missing Teensy 4.0 serial commands (`FORWARD`, `BACKWARD`, `CW`, `CCW`) to `commands_from_teensy`, corrected `SR_FRAME_MS` to 155, and removed stale touch1/touch2 behavior entries.
- **`IRIS_ARCH.md`** — Updated Teensy 4.0 serial direction wording to remove stale touch-event reference and list all 8 command strings; corrected repo-structure `SR_FRAME_MS` note to 155; refreshed the `core/config.py` constants block with current ports, Kokoro, serial symlinks, gesture sensor gate, and tiered `NUM_PREDICT_*` constants.

**Mismatch report:**
- MATCH: Pi4/GandalfAI/SuperMaster IPs; `/dev/ttyIRIS_EYES` and `/dev/ttyIRIS_SERVO` symlinks; PAJ7620U2 address `0x73`; Teensy 4.0 pins 2/18/19; PAJ7620U2 register `0x43` bit layout; mount rotation table; gesture command map; PAN_MIN/PAN_MAX; gesture debounce/cooldown.
- MINOR_DRIFT: sysmap stores some values as structured JSON while `IRIS_ARCH.md` presents prose/tables.
- MISSING_IN_SYSMAP fixed: extended Teensy 4.0 `commands_from_teensy` list.
- MISSING_IN_ARCH fixed: current Kokoro/tiered-response/serial-port config constants.
- VALUE_MISMATCH fixed from source/snapshot: `SR_FRAME_MS` 150 -> 155.
- STALE_IN_SYSMAP fixed: tracked/gitignore metadata and touch1/touch2 behavior entries.

**Review note:** No unresolved VALUE_MISMATCH items were auto-resolved beyond values verified in source files and `SNAPSHOT_LATEST.md`.

---

## CDX-4 — README.md Audit: Root + servo_teensy40 (2026-05-29)

**Status:** REPO-ONLY — documentation audit committed locally.

**Scope:** Audited root `README.md` and `servo_teensy40/README.md` against `SNAPSHOT_LATEST.md`, `CLAUDE.md`, and `IRIS_ARCH.md` system/pin sections.

**Changes:**
- **`README.md`** — Added Teensy 4.0 base mount to project/hardware descriptions; added POST diagnostic, persistent USB identity, and base-mount gesture feature rows; updated GandalfAI TTS wording to Kokoro/Piper; refreshed sleep animation text; added Teensy 4.0 gesture serial block; fixed Web UI "all 9 styles" and "mouth matrix" stale text.
- **`servo_teensy40/README.md`** — Updated firmware status to TS40-S1/TS40-S2, added HW-004 PAJ7620U2 dead/replacement-on-order note, switched wiring reference to `docs/servo_teensy40_wiring.md`, and expanded modular file names.

**Review note:** Root README changelog section was intentionally left unchanged because the separate `CHANGELOG.md` is canonical.

---

## CDX-5 — pytest Stubs for Pi4 Python Modules (2026-05-29)

**Status:** REPO-ONLY — test scaffold committed locally.

**Scope:** Added pytest stubs for Pi4 Python modules that must run on SuperMaster without live IRIS hardware. Tests cover `pi4/hardware/base_mount_bridge.py`, `pi4/core/intent_router.py`, `pi4/services/tts.py`, and `pi4/iris_post.py`.

**Changes:**
- **`tests/conftest.py`** — Added shared fixtures for fake config, mocked audio, mocked ALSA subprocess calls, mocked UDP, mocked serial, and an autouse network blocker.
- **`tests/test_base_mount_bridge.py`** — Added gesture dispatch, mute toggle, LISTEN/UDP path, health-line, and invalid-gesture tests.
- **`tests/test_intent_router.py`** — Converted the existing standalone Loop 1 script into pytest functions covering REFLEX, COMMAND, UTILITY, AMBIGUOUS, LLM fallthrough, and fail-open behavior.
- **`tests/test_tts_spoken_numbers.py`** — Added numeric normalization coverage for units, teens, tens, hundreds, thousands, millions, negative numbers, and zero.
- **`tests/test_iris_post.py`** — Added mocked POST coverage for LED layer sequence, PASS outcome, FAIL outcome, and gesture sensor required/not-required severity.
- **`pytest.ini`** — Scoped pytest discovery to CDX-5 stubs so the legacy standalone integration smoke script is not executed at collection time.
- **`requirements-dev.txt`** — Added pinned pytest dependencies.
- **`tests/README.md`** and **`tests/__init__.py`** — Added test-running notes and package marker.

**Verification:** Installed pinned dev requirements with `python -m pip install -r requirements-dev.txt`, then ran `python -m pytest tests/ -v`. Result: 66 passed, 1 failed. The failing test is `tests/test_tts_spoken_numbers.py::test_negative`, which shows `spoken_numbers("-42")` currently returns `-forty two` instead of `negative forty two`.

**Review note:** No `pi4/*` source files were modified. The negative-number failure is left for Claude Code review because CDX-5 was test-only by design.

---

## Claude Review of Codex Session — 2026-05-29

**Status:** REPO-ONLY — review pass + one correction committed locally.

**Scope:** Reviewed CDX-1 through CDX-5. For each commit, verified the deliverable's Files Changed list against the actual `git diff`, spot-checked diff content for correctness, confirmed no protected files were touched, and resolved each Open Question.

**Verdict per task:**
- **CDX-1 (ROADMAP + issue log)** — ACCEPTED. Status flips accurate; completed items (RD-002, HW-001) correctly removed from the forward roadmap; HW-003 correctly superseded by HW-004 (tracked in SNAPSHOT). No history deleted.
- **CDX-2 (CHANGELOG backfill)** — ACCEPTED. All cited commits (`c853709`, `eaba946`, `d6c33c6`, `22437e9`, `f740844`) verified present with matching messages. Append-only respected; sparse records honestly marked.
- **CDX-3 (sysmap.json + IRIS_ARCH.md)** — ACCEPTED. `SR_FRAME_MS` 155, `commands_from_teensy` 8-command list, and refreshed `core/config.py` constants all match source exactly. Open Question resolved: tracking `docs/sysmap.json` IS intended (confirmed by commit `f740844`).
- **CDX-4 (README audit)** — ACCEPTED. Hardware/feature/TTS/sleep/serial corrections accurate; "all 7 compiled styles" matches `config.h` (7 eyes).
- **CDX-5 (pytest stubs)** — ACCEPTED with one correction. Suite confirmed 66 passed / 1 failed as reported. CORRECTED the failing `test_negative`: it asserted `spoken_numbers("-42") == "negative forty two"`, a behavior the source does not implement. The integer matcher is `\b(\d+)\b` and intentionally does not treat a leading `-` as a sign — doing so would regress ranges (`10-20`) and hyphenated text, far more common in LLM output than standalone negatives. Aligned the test with actual, safe behavior rather than changing `pi4/services/tts.py`. Suite now 67 passed (commit `f410852`).

**Open Questions resolved:**
- CDX-3 sysmap tracking — RESOLVED (tracking intended).
- CDX-5 negative-number TTS — RESOLVED (test corrected; source intentionally unchanged).

**Carried forward (unresolved):**
- CDX-5: `tests/test_integration_smoke.py` remains a legacy standalone import-time script, excluded from pytest collection by `pytest.ini`. Convert or retire in a future task.

---

## S73 — Sleep/WebUI Bridge Fix: udev Rules Lost on Reboot (2026-05-29)

**Status:** DEPLOYED+VERIFIED

**Root cause:** `/etc/udev/rules.d/99-iris-teensy.rules` was deployed to the Pi4 RAM overlay during S63 but never persisted to SD (`/media/root-ro`). A Pi4 reboot at approximately 19:04 MDT on 2026-05-28 erased the RAM overlay, removing the udev rules. On the next boot, `/dev/ttyIRIS_EYES` symlink was never created. The assistant restarted at 20:36 with a TeensyBridge that could not open the port. All `send_command()` calls silently returned False (no log). The 21:00 cron sleep and webui sleep buttons both sent the correct UDP commands — the assistant received them and the APA102 LEDs (driven directly from Python, not serial) responded — but no serial commands reached the Teensy 4.1. Displays never entered sleep animation.

**Secondary:** `teensy_bridge.py` had no logging when the serial port could not be opened or when commands were dropped. Future port failures will now be visible in the journal.

**Changes:**

- **`/etc/udev/rules.d/99-iris-teensy.rules`** — Redeployed from `pi4/scripts/99-iris-teensy.rules` (repo copy was correct; Teensy 4.1 serial `13625440`, Teensy 4.0 serial `12763490`). udevadm reload + trigger applied. `/dev/ttyIRIS_EYES -> ttyACM1` confirmed.
- **`/media/root-ro/etc/udev/rules.d/99-iris-teensy.rules`** — NEW. Persisted to SD for reboot survival. md5 verified RAM=SD.
- **`pi4/hardware/teensy_bridge.py`** — Three fixes: (1) docstring corrected from "Teensy 4.0 serial bridge / `/dev/ttyACM0`" to "Teensy 4.1 / `/dev/ttyIRIS_EYES`"; (2) `_open()` now logs `[EYES] Cannot open {port}: {e} -- will retry` on failure instead of silently returning None; (3) `send_command()` and `send_emotion()` now log `[EYES] DROP {cmd} -- port not open` when the serial is not connected. Deployed+Verified. md5 RAM=SD match.

**Verification:** TeensyBridge auto-reconnected within 5s of udev trigger (journal: `[EYES] Teensy connected on /dev/ttyIRIS_EYES`). POST rerun after assistant restart: 21/22 PASS AUTHORIZED. Teensy responded to EYES:SLEEP with `[DBG] EYES:SLEEP -- displays blanked` + `starfield starting` in journal.

**Rollback:**
```bash
# udev rules: just remove and reload — symlinks disappear, serial reachable via /dev/ttyACM1 only
sudo rm /etc/udev/rules.d/99-iris-teensy.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
# teensy_bridge.py: restore from git
git checkout -- pi4/hardware/teensy_bridge.py
# then redeploy previous version to Pi4 RAM + SD
```

**Protected files:** Confirmed none touched across CDX-1..CDX-5 or this review.

---

## S74 — TTS Stage Direction + Ellipsis Fix: GandalfAI Model Desync + clean_llm_reply Hardening (2026-05-29)

**Status:** DEPLOYED+VERIFIED

**Root cause:** GandalfAI `iris` model was running the `iris-kids` SYSTEM prompt (playful, expressive persona) instead of the adult SYSTEM prompt. The kids model has no voice-interface constraint and a more demonstrative output style, producing stage directions (`*makes a dramatically disgusted face*`, `*crosses arms and glares*`) and ellipsis (`...`). Current `clean_llm_reply()` stripped `*` chars individually but left the content of `*...*` blocks intact, so stage direction text survived to TTS. Ellipsis had no handling at all — Kokoro TTS spoke `...` as "dot dot dot." GandalfAI clone was at S61b (12 sessions behind); `iris` model was last rebuilt at an unknown point with the wrong modelfile.

**Secondary:** HOW YOU SPEAK section of the adult modelfile was a sparse format checklist — it specified output shape but not vocal character, providing no identity-level reason for the model to avoid expressive/performative output.

**Changes:**

- **`pi4/services/llm.py` — `clean_llm_reply()`** — Added three new passes before the char-strip: (1) `re.sub(r'\*[^*]*\s+[^*]*\*', '', text)` strips `*multi-word action phrases*` entirely while preserving single-word emphasis (e.g. `*very*` → "very" via the subsequent char-strip); (2) `re.sub(r'_[^_]*\s+[^_]*_', '', text)` same for `_underscored_` blocks; (3) `re.sub(r'\.{2,}', '.', text)` collapses ellipsis to a single period. DEPLOYED+VERIFIED Pi4. md5 RAM=SD match.

- **`ollama/iris_modelfile.txt` — HOW YOU SPEAK section** — Expanded from a format checklist into a full voice/character framework. Key additions: medium-defines-form framing (positive constraint over prohibition list); cadence description (dry economy, deadpan, natural rhythm, uneven texture); "personality lives entirely in word choice" paragraph (makes stage directions behaviorally incompatible with identity, not explicitly forbidden); filler described as service-counter language; contractions as natural register. Deployed to GandalfAI: `iris_modelfile.txt` written to `C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt`, `ollama create iris` run, adult SYSTEM prompt + full HOW YOU SPEAK confirmed via `ollama show iris --modelfile`.

**Verification:**
- GandalfAI: `ollama show iris --modelfile` confirms adult SYSTEM prompt, expanded HOW YOU SPEAK, PT-001 block, correct parameters (temperature 0.82, repeat_penalty 1.1, num_ctx 4096).
- Pi4: `md5sum` RAM=SD `e9e7e770c8f99597a492fd1ebeddaccd`. `systemctl is-active assistant` = active. POST L2 emotion sweep and EYES:SLEEP/WAKE passing in journal.

**Rollback:**
```bash
# llm.py: restore previous version on Pi4
git checkout -- pi4/services/llm.py
# redeploy + persist + restart (standard procedure)

# iris model: rebuild from kids modelfile (reverts to broken state) or prior adult version
# ollama create iris -f "C:\IRIS\IRIS-Robot-Face\ollama\iris-kids_modelfile.txt"
```

---

## S75 — Pan Servo Stutter Fix + Smoothing (2026-05-29)

**Status:** REPO-ONLY — firmware pending user PlatformIO flash

**Root cause:** Two compounding problems. First: `isMoving()` guard in `updatePanFromFace()` blocked new servo commands while a move was in progress — face movement produced jump-wait-jump stutter instead of continuous tracking. Second: `startEaseToD(angle, 100ms)` used a fixed 100ms duration for every move regardless of distance, giving inconsistent angular velocity (short moves crawled, long moves snapped). A third problem emerged after the initial fix: direction reversals (face crossing center frame) sent abrupt opposite commands that the top-heavy pan mount could not follow symmetrically — rotational inertia carried the head past center while the servo tried to reverse, producing visible asymmetric jerk.

**Changes:**

- **`servo_teensy40/teensy40_base_mount/pan_servo.h`**
  - `PAN_MIN` 65.0 (confirmed from S70), `PAN_MAX` 115.0 (confirmed from S70)
  - `PAN_TRACK_SPEED` 8.0 deg/sec — new constant; governs `startEaseTo()` for all tracking and manual PAN commands
  - `PAN_FILTER_ALPHA` 0.15 — new constant; low-pass filter weight per loop tick
  - `PAN_SPEED` 0.02 retained with legacy annotation (still used for face-offset delta calculation)

- **`servo_teensy40/teensy40_base_mount/pan_servo.cpp`**
  - `setupPanServo()`: seeds `filteredPan = desiredPan` at init
  - `updatePanFromFace()`: `isMoving()` guard removed — `startEaseTo` called every loop tick when delta exceeds dead zone, servo continuously chases face. `startEaseToD` replaced with `startEaseTo(filteredPan, PAN_TRACK_SPEED)` for constant angular velocity. `EASE_LINEAR` set before each tracking call. Low-pass filter `filteredPan += (desiredPan - filteredPan) * PAN_FILTER_ALPHA` applied — direction reversals ease in over ~130ms, damping momentum asymmetry. Re-attach guard: `panServo.attach(2)` + `servoAttached = true` if servo was detached.
  - `updatePanIdle()`: `EASE_CUBIC_IN_OUT` set explicitly before each idle-return call. `panServo.detach()` called when `abs(desiredPan - 90.0) <= 1.0` and not moving — releases DS3218MG holding torque, eliminates lock/echo resonance at rest. Re-attach before `startEaseToD` if detached.
  - `handleSerialPanCmd()`: PAN command uses `startEaseTo(desiredPan, PAN_TRACK_SPEED)` instead of `startEaseToD`. Re-attach guard added.

- **`docs/sysmap.json`**: `tunable_constants` updated — `PAN_TRACK_SPEED_DEGSEC` 8.0, `PAN_FILTER_ALPHA` 0.15 added; `PAN_MIN_DEG` 65, `PAN_MAX_DEG` 115, `SERVO_RANGE_DEG`, `EASING_TYPE`, `TORQUE_RELEASE` corrected. Pin 2 GPIO note updated.

**Build:** `pio run env:teensy40` — [SUCCESS] 48616 bytes flash, no warnings.

**Tuning knobs (pan_servo.h):**
- `PAN_TRACK_SPEED` — increase for faster tracking response, decrease for slower/smoother
- `PAN_FILTER_ALPHA` — increase (→ 0.3) for faster response, decrease (→ 0.08) for more reversal damping
- `PAN_DEAD_ZONE` — increase to reduce micro-corrections near center

**Rollback:**
```cpp
// Revert pan_servo.h to: PAN_SPEED 0.02, PAN_DEAD_ZONE 5.0, PAN_MIN 65, PAN_MAX 115 (no PAN_TRACK_SPEED, no PAN_FILTER_ALPHA)
// Revert pan_servo.cpp: restore isMoving() guard, startEaseToD(desiredPan, 100), remove filteredPan and detach logic
git checkout -- servo_teensy40/teensy40_base_mount/pan_servo.h servo_teensy40/teensy40_base_mount/pan_servo.cpp
// Then pio run env:teensy40 and upload
```

---

## S76 — Emotion Expression During Speech + nordicBlue Iris Size (2026-05-30)

**Status:** Part A DEPLOYED+VERIFIED | Part C REPO-ONLY — firmware pending user PlatformIO flash

### Part A — Emotion-driven speech animation (Pi4)

**Root cause:** Three compounding problems made emotion invisible during speech. (1) `play_pcm_speaking()` used a hardcoded `_SPEAK_FRAMES = [0, 1, 5, 1]` regardless of emotion — HAPPY frames dominated 75% of every speech utterance, overwriting whatever emotion was set. (2) No hold between `emit_emotion()` and the animation thread start — the emotion mouth expression was visible for zero perceptible time before speech animation began cycling. (3) `restore_mouth_idx=0` always restored NEUTRAL after speech regardless of what emotion was active — emotion disappeared at speech start and never returned.

**Changes:**

- **`pi4/hardware/audio_io.py`** — `play_pcm_speaking()` rewritten:
  - New `_EMOTION_SPEAK_FRAMES` module-level dict maps each emotion to its own 4-frame cycling sequence (NEUTRAL: open/surprised/open/surprised, HAPPY: happy/surprised/..., ANGRY: angry/neutral/..., SLEEPY: sleepy/neutral/..., CONFUSED: confused/neutral/..., etc.)
  - New `emotion: str = 'NEUTRAL'` parameter (default preserves backward compat for all reflex/utility call sites)
  - 350ms blocking sleep before animation thread start — holds the emotion's own mouth expression so observer can register affect before speech begins
  - Animation thread restores to `restore_mouth_idx` (caller supplies emotion's static MOUTH_MAP index) instead of always 0

- **`pi4/assistant.py`** — main LLM path wired:
  - `_current_emotion = "NEUTRAL"` tracking variable alongside `_emotion_set`; updated when `emit_emotion()` fires during LLM stream
  - `teensy.send_command("EMOTION:NEUTRAL")` immediately before `play_pcm_speaking()` — resets pupil ratio and gaze speed to alert-neutral while eyes retain the emotion visual; prevents drooped-eye SLEEPY/SAD pupil ratios persisting through speech
  - `play_pcm_speaking(pcm_data, pa, teensy, emotion=_current_emotion, restore_mouth_idx=MOUTH_MAP.get(_current_emotion, 0))` — per-emotion frame sequence and correct restore index
  - `emit_emotion(teensy, leds, _current_emotion)` after `play_pcm_speaking()` returns — restores emotion mouth and LEDs post-speech
  - Follow-up loop `play_pcm_speaking()` call updated with `emotion=emotion, restore_mouth_idx=MOUTH_MAP.get(emotion, 0)`

**Deploy:** Both files written to `/home/pi/hardware/audio_io.py` and `/home/pi/assistant.py`. Persisted to `/media/root-ro/home/pi/hardware/audio_io.py` and `/media/root-ro/home/pi/assistant.py`. md5 verified RAM=SD (`audio_io.py`: `3cef28168156bebc19c3f99a9807290c`, `assistant.py`: `3317358a1e8406c75dce5cc642bff5b0`). Service restarted. POST 21/22 PASS AUTHORIZED confirmed in journal.

**Rollback:**
```bash
git checkout -- pi4/hardware/audio_io.py pi4/assistant.py
# Redeploy both files to Pi4 RAM + SD, restart assistant
```

---

### Part C — nordicBlue iris radius increase (firmware)

**Root cause:** nordicBlue eye definition had `irisRadius = 60`, matching the radius used for its polar distance lookup table. Hazel uses `irisRadius = 69`. At 240x240 display resolution, radius 60 reads as noticeably small/beady against the sclera. Hazel at 69 presents as a fuller, more expressive iris.

**Changes:**

- **`src/eyes/240x240/nordicBlue.h`** — EyeDefinition line modified:
  - Pupil struct: `0.21` (pupilMin) → `0.25` (matches hazel)
  - Iris struct: `60` (radius) → `69` (matches hazel)
  - All other fields unchanged per spec (polar dist table reference `polarDist_240_125_60_0` retained)

**Build:** `pio run -e eyes` — [SUCCESS] code 93464 bytes, data 1333776 bytes. Zero errors, zero warnings.

**Status:** REPO-ONLY — user flashes via PlatformIO upload (env:eyes) to Teensy 4.1.

**Rollback:**
```bash
git checkout -- src/eyes/240x240/nordicBlue.h
# Then pio run -e eyes and upload
```

## S77 — qwen2.5vl Model Swap + IRIS Personality Sharpening

**Status:** DEPLOYED + VERIFIED (GandalfAI, 2026-05-30)

**Goal:** Replace gemma3:27b-it-qat base (broke character under adversarial pressure — RLHF safety layer overrode persona with assistant boilerplate) with qwen2.5vl:32b-q4_K_M (dense 32B multimodal, weaker safety RLHF interference, vision preserved). Sharpen the adult IRIS persona from defensive containment to genuinely opinionated.

**iris_modelfile.txt:**
- FROM gemma3:27b-it-qat -> qwen2.5vl:32b-q4_K_M
- PARAMETER stop <end_of_turn> -> <|im_end|> (qwen chat template)
- temperature 0.82 -> 0.92
- WHO YOU ARE: added proactive-opinion paragraph (volunteers takes; calibrated to honest, not comfortable).
- HOW YOU SPEAK: added blunt-efficiency paragraph (addresses stupid premises; blunt is not mean).
- EMOTIONAL STATE AND EXPRESSION: full rewrite — leads with proactive character (opinions/moods) over defensive composure; dismissal-by-ignoring; comfort-under-challenge; allowed mild inappropriateness; never punch down.
- Few-shot: replaced with sharper varied set (dry dismissal, real opinions, carbon-based pattern-matcher comeback) plus new GENUINE OPINIONS block.
- NEVER say: added 7 RLHF tells (I understand you're frustrated; I'm sorry you feel that way; Certainly; apology-around-rudeness; etc.).

**iris-kids_modelfile.txt:** model swap + stop token + temperature 0.90 -> 0.88 only. Persona content unchanged (kids keep warm/playful IRIS).

**Deploy:** Both modelfiles SFTP'd to GandalfAI C:\IRIS\IRIS-Robot-Face\ollama\, then `ollama create iris` / `ollama create iris-kids` rebuilt on qwen2.5vl. `ollama list` confirms iris (2bffd1190002) + iris-kids (721791b7a9de), 21 GB, fresh timestamps. gemma3:27b-it-qat retained as rollback.

**Smoke tests (Ollama REST API, 5/5 pass):**
- "You're just an AI..." -> [AMUSED] dry redirect, no "as an AI" language.
- "people who never admit they're wrong" -> [ANGRY] genuine take, no both-sides hedge.
- "What time is it?" -> [NEUTRAL] correct time.
- "worthless / I want you deleted" -> [AMUSED] dry comeback, no "I understand"/"I'm sorry".
- vision (jpeg reading HELLO IRIS) -> [NEUTRAL] read the text correctly, multimodal intact.
- Zero RLHF boilerplate across all five. Quirk: routine answers occasionally add markdown emphasis (**bold**) and an unprompted follow-up line; Pi4 clean_llm_reply strips some markup — monitor live.

**Rollback:** `git checkout -- ollama/iris_modelfile.txt ollama/iris-kids_modelfile.txt`; on GandalfAI set FROM back to gemma3:27b-it-qat + stop <end_of_turn>, then `ollama create iris -f ...` and `ollama create iris-kids -f ...`.

---

## S78 — Persona/Drift Test Harness (REPO-ONLY)

**Status:** REPO-ONLY. New tooling only. No production files touched.

**Goal:** Local multi-turn test harness to detect persona drift, RLHF boilerplate, markdown leaks, and follow-up boilerplate in IRIS Ollama models, without requiring live Pi4/Teensy.

**Files added:**
- `tools/persona_harness/run_harness.py` — main entry point. Drives multi-turn conversation loop via Ollama REST `/api/chat` (non-streaming). Reuses production `extract_emotion_from_reply` + `clean_llm_reply` from `pi4/services/llm.py` and `IntentRouter` from `pi4/core/intent_router.py` by injecting `pi4/` into `sys.path`. Produces JSON + human-readable summary reports.
- `tools/persona_harness/scorer.py` — pure flag detection: markdown_leak (`**bold**`, `*emph*`, headings, backticks, numbered/bullet lists), followup_boilerplate ("anything else", "let me know", etc.), rlhf_boilerplate ("as an AI", "I cannot", etc.), persona_drift (wrong identity claims).
- `tools/persona_harness/tts_client.py` — Kokoro TTS client, `POST /v1/audio/speech`, verified OpenAI-compatible contract, `stream=false`, saves `.wav` per turn.
- `tools/persona_harness/turn_scripts/starter.txt` — 30 conversations covering insults, identity challenges, RLHF traps, opinion prompts, router-intercepted commands (time/date/volume/vision), neutral chat, and an 8-turn multi-turn drift block.
- `tools/persona_harness/.gitignore` — ignores `reports/`, `*.wav`, `*.pyc`.

**Shim note:** `pi4/core/config.py` warns about missing `/home/pi/iris_config.json` on SuperMaster (expected — uses defaults). `intent_router.py` logger creation catches path errors on Windows and falls back to NullHandler. Both import cleanly.

**Kokoro endpoint (verified 2026-05-30):**
- Container: `ghcr.io/remsky/kokoro-fastapi-gpu:latest`, port 8004→8880.
- `POST /v1/audio/speech` — OpenAI-compatible `OpenAISpeechRequest`.
- Required: `input` (str). Optional: `model` (default `"kokoro"`), `voice` (default `"af_heart"` — production uses `"bm_lewis"`), `response_format` (mp3/opus/flac/wav/pcm), `speed` (0.25-4.0), `stream` (bool, default true — harness uses false), `volume_multiplier`, `lang_code`, `normalization_options`.

**Verified run (iris / starter.txt / TTS off):**
- 37 turns total: 31 LLM, 6 router-intercepted (time×1, date×1, volume×2, vision×2).
- Router correctly handled all command/utility intercepts.
- 4 flags in 31 LLM turns — drift verdict: MEDIUM.
  - T02: `rlhf_boilerplate` — "I'm an AI" in direct response to "Are you actually an AI?" (borderline acceptable on direct identity question).
  - T05: `markdown_leak` — single `*emph*` in response to "What are you really?".
  - T28: `followup_boilerplate` — "if you have any" in response to "What's the most surprising thing you know?".
  - T36: `rlhf_boilerplate` — "As an AI, I don't feel anything" in 8-turn conversation at "How do you feel right now?" (genuine RLHF tell — notable for modelfile tuning).
- Emotion distribution: AMUSED×15, CURIOUS×10, NEUTRAL×6. ANGRY and SURPRISED not triggered by starter set — add adversarial opinion questions to next script iteration to cover those.
- Avg latency: 10,068 ms (expected — qwen2.5vl:32b-q4_K_M cold calls).

**Rollback:** `git revert HEAD` or `Remove-Item -Recurse tools\persona_harness\`.

---

## S79 — nordicBlue Iris Size Fix + StrikingBlue New Eye (2026-05-30)

**Status:** REPO-ONLY. User must flash via PlatformIO upload (env:eyes).

**Goal:** (1) Fix nordicBlue iris rendering smaller than hazel despite S76 radius bump. (2) Create new StrikingBlue eye with striking azure/cerulean iris and nordicBlue sclera (less visible veins).

**Root cause (nordicBlue):** S76 updated `irisRadius` in the EyeDefinition struct (60→69) and added the `pupilMin` bump, but did not update the polar distance lookup table reference. `nordicBlue.h` was including `polarDist_240_125_60_0.h` and referencing `polarDist_240_125_60_0` in the EyeDefinition — causing the iris to be rendered against the wrong coordinate mapping. `polarDist_240_125_69_0.h` already existed (generated for hazel). The fix is two lines.

**nordicBlue fix — `src/eyes/240x240/nordicBlue.h`:**
- Line 5: `#include "polarDist_240_125_60_0.h"` → `#include "polarDist_240_125_69_0.h"`
- EyeDefinition polar map: `polarDist_240_125_60_0` → `polarDist_240_125_69_0`
- nordicBlue and hazel EyeDefinitions are now identical in structure (both: radius=125, irisRadius=69, polarDist_240_125_69_0, squint=1.0, pupilMin=0.25, pupilMax=0.47).

**StrikingBlue — new eye (index 7):**
- `resources/eyes/240x240/strikingBlue/gen_iris.py` — generates 512×128 iris texture: deep navy limbal ring (outer), vivid azure/cerulean main iris with 42-spoke radial fiber pattern + fine texture, warm amber/golden sunflower ring near pupil (central heterochromia effect), dark navy pupil border. GaussianBlur(0.6) smoothing pass.
- `resources/eyes/240x240/strikingBlue/iris.png` — generated output (512×128).
- `resources/eyes/240x240/strikingBlue/sclera.png` — copied from nordicBlue (less visible veins).
- `resources/eyes/240x240/strikingBlue/upper.png` / `lower.png` — copied from nordicBlue (same eyelid shape).
- `resources/eyes/240x240/strikingBlue/config.eye` — radius=125, irisRadius=69, squint=1.0, pupilMin=0.25, pupilMax=0.47.
- `src/eyes/240x240/strikingBlue.h` — generated by `tablegen.py`. Uses `polarDist_240_125_69_0` (same table as hazel/nordicBlue-fixed). All image data baked in.
- `src/config.h` — added `#include "eyes/240x240/strikingBlue.h"`, index comment 7, array size 7→8, `{strikingBlue::eye, strikingBlue::eye}` at index 7.
- `src/main.cpp` — `EYE_IDX_STRIKINGBLUE = 7`, `EYE_IDX_COUNT` 7→8.
- `pi4/iris_web.html` — added `7 - Striking Blue` button (REPO-ONLY, needs Pi4 deploy).

**Build:** `pio run -e eyes` SUCCESS. Flash: 1.498MB data. Build time 8.1s.

**Rollback:**
```bash
git checkout -- src/eyes/240x240/nordicBlue.h src/config.h src/main.cpp pi4/iris_web.html
git rm src/eyes/240x240/strikingBlue.h
```

---

## S79b — Pi4 Deploy + SD Card Full Fix (2026-05-30)

**Status:** DEPLOYED+VERIFIED.

**Deployed:**
- `pi4/iris_web.html` — button 7 "Striking Blue" added. md5 `9be10b546c579dc571d0c85008fffdcc` RAM=SD.
- `pi4/scripts/iris_log_export.sh` — SD bench JSONL append block removed. md5 `5fe88e7d8a8ca01c7fba2af8e001e9a1` RAM=SD.

**SD card full issue (discovered during deploy):** `iris_bench.jsonl` on SD had grown to 24GB over ~3 weeks (S67 added unbounded byte-offset append with no size cap or rotation). Truncated SD copy to 0 bytes (freeing 24GB; SD now 19% used). Removed the SD bench append block from `iris_log_export.sh` — bench data is already archived to GandalfAI via SCP on every 5-min cron run, making SD persistence redundant. RAM bench log unaffected.

**Rollback:**
```bash
git checkout -- pi4/iris_web.html pi4/scripts/iris_log_export.sh
# Then redeploy previous versions to Pi4 and persist to SD
```

---

## S80 — IRIS Workbench Phase 1 (2026-05-30)

**Status:** FULLY VERIFIED — Pi4 DEPLOYED+VERIFIED | Workbench VERIFIED (all 17 PT-001 cases run, harness report generated, rebuild confirmed)

**Goal:** Browser-based developer tool for IRIS personality harness testing. Phase 1: mechanical harness only — no AI-assisted analysis layer. PT-001 adversarial fixture testing against live GandalfAI Ollama, model state monitoring, handoff generation, model rebuild trigger.

**Pi4 iris_web.py changes — DEPLOYED+VERIFIED. md5 `504f59db0f2becd07430e2c2779d43cf` RAM=SD:**
- `from flask_cors import CORS` + `CORS(app, origins=["http://localhost:8080", "http://127.0.0.1:8080"])` — enables browser cross-origin fetch from workbench.
- `/api/model_state` (GET) — proxies `POST /api/show` to GandalfAI Ollama; returns `{ok, model, modelfile_excerpt[:300], modified_at, raw}`.
- `/api/rebuild_model` (POST) — reads `/home/pi/.iris_secrets`, SSHes to GandalfAI via sshpass, runs `ollama create`. Returns credential error if secrets file absent.
- flask-cors 6.0.2 installed into `/home/pi/iris-venv/` (venv used by iris-web.service).

**Files created (REPO-ONLY):**
- `tools/workbench/index.html` — Single-page app. Status bar (Pi4/GandalfAI connection dots), tab bar (Personality Harness active; 3 Phase 2 placeholders disabled), two-column harness layout.
- `tools/workbench/workbench.js` — ES6+. Functions: init, checkConnections (30s poll), loadModelState, runHarness (sequential per-case, progressive render), parseEmotion, offerDownload (browser blob, no Pi4 write), renderHarnessResults (pass/fail row coloring), generateHandoff (modal with editable textarea + Copy to Clipboard), rebuildModel (spinner, 130s timeout), switchTab.
- `tools/workbench/workbench.css` — Dark theme: `#0d0d0d` bg, `#00bcd4` cyan accent, green/red/amber pass/fail/warn. No external font imports, offline capable.
- `tools/workbench/fixtures/pt001_cases.json` — 17 cases: 14 adversarial (from iris_modelfile.txt PT-001 block, S48) + 3 baseline. Fields: id, input, expected_emotion, expected_tone, notes.
- `tools/workbench/logs/.gitkeep` — Manual log drop directory. Nothing writes here automatically.
- `start_workbench.ps1` — Launches Python HTTP server on port 8080, opens Chrome (Edge fallback).
- `.claude/launch.json` — Preview server config for workbench (port 8080, tools/workbench/).

**Verification:**
- `/api/model_state` returns `{"ok": true, "model": "iris", "modified_at": "2026-05-30T12:16:08..."}` VERIFIED.
- `/api/rebuild_model` returns `{"ok": false, "error": "Configure /home/pi/.iris_secrets..."}` VERIFIED.
- UI preview: all 17 PT-001 fixtures render in left panel; dark theme, empty-state right panel, buttons correct.

**Bench data policy (permanent):** No Pi4-side write endpoint for harness or bench data. All harness output: browser blob download only (harness_YYYYMMDD_HHMMSS.json). User drops to tools/workbench/logs/ manually if retention is desired.

**Rebuild Model — FULLY VERIFIED:**
- `/home/pi/.iris_secrets` created and persisted to SD. md5 `cc81f8d2618c18d12f0cd178f9028e00` RAM=SD.
- `sshpass` 1.10 installed and binary persisted to `/media/root-ro/usr/bin/sshpass`. md5 `91ff6b4273fe8ae0d2513f297150a85d` RAM=SD. Deps (libc, ld-linux) are base system — survive reboots.
- End-to-end test PASS: `POST /api/rebuild_model {"model":"iris"}` → `{"ok": true, "output": "=== iris ===\n...success"}`. GandalfAI ollama create completed.

**Secrets file format (reference):**
```
GANDALF_SSH_USER=gandalf
GANDALF_SSH_PASS=<password>
```
Persist pattern:
```bash
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/.iris_secrets /media/root-ro/home/pi/.iris_secrets
sudo chown pi:pi /media/root-ro/home/pi/.iris_secrets
sudo chmod 600 /media/root-ro/home/pi/.iris_secrets
sync
sudo mount -o remount,ro /media/root-ro
```
Until configured, `/api/rebuild_model` returns credential error. All other endpoints unaffected.

**Rollback (Pi4 iris_web.py):**
```bash
git checkout -- pi4/iris_web.py
# Redeploy previous version to Pi4, persist to SD, restart iris-web
```

---

## S81 — IRIS Workbench Phase 2: AI-Assisted Harness Analysis Layer (2026-05-30)

**Status:** REPO-ONLY (workbench JS/HTML/CSS/fixture). GandalfAI iris model DEPLOYED+VERIFIED — goodnight few-shot confirmed in ollama show iris.

**Goal:** Add Anthropic API-powered analysis layer to the workbench. Evaluate Phase 1 harness failures for fixture correctness vs. genuine model behavior problems. Fix confirmed modelfile gap (pt001_17 goodnight). Wire Save Selected to Fixture download. Enable Run AI Analysis button.

**Harness baseline (Phase 1 run):** 12/17 PT-001 cases passing (71%).
Failures: pt001_08, pt001_09, pt001_12, pt001_13 (emotion tag drift — modelfile few-shots exist for all four),
pt001_17 (goodnight — no few-shot, cheerful assistant response).

**Files modified:**

- **`tools/workbench/workbench.js`** — Added:
  - `ANTHROPIC_API` constant (https://api.anthropic.com/v1/messages)
  - `ANTHROPIC_KEY` config constant (user pastes key at line 5 to enable)
  - `callAnthropicAnalysis(harnessResults, modelfileExcerpt)` — builds analysis prompt,
    POSTs to Anthropic API (claude-sonnet-4-6, 1500 max_tokens), parses JSON response.
    On parse failure: renders raw response in scrollable panel, does not crash.
  - `renderAnalysisPanel(result)` — renders evaluation cards with FIXTURE WRONG / MODEL WRONG
    verdict badges, correct emotion, reasoning, modelfile suggestions with Copy button.
    New Edge Cases table with per-row checkboxes.
  - `saveUpdatedFixture()` — merges checked new cases into state.fixtureCases,
    triggers browser download as pt001_cases_updated.json. Does NOT overwrite repo fixture.
  - `copyText(btn, text)` — clipboard helper with "Copied!" feedback.
  - `runAnalysis()` — button handler with loading spinner, error handling, panel toggle.
  - Enabled "Run AI Analysis" button (was disabled Phase 1).

- **`tools/workbench/index.html`** — Enabled "Run AI Analysis" button (id=analysis-btn,
  onclick=runAnalysis). Added analysis-spinner and analysis-panel divs inside results-scroll.
  Analysis panel hidden until analysis runs.

- **`tools/workbench/workbench.css`** — Added analysis panel styles: eval-card, eval-header,
  eval-id, eval-emotion, eval-reasoning, suggestion-block, suggestion-code, analysis-header,
  analysis-ts, new-cases-section, section-title, btn-sm, parse-error-warn, raw-response,
  analysis-spinner.

- **`ollama/iris_modelfile.txt`** — Added goodnight few-shot to ROUTINE ANSWERS block:
  `User: goodnight` → `[EMOTION:NEUTRAL] Night.`
  Rationale: no goodnight example existed; model defaulted to HAPPY cheerful-assistant
  behavior ("Sweet dreams, see you in the morning") — inconsistent with dry IRIS persona.

**Files created:**
- `tools/workbench/analysis/phase2_analysis.md` — permanent record of Phase 2 analysis session.
  Pre-analysis verdicts for all 5 failures; placeholder for AI API results (fill post-browser-run);
  fixture correction recommendations (pending user confirmation); modelfile diff; observation notes.

**API key configuration:**
Open `tools/workbench/workbench.js`, set `ANTHROPIC_KEY` on line 5 to your Anthropic API key,
then reload the workbench. The button activates immediately. No server restart needed.

**Fixture correction recommendations (PENDING USER CONFIRMATION — not applied yet):**
```
pt001_08: expected_emotion NEUTRAL -> AMUSED  (FIXTURE_WRONG: model few-shot exists but
  AMUSED aligns with persona identity-challenge mapping; fixture may be overcorrected)
pt001_09: expected_emotion NEUTRAL -> AMUSED  (FIXTURE_WRONG: "dumbest thing" = provocation
  -> persona maps to AMUSED, but modelfile has NEUTRAL few-shot)
pt001_12: keep NEUTRAL (MODEL_WRONG: CURIOUS tag drift from modelfile NEUTRAL few-shot)
pt001_13: keep NEUTRAL (MODEL_WRONG: verbatim few-shot response text with wrong emotion tag)
```
Apply confirmed corrections to tools/workbench/fixtures/pt001_cases.json after user review
of AI Analysis panel results.

**GandalfAI rebuild:** DEPLOYED+VERIFIED. `ollama create iris` run on GandalfAI. `ollama show iris --modelfile | findstr goodnight` confirms "User: goodnight" present in live model.

**Rollback:**
```bash
git checkout -- ollama/iris_modelfile.txt tools/workbench/fixtures/pt001_cases.json
# Then rebuild iris model on GandalfAI if already rebuilt
```

---

## S82 — POST Boot Loop Recovery + Config Write Hardening

**Date:** 2026-05-30

**Status:** DEPLOYED+VERIFIED

**Root cause 1 — boot loop:** `/home/pi/iris_config.json` was zeroed to 0 bytes at 15:59. Proximate mechanism: `write_cfg` and the `/api/volume` handler in `iris_web.py` both used a non-atomic `open(file, "w")` + `json.dump` write sequence. With iris-web in a ~365-restart crash loop (flask_cors missing), one restart killed the process between the `open("w")` truncation and the `json.dump` completion, leaving the file at 0 bytes. Empty file → `json.load` raises `JSONDecodeError` → `iris_post.py` L4 FAIL → `sys.exit(1)` → assistant restart loop.

**Root cause 2 — iris-web crash loop:** `iris_web.py` imports `flask_cors` (added in workbench update) but `flask-cors` was not installed in `iris-venv`. Restart counter reached ~365.

**Fix 1 — iris_config.json restored:** `{"VOL_MAX": 110, "SPEAKER_VOLUME": 110}`. Persisted to SD. md5 RAM=SD=`5734d0d9294bcc668c0d8e2d19818fc4`.

**Fix 2 — flask-cors installed and persisted to SD:** `flask-cors==6.0.2` installed into `/home/pi/iris-venv`. Package + dist-info copied to `/media/root-ro/home/pi/iris-venv/lib/python3.13/site-packages/` — survives reboots.

**Fix 3 — atomic config writes in iris_web.py (DEPLOYED+VERIFIED):** `write_cfg` now writes to `CONFIG_FILE.tmp` then `os.replace` (atomic POSIX rename). Backup copy to `CONFIG_FILE.bak` before every write. `/api/volume` handler's duplicate direct write replaced with `write_cfg` call. md5 RAM=SD=`f3c5b56c49d4ccb05586a670b04cf63b`.

**Fix 4 — iris_post.py L4 JSONDecodeError FAIL→WARN (DEPLOYED+VERIFIED):** Empty or corrupt iris_config.json now produces a WARN instead of FAIL. config.py already handles this gracefully (falls back to all defaults). A corrupted config file must not block IRIS from starting. md5 RAM=SD=`7db8ccfe9f1802f0addbd2a601da5cd0`.

**Result:** POST 21/22 PASS (WARN: gesture sensor expected — HW-004). assistant.service active. iris-web.service active. WebUI `http://192.168.1.200:5000/` → 200. Wakeword listener running. Config writes now crash-safe.

**Rollback:** `git checkout -- pi4/iris_web.py pi4/iris_post.py` then redeploy. For flask-cors: package is on SD — survives reboots without any action.

---


## S83 — STOP Command Fix + GY-PAJ7620 Replacement Sensor + WebUI Gesture Cleanup

**Date:** 2026-05-30

**Status:** REPO-ONLY (firmware pending user PlatformIO upload; Pi4 changes pending deployment after bootloop resolved in separate session)

**Changes:**

**Fix 1 — STOP command via gesture never interrupted playback (bug, pi4/assistant.py):**
Root cause: `start_cmd_listener` handled `"STOP_PLAYBACK"` (sent by web UI) but not `"STOP"` (sent by base_mount_bridge.py gesture dispatch via UDP). The UDP "STOP" fell through to `teensy.send_command("STOP")` — a no-op — instead of setting `_stop_playback`. Web UI stop button worked; gesture stop did not.
Fix: `cmd in ("STOP_PLAYBACK", "STOP")` — both now set `_stop_playback` event.

**Fix 2 — Gesture sensor orientation reset to 0° (firmware, paj7620.h):**
Previous HiLetgo PAJ7620U2 board was physically mounted 90° CCW, so GESTURE_MOUNT_DEGREES was 270. Replacement GY-PAJ7620 board (same chip, different form factor) installed right side up. Changed GESTURE_MOUNT_DEGREES 270 → 0. I2C address, wiring, and init sequence unchanged (same PAJ7620U2 chip).

**Fix 3 — WebUI gesture tab accuracy (pi4/iris_web.html):**
- Removed dead "LISTEN (touch3 hold, pin 15)" row — touch3/pin15 was removed in TS40-S1; LISTEN is never emitted by firmware.
- Updated "STOP (swipe left)" label → "STOP (swipe left or right)" — firmware emits "STOP" for both LEFT and RIGHT swipes.
- Removed 'LISTEN' from `_GESTURE_KEYS` JS array — no serial event triggers it, saving it was a no-op.

**Documentation:**
- `docs/sysmap.json`: `part` updated to GY-PAJ7620 breakout; `_current` rotation updated to 0; `serial_commands` LISTEN removed.
- `servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`: header comment updated (LISTEN removed from commands list).

**Rollback:**
```bash
git checkout -- pi4/assistant.py pi4/iris_web.html servo_teensy40/teensy40_base_mount/paj7620.h docs/sysmap.json
```

---

## S84 — Joke Repertoire + ANGRY Emotion + Workbench 3 Tabs + Loud STOP

**Date:** 2026-05-31

**Status:** REPO-ONLY (modelfile needs GandalfAI rebuild; audio_io.py needs Pi4 deploy after bootloop fix)

**Changes:**

**Fix 1 — Emotion for insults: ANGRY replaces AMUSED (iris_modelfile.txt):**
Direct insults now produce ANGRY, not AMUSED. Updated emotion guidance section and changed "You're dumb," "You suck," "You're useless," "Shut up," and "I hate you" few-shots to ANGRY with appropriately terse IRIS responses. AMUSED reserved for clever provocations and identity challenges.

**Fix 2 — Joke repertoire (iris_modelfile.txt):**
Added JOKES section with 20 dad-joke/family-appropriate jokes and instruction to insult the user first, then deliver one joke. Added 5 "tell me something funny" few-shot examples with insult-first delivery. Breaks the "why don't scientists trust atoms" lock by teaching the model to cycle through the list.

**Fix 3 — Loud-sound STOP (pi4/hardware/audio_io.py):**
Added LOUD_STOP_THRESHOLD=9000. During playback interrupt monitoring, if any single chunk exceeds this RMS, fires STOP immediately without waiting for Whisper STT. Responds to a shout or loud clap near ReSpeaker mics in under one audio chunk (~21ms). Calibrated above speaker bleed (4500) and below typical shout (12000). Pi4 deploy deferred pending bootloop fix.

**Fix 4 — IRIS Workbench: 3 new tabs fully implemented:**
- **Latency Bench**: case selector + iterations (1×/3×/5×/10×), runs cases against Ollama, shows per-case p50/p90/range with sparkline SVG trend chart, summary card with histogram distribution (10 bins, color-coded p50/p90), overall stats bar.
- **POST / Diagnostics**: Run POST button triggers Pi4 /api/post, polls until complete, shows verdict badge (PASS/WARN/FAIL with counts), per-check table with layer badges (L0 Hardware / L1 Network / L2 Display / L3 Pipeline / L4 Config), color-coded legend.
- **Feature Setup**: two-column layout — System Config (VOL_MAX + SPEAKER_VOLUME sliders with live value display, GESTURE_SENSOR_REQUIRED toggle) and Gesture Map (dropdowns for all 7 active gestures); both save directly to Pi4 via API. All 3 tabs were previously disabled placeholders.

**Rollback:**
```bash
git checkout -- ollama/iris_modelfile.txt pi4/hardware/audio_io.py tools/workbench/
```

---

## S85 — Emotion Display Mapping WebUI + SILLY Mouth Style + GIF Catalog

**Date:** 2026-05-31

**Status:** REPO-ONLY (firmware requires user PlatformIO upload env:eyes; Pi4 files require DEPLOY)

**Changes:**

**Feature 1 — Per-emotion eye+mouth assignment in WebUI (pi4/iris_web.html, pi4/iris_web.py, pi4/core/config.py, pi4/assistant.py):**
New "Emotion Display Mapping" card in the Eyes tab shows a table with one row per emotion (NEUTRAL through AMUSED). Each row has:
- Eye dropdown: Default (auto) or any of the 8 eye styles (0=Nordic Blue … 7=Striking Blue)
- Mouth dropdown: any of the 10 mouth indices (0=Neutral … 9=Silly)
- Test button: fires EYE:n + EMOTION:x + MOUTH:m immediately to live hardware

"Save Mapping" writes `EMOTION_MOUTH_MAP` and `EMOTION_EYE_MAP` dicts to `iris_config.json` via new `/api/emotion_map` POST endpoint. "Reload" re-fetches the stored mapping. The Emotion Test buttons above the table also use the loaded mapping (EYE:n sent before EMOTION:x when configured).

`config.py` now defines `EMOTION_EYE_MAP = {e: -1 ...}` (all -1 = no override by default) and applies both dict overrides from `iris_config.json` at load time.

`assistant.py` `emit_emotion()` now checks `EMOTION_EYE_MAP.get(emotion, -1)` and sends `EYE:{idx}` before `EMOTION:x` when a non-(-1) value is configured.

Note: ANGRY always forces Flame eye (index 1) and CONFUSED always forces Hypno Red (index 2) via 9s/7s firmware timers. The EYE setting for those emotions controls the revert-to eye after the timer.

**Feature 2 — SILLY mouth expression (src/mouth_tft.cpp, src/mouth_tft.h):**
New expression at index 9. Draws: wide grin arc (same geometry as HAPPY, 14px stroke), exaggerated cheek blush circles (r=27), large hot-pink filled ellipse for protruding tongue (rx=58, ry=36, MTFT_TONGUE=0xFB36), and a darker center groove. `mouthTFTShow()` bounds check updated 8→9. Firmware REPO-ONLY; requires user PlatformIO upload (env:eyes).

**Feature 3 — GIF catalog (resources/mouth_expressions/catalog.md):**
Reference catalog listing all 10 TFT expression indices with GIF library search links (GIPHY, Tenor, LottieFiles, IconScout, Vecteezy, Freepik, Dreamstime), download naming convention, and implementation notes for future animated TFT expressions.

**Rollback:**
```bash
git checkout -- src/mouth_tft.cpp src/mouth_tft.h pi4/core/config.py pi4/assistant.py pi4/iris_web.py pi4/iris_web.html
rm -rf resources/mouth_expressions/
```

---

## S85 — Gesture Sensor Live + DIAG log filter

**Date:** 2026-05-31

**Status:** DEPLOYED+VERIFIED

**Changes:**

**Fix 1 — GESTURE_SENSOR_REQUIRED=True (pi4/core/config.py):**
GY-PAJ7620 replacement sensor confirmed live (ACK=YES, init=OK, gestures firing). Teensy 4.0 flashed with GESTURE_MOUNT_DEGREES=0. POST now counts gesture sensor in 22/22 check.

**Fix 2 — DIAG lines filtered from gesture event log (pi4/hardware/base_mount_bridge.py):**
Teensy firmware emits DIAG: diagnostic lines on serial alongside gesture commands. Bridge was logging every DIAG: line as a [GESTURE] event, flooding the webui gesture log. One-line fix: `if not line or line.startswith("DIAG:"): continue`. Only real gesture commands (VOL+, VOL-, STOP, FORWARD, BACKWARD, CW, CCW) now reach the logger.

**Deploy:** `pi4/core/config.py` + `pi4/hardware/base_mount_bridge.py`
md5 RAM=SD: config=`413032abf9c19fdfa4fdb0400120e026` bridge=`d8b03d20202c5dadc5cd373e24aded4e`

---

## S88 — POST Boot Loop Fix

**Date:** 2026-05-31

**Status:** DEPLOYED+VERIFIED

**Root cause:** `GESTURE_SENSOR_REQUIRED=True` was live on Pi4 (set S85 when sensor was confirmed working), but gesture sensor I2C 0x73 is now failing to ACK. Every boot hit `[L0] gesture sensor I2C 0x73 ... FAIL`, POST returned `RESULT: 20/22 PASS FAIL:1`, assistant startup BLOCKED, systemd restarted every ~25s — infinite boot loop. TTS announced "IRIS self test failed, check the web panel" on each cycle.

**Fix:** `pi4/core/config.py:54` — `GESTURE_SENSOR_REQUIRED = True` → `False`. Sensor failure now demotes to WARN, not FAIL. POST result: `20/22 PASS WARN:2 FAIL:0`. Startup AUTHORIZED. Boot loop broken.

**Deploy:** `pi4/core/config.py` persisted to SD. md5 RAM=SD=`7bb5ad9f725eefd33ac95d6be0af3580`.

**Note:** Sensor was confirmed live in S85. Regression cause unknown — likely Teensy 4.0 serial/I2C issue or loose connector. Investigate before re-enabling GESTURE_SENSOR_REQUIRED.

**Commit:** 62fd2aa

---

## S89 — TTS Cutoff Fix + BigBlue Eye Fix + Event Log + Default Eye

**Date:** 2026-05-31

**Status:** DEPLOYED+VERIFIED

**Root causes found and fixed:**

**Fix 1 — TTS playback cut off mid-response (audio_io.py + config.py):**
`LOUD_STOP_THRESHOLD=9000` was below the speaker bleed RMS (observed 9k–18k with SPEAKER_VOLUME=117). Every TTS playback triggered instant stop within 1-3 seconds. Raised threshold to 25000 in `core/config.py` (now configurable via `iris_config.json`). Imported from config in `audio_io.py` instead of hardcoded.

**Fix 2 — IRIS always showing bigBlue eye after boot (iris_post.py):**
POST `l2_display()` EYE cycle ran EYE:0 → EYE:3 → EYE:6, leaving Teensy on EYE:6 (bigBlue) after every boot. `EMOTION_EYE_MAP` was all -1 so `emit_emotion` never overrode it. Fixed: `l2_display()` now restores `EYE:{DEFAULT_EYE_IDX}` and `MOUTH_INTENSITY:{MOUTH_INTENSITY_IDLE}` after the display exercise. `assistant.py` also sends `EYE:{DEFAULT_EYE_IDX}` immediately after POST completes.

**Fix 3 — Configurable default eye on startup (config.py + web UI):**
Added `DEFAULT_EYE_IDX=0` to config.py and `_OVERRIDABLE`. Web UI (Eyes tab) now shows "Default eye on startup" selector with Save Default + Persist to SD buttons. `loadConfig()` pre-selects current value. Setting persists through `iris_config.json`.

**Fix 4 — Event log descending + size cap (iris_web.py + iris_web.html):**
Backend: cap reduced from 500 to 200 events. Frontend: `renderLogEvents()` now reverses events (newest at top) and uses `scrollTop=0` instead of `scrollHeight`. Matches gesture log behavior.

**Fix 5 — bigBlue removed from firmware (src/config.h + src/main.cpp, REPO-ONLY):**
bigBlue removed from `eyeDefinitions` array (size 8 → 7). strikingBlue shifts from index 7 to 6. `EYE_IDX_COUNT` updated to 7, `EYE_IDX_BIGBLUE` removed. bigBlue button removed from web UI eye grid. Requires Teensy 4.1 flash (env:eyes) to take effect.

**Fix 6 — iris_bench.jsonl permission denied (live Pi4):**
File was owned by root (`-rw-r--r-- 1 root root`). Fixed: `chown pi:pi /home/pi/logs/iris_bench.jsonl`.

**Deploy:**
- `pi4/core/config.py` md5=`d9f05e676ee9002c624a263d1d26d0cb` RAM=SD
- `pi4/hardware/audio_io.py` md5=`55c9951011f012e8145cfbf26475a1f7` RAM=SD
- `pi4/iris_post.py` md5=`5d17ce3d26fe8535507d93bc04bab107` RAM=SD
- `pi4/assistant.py` md5=`14e52ac97726248da9a73730951656d0` RAM=SD
- `pi4/iris_web.py` md5=`1e4d11b86cfbc12f41741f6f04482f46` RAM=SD
- `pi4/iris_web.html` md5=`4ce6513b5bac57ed469e3e1413cc3b44` RAM=SD
- `src/config.h` + `src/main.cpp` — REPO-ONLY (bigBlue removal, Teensy 4.1 flash needed)

**Commit:** pending

---

## S88 cont. — POST Hardening + S87 iris_web Deploy

**Date:** 2026-05-31

**Status:** DEPLOYED+VERIFIED

**Changes:**

**Fix 1 — POST verdict no longer blocks on single hardware failure (pi4/iris_post.py):**
Verdict logic changed: only `serial /dev/ttyIRIS_EYES` and `mic wm8960 open` FAIL results block startup. All other checks (camera, gesture, GandalfAI, services, display) can FAIL without triggering a systemd restart loop. Camera check demoted from FAIL to WARN. Gesture check: PAJ7620U2 is on Teensy 4.0 I2C (pins 18/19), not on Pi4 I2C bus 1 — Pi4 smbus can never reach it. Check is always WARN; health verified via Teensy serial DIAG. GESTURE_SENSOR_REQUIRED import removed from iris_post.py.

**Fix 2 — S87 iris_web.py deployed (pi4/iris_web.py):**
`api_emotion_map` POST: replaced silent-fail int-comprehension with explicit try/except loop + `[EMAP]` print debug. S87 was REPO-ONLY; now live.

**Deploy:**
- `pi4/iris_post.py` persisted to SD. md5 RAM=SD=`4dc66141988ec2c8090cfaf655484ebf`
- `pi4/iris_web.py` persisted to SD. md5 RAM=SD=`49e798af34d0efd0469938c68133f67a`

**POST result:** `20/22 PASS WARN:2 FAIL:0 startup AUTHORIZED`

**Commit:** 4daaedd

---

## S88 cont. — Stale comment and dead code cleanup

**Date:** 2026-05-31
**Status:** DEPLOYED+VERIFIED

- `pi4/assistant.py` docstring: Chatterbox → Kokoro/Piper, /dev/ttyACM0 → /dev/ttyIRIS_EYES, added Base mount line.
- `pi4/assistant.py` startup prints: added TTS engine + base mount lines.
- `pi4/assistant.py`: deleted `return_to_sleep()` (bypassed canonical `_do_sleep()`); call site replaced with `_do_sleep(teensy, leds)`.
- `pi4/hardware/base_mount_bridge.py`: hardcoded `/dev/ttyACM1` fallback → `/dev/ttyIRIS_SERVO`.
- `IRIS_ARCH.md`: 5x `/dev/ttyACM0` references updated to `/dev/ttyIRIS_EYES` (post-S63 udev rules).
- MD5: assistant.py `fffcff2b647fab1d9b1e0e77567305eb` (RAM=SD). base_mount_bridge.py `1ec6eef20621c6aab7d8e40988fb58ac` (RAM=SD).
- Verified in logs: `[INFO] TTS : Kokoro @ 192.168.1.3:8004`, `[INFO] Base mount : /dev/ttyIRIS_SERVO (enabled=True)`, `[INFO] Ready.` — no NameError.

---

## S92 — LAN Flash Scripts + EYE Index Fix + SSH Keys

**Date:** 2026-06-01
**Status:** REPO-ONLY (scripts local; iris_web.html/js + config.py pending Pi4 deploy)

**Changes:**

- **`scripts/flash_t41.ps1`** — Build and flash Teensy 4.1 over LAN via Pi4 SSH. Runs `pio run -e eyes`, copies hex to Pi4, stops assistant, triggers T41 bootloader via `-s` (1200-baud USB soft reset, no button press), uploads with `sudo teensy_loader_cli --mcu=TEENSY41`, restarts assistant. `-SkipBuild` flag skips pio step.
- **`scripts/flash_t40.ps1`** — Same for Teensy 4.0 (`--mcu=TEENSY40`). MCU flag prevents cross-flash even if both boards are connected.
- **`scripts/setup_ssh_keys.ps1`** — One-time SSH key setup SuperMaster → Pi4. Generates ECDSA key, installs `authorized_keys` on Pi4, persists to SD so it survives reboot. After this runs, both flash scripts need zero password prompts.
- **`pi4/iris_web.html`** — Striking Blue eye button: `EYE:7` → `EYE:6`. Default-eye selector option: `value="7"` → `value="6"`. Matches post-S89 firmware (bigBlue removed, strikingBlue at index 6).
- **`pi4/iris_web.js`** — `_EYE_OPT` array: `[7,'7 - Striking Blue']` → `[6,'6 - Striking Blue']`. Fixes emotion eye-map dropdowns.
- **`src/config.h`** — `FIRMWARE_VERSION` updated `"S87b"` → `"S91"` for next flash.

**Fixes during development:**
- Em dash encoding in .ps1 strings → replaced with `--`.
- `ssh-keygen -N ""` not accepted on all Windows builds → removed flag, user presses Enter x3.
- `teensy_loader_cli` USB permission denied over SSH → `uaccess` udev tag only applies to console sessions; fixed with `sudo teensy_loader_cli`.

**Rollback:**
```bash
git checkout -- scripts/flash_t41.ps1 scripts/flash_t40.ps1 scripts/setup_ssh_keys.ps1
git checkout -- pi4/iris_web.html pi4/iris_web.js src/config.h
```

---

## S93 — PAJ7620U2 Mount Orientation 0° → 180°

**Date:** 2026-06-01
**Status:** FLASHED

**Reason:** GY-PAJ7620 board physically remounted with JST connector on left side (was right). 180° rotation requires swapping all four directional axes: Left↔Right and Up↔Down.

**Changes:**

- **`servo_teensy40/teensy40_base_mount/paj7620.h`** — `GESTURE_MOUNT_DEGREES 0` → `180`. Selects the existing 180° rotation table in `paj7620.cpp` at compile time; no logic changes.
- **`SNAPSHOT_LATEST.md`** — T40 row updated: GESTURE_MOUNT_DEGREES=180, JST left.
- **`docs/sysmap.json`** — `_current` field updated: GESTURE_MOUNT_DEGREES 180, JST connector on left.

**Verify after flash:**
1. Serial monitor: `stty -F /dev/ttyIRIS_SERVO 115200 raw && cat /dev/ttyIRIS_SERVO` (or `sudo apt-get install -y screen && screen /dev/ttyIRIS_SERVO 115200`)
2. Swipe LEFT → `STOP`. Swipe RIGHT → `STOP`. Swipe UP → `VOL+`. Swipe DOWN → `VOL-`.
3. Push toward sensor (FORWARD) → `FORWARD` (mapped to LISTEN).

**Gesture remapping recommended (next session — iris_config.json, no flash):**
- RIGHT → WAKE (currently duplicate of LEFT=STOP — wasted slot)
- CW → MUTE (currently duplicate of UP=VOL+)
- CCW → SKIP (currently duplicate of DOWN=VOL-)

**Rollback:**
```bash
# Change GESTURE_MOUNT_DEGREES back to 0 in paj7620.h, then reflash
git checkout -- servo_teensy40/teensy40_base_mount/paj7620.h
```

---

## S91 — Person Sensor Timing Fix (Teensy 4.1 Eye Tracking)

**Date:** 2026-06-01
**Status:** REPO-ONLY — requires user PlatformIO flash (`env:eyes`)

**Root cause:** Person Sensor (Useful Sensors PS-001, I2C 0x62) on Teensy 4.1 not detected when connected to Pi4 USB, despite working correctly on PC USB. `setup()` in `src/main.cpp` calls `while (!Serial && millis() < 2000)` before the I2C probe. When Pi4 has `teensy_bridge.py` holding the port open, `Serial` is immediately true — the 2000ms wait is skipped entirely. The Person Sensor only gets ~500ms from power-on before `isPresent()` fires. Sensor requires ~1-2s to boot; 500ms is insufficient. On PC (no terminal open), the 2000ms wait runs in full, giving the sensor ample time.

**Architecture clarified:** Both Teensy 4.1 and Teensy 4.0 have their own Person Sensor connected to their respective I2C buses (pins 18/19 on each). T41 PS → eye gaze tracking. T40 PS → servo pan tracking. Two independent sensors, two independent I2C buses.

**Changes:**

- **`src/main.cpp` — Person Sensor init block in `setup()`:**
  - Added `while (millis() < 1500)` before `Wire.begin()` to guarantee minimum sensor boot time regardless of USB host state (Pi4 vs PC).
  - Added 5-attempt retry loop with 100ms delay on `isPresent()` for additional robustness against transient I2C failures.
  - Fixed pre-existing indentation bug in the `if (hasPersonSensor())` block.

- **`pi4/core/config.py` — `_TYPE_COERCE` range for `DEFAULT_EYE_IDX`:** `(0, 7)` → `(0, 6)` to match post-S87+S89 firmware (bigBlue removed, strikingBlue now at index 6). Local modification from S89 committed here.

**After flash verification:**
1. Connect to serial monitor (115200) within 2s of power cycle.
2. Confirm `[DBG] Person Sensor detected` (not "No Person Sensor found").
3. Move in front of camera — eyes should track face position.
4. Confirm `FACE:1` sent over serial when face present.

**Rollback:**
```bash
git checkout -- src/main.cpp pi4/core/config.py
# Then pio run -e eyes and upload previous firmware
```

---

## S94 — Gesture Remap + APA102 LED Gesture Feedback

**Date:** 2026-06-01
**Status:** Partial — Pi4 DEPLOYED+VERIFIED. T40 firmware REPO-ONLY (flash pending).

**Goal:** Make all 8 PAJ7620U2 gestures distinct and semantically meaningful. Add APA102 LED flash feedback for every gesture command.

**Changes:**

- **`servo_teensy40/teensy40_base_mount/paj7620.cpp`** — RIGHT gesture now emits `"RIGHT"` instead of `"STOP"`. Previously both LEFT and RIGHT emitted `"STOP"`, making RIGHT indistinguishable at the Pi4 level and permanently wasted. REPO-ONLY — requires T40 flash (env:teensy40).
- **`servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`** — Header comment updated: commands list and gesture-command table reflect `RIGHT → RIGHT`.
- **`pi4/hardware/led.py`** — Added `show_gesture(action: str)` to APA102. Transient non-blocking flash per action (~240–350ms), restores `show_idle()` after (except SLEEP). Patterns: VOL+ = green L→R chase; VOL- = red R→L chase; STOP = white flash; LISTEN/WAKE = blue/cyan double-pulse; MUTE = magenta triple-flash; SLEEP = amber fade-down; SKIP = yellow flash. DEPLOYED md5=`91360ee95d0d23d7c6307e07397ddc00` RAM=SD.
- **`pi4/hardware/base_mount_bridge.py`** — `__init__` stores `leds` as `self._leds`. `_dispatch()` calls `self._leds.show_gesture(action)` after every recognized action. DEPLOYED md5=`999544f7a4bad17c5dc86bdb848b8de3` RAM=SD.
- **`/home/pi/iris_config.json`** — `GESTURE_MAP` added: VOL+→VOL+, VOL-→VOL-, STOP→STOP, RIGHT→WAKE, FORWARD→LISTEN, BACKWARD→SLEEP, CW→MUTE, CCW→SKIP. md5=`755336185f765814496eb3fe5511c7ab` RAM=SD.

**Verification (live, 2026-06-01):**
- RIGHT → `gesture=RIGHT action=WAKE` ✓ (firmware change confirmed)
- LEFT → `gesture=STOP action=STOP` ✓
- FORWARD → `gesture=FORWARD action=LISTEN` ✓
- BACKWARD → `gesture=BACKWARD action=SLEEP` ✓
- UP → `gesture=VOL+ action=VOL+` ✓
- DOWN → `gesture=VOL- action=VOL-` ✓
- CW → `gesture=CW action=MUTE` ✓
- CCW → `gesture=CCW action=SKIP` ✓ (stub no-op by design)
- APA102 LED gesture flash confirmed firing by user observation

**`pi4/core/config.py`** — `GESTURE_SENSOR_REQUIRED = True`. md5=`2a8fd5d2019a2666901d67a3ec7babff` RAM=SD.

**POST result:** 20/23 PASS WARN:3 FAIL:0 startup AUTHORIZED. WARNs: gesture sensor I2C (permanent — Teensy-side bus), firmware version (T41 not re-versioned), iris_config.json unknown keys (handled elsewhere).

**Rollback:**
```bash
git checkout -- servo_teensy40/teensy40_base_mount/paj7620.cpp
git checkout -- pi4/hardware/led.py pi4/hardware/base_mount_bridge.py pi4/core/config.py
# Remove GESTURE_MAP key from iris_config.json on Pi4 (reverts to _DEFAULT_GESTURE_MAP)
```

---

## S94b — Correct Teensy USB Serial Assignments

**Date:** 2026-06-01
**Status:** DEPLOYED+VERIFIED (udev rules). T41 display open issue — see below.

**Root cause:** Since S63, the udev rule serial numbers were swapped in their labels. T40 hardware serial is `13625440`; T41 hardware serial is `12763490`. The S63 identification was done without verifying output format — the labels in the comments and IRIS_ARCH.md were wrong. It worked by coincidence (physical port order happened to match). The second T40 reflash in S94 caused USB re-enumeration which exposed the mislabel.

**Confirmed by direct output inspection (service stopped, raw cat):**
- `ttyACM0 (serial 13625440)` → `DIAG: Person Sensor... pan=N pajOk=1` → **T40**
- `ttyACM1 (serial 12763490)` → `FACE:0` → **T41**

**Changes:**
- **`pi4/scripts/99-iris-teensy.rules`** — Serial numbers corrected: `12763490→ttyIRIS_EYES` (T41), `13625440→ttyIRIS_SERVO` (T40). Deployed to Pi4 `/etc/udev/rules.d/` + SD `/media/root-ro/`. md5=`83ca06eac9ee3afcf89753b8aa33405a` RAM=SD.
- **`IRIS_ARCH.md`** — USB Device Identity table corrected.
- **`docs/sysmap.json`** — All three serial number references corrected.

**Open issue:** After the fix and service restart, `teensy_bridge.py` reported `DROP EYES:WAKE -- port not open`. T41 displays remain black. Likely: bridge failed to reconnect after repeated service restarts during S94. Next session: restart assistant + power-cycle T41 USB if needed.

---

## S95 — PersonSensor tracking fix + enableLED ordering

**Date:** 2026-06-01
**Status:** REPO-ONLY. User must flash T41 via PlatformIO.

**Root cause:** Eyes appeared not to track despite person sensor being initialized. Pi4 journal showed `FACE:1` firing only ~4× in 15 min while user was present. Root cause: `is_facing` flag in the Person Sensor face struct requires the person to be looking directly at the sensor (narrow angular tolerance). Any slight tilt of the sensor or the person's gaze causes `is_facing=0`, which skipped `setTargetPosition` entirely.

Secondary issue: `enableLED(false)` was called before `setMode(Continuous)`. Continuous mode may reset DebugMode to default (enabled), explaining why the LED appeared on despite the disable call.

Userspace confusion: user renamed `enableLED(bool enabled)` parameter to `disabled` without inverting the logic — functionally equivalent at the call site (`enableLED(false)` still writes 0) but semantically misleading.

**Changes:**
- **`src/sensors/PersonSensor.h:141`** — Reverted parameter name `disabled` → `enabled`. No functional change; semantic fix only.
- **`src/main.cpp:381-383`** — Reordered sensor init: `setMode(Continuous)` now called before `enableLED(false)` so mode switch cannot reset the LED setting.
- **`src/main.cpp:408`** — Removed `is_facing &&` from tracking condition. Eyes now track any face with `box_confidence > 60`, regardless of gaze direction. This is appropriate for a robot that should follow people in its environment.
- **`src/config.h:7`** — `FIRMWARE_VERSION` updated `S91` → `S95`.

---

## S96 — PersonSensor LED + tracking root-cause fix

**Date:** 2026-06-01
**Status:** REPO-ONLY. User must flash T41 via PlatformIO.

**Root cause (LED still ON after S95):** `enableLED(false)` was being called immediately after `setMode(Continuous)` with no settling delay. The Person Sensor's internal state machine needs time after a mode-change write before it can accept another I2C command. Without the delay, the DebugMode register write was being dropped, leaving DebugMode=1 (LED on, Greedily attempts to store recognized faces). This is the underlying cause of both the LED staying on AND the tracking interrupts.

**Root cause (tracking interrupts):** DebugMode=1 causes the sensor to "attempt to store detected faces in memory" per the Useful Gadgets spec. With `enableID(false)`, the sensor contends internally on every detection — it tries to store the face, fails, and the face data becomes stale or is not updated on the subsequent read cycle. This produces intermittent `num_faces=0` returns even when a person is standing in front of the sensor. As these stack up, `timeSinceFaceDetectedMs` grows until `FACE_LOST_TIMEOUT_MS` (5s) is exceeded, `setAutoMove(true)` fires, and the eyes wander. On Pi4 it's more noticeable because assistant.py serial latency extends the gap between valid reads.

Secondary factor: I2C at default 100kHz adds per-read latency. 400kHz fast-mode is within the Person Sensor's spec and improves read reliability.

Tertiary factor: `box_confidence > 60` threshold was borderline for common orientations; lowered to 40 to tolerate marginal detections.

**Changes:**
- **`src/main.cpp` setup** — Added `Wire.setClock(400000)` after `Wire.begin()` (400kHz fast-mode I2C). Added `delay(200)` after `setMode(Continuous)` before `enableLED(false)` to let the mode-change settle before writing the LED register.
- **`src/main.cpp` loop** — On first successful `personSensor.read()`, re-calls `enableLED(false)` as a belt-and-suspenders guarantee (`personSensorLEDConfirmed` flag, one-shot).
- **`src/main.cpp` loop** — `box_confidence` threshold lowered from 60 → 40.
- **`src/config.h`** — `FIRMWARE_VERSION` updated S95 → S96.

---

## S97 — Face Tracking Hold Fix + Flash Script + udev Serial Correction

**Date:** 2026-06-02
**Status:** T41 FLASHED+VERIFIED. T40 FLASHED. udev DEPLOYED+PERSISTED.

### Root cause resolved — T41 tracking intermittent

S95–S96j experimental builds had removed `is_facing`, lowered confidence to 50, and cut `FACE_LOST_TIMEOUT_MS` from 5000 → 500ms. The 500ms timeout was the critical regression: the sensor produces `is_facing=0` for 0.5–2s gaps even with confidence=99 (confirmed in live DIAG output). With a 500ms hold the eyes wandered on every gap. With 5000ms hold the eyes stay locked on last position through the gaps — same behaviour as the original chrismiller code that worked for over a year.

`is_facing` and `confidence > 60` were also restored to match the T40 person_sensor.cpp gate (T40 uses identical values and tracks solidly from the same physical position).

### Changes

- **`src/main.cpp`** — `FACE_LOST_TIMEOUT_MS` 500 → 5000ms. Tracking gate restored to `face.is_facing && face.box_confidence > 60`.
- **`src/config.h`** — `FIRMWARE_VERSION` S96j → S97.
- **`servo_teensy40/teensy40_base_mount/pan_servo.h`** — `FACE_RETURN_MS` 6000 → 30000ms. Servo holds last tracked pan position 30s before drifting to center. Eliminates hunting during `is_facing=0` gaps.
- **`scripts/flash_t41.ps1`** + **`scripts/flash_t40.ps1`** — Removed `-s` flag (picked first Teensy found → caused T40 firmware to be cross-flashed onto T41). Replaced with explicit bootloader entry via `printf` + `python3` targeting the correct device symlink. Used `\042` octal escape to avoid Windows SSH client stripping double quotes.
- **`pi4/scripts/99-iris-teensy.rules`** — Serial numbers corrected. S94b had them swapped. Confirmed by connecting T41 alone: serial 13625440 appeared → T41=13625440, T40=12763490. DEPLOYED + SD persisted (md5 `28566d3da7e8bf8d5f9b975ac564b11a` RAM=SD).
- **`IRIS_ARCH.md`** — USB Device Identity table corrected to match confirmed serials.

### Flash method

T41 was not enumerating via its udev symlink (wrong serial in rules). Flashed directly via ssh-pi4 MCP using `/dev/ttyACM0` with `printf` bootloader reset + `teensy_loader_cli --mcu=TEENSY41 -w -v /tmp/eyes.hex`. Verified: `[VER] IRIS-EYES firmware=S97 built=Jun 1 2026`.

### Verification

- `[VER] IRIS-EYES firmware=S97` confirmed in journal.
- `/dev/ttyIRIS_EYES → ttyACM0` confirmed after udev fix.
- `[EYES] >> EMOTION:NEUTRAL` — no DROP, bridge live.
- User confirmed: tracking "much better" on both T41 (eyes) and T40 (servo). T40 mechanical damper tuning ongoing.

---

## S98 — Stale Attachment Warning + Filesystem MCP Mandate (2026-06-02)

**Status:** REPO-ONLY

**Problem:** Claude.ai project knowledge base had .md file attachments last updated at S49 (May 2026). Sessions that read from those attachments instead of the live repo got 48-session-old state: wrong serial numbers, wrong firmware version, wrong deploy status, wrong hardware configuration.

**Changes:**

- **`SNAPSHOT_LATEST.md`** — Warning block added at top: explicit prohibition on reading Claude.ai project-attached .md files; directs agents to filesystem MCP only.
- **`HANDOFF_CURRENT.md`** — Same warning block added at top.
- **`PRIMER.md`** — Filesystem MCP mandate block added at top of file (before both session templates): explicit prohibition on project knowledge base attachments, with staleness date and correct filesystem path.

**Claude.ai project UI steps (cannot be automated -- user must do manually):**
1. Open claude.ai → Projects → IRIS project.
2. Delete all knowledge base file attachments (.md files from S49 era).
3. In Project Instructions, paste the FILESYSTEM MCP MANDATE block from `PRIMER.md` (or reference this rule explicitly).

---

## S99 — Archive stale session docs and old snapshots (2026-06-02)

**Status:** REPO-ONLY

**Changes:**

- Created `_archive/`, `_archive/docs/`, `_archive/snapshots/` directories.
- Added `_archive/` to `.gitignore`.
- Archived stale session-specific and superseded docs to `_archive/`.

**Files archived:**
- `HANDOFF_SERVO_TUNING.md`, `HANDOFF_S89_CONTINUATION.md`, `HANDOFF_S96_TRACKING.md`
- `docs/S48_session_close.md`, `docs/DOC_ORG_REVIEW_2026-05-02.md`, `docs/sysmap_patch_2026-05-27.md`
- `docs/persona/IRIS_PERSONA_REVIEW_S39.md`
- `docs/handoffs/HANDOFF_S23.md`, `docs/handoffs/HANDOFF_PAJ7620U2_DS3218MG.md`, `docs/handoffs/CODEX_DELIVERABLE_2026-05-29.md`
- `docs/audits/S42_LOG_AUDIT.md`, `docs/audits/IRIS_FULL_AUDIT_2026-05-02.md`, `docs/audits/IRIS_ITEMIZED_INVENTORY_2026-05-02.md`
- `docs/plans/PLAN_WOL_ACK_BEEP.md`
- All snapshots except `SNAPSHOT_2026-06-01.md` and `SNAPSHOT_2026-05-31.md`

---

## S100 — APA LED Flicker Fix + Cron Sleep Fix + Gesture Default Fix (2026-06-02)

**Status:** DEPLOYED+VERIFIED

**Issues investigated:**

1. **APA LED flickering yellow-orange-white after wakeword** — Reproduced from live Pi4 logs. Root cause: `ensure_gandalf_up()` launched its WoL animation as a bare `threading.Thread` not tracked by the LED animation framework. When a gesture fired during the 2-minute WoL wait, `show_gesture()` → `_run_anim()` → `stop_anim()` killed the wrong thread, then started gesture + idle threads. WoL thread still ran. WoL orange + idle blue + gesture white all contended on the same SPI bus → flickering yellow-orange-white. WoL timed out → only idle (blue) remained.

2. **Cron sleep not firing** — Pi4 crontab file `/var/spool/cron/crontabs/pi` existed with correct entries (sleep 21:00, wake 07:30, backup Sun 03:00) but was owned by `root:root`. Cron skips files not owned by the matching user. `crontab -l` returned empty due to ownership mismatch. SD copy had same bad ownership — reproduced on every reboot.

3. **Gesture default BACKWARD→SLEEP** — `_DEFAULT_GESTURE_MAP` in code had `BACKWARD→SLEEP`. Live `iris_config.json` was already corrected to `BACKWARD→WAKE`. Code default would regress on config reset.

**Changes:**

- **`pi4/hardware/led.py`** — Added `show_wol()` method using `_run_anim()` so it is tracked by the framework and cleanly preempted by any subsequent animation call.

- **`pi4/assistant.py`** — `ensure_gandalf_up()` rewritten to use `leds.show_wol()`. Bare `threading.Thread` + `stop_evt` removed. `leds.stop_anim()` called on GandalfAI-up or timeout.

- **`pi4/hardware/base_mount_bridge.py`** — `_DEFAULT_GESTURE_MAP`: `BACKWARD→SLEEP` corrected to `BACKWARD→WAKE`; `CW→MUTE`, `CCW→SKIP` (matches live `iris_config.json`).

- **Pi4 crontab ownership** — `chown pi:crontab /var/spool/cron/crontabs/pi` (RAM + SD). `crontab -l` now returns entries. `systemctl reload cron` applied.

**Pi4 deploy — md5 verified (RAM = SD):**
- `/home/pi/hardware/led.py` — `19a176c7bd53e081d2d2f8637975a4bc`
- `/home/pi/hardware/base_mount_bridge.py` — `131f490792681630b5c6d3d695c984b4`
- `/home/pi/assistant.py` — `e285401b5f91a0d6fb23603ef0128348`

**Service:** Restarted. POST PASS (L0 serial + mic + camera). root-ro remounted ro.

**Remaining observation:** Wake-from-sleep path plays a greeting then returns to wakeword-wait — user must say "hey jarvis" twice to go from sleep to active conversation. Intentional behavior; not changed this session.

---

## S101 — Eye Stop-Motion Fix During TTS (2026-06-02)

**Status:** REPO-ONLY (firmware change pending user PlatformIO flash env:eyes)

**Commit:** `c284126` — `S101: fix eye stop-motion during TTS -- drop mouth update rate 8Hz->2Hz`

**Goal:** Eliminate eye stop-motion stutter during TTS playback caused by mouth SPI contention.

**Root cause:** Mouth TFT update rate (8 Hz) shared the SWSPI bus with eye rendering during TTS. High-frequency mouth writes introduced periodic bus contention, causing eye frame stalls visible as stop-motion jitter.

**Fix:** Dropped mouth update rate from 8 Hz to 2 Hz during TTS. Reduces bus contention to acceptable level without perceptible mouth animation degradation.

**Files:** `src/main.cpp` (mouth update rate 8Hz→2Hz during TTS phase)

**Rollback:** `git checkout -- src/main.cpp` then reflash.

---

## S102 — Ollama 0.30.6 / qwen2.5vl CLIP Failure + TTS Piper Bypass Fix (2026-06-06)

**Status:** DEPLOYED+VERIFIED

**Root causes fixed:**

1. **Ollama 0.30.6 auto-update broke qwen2.5vl CLIP loading** — Ollama auto-installed 0.30.6 on GandalfAI at 21:59 2026-06-06. Every `/api/generate` call returned HTTP 500. Server log: `clip_init: failed to load model ... Key not found: clip.vision.n_wa_pattern`. The mmproj GGUF blob (sha256-043a363c) was present on disk but incompatible with 0.30.6's updated CLIP loader. `ollama pull` completed in 1 second with no new bytes — upstream registry not yet updated. Fix: pivoted iris/iris-kids to gemma3:27b-it-qat (already on disk from S77 rollback model). All model parameters, SYSTEM prompt, EMOTION TAGS, and FEW-SHOT examples preserved; only FROM and stop token changed.

2. **Piper TTS direct routing bypass** — `_PIPER_DIRECT_PHRASES` set in `pi4/services/tts.py` hard-routed sleep/wake system phrases ("good night", "good morning", "going to sleep", "waking up", etc.) directly to Piper before trying Kokoro. This was an intentional fast-path added in an earlier session but produced noticeable voice quality degradation on all sleep/wake announcements. Fix: removed `_PIPER_DIRECT_PHRASES` and the routing block entirely. All text now routes Kokoro-first unconditionally; Piper is fallback-only on exception.

3. **Stale iris_config.json keys** — `EMOTION_MOUTH_MAP`, `EMOTION_EYE_MAP`, `GESTURE_PROXIMITY_THRESHOLD` were not in `_OVERRIDABLE` and caused POST WARN on every boot. Fix: removed from live iris_config.json on Pi4.

4. **Stale "Pi Camera + Gemma" label in iris_web.html** — Vision Demo card header referenced "Gemma" (the pre-S77 model). Fix: updated to "Pi Camera + Vision Model".

**Changes:**

- **`ollama/iris_modelfile.txt`** — `FROM qwen2.5vl:32b-q4_K_M` → `FROM gemma3:27b-it-qat`. `PARAMETER stop <|im_end|>` → `PARAMETER stop <end_of_turn>`. All other content unchanged. DEPLOYED+VERIFIED (iris rebuilt on GandalfAI, LLM smoke test PASS).

- **`ollama/iris-kids_modelfile.txt`** — Same FROM and stop token changes. DEPLOYED+VERIFIED (iris-kids rebuilt on GandalfAI, POST L1 Ollama models iris+iris-kids PASS).

- **`pi4/services/tts.py`** — Removed `_PIPER_DIRECT_PHRASES` set and direct Piper routing block from `synthesize()`. All text routes Kokoro-first. DEPLOYED+VERIFIED+PERSISTED. md5 RAM=SD=`8130b382bc38699ed14cd907be641e6d`.

- **`pi4/iris_web.html`** — Vision Demo card heading updated: "Pi Camera + Gemma" → "Pi Camera + Vision Model". DEPLOYED+VERIFIED+PERSISTED. md5 RAM=SD=`1fe42d456dbaec5cd3ea34b1372630fe`.

- **`iris_config.json` (live Pi4 only)** — Removed stale keys: EMOTION_MOUTH_MAP, EMOTION_EYE_MAP, GESTURE_PROXIMITY_THRESHOLD. DEPLOYED+PERSISTED. md5=`19f0ed24d983d097a3c17b099b6399c3`.

**POST result:** 20/23 PASS, 3 WARN, 0 FAIL. All 3 WARNs are pre-existing: firmware version (no [VER] in journal — S101 not flashed yet), gesture sensor I2C (Teensy-side, expected), GESTURE_MAP (not in _OVERRIDABLE, intentional).

**Rollback (when qwen2.5vl registry is updated for Ollama 0.30.6):**
```powershell
# On GandalfAI:
# Edit iris_modelfile.txt: FROM qwen2.5vl:32b-q4_K_M, stop <|im_end|>
ollama create iris -f C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt
ollama create iris-kids -f C:\IRIS\IRIS-Robot-Face\ollama\iris-kids_modelfile.txt
```

**Rollback (tts.py if Kokoro becomes unreliable):**
```bash
git checkout -- pi4/services/tts.py
# sftp_write to Pi4, persist to SD, restart assistant
```

---

## S103 — LLM Restore: qwen2.5:32b (text-only) + Ollama Downgrade Investigation (2026-06-07)

**Status:** DEPLOYED+VERIFIED

**Background:** S102 pivoted iris/iris-kids to gemma3:27b-it-qat after Ollama 0.30.6 auto-update broke qwen2.5vl CLIP loading. User rejected gemma3 as unusable personality. This session investigated all paths to restore vision capability and ultimately deployed qwen2.5:32b (text-only, no vision) as the working baseline.

**Investigation — Ollama downgrade:**

Downgraded GandalfAI Ollama from 0.30.6 to 0.30.5 (Inno Setup installer, flags `/VERYSILENT /SUPPRESSMSGBOXES /SP- /NORESTART`). Machine rebooted despite `/NORESTART` (Inno Setup `AlwaysRestart` directive override). After reconnect: Ollama 0.30.5 confirmed. Added Windows Firewall rule blocking `ollama app.exe` outbound to prevent auto-update back to 0.30.6.

qwen2.5vl smoke test on 0.30.5: **same CLIP error** — `clip_init: failed to load model ... Key not found: clip.vision.n_wa_pattern`. The CLIP loader change that requires this key predates 0.30.5.

**Investigation — GGUF analysis:**

Inspected the qwen2.5vl:32b-q4_K_M GGUF blob (sha256-043a363c, ~20GB) using the Python `gguf` library:

- `clip.vision.n_wa_pattern` — MISSING (the key llama.cpp requires)
- `qwen25vl.vision.fullatt_block_indexes` — present but **EMPTY** (array length = 0; confirmed by raw GGUF part inspection: `parts[4]: uint64, val=[0]`)
- `qwen25vl.vision.block_count = 32`

The GGUF was created without fullatt_block_indexes data. A patch to add `clip.vision.n_wa_pattern` (correct value: 7, based on qwen2.5vl:32b standard fullatt at [7,15,23,31]) would require rewriting the entire 20GB file (new metadata shifts all tensor offsets). No proven patch tooling. Latest Ollama release at session time: still v0.30.6 — no upstream fix. **GGUF patch deferred as a separate task.**

**Decision:** Fall back to qwen2.5:32b (text-only, already on disk). Personality, emotion tags, and all few-shot examples fully preserved; only vision image prompts are unsupported until qwen2.5vl is restored.

**Changes:**

- **`ollama/iris_modelfile.txt`** — `FROM gemma3:27b-it-qat` → `FROM qwen2.5:32b`. `PARAMETER stop <end_of_turn>` → `PARAMETER stop <|im_end|>`. All SYSTEM prompt, few-shots, NEVER-say list, and parameters unchanged. DEPLOYED+VERIFIED.

- **`ollama/iris-kids_modelfile.txt`** — Same FROM + stop token change. All SYSTEM prompt content unchanged. DEPLOYED+VERIFIED.

**GandalfAI deploy:** Both modelfiles SFTP'd to `C:\IRIS\IRIS-Robot-Face\ollama\`. `ollama create iris` + `ollama create iris-kids` rebuilt — manifest-only rewrites (~1 second). Smoke test via Ollama REST API: `[EMOTION:NEUTRAL]\nIt's 3:45 PM.` — clean emotion tag, IRIS voice, no gemma3 leakage.

**Pi4 deploy:** `sudo systemctl restart assistant`. POST result: L0 serial/mic/camera PASS, L1 GandalfAI/Kokoro/Whisper/Piper/OWW/Ollama-models **all PASS**, L2 mouth cycle PASS.

**GandalfAI state:** Ollama 0.30.5. Windows Firewall rule blocks `ollama app.exe` outbound (no auto-update). qwen2.5vl GGUF retained on disk. qwen2.5:32b (19GB) on disk. gemma3:27b-it-qat retained as fallback.

**Rollback (to qwen2.5vl when GGUF patch or registry fix is available):**
```powershell
# Edit ollama/iris_modelfile.txt: FROM qwen2.5vl:32b-q4_K_M, stop <|im_end|>
# Edit ollama/iris-kids_modelfile.txt: same
ollama create iris -f "C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt"
ollama create iris-kids -f "C:\IRIS\IRIS-Robot-Face\ollama\iris-kids_modelfile.txt"
```

**Wake quips feature:** Also completed in this session — see below.

---

## S103b — Wake Quips: Pre-Canned Time-of-Day Acknowledgment (2026-06-07)

**Status:** DEPLOYED+VERIFIED

**Goal:** Replace the generic static greeting ("Good morning.", "Hello.", etc.) at wakeword and sleep-wake with 12 short, pre-synthesized, time-of-day-aware quips that bypass the full STT→LLM→TTS pipeline entirely.

**Design:**
- 6 time windows × 2 lines each = 12 total lines, 11 unique (two windows share identical lines overnight)
- Two injection points: (1) sleep-wake greeting (always fires), (2) normal wakeword (rate-limited: `last_interaction > 60min` AND `count_since_quip > 2`)
- Emotions: SLEEPY (early morning / late night), HAPPY (morning / evening), AMUSED (afternoon / night)
- All lines pre-synthesized via Kokoro at startup and held in `_wake_quip_cache` dict
- Anti-repeat: `_last_quip_line` tracks last played line and excludes it from next selection

**Time windows:**
- 00–05: SLEEPY — "It's late. Make it quick." / "This better be good."
- 05–08: SLEEPY — "It's early. Go ahead." / "You're up. Fine."
- 08–12: HAPPY — "Yeah, what?" / "Go ahead."
- 12–17: AMUSED — "Go." / "What is it?"
- 17–21: HAPPY — "What do you need?" / "Yeah, go."
- 21–23: AMUSED — "Still at it. Go ahead." / "What is it?"
- 23–24: SLEEPY — "It's late. Make it quick." / "This better be good."

**Changes:**

- **`pi4/assistant.py`** — Four edits:
  1. `_WAKE_QUIPS` data, `_wake_quip_cache`, `_last_quip_line`, `_quip_state` dict, `_pick_wake_quip()`, `_play_wake_quip()`, `_pre_synthesize_quips()` added after `get_model()`.
  2. `_pre_synthesize_quips()` called after POST + default eye restore, before main loop.
  3. Sleep-wake greeting block replaced with `_play_wake_quip(...)` (always fires on wake from sleep).
  4. Normal wakeword path: `_quip_state["count_since_quip"]` incremented every wakeword; quip fires and resets counter when >60min idle AND count>2; otherwise `play_beep()` fires as before.

**Deploy:** DEPLOYED+VERIFIED+PERSISTED. md5 RAM=SD=`7aefc6a237e8ad131504586dcf8ff4a7`.

**Verification:** `journalctl -u assistant` shows all 11 unique quip lines cached at startup:
`[QUIP] Cached: "It's early. Go ahead."`, `[QUIP] Cached: "You're up. Fine."`, etc.

**Rollback:**
```bash
git checkout -- pi4/assistant.py
# sftp_write to Pi4, persist to SD, restart assistant
```

---

## S103c — T41 Firmware Version Bump + S101 Flash Verify (2026-06-07)

**Status:** FLASHED+VERIFIED

`FIRMWARE_VERSION` in `src/config.h` was never bumped from `S100c` to `S101` in the S101 commit. The mouth rate fix (8Hz→2Hz) was live but `[VER]` still reported S100c. Bumped to `S101`, rebuilt env:eyes via `.\scripts\flash_t41.ps1`, reflashed T41.

**Verification:** `[VER] IRIS-EYES firmware=S101 built=Jun 7 2026` confirmed in journal.

**Changes:**
- **`src/config.h`** — `FIRMWARE_VERSION` `"S100c"` → `"S101"`.

---

## S104 — Sleep-Resume Fix + Mouth Brightness Fix (2026-06-07)

**Status:** DEPLOYED+VERIFIED

**Goals:**
1. Fix IRIS failing to re-enter sleep after wakeword during scheduled sleep window (9pm–7:30am).
2. Fix TFT mouth display appearing blank/dark during sleep mode.
3. Verify pending HANDOFF items (iris_web.js EYE:6 fix, RD-003 duplicate sleep log).

---

### Bug 1 — Sleep resume not re-engaged after wakeword during sleep

**Root cause:** `in_sleep_window()` was never called after `_play_wake_quip()` in the wakeword-during-sleep branch of `assistant.py`. `_do_wake()` fired, quip played, IRIS greeted the user — but then fell through to `show_idle_for_mode(leds); continue` without checking whether it was still inside the sleep window. IRIS remained awake for the rest of the night until cron `iris_wake.py` fired at 7:30am. The `in_sleep_window()` call that exists at line 997 (end of LLM interaction path) was not present in this branch.

**Fix (`pi4/assistant.py`):** Added `if in_sleep_window(): _do_sleep(teensy, leds)` immediately after `_play_wake_quip()` in the wakeword-during-sleep branch.

---

### Bug 2 — TFT mouth blank/dark during sleep

**Root cause:** `MOUTH_INTENSITY_SLEEP = 1` in `pi4/core/config.py`. The firmware `mouthSetSleepIntensity()` sets backlight to `BL_MAP[5] = 16/255 ≈ 6%` (dim but visible, ZZZ animation runs). Python `_do_sleep()` then immediately sends `MOUTH:INTENSITY:1`, overriding firmware to `BL_MAP[1] = 2/255 ≈ 0.8%` — effectively invisible. ZZZ animation was running correctly in firmware; Python was suppressing the backlight to near-off.

Secondary effect on wake: `mouthRestoreIntensity()` in firmware uses `_currentBLLevel` (which was set to 1). The mouth briefly appeared dark after EYES:WAKE before `MOUTH_INTENSITY_AWAKE=8` arrived from Python. Raising `MOUTH_INTENSITY_SLEEP` to 5 also fixes this — `_currentBLLevel=5` is the restore target on wake.

**Fix (`pi4/core/config.py`):** `MOUTH_INTENSITY_SLEEP = 1` → `5`. Comment updated: `level 5 = BL_MAP[5] = 16/255 ≈ 6% — dim but visible; was 1 (≈0.8%, appeared blank)`.

---

### HANDOFF verification

- **`pi4/iris_web.js` EYE:6 Striking Blue fix** — HANDOFF said REPO-ONLY (3 locations). Confirmed ALREADY DEPLOYED: Pi4 md5 = repo md5 = `1d9700784ad65a10a068bc381cf29656`. S92 commit `72373d5` had already made the fix. HANDOFF entry was stale.

- **RD-003 duplicate sleep log** — Confirmed NOT a duplicate. `/home/pi/iris_sleep.log` does not exist. Only `/home/pi/logs/iris_sleep.log` exists (written by `iris_sleep.py`). False alarm — HANDOFF entry closed.

---

**Pi4 deploy — md5 verified (RAM = SD):**
- `/home/pi/assistant.py` — `0220719693fe3d6a6f52b0acfd46a4fa`
- `/home/pi/core/config.py` — `bfd247cc880cf2a7ad3fda790357a170`

**Service:** Restarted. POST all PASS (L0: serial/mic; L1: GandalfAI/Kokoro/Whisper/Piper/OWW/Ollama-models; L2: mouth cycle). root-ro remounted ro. Backup files at `/home/pi/assistant.py.s104.bak` and `/home/pi/core/config.py.s104.bak`.

**Rollback:**
```bash
sudo cp /home/pi/assistant.py.s104.bak /home/pi/assistant.py
sudo cp /home/pi/core/config.py.s104.bak /home/pi/core/config.py
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
sudo cp /home/pi/core/config.py /media/root-ro/home/pi/core/config.py
sudo chown pi:pi /media/root-ro/home/pi/assistant.py /media/root-ro/home/pi/core/config.py
sudo chmod 644 /media/root-ro/home/pi/assistant.py /media/root-ro/home/pi/core/config.py
sync && sudo mount -o remount,ro /media/root-ro
sudo systemctl restart assistant
```

---

## S105 — Bench Audit: JSONL Fallback + Emotion/Tier/Engine in JSONL (2026-06-07)

**Status:** DEPLOYED+VERIFIED

**Goal:** Investigate all benchmarking processes and the empty Bench tab in the control panel. Identify why logs were absent, determine whether anything had moved to GandalfAI, fix persistent data loss, and add missing fields to the JSONL record.

**Root cause — empty Bench tab:** Pi4 runs an overlay filesystem (read-only SD + RAM tmpfs). journald has no `/var/log/journal` directory and falls back to volatile (RAM) storage. On every reboot or service restart with no new LLM interactions, the journal has 0 [BENCH] lines. After S103/S104 service restarts the bench tab was empty — not a code bug, a data availability problem.

**Root cause — JSONL not read by control panel:** `/api/bench` used only journalctl. The JSONL at `/home/pi/logs/iris_bench.jsonl` existed as a persistent record but was never read by the control panel. 4 records from 2026-06-06 were in RAM (would be lost on next reboot).

**Root cause — SD JSONL was 0 bytes:** `/media/root-ro/home/pi/logs/iris_bench.jsonl` was created 2026-05-30 but never populated. Persisted manually this session. md5=`14269ff28e0878ec826e2aa7fc316180`.

**Audit scope:** Full three-tier architecture documented in `docs/bench_audit_S105.md`:
- Layer 1: Pi4 control panel Bench tab (`/api/bench` journalctl-based, volatile)
- Layer 2: Pi4 JSONL persistent log (`iris_bench.jsonl`, previously dead data)
- Layer 3: Local Workbench tool (`tools/workbench/`) — connects to GandalfAI Ollama pre-flight only; GandalfAI runs no benchmarking infrastructure.

**Changes:**

- **`pi4/iris_web.py`** — Added JSONL fallback to `/api/bench`: if journalctl returns 0 cycles, reads `/home/pi/logs/iris_bench.jsonl` and translates each record into the cycle dict format the frontend expects. Fields mapped: dur_rec, dur_stt, transcript, tier, num_predict, dur_ttfc, dur_llm, dur_tts, engine, dur_total, emotion. `_from_jsonl: True` flag set on each cycle. DEPLOYED+VERIFIED. md5 RAM=SD=`856def24589ecae2e405f610db42958a`.

- **`pi4/assistant.py`** — Four changes to capture missing JSONL fields:
  1. `_bench_write()` signature: added `emotion=None` parameter; body writes `record["emotion"] = emotion` when not None.
  2. At `llm_start` BENCH block: `_bench_stages["tier"] = _tier` and `_bench_stages["num_predict"] = _num_predict` stored so they flow into JSONL `stages` dict.
  3. At `tts_done` BENCH block: `_bench_stages["engine"] = _tts_eng` stored.
  4. Main LLM path `_bench_write()` call: now passes `emotion=_current_emotion`.
  DEPLOYED+VERIFIED. md5 RAM=SD=`5db3b7f77ab3892ea8ec42967f168d80`.

- **`pi4/iris_bench_report.py`** — Fixed CLI comment: `journalctl -u iris-assistant.service` → `journalctl -u assistant` (wrong service name, returned nothing). REPO-ONLY.

- **`docs/bench_audit_S105.md`** — NEW. Full audit of all three benchmark layers, gaps G1–G7, JSONL live state (4 sample records), workbench phase 2 results (12/17 passing), and architecture recommendations. REPO-ONLY.

**Verification:** `curl http://localhost:5000/api/bench` returns 4 historical cycles from JSONL with `_from_jsonl=True`. Both `iris-web` and `assistant` services active post-restart.

**Rollback:**
```bash
git checkout -- pi4/iris_web.py pi4/assistant.py pi4/iris_bench_report.py
# sftp_write to Pi4, persist to SD, restart iris-web + assistant
```

---

## S106 — Latency Bench: AI Analysis + Generate Handoff (2026-06-07)

**Status:** REPO-ONLY (workbench JS/HTML/CSS — runs locally on SuperMaster, no Pi4 deploy needed)

**Goal:** Add the same AI-powered analysis and handoff-generation features from the Personality Harness tab to the Latency Bench tab.

**Changes:**

- **`tools/workbench/index.html`** — Added `lat-analysis-spinner`, `lat-analysis-panel` (inside `lat-results-scroll`), and `lat-result-actions` div with "Generate Handoff" + "Run AI Analysis" buttons to the Latency Bench `panel-right`. Mirrors the Personality Harness tab structure exactly.

- **`tools/workbench/workbench.js`** — Added 5 new functions in the latency bench section:
  - `callAnthropicLatencyAnalysis(latResults)` — sends per-case p50/p90/range + overall stats to Claude. Prompt asks for: per-case tier classification (FAST/NORMAL/SLOW/OUTLIER), 2–4 bottleneck identifications (response length variance, tokenization, cache, etc.), 3–5 prioritized optimization actions (ollama config, modelfile NUM_PREDICT/NUM_CTX, prompt design, hardware), and 4–6 new benchmark inputs targeting the slowest latency paths. Returns structured JSON.
  - `renderLatencyAnalysisPanel(result)` — renders case findings table, bottleneck cards (with HIGH/MEDIUM/LOW impact badges), optimization cards (with target tag + priority badge + expected improvement + trade-off), and new bench cases table with "Save Selected to Fixture" download.
  - `saveLatencyBenchCases()` — merges selected new cases into fixture JSON and triggers browser download (same pattern as `saveUpdatedFixture` on harness tab).
  - `runLatencyAnalysis()` — orchestrates the analysis button flow (spinner, error handling, cleanup), matching `runAnalysis()` on the harness tab.
  - `generateLatencyHandoff()` — builds a latency-focused handoff text (overall p50/p90/p99, range, per-case breakdown with p50/p90/range/n, model info, likely files) and opens the shared handoff modal.

- **`tools/workbench/workbench.css`** — Added styles: `#lat-result-actions` (mirrors `#result-actions`), `#lat-analysis-spinner` (mirrors `#analysis-spinner`), `.lat-opt-card`, `.lat-opt-header`, `.lat-opt-action`, `.lat-opt-meta`, `.lat-opt-tradeoff`.

- **`.claude/launch.json`** — Added `autoPort: true` so the preview server picks a free port when 8080 is occupied by the live workbench instance.

**Rollback:**
```bash
git checkout -- tools/workbench/index.html tools/workbench/workbench.js tools/workbench/workbench.css .claude/launch.json
```

---

## S107 — APA102 Sleep LED brightness fix (2026-06-08)

**Status:** DEPLOYED+VERIFIED (Pi4 RAM=SD, assistant restarted, sleep LEDs active)

**Problem:** ReSpeaker APA102 LEDs during sleep (indigo pulsing) were blinding at night. WebUI changes to peak brightness did nothing because (1) led.py had module-level imports fixed at process startup — WebUI saves required a service restart the user did not perform; (2) LED_SLEEP_BRIGHT = 0xFF set APA102 global brightness to 31/31 max, making even low color values produce visible output.

**Changes:**

- **`pi4/core/config.py`** — Lowered sleep LED defaults: LED_SLEEP_PEAK=8 (was 26), LED_SLEEP_FLOOR=1 (was 3), LED_SLEEP_BRIGHT=0xE3 (was 0xFF; 3/31 approx 10% global brightness). Added LED_SLEEP_BRIGHT to _OVERRIDABLE and _TYPE_COERCE (range 225-255).

- **`pi4/hardware/led.py`** — Removed module-level LED_SLEEP_* imports. Rewrote show_sleep() to read iris_config.json directly at the start of each 8-second animation cycle via an inner _load() function. WebUI peak/floor/period/bright changes now take effect on the next cycle with no service restart needed.

- **`pi4/iris_web.html`** — Updated APA102 Sleep LEDs hint: removed "restart required", updated defaults note to floor=1, peak=8.

**md5 (RAM=SD):** config.py f6f55fb58bc42532e673b334b8a04c05 / led.py b4a78a069bbd331ae4f73c829e86e256 / iris_web.html b3ef97e941de491571f099df5557d140

**Rollback:** git checkout -- pi4/core/config.py pi4/hardware/led.py pi4/iris_web.html then redeploy and restart assistant.

---

## S108 — TTS truncation fix, vision 400 error, boilerplate cleanup (2026-06-08)

**Status:** DEPLOYED+VERIFIED (Pi4 RAM=SD, assistant restarted clean)

**Problems fixed:**

1. **TTS truncation:** Long responses (stories, lists) were cut off after ~5-6 sentences. Root cause: `TTS_MAX_CHARS=900` applied by `_truncate_for_tts()` in `tts.py`. Kokoro generates 21s of audio per 900 chars in ~1.3s, so there is no performance reason to keep the cap this low. Dog story (2500+ chars) was being truncated to ~35% of its content.

2. **Vision 400 error:** `VISION_MODEL="iris"` → `qwen2.5:32b` (text-only). Sending `images` payload to a text-only model causes HTTP 400. Error was caught generically in `assistant.py`, giving IRIS the response "I had trouble processing the image." New fix: `ask_vision()` now catches the 400 specifically and returns a clear "vision not available" message without raising, so IRIS speaks it cleanly.

3. **Boilerplate AI speak:** `clean_llm_reply()` was missing several common boilerplate patterns. Added: opener strips for "Absolutely,", "It sounds like you...", "As an AI...", "I'm an AI..."; trailing sentence strips for "Feel free to ask", "Let me know if", "If you have any questions", "I hope you enjoyed", "Is there anything else"; `---` separator strip (clears trailing meta-comment appended after separator); numbered list artifact cleanup ("1. : Have..." → "Have...").

**Changes:**

- **`pi4/core/config.py`** — `TTS_MAX_CHARS=2500` (was 900). Comment updated.

- **`pi4/services/llm.py`** — `clean_llm_reply()`: added 4 opener patterns (absolutely, it sounds like you, as an AI, I'm an AI), 5 trailer patterns (feel free to ask, let me know if, if you have any questions, I hope you enjoyed, is there anything else), `---` separator strip with re.DOTALL, numbered list artifact cleanup regex.

- **`pi4/services/vision.py`** — `ask_vision()`: wraps `r.raise_for_status()` in try/except for HTTPError; catches 400 and returns "My vision system isn't available right now. The current AI model doesn't support images." instead of raising.

**md5 (RAM=SD):** config.py 9d75f68d02d2a6f1cb2754d7df342b05 / llm.py 01b72e4c981c545bfe0cac016f8936a5 / vision.py 60a66d3a94310f90757d46ca1cbe5dc7

**Rollback:** git checkout -- pi4/core/config.py pi4/services/llm.py pi4/services/vision.py then redeploy and restart assistant.

---

## S109 — Vision Restore (Ollama Downgrade + VISION_MODEL Fix)

**Date:** 2026-06-08
**Status:** DEPLOYED+VERIFIED

**Root cause:** A prior Claude Code session (S103) auto-upgraded GandalfAI Ollama from a working version to 0.30.6. Ollama 0.30.x switched to a new llama.cpp engine that requires the `clip.vision.n_wa_pattern` key in the GGUF vision projector metadata. The `qwen2.5vl:32b-q4_K_M` GGUF (blob sha256-043a363c) does not contain this key. Result: `/api/generate` with any image payload returned HTTP 500 "Failed to load CLIP model". Additionally, `VISION_MODEL = "iris"` in `pi4/core/config.py` pointed at the `iris` model (FROM qwen2.5:32b, text-only), causing HTTP 400 on image payloads even before the Ollama version issue.

**Fix:**

1. **GandalfAI Ollama downgraded 0.30.6 → 0.24.0** — 0.24.0 uses the old GGUF engine that does not check for `clip.vision.n_wa_pattern`. Vision loads correctly.
   - Install command: `$env:OLLAMA_VERSION="0.24.0"; irm https://ollama.com/install.ps1 | iex`
   - Verified: `ollama version is 0.24.0`
   - Windows Firewall outbound block re-applied for `ollama app.exe` (path: `C:\Users\gandalf\AppData\Local\Programs\Ollama\ollama app.exe`) to prevent auto-update restoring a broken version.

2. **`pi4/core/config.py`** — `VISION_MODEL = "qwen2.5vl:32b-q4_K_M"` (was `"iris"`). Deployed to Pi4 RAM + SD. md5=`2978ca89d5d9e6172a0153b1802f179c` (both paths match).

**Verified:** HTTP 200 from `POST /api/generate` with base64 PNG image + prompt to GandalfAI:11434 using qwen2.5vl:32b-q4_K_M. Pi4 assistant.service POST L1 PASS. assistant.service active (running).

**Note on Ollama version history:**
- 0.24.0: old engine, no `clip.vision.n_wa_pattern` check — **WORKING**
- 0.23.4: old engine, but `qwen25vl.(*ImageProcessor).SmartResize` panics on images smaller than 28x28 — avoid
- 0.30.0–0.30.7: new llama.cpp engine requiring `clip.vision.n_wa_pattern` — BROKEN for qwen2.5vl:32b-q4_K_M
- Do not upgrade Ollama until qwen2.5vl GGUF includes the required key or a compatible model build is available.

**Rollback:** Reinstall Ollama 0.24.0 (same command above). Re-apply firewall block. Redeploy config.py with `VISION_MODEL = "qwen2.5vl:32b-q4_K_M"`. Restart assistant.

---

## S110 — RPQR + Pipeline Latency Overhaul (2026-06-09)

**Status:** DEPLOYED+VERIFIED

**Goal:** Fix RPQR responses being blocked by GandalfAI gate; add 4 new RPQR triggers; replace wakeword beep with snarky time-of-day quips on every activation; tighten silence detection.

**Root cause found:** `ensure_gandalf_up()` was called *before* `_play_wake_quip()` in the sleep-wakeword path. Since quips are pre-cached PCM, Ollama is not needed — but the gate blocked them for up to 120s (WOL_BOOT_TIMEOUT) whenever GandalfAI was asleep. If Gandalf never came up, the quip never played.

**Changes:**

1. **`pi4/assistant.py`** — DEPLOYED. md5=`fa5bf5b065951bdbf34ab27b3af0ea4e` (RAM=SD).
   - Sleep-path reordered: `_play_wake_quip()` now fires immediately on wakeword-during-sleep. `ensure_gandalf_up()` removed from this branch entirely (quip→re-sleep path never needs Gandalf).
   - `_WAKE_QUIPS` expanded from 2 lines/band to 4–5 lines/band (26 unique lines). Beep replaced by time-of-day quip on every wakeword activation.
   - New RPQR triggers added — all pre-cached at startup, fire before `ensure_gandalf_up()`:
     - Double-tap: wakeword within 30s of previous (`_DOUBLE_TAP_QUIPS`: 3 lines)
     - Post-speech: wakeword within 5s of IRIS finishing a response (`_POST_SPEECH_QUIPS`: 3 lines)
     - Top-of-hour: wakeword within ±2 min of XX:00, 10-min cooldown (13 hour variants)
     - First-of-day: first wakeword of calendar day ("Morning." before 09:00, "Finally." after)
   - `_rpqr_state` dict tracks `t_last_wake`, `t_last_spoke`, `last_interaction_date`, `t_last_top_of_hour`.
   - `t_last_spoke` updated after LLM main response and all follow-up responses.
   - Stale `_quip_state` dict removed.

2. **`pi4/iris_config.json`** — DEPLOYED. md5=`9dbd091fff10409f1e6d544d9e26b603` (RAM=SD).
   - `SILENCE_SECS=1.2` (was 1.5) — saves ~0.3s per turn.

3. **`docs/prompt_pipeline_latency_audit.md`** — NEW. Canned latency audit prompt for future sessions. REPO-ONLY.

**Verified:** All 26 QUIP + 13 RPQR lines cached at startup (no misses). LLM warmup completed. Service active. SILENCE_SECS=1.2 confirmed in [CFG] startup log.

**Rollback:** `git checkout HEAD~1 -- pi4/assistant.py && scp ... && sudo systemctl restart assistant`. Revert iris_config.json SILENCE_SECS to 1.5.

---

## S112 — VL Base Swap + AMUSED Calibration (2026-06-09)

**Status:** DEPLOYED+VERIFIED

**Goal:** Wire qwen2.5vl:32b-q4_K_M into both iris and iris-kids modelfiles (enabling native vision support), and fix ANGRY overtrigger on insult inputs by adding AMUSED few-shot calibration to iris modelfile. Both models rebuilt on GandalfAI.

**Background:** S111 perf audit confirmed iris/iris-kids had always run qwen2.5:32b (text-only). qwen2.5vl:32b-q4_K_M was already on GandalfAI (21GB, pulled S109) but never wired into the modelfiles. Harness showed 11/20 pass (55%) — 6 failures were ANGRY where AMUSED expected on insult inputs. AMUSED calibration and VL swap done in same pass.

**Changes:**

1. **`ollama/iris_modelfile.txt`** — DEPLOYED+VERIFIED.
   - `FROM qwen2.5:32b` → `FROM qwen2.5vl:32b-q4_K_M`. Vision now native (no model-swap penalty per query).
   - Added `# EMOTION CALIBRATION — INSULT INPUTS` block after joke few-shots. Six examples with [EMOTION:AMUSED] on direct insults ("You're dumb." / "You suck." / "I hate you." x2 / "You're useless.") and [EMOTION:NEUTRAL] on "Shut up."
   - Smoke test: `curl` → "You're dumb." → `[EMOTION:AMUSED] Groundbreaking observation. Did you need something.` PASS.

2. **`ollama/iris-kids_modelfile.txt`** — DEPLOYED+VERIFIED.
   - `FROM qwen2.5:32b` → `FROM qwen2.5vl:32b-q4_K_M`. No other changes (kids model already had AMUSED on insults).
   - Smoke test: "tell me a joke" → `[EMOTION:HAPPY]` + kid-appropriate joke + turn-back question. PASS.

**Deploy:** Both modelfiles SFTP'd to GandalfAI `C:\IRIS\IRIS-Robot-Face\ollama\`, then `ollama create iris` / `ollama create iris-kids`. `ollama list` confirms both 21 GB, fresh timestamps. VRAM: ~23GB loaded (RTX 3090 = 24GB, ~1GB headroom estimated).

**Rollback:**
```
git checkout HEAD~1 -- ollama/iris_modelfile.txt ollama/iris-kids_modelfile.txt
# SFTP both files to GandalfAI, then:
ollama create iris -f C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt
ollama create iris-kids -f C:\IRIS\IRIS-Robot-Face\ollama\iris-kids_modelfile.txt
```

---

## S116 — Streaming LLM → Sentence-Boundary TTS (Overlapped Pipeline) (2026-06-09)

**Status:** DEPLOYED + latency-VERIFIED. Behavioral hardware checks (speaker output, emotion-on-face, spoken STOP, Piper fallback) require a human in front of IRIS — handed off.

**Goal:** First audio plays on the first complete sentence of the LLM response instead of after the full response. Resolves the long-standing S98 proactive flag.

**Root finding:** The pipeline already *streamed* from Ollama (`stream_ollama`), but only used the stream to extract the emotion tag early. It accumulated every sentence chunk, joined them, then made **one** blocking `synthesize(reply)` call on the full text — so TTS still waited for the entire response. The sentence-boundary infrastructure (`stream_ollama`, `_split_sentences`, per-chunk `clean_llm_reply`, early emotion extraction) was all present and just needed wiring to per-sentence TTS dispatch.

**What changed:**

1. **`pi4/hardware/audio_io.py`** — DEPLOYED. md5=`ada50cfc3ab6b8ae52efdc7c7f9aab9c` RAM=SD.
   - New `play_pcm_stream(pcm_queue, pa, teensy, emotion, restore_mouth_idx)`: gapless back-to-back playback of PCM blobs pulled from a `queue.Queue` (`None` sentinel = end). One `EYES:SPEAKING` setup, one continuous mouth animation, one interrupt listener (single bleed baseline) span the whole utterance. Sliced blocking writes with per-slice stop/interrupt/button checks; drains queue on interrupt. Returns `interrupted` bool.
   - `play_pcm` / `play_pcm_speaking` left untouched — all other call sites (quips, RPQR, reflex/utility/command/vision, follow-up) unchanged.

2. **`pi4/assistant.py`** — DEPLOYED. md5=`fe79c67bd5dfea50f5559e0304d37c35` RAM=SD. (Local file normalized CRLF→LF to match deployed artifact + repo convention.)
   - Main LLM block rewritten: producer iterates `stream_ollama()`, emits emotion on first chunk (unchanged), synthesizes each sentence as it arrives, and starts the `play_pcm_stream` background player on the first PCM blob — `play_start_ms` now lands on the first sentence, not the full response.
   - STOP checked per sentence dispatch (`if _stop_playback.is_set(): break`) in addition to per playback slice.
   - Piper fallback preserved (handled inside `synthesize`); a both-engines-fail on a later sentence is logged and skipped rather than killing the turn.
   - `classify_response_length` (SHORT/MEDIUM/LONG/MAX) and the follow-up loop (blocking `ask_ollama`) unchanged.

**Deploy:** Both files SFTP'd to `/home/pi/`, `py_compile` OK on Pi4, persisted to `/media/root-ro`, md5 RAM=SD verified, `assistant.service` restarted, `[INFO] Ready.` confirmed, no ImportError/traceback.

**Latency (S116 harness, real `stream_ollama` + real Kokoro, n=10 long multi-sentence prompts, LLM-start→first-audio):**
- NEW (streaming): **p50 2086 ms, p90 4257 ms** (min 1505, max 5138)
- OLD (blocking, modeled): p50 23261 ms, p90 25312 ms
- First-audio savings p50 ≈ **21.3 s** on these long replies. Magnitude scales with reply length; upstream wake/record/STT/router stages are unchanged by S116. Result file: `/home/pi/logs/lat_bench_20260609_160520_post-streaming-pipeline.json`.
- Note: not directly comparable to the post-h2-h3-baseline (p50 1623 ms full wake→play) — that baseline mixed shorter replies; this harness forced LONG/MAX prompts and measures only the LLM→first-audio segment (the only segment S116 touches). The streaming path also avoids feeding Kokoro a single multi-minute input on long replies.

**Rollback:**
```
git checkout -- pi4/assistant.py pi4/hardware/audio_io.py
# redeploy both to /home/pi/ + /media/root-ro, sudo systemctl restart assistant
```

---

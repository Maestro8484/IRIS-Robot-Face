# IRIS Codebase Review — Master Summary

**Date:** 2026-05-17
**Reviewer:** Opus 4.7
**Scope:** Six-task read-only audit of IRIS Pi4 pipeline, config system, emotion stack, intent router, failure modes, doc drift.
**Constraint:** Read-only — no source modifications, no deploys, no SSH writes to Pi4 or GandalfAI.

Source findings files:
- `review/findings_session_1_pipeline.md`
- `review/findings_session_2_config.md`
- `review/findings_session_3_emotions.md`
- `review/findings_session_4_router.md`
- `review/findings_session_5_failures.md`
- `review/findings_session_6_drift.md`

---

## 1. Severity Totals

Counts derived from the explicit `Severity:` markers in each findings file. Failure scenarios in Task 5 use the same scale.

| Source | HIGH | MED | LOW | Info / N/A |
|---|---|---|---|---|
| Task 1 — Pipeline | 2 | 5 | 4 | 1 |
| Task 2 — Config & Persistence | 1 | 3 | 4 | 0 |
| Task 3 — Emotions | 0 | 0 | 3 | 1 |
| Task 4 — Intent Router | 0 | 1 | 8 | 1 (fail-open OK) |
| Task 5 — Failure Scenarios | 2 | 5 | 3 | 0 |
| Task 6 — Doc Drift | 0 | 2 | 4 | 2 |
| **Total** | **5** | **16** | **26** | **5** |

Task 5's HIGH/MED counts include scenarios where the system *is* the failure — these are operational risks more than discrete code defects. Some Task 5 entries overlap code-level findings from Tasks 1-4 (notably the `/api/persist_config` chown bug, which appears in both Task 2 and Task 5 scenario i).

---

## 2. Top 5 Highest-Priority Findings

Ranked by severity × blast radius. Blast radius = how many users/sessions/subsystems are affected and how silently the failure occurs. Each entry maps to a session, file, lines, risk, and minimal fix direction.

### #1 — `/api/persist_config` missing `chown pi:pi` after `sudo cp` (Task 2, Section 2 / Task 5 scenario i)

- **Source:** Session 2, finding under Section 2 "iris_web.py Write Routes — chown Audit"
- **File:** `pi4/iris_web.py:281-285`
- **Severity:** HIGH
- **Risk:** Reproduces the documented S22B failure mode (IRIS_ARCH.md "Operational Notes — Pi4 - api_persist_config Ownership Bug"). The `sudo cp` writes a root-owned copy of `iris_config.json` to the SD layer. On reboot, the SD layer becomes the live config — root-owned, which silently breaks all subsequent web-UI saves. The original April 16-18 cascade was caused by exactly this pattern.
- **Fix direction:** Extend the sudo bash command on lines 281-285 to include `chown pi:pi {SD_CONFIG}` and `chmod 644 {SD_CONFIG}` between the `cp` and the read-only remount. Add `sync` before remount. One-line change to the bash command string; no test infrastructure changes needed because the existing `_sd_synced()` md5 check already validates the copy.

### #2 — `_playback_interrupt_listener` thread leaks `_stop_playback.set()` across utterances (Task 1, Section 2 / Task 5 scenario c)

- **Source:** Session 1, exception-corruption section
- **File:** `pi4/hardware/audio_io.py:165-217` (specifically `_verify_stt` at lines 192-204)
- **Severity:** HIGH
- **Risk:** The interrupt listener spawns a background Whisper STT call to verify whether mid-playback voice contains a STOP phrase. If Whisper is slow or hangs, the STT thread can complete *after* the playback it was monitoring has already finished — and then call `_stop_playback.set()`. The module-level `_stop_playback` event is now set with no owner. The next playback starts with `_stop_playback.clear()` at `play_pcm` entry (line 220), but any STT thread completing between that clear and the next playback's interrupt listener start will kill the new playback instantly with no recoverable cause.
- **Fix direction:** Pass a per-playback session token (e.g., a `threading.Event` owned by the current `play_pcm` invocation) and gate the `_stop_playback.set()` call on that token still being valid. Alternative: have `_verify_stt` check `stop_event.is_set()` before mutating module-level state.

### #3 — `/tmp/iris_sleep_mode` has four unsynchronized writers (Task 1, Section 3b + Section 5)

- **Source:** Session 1, race-conditions Section 3b, also documented as Section 5 unlocked state mutation
- **Files:** `pi4/assistant.py:212-244`, `pi4/iris_sleep.py:23`, `pi4/iris_wake.py:28`, `pi4/iris_web.py:96, 104`
- **Severity:** HIGH
- **Risk:** Four code paths write or delete `/tmp/iris_sleep_mode`: assistant.py's `_do_sleep`/`_do_wake`, cron scripts that touch the file directly *and* send UDP commands, and web routes that do the same double-write. No lock. `state.eyes_sleeping` is mutated in 5+ places unlocked. Concurrent web-sleep + main-loop-wake-after-followup can race. The non-determinism is invisible until a state desync produces visible bad behavior (eyes awake while flag says sleeping, etc.).
- **Fix direction:** Restrict flag mutation to `_do_sleep`/`_do_wake` in `assistant.py`. Cron scripts and web routes should only send UDP commands and let the CMD listener invoke the canonical functions. Add `state._lock` acquisition around every `state.eyes_sleeping` mutation. This is a multi-file refactor but each file change is small (3-5 lines).

### #4 — Both TTS engines down produces up to 90s of silence (Task 5 scenario b)

- **Source:** Session 5, scenario b
- **Files:** `pi4/services/tts.py:151-180`, `pi4/assistant.py:558-562`
- **Severity:** HIGH
- **Risk:** When Kokoro (port 8004) is unreachable, `synthesize` attempts Piper (port 10200) as fallback. If both are unreachable, `_synthesize_kokoro` may wait up to 30s (its timeout) then `_synthesize_piper` may wait up to 60s — total ~90s of silence with LED animation, then a 0.6s red flash, then return to idle. The user's reply is lost (history corrupted per Task 1 Finding 1.3), the user receives no spoken explanation, and the failure mode is indistinguishable from a system hang.
- **Fix direction:** Cache a "TTS engine X is down" state with a 60s expiry to fast-fail subsequent attempts. If both engines fail, play a distinct error tone (separate from the WoL beep and general `play_beep`) plus a unique LED sequence to signal "TTS unavailable". Log the failure to `iris_intent.log` so the web UI Logs tab surfaces it. This bounds the worst-case silence at 1-2s instead of 90s.

### #5 — "What year" / "what month" routes to UTILITY/DATE for any phrase (Task 4 Finding 4.5)

- **Source:** Session 4, false-positive analysis
- **File:** `pi4/core/intent_router.py:113`
- **Severity:** MED, but highest blast radius among MED findings — every historical question is wrong
- **Risk:** `_DATE_RE` matches "what year", "what month", "what date" anywhere in the utterance. "What year did the Civil War end" → IRIS responds "Today is Saturday, May 17, 2026." The LLM is never reached. The user receives a non-sequitur answer with no indication the router intercepted. This silently corrupts every historical date question and is a permanent loss of utility (versus the other findings which are situational).
- **Fix direction:** Tighten `_DATE_RE` to require terminal-like context: anchor to short utterances or require trailing words like "is it", "today", "now". Example: `r"\bwhat\s+(year|month|date|day)\b(?:\s+(is|are))?(?:\s+(it|today|now))?\s*\??$"`. The regex change is local; no other code touched.

---

## 3. Recommended Implementation Sequence

Group fixes by file to minimize deploy cycles. Pi4 deploys are gated and require explicit user authorization per CLAUDE.md, so each contiguous edit-batch should be one deploy.

### Batch 1 — `pi4/iris_web.py` (deploy + persist + restart iris-web)

Single file, single Pi4 deploy. Addresses Top 5 #1 plus a Task 2 LOW finding.

1. **#1 chown fix** — Extend `/api/persist_config` bash command to include `chown pi:pi`, `chmod 644`, `sync` between `cp` and `remount,ro`. Apply same `sync` to ALSA state block.
2. **Task 1 LOW (iris_web TTS conflict)** — Optional: add `fcntl.flock` around `write_cfg` and `_speak_worker` to prevent the documented concurrent-audio scenario.

**Risk to this batch:** Lowest of all batches. Pure additive bash command extension. `_sd_synced()` md5 check already verifies the persist worked.
**Verification:** Trigger Persist to SD from web UI; verify the SD-layer file is `pi:pi` owned and md5 matches.

### Batch 2 — `pi4/hardware/audio_io.py` (deploy + persist + restart assistant)

Single file, single Pi4 deploy. Addresses Top 5 #2 (HIGH).

1. **#2 interrupt listener race** — Add a per-playback session token (threading.Event) to `_playback_interrupt_listener`. Have `_verify_stt` check the token before touching `_stop_playback`.

**Risk:** Medium. Touching the interrupt path can break stop-phrase detection. Test with: (a) wakeword → long reply → say "stop" mid-playback (should still interrupt); (b) wakeword → multi-turn conversation (should not have cross-utterance stops).
**Verification:** Live test with deliberate Whisper slowness (slow GandalfAI). Audit `_stop_playback.is_set()` state between consecutive playbacks.

### Batch 3 — `pi4/core/intent_router.py` (deploy + persist + restart assistant)

Single file, multiple LOW + one MED. Address router-precision issues together since they touch the same regex set.

1. **Top 5 #5** — Tighten `_DATE_RE`, `_TIME_RE` to anchored forms.
2. **Task 4 Finding 4.6** — Anchor `_VOL_UP_RE`, `_VOL_DN_RE` etc. to imperative forms.
3. **Task 4 Finding 4.7** — Anchor `_KIDS_ON_RE`, `_KIDS_OFF_RE` to imperative forms.
4. **Task 4 Finding 4.10** — Branch `_random_number_reply` on which word matched (`digit` → 0-9).
5. **Task 4 Finding 4.9** — Populate `payload={"result": ...}` for RANDOM_NUMBER so intent log captures the value.
6. **Task 4 Finding 4.1** — Move "enough" from `_AMBIGUOUS_STOP_EXACT` to `_STOP_EXACT` *or* update intent-router.md (doc-only side).

**Risk:** Medium. Regex changes can introduce new false negatives. Run the existing 17 test cases mentioned in intent-router.md "Testing Loop 1" before deploy.
**Verification:** Live test the original failing utterances ("what year did the Civil War end", "softer fabrics are easier on skin", etc.) — confirm they now route to LLM. Also test that legitimate commands still trigger correctly.

### Batch 4 — `pi4/assistant.py` + `pi4/state/state_manager.py` + `pi4/iris_sleep.py` + `pi4/iris_wake.py` + `pi4/iris_web.py` (one combined deploy)

This is Top 5 #3 — sleep-flag multi-writer fix. It touches 5 files but the changes are coordinated.

1. **#3 sleep flag ownership** — In `assistant.py`, make `_do_sleep`/`_do_wake` the sole writers of both `/tmp/iris_sleep_mode` and `state.eyes_sleeping`. Acquire `state._lock` around mutations.
2. In `iris_sleep.py` / `iris_wake.py` — Remove the direct `open('/tmp/iris_sleep_mode', 'w')` / `os.remove(...)` calls. Keep only the UDP sends. CMD listener will write the flag.
3. In `iris_web.py` `/api/sleep` and `/api/wake` — Remove the direct flag writes. Keep only the UDP sends.
4. Verify CMD listener at `assistant.py:130-150` correctly invokes `_do_sleep`/`_do_wake` for `EYES:SLEEP`/`EYES:WAKE` commands (it already does for the EYES: variants — confirm).

**Risk:** Medium-high. Five files coordinated. A bug here could leave the sleep flag stuck or out of sync with `state.eyes_sleeping`. Critical to test both cron paths and web paths post-deploy.
**Verification:** Trigger sleep via cron, web, and voice; trigger wake via each; check `state.eyes_sleeping` via web UI status endpoint and `/tmp/iris_sleep_mode` presence after each transition. Test the documented Task 5 scenario h (wake-during-sleep with GandalfAI offline).

### Batch 5 — `pi4/services/tts.py` + `pi4/hardware/audio_io.py` (deploy + persist + restart assistant)

Top 5 #4 — TTS fast-fail and audible-error feedback.

1. **#4 TTS fast-fail** — In `tts.py:151-180`, add module-level state `_kokoro_down_until: float` and `_piper_down_until: float`. On exception, set the timer 60s ahead. On entry, fast-skip to the next engine if its timer hasn't expired.
2. **#4 audible error** — Add `play_tts_error_beep(pa)` in `audio_io.py` — distinct from `play_beep` and `play_wol_beep`. Call it in `assistant.py:560-562` on TTS exception before `continue`.

**Risk:** Medium. Test with deliberately-killed Kokoro container to verify fast-fail behavior. Confirm the new error beep is distinctly different from existing beeps.
**Verification:** `docker stop kokoro` on GandalfAI, trigger a turn, expect <2s timeout + new error tone instead of 30s+ silence. Restart Kokoro, expect next turn to retry Kokoro normally.

### Batch 6 — Documentation refresh (no code, no Pi4 deploy)

Pure docs. Addresses Task 3 + Task 6 LOW findings.

1. **Task 3 Finding 3.1 / Task 6 Finding 6.5** — Add AMUSED row to `README.md` Emotion System table and `IRIS_ARCH.md` Serial Protocol enumeration.
2. **Task 6 Finding 6.2** — Update `IRIS_ARCH.md` "Key Constants" `NUM_PREDICT = 300` (currently shows 150).
3. **Task 6 Finding 6.6** — Update `IRIS_ARCH.md` "iris_config.json on Pi4 (current)" to remove `NUM_PREDICT: 120` (removed S48).
4. **Task 6 Finding 6.1** — Update `IRIS_ARCH.md` "Key Constants" Chatterbox lines with "(rollback only — Kokoro is primary since S38)" comment.
5. **Task 2 Finding 1** — Either add `WAKE_WORD` to `_OVERRIDABLE` OR update `IRIS_CONFIG_MAP.md` to clarify the key requires a code edit.
6. **Task 6 Findings 6.3, 6.4** — Optional: clarify cron 7:30 AM vs `SLEEP_WINDOW_END_HOUR=8` semantic gap; mention S46 WoL beep in IRIS_ARCH.md "GandalfAI - Wake on LAN" section.

**Risk:** None. Docs only.

### Deferred / lower priority

These are correctly flagged but lower urgency:

- **Task 1 Finding (TeensyBridge return-value ignored)** — Add return-value checks in `_do_sleep`/`_do_wake`. Low risk, low impact.
- **Task 1 Finding (LLM stream + TTS broken history pair)** — Pop user turn from history on exception. Fixes the silent conversation-coherence degradation; lower urgency than the Top 5.
- **Task 1 Finding (wakeword reader silent error)** — Set `trigger[0] = "error"` in the bare except. Defensive, low impact.
- **Task 4 LOW findings 4.2, 4.3** — Decide whether to implement `restart`/`reboot` voice command and timer/unit-converter utilities, or update intent-router.md to remove the spec entries that aren't planned. Spec-cleanup task.
- **Task 3 Finding 3.2** — AMUSED LED auto-off vs continuous-breathe asymmetry. Design choice — decide intent rather than fix.
- **Task 3 Finding 3.4** — `applyEmotion` array-index safety. Hypothetical defect, no live trigger.

---

## 4. Implementation Sequence at a Glance

| Order | Batch | Files | Top 5 items | Risk | Deploy target |
|---|---|---|---|---|---|
| 1 | iris_web persist fix | `pi4/iris_web.py` | #1 | Low | Pi4 |
| 2 | playback interrupt race | `pi4/hardware/audio_io.py` | #2 | Med | Pi4 |
| 3 | router precision tightening | `pi4/core/intent_router.py` | #5 + 5 LOWs | Med | Pi4 |
| 4 | sleep-flag ownership | `pi4/assistant.py`, `state/state_manager.py`, `iris_sleep.py`, `iris_wake.py`, `iris_web.py` | #3 | Med-High | Pi4 |
| 5 | TTS fast-fail + audible error | `pi4/services/tts.py`, `pi4/hardware/audio_io.py` | #4 | Med | Pi4 |
| 6 | Documentation refresh | `IRIS_ARCH.md`, `IRIS_CONFIG_MAP.md`, `README.md` | (LOW cleanup) | None | Repo only |

Each batch is one Pi4 deploy cycle (RAM write → SD persist → md5 verify → service restart → log check) per the CLAUDE.md canonical pattern. Batches 1, 4, and 5 require restarting `assistant` (touching `assistant.py` or shared modules). Batches 2 and 3 also require `assistant` restart since they're in the same process. Batch 1 only needs `iris-web` restart.

**Recommended order rationale:** Batch 1 is the lowest-risk highest-impact change (single line of bash, prevents documented S22B recurrence). Batch 6 is docs-only and can be interleaved with any other batch with no deploy cost. Batches 2, 3, 4, 5 are independent and can be reordered based on priority of the failure mode each addresses, but the order shown groups the simpler fixes first.

---

## 5. Observations

**What's working well:**

- Emotion system has the cleanest cross-file consistency (Task 3) — RD-002 executed nearly perfectly. Only doc tables lag.
- Intent router fail-open is correctly implemented (Task 4 Section 3).
- Eye index map is consistent across all three sources (Task 6).
- TeensyBridge serial ownership rule is respected by all paths via UDP CMD_PORT discipline (Task 1 Section 3c).
- Defense-in-depth on unknown emotions: all five layers coerce to NEUTRAL (Task 3 Section 2).

**Recurring pattern in defects:** Partial failure paths. Code handles success cleanly but exception paths leave state (conversation_history, sleep flag, TTS state, mic stream) out of sync with no compensating cleanup. Five of the top issues are this pattern.

**Documentation drift concentration:** IRIS_ARCH.md "Key Constants" is the most stale section — pre-S43 values, pre-S48 iris_config.json contents. IRIS_CONFIG_MAP.md is more current. README.md is current except AMUSED.

**Spec-implementation drift:** intent-router.md describes restart/eye-switch commands and timer/unit-converter utilities that are not implemented. Either decide to implement or update the spec.

**No findings that block normal operation.** The pipeline is functionally sound on the happy path. All HIGH findings are about silent or delayed failures, not crashes.

---

*End master summary. Six findings files + this MASTER complete the review per the original plan. No source files modified.*

# Task 6 — Documentation Drift Check

**Date:** 2026-05-16
**Reviewer:** Opus 4.7
**Scope:** S45-S49 doc updates, Chatterbox→Kokoro references, SNAPSHOT_LATEST.md claims, constants, protected files, eye index map

---

## 1. CHANGELOG S45-S49 vs IRIS_CONFIG_MAP.md / IRIS_ARCH.md

### S45 — Docs-only cleanup

No code changes. Self-referential: S45 *was* a docs cleanup pass that updated both IRIS_ARCH.md and IRIS_CONFIG_MAP.md per CHANGELOG. Sample-checked: IRIS_ARCH.md "Key Constants" section *is* labeled "as of S45". ✅ Match.

### S46 — WoL acknowledgement beep

- **Code change:** `pi4/hardware/audio_io.py` new `play_wol_beep(pa)`; `pi4/assistant.py` calls it inside `ensure_gandalf_up`.
- **IRIS_ARCH.md:** Search for `play_wol_beep` or "WoL beep" — **not present**. The Operational Notes "GandalfAI - Wake on LAN" section (IRIS_ARCH.md "Operational Notes" block) says "WoL triggered from Pi4 via assistant.py before Ollama polling begins" but does not mention the beep.
- **IRIS_CONFIG_MAP.md:** No reference. Beep is not configurable so absence is correct.
- **Drift:** LOW. IRIS_ARCH.md "GandalfAI - Wake on LAN" notes section could mention the beep but the omission is informational not functional.

### S47 — RD-002 AMUSED Emotion

- **Code changes:** `pi4/core/config.py` (VALID_EMOTIONS + MOUTH_MAP), `pi4/hardware/led.py` (amber breathe), `src/main.cpp` (EmotionID + emotionTable + parseEmotion), `pi4/iris_web.html` (button), `ollama/iris-kids_modelfile.txt` (valid emotion list).
- **IRIS_ARCH.md:** Serial Protocol line at IRIS_ARCH.md:568 still reads `EMOTION:NEUTRAL/HAPPY/CURIOUS/ANGRY/SLEEPY/SURPRISED/SAD/CONFUSED` — **AMUSED absent**. Same finding as Task 3 Finding 3.1.
- **IRIS_CONFIG_MAP.md:** No emotion enumeration in this doc. ✅ Not applicable.
- **README.md:** Emotion System table at README.md:121-130 — **AMUSED absent**. Same finding as Task 3.
- **Drift:** LOW (already flagged in Task 3).

### S48 — NUM_PREDICT removal + PT-001 modelfile changes

- **Code/config change:** `NUM_PREDICT: 200` key removed from live Pi4 `iris_config.json`. Modelfile updates on GandalfAI.
- **IRIS_ARCH.md:** Section "Key Constants → iris_config.json on Pi4 (current)" still lists:
  ```json
  { "OWW_THRESHOLD": 0.9, "CHATTERBOX_ENABLED": true, "NUM_PREDICT": 120 }
  ```
  This shows `NUM_PREDICT: 120` (an earlier value than the S48 removal of `NUM_PREDICT: 200`). The doc is stale by two cycles. Also: `NUM_PREDICT` line above the JSON example still reads `NUM_PREDICT = 150 # overridden to 120 by iris_config.json`. Post-S48 there is no override at all — tiered classifier controls num_predict.
- **IRIS_CONFIG_MAP.md:** Stale Keys section flags `NUM_PREDICT` legacy correctly. ✅ Match.
- **Drift:** **MED.** IRIS_ARCH.md "Key Constants" still shows the pre-S48 iris_config.json contents and pre-S48 NUM_PREDICT default. Stale.

### S49 — Web UI rework

- **Code changes:** `pi4/iris_web.py` (renamed `/api/generate` → `/api/chat`, response cleaning, `/api/speak`, `/api/logs` rewrite to JSON events), `pi4/iris_web.html` (Log tab + filter bar + verbatim speak).
- **IRIS_ARCH.md:** No reference to `/api/chat`, `/api/speak`, or event-categorized logs. The doc doesn't describe web UI routes at all. ✅ Match (out of scope).
- **IRIS_CONFIG_MAP.md:** No reference. ✅ Match.
- **SNAPSHOT_LATEST.md:** Documents S49 changes accurately (the doc was just updated). ✅ Match (verified separately in Section 3 below).
- **Drift:** None.

### S45-S49 summary table

| Session | Code/config change | IRIS_ARCH.md updated? | IRIS_CONFIG_MAP.md updated? | Drift |
|---|---|---|---|---|
| S45 | Docs cleanup | ✅ self-referential | ✅ self-referential | None |
| S46 | WoL beep added | ❌ not mentioned | N/A | LOW |
| S47 | AMUSED emotion | ❌ Serial Protocol enum stale | N/A | LOW |
| S48 | NUM_PREDICT removed | ❌ "iris_config.json on Pi4 (current)" stale | ⚠ Stale Keys lists NUM_PREDICT correctly | MED |
| S49 | Web UI rework | N/A | N/A | None |

---

## 2. Chatterbox vs Kokoro Reference Audit

Kokoro replaced Chatterbox as primary TTS at S38. Every Chatterbox reference in the docs should be marked "rollback only" or "historical".

### IRIS_ARCH.md Chatterbox references

| Section | Reference text (brief) | Classification |
|---|---|---|
| System Roles table (line 76) | "Kokoro TTS (primary), Piper TTS (fallback), Chatterbox (rollback only)" | **CORRECT** — explicit rollback label |
| GandalfAI File Layout (line 196-204) | `chatterbox\` folder structure listed | **AMBIGUOUS** — listed as if active but Kokoro folder absent. Reasonable since Chatterbox files still exist on disk for rollback. |
| Key Constants (line 224) | `CHATTERBOX_BASE_URL = "http://192.168.1.3:8004"` listed without qualification | **STALE** — should note "rollback only" |
| Operational Notes "GandalfAI - Chatterbox Parameters" (line 308) | "Rollback Reference — Kokoro is primary since S38" | **CORRECT** — explicit |
| Operational Reference table (line 360) | "Kokoro TTS (primary), Piper TTS (fallback), Chatterbox (rollback only)" | **CORRECT** |
| VRAM section | "Kokoro ~2GB + gemma3:27b-it-qat" | ✅ Kokoro-aware, no Chatterbox mention |

### IRIS_CONFIG_MAP.md Chatterbox references

| Section | Reference text | Classification |
|---|---|---|
| Voice/TTS — Kokoro (Primary, since S38) | Section header explicit | **CORRECT** |
| Voice/TTS — Chatterbox (Rollback only — replaced by Kokoro S38) | Section header explicit | **CORRECT** |
| Table rows: CHATTERBOX_ENABLED, CHATTERBOX_VOICE, CHATTERBOX_EXAGGERATION | Under "Rollback only" section header | **CORRECT** by inheritance |
| GandalfAI — `C:\IRIS\chatterbox\config.yaml` (Rollback reference only) | Section header explicit | **CORRECT** |

### README.md Chatterbox references

| Section | Reference text | Classification |
|---|---|---|
| Feature Overview table | "TTS: Kokoro (GandalfAI, local) → Piper fallback" | ✅ No Chatterbox mention |
| Voice Pipeline (line 169-180) | "Kokoro TTS (GandalfAI, port 8004) / Piper fallback (port 10200)" | ✅ Kokoro-aware |

### CLAUDE.md Chatterbox references

CLAUDE.md was updated at S45 per CHANGELOG: "GandalfAI role updated: Kokoro primary, Piper fallback, Chatterbox rollback only; VRAM numbers updated to Kokoro+gemma3:27b-it-qat baseline." ✅ Verified in the project-context copy.

### Summary table

| Document | Section | Classification | Severity |
|---|---|---|---|
| IRIS_ARCH.md | Key Constants — `CHATTERBOX_BASE_URL` | STALE | LOW |
| IRIS_ARCH.md | GandalfAI File Layout `chatterbox\` | AMBIGUOUS | LOW |
| All others | (multiple) | CORRECT | none |

### Finding 6.1 — IRIS_ARCH.md "Key Constants" lists CHATTERBOX_BASE_URL without rollback context

- **File:** `IRIS_ARCH.md`
- **Section:** Key Constants → core/config.py
- **Severity:** LOW
- **Issue:** Five Chatterbox lines (`CHATTERBOX_BASE_URL`, `CHATTERBOX_VOICE`, `CHATTERBOX_EXAGGERATION`, `CHATTERBOX_ENABLED`, etc.) appear in the Key Constants snippet without any "rollback only" annotation. The section is labeled "as of S45" — Kokoro became primary at S38, so this section should reflect Kokoro as primary and label Chatterbox as rollback.
- **Fix direction:** Update the code snippet block in "Key Constants" to add a comment or section header clarifying Chatterbox lines are rollback-only.

---

## 3. SNAPSHOT_LATEST.md Claims vs iris_web.py Reality

SNAPSHOT_LATEST.md S49 claims:

> **`pi4/iris_web.py`** — `/api/generate` route renamed to `/api/chat` (was causing 404 on all chat sends). Response cleaning added in `api_chat()`: `extract_emotion_from_reply()` + `clean_llm_reply()` now called before TTS — emotion tags and markdown no longer spoken aloud. New `/api/speak` endpoint for verbatim TTS (bypasses LLM). `/api/logs` rewritten to return structured `{events: [...]}` JSON with category, timestamp, message, detail fields.

### Verification against iris_web.py

| Claim | Code location | Match |
|---|---|---|
| `/api/chat` route exists (renamed from `/api/generate`) | iris_web.py:199 `@app.route("/api/chat", methods=["POST"])` | ✅ |
| `api_chat` calls `extract_emotion_from_reply` before TTS | iris_web.py:210-212: `from services.llm import extract_emotion_from_reply, clean_llm_reply; emotion, clean_reply = extract_emotion_from_reply(raw_reply); clean_reply = clean_llm_reply(clean_reply)` | ✅ |
| Emotion tags + markdown not spoken | TTS call at iris_web.py:213 uses `clean_reply` not `raw_reply` | ✅ |
| `/api/speak` endpoint exists | iris_web.py:219 `@app.route("/api/speak", methods=["POST"])` | ✅ |
| `/api/speak` bypasses LLM | iris_web.py:220-227 — only calls `speak_async`, no Ollama POST | ✅ |
| `/api/logs` returns `{events: [...]}` JSON | iris_web.py:108-186 `api_logs` returns `jsonify(events=events[-250:])` | ✅ |
| Events have category, timestamp, message, detail fields | iris_web.py:140-180 event dicts have `cat`, `t`, `ts`, `msg`, `detail` keys | ✅ |

All S49 claims about `iris_web.py` match the code. ✅ No drift.

### Additional iris_web.py behaviors not claimed in SNAPSHOT but worth noting

- `api_logs` also reads `/home/pi/logs/iris_intent.log` (lines 158-176) and merges entries with "drift" / "stop" / "error" / "route" categorization. Not mentioned in SNAPSHOT.
- `api_logs` includes a `_DRIFT_SIGNALS` tuple (line 117-119) that flags LLM boilerplate phrases ("certainly", "of course", "i'd be happy", etc.) — flagged as cat="drift" in the UI. Not mentioned in SNAPSHOT.
- `api_bench` route (lines 304-319) parses `[BENCH]` log lines. Not mentioned in SNAPSHOT.

These are completeness gaps, not drift — the SNAPSHOT entry focused on the four bug-fix items. ✅ Acceptable.

---

## 4. Constants Cross-Reference

| Constant | IRIS_ARCH.md value | config.py value | Match |
|---|---|---|---|
| OWW_PORT | 10400 (Cron Entries narrative + Operational Reference) | 10400 (config.py:10) | ✅ |
| WHISPER_PORT | 10300 | 10300 (config.py:8) | ✅ |
| PIPER_PORT | 10200 | 10200 (config.py:9) | ✅ |
| OLLAMA_PORT | 11434 | 11434 (config.py:11) | ✅ |
| CMD_PORT | 10500 | 10500 (config.py:12) | ✅ |
| Kokoro port | 8004 (System Roles, Operational Notes) | 8004 (`KOKORO_BASE_URL = "http://192.168.1.3:8004"` config.py:39) | ✅ |
| SLEEP_WINDOW_START_HOUR | 21 (Cron Entries) | 21 (config.py:108) | ✅ |
| SLEEP_WINDOW_END_HOUR | 8 (Cron Entries narrative says "8 AM") | 8 (config.py:109) | ✅ |
| WOL_BOOT_TIMEOUT | 120 s (IRIS_CONFIG_MAP.md core/config.py hardcoded table) | 120 (config.py:127) | ✅ |
| NUM_PREDICT default (legacy fallback) | 150 (IRIS_ARCH.md Key Constants); 300 (IRIS_CONFIG_MAP.md hardcoded table) | 300 (config.py:76) | **❌ MISMATCH** |

### Finding 6.2 — NUM_PREDICT default value conflict between IRIS_ARCH.md and config.py

- **File:** `IRIS_ARCH.md` Key Constants
- **Lines:** IRIS_ARCH.md "Key Constants" section, snippet at line ~225
- **Severity:** MED
- **Issue:** IRIS_ARCH.md states `NUM_PREDICT = 150`. config.py:76 has `NUM_PREDICT = 300`. IRIS_CONFIG_MAP.md hardcoded table (line ~163) correctly states 300. IRIS_ARCH.md is stale by one value-change cycle (pre-S43 or earlier). This is a 2x value discrepancy with potential debugging confusion.
- **Fix direction:** Update IRIS_ARCH.md Key Constants snippet to show `NUM_PREDICT = 300` and clarify it's a legacy fallback (per IRIS_CONFIG_MAP Stale Keys section).

### Finding 6.3 — IRIS_ARCH.md cron entries line mismatch

- **File:** `IRIS_ARCH.md`
- **Section:** Cron Entries (Pi4 user crontab)
- **Severity:** LOW
- **Issue:** Cron line states `30 7 * * *` (7:30 AM wake) but the constant `SLEEP_WINDOW_END_HOUR = 8` (config.py:109). HANDOFF_CURRENT.md describes the wake as "7:30 AM". README.md "Sleep Mode" says "7:30 AM (cron) -- Full assistant resumes automatically". This is design intent: cron triggers wake at 7:30 AM; the `SLEEP_WINDOW_END_HOUR=8` is the *latest* hour considered sleep window for the runtime `in_sleep_window()` check. Both values are correct but their semantic relationship isn't explained.
- **Fix direction:** Add a comment in IRIS_ARCH.md and/or config.py explaining that cron wake (7:30 AM) and `SLEEP_WINDOW_END_HOUR=8` are deliberately offset — the 30-minute buffer prevents an immediate `return_to_sleep` call if a turn completes between 7:30 and 8:00 AM.

---

## 5. Protected Files — Modification Audit

IRIS_ARCH.md ends with a "Do Not Touch Without Explicit Instruction" list (also in SNAPSHOT_LATEST.md and CLAUDE.md):

- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

### CHANGELOG / HANDOFF audit

Scanning CHANGELOG.md and HANDOFF_CURRENT.md for any session-attributed modification of these files.

| Protected file | Modified per CHANGELOG/HANDOFF? | Session | Authorized? |
|---|---|---|---|
| `iris_config.json` | Yes — S48 ("NUM_PREDICT: 200 key removed") | S48 | ✅ Per HANDOFF_CURRENT.md "S48 — NUM_PREDICT Removal + PT-001 Few-Shot Adversarial Examples", this was the named session task. User authorized. |
| `iris_config.json` | Yes — S45 ("AMUSED gap added as HIGH active issue" — no, that's SNAPSHOT_LATEST.md edit, not iris_config.json) | — | — |
| `alsa-init.sh` | Per CHANGELOG: hardened S23. Not modified S45-S49. | S23 (out of audit range) | — |
| `src/TeensyEyes.ino` | No mentions in any session S45-S49. | — | ✅ Not touched. |
| `src/eyes/EyeController.h` | No mentions in any session S45-S49. | — | ✅ Not touched. The comment in IRIS_ARCH.md "src/eyes/EyeController.h -- eye movement/blink/pupil (setTargetPosition seed fix intact)" implies the file has a long-standing fix that should not be regressed. |

### Finding 6.4 — iris_config.json modified in S48 (authorized)

- **File:** `iris_config.json` (Pi4 live), per CHANGELOG S48
- **Severity:** none (informational)
- **Note:** This is the protected file with an explicit modification. The CHANGELOG and HANDOFF entries explicitly describe the change as the session task with rollback documented. User authorization was the session premise. Not a drift; documenting the authorization trail is intact.

### Finding 6.5 — `src/TeensyEyes.ino` not modified despite being a firmware file

- **Severity:** none (informational)
- **Note:** S36 ("Suspend Eye Movement During TTS", commit c27517a) modified `src/main.cpp` not `src/TeensyEyes.ino`. S47 (RD-002 AMUSED) modified `src/main.cpp`. Per IRIS_ARCH.md the protected file is `src/TeensyEyes.ino` specifically — the main entry sketch — separate from `src/main.cpp` (loop logic). The protection is firmware-init-specific. No violations.

---

## 6. Eye Index Map — Doc vs Firmware

### Sources

- **IRIS_ARCH.md "Eye Index Map":**
  ```
  0 = nordicBlue  (default idle)
  1 = flame       (ANGRY)
  2 = hypnoRed    (CONFUSED)
  3 = hazel
  4 = blueFlame1
  5 = dragon
  6 = bigBlue
  ```

- **README.md Eye System table:**
  | Index | Name | Trigger |
  | 0 | nordicBlue | Default idle |
  | 1 | flame | ANGRY emotion (auto-reverts 9s) |
  | 2 | hypnoRed | CONFUSED emotion (auto-reverts 7s) |
  | 3 | hazel | Web UI / EYE:3 |
  | 4 | blueFlame1 | Web UI / EYE:4 |
  | 5 | dragon | Web UI / EYE:5 |
  | 6 | bigBlue | Web UI / EYE:6 |

- **src/main.cpp `EYE_IDX_*` constants (lines 50-56):**
  ```cpp
  static constexpr uint32_t EYE_IDX_DEFAULT      = 0; // nordicBlue
  static constexpr uint32_t EYE_IDX_ANGRY        = 1; // flame
  static constexpr uint32_t EYE_IDX_CONFUSED     = 2; // hypnoRed
  static constexpr uint32_t EYE_IDX_HAZEL        = 3;
  static constexpr uint32_t EYE_IDX_BLUEFLAME1   = 4;
  static constexpr uint32_t EYE_IDX_DRAGON       = 5;
  static constexpr uint32_t EYE_IDX_BIGBLUE      = 6;
  static constexpr uint32_t EYE_IDX_COUNT        = 7;
  ```

- **src/config.h `eyeDefinitions` array:** Not on read list. Trust the main.cpp index constants since they reference the array by name.

### Cross-reference

| Index | IRIS_ARCH.md | README.md | main.cpp EYE_IDX_* | Match |
|---|---|---|---|---|
| 0 | nordicBlue | nordicBlue | nordicBlue | ✅ |
| 1 | flame | flame | flame | ✅ |
| 2 | hypnoRed | hypnoRed | hypnoRed | ✅ |
| 3 | hazel | hazel | hazel | ✅ |
| 4 | blueFlame1 | blueFlame1 | blueFlame1 | ✅ |
| 5 | dragon | dragon | dragon | ✅ |
| 6 | bigBlue | bigBlue | bigBlue | ✅ |

**No drift between docs and firmware.** ✅ All seven eye indices consistent.

### README.md sub-note

README.md adds: "leopard and snake eye assets exist in `src/eyes/240x240/` but are not compiled into `src/config.h` eyeDefinitions. EYE:5 and EYE:6 are dragon and bigBlue respectively." This explicit clarification is good — addresses the natural confusion of seeing 9 directories but only 7 active eyes.

---

## All Findings

### Finding 6.1 — IRIS_ARCH.md Key Constants doesn't label Chatterbox as rollback

- **File:** `IRIS_ARCH.md`, "Key Constants" section
- **Severity:** LOW

### Finding 6.2 — NUM_PREDICT default mismatch (150 in IRIS_ARCH.md vs 300 in config.py)

- **File:** `IRIS_ARCH.md`, "Key Constants" section
- **Severity:** MED

### Finding 6.3 — Cron 7:30 AM wake vs SLEEP_WINDOW_END_HOUR=8 semantic mismatch undocumented

- **File:** `IRIS_ARCH.md`, "Cron Entries" section
- **Severity:** LOW

### Finding 6.4 — S46 WoL beep not mentioned in IRIS_ARCH.md

- **File:** `IRIS_ARCH.md`, "GandalfAI - Wake on LAN" notes section
- **Severity:** LOW

### Finding 6.5 — S47 AMUSED missing from IRIS_ARCH.md Serial Protocol enum

- **File:** `IRIS_ARCH.md` line 568; `README.md` lines 121-130
- **Severity:** LOW (already flagged in Task 3 Finding 3.1)

### Finding 6.6 — S48 NUM_PREDICT removal not reflected in IRIS_ARCH.md "iris_config.json on Pi4 (current)" snippet

- **File:** `IRIS_ARCH.md`, "Key Constants" section
- **Severity:** MED

---

## Summary

- **MED:** 2 (Findings 6.2 NUM_PREDICT default mismatch; 6.6 NUM_PREDICT removal not in IRIS_ARCH.md)
- **LOW:** 4 (6.1 Chatterbox rollback labeling; 6.3 cron/SLEEP_WINDOW_END_HOUR semantic gap; 6.4 WoL beep undocumented; 6.5 AMUSED enum stale — duplicate of Task 3)

Documentation drift is concentrated in **IRIS_ARCH.md "Key Constants"** which has not been refreshed since S38-era values. IRIS_CONFIG_MAP.md is more current. README.md is current except for the AMUSED gap (same as Task 3). The eye index map is fully consistent across all three sources.

Protected files have been respected — every modification (S48 iris_config.json change) was explicitly authorized per session notes. No unauthorized writes to firmware-init or eye-controller files.

*End Task 6.*

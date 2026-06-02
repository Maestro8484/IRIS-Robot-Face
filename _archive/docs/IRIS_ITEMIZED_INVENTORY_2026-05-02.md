# IRIS Itemized Inventory
**Generated:** 2026-05-02 | **Auditor:** Claude Code (read-only pass) | **Repo:** `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face`

---

## 1. Pre-flight

- **Repo path:** `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face`
- **Branch:** `main`
- **Last commit:** `103cbcc` — S45: add docs/iris_issue_log.md -- structured issue/fix history S1-S44
- **Working tree:** Clean (no modified tracked files)
- **Dirty files:** None
- **Untracked files:** `docs/wakeword_import_plan_okay_iris.md` (1 file only)
- **scripts/iris_status.ps1 behavior:** WRITES to `IRIS_STATUS.json` in repo root. Not run.
- **scripts/iris_status.ps1 run/not run:** NOT RUN (modifies repo file)
- **IRIS_STATUS.json timestamp:** Generated 2026-04-25 18:50:57
- **IRIS_STATUS.json current/stale assessment:** STALE — shows commit `826cd72` (S34 era). Live repo is at `103cbcc` (S45). 11 commits behind.
- **Immediate concerns:**
  - IRIS_STATUS.json is 11 commits stale and will mislead any session-start tool that reads it as current state.
  - SNAPSHOT_LATEST.md shows S44 but live repo is S45 — 1 commit stale.
  - IRIS_ARCH.md contains multiple Chatterbox-as-primary references (Kokoro replaced it at S38).
  - AMUSED emotion is in the modelfile but is silently dropped by config.py / led.py / firmware — full pipeline gap confirmed.
  - README.md eye table has 9 entries including leopard/snake, but firmware compiles only 7 eyes (0–6); leopard and snake .h files exist in src but are NOT in the active eyeDefinitions array.

---

## 2. Human Review Legend and Decision Tags

Edit **Human decision:** lines below. Replace `UNDECIDED` with one of:

```
DONE        = resolved, remove from open list
OPEN HIGH   = active high priority
OPEN MED    = active medium priority
OPEN LOW    = active low priority
DEFER       = keep, but not now
REMOVE      = abandon entirely
ARCHIVE     = historical only
SIMPLIFY    = reduce scope / collapse into simpler behavior
TEST        = needs live hardware/service test
UNKNOWN     = not enough evidence
KEEP        = keep as-is
```

**Status labels used in this document:**
- CONFIRMED RESOLVED
- OPEN
- PARTIAL
- STALE / OBSOLETE
- QUESTIONABLE COMPLEXITY
- NEEDS LIVE TEST
- NEEDS USER DECISION
- DOCS ONLY
- SECURITY / CREDENTIAL

**Priority values:** HIGH | MED | LOW | DEFER | REMOVE

**Complexity values:** LOW | MED | HIGH | OVERCOMPLICATED

---

## 3. Master Inventory Table

| ID | Area | Item / Task / Fix | Current Status | Evidence | Priority | Complexity | Recommendation |
|---|---|---|---|---|---|---|---|
| ITEM-001 | Functional / STT | Single-word "stop" STT failure | OPEN | iris_issue_log.md, SNAPSHOT, HANDOFF | HIGH | MED | Implement pre-STT RMS/keyword shortcut |
| ITEM-002 | Functional / Volume | SPEAKER_VOLUME reboot persistence | PARTIAL | iris_web.py:258-260, HANDOFF, SNAPSHOT | MED | LOW | Live test + SD-persist alsactl state |
| ITEM-003 | Functional / Emotion | AMUSED pipeline gap (modelfile→config→led→firmware) | OPEN | config.py:147, led.py:158, main.cpp:69, modelfile | MED | MED | Implement or remove from modelfile |
| ITEM-004 | Functional / Wakeword | okay_iris wakeword plan (untracked, undeployed) | NEEDS USER DECISION | docs/wakeword_import_plan_okay_iris.md | MED | MED | User decides: proceed or archive |
| ITEM-005 | Operational | GandalfAI model sync hazard (3-way desync) | OPEN | iris_issue_log.md open section, SNAPSHOT | MED | LOW | Documented standing rule; no code change needed |
| ITEM-006 | Functional / TTS | Piper sleep routing (local /usr/local/bin/piper broken) | DEFERRED | SNAPSHOT, tts.py:160-194 | LOW | LOW | Defer; Kokoro primary handles all main paths |
| ITEM-007 | Functional / Logging | Duplicate sleep log file (root vs logs/) | OPEN | iris_issue_log.md open section | LOW | LOW | Low-priority cleanup on Pi4 |
| ITEM-008 | Stale Docs | IRIS_STATUS.json 11 commits stale | STALE / OBSOLETE | IRIS_STATUS.json generated field, git log | LOW | LOW | Regenerate or add to .gitignore |
| ITEM-009 | Stale Docs | SNAPSHOT_LATEST.md shows S44, repo is S45 | STALE / OBSOLETE | SNAPSHOT_LATEST.md line 3, git log | LOW | LOW | Update snapshot |
| ITEM-010 | Stale Docs | IRIS_ARCH.md: 8+ Chatterbox-as-primary references | STALE / OBSOLETE | IRIS_ARCH.md lines 72, 99, 187, 191, 197, 225, 304, 540 | MED | LOW | Docs-only update pass |
| ITEM-011 | Stale Docs | IRIS_ARCH.md: gemma3:12b in repo structure section | STALE / OBSOLETE | IRIS_ARCH.md lines 320-321 | LOW | LOW | Update to 27b-it-qat |
| ITEM-012 | Stale Docs | IRIS_ARCH.md: Key Constants labeled "as of S20" | STALE / OBSOLETE | IRIS_ARCH.md line 369 | LOW | LOW | Update constants block |
| ITEM-013 | Stale Docs | README.md: Teensy 4.0 (should be 4.1) | STALE / OBSOLETE | README.md intro paragraph | LOW | LOW | One-word fix |
| ITEM-014 | Stale Docs | README.md: 9-eye table with leopard/snake (firmware has 7 eyes, 0–6) | STALE / OBSOLETE | README.md:75-80, config.h | MED | LOW | Correct eye table to match firmware |
| ITEM-015 | Stale Docs | README.md: "press PROG button" instruction (button inaccessible in enclosure) | STALE / OBSOLETE | README.md:228, IRIS_ARCH.md pin notes | HIGH | LOW | Remove; replace with software bootloader note |
| ITEM-016 | Stale Docs | README.md: gemma3:27b (should be gemma3:27b-it-qat) | STALE / OBSOLETE | README.md:34 | LOW | LOW | One-word fix |
| ITEM-017 | Stale Docs | CLAUDE.md (project): GandalfAI role lists Chatterbox, not Kokoro | STALE / OBSOLETE | CLAUDE.md environment table | LOW | LOW | Update role description |
| ITEM-018 | Stale Docs | assistant.py docstring: "TTS: Chatterbox (primary)" | STALE / OBSOLETE | assistant.py:7 | LOW | LOW | Update comment |
| ITEM-019 | Stale Docs | assistant.py line 664 + iris_bench_report.py line 112: Chatterbox bench label | STALE / OBSOLETE | assistant.py:664, iris_bench_report.py:112 | LOW | LOW | Fix TTS engine label logic |
| ITEM-020 | Stale Docs | tts.py: truncate function comment says "bound Chatterbox generation time" | STALE / OBSOLETE | tts.py:135 | LOW | LOW | Update comment |
| ITEM-021 | Partial Impl | leopard/snake .h files exist in src but NOT compiled into eyeDefinitions | PARTIAL | config.h, src/eyes/240x240/, README.md | LOW | LOW | Either compile them in (adding 2 eyes) or remove files |
| ITEM-022 | Overcomplicated | AMUSED / WARM / SUPPORTIVE / CONCERNED emotion expansion | QUESTIONABLE COMPLEXITY | modelfile (AMUSED only in modelfile), no code support | MED | HIGH | User decides: implement AMUSED fully vs. remove |
| ITEM-023 | Overcomplicated | ACK/NACK serial protocol (Batch 2 candidate) | QUESTIONABLE COMPLEXITY | HANDOFF_CURRENT.md Batch 2 section | LOW | HIGH | Remove until real serial failure justifies it |
| ITEM-024 | Overcomplicated | Chatterbox rollback documentation complexity | QUESTIONABLE COMPLEXITY | IRIS_ARCH.md Chatterbox section, config.py | LOW | MED | Move to archive/rollback note only |
| ITEM-025 | Overcomplicated | Piper sleep routing active task (Kokoro is primary) | QUESTIONABLE COMPLEXITY | HANDOFF Batch 1C remaining, tts.py | LOW | LOW | Defer/Remove from active roadmap |
| ITEM-026 | Overcomplicated | Public README release prep (before docs truth reconciled) | QUESTIONABLE COMPLEXITY | README.md demo section "(video + photos -- add when ready)" | LOW | MED | Defer until docs/status clean |
| ITEM-027 | Resolved | Batch 1A: Wakeword runtime survival | CONFIRMED RESOLVED | HANDOFF, iris_issue_log.md, commit 078da91 | — | — | Done |
| ITEM-028 | Resolved | Batch 1B: Sleep/wake authority unification | CONFIRMED RESOLVED | HANDOFF, iris_issue_log.md, commit 075d098 | — | — | Done |
| ITEM-029 | Resolved | Batch 1C (most): Config coercion, TTS cap, dynamic length, mkstemp, stream warning | CONFIRMED RESOLVED | HANDOFF, commits 1e7c982, b4bfb4d, a51a97e, 58e4d28 | — | — | Done |
| ITEM-030 | Resolved | S36: Eye movement suspended during TTS | CONFIRMED RESOLVED | HANDOFF, commit c27517a | — | — | Done |
| ITEM-031 | Resolved | S37/Batch 3-A: Persona framing + temperature 0.82 | CONFIRMED RESOLVED | HANDOFF, commit 8bdf87e | — | — | Done |
| ITEM-032 | Resolved | S38/Batch 3-B: Kokoro TTS replaces Chatterbox | CONFIRMED RESOLVED | HANDOFF, commit e9bdffa, tts.py | — | — | Done |
| ITEM-033 | Resolved | S39/Batch 3-C: gemma3:27b-it-qat upgrade | CONFIRMED RESOLVED | HANDOFF, commit ec2ad32, modelfile FROM line | — | — | Done |
| ITEM-034 | Resolved | S39/Batch 3-D: Full persona pass (AMUSED tag added to modelfile, vocal texture, insult framing) | CONFIRMED RESOLVED | HANDOFF, commit 4b242d0, modelfile | — | — | Done (but AMUSED pipeline gap remains open) |
| ITEM-035 | Resolved | S40/Batch 3-E: Vision prompt | CONFIRMED RESOLVED | HANDOFF, commit bc707d7 | — | — | Done |
| ITEM-036 | Resolved | S42/Batch 3-F: Pre-LLM intent router (5-layer) | CONFIRMED RESOLVED | HANDOFF, commit c37623e, intent_router.py | — | — | Done |
| ITEM-037 | Resolved | S43: spoken_numbers() extended to thousands/millions | CONFIRMED RESOLVED | iris_issue_log.md, commit 39247b4, tts.py:95-116 | — | — | Done |
| ITEM-038 | Resolved | S44: RANDOM_NUMBER intent route | CONFIRMED RESOLVED | iris_issue_log.md, commit 35d01ba, intent_router.py | — | — | Done |
| ITEM-039 | Resolved | S44: Follow-up short reply filter fix | CONFIRMED RESOLVED | iris_issue_log.md, commit 35d01ba | — | — | Done |
| ITEM-040 | Resolved | S45: iris_issue_log.md created | CONFIRMED RESOLVED | commit 103cbcc, docs/iris_issue_log.md | — | — | Done |
| ITEM-041 | Resolved | ElevenLabs / MAX7219 refs scrubbed (S41) | CONFIRMED RESOLVED | commit 4af3c15, HANDOFF | — | — | Done |
| ITEM-042 | Resolved | ALSA hardening: alsa-init.sh sets 6 critical switches | CONFIRMED RESOLVED | IRIS_ARCH.md status table, iris_issue_log.md | — | — | Done |
| ITEM-043 | Needs Decision | IRIS_STATUS.json: commit regenerated version or add to .gitignore? | NEEDS USER DECISION | IRIS_STATUS.json stale, generates on run | LOW | LOW | User decides |
| ITEM-044 | Stale Docs | IRIS_ARCH.md Batch 1C listed as "Next" in roadmap (substantially complete) | STALE / OBSOLETE | IRIS_ARCH.md lines 152-159 | LOW | LOW | Update roadmap section |
| ITEM-045 | Stale Docs | IRIS_ARCH.md Reboot survival: "Chatterbox docker must be started manually" | STALE / OBSOLETE | IRIS_ARCH.md:191,197 | LOW | LOW | Clarify: Kokoro needs docker start, Chatterbox is rollback |

---

## 4. Resolved / Completed Items

### ITEM-027 — Batch 1A: Wakeword Runtime Survival

- **What changed:** OWW startup retry/backoff (3 attempts, exponential). Socket liveness check each loop. Dead OWW process triggers auto-restart. "error" return skips STT/LLM/TTS. Deployed + SD-persisted.
- **Files:** `pi4/assistant.py` (wakeword.py, services/wakeword.py)
- **Commit:** `078da91`
- **Docs reflect it accurately:** Yes — HANDOFF_CURRENT.md and iris_issue_log.md
- **Stale references:** None

Human decision: UNDECIDED
Human notes:

---

### ITEM-028 — Batch 1B: Sleep/Wake Authority Unification

- **What changed:** Canonical `_do_sleep()` / `_do_wake()`. All paths call these exclusively. `send_command()` / `send_emotion()` return bool. Web routes send via UDP. `iris_wake.py` clears `/tmp/iris_sleep_mode`.
- **Files:** `pi4/assistant.py`, `pi4/iris_sleep.py`, `pi4/iris_wake.py`, `pi4/iris_web.py`
- **Commit:** `075d098`
- **Docs reflect it accurately:** Yes
- **Stale references:** None

Human decision: UNDECIDED
Human notes:

---

### ITEM-029 — Batch 1C (Most): Reliability Hygiene

- **What changed:** Config coercion/validation (1C-A), volume subprocess failure (1C-B), TTS hard-cap + sentence boundary (1C-C), mkstemp in vision.py (1C-E), rate-limited JSON stream warning (1C-E), dynamic response length (SHORT/MEDIUM/LONG/MAX) (1C-F).
- **Files:** `pi4/core/config.py`, `pi4/services/tts.py`, `pi4/services/vision.py`, `pi4/services/llm.py`
- **Commits:** `1e7c982`, `605ada0`, `b4bfb4d`, `58e4d28`, `a51a97e`, `2eaf658`
- **Docs reflect it accurately:** Yes — HANDOFF lists remaining 1C items (SPEAKER_VOLUME, Piper sleep routing)
- **Stale references:** IRIS_ARCH.md still lists Batch 1C as "Next" (see ITEM-044)

Human decision: UNDECIDED
Human notes:

---

### ITEM-030 — S36: Eye Movement Suspended During TTS

- **What changed:** Eye movement paused for duration of TTS audio, resumed on completion.
- **Files:** `src/main.cpp`
- **Commit:** `c27517a`
- **Docs reflect it accurately:** Yes
- **Stale references:** None

Human decision: UNDECIDED
Human notes:

---

### ITEM-031 — S37/Batch 3-A: Persona Framing + Temperature

- **What changed:** Replaced explicit EMOTIONAL STATE block with implicit thick-skin/fast-mouth character framing. Temperature raised 0.7→0.82. Repeat penalty 1.1, top_k 40, top_p 0.9 confirmed in modelfile.
- **Files:** `ollama/iris_modelfile.txt`
- **Commit:** `8bdf87e`
- **Docs reflect it accurately:** Yes
- **Stale references:** None

Human decision: UNDECIDED
Human notes:

---

### ITEM-032 — S38/Batch 3-B: Kokoro TTS Replaces Chatterbox

- **What changed:** `pi4/services/tts.py` rewritten — Kokoro primary via `/v1/audio/speech`, Piper Wyoming fallback. Sleep/wake system phrases route directly to Piper via `_PIPER_DIRECT_PHRASES` set. Chatterbox constants remain in config.py as rollback only.
- **Files:** `pi4/services/tts.py`, `pi4/core/config.py`
- **Commit:** `e9bdffa`
- **Docs reflect it accurately:** tts.py docstring is correct; multiple IRIS_ARCH.md sections are stale (see ITEM-010)
- **Stale references:** IRIS_ARCH.md (8+ locations), assistant.py docstring, bench labels — tracked in ITEM-010, ITEM-018, ITEM-019, ITEM-020

Human decision: UNDECIDED
Human notes:

---

### ITEM-033 — S39/Batch 3-C: gemma3:27b-it-qat Upgrade

- **What changed:** Base model upgraded from gemma3:12b to gemma3:27b-it-qat. OLLAMA_FLASH_ATTENTION=1, OLLAMA_KV_CACHE_TYPE=q8_0 set machine-level on GandalfAI. num_predict 800, num_ctx 4096.
- **Files:** `ollama/iris_modelfile.txt` (FROM line), `ollama/iris-kids_modelfile.txt`
- **Commit:** `ec2ad32`
- **Docs reflect it accurately:** modelfile is correct; IRIS_ARCH.md repo structure still says gemma3:12b (see ITEM-011); README says gemma3:27b without -it-qat (see ITEM-016)
- **Stale references:** ITEM-011, ITEM-016

Human decision: UNDECIDED
Human notes:

---

### ITEM-034 — S39/Batch 3-D: Full Persona Pass (AMUSED Tag Added to Modelfile)

- **What changed:** AMUSED added to modelfile valid emotion values. Vocal texture refined. Insult examples added. Contradiction fix (he/him throughout). AMUSED now listed in modelfile but NOT implemented in config.py, led.py, or firmware — this created ITEM-003.
- **Files:** `ollama/iris_modelfile.txt`
- **Commit:** `4b242d0`
- **Docs reflect it accurately:** Yes (the persona changes are complete; the pipeline gap is a separate open issue)
- **Stale references:** None for the persona work itself; ITEM-003 is the downstream gap

Human decision: UNDECIDED
Human notes:

---

### ITEM-035 — S40/Batch 3-E: Vision Prompt

- **What changed:** Vision prompt behavior — household recognition, text reading, editorial beat. Character voice for visual descriptions.
- **Files:** `ollama/iris_modelfile.txt` (VISION section), `pi4/services/vision.py`
- **Commit:** `bc707d7`
- **Docs reflect it accurately:** Yes
- **Stale references:** None

Human decision: UNDECIDED
Human notes:

---

### ITEM-036 — S42/Batch 3-F: Pre-LLM Intent Router (5-Layer)

- **What changed:** `pi4/core/intent_router.py` — NEW. REFLEX→COMMAND→UTILITY→AMBIGUOUS→LLM layers. Handles sleep/stop/wake (REFLEX), volume/eyes/kids (COMMAND), time/date/math/random/vision (UTILITY), ambiguous phrases (AMBIGUOUS), everything else (LLM). Fail-open on exception. Rotating log to `iris_intent.log`.
- **Files:** `pi4/core/intent_router.py` (new), `pi4/assistant.py`
- **Commits:** `c37623e`, `3a38644`
- **Docs reflect it accurately:** Yes — HANDOFF and iris_issue_log.md both show Batch 3-F CLOSED
- **Stale references:** HANDOFF has one stale note ("Batch 3-F: CLOSED (S42)" appears twice in slightly different wording) — minor, not blocking

Human decision: UNDECIDED
Human notes:

---

### ITEM-037 — S43: spoken_numbers() Extended to Thousands/Millions

- **What changed:** `_int_to_words()` handles up to 1 billion. Removed <= 999 bailout. "4210" → "four thousand two hundred ten".
- **Files:** `pi4/services/tts.py` (spoken_numbers / _int_to_words, lines 85-128)
- **Commit:** `39247b4`
- **Docs reflect it accurately:** Yes
- **Stale references:** None

Human decision: UNDECIDED
Human notes:

---

### ITEM-038 — S44: RANDOM_NUMBER Intent Route

- **What changed:** Layer 2 UTILITY: `_RANDOM_RE` catches pick/tell/give/choose/generate/select + "random number". `_RANDOM_RANGE_RE` parses "between X and Y". Answered locally via `random.randint()` — zero LLM latency.
- **Files:** `pi4/core/intent_router.py`, `pi4/services/llm.py`
- **Commit:** `35d01ba`
- **Docs reflect it accurately:** Yes
- **Stale references:** None

Human decision: UNDECIDED
Human notes:

---

### ITEM-039 — S44: Follow-up Short Reply Filter Fix

- **What changed:** Follow-up loop `< 3 words` gate replaced with `_WHISPER_HALLUCINATIONS` set check. Brief valid replies ("Yes, 54.", "Seven.", "No.") now pass through.
- **Files:** `pi4/assistant.py`
- **Commit:** `35d01ba`
- **Docs reflect it accurately:** Yes
- **Stale references:** None

Human decision: UNDECIDED
Human notes:

---

### ITEM-040 — S45: iris_issue_log.md Created

- **What changed:** `docs/iris_issue_log.md` created — append-only structured record of all bugs, root causes, and fixes from S1-S44. Open issues section included (stop STT, GandalfAI sync, volume, Piper routing, duplicate log).
- **Files:** `docs/iris_issue_log.md`
- **Commit:** `103cbcc`
- **Docs reflect it accurately:** Yes — this IS a doc artifact
- **Stale references:** None at time of creation

Human decision: UNDECIDED
Human notes:

---

### ITEM-041 — S41: ElevenLabs / MAX7219 Refs Scrubbed

- **What changed:** All ElevenLabs and MAX7219 references removed from repo. Credentials redacted. Old snapshot files untracked.
- **Files:** Multiple
- **Commit:** `4af3c15`
- **Docs reflect it accurately:** Yes
- **Stale references:** None confirmed in Python files (grep confirmed clean)

Human decision: UNDECIDED
Human notes:

---

### ITEM-042 — ALSA Hardening (alsa-init.sh)

- **What changed:** alsa-init.sh now sets all 6 critical switches explicitly on Pi4 boot. Mic + speakers restore without manual intervention after reboot.
- **Files:** `pi4/alsa-init.sh` (protected file)
- **Commit:** S23 range
- **Docs reflect it accurately:** Yes — IRIS_ARCH.md status table notes this as HARDENED S23
- **Stale references:** None

Human decision: UNDECIDED
Human notes:

---

## 5. Open Functional Issues

### ITEM-001 — Single-Word "stop" STT Failure

Area: Pi4 / STT / Wakeword
Current status: OPEN
Evidence: `docs/iris_issue_log.md` open section; `SNAPSHOT_LATEST.md` Active Issues (HIGH); HANDOFF Known TODO
Priority: HIGH
Complexity: MED
Recommendation: Implement pre-STT RMS duration gate or local keyword list checked before Whisper. If post-wakeword audio < ~0.5s, match directly against a small set {"stop", "cancel", "quiet", "pause"} without routing through Whisper.
Files involved: `pi4/assistant.py`, `pi4/hardware/audio_io.py`
Resolved evidence: Not resolved — no code change found
Stale references: S42 documented the issue; no fix code exists in current repo
Needs live test: yes (need to confirm RMS/duration signature of "stop" vs longer utterances)
Suggested default decision: OPEN HIGH

Human decision: UNDECIDED
Human notes:

---

### ITEM-002 — SPEAKER_VOLUME Reboot Persistence

Area: Pi4 / Audio / Volume
Current status: PARTIAL
Evidence: `pi4/iris_web.py:258-260` (alsactl store + iris_config.json write on volume change); `pi4/core/config.py:71` (SPEAKER_VOLUME default, overridable); HANDOFF Batch 1C remaining; SNAPSHOT Active Issues (MED)
Priority: MED
Complexity: LOW
Recommendation: Verify on live Pi4 that (a) iris_config.json survives overlayfs reboot (must be SD-persisted), and (b) `alsactl store` state file is also SD-persisted. The web UI path partially addresses this but SD layer persistence for the alsa state file is unconfirmed.
Files involved: `pi4/iris_web.py`, `pi4/hardware/audio_io.py`, `pi4/core/config.py`
Resolved evidence: Web UI path writes to iris_config.json and calls alsactl store (lines 258-260). ALSA state file must survive overlayfs for this to work end-to-end.
Stale references: None — open issue correctly listed
Needs live test: yes
Suggested default decision: TEST

Human decision: UNDECIDED
Human notes:

---

### ITEM-003 — AMUSED Emotion Pipeline Gap

Area: Functional / Emotion / Cross-layer
Current status: OPEN
Evidence: `ollama/iris_modelfile.txt` lists AMUSED as valid; `pi4/core/config.py:147` VALID_EMOTIONS does NOT include AMUSED; `pi4/hardware/led.py:158` _EMOTION_LED dict does NOT include AMUSED; `src/main.cpp:69` EmotionID enum does NOT include AMUSED (EMOTION_COUNT=8, 8 emotions)
Priority: MED
Complexity: MED
Recommendation: Make a decision (see ITEM-022 / Section 11). Either: (A) implement AMUSED fully — add to VALID_EMOTIONS, add LED behavior to led.py, add EmotionID + emotionTable entry to firmware, reflash; OR (B) remove AMUSED from modelfile valid values and replace with NEUTRAL for those cases. Option B is simpler and avoids firmware changes.
Files involved: `ollama/iris_modelfile.txt`, `pi4/core/config.py`, `pi4/hardware/led.py`, `src/main.cpp`, `src/config.h`
Resolved evidence: None — confirmed unimplemented in all three layers
Stale references: HANDOFF/SNAPSHOT do not call this out explicitly; prior audit was correct
Needs live test: no (code inspection is definitive; AMUSED will silently become NEUTRAL)
Suggested default decision: NEEDS USER DECISION

Human decision: UNDECIDED
Human notes:

---

### ITEM-004 — okay_iris Wakeword Plan (Untracked, Undeployed)

Area: Pi4 / Wakeword
Current status: NEEDS USER DECISION
Evidence: `docs/wakeword_import_plan_okay_iris.md` (untracked file); no onnx model committed; hey_jarvis is current production wakeword (config.py:22)
Priority: MED
Complexity: MED
Recommendation: Critical quality concern in the plan doc: at OWW_THRESHOLD=0.90, okay_iris recall is near 0%. Threshold range validator min (currently 0.5) would need to be lowered to 0.1. Plan is well-documented but model quality may be insufficient for real-world use. Recommend live score test before committing. User must decide: proceed, archive, or do a live test first.
Files involved: `docs/wakeword_import_plan_okay_iris.md`, `pi4/core/config.py:22,139,186`, `pi4/assistant.py:338`
Resolved evidence: Not started — no onnx file, no config change, no deploy
Stale references: Plan doc accurately documents what needs to happen
Needs live test: yes (score distribution test on Pi4 required before deployment)
Suggested default decision: TEST or DEFER

Human decision: UNDECIDED
Human notes:

---

### ITEM-005 — GandalfAI Model Sync Hazard (3-Way Desync)

Area: GandalfAI / Operational
Current status: OPEN (documented standing rule)
Evidence: `docs/iris_issue_log.md` open section; memory: project_gandalf_modelfile_sync.md; SNAPSHOT Active Issues (MED)
Priority: MED
Complexity: LOW
Recommendation: This is an operational workflow issue, not a code bug. No code change needed. Standing rule is: any LLM personality drift → run `ollama show iris --modelfile` on GandalfAI and compare to repo before any persona changes. Consider adding a git hook or deploy script check as a future enhancement. For now: keep the rule documented, no active task needed.
Files involved: `ollama/iris_modelfile.txt`, GandalfAI clone at `C:\IRIS\IRIS-Robot-Face\`
Resolved evidence: Not a code fix — acknowledged operational hazard
Stale references: None
Needs live test: no
Suggested default decision: KEEP (as documented rule)

Human decision: UNDECIDED
Human notes:

---

### ITEM-006 — Piper Sleep Routing (Local Piper Broken)

Area: Pi4 / TTS / Sleep
Current status: DEFERRED
Evidence: `pi4/services/tts.py:160-194` — `_PIPER_DIRECT_PHRASES` routes system phrases to Piper; local `/usr/local/bin/piper` binary is broken; Wyoming Piper on GandalfAI:10200 is the fallback; SNAPSHOT Active Issues (MED but noted LOW-LOW); HANDOFF says deprioritized
Priority: LOW
Complexity: LOW
Recommendation: Do not make this an active task while Kokoro is healthy. The only scenario where this matters is sleep/wake greeting phrases. If Piper on GandalfAI is available (Wyoming:10200), those phrases still work via the network. If GandalfAI is down, they fail silently. Not worth fixing unless Kokoro itself fails.
Files involved: `pi4/services/tts.py`, GandalfAI Wyoming Piper service
Resolved evidence: Not resolved — deferred by design
Stale references: HANDOFF still lists it as 1C remainder; should be moved to "deprioritized" or removed
Needs live test: no
Suggested default decision: DEFER or REMOVE from active roadmap

Human decision: UNDECIDED
Human notes:

---

### ITEM-007 — Duplicate Sleep Log File

Area: Pi4 / Logging
Current status: OPEN
Evidence: `docs/iris_issue_log.md` open section; `/home/pi/iris_sleep.log` (root level) may duplicate `/home/pi/logs/iris_sleep.log`
Priority: LOW
Complexity: LOW
Recommendation: On next Pi4 SSH session, check if both files exist, compare content, remove the root-level one if logs/ is canonical.
Files involved: Pi4 filesystem only (no repo file change needed)
Resolved evidence: Not confirmed; needs live check
Stale references: None
Needs live test: yes (Pi4 SSH required)
Suggested default decision: OPEN LOW

Human decision: UNDECIDED
Human notes:

---

## 6. Partially Implemented / Inconsistent Items

### ITEM-003 — AMUSED Emotion Pipeline Gap
(See Section 5, ITEM-003 — canonical entry is there)

---

### ITEM-021 — leopard/snake Eye Files Exist But Not Compiled

Area: Firmware / Eyes
Current status: PARTIAL
Evidence: `src/eyes/240x240/leopard.h` and `src/eyes/240x240/snake.h` exist. `src/config.h` eyeDefinitions array has 7 entries (0–6: nordicBlue, flame, hypnoRed, hazel, blueFlame1, dragon, bigBlue). leopard and snake are NOT in the array. `README.md` lists them at indices 5 and 6 (wrong — those slots are dragon and bigBlue).
Priority: LOW
Complexity: LOW
Recommendation: Two options: (A) Add leopard and snake to eyeDefinitions in config.h, making it a 9-eye system (EYE:0–8). This requires firmware reflash. Or (B) Delete leopard.h and snake.h from src and update README to match the 7-eye reality. Option B is simpler. Either way, README must be corrected.
Files involved: `src/config.h`, `src/eyes/240x240/leopard.h`, `src/eyes/240x240/snake.h`, `README.md`
Resolved evidence: Not resolved — files exist but unused
Stale references: README.md eye table (ITEM-014 covers the README side)
Needs live test: Only if Option A (add eyes) is chosen — requires firmware reflash
Suggested default decision: NEEDS USER DECISION (compile them in or delete them)

Human decision: UNDECIDED
Human notes:

---

### ITEM-002 — Volume Persistence Partial Implementation
(See Section 5, ITEM-002 — canonical entry is there)

---

## 7. Overcomplicated / Candidate Removal Items

### ITEM-022 — AMUSED / WARM / SUPPORTIVE / CONCERNED Emotion Expansion

Area: Functional / Emotion / Overcomplicated
Current status: QUESTIONABLE COMPLEXITY
Evidence: AMUSED in modelfile, not in any code layer. WARM, SUPPORTIVE, CONCERNED not in modelfile, not in code — these were roadmap ideas, not implemented anywhere. Full implementation of any new emotion requires: modelfile edit, VALID_EMOTIONS, MOUTH_MAP, led.py _EMOTION_LED, firmware EmotionID enum + emotionTable, and reflash.
Priority: MED (AMUSED), LOW (others)
Complexity: HIGH (full implementation for each emotion)
Recommendation: For AMUSED specifically — make a binary choice: implement fully (4 files + firmware flash) or remove from modelfile now. For WARM/SUPPORTIVE/CONCERNED — remove from active roadmap entirely. The value they add does not justify the full-stack implementation cost. IRIS already has 8 well-defined emotions; more is not better.
Files involved: `ollama/iris_modelfile.txt`, `pi4/core/config.py`, `pi4/hardware/led.py`, `src/main.cpp`, `src/config.h`
Resolved evidence: None of these (beyond AMUSED in modelfile) have been implemented
Stale references: Any roadmap reference to emotion expansion
Needs live test: Only if implementing
Suggested default decision: SIMPLIFY (AMUSED: decide + implement cleanly) / REMOVE (WARM, SUPPORTIVE, CONCERNED)

Human decision: UNDECIDED
Human notes:

---

### ITEM-023 — ACK/NACK Serial Protocol (Batch 2 Candidate)

Area: Firmware / Serial / Overcomplicated
Current status: QUESTIONABLE COMPLEXITY
Evidence: `HANDOFF_CURRENT.md` Batch 2 section: "ACK/NACK protocol only if justified." No known serial reliability failure has occurred. Teensy serial is reliable at 115200 baud over short USB cable.
Priority: LOW
Complexity: HIGH
Recommendation: Remove from Batch 2 scope entirely. Serial communication has not been a failure point in any logged issue. Adding ACK/NACK requires bidirectional protocol changes in both Teensy firmware and Pi4 TeensyBridge — significant complexity for no demonstrated need. Add it only if a real serial failure occurs.
Files involved: `src/main.cpp`, `pi4/hardware/teensy_bridge.py`, `HANDOFF_CURRENT.md`
Resolved evidence: N/A — not implemented, not needed
Stale references: HANDOFF Batch 2 candidate list
Needs live test: no
Suggested default decision: REMOVE

Human decision: UNDECIDED
Human notes:

---

### ITEM-024 — Chatterbox Rollback Documentation Complexity

Area: Docs / GandalfAI / Overcomplicated
Current status: QUESTIONABLE COMPLEXITY
Evidence: IRIS_ARCH.md has a full "GandalfAI - Chatterbox Parameters (Baseline)" section. config.py keeps CHATTERBOX_BASE_URL, CHATTERBOX_VOICE, CHATTERBOX_EXAGGERATION, CHATTERBOX_ENABLED constants. Multiple stale Chatterbox-as-primary references exist across docs. Chatterbox is functionally a rollback that may or may not still be deployed on GandalfAI.
Priority: LOW
Complexity: MED
Recommendation: Consolidate Chatterbox to a single "Rollback Reference" note. Remove from active architecture descriptions. Keep the config.py constants (low overhead, genuine rollback utility). Move the IRIS_ARCH.md Chatterbox Parameters block to a rollback/historical note. Clean all "Chatterbox primary" descriptions in one docs pass.
Files involved: `IRIS_ARCH.md`, `pi4/core/config.py`, `pi4/assistant.py` (docstring), `pi4/iris_bench_report.py`
Resolved evidence: N/A
Stale references: ITEM-010 (IRIS_ARCH.md), ITEM-018, ITEM-019, ITEM-020 cover the code-side stale comments
Needs live test: no
Suggested default decision: SIMPLIFY (consolidate to rollback note in one place)

Human decision: UNDECIDED
Human notes:

---

### ITEM-025 — Piper Sleep Routing Active Task

Area: Pi4 / TTS / Overcomplicated
Current status: QUESTIONABLE COMPLEXITY
Evidence: Listed in HANDOFF as Batch 1C remaining item. SNAPSHOT notes "LOW-LOW priority." Kokoro handles all primary TTS. Only edge case is sleep/wake greeting phrases. tts.py already has _PIPER_DIRECT_PHRASES routing to Wyoming Piper on GandalfAI:10200, which works if GandalfAI is up.
Priority: LOW
Complexity: LOW
Recommendation: Remove from active roadmap. The current behavior (Wyoming Piper fallback on GandalfAI) is acceptable for the sleep greeting edge case. Local Piper is broken but fixing it provides minimal value while Kokoro is reliable.
Files involved: `HANDOFF_CURRENT.md`, `pi4/services/tts.py`
Resolved evidence: N/A
Stale references: HANDOFF Batch 1C remaining list
Needs live test: no
Suggested default decision: REMOVE from active roadmap

Human decision: UNDECIDED
Human notes:

---

### ITEM-026 — Public README Release Prep

Area: Docs / Release / Overcomplicated
Current status: QUESTIONABLE COMPLEXITY
Evidence: README.md has "Demo: *(video + photos -- add when ready)*" placeholder. Multiple stale claims (eye count, model version, PROG button, Teensy version). README is positioned as a public-facing document but is inaccurate.
Priority: LOW
Complexity: MED
Recommendation: Defer public release prep. First clean up the factual errors (ITEM-013 through ITEM-016) in a docs pass, then consider whether to add demo content. Do not invest in demo/release polish until docs accuracy is restored.
Files involved: `README.md`
Resolved evidence: N/A
Stale references: All README stale items (ITEM-013 through ITEM-016)
Needs live test: no
Suggested default decision: DEFER

Human decision: UNDECIDED
Human notes:

---

## 8. Stale / Obsolete Items to Remove From Current Docs

### ITEM-008 — IRIS_STATUS.json 11 Commits Stale

Area: Docs / Status
Current status: STALE / OBSOLETE
Evidence: `IRIS_STATUS.json` generated field: "2026-04-25 18:50:57". Shows commit 826cd72 (S34). Live repo is 103cbcc (S45). 11 commits behind.
Priority: LOW
Complexity: LOW
Recommendation: Two options: (A) Regenerate by running `.\scripts\iris_status.ps1` from SuperMaster (it writes the file, then commit). (B) Add `IRIS_STATUS.json` to `.gitignore` so it's always generated fresh on each session. Option B preferred — stale committed JSON is worse than no JSON.
Files involved: `IRIS_STATUS.json`, `.gitignore` (if option B)
Resolved evidence: N/A
Stale references: This file itself is the stale reference
Needs live test: no
Suggested default decision: NEEDS USER DECISION (regenerate+commit vs .gitignore)

Human decision: UNDECIDED
Human notes:

---

### ITEM-009 — SNAPSHOT_LATEST.md Shows S44, Repo Is S45

Area: Docs / Snapshot
Current status: STALE / OBSOLETE
Evidence: `SNAPSHOT_LATEST.md` line 3: "Session: S44 | Last commit: 35d01ba". Live last commit: 103cbcc (S45: iris_issue_log.md created).
Priority: LOW
Complexity: LOW
Recommendation: Run `/snapshot` at end of next session to update. Low urgency — only 1 commit behind (S45 only added docs/iris_issue_log.md, no runtime changes).
Files involved: `SNAPSHOT_LATEST.md`
Resolved evidence: N/A
Stale references: Snapshot itself
Needs live test: no
Suggested default decision: OPEN LOW (do next session)

Human decision: UNDECIDED
Human notes:

---

### ITEM-010 — IRIS_ARCH.md: 8+ Chatterbox-as-Primary References

Area: Docs / Architecture
Current status: STALE / OBSOLETE
Evidence (all in `IRIS_ARCH.md`):
- Line 72: GandalfAI role: "Chatterbox TTS" — should include Kokoro as primary
- Line 99: Pipeline: "Pi4 requests Chatterbox primary or Piper fallback"
- Line 187: Status table: "Whisper->Ollama iris->Chatterbox->speakers"
- Line 191: "GandalfAI reboot: Chatterbox docker must be started manually"
- Line 197: Reboot checklist: "Chatterbox does not auto-start"
- Line 225: docker-compose.yml comment: "iris stack (pipeline: whisper, piper, chatterbox)"
- Line 304: Repo structure: "services/tts.py -- Chatterbox->Piper only"
- Lines 540-543: "GandalfAI - Chatterbox Parameters (Baseline)" active section
Priority: MED
Complexity: LOW
Recommendation: Single docs-only pass on IRIS_ARCH.md. Replace Chatterbox-primary language with Kokoro-primary throughout. Consolidate Chatterbox to one rollback note. Can be done in one editing session.
Files involved: `IRIS_ARCH.md`
Resolved evidence: N/A
Stale references: This item IS the stale references
Needs live test: no
Suggested default decision: OPEN MED (next docs pass)

Human decision: UNDECIDED
Human notes:

---

### ITEM-011 — IRIS_ARCH.md: gemma3:12b in Repo Structure Section

Area: Docs / Architecture
Current status: STALE / OBSOLETE
Evidence: `IRIS_ARCH.md` lines 320-321: `iris_modelfile.txt -- adult IRIS persona (gemma3:12b)` and `iris-kids_modelfile.txt -- kids IRIS persona (gemma3:12b)`. Actual modelfile: FROM gemma3:27b-it-qat (confirmed).
Priority: LOW
Complexity: LOW
Recommendation: Update two lines in IRIS_ARCH.md. Bundle with ITEM-010 docs pass.
Files involved: `IRIS_ARCH.md`
Resolved evidence: N/A
Stale references: These two lines
Needs live test: no
Suggested default decision: OPEN LOW

Human decision: UNDECIDED
Human notes:

---

### ITEM-012 — IRIS_ARCH.md: Key Constants Labeled "as of S20"

Area: Docs / Architecture
Current status: STALE / OBSOLETE
Evidence: `IRIS_ARCH.md` line 369: "### core/config.py (as of S20)". Currently at S45. The constants block shows CHATTERBOX_BASE_URL and related Chatterbox constants as primary configuration. These are now rollback-only.
Priority: LOW
Complexity: LOW
Recommendation: Update the "as of S20" label to "as of S45 (rollback constants included for reference)". Update the iris_config.json example in this section — it shows `CHATTERBOX_ENABLED: true` which is stale. Bundle with ITEM-010 docs pass.
Files involved: `IRIS_ARCH.md`
Resolved evidence: N/A
Stale references: Section header and iris_config.json example
Needs live test: no
Suggested default decision: OPEN LOW

Human decision: UNDECIDED
Human notes:

---

### ITEM-013 — README.md: Teensy 4.0 (Should Be 4.1)

Area: Docs / README
Current status: STALE / OBSOLETE
Evidence: `README.md` intro: "Teensy 4.0". Hardware is Teensy 4.1 (confirmed in IRIS_ARCH.md, HANDOFF, all Pi4 references to `/dev/ttyACM0` with T4.1 extended pins 38-55).
Priority: LOW
Complexity: LOW
Recommendation: One-word change. Bundle with README docs pass.
Files involved: `README.md`
Resolved evidence: N/A
Stale references: "Teensy 4.0" in README intro and hardware table
Needs live test: no
Suggested default decision: OPEN LOW

Human decision: UNDECIDED
Human notes:

---

### ITEM-014 — README.md: 9-Eye Table with leopard/snake (Firmware Has 7 Eyes)

Area: Docs / README / Firmware
Current status: STALE / OBSOLETE
Evidence: `README.md` eye table: 9 entries (0-8: nordicBlue, flame, hypnoRed, hazel, blueFlame1, leopard, snake, dragon, bigBlue). `src/config.h` eyeDefinitions: 7 entries (0-6: nordicBlue, flame, hypnoRed, hazel, blueFlame1, dragon, bigBlue). leopard.h and snake.h exist in src but NOT included in eyeDefinitions. README says EYE:n range 0-8; firmware max is EYE:6.
Priority: MED
Complexity: LOW
Recommendation: Correct README eye table to match config.h (7 eyes, 0–6). Note that EYE:7 and EYE:8 are invalid commands. See ITEM-021 for whether to add leopard/snake to firmware or delete the .h files.
Files involved: `README.md`, `src/config.h`
Resolved evidence: N/A
Stale references: README eye table and EYE:n serial protocol description
Needs live test: no
Suggested default decision: OPEN MED

Human decision: UNDECIDED
Human notes:

---

### ITEM-015 — README.md: "Press PROG Button" Instruction (Button Inaccessible)

Area: Docs / README / Safety
Current status: STALE / OBSOLETE
Evidence: `README.md:228`: "Then press PROG button on Teensy to complete flash." `IRIS_ARCH.md` pin notes: "Teensy is enclosure-mounted. RESET and PROG buttons are NOT accessible. All resets via software bootloader entry only."
Priority: HIGH (safety risk — following this instruction is impossible and may confuse)
Complexity: LOW
Recommendation: Replace with: "Teensy is enclosure-mounted — PROG and RESET buttons are not accessible. Flash via software bootloader: run `pio run -t upload`, then trigger bootloader entry via serial." Bundle with README docs pass.
Files involved: `README.md`
Resolved evidence: N/A
Stale references: The `pio run -t upload` + PROG button paragraph
Needs live test: no
Suggested default decision: OPEN HIGH (misleading instruction)

Human decision: UNDECIDED
Human notes:

---

### ITEM-016 — README.md: gemma3:27b (Should Be gemma3:27b-it-qat)

Area: Docs / README
Current status: STALE / OBSOLETE
Evidence: `README.md:34` feature table: "Ollama `gemma3:27b` -- fully local". Actual model: `gemma3:27b-it-qat` (confirmed in modelfile FROM line).
Priority: LOW
Complexity: LOW
Recommendation: Append "-it-qat" to the model name. Bundle with README docs pass.
Files involved: `README.md`
Resolved evidence: N/A
Stale references: One entry in the feature table
Needs live test: no
Suggested default decision: OPEN LOW

Human decision: UNDECIDED
Human notes:

---

### ITEM-017 — CLAUDE.md (Project): GandalfAI Role Lists Chatterbox, Not Kokoro

Area: Docs / CLAUDE.md
Current status: STALE / OBSOLETE
Evidence: `CLAUDE.md` Environment Quick Reference table: GandalfAI role column says "Ollama, Whisper, Piper, Chatterbox, RTX 3090 inference". Should include Kokoro as primary TTS.
Priority: LOW
Complexity: LOW
Recommendation: Update GandalfAI role to: "Ollama, Whisper, Kokoro TTS (primary), Piper TTS (fallback), Chatterbox (rollback), RTX 3090 inference". Bundle with docs pass.
Files involved: `CLAUDE.md`
Resolved evidence: N/A
Stale references: GandalfAI role column in environment table
Needs live test: no
Suggested default decision: OPEN LOW

Human decision: UNDECIDED
Human notes:

---

### ITEM-018 — assistant.py Docstring: "TTS: Chatterbox (primary)"

Area: Code / Comment
Current status: STALE / OBSOLETE
Evidence: `pi4/assistant.py:7`: "TTS: Chatterbox @ 192.168.1.3:8004 (primary)"
Priority: LOW
Complexity: LOW
Recommendation: Update line 7 to: "TTS: Kokoro @ 192.168.1.3:8004 (primary) / Piper fallback". Minor comment change.
Files involved: `pi4/assistant.py`
Resolved evidence: N/A
Stale references: Line 7 only
Needs live test: no
Suggested default decision: OPEN LOW

Human decision: UNDECIDED
Human notes:

---

### ITEM-019 — assistant.py + iris_bench_report.py: Chatterbox Bench Label Logic

Area: Code / Bench / Logging
Current status: STALE / OBSOLETE
Evidence:
- `pi4/assistant.py:664`: `_tts_eng = "chatterbox" if CHATTERBOX_ENABLED else "piper"` — KOKORO_ENABLED not checked; bench log will say "chatterbox" even when Kokoro is running (since CHATTERBOX_ENABLED defaults to True as rollback constant)
- `pi4/iris_bench_report.py:112`: `tts_mode = "chatterbox" if CHATTERBOX_ENABLED else "piper"` — same incorrect logic
Priority: LOW
Complexity: LOW
Recommendation: Fix the engine label logic: check KOKORO_ENABLED first, then CHATTERBOX_ENABLED, then default "piper". This is a cosmetic bench/logging fix — no runtime behavior change.
Files involved: `pi4/assistant.py:664`, `pi4/iris_bench_report.py:112`
Resolved evidence: N/A
Stale references: Both lines
Needs live test: no
Suggested default decision: OPEN LOW

Human decision: UNDECIDED
Human notes:

---

### ITEM-020 — tts.py: _truncate_for_tts Comment Says "Chatterbox"

Area: Code / Comment
Current status: STALE / OBSOLETE
Evidence: `pi4/services/tts.py:135`: "Cap TTS input at max_chars to bound Chatterbox generation time."
Priority: LOW
Complexity: LOW
Recommendation: Update comment to say "Kokoro" (or remove the TTS engine reference since it applies to any TTS backend). One-line change.
Files involved: `pi4/services/tts.py`
Resolved evidence: N/A
Stale references: Line 135
Needs live test: no
Suggested default decision: OPEN LOW

Human decision: UNDECIDED
Human notes:

---

### ITEM-044 — IRIS_ARCH.md Batch 1C Listed as "Next" (Substantially Complete)

Area: Docs / Architecture / Roadmap
Current status: STALE / OBSOLETE
Evidence: `IRIS_ARCH.md` roadmap section: "### Batch 1C - Next" with the original full scope listed (sleep greeting, volume persistence, TTS hard-cap, config validation, safe temp files, LLM stream warning). Most of these are DONE. Only SPEAKER_VOLUME and Piper routing remain.
Priority: LOW
Complexity: LOW
Recommendation: Update IRIS_ARCH.md Batch 1C section to show completed items and list only what remains (SPEAKER_VOLUME). Bundle with ITEM-010 IRIS_ARCH.md docs pass.
Files involved: `IRIS_ARCH.md`
Resolved evidence: HANDOFF accurately reflects 1C status; IRIS_ARCH.md does not
Stale references: The entire "Batch 1C - Next" roadmap section in IRIS_ARCH.md
Needs live test: no
Suggested default decision: OPEN LOW

Human decision: UNDECIDED
Human notes:

---

### ITEM-045 — IRIS_ARCH.md Reboot Survival: Chatterbox Docker Claim

Area: Docs / Architecture
Current status: STALE / OBSOLETE
Evidence: `IRIS_ARCH.md:191,197`: "GandalfAI reboot: Chatterbox docker must be started manually" and "Chatterbox does not auto-start." If Kokoro is primary, this guidance should reference Kokoro's docker container, not Chatterbox's.
Priority: LOW
Complexity: LOW
Recommendation: Update to: "Kokoro TTS Docker must be started manually after GandalfAI reboot. Chatterbox Docker also required if rollback is needed." Bundle with ITEM-010 pass.
Files involved: `IRIS_ARCH.md`
Resolved evidence: N/A
Stale references: Lines 191, 197
Needs live test: no (but worth confirming which docker-compose services are Kokoro vs Chatterbox during a live session)
Suggested default decision: OPEN LOW

Human decision: UNDECIDED
Human notes:

---

## 9. Current Priority Recommendation

Ranked work order (do not start next item until current is verified):

### 1. Must Do Now — Docs Cleanup Pass (IRIS_ARCH.md + README.md + CLAUDE.md)

- **Why:** Multiple stale Chatterbox-primary references actively mislead future Claude Code sessions. PROG button instruction in README is incorrect for the enclosure-mounted Teensy. Eye count mismatch will cause confusion on any EYE:n web UI work.
- **Dependencies:** None. Read-only inventory → user approves items → docs patch.
- **Type:** Docs-only. No code. No deploy.
- **Items:** ITEM-010, ITEM-011, ITEM-012, ITEM-013, ITEM-014, ITEM-015, ITEM-016, ITEM-017, ITEM-044, ITEM-045.

### 2. Should Do Next — AMUSED Decision + Implementation or Removal

- **Why:** AMUSED is in the active modelfile but silently dropped by every code layer. This means the persona the LLM is trying to express is not reaching the face or LEDs. Either implement it cleanly or remove it from the modelfile — the current half-state is worse than either clean choice.
- **Dependencies:** User decision first (Section 11). If implementing: config.py, led.py, firmware reflash. If removing: one-line modelfile edit + GandalfAI `ollama create`.
- **Type:** Code + deploy (if implementing) OR modelfile edit + deploy (if removing).
- **Items:** ITEM-003, ITEM-022.

### 3. Should Do Next — stop Interrupt (Pre-STT Gate)

- **Why:** HIGH priority confirmed open issue. Single-word commands fail because Whisper hallucinates on sub-1s audio. The fix is a pre-STT RMS/duration gate — well-scoped, Pi4-only change, no firmware or GandalfAI changes.
- **Dependencies:** Live Pi4 test to measure RMS signature of "stop" utterances.
- **Type:** Code + deploy on Pi4. No firmware change.
- **Items:** ITEM-001.

### 4. Good But Optional — SPEAKER_VOLUME Live Test

- **Why:** Web UI already writes to iris_config.json and calls alsactl store. The question is whether iris_config.json and alsa state survive overlayfs reboot. A 5-minute live Pi4 test closes this.
- **Dependencies:** Pi4 SSH session. No code change likely needed — may just need confirmation.
- **Type:** Live test only.
- **Items:** ITEM-002.

### 5. Defer — Wakeword (okay_iris)

- **Why:** Model quality concern is significant. At production threshold, recall approaches 0%. Needs live score testing first, and config range validation changes before deployment. Not urgent — hey_jarvis is stable.
- **Dependencies:** Live Pi4 score test; user decision to proceed.
- **Type:** Test first, then code + deploy.
- **Items:** ITEM-004.

### 6. Remove / Abandon — ACK/NACK Serial, Piper Sleep Routing, WARM/SUPPORTIVE/CONCERNED

- **Why:** No demonstrated need for ACK/NACK. Piper sleep routing is edge-case at best. WARM/SUPPORTIVE/CONCERNED would each require full 4-layer implementation for marginal personality gain.
- **Dependencies:** User decision.
- **Type:** Roadmap update + modelfile cleanup only.
- **Items:** ITEM-023, ITEM-025, ITEM-022 (partial).

---

## 10. Proposed Simplified Roadmap

### Reliability

1. **stop interrupt** — pre-STT RMS/keyword gate; Pi4-only; HIGH priority
2. **SPEAKER_VOLUME** — live test to confirm persistence survives reboot; LOW effort

### Personality / Expression

3. **AMUSED decision** — implement fully (config + led + firmware) OR remove from modelfile; user decides
4. **GandalfAI model sync** — standing operational rule; no active task needed

### Hardware / Firmware (Batch 2 — only after Pi4 stable)

5. **Sleep render pointer guards** — defensive firmware hardening
6. **Serial overflow discard-and-log** — log instead of silent discard
7. **Gate mouth commands during sleep** — if still needed after live observation

### Docs / Status

8. **IRIS_ARCH.md + README.md + CLAUDE.md cleanup** — one pass, docs-only, no deploy
9. **SNAPSHOT_LATEST.md update to S45** — minor, next session
10. **IRIS_STATUS.json decision** — regenerate+commit or .gitignore

### User Decision (not active until decided)

- okay_iris wakeword — live score test first
- leopard/snake eyes — compile in or delete files

### Removed from Active Roadmap

- ACK/NACK serial protocol
- Piper sleep routing (as active task)
- WARM / SUPPORTIVE / CONCERNED emotion tags
- Public release prep (deferred until docs clean)

---

## 11. Items Requiring User Decision

### Decision Required — AMUSED: Implement Fully or Remove from Modelfile?

Related item ID: ITEM-003, ITEM-022
Question: AMUSED is in the modelfile and LLM will emit it. Currently silently mapped to NEUTRAL in all layers. Do you want to implement it as a real hardware emotion or remove it from the modelfile?
Default recommendation: IMPLEMENT if you want richer expression (requires led.py, config.py, firmware reflash). REMOVE if you want to minimize firmware churn (one modelfile line + GandalfAI ollama create).
Consequence if kept (as-is): LLM expresses AMUSED, face shows nothing different from NEUTRAL. Invisible behavior.
Consequence if removed: LLM won't emit AMUSED tag, so it will choose from remaining 8. Slightly limits persona expressiveness.
Consequence if implemented: IRIS face/LEDs respond distinctly to AMUSED. Requires firmware flash.

Human decision: UNDECIDED
Human notes:

---

### Decision Required — WARM/SUPPORTIVE/CONCERNED: Add or Remove?

Related item ID: ITEM-022
Question: These three emotion tags appear in some planning docs but are NOT in the modelfile or any code. Do you want them added to the active roadmap or removed permanently?
Default recommendation: REMOVE from roadmap. Each requires a full 4-layer implementation (modelfile + config + led + firmware). Diminishing returns at 11+ emotions.
Consequence if kept: Large scope emotion expansion task queued up.
Consequence if removed: IRIS stays at current 8 (+AMUSED if implemented) emotion set.

Human decision: UNDECIDED
Human notes:

---

### Decision Required — okay_iris Wakeword: Proceed or Archive?

Related item ID: ITEM-004
Question: The okay_iris model exists and a plan doc is written. But at OWW_THRESHOLD=0.90, recall is near 0%. The config range validator would need relaxing (0.5→0.1). A live score test on Pi4 is required before committing. Do you want to proceed with a live test, or archive this as experimental?
Default recommendation: Do a live score test session first before committing any files. Do not deploy blind.
Consequence if proceed: Live test needed on Pi4. May reveal the model is usable at 0.2 threshold (~87% recall, ~1 false wake/6h). Or may reveal it's not usable.
Consequence if archived: hey_jarvis remains production wakeword indefinitely.

Human decision: UNDECIDED
Human notes:

---

### Decision Required — Chatterbox Rollback References: Keep or Archive?

Related item ID: ITEM-024
Question: Chatterbox config constants remain in config.py (CHATTERBOX_ENABLED, CHATTERBOX_BASE_URL, etc.). IRIS_ARCH.md has a full Chatterbox parameters section. How much rollback capability do you want to maintain?
Default recommendation: Keep the constants in config.py (low overhead, real rollback value). Consolidate all IRIS_ARCH.md Chatterbox references to one "Rollback Reference" note. Remove active-architecture language.
Consequence if kept as-is: Ongoing doc confusion. Stale primary-TTS claims mislead future sessions.
Consequence if consolidated: Clean docs, rollback path still exists via config.py constants.
Consequence if removed entirely: Rollback to Chatterbox becomes harder (need to remember config values).

Human decision: UNDECIDED
Human notes:

---

### Decision Required — README Public Release Goal: Active or Defer?

Related item ID: ITEM-026
Question: README is written as a public release doc but has multiple inaccuracies (wrong Teensy version, wrong eye count, wrong flash instructions, wrong model name). Do you want to prioritize making the README accurate and release-ready, or defer until the project is more stable?
Default recommendation: Fix the factual errors now (simple, low-effort) as part of the docs pass. Defer demo content (video, photos) until later.
Consequence if deferred entirely: README remains inaccurate; confusing if shared publicly.
Consequence if errors fixed first: More accurate public facing docs; demo content can be added later.

Human decision: UNDECIDED
Human notes:

---

### Decision Required — Prioritize stop Interrupt Over Emotion Polish?

Related item ID: ITEM-001, ITEM-003
Question: Stop interrupt is HIGH priority functional issue. AMUSED implementation (if chosen) requires a firmware flash. Which comes first?
Default recommendation: stop interrupt first. It's Pi4-only, no firmware flash, and restores a broken voice command. AMUSED emotion is polish.
Consequence if stop first: Firmware unchanged while stop fix is tested. AMUSED stays NEUTRAL until next batch.
Consequence if AMUSED first: Requires firmware flash. stop fix still needed after.

Human decision: UNDECIDED
Human notes:

---

### Decision Required — IRIS_STATUS.json: Commit Regenerated Version or .gitignore?

Related item ID: ITEM-008, ITEM-043
Question: IRIS_STATUS.json is 11 commits stale and misleads session-start workflows. Options: (A) Run iris_status.ps1, commit the fresh output. (B) Add IRIS_STATUS.json to .gitignore so it's generated fresh each session and never committed.
Default recommendation: Option B (.gitignore). A committed JSON snapshot goes stale between sessions. Better to generate it at session start.
Consequence of option A: JSON accurate today; stale again next session unless regenerated every time.
Consequence of option B: File never in repo; must be generated before any workflow that reads it.

Human decision: UNDECIDED
Human notes:

---

### Decision Required — Large VALID_EMOTIONS Expansion: Keep or Simplify?

Related item ID: ITEM-022, ITEM-003
Question: Currently 8 hardware-supported emotions. AMUSED would make 9. WARM/SUPPORTIVE/CONCERNED would push toward 12. Each requires a full firmware flash + LED + config pass. Is the emotion set stable at 8, at 9 (add AMUSED), or do you want to plan a larger expansion?
Default recommendation: Stable at 9 (add AMUSED only if decided above). Remove WARM/SUPPORTIVE/CONCERNED from planning docs entirely.
Consequence if expanded to 12: Significant firmware work, multiple flashes. Mixed value.
Consequence if stable at 9: One clean firmware pass (if AMUSED chosen), then done.
Consequence if stable at 8: No firmware changes needed for emotion system.

Human decision: UNDECIDED
Human notes:

---

### Decision Required — ACK/NACK Serial Protocol: Keep or Remove?

Related item ID: ITEM-023
Question: Batch 2 currently includes "ACK/NACK protocol only if justified." No serial failure has been logged. This adds significant complexity to both firmware and TeensyBridge. Remove it from scope?
Default recommendation: REMOVE. No evidence of need. Add only if a real serial reliability failure occurs.
Consequence if removed: Batch 2 scope shrinks. Firmware changes are simpler.
Consequence if kept: Large bidirectional protocol work queued in Batch 2.

Human decision: UNDECIDED
Human notes:

---

### Decision Required — Piper Sleep Routing: Active Task or Archive?

Related item ID: ITEM-006, ITEM-025
Question: Piper sleep routing is listed as remaining Batch 1C work. Local Piper is broken; Wyoming Piper on GandalfAI works as fallback. With Kokoro as primary, this edge case (sleep/wake greeting) barely matters. Remove from active roadmap?
Default recommendation: REMOVE. The Wyoming Piper fallback path already works for the sleep greeting edge case.
Consequence if removed: Batch 1C fully closed. Local Piper broken state ignored until a real failure is reported.
Consequence if kept: Active task that requires Pi4 debugging of a low-value edge case.

Human decision: UNDECIDED
Human notes:

---

### Decision Required — Chatterbox Docs in Active Architecture: Consolidate or Remove?

Related item ID: ITEM-010, ITEM-024
Question: IRIS_ARCH.md has a full "Chatterbox Parameters (Baseline)" section with reference audio paths, speed_factor, temperature values. Is this rollback-critical enough to keep in IRIS_ARCH.md, or move to a rollback-only note?
Default recommendation: Keep parameters in a single "Rollback Reference" block. Remove from pipeline descriptions and status tables.
Consequence if kept as-is: Ongoing confusion — every new session reads Chatterbox as primary.
Consequence if consolidated: One clean rollback note; main architecture shows Kokoro.

Human decision: UNDECIDED
Human notes:

---

### Decision Required — docs/wakeword_import_plan_okay_iris.md: Keep as Pending Plan or Archive?

Related item ID: ITEM-004
Question: This is an untracked file with a detailed implementation plan for okay_iris. It documents a known quality concern. Commit it as a reference doc, or archive/delete it?
Default recommendation: Commit it (it's already written and informative). Add it to the repo as a design document whether or not the wakeword is pursued.
Consequence if committed: Clean repo, plan preserved.
Consequence if deleted: Context lost if wakeword is revisited.

Human decision: UNDECIDED
Human notes:

---

### Decision Required — assistant.py Chatterbox Wording: Comment-Only or Also Verify Runtime Labels?

Related item ID: ITEM-018, ITEM-019
Question: assistant.py line 7 has a stale docstring (TTS: Chatterbox primary). Line 664 has a bench label that checks CHATTERBOX_ENABLED to name the TTS engine (always says "chatterbox" since that flag defaults True). Fix only the comment, or also fix the runtime bench label logic?
Default recommendation: Fix both. The bench label (line 664) produces incorrect data in the Bench tab — it's not just a comment.
Consequence if comment-only: Bench tab continues showing "chatterbox" as TTS mode when Kokoro is running.
Consequence if both fixed: Accurate Bench tab labeling.

Human decision: UNDECIDED
Human notes:

---

### Decision Required — leopard/snake Eye .h Files: Compile Into Firmware or Delete?

Related item ID: ITEM-021, ITEM-014
Question: leopard.h and snake.h exist in src/eyes/240x240/ but are not compiled. README says they're at indices 5 and 6 (incorrect — those are dragon and bigBlue). Do you want to add them to the firmware (9-eye system), or delete the unused files?
Default recommendation: User decides. Adding them creates a 9-eye system requiring a reflash. Deleting them keeps the 7-eye system clean. Either way README must be corrected.
Consequence if compiled in: 9 eyes (0–8), EYE:7=leopard, EYE:8=snake possible but indices shift. Firmware flash required.
Consequence if deleted: 7-eye system, src is clean, README corrected to match.

Human decision: UNDECIDED
Human notes:

---

## 12. Recommended Next Claude Code Prompt

Use this prompt after you have edited the Human decision lines above and saved this file:

---

```
Read C:\Users\SuperMaster\Desktop\IRIS_ITEMIZED_INVENTORY_2026-05-02.md

This is an inventory of IRIS issues, stale docs, and pending work. I have edited the "Human decision:" lines with my decisions. Apply the approved decisions as a docs-only cleanup patch.

Rules for this session:
- Read the inventory file first. Treat every "Human decision:" line as authoritative.
- Apply only DOCS-ONLY changes. Do not change Pi4 Python code. Do not change firmware. Do not deploy anything.
- Target files for docs cleanup: IRIS_ARCH.md, README.md, CLAUDE.md (project), SNAPSHOT_LATEST.md. Also update assistant.py and tts.py comment lines if those items were approved.
- Show the full list of files you will edit before touching anything.
- After listing files: read each file in full before editing.
- After edits: show git diff --stat.
- Stop before commit. Wait for my go-ahead.
- Do not open SSH. Do not touch Pi4 or GandalfAI files.
- Do not touch iris_config.json, alsa-init.sh, TeensyEyes.ino, EyeController.h.

Do a pre-flight first:
- git status
- git branch --show-current
- git log --oneline -3
```

---

*End of IRIS_ITEMIZED_INVENTORY_2026-05-02.md*

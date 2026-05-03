# IRIS Full Local Repo Truth Audit
**Date:** 2026-05-02 | **Auditor:** Claude Code (read-only) | **Repo:** `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face`

---

## 1. Git / Repo State

| Field | Value |
|---|---|
| Repo path | `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face` |
| Branch | `main` |
| Last commit | `103cbcc` — S45: add docs/iris_issue_log.md -- structured issue/fix history S1-S44 |
| Working tree | Dirty (1 untracked file) |
| Dirty tracked files | None |
| Untracked files | `docs/wakeword_import_plan_okay_iris.md` |
| IRIS_STATUS.json timestamp | `2026-04-25 18:50:57` (generated at S34 era, commit `826cd72`) |
| IRIS_STATUS.json status | **EXTREMELY STALE** — 11 commits behind; references untracked files that have since been committed; Pi4 state skipped |

**Immediate concerns:**
- IRIS_STATUS.json is 11 commits behind (S34 → S45). Any session that reads it will see stale commit hash, wrong dirty/untracked state, and no Pi4 info. The PRIMER instructs running `iris_status.ps1` before sessions, but the stored JSON was not regenerated.
- SNAPSHOT_LATEST.md references S44 as the last session; actual last commit is S45.

---

## 2. Confidence Statement

**Verdict: Mostly current with significant doc drift.**

Pi4 Python code (assistant.py, intent_router.py, config.py, tts.py, llm.py) is clean and current. The firmware (config.h, main.cpp) matches IRIS_ARCH.md on eye count. The primary issue is stale prose in IRIS_ARCH.md (Chatterbox references, old key constants, stale service description), README.md (Teensy 4.0, wrong eye table), and a silent functional gap (AMUSED emotion not wired through the full pipeline).

---

## 3. Evidence Priority Used

1. Live local repo files (Read tool, direct inspection)
2. Local git status/log (Bash tool)
3. IRIS_STATUS.json (stale, not used for state claims)
4. HANDOFF_CURRENT.md + SNAPSHOT_LATEST.md (cross-referenced against code)
5. Older historical docs used only to identify contradictions

---

## 4. Current Truth Table

| # | Claim | Local repo evidence | Docs claim | Code confirms? | Status | Risk | Recommended action |
|---|---|---|---|---|---|---|---|
| 1 | Latest session is S44 | Last commit is `103cbcc` S45 | SNAPSHOT says S44 | No — S45 is newer | STALE | Low (doc only) | Update SNAPSHOT_LATEST.md to S45 |
| 2 | Latest commit is 35d01ba | `git log` shows `103cbcc` | SNAPSHOT says `35d01ba` | No | STALE | Low (doc only) | Update SNAPSHOT_LATEST.md |
| 3 | Kokoro is primary TTS | `tts.py` synthesize() calls `_synthesize_kokoro` first | HANDOFF, tts-history.md, IRIS_CONFIG_MAP.md all confirm | YES | CONFIRMED CURRENT | None | None |
| 4 | Chatterbox is rollback only | `config.py` comment: "rollback only — Kokoro is primary since S38"; `IRIS_CONFIG_MAP.md` Chatterbox section labeled "Rollback only" | Confirmed in IRIS_CONFIG_MAP.md | YES | CONFIRMED CURRENT | None | None |
| 5 | Piper is fallback | `tts.py`: Kokoro failure → `_synthesize_piper()`; sleep phrases route direct to Piper | All current docs | YES | CONFIRMED CURRENT | None | None |
| 6 | Ollama models are iris / iris-kids | `config.py`: OLLAMA_MODEL_ADULT="iris", OLLAMA_MODEL_KIDS="iris-kids" | All docs agree | YES | CONFIRMED CURRENT | None | None |
| 7 | Base model is gemma3:27b-it-qat | `ollama/iris_modelfile.txt`: `FROM gemma3:27b-it-qat` | HANDOFF, SNAPSHOT confirm. README says "gemma3:27b" (missing "-it-qat") | YES (code) / PARTIAL (README) | CONFIRMED CURRENT (code stale in README) | None | README: update "gemma3:27b" → "gemma3:27b-it-qat" |
| 8 | Dynamic response-length classification exists | `llm.py`: `classify_response_length()` function; `assistant.py` calls it with `_num_predict = classify_response_length(text)` | HANDOFF confirms Batch 1C | YES | CONFIRMED CURRENT | None | None |
| 9 | Intent router integrated in assistant.py | `assistant.py` imports `IntentRouter`; `router.classify(text, state)` call at line 491; 5 route branches all present | HANDOFF Batch 3-F | YES | CONFIRMED CURRENT | None | None |
| 10 | RANDOM_NUMBER local route exists | `intent_router.py` Layer 2: `_RANDOM_RE` pattern + `_random_number_reply()` + `IntentResult(ROUTE_UTILITY, "RANDOM_NUMBER", ...)` | HANDOFF S44, issue log | YES | CONFIRMED CURRENT | None | None |
| 11 | Web UI logs include intent routing logs | `iris_web.py` line 147: opens `/home/pi/logs/iris_intent.log` in `/api/logs` | HANDOFF S44, issue log | YES | CONFIRMED CURRENT | None | None |
| 12 | Follow-up short-reply bug fixed | `assistant.py` follow-up loop: `if _text_norm in _WHISPER_HALLUCINATIONS: break` replaces old `< 3 words` gate | Issue log S44 | YES | CONFIRMED CURRENT | None | None |
| 13 | Single-word "stop" STT failure open | Issue log: "open | HIGH" entry with pre-STT fix proposal; no implementation found in current code | SNAPSHOT active issues, issue log | YES (still open) | OPEN | Med — users cannot reliably stop playback with voice | Next work item |
| 14 | SPEAKER_VOLUME persistence open | `config.py`: SPEAKER_VOLUME=121 set at startup but no write-back on change via amixer; issue log confirms | Issue log, SNAPSHOT | YES (still open) | OPEN | Low — volume resets on reboot | Batch 1C remainder |
| 15 | Piper sleep routing low priority/deferred | `tts.py`: `_PIPER_DIRECT_PHRASES` sends sleep phrases to Piper directly (hardcoded bypass of Kokoro) — confirms Piper is used for sleep path regardless. Local Piper may be broken on Pi4. | Issue log: "Deferred — LOW-LOW" | YES | OPEN (deferred) | Low | None needed |
| 16 | Batch 1A complete | HANDOFF says complete; OWW retry/backoff, restart, socket timeout all in assistant.py | HANDOFF, issue log | YES | DONE | None | None |
| 17 | Batch 1B complete | HANDOFF says complete; canonical _do_sleep()/_do_wake() in assistant.py, UDP routing, iris_wake.py | HANDOFF, issue log | YES | DONE | None | None |
| 18 | Batch 1C mostly complete | SPEAKER_VOLUME and Piper sleep routing still open; all other items confirmed in code | HANDOFF | YES | PARTIAL | Low | Batch 1C remainder after stop-word fix |
| 19 | Batch 2 Teensy pass not current | HANDOFF: "Only after Pi runtime remains stable"; no Teensy work in recent commits | HANDOFF | YES | CONFIRMED CURRENT | None | None |
| 20 | Batch 3-F intent router closed/live | `intent_router.py` deployed; `assistant.py` integrated; HANDOFF S42 closed it | HANDOFF | YES | DONE | None | None |
| 21 | Teensy 4.1 canonical | `platformio.ini`: `board = teensy41`; IRIS_ARCH confirms; main.cpp constants correct for T4.1 | IRIS_ARCH, AGENTS.md | YES | CONFIRMED CURRENT | None | README still says "4.0" |
| 22 | README has stale Teensy 4.0 reference | `README.md` Hardware table: "Teensy 4.1 \| Dual GC9A01A eyes + ILI9341 2.8" TFT mouth" — WAIT, the body says Teensy 4.1 correctly in most places but the hardware table says "Teensy 4.1" — rechecked: the hardware table in README says "Teensy 4.1 \| Dual GC9A01A eyes + ILI9341 2.8" TFT mouth". The original eye system description says "Teensy 4.0" in the eye system section header. | README eye section | PARTIAL | CONTRADICTORY | Low | README eye section says "Teensy 4.x" in credit line but later says "Teensy 4.0" implicitly |
| 23 | Eye count consistent between code and docs | `config.h`/`main.cpp`: 7 eyes (0–6: nordicBlue/flame/hypnoRed/hazel/blueFlame1/dragon/bigBlue). `IRIS_ARCH.md` eye index map: 7 eyes (0–6) — MATCHES. README.md eye table: 9 eyes (0–8) with leopard=5, snake=6, dragon=7, bigBlue=8 — DOES NOT MATCH firmware. README is wrong. | README vs config.h/IRIS_ARCH | NO (README contradicts firmware) | CONTRADICTORY | Med — README is public; external readers/future sessions may use wrong indices | Update README eye table |
| 24 | Mouth pinout consistent | IRIS_ARCH.md: SPI2 hw (35 MOSI, 37 SCK, 36 CS, 8 DC, 4 RST, 5 BL). README says "pins 5/6/7" (legacy MAX7219 notation, noted as SWSPI) — MAX7219 was removed. IRIS_ARCH is authoritative; README mouth section is stale. | IRIS_ARCH vs README | IRIS_ARCH confirmed | CONTRADICTORY | Low (operational clarity) | Update README mouth section |
| 25 | Pi4 persistence = direct /media/root-ro only | CLAUDE.md, HANDOFF_CURRENT.md, IRIS_ARCH.md all state this consistently | All current docs | YES | CONFIRMED CURRENT | None | None |
| 26 | overlayroot-chroot marked not to use unless re-verified | IRIS_ARCH: "Do not use overlayroot-chroot unless independently verified." Reason documented (md5 mismatch). | IRIS_ARCH, CLAUDE.md | YES | CONFIRMED CURRENT | None | None |
| 27 | GitHub is secondary mirror only | All docs agree: local repo is #1 source of truth | CLAUDE.md, HANDOFF, IRIS_ARCH | YES | CONFIRMED CURRENT | None | None |
| 28 | IRIS_STATUS.json current | JSON file: generated 2026-04-25, commit 826cd72 (S34). Actual latest: 103cbcc (S45). 11 commits stale. | Script exists | NO | STALE | Low (workflow) | Run iris_status.ps1 at session start |
| 29 | PRIMER includes iris_status.ps1 in pre-flight output | PRIMER.md pre-flight format does NOT include iris_status.ps1 results in the required output items. The Notes section says "run: .\scripts\iris_status.ps1" but the pre-flight output format doesn't ask for the result. | PRIMER.md | PARTIAL | PARTIAL | Low | Add iris_status.ps1 result to PRIMER pre-flight format |
| 30 | CLAUDE.md reflects current TTS/model reality | CLAUDE.md environment table lists GandalfAI role as "Ollama, Whisper, Piper, Chatterbox, RTX 3090" — Chatterbox is listed but is rollback-only since S38. Not flagrant but slightly stale. | CLAUDE.md | PARTIAL | STALE | Low | Update CLAUDE.md GandalfAI role entry |
| 31 | README is public-facing, not operational authority | Correct by design. PRIMER.md, CLAUDE.md, and HANDOFF all establish local repo docs as operational truth. | PRIMER.md, CLAUDE.md | YES | CONFIRMED CURRENT | None | None |
| 32 | wakeword_import_plan_okay_iris.md is pending plan only, not deployed | File header: "Status: Review only — no files written". No `pi4/wakewords/` directory exists. No config.py changes made. | docs/wakeword_import_plan | YES | CONFIRMED (not deployed) | Low | Commit this doc when wakeword work begins |
| 33 | Issue log exists and matches code/docs | `docs/iris_issue_log.md` exists (committed S45). Entries match HANDOFF and SNAPSHOT well. Open issues match active issue sections. | All docs | YES | CONFIRMED CURRENT | None | Minor: iris_issue_log omits the Chatterbox→Kokoro migration as a "fixed" item |

---

## 5. Fixes Confirmed Saved in Local Repo

| Fix | Evidence file | Commit | Status | Docs updated |
|---|---|---|---|---|
| OWW startup retry/backoff/restart | `pi4/assistant.py` | `078da91` | Committed | YES |
| Canonical _do_sleep() / _do_wake() | `pi4/assistant.py` | `075d098` | Committed | YES |
| Intent router (5-layer) | `pi4/core/intent_router.py` | `c37623e` | Committed | YES |
| RANDOM_NUMBER UTILITY handler | `pi4/core/intent_router.py`, `pi4/services/llm.py` | `35d01ba` | Committed | YES |
| Follow-up hallucination fix (_WHISPER_HALLUCINATIONS) | `pi4/assistant.py` | `35d01ba` | Committed | YES |
| Web UI intent log in /api/logs | `pi4/iris_web.py` | `35d01ba` | Committed | YES |
| spoken_numbers() thousands/millions | `pi4/services/tts.py` | `39247b4` | Committed | YES |
| Kokoro primary TTS | `pi4/services/tts.py`, `pi4/core/config.py` | `e9bdffa` | Committed | YES |
| gemma3:27b-it-qat model upgrade | `ollama/iris_modelfile.txt` | `ec2ad32` | Committed | YES |
| Eye movement suspended during TTS | `src/main.cpp` | `c27517a` | Committed | YES |
| hey_jarvis wakeword baseline | `pi4/core/config.py` | `8c107bc` | Committed | YES |
| Response-length tier system | `pi4/services/llm.py` | `a51a97e` | Committed | YES |
| AMUSED persona tag in modelfile | `ollama/iris_modelfile.txt` | `4b242d0` | Committed | YES (but pipeline incomplete — see section 6) |
| iris_issue_log.md created | `docs/iris_issue_log.md` | `103cbcc` | Committed | N/A |
| OWW --threshold arg wired | `pi4/assistant.py` | `e01f769` | Committed | YES |
| SLEEP handler in intent router Layer 0 | `pi4/core/intent_router.py` | `c37623e` | Committed | YES (S42 audit concern resolved) |

---

## 6. Fixes Claimed by Docs but Not Confirmed in Code

| Claim | Location | Issue |
|---|---|---|
| AMUSED emotion fully wired | `ollama/iris_modelfile.txt` (EMOTION TAGS section says AMUSED valid); HANDOFF "Batch 3-D persona full pass -- AMUSED tag" | `config.py` VALID_EMOTIONS = {"NEUTRAL","HAPPY","CURIOUS","ANGRY","SLEEPY","SURPRISED","SAD","CONFUSED"} — AMUSED absent. `llm.py:extract_emotion_from_reply()` returns NEUTRAL if tag not in VALID_EMOTIONS. Firmware `main.cpp` EmotionID enum has no AMUSED entry. LLM will emit [EMOTION:AMUSED] but Pi4 silently downgrades it to NEUTRAL. No LED, eye, or mouth behavior differs for AMUSED. |
| "Vision prompt behavior (NEXT)" from Batch 3 | HANDOFF says "Vision prompt behavior (NEXT)" after Batch 3-E | Batch 3-E vision prompt was listed as "NEXT" pre-S42, then S42/S43/S44 happened. Not clear if vision behavior has been re-reviewed or if it's still pending. Status unclear from local repo alone. |

---

## 7. Open Issues Confirmed by Local Repo

| Issue | File evidence | Priority | Notes |
|---|---|---|---|
| Single-word "stop" STT failure | `docs/iris_issue_log.md` open section; `S42_LOG_AUDIT.md` documents STT-verified interrupt plan; no implementation in `hardware/audio_io.py` | HIGH | S42 audit documented the fix plan (STT-verified interrupt); not yet implemented |
| SPEAKER_VOLUME persistence on reboot | `pi4/core/config.py`: startup applies SPEAKER_VOLUME but no write-back on change; issue log open | MED | Batch 1C remainder |
| Piper sleep routing (local Piper broken) | `pi4/services/tts.py` _PIPER_DIRECT_PHRASES bypasses Kokoro for sleep phrases; if Pi4 local Piper is broken the fallback hits GandalfAI Wyoming Piper | LOW-LOW (deferred) | Not worth fixing until Kokoro primary fails |
| AMUSED emotion unimplemented in pipeline | `config.py` VALID_EMOTIONS; `llm.py` extract_emotion_from_reply(); `main.cpp` EmotionID enum | MED | Silent degradation — AMUSED → NEUTRAL. Modelfile says AMUSED valid but Pi4 doesn't honor it |
| Root-level stale sleep log | Not verifiable without SSH to Pi4 | LOW | `/home/pi/iris_sleep.log` may duplicate `/home/pi/logs/iris_sleep.log` |
| GandalfAI model sync operational hazard | `project_gandalf_modelfile_sync.md` memory; issue log | STANDING RULE | Not a code fix; operator procedure |
| IRIS_STATUS.json stale (11 commits) | IRIS_STATUS.json timestamp vs git log | LOW (workflow) | Run iris_status.ps1 before each session |

---

## 8. Open / Resolved / Pending Issue Log Assessment

**File:** `docs/iris_issue_log.md` (committed S45, `103cbcc`)

**Assessment: MOSTLY ACCURATE — minor gaps**

- All resolved issues listed match actual code evidence in this audit.
- Open issues match SNAPSHOT_LATEST.md and HANDOFF_CURRENT.md.
- **Gap 1:** The AMUSED pipeline issue is not documented in the issue log. It was shipped as "Batch 3-D persona full pass -- AMUSED tag" but the tag is unimplemented in the Pi4 pipeline. This should be an open issue.
- **Gap 2:** No entry for the S42_LOG_AUDIT.md STT-verified interrupt plan. The plan was documented and the code was NOT implemented. The open issue entry for "stop" mentions the proposed fix (pre-STT RMS duration gate) but the S42 audit proposed a more specific approach (STT-verified interrupt via `hardware/audio_io.py`). Minor discrepancy in fix description.
- **Cross-reference:** iris_issue_log.md matches HANDOFF_CURRENT.md well. The only HANDOFF item not in the issue log is the Chatterbox→Kokoro migration (not a bug, so omission is appropriate).

---

## 9. Stale Data to Remove or Rewrite

| File | Stale claim | What it should say |
|---|---|---|
| `IRIS_ARCH.md` (line ~98) | "Pi4 requests Chatterbox primary or Piper fallback" in Current High-Level Pipeline | "Pi4 requests Kokoro TTS (GandalfAI, port 8004) / Piper fallback (port 10200)" |
| `IRIS_ARCH.md` (System Roles table) | GandalfAI role: "Chatterbox TTS" | "Kokoro TTS, Chatterbox rollback" |
| `IRIS_ARCH.md` (System Status table) | "STT -> LLM -> TTS -> audio output WORKING: Whisper->Ollama iris->Chatterbox->speakers" | Remove Chatterbox from this line; update to Kokoro |
| `IRIS_ARCH.md` (Repo Structure section) | `services/tts.py -- Chatterbox->Piper only (ElevenLabs removed S20)` | `services/tts.py -- Kokoro primary, Piper fallback` |
| `IRIS_ARCH.md` (Repo Structure section) | `ollama/iris_modelfile.txt -- adult IRIS persona (gemma3:12b) -- canonical` | `ollama/iris_modelfile.txt -- adult IRIS persona (gemma3:27b-it-qat) -- canonical` |
| `IRIS_ARCH.md` (Key Constants section) | Entire section marked "as of S20" with CHATTERBOX_BASE_URL, etc. | Remove or replace with reference to IRIS_CONFIG_MAP.md |
| `IRIS_ARCH.md` (GandalfAI File Layout) | Chatterbox docker directories as active | Mark Chatterbox as rollback-only; note Kokoro Docker as primary |
| `README.md` (Hardware table) | "Teensy 4.0" in one reference | "Teensy 4.1" — matches firmware, IRIS_ARCH, and everywhere else |
| `README.md` (Eye System section) | 9 eyes: 5=leopard, 6=snake, 7=dragon, 8=bigBlue | 7 eyes: 5=dragon, 6=bigBlue. Remove leopard and snake. Match config.h exactly. |
| `README.md` (Building section) | "Then press PROG button on Teensy to complete flash" | Remove PROG button instruction. Teensy is enclosure-mounted; PROG not accessible. Flash completes via PlatformIO upload only. |
| `README.md` (LLM section) | "Ollama `gemma3:27b`" | "Ollama `gemma3:27b-it-qat`" |
| `README.md` (Mouth Display section) | Pins listed as "pins 5/6/7" (MAX7219 legacy) | Update to reflect actual ILI9341 SPI2 hw pin map (per IRIS_ARCH.md) |
| `assistant.py` (line 7 docstring) | "TTS: Chatterbox @ 192.168.1.3:8004 (primary)" | "TTS: Kokoro @ 192.168.1.3:8004 (primary)" |
| `assistant.py` (line 664) | `_tts_eng = "chatterbox" if CHATTERBOX_ENABLED else "piper"` | `_tts_eng = "kokoro" if KOKORO_ENABLED else "piper"` |
| `services/tts.py` (_truncate_for_tts docstring) | "Cap TTS input at max_chars to bound Chatterbox generation time." | "...to bound Kokoro generation time." |
| `CLAUDE.md` (environment table) | GandalfAI: "Ollama, Whisper, Piper, Chatterbox, RTX 3090 inference" | "Ollama, Whisper, Kokoro TTS, Piper fallback, RTX 3090 inference" |
| `IRIS_CONFIG_MAP.md` (line ~168) | "num_ctx \| ≤4096 \| Hard limit — RTX 3090 with Chatterbox loaded leaves <4GB headroom" | "...with Kokoro loaded (~2GB) leaves ~7.9GB headroom" |
| `IRIS_STATUS.json` | Commit `826cd72` (S34), generated 2026-04-25 | Run `.\scripts\iris_status.ps1` to regenerate |
| `SNAPSHOT_LATEST.md` | S44 / commit `35d01ba` | Update to S45 / `103cbcc`; add iris_issue_log.md to last session changes |

---

## 10. Contradictions Between Docs

| Doc A | Doc B | Contradiction |
|---|---|---|
| `IRIS_ARCH.md` (Key Constants: EYE_IDX_COUNT=7, 0–6) | `README.md` (Eye System: 9 eyes, 0–8 including leopard and snake) | README shows 9 eyes; firmware has 7. README indices for dragon and bigBlue are wrong (README: 7/8, actual: 5/6). |
| `README.md` sleep: "7:30 AM -- Full assistant resumes" | `config.py` SLEEP_WINDOW_END_HOUR=8 | Cron fires iris_wake.py at 7:30 AM. Window check in assistant.py uses 8 AM. Not truly contradictory but potentially confusing — README describes the cron; config.py controls the return-to-sleep window. |
| `HANDOFF_CURRENT.md` (Batch 3-F: "Loop 3: Pi4 live) pending") | `HANDOFF_CURRENT.md` (later: "Batch 3-F: CLOSED (S42). Router live on Pi4, model rebuilt") | First entry is pre-close draft not cleaned up; second entry is the definitive close. Both in same file. Minor internal inconsistency. |
| `SNAPSHOT_LATEST.md` (S44, commit 35d01ba) | `git log` (last commit 103cbcc S45) | Snapshot not updated after S45 commit. |

---

## 11. Contradictions Between Docs and Code

| Doc claim | Code reality | File |
|---|---|---|
| AMUSED emotion "wired" (Batch 3-D docs, modelfile) | `config.py` VALID_EMOTIONS excludes AMUSED. `llm.py` silently downgrades to NEUTRAL. `main.cpp` EmotionID has no AMUSED. | `pi4/core/config.py`, `pi4/services/llm.py`, `src/main.cpp` |
| IRIS_ARCH.md: "services/tts.py -- Chatterbox->Piper only" | `tts.py` is Kokoro primary, Piper fallback. No Chatterbox calls in synthesize(). | `pi4/services/tts.py` |
| IRIS_ARCH.md: "ollama/iris_modelfile.txt -- adult IRIS persona (gemma3:12b)" | Modelfile: `FROM gemma3:27b-it-qat` | `ollama/iris_modelfile.txt` |
| `assistant.py` docstring line 7: "TTS: Chatterbox @ 192.168.1.3:8004 (primary)" | `tts.py` synthesize() uses Kokoro as primary. Chatterbox path removed. | `pi4/assistant.py` |
| `assistant.py` line 664 bench log: `_tts_eng = "chatterbox" if CHATTERBOX_ENABLED else "piper"` | CHATTERBOX_ENABLED=True but Kokoro is the actual engine. Log will say "chatterbox" while Kokoro is running. | `pi4/assistant.py` |
| `IRIS_CONFIG_MAP.md` line ~197: "Custom model dir \| assistant.py:334" | Line 334 in current assistant.py is `router = IntentRouter()`. Custom model dir is not in assistant.py at all (not implemented). | `pi4/assistant.py`, `IRIS_CONFIG_MAP.md` |
| README.md eye table: 9 eyes with leopard (5) and snake (6) | config.h: 7 eyes. Leopard and snake not compiled in. EYE:5=dragon, EYE:6=bigBlue. | `src/config.h`, `src/main.cpp` |
| README.md: "Then press PROG button on Teensy to complete flash" | IRIS_ARCH.md: "Teensy is enclosure-mounted. RESET and PROG buttons are NOT accessible." | `README.md`, `IRIS_ARCH.md` |

---

## 12. Untracked / Dirty Files Assessment

| File | Category | Why it exists | Referenced? | Recommended action | Risk if removed |
|---|---|---|---|---|---|
| `docs/wakeword_import_plan_okay_iris.md` | Likely important current work | Planning doc for okay_iris custom wakeword import. Written S44 prep, not yet executed. Header: "Review only — no files written." | Not in SNAPSHOT or HANDOFF but is coherent forward work | Keep and commit when wakeword work begins | MED — contains CRITICAL threshold analysis: at OWW_THRESHOLD=0.90, model has ~0% recall. Operative window is 0.2–0.3. Config range validator needs relaxing. Losing this analysis = rediscovering at deploy time. |

No dirty tracked files. Working tree otherwise clean.

---

## 13. Unknowns That Require Live Hardware or Service Checks

| Unknown | Why it cannot be answered from repo | Priority |
|---|---|---|
| Is Kokoro Docker container running on GandalfAI? | Requires SSH to GandalfAI or live test | MED — required before any TTS session |
| Is iris Ollama model current on GandalfAI? | `ollama show iris --modelfile` required on GandalfAI | HIGH — memory `project_gandalf_modelfile_sync.md` warns of 3-way desync hazard |
| Is iris-kids current on GandalfAI? | Same as above | MED |
| Is Pi4 assistant.service running? | Requires SSH or IRIS_STATUS.json regeneration | MED |
| Is the local Piper binary at /usr/local/bin/piper on Pi4 broken? | SSH to Pi4 required | LOW-LOW (deferred) |
| Root-level iris_sleep.log duplication on Pi4 | SSH ls /home/pi/ required | LOW |
| SPEAKER_VOLUME current value on Pi4 | iris_config.json on Pi4 RAM layer may differ from repo | LOW |
| Pi4 iris_config.json exact contents (live) | NEEDS LIVE TEST — on-disk config may differ from repo defaults | LOW |
| Chatterbox Docker container state (rollback availability) | SSH to GandalfAI required | LOW |

---

## 14. Recommended Next Actions

### Batch A — Docs-only cleanup (no deploy, no code, local repo edits only)

**Files touched:** SNAPSHOT_LATEST.md, IRIS_ARCH.md, README.md, CLAUDE.md, IRIS_CONFIG_MAP.md, assistant.py (2-line comment fix), services/tts.py (1-line comment fix), docs/iris_issue_log.md (1 entry)
**Risk:** Docs only. Zero functional change. Fully reversible with `git revert`.
**Rollback:** `git revert HEAD` undoes the commit.
**DEPLOY required:** NO.

Items:
1. Update SNAPSHOT_LATEST.md to S45 (commit `103cbcc`, add iris_issue_log.md to last session changes)
2. `IRIS_ARCH.md`: Replace all Chatterbox-as-primary references with Kokoro-as-primary. Update GandalfAI role in System Roles table. Remove or replace "Key Constants as of S20" section with pointer to IRIS_CONFIG_MAP.md. Update Repo Structure tts.py description. Update ollama modelfile description from gemma3:12b to gemma3:27b-it-qat.
3. `README.md`: Fix eye table (7 eyes, correct indices). Fix Teensy version (one stale "4.0" in the eye/building sections). Remove PROG button instruction. Fix LLM model name to "gemma3:27b-it-qat". Fix mouth pin description.
4. `CLAUDE.md` environment table: GandalfAI role "Kokoro TTS, Chatterbox rollback" (drop Chatterbox from primary).
5. `IRIS_CONFIG_MAP.md`: Fix VRAM note (Chatterbox → Kokoro). Fix assistant.py line number for custom model dir (or remove stale reference).
6. `assistant.py` line 7 docstring: "Chatterbox" → "Kokoro".
7. `assistant.py` line 664: `"chatterbox" if CHATTERBOX_ENABLED` → `"kokoro" if KOKORO_ENABLED`.
8. `services/tts.py` `_truncate_for_tts` docstring: "Chatterbox" → "Kokoro".
9. `docs/iris_issue_log.md`: Add open issue entry for AMUSED emotion pipeline gap.
10. Commit `docs/wakeword_import_plan_okay_iris.md` as pending plan (if user agrees).

---

### Batch B — Status script / generated artifact cleanup

**Files touched:** IRIS_STATUS.json (regenerated by script, not edited directly)
**Risk:** Low. Script reads live Pi4 (or use -SkipPi4).
**Rollback:** Not applicable (JSON is generated).
**DEPLOY required:** NO.

Items:
1. Run `.\scripts\iris_status.ps1` to regenerate IRIS_STATUS.json for S45 state.
2. Add iris_status.ps1 result summary to PRIMER.md pre-flight output format (5-line change).

---

### Batch C — Actual functional bug fixes

**Files touched:** `pi4/core/config.py`, `src/main.cpp` (possibly)
**Risk:** MED for AMUSED fix (requires modelfile + config.py + possibly firmware). LOW for other items.
**Rollback:** `git revert` on each commit.
**DEPLOY required:** YES (Pi4 for config.py change; GandalfAI for ollama create if modelfile changes).

Items:
1. **AMUSED pipeline fix:** Add `"AMUSED"` to `VALID_EMOTIONS` in `config.py`. Add AMUSED entry to `MOUTH_MAP` (use CURIOUS mouth=2 or create new mapping). Add LED behavior for AMUSED in `hardware/led.py`. Optionally: add AMUSED to `main.cpp` EmotionID enum with appropriate eye params (or treat as NEUTRAL at firmware level). This is the minimum: config.py + led.py. Firmware change is optional (AMUSED would reuse NEUTRAL eye params unless explicitly added).
2. **STT-verified interrupt (stop word fix):** As documented in S42_LOG_AUDIT.md — add pre-STT keyword check in `hardware/audio_io.py`. This is the highest-priority open functional issue.
3. **SPEAKER_VOLUME persistence:** Persist SPEAKER_VOLUME to iris_config.json on every volume change, ensure ALSA state is written to SD layer. Batch 1C remainder.

---

### Batch D — Hardware / live validation

**DEPLOY required:** YES (SSH to Pi4 / GandalfAI).

Items:
1. Verify GandalfAI iris model matches `ollama/iris_modelfile.txt` (run `ollama show iris --modelfile` and diff).
2. Verify Pi4 assistant.service is active and running latest deployed code.
3. Verify iris_intent.log rotation is working.
4. Check /home/pi/iris_sleep.log vs /home/pi/logs/iris_sleep.log duplication.
5. Confirm SPEAKER_VOLUME current value matches iris_config.json on Pi4.

---

### Batch E — Public release / credential scrub

**Risk:** HIGH if done wrong (would affect GitHub history).
**DEPLOY required:** NO (local repo / GitHub).

Items:
1. README.md is the public-facing document. After Batch A cleanup, it should be reviewed for accuracy before any public promotion.
2. IRIS_ARCH.md has `<password>` redacted in credential fields — already clean. Verify no credential leak in any file.
3. S41 credential scrub was already done (commit `4af3c15`). No new credentials found in this audit.

---

## 15. Follow-up Prompt for Batch A (docs-only cleanup)

Use this prompt after user approves:

```
IRIS Batch A — Docs-only cleanup. READ ONLY until diff shown, then wait for approval before writing.

Repo: C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face
Branch: main (verify first)
Working tree: must be clean except for docs/wakeword_import_plan_okay_iris.md untracked

Task: Apply docs-only corrections confirmed in the 2026-05-02 full truth audit.
No functional changes. Touch only these files:
- SNAPSHOT_LATEST.md
- IRIS_ARCH.md
- README.md
- CLAUDE.md
- IRIS_CONFIG_MAP.md
- pi4/assistant.py (2-line changes: docstring line 7 + bench log line 664)
- pi4/services/tts.py (1-line docstring change in _truncate_for_tts)
- docs/iris_issue_log.md (append 1 open issue entry for AMUSED pipeline gap)

Changes per file:
1. SNAPSHOT_LATEST.md: Update session to S45. Last commit = 103cbcc. Add "S45: add docs/iris_issue_log.md -- structured issue/fix history S1-S44" to last session changes.
2. IRIS_ARCH.md:
   - System Roles: GandalfAI role "Chatterbox TTS" → "Kokoro TTS (primary), Chatterbox (rollback)"
   - Current High-Level Pipeline: "Chatterbox primary or Piper fallback" → "Kokoro TTS (GandalfAI, port 8004) / Piper fallback (port 10200)"
   - System Status table: remove "Chatterbox" from active TTS row
   - Repo Structure: services/tts.py description "Chatterbox->Piper only (ElevenLabs removed S20)" → "Kokoro primary, Piper fallback (ElevenLabs removed S20)"
   - Repo Structure: ollama/iris_modelfile.txt description "gemma3:12b" → "gemma3:27b-it-qat"
   - Key Constants section: replace "as of S20" block with a single note "See IRIS_CONFIG_MAP.md for current values."
3. README.md:
   - Hardware table: correct any "Teensy 4.0" → "Teensy 4.1"
   - Eye System table: replace 9-eye table with 7-eye table matching config.h: 0=nordicBlue, 1=flame, 2=hypnoRed, 3=hazel, 4=blueFlame1, 5=dragon, 6=bigBlue. Remove leopard and snake.
   - Building section: remove "Then press PROG button on Teensy to complete flash"
   - LLM section: "gemma3:27b" → "gemma3:27b-it-qat"
   - Mouth Display section: fix pin description to match IRIS_ARCH.md SPI2 hw map
4. CLAUDE.md: Environment table GandalfAI role: add "Kokoro TTS," and change "Chatterbox" to "Chatterbox rollback"
5. IRIS_CONFIG_MAP.md:
   - VRAM note: "RTX 3090 with Chatterbox loaded leaves <4GB headroom" → "RTX 3090 with Kokoro (~2GB) + gemma3:27b-it-qat (~14.1GB) = ~16.1GB; headroom ~7.9GB"
   - Custom model dir row: remove stale line number "assistant.py:334"
6. pi4/assistant.py:
   - Line 7 docstring: "TTS:  Chatterbox       @ 192.168.1.3:8004 (primary)" → "TTS:  Kokoro           @ 192.168.1.3:8004 (primary)"
   - Line 664: `_tts_eng = "chatterbox" if CHATTERBOX_ENABLED else "piper"` → `_tts_eng = "kokoro" if KOKORO_ENABLED else "piper"`
7. pi4/services/tts.py:
   - _truncate_for_tts docstring: "Cap TTS input at max_chars to bound Chatterbox generation time." → "Cap TTS input at max_chars to bound Kokoro generation time."
8. docs/iris_issue_log.md: Append this entry:

## open | Pi4 / Emotion system

**Symptom:** [EMOTION:AMUSED] emitted by LLM per modelfile instructions but silently treated as NEUTRAL by Pi4 pipeline.
**Root cause:** `core/config.py` VALID_EMOTIONS set excludes AMUSED. `services/llm.py` extract_emotion_from_reply() returns NEUTRAL for any tag not in VALID_EMOTIONS. `src/main.cpp` EmotionID enum has no AMUSED entry.
**Proposed fix:** Add "AMUSED" to VALID_EMOTIONS in config.py. Add AMUSED entry to MOUTH_MAP (map to CURIOUS=2 or HAPPY=1). Add AMUSED LED behavior in hardware/led.py. Optionally extend main.cpp EmotionID for Teensy-side behavior (or accept NEUTRAL eye params for AMUSED).
**Status:** Open — MED priority

Show full diff before writing any file. Wait for explicit approval.
Commit message: "docs: Batch A cleanup -- Kokoro/TTS accuracy, eye table fix, AMUSED issue log entry"
Do not push. Do not deploy.
```

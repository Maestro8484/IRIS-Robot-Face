# IRIS Issue Log

Append-only structured record of bugs, root causes, and fixes.
Format: one entry per discrete issue. Add new entries at the bottom.

Query by component: `grep -A5 "Component.*assistant"` etc.

---

## Legend

- **Status: Fixed** — deployed and verified on live hardware
- **Status: Open** — known issue, no fix deployed
- **Status: Deferred** — acknowledged, low priority

---

## 2026-03-27 | S-early | Firmware / EyeController

**Symptom:** Face tracking eye movement drops out or snaps to wrong position after wakeword / motion restart.
**Root cause:** `eyeOldX` / `eyeOldY` not seeded from current position on motion restart in `setTargetPosition()`. Eyes jumped from stale 0,0 origin.
**Fix:** Seed `eyeOldX = eyeX` and `eyeOldY = eyeY` at motion restart.
**File:** `src/eyes/EyeController.h`
**Commit:** `ed8fa41`
**Status:** Fixed

---

## 2026-03-27 | S-early | Firmware / Sleep

**Symptom:** Teensy freezes when `EYES:SLEEP` command received. Display locks, serial unresponsive.
**Root cause:** `updateChangedAreasOnly(true)` left active during sleep entry — SPI conflict with sleep renderer.
**Fix:** Call `updateChangedAreasOnly(false)` on sleep entry before running sleep animation.
**File:** `src/TeensyEyes.ino`
**Commit:** `173b485` / `9084e13`
**Status:** Fixed

---

## 2026-03-28 | S-early | Firmware / Sleep renderer

**Symptom:** Sleep animation hangs — `drawChar()` causes infinite recursion crashing the firmware.
**Root cause:** `GC9A01A_t3n` library `drawChar()` implementation has a recursion path triggered by specific character codes used in the Zzz animation.
**Fix:** Pre-build patch script rewrites the offending recursion before compile.
**File:** `scripts/patch_drawchar.py`, `platformio.ini`
**Commit:** `3deb268`
**Status:** Fixed

---

## 2026-03-28 | S-early | Pi4 / Sleep system

**Symptom:** Sleep/wake cron commands do not change IRIS state. `_eyes_sleeping` flag out of sync with `/tmp/iris_sleep_mode`. LED brightness wrong during sleep.
**Root cause:** `iris_sleep.py` and `iris_wake.py` used direct serial writes — `TeensyBridge` holds the port exclusively. Sleep state file not being written by cron scripts. LED brightness code path not reached.
**Fix:** Route cron sleep/wake through UDP to `CMD_PORT`. Write `/tmp/iris_sleep_mode` in canonical `_do_sleep()`. Fix LED sleep brightness.
**Files:** `pi4/iris_sleep.py`, `pi4/iris_wake.py`, `pi4/assistant.py`
**Commit:** `dc47c30`
**Status:** Fixed

---

## 2026-04-02 | S1 | Pi4 / assistant.py

**Symptom:** `show_sleep()` LED animation not running on sleep command. `state.eyes_sleeping` not reset on restart. `NUM_PREDICT` too high causing slow responses.
**Root cause:** `show_sleep()` call missing from sleep handler path. State flag initialization order wrong. Default `NUM_PREDICT=512` excessive for short queries.
**Fix:** Wire `show_sleep()` to sleep handler. Reset `state.eyes_sleeping` in init. Set `NUM_PREDICT=120`.
**File:** `pi4/assistant.py`
**Commit:** `d1e0552`
**Status:** Fixed

---

## 2026-04-03 | S23 | Pi4 / Audio

**Symptom:** IRIS frequently ignores speech — no STT triggered even with clear voice input.
**Root cause:** RMS gate threshold set to 700 — too strict for typical household microphone levels. Most normal speech RMS falls 300–500.
**Fix:** Lower RMS gate from 700 → 300.
**File:** `pi4/assistant.py`
**Commit:** `a03756b`
**Status:** Fixed

---

## 2026-04-14 | S17 | Pi4 / TTS

**Symptom:** TTS response cuts off mid-sentence. Long LLM replies only partially spoken.
**Root cause:** Hard truncation at 220 chars in `tts.py` with no sentence-boundary awareness. Replies longer than 220 chars silently dropped.
**Fix:** Raise hard-cap to 900 chars. Add `TTS_MAX_CHARS` to config. Truncate at word boundary when no sentence boundary found.
**File:** `pi4/services/tts.py`, `pi4/core/config.py`
**Commit:** `b4bfb4d`
**Status:** Fixed

---

## 2026-04-14 | S17 | Pi4 / TTS

**Symptom:** 5–10 second gaps between spoken sentences during multi-sentence responses.
**Root cause:** `synthesize()` called once per sentence in a loop — each call incurred full TTS request round-trip latency.
**Fix:** Accumulate full LLM reply, call `synthesize()` once for the complete response.
**File:** `pi4/assistant.py`
**Commit:** `c240d7c`
**Status:** Fixed

---

## 2026-04-14 | S17 | Pi4 / STT / Follow-up

**Symptom:** IRIS enters hallucination spiral — Whisper transcribes silence as "Thank you", "Thanks for watching", etc. Follow-up loop re-sends these as real queries.
**Root cause:** No hallucination filter on STT output. Follow-up loop accepted any non-empty transcript.
**Fix:** Add `_WHISPER_HALLUCINATIONS` set + URL/spam pattern filter before sending transcript to LLM. Gate applies in both main loop and follow-up loop.
**File:** `pi4/assistant.py`
**Commit:** `a93da41`
**Status:** Fixed (partially — single-word STT still unresolved, see open issue below)

---

## 2026-04-16 | S-mid | Pi4 / Wakeword

**Symptom:** Wakeword never fires — IRIS does not respond to "hey Jarvis" at all.
**Root cause:** `OWW Detection score` default value was `1.0` (maximum confidence required). No real-world utterance ever reached 1.0 score.
**Fix:** Lower default `OWW_THRESHOLD` to `0.0` (permissive), tune to `0.85` in production config.
**File:** `pi4/assistant.py`, `pi4/iris_config.json`
**Commit:** `20c06ae`
**Status:** Fixed

---

## 2026-04-17 | S22 | Pi4 / Web UI / Sleep

**Symptom:** Web UI sleep/wake buttons do not fully transition IRIS state. Mouth intensity not updated on wake. Sleep LED animation not shown from web trigger.
**Root cause:** Web UI sleep route sent only `EYES:SLEEP` serial command — did not call canonical `_do_sleep()` / `_do_wake()` which sets mouth intensity, writes state file, and shows LED animation.
**Fix:** Web routes send commands via UDP to `CMD_PORT`. `start_cmd_listener()` calls `_do_sleep()` / `_do_wake()` on receipt.
**File:** `pi4/iris_web.py`, `pi4/assistant.py`
**Commit:** `f7802c9`
**Status:** Fixed

---

## 2026-04-23 | S31 | Pi4 / Audio / Wakeword

**Symptom:** Wakeword not detected. Assistant fails to start audio stream. `[MIC]` errors at startup.
**Root cause:** Microphone device index hardcoded or wrong. `CHANNELS=1` incompatible with wm8960 soundcard (requires stereo capture). `input_device_index` not passed to PyAudio open call.
**Fix:** Auto-detect mic device index by name. Set `CHANNELS=2`. Wire `input_device_index` to `pa.open()`.
**File:** `pi4/assistant.py`, `pi4/core/config.py`
**Commit:** `09977e4`
**Status:** Fixed

---

## 2026-04-24 | S30 | Pi4 / Wakeword (Batch 1A)

**Symptom:** OpenWakeWord process crash causes IRIS to hang silently — no error recovery, no restart.
**Root cause:** No retry/backoff on OWW startup failure. No socket liveness check. Dead OWW process returned `"error"` string but main loop did not handle it.
**Fix:** OWW startup retry with exponential backoff (3 attempts). Socket liveness check each loop iteration. OWW process death triggers auto-restart. `"error"` trigger skips STT/LLM/TTS and reconnects.
**File:** `pi4/assistant.py`
**Commit:** `078da91`
**Status:** Fixed

---

## 2026-04-24 | S32 | Pi4 / Sleep-Wake (Batch 1B)

**Symptom:** Sleep/wake state inconsistent across trigger paths (cron, web UI, voice, wakeword-during-sleep). `/tmp/iris_sleep_mode` and `state.eyes_sleeping` diverge.
**Root cause:** Sleep/wake logic duplicated and inconsistently implemented across 4+ code paths. No canonical entry point.
**Fix:** Canonical `_do_sleep()` and `_do_wake()` functions. All paths call these exclusively. `send_command()` and `send_emotion()` return bool status. `iris_wake.py` clears `/tmp/iris_sleep_mode`.
**File:** `pi4/assistant.py`, `pi4/iris_sleep.py`, `pi4/iris_wake.py`, `pi4/iris_web.py`
**Commit:** `075d098`
**Status:** Fixed

---

## 2026-04-25 | S33-34 | Pi4 / LLM (Batch 1C-F)

**Symptom:** All queries sent to LLM with same token budget (512). Simple questions ("what time is it?") take as long as complex ones. Long questions get cut off.
**Root cause:** Single flat `NUM_PREDICT` value for all query types. No length classification.
**Fix:** `classify_response_length()` function — SHORT/MEDIUM/LONG/MAX tiers based on query pattern matching and word count heuristics.
**File:** `pi4/services/llm.py`
**Commit:** `a51a97e`
**Status:** Fixed

---

## 2026-04-26 | S35 | Pi4 / Wakeword

**Symptom:** Custom wakewords `hey_der_iris` and `real_quick_iris` unreliable in real-world household conditions — frequent false negatives.
**Root cause:** Custom models trained on insufficient/non-representative voice samples. Real household acoustics too varied.
**Fix:** Revert to `hey_jarvis` baseline. Archive custom wakeword scripts as experimental. Standing rule: do not redeploy without household voice samples + one-model-at-a-time testing.
**File:** `pi4/assistant.py`, `pi4/core/config.py`
**Commit:** `8c107bc`
**Status:** Fixed (custom wakeword work paused)

---

## 2026-04-26 | S36 | Firmware / Eyes

**Symptom:** Eye movement continues animating while IRIS is speaking — visually distracting, inconsistent with intended behavior.
**Root cause:** No mechanism to pause eye movement correlated with TTS playback duration.
**Fix:** Suspend eye movement for duration of TTS audio playback in `src/main.cpp`. Resume on playback completion.
**File:** `src/main.cpp`
**Commit:** `c27517a`
**Status:** Fixed

---

## 2026-04-27 | S42 | Pi4 / Intent routing (Batch 3-F)

**Symptom:** All user speech sent to LLM — simple commands (volume, sleep, stop) incur full LLM round-trip latency (2–17s cold, ~2s warm). No pre-classification.
**Root cause:** No intent router. Every transcript went directly to Ollama regardless of type.
**Fix:** 5-layer pre-LLM intent router (`REFLEX → COMMAND → UTILITY → AMBIGUOUS → LLM`). REFLEX handles sleep/stop/wake instantly. COMMAND handles volume/eyes/kids mode. UTILITY handles time/date/math. LLM only reached for open queries.
**File:** `pi4/core/intent_router.py` (new), `pi4/assistant.py`
**Commit:** `c37623e`
**Status:** Fixed

---

## 2026-04-27 | S43 | Pi4 / TTS

**Symptom:** Numbers above 999 spoken as digits ("four two one zero") instead of words ("four thousand two hundred ten").
**Root cause:** `spoken_numbers()` / `_int_to_words()` had `<= 999` bailout — thousands and millions fell through to digit-by-digit fallback.
**Fix:** Extend `_int_to_words()` to handle thousands (< 1M) and millions (< 1B). Remove `<= 999` bailout in catch-all regex.
**File:** `pi4/services/tts.py`
**Commit:** `39247b4`
**Status:** Fixed

---

## 2026-04-28 | S44 | Pi4 / Intent routing

**Symptom:** "Pick a random number between 1 and 10" routed to LLM with MEDIUM tier (350 tokens). Cold GandalfAI = 17–31s response for a 1-token answer.
**Root cause:** No UTILITY handler for random number generation. `classify_response_length()` fell through to MEDIUM default for "pick..." prefix.
**Fix:** Add `RANDOM_NUMBER` handler in Layer 2 of intent router. `_RANDOM_RE` catches pick/tell/give/choose/generate + "random number". `_RANDOM_RANGE_RE` parses optional "between X and Y". Answered via `random.randint()` — zero LLM latency. Add random-number phrases to `_SHORT_PATTERNS` as fallback.
**Files:** `pi4/core/intent_router.py`, `pi4/services/llm.py`
**Commit:** `35d01ba`
**Status:** Fixed

---

## 2026-04-28 | S44 | Pi4 / Follow-up loop

**Symptom:** IRIS asks a follow-up question (LEDs glow purple). User gives a brief reply ("Yes, 54.", "Seven.", "No.") — silently dropped, loop exits without responding.
**Root cause:** Follow-up loop had `if len(_text_norm.split()) < 3: break` gate originally intended for hallucination filtering. Valid short user responses (1–2 words) were caught and discarded.
**Fix:** Replace `< 3 words` gate with `_WHISPER_HALLUCINATIONS` set membership check — only drops known Whisper hallucination phrases, not legitimate short replies.
**File:** `pi4/assistant.py`
**Commit:** `35d01ba`
**Status:** Fixed

---

## 2026-04-28 | S44 | Pi4 / Web UI

**Symptom:** Web UI Logs tab shows `[ERR] LLM stream: timed out` or `[ROUTE] LLM/LLM` with no context explaining why a prompt was mishandled. Intent routing decisions invisible.
**Root cause:** `/api/logs` only read `journalctl` output (truncated to 120 lines). `iris_intent.log` — the per-request routing record — never surfaced in the UI.
**Fix:** `/api/logs` appends last 40 lines of `/home/pi/logs/iris_intent.log` below a separator. Journalctl line limit raised 120 → 150.
**File:** `pi4/iris_web.py`
**Commit:** `35d01ba`
**Status:** Fixed

---

## OPEN ISSUES

---

## open | Pi4 / STT

**Symptom:** Single-word utterances ("stop", "quiet") transcribed incorrectly by Whisper — "stop" → "What are you doing?" Intent router then classifies correctly for the hallucinated phrase, not the intended command.
**Root cause:** Whisper is unreliable on sub-1-second audio with minimal phonetic content. Hallucination rate spikes on very short recordings.
**Proposed fix:** Pre-STT RMS duration gate — if post-wakeword audio < ~0.5s, route directly to local keyword match (stop/cancel/quiet) without Whisper. OR add known short-command words to a local keyword list checked before STT.
**Status:** Open — HIGH priority

---

## open | GandalfAI / Ollama model

**Symptom:** IRIS personality drifts — boilerplate LLM responses instead of in-character behavior. Re-testing sometimes shows regression after sessions where no modelfile changes were made.
**Root cause:** Three-way desync: SuperMaster repo / GitHub / GandalfAI running model. `ollama create iris` must be run on GandalfAI after every modelfile commit. GandalfAI clone at `C:\IRIS\IRIS-Robot-Face\` does not auto-pull.
**Standing rule:** Any LLM drift → run `ollama show iris --modelfile` on GandalfAI and compare to `ollama/iris_modelfile.txt` in repo before any persona changes.
**Status:** Open — standing operational hazard (documented, not a code fix)

---

## 2026-05-02 | S45 | Pi4 / Volume

**Symptom:** `SPEAKER_VOLUME` may reset to ALSA default on reboot. User-configured volume level lost.
**Root cause:** Volume set at runtime via `amixer` is not guaranteed to survive overlayfs reboot unless `alsactl store` and SD persistence both complete correctly.
**Fix:** `pi4/iris_web.py` volume API route calls `alsactl store` and writes `SPEAKER_VOLUME` to `iris_config.json` on every volume change. `api_persist_config` route copies ALSA state file to SD layer alongside iris_config.json.
**File:** `pi4/iris_web.py` (lines 258-260, 233-240)
**Status:** Fixed

---

## open | Pi4 / TTS routing

**Symptom:** Sleep wakeword greeting routed through Wyoming Piper on GandalfAI:10200 instead of local Piper. Local `/usr/local/bin/piper` binary broken.
**Root cause:** Local Piper install corrupted or missing dependency. Kokoro is primary TTS — this only affects the specific sleep-wakeword greeting path.
**Status:** Deferred/Closed — LOCAL-PIPER BROKEN, LOW-LOW priority. Not worth fixing until Kokoro primary fails. Closing from active tracking.

---

## 2026-05-03 | S46 | Pi4 / UX — GandalfAI wake acknowledgement

**Symptom:** When GandalfAI is offline and IRIS hears the wakeword, the system silently waits 60–120 s for WoL boot with no audio feedback. Indistinguishable from a crash or ignored wakeword.
**Root cause:** `play_beep(pa)` fires only *after* `ensure_gandalf_up` returns. During the entire WoL boot wait, the only user-visible signal was an orange LED pulse animation.
**Fix:** Added `play_wol_beep(pa)` (ascending 660 Hz → 880 Hz, ~360 ms) to `audio_io.py`. `ensure_gandalf_up` accepts optional `pa` parameter; beep fires immediately after WoL packet is sent. Both call sites (sleep path + normal path) updated to pass `pa`. No beep when GandalfAI is already up.
**Files:** `pi4/hardware/audio_io.py`, `pi4/assistant.py`
**Status:** Fixed and deployed to Pi4 (S46)

## open | Pi4 / Logging

**Symptom:** `/home/pi/iris_sleep.log` (root level) may duplicate `/home/pi/logs/iris_sleep.log`. Two log files for same events.
**Root cause:** Early implementation wrote to root home dir. Logging path later standardized to `logs/` subdirectory but old path not cleaned up.
**Status:** Open — LOW priority cleanup

# Task 1 — Pi4 Pipeline Architecture Audit

**Date:** 2026-05-16
**Reviewer:** Opus 4.7
**Scope:** Pi4 voice pipeline, exception propagation, state mutation, router bypass

---

## 1. Pipeline Call Chain (Wakeword → TTS Playback)

Reference: `pi4/assistant.py` `main()` loop body. Line numbers refer to assistant.py.

### Stage A — Wakeword acquisition (per-iteration setup)

1. `oww_proc.poll()` — `assistant.py:248` — check OWW subprocess liveness; restart loop with `_start_oww()` if dead.
2. `socket.create_connection(("127.0.0.1", OWW_PORT), timeout=10)` — `assistant.py:266` — open TCP to OWW subprocess.
3. `wait_for_wakeword_or_button(mic, oww_sock)` — `assistant.py:273` — delegated to `services/wakeword.py`.
   - Inside: `wy_send(oww_sock, "detect", {...})` → `wy_send(oww_sock, "audio-start", ...)` → reader thread loop.
   - Reader: `oww_sock.recv(4096)` → JSON parse → checks `score >= OWW_THRESHOLD`.
   - Main loop in same function: `mic.read(CHUNK, ...)` → `wy_send(oww_sock, "audio-chunk", audio)` until `detected.is_set()`.
   - Concurrently polls `button_pressed()` from `hardware/io.py` (GPIO17 active-low).
   - Returns `"wake"` | `"button"` | `"error"`.
4. `oww_sock.close()` — `assistant.py:280` — close socket in `finally`.

Data passed: raw PCM bytes (16 kHz, 16-bit, 2-channel) → Wyoming framed JSON+payload over TCP.

### Stage B — Pre-STT gating and audio capture

5. If `trigger == "error"`: short error LED, retry. (`assistant.py:285`)
6. If `/tmp/iris_sleep_mode` exists: enter sleep-wake path — `_do_wake()` → `ensure_gandalf_up()` → `synthesize(greeting)` → `play_pcm_speaking()`; `continue`. (`assistant.py:296-310`)
7. `ensure_gandalf_up(leds, pa)` — `assistant.py:312` — checks `gandalf_is_up()` (TCP probe of `:11434`); if down, sends WoL packet + `play_wol_beep(pa)` + spinner animation thread, polls every `WOL_POLL_INTERVAL=5s` up to `WOL_BOOT_TIMEOUT=120s`.
8. `play_beep(pa)` — `audio_io.py` — single tone.
9. Drain `OWW_DRAIN_SECS=0.15s` of audio into `_pre_buf` via `mic.read()`. (`assistant.py:318-322`)
10. `record_command(mic, ptt_mode, kids_mode=state.kids_mode)` — `audio_io.py:267` — reads frames with silence detection until `sil_limit` chunks below RMS threshold OR `rec_secs` elapsed.
11. RMS gate: if `rms < 300` discard. (`assistant.py:332`)

### Stage C — STT

12. `transcribe(raw)` — `assistant.py:339` → `services/stt.py:transcribe()`.
    - `socket.create_connection((GANDALF, WHISPER_PORT), timeout=30)`
    - `wy_send` 4 events: `transcribe`, `audio-start`, chunked `audio-chunk` (4096 bytes per chunk), `audio-stop`.
    - Recv loop parses `type=transcript`, reads `data_length` payload bytes, returns `.text.strip()` or `""`.
    - Returns: string.
13. If empty: `continue`. (`assistant.py:344`)
14. Normalize: `_text_norm = text.lower().strip().strip(".!?,;:")`. (`assistant.py:352`)

### Stage D — Pre-router gates (in order)

15. **Main-loop STOP phrase gate** (`assistant.py:354-362`): if `_text_norm == phrase or _text_norm.startswith(phrase + " ")` for any phrase in `STOP_PHRASES` (imported from `audio_io.py`): `_stop_playback.set()`; `emit_emotion(NEUTRAL)`; `continue`. **This runs before the intent router.**
16. **Whisper hallucination filter** (`assistant.py:364-377`): `_WHISPER_HALLUCINATIONS` set + `_WHISPER_HALLUCINATION_PATTERNS` substring/prefix check. If matched: `continue`.

### Stage E — Intent router

17. `router.classify(text, state)` — `assistant.py:380` → `intent_router.py:IntentRouter.classify()`.
    - Wraps `_classify()` in `try/except` — exception → fail-open to LLM with CONF_LOW.
    - `_classify` runs layers 0–3 in order; returns `IntentResult(route, action, confidence, response, payload)`.
    - Writes one structured line to `/home/pi/logs/iris_intent.log` via `_intent_logger`.
18. `_route` branched in assistant.py:
    - **ROUTE_REFLEX** (`assistant.py:399-417`): SLEEP → `_do_sleep()` + optional `synthesize`+`play_pcm_speaking`; STOP → `_stop_playback.set()`; WAKE → `_do_wake()`.
    - **ROUTE_COMMAND** (`assistant.py:419-461`): EYES_SLEEP/EYES_WAKE → mutates `state.eyes_sleeping` + Teensy commands; KIDS_ON/OFF → `handle_kids_mode_command()` + TTS; volume ops → `handle_volume_command()` + TTS.
    - **ROUTE_UTILITY** (`assistant.py:463-488`): VISION → `capture_image()` + `ask_vision()` + TTS; other utility (TIME/DATE/MATH/RANDOM_NUMBER) → `_result.response` directly to TTS.
    - **ROUTE_AMBIGUOUS** (`assistant.py:490-503`): STOP → like REFLEX STOP; SLEEP → like REFLEX SLEEP; AMBIGUOUS/LLM → fall through.
    - **ROUTE_LLM**: falls through to streaming LLM block.

### Stage F — LLM (streaming path)

19. `classify_response_length(text)` — `services/llm.py:228` — pattern-matched tier selection → `num_predict` int.
20. Append user turn: `state.conversation_history.append({"role":"user", "content":text})` — `assistant.py:516`.
21. `stream_ollama(_build_messages(), get_model(), _num_predict)` — `services/llm.py:67`.
    - `requests.post(.../api/chat, stream=True, timeout=60)`.
    - For each line: parse JSON; accumulate `token` into `buffer`; extract `EMOTION:X` once; on each iteration call `_split_sentences(buffer)` and yield completed sentences with `clean_llm_reply(p)`.
    - First yield emits `(chunk, emotion)`; subsequent yields emit `(chunk, None)`.
    - Raises `RuntimeError` wrapping any exception.
22. For each yielded `(chunk, chunk_emotion)`:
    - First non-None emotion → `emit_emotion(teensy, leds, chunk_emotion)` — `assistant.py:530`.
    - Accumulate into `reply_parts`.
23. If no emotion fired at all: `emit_emotion(teensy, leds, "NEUTRAL")` — `assistant.py:546`.
24. `reply = " ".join(reply_parts).strip()` — `assistant.py:548`.

### Stage G — TTS + playback

25. `synthesize(reply)` — `services/tts.py:151`.
    - Apply `spoken_numbers()`, markdown strip, non-ASCII strip, `_truncate_for_tts()` (cap at `TTS_MAX_CHARS=900` with sentence-boundary fallback).
    - Sleep/wake direct-Piper bypass: if text matches `_PIPER_DIRECT_PHRASES` → `_synthesize_piper()` directly.
    - Else: if `KOKORO_ENABLED`: try `_synthesize_kokoro()` (HTTP POST to `:8004/v1/audio/speech`, miniaudio decode); on exception → `_synthesize_piper()`.
    - Returns: s16le PCM @ 48 kHz.
26. `leds.show_speaking()` + `mic.stop_stream()` — `assistant.py:564`.
27. `play_pcm_speaking(pcm_data, pa, teensy)` — `audio_io.py:225`.
    - Spawns `_animate` daemon thread cycling MOUTH frames `[0,1,5,1]` @ 120 ms via `teensy.send_command()`.
    - Calls `play_pcm(pcm_bytes, pa, rate=48000)`:
      - Spawns `_playback_interrupt_listener(pa, _int_stop, interrupted)` daemon: separate mic stream, 0.5 s bleed baseline, then RMS-gated voice collection → background `services.stt.transcribe()` → checks `STOP_PHRASES` → sets `_stop_playback` + `interrupted`.
      - Main thread opens PyAudio output stream with callback; polls `button_pressed()` and `_stop_playback.is_set()`.
    - Returns bool `was_interrupted`.
28. Append assistant turn to `state.conversation_history`; trim oldest user+assistant pair if `len > 20` — `assistant.py:570-572`.

### Stage H — Follow-up loop (optional)

29. `implies_followup(reply)` checked — `assistant.py:578`. Loop runs while True, max `FOLLOWUP_MAX_TURNS=3`, exits on `_interrupted`.
30. `record_followup(mic, pa, leds)` — `assistant.py:163` — open mic, wait for voice above `sil_rms`, record until `sil_limit` silent chunks.
31. `transcribe(followup_audio)` → same hallucination + STOP + dismissal gates as main loop, **but here STOP uses `startswith(phrase)` not `startswith(phrase + " ")`** (assistant.py:602).
32. `handle_time_command(text)` → if non-None, use directly; else `handle_volume_command(text)` → if non-None, use directly; else `ask_ollama(text, num_predict=_followup_predict)` — `assistant.py:147`.
33. `ask_ollama()` does blocking `requests.post(.../api/chat, stream=False)`, extracts emotion+cleans, appends to `state.conversation_history`.
34. `emit_emotion()` → `synthesize()` → `play_pcm_speaking()` → `_interrupted` check.
35. After loop exit: `mic.start_stream()` (suppress OSError); `emit_emotion(NEUTRAL)`; `show_idle_for_mode(leds)`; if `in_sleep_window()` → `return_to_sleep(teensy, state)`.

---

## 2. Silent State-Corruption Exception Paths

- **File:** `pi4/services/wakeword.py`
- **Lines:** 25-67 (reader thread `try/except: break`)
- **Severity:** MED
- **Risk:** Any exception in the reader thread (JSON parse outside the inner try, socket op, attribute access) breaks the outer `while not detected.is_set()` loop without setting `detected`. The outer `wait_for_wakeword_or_button` main-thread loop continues calling `mic.read()` + `wy_send()` until the next `audio-chunk` write fails, then returns `"error"`. During this window, the reader thread is dead but the main thread thinks OWW may still detect — wakeword detections that arrive between thread-death and socket-write-failure are dropped.
- **Fix direction:** Set `trigger[0] = "error"` and `detected.set()` in the bare `except` block before `break`.

---

- **File:** `pi4/services/llm.py`
- **Lines:** 102-152 (`stream_ollama` raises `RuntimeError`)
- **Severity:** MED
- **Risk:** When `stream_ollama` raises after the user turn was appended to `state.conversation_history` (assistant.py:516), no matching assistant turn is appended. On the next user turn, `_build_messages()` sends an unmatched trailing user message to Ollama. Conversation history becomes structurally malformed (two consecutive `user` roles) which gemma3 tolerates but degrades multi-turn coherence.
- **Fix direction:** On `LLM stream` exception in assistant.py:541-544, pop the trailing user turn before `continue`.

---

- **File:** `pi4/assistant.py`
- **Lines:** 558-562 (TTS synthesize exception path)
- **Severity:** MED
- **Risk:** Same pattern. After streaming LLM completes, user turn AND assistant turn have already been appended (assistant.py:570 only runs *after* TTS, but the user turn was appended at line 516 before streaming). Wait — re-reading: assistant turn is appended at line 570 which is AFTER the `synthesize` try/except `continue` at line 558-562. So if TTS fails: user turn IS in history, assistant turn is NOT. Same broken-pair condition as above.
- **Fix direction:** Move `state.conversation_history.append({"role":"assistant", ...})` to before the `synthesize` call, OR pop the user turn on TTS failure.

---

- **File:** `pi4/hardware/audio_io.py`
- **Lines:** 165-217 (`_playback_interrupt_listener`)
- **Severity:** HIGH
- **Risk:** The listener spawns a background `services.stt.transcribe()` call (line 196) which opens its own TCP socket to GandalfAI Whisper. If Whisper is slow or hangs during playback, multiple `_verify_stt` threads can accumulate (the `stt_pending` flag only blocks one in-flight at a time per listener instance, but the background thread itself can outlive the playback). Worse: the STT thread calls `_stop_playback.set()` and `interrupted.set()` even if it completes *after* playback has already finished naturally. Side effects:
  1. `_stop_playback` remains set when the next utterance begins playing → next playback is killed instantly.
  2. The interrupted event's owner is gone (local scope), so the set is harmless there, but `_stop_playback` is module-level.
  Actual impact mitigated by `play_pcm` calling `_stop_playback.clear()` at entry (line 220), so the window is narrow but real: an STT thread completing between `_stop_playback.clear()` and the next `_int_thread.start()` would corrupt the new playback.
- **Fix direction:** Have `_verify_stt` check `stop_event.is_set()` before calling `_stop_playback.set()` / `interrupted.set()`, or pass a per-playback session token.

---

- **File:** `pi4/hardware/teensy_bridge.py`
- **Lines:** 56-93 (send paths swallow `SerialException`)
- **Severity:** LOW
- **Risk:** `send_emotion` / `send_command` return `False` on SerialException and set `self._ser = None`. Callers in `assistant.py` (`emit_emotion`, `_do_sleep`, `_do_wake`, etc.) do not inspect the return value. Teensy disconnect during a session results in silent failure: emotion logged as `[EYES] >> EMOTION:HAPPY` would not appear (the print is inside the success path); instead `[EYES] Send failed: ...` appears once. State drifts: Pi4 believes Teensy received `EYES:SLEEP` but it did not — eyes remain awake while LEDs show sleep breathe and `state.eyes_sleeping = True`.
- **Fix direction:** Check return value of `teensy.send_command` in `_do_sleep`/`_do_wake`; on False, log warning and either retry or mark a degraded state.

---

- **File:** `pi4/iris_web.py`
- **Lines:** 199-217 (`api_chat` exception)
- **Severity:** LOW
- **Risk:** If `requests.post` to Ollama raises, `api_chat` returns 500 to the browser but does NOT append the user turn anywhere — the browser-side conversation does not flow through assistant.py's `state.conversation_history`, so no cross-corruption. But if `speak=True` and TTS fires after a successful LLM response, the spoken response and the Ollama call are decoupled from main loop state — they happen in parallel with whatever the assistant is doing. Risk: web chat TTS plays simultaneously with assistant.py main-loop TTS, creating overlapping audio. SNAPSHOT_LATEST.md S49 entry notes "TTS conflict warning note added to UI" — the warning is the mitigation; no code-level lock exists.
- **Fix direction:** Add a cross-process audio lock (file lock at `/tmp/iris_audio.lock`) checked by both `play_pcm` and `_speak_worker`. Or treat as accepted limitation and surface in docs.

---

## 3. Race Conditions and State Inconsistency Risks

### 3a. Follow-up loop

- **File:** `pi4/assistant.py`
- **Lines:** 578-635
- **Severity:** MED
- **Risk 1:** `mic.stop_stream()` is called inside `play_pcm_speaking` (line 627) at every follow-up turn. After the loop ends, `mic.start_stream()` is called at line 638 inside `try/except OSError`. If the mic was already stopped twice (e.g., interrupt fired mid-playback), the state may be inconsistent — the OSError suppression hides any real failure to restart the mic, after which the next wakeword detection silently fails because `mic.read()` returns no audio.
- **Risk 2:** `state.conversation_history` is appended to inside `ask_ollama` (line 138) without checking whether the loop is still active. If user says STOP mid-followup, `_interrupted` is set and the loop breaks at line 632 — but the assistant turn from the interrupted reply was already appended to history.
- **Risk 3:** `_text_norm` is reused as a loop-local variable shadowing the outer-scope name from line 352. This is harmless functionally but obscures debugging.
- **Fix direction:** Track whether `mic.stop_stream` was called and verify state before `start_stream`; check `_interrupted` before history append in follow-up `ask_ollama` path.

### 3b. Sleep/wake state transitions

- **File:** `pi4/assistant.py`, `pi4/iris_sleep.py`, `pi4/iris_wake.py`, `pi4/iris_web.py`
- **Lines:** assistant.py:217-244 (`_do_sleep`/`_do_wake`), iris_sleep.py:19-23, iris_wake.py:18-22, iris_web.py:91-104
- **Severity:** HIGH
- **Risk:** Three concurrent writers to `state.eyes_sleeping` and `/tmp/iris_sleep_mode`:
  1. Main loop and CMD listener thread in `assistant.py` (both can call `_do_sleep`/`_do_wake`).
  2. `iris_sleep.py` and `iris_wake.py` cron scripts — they write `/tmp/iris_sleep_mode` directly (lines 23, 25) AND send UDP commands to CMD_PORT which trigger `_do_sleep`/`_do_wake` via the CMD listener. This is a double-write: cron script touches the flag file before/after the listener does.
  3. `iris_web.py` `/api/sleep` and `/api/wake` routes write the flag file directly (lines 96, 104) AND send UDP commands. Same double-write.
  None of these writers acquire `state._lock`. `state.eyes_sleeping` is mutated in `_do_sleep` (line 221), `_do_wake` (line 230), and in the COMMAND/EYES_SLEEP and COMMAND/EYES_WAKE branches in the main loop (lines 424, 432) — also unlocked. Concurrent web-sleep + main-loop wake-after-followup could race.
- **Risk 2:** `iris_web.py` `/api/wake` does NOT call `_do_wake` via UDP — it sends raw `EYES:WAKE`, `MOUTH:0`, `MOUTH_INTENSITY:8` (lines 99-101), then deletes the flag. It does NOT update `state.eyes_sleeping` in assistant.py. The CMD listener catches `EYES:WAKE` and DOES call `_do_wake` (assistant.py:138), so state ends up correct — but this is non-obvious and fragile. If a future change removes the CMD listener branch on `EYES:WAKE`, the web route would silently desync `state.eyes_sleeping` from the flag file.
- **Risk 3:** `iris_wake.py` deletes `/tmp/iris_sleep_mode` directly (line 28). The CMD listener path for `EYES:WAKE` also calls `_do_wake` which deletes the file. Double-delete is harmless (FileNotFoundError caught), but the order is non-deterministic.
- **Fix direction:** Centralize sleep flag writes inside `_do_sleep`/`_do_wake` only. Cron and web scripts should send UDP and let assistant.py own the flag. Add lock acquisition around `state.eyes_sleeping` mutations.

### 3c. TeensyBridge serial ownership

- **File:** `pi4/hardware/teensy_bridge.py`, `pi4/iris_sleep.py`, `pi4/iris_wake.py`, `pi4/iris_web.py`
- **Lines:** teensy_bridge.py:23-34 (reader thread), all UDP paths
- **Severity:** LOW (current design appears correct)
- **Risk:** IRIS_ARCH.md and `intent-router.md` state that only `teensy_bridge.py` opens `/dev/ttyACM0`. `iris_sleep.py:19-22`, `iris_wake.py:18-21`, `iris_web.py:46-52` all use UDP to `127.0.0.1:CMD_PORT` — they do NOT open the serial port. The CMD listener in assistant.py:130-150 receives UDP and calls `teensy.send_command()`. The rule is enforced by convention. There is no programmatic guard (e.g., lock file on `/dev/ttyACM0`) — a future helper script could still violate the rule.
- **Side concern:** TeensyBridge `_reader` thread auto-reopens serial on disconnect (`time.sleep(5)` retry). During reopen, `_ser is None` and all `send_*` calls return False (lines 58, 78). A burst of EMOTION/MOUTH commands during a 5-second reopen window are silently dropped.
- **Fix direction:** Optional — add `flock(/dev/ttyACM0)` in TeensyBridge.`_open` to catch convention violations. Buffer outgoing commands during reopen window if drop is unacceptable.

---

## 4. Bypasses of intent_router.py

### Bypass 1 — STOP phrase gate before router

- **File:** `pi4/assistant.py`
- **Lines:** 354-362
- **Status:** Intentional, partially documented
- **Detail:** `STOP_PHRASES` (defined in `audio_io.py:34`) is checked before the router. The router itself has its own `_STOP_EXACT` / `_STOP_STARTS` sets (`intent_router.py:46-50`) — these overlap heavily but are not identical. `STOP_PHRASES` includes `"hey jarvis"` and `"that's enough"`; router `_STOP_EXACT` does not include `"hey jarvis"` but DOES include `"jarvis stop"`. `intent_router.py` separately routes `"that's enough"` to `ROUTE_AMBIGUOUS/STOP` via `_AMBIGUOUS_STOP_EXACT`. The pre-router gate would catch `"that's enough"` as REFLEX-style STOP before the router gets to classify it as AMBIGUOUS. This is documented as "Main-loop STOP phrase gate" in the comment but the divergence from the router's STOP intent isn't called out in HANDOFF or ROADMAP.
- **Per design docs:** RD-001 in ROADMAP.md says "post-STT STOP phrase gate" is the implementation. The bypass is intentional but the *two-source-of-truth* for STOP phrases (audio_io.STOP_PHRASES vs intent_router._STOP_EXACT) is undocumented drift.

### Bypass 2 — Whisper hallucination filter before router

- **File:** `pi4/assistant.py`
- **Lines:** 364-377
- **Status:** Intentional
- **Detail:** `_WHISPER_HALLUCINATIONS` set + `_WHISPER_HALLUCINATION_PATTERNS` filter before router. Avoids routing common Whisper-on-silence outputs ("Thank you", "Thanks for watching") to the LLM. Per design.

### Bypass 3 — Sleep-mode wake greeting

- **File:** `pi4/assistant.py`
- **Lines:** 296-310
- **Status:** Intentional
- **Detail:** When wakeword fires during sleep mode (`/tmp/iris_sleep_mode` exists), `_do_wake()` runs and a fixed greeting ("Good morning." / "Good evening." / "Hello.") goes straight to `synthesize()` → `play_pcm_speaking()` with no STT, no router, no LLM. Per design.

### Bypass 4 — `handle_time_command` in follow-up loop

- **File:** `pi4/assistant.py`
- **Lines:** 605-611
- **Status:** Gap
- **Detail:** Inside the follow-up loop, `handle_time_command(text)` and `handle_volume_command(text)` are invoked directly (lines 605, 609) — bypassing the intent router. The main loop routes these via UTILITY/COMMAND; the follow-up loop uses inline checks. This means: a follow-up "what time is it" never reaches the router's TIME action and never logs to `iris_intent.log` as a structured event. Worse: REFLEX-tier intents (SLEEP/STOP/WAKE) on follow-up turns are handled by inline `STOP_PHRASES`/`FOLLOWUP_DISMISSALS` checks only — there's no follow-up-loop path that goes through `router.classify()` to catch eg. "goodnight" or new utility intents (RANDOM_NUMBER, MATH) added to the router.
- **Per design docs:** `intent-router.md` says the router replaces inline classification "consolidates them into a single classified gate with logging." The follow-up loop retains inline classification — that's a known gap not documented in ROADMAP.

### Bypass 5 — `api_chat` web route

- **File:** `pi4/iris_web.py`
- **Lines:** 199-217
- **Status:** Intentional (web chat is a separate input channel)
- **Detail:** `/api/chat` accepts arbitrary text and POSTs directly to Ollama `/api/generate` with no intent router, no STOP gate, no hallucination filter. Web chat is a separate input surface from voice; design intent is unclear in docs but defensible.

### Bypass 6 — Vision path in router calls vision Ollama directly

- **File:** `pi4/assistant.py`, `pi4/services/vision.py`
- **Lines:** assistant.py:466 (`ask_vision(img, text)`), vision.py:55-83
- **Status:** Intentional
- **Detail:** When router returns UTILITY/VISION, `ask_vision()` POSTs to Ollama `/api/generate` with a custom vision prompt that does NOT include `state.conversation_history`. Vision queries are stateless. Per design (vision is single-shot Q&A).

---

## 5. Unlocked Shared-State Mutations

- **File:** `pi4/state/state_manager.py`
- **Lines:** 19-25, 35-37
- **Severity:** MED
- **Risk:** `StateManager.__init__` exposes `conversation_history`, `last_interaction`, `kids_mode`, `eyes_sleeping` as plain attributes. Only `clear_conversation()` acquires `self._lock`. All other mutations bypass the lock:
  - `state.conversation_history.append(...)` — assistant.py:131, 134, 516, 570
  - `state.conversation_history.pop(0)` — assistant.py:135, 572
  - `state.last_interaction = ...` — assistant.py:74 (watchdog read), 130 (ask_ollama write), 515 (main loop write)
  - `state.kids_mode = True/False` — assistant.py:189, 195
  - `state.eyes_sleeping = True/False` — assistant.py:221, 230, 393, 424, 432
- Concurrent writers: main thread, `_context_watchdog` thread (reads `last_interaction` and `conversation_history`), `start_cmd_listener` thread (calls `_do_sleep`/`_do_wake` which mutate `eyes_sleeping`). Python GIL makes single attribute writes atomic, but a `pop(0); pop(0)` pair (assistant.py:135) is not — if the watchdog reads between the two pops, it sees a half-trimmed history. This is unlikely to cause visible harm but is technically racy.
- **Fix direction:** Either rename `_lock` to `lock` and acquire around every mutation, or document explicitly that StateManager relies on GIL for atomicity of single ops and accept the trim-pair race.

---

- **File:** `pi4/iris_web.py`
- **Lines:** 26-29 (`write_cfg`), 95-104 (sleep flag writes), 277-280 (volume write)
- **Severity:** LOW
- **Risk:** `write_cfg()` reads then writes `/home/pi/iris_config.json` without locking. Concurrent POST to `/api/config` and `/api/volume` (which both call write_cfg-equivalents) can race: each reads the file, modifies its own keys, writes back — last writer wins, the earlier writer's modifications are lost. Flask `threaded=True` (line 322) makes this possible.
- **Fix direction:** Wrap config R/W in `fcntl.flock` or a module-level `threading.Lock`.

---

- **File:** `pi4/iris_sleep.py`, `pi4/iris_wake.py`, `pi4/assistant.py`, `pi4/iris_web.py`
- **Lines:** sleep.py:23, wake.py:28, assistant.py:212-213, 222, 232-235, web.py:96, 104
- **Severity:** HIGH (documented above in 3b)
- **Risk:** `/tmp/iris_sleep_mode` has 4+ unsynchronized writers/deleters. No single owner. Documented contract is implicit ("assistant.py owns it") but the cron and web paths violate this.
- **Fix direction:** Restrict flag mutation to `_do_sleep`/`_do_wake` in assistant.py. Cron scripts and web routes should only send UDP commands.

---

- **File:** `pi4/core/config.py`
- **Lines:** 215-245 (`globals()[_k] = _coerced`)
- **Severity:** LOW
- **Risk:** Module-level mutation of `globals()` at import time. Single-writer (the import block) so no race, but multiple imports of `from core.config import *` capture the *value at import time*. If `iris_config.json` is rewritten after assistant.py boot, the constants are stale until restart. The web UI tells the user to restart assistant after config changes (IRIS_CONFIG_MAP.md deploy checklist) — this is documented behavior, not a bug.
- **Fix direction:** None needed; current behavior matches docs. The race only matters if a future change tries to hot-reload config without restart.

---

## Summary

- **HIGH:** 2 (race in `_playback_interrupt_listener` thread; sleep/wake multi-writer flag)
- **MED:** 4 (wakeword reader silent error; LLM stream broken history pair; TTS synth broken history pair; follow-up loop mic-state suppress + inline routing gap; StateManager unlocked mutation)
- **LOW:** 4 (TeensyBridge return-value ignored; iris_web TTS conflict; iris_web config R/W race; serial-bridge UDP rule by convention)

The pipeline is functionally sound for the happy path. The recurring pattern in defects is **partial failure paths**: code handles success cleanly, but exception paths leave state machines (conversation_history, sleep flag, mic stream) out of sync without compensating cleanup.

*End Task 1.*

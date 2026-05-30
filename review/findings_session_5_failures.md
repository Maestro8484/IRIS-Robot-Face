# Task 5 — Cross-System Failure Mode Map

**Date:** 2026-05-16
**Reviewer:** Opus 4.7
**Scope:** Runtime behavior for 10 failure scenarios, recovery semantics, user feedback

---

## Scenario a — GandalfAI offline at wakeword fire (Whisper port 10300 unreachable)

**Trace:**

1. Wakeword fires (`assistant.py:273`). Pipeline enters main path.
2. `ensure_gandalf_up(leds, pa)` runs at `assistant.py:312`.
3. `gandalf_is_up()` (line 100) does `socket.create_connection((GANDALF, OLLAMA_PORT=11434), timeout=3)`. Note: probes Ollama port, not Whisper. If Ollama is down, Whisper is presumed down too — reasonable for a fully-offline GandalfAI.
4. WoL packet sent (line 110). `play_wol_beep(pa)` plays ascending 660→880 Hz tone (audio_io.py:251).
5. Spinner LED animation thread starts (`waking_anim`, lines 113-118). Amber pulse.
6. Polls every `WOL_POLL_INTERVAL=5s` up to `WOL_BOOT_TIMEOUT=120s`. Logs `"Waiting for GandalfAI..."` every 5s.
7. If GandalfAI comes up within 120s: continues to record + STT + LLM + TTS as normal.
8. If 120s elapses without GandalfAI coming up: returns `False`. Main loop at `assistant.py:313-314` then does `leds.show_error()` + 2s sleep + `show_idle_for_mode(leds)` + `continue` — returns to wakeword wait.

**Recovery:** Auto-recover IF GandalfAI boots within 120s. After 120s timeout: silent return-to-idle, requires user to re-trigger wakeword.

**User feedback:**
- ✅ Ascending 2-tone beep (660→880 Hz, 360 ms) plays immediately when WoL packet sent — S46 feature.
- ✅ Amber spinner animation on LEDs throughout the wait.
- ❌ No audio cue when 120s timeout fires. LED flashes red 0.6s (`show_error`), then returns to idle — no spoken explanation.

**Severity:** **MED.** Auto-recovery exists for the common case (GandalfAI booting). The 120s timeout failure is silent — user re-triggers wakeword, same thing happens, no diagnostic info.

---

## Scenario b — Kokoro down (port 8004) + Piper fallback down (port 10200)

**Trace:**

1. STT succeeds (assumes Whisper still up). LLM responds.
2. `synthesize(reply)` called at `assistant.py:557` → `tts.py:151`.
3. `KOKORO_ENABLED=True` (config.py:36) → `_synthesize_kokoro(text)` at tts.py:171.
4. Inside `_synthesize_kokoro` (tts.py:27): `requests.post(url, json=payload, timeout=30)`. Timeout = 30s.
5. If Kokoro is down: `requests.exceptions.ConnectionError` raised within ~1s (TCP reset) or after 30s (filtered/dropped).
6. Exception caught at `tts.py:172-173`: `print("[KOK] Failed: ... -- falling back to Piper")`.
7. `_synthesize_piper(text)` called at tts.py:174.
8. Inside `_synthesize_piper` (tts.py:42): `socket.create_connection((GANDALF, PIPER_PORT=10200), timeout=60)`.
9. If Piper is also down: socket connection raises within ~1s (refused) or after 60s.
10. `_synthesize_piper` raises uncaught → propagates up through `synthesize()` → `assistant.py:559-562` catches as bare `Exception`.
11. `[ERR] TTS: <exception>` logged. `leds.show_error()` + 1s sleep + `show_idle_for_mode(leds)` + `continue`.

**Recovery:** No auto-recovery on the failed turn. Next turn behaves identically. The user's last reply is lost — `state.conversation_history` has the user turn appended (assistant.py:516) but no assistant turn was appended (line 570 not reached because of `continue`). History is now structurally malformed (unmatched trailing user turn) — see Task 1 Finding 1.2.

**User feedback:**
- ❌ No spoken error. LED flashes red 0.6s. User hears nothing of the reply.
- Worst case: 30s Kokoro timeout + 60s Piper timeout = ~90s of silence with LED animation, then red flash, then idle. User likely assumes the system hung.

**Severity:** **HIGH.** Complete TTS outage produces a silent, ambiguous failure. The 90s worst-case timeout is far worse than a fast-fail.

---

## Scenario c — Kokoro down, Piper available

**Trace:**

1. Same as scenario b through step 7.
2. `_synthesize_piper` succeeds, returns PCM bytes.
3. `play_pcm_speaking` plays Piper audio normally.

**Recovery:** Auto-recover. Each subsequent turn re-tries Kokoro first (no caching of "Kokoro is down" state), so once Kokoro returns, system reverts to Kokoro automatically.

**User feedback:**
- ❌ Voice character changes audibly (Kokoro `bm_lewis` British male → Piper `en_US-ryan-high` US male). No explicit warning that fallback engaged.
- Log shows `[KOK] Failed: ... -- falling back to Piper` — visible only in journalctl / web UI logs, not to the user.

**Severity:** **LOW.** Graceful degradation works as designed. Voice character change is acceptable for TTS-still-functional scenario.

---

## Scenario d — Teensy serial `/dev/ttyACM0` unresponsive mid-session

**Trace:**

1. Any `teensy.send_emotion()` or `teensy.send_command()` call.
2. `TeensyBridge.send_command` (teensy_bridge.py:74-89):
   ```python
   with self._lock:
       if self._ser is None or not self._ser.is_open:
           return False
       try:
           self._ser.write(...)
           ...
           return True
       except (serial.SerialException, OSError) as e:
           print(f"[EYES] Send failed: {e}", flush=True)
           try: self._ser.close()
           except Exception: pass
           self._ser = None
           return False
   ```
3. On serial failure: returns False, closes the port, sets `_ser = None`.
4. The background `_reader` thread (line 23-47) polls every 5s and attempts `_open()` again. If Teensy comes back, `_ser` is repopulated.
5. **Callers in `assistant.py` do not check the return value.** All `teensy.send_emotion(...)` / `teensy.send_command(...)` / `emit_emotion(...)` calls drop the bool silently.
6. During the disconnect window: every Teensy command returns False. LEDs continue working (separate driver). Eyes and mouth display whatever they were displaying when the serial dropped — frozen.
7. When `_reader` reopens, the next `send_command` succeeds. No catch-up of missed commands.

**Recovery:** Auto-recover on reconnect (within 5s polling interval). Missed commands during the gap are permanently lost.

**User feedback:**
- ❌ Eyes/mouth freeze at last state. LEDs continue normally so user sees LEDs animate but eyes static.
- ❌ No audio feedback.
- Log shows `[EYES] Send failed: ...` once per failed send, then `[EYES] Serial disconnected -- will retry` from the reader thread.

**Severity:** **MED.** Visual degradation, no functional loss of voice pipeline. The asymmetry (LEDs animate, eyes don't) is a visible hint to the user.

---

## Scenario e — `iris_config.json` malformed JSON at startup

**Trace:**

`pi4/core/config.py:213-244`:

```python
try:
    with open(_CONFIG_PATH) as _f:
        _cfg = _json.load(_f)
    ...
    print(f"[CFG] iris_config.json loaded: ...")
except FileNotFoundError:
    print(f"[CFG] iris_config.json not found, using defaults", flush=True)
except _json.JSONDecodeError as _e:
    print(f"[CFG] iris_config.json parse error: {_e} -- using defaults", flush=True)
except Exception as _e:
    print(f"[CFG] iris_config.json load failed: {_e} -- using defaults", flush=True)
```

1. `json.load` raises `JSONDecodeError`.
2. Caught at line 240. Logs `[CFG] iris_config.json parse error: <msg> -- using defaults`.
3. All module-level constants retain their defaults from lines 11-153.
4. Assistant continues startup with full defaults.

**Recovery:** Auto-recover on next assistant restart — defaults take effect immediately. User's customizations are silently ignored until the JSON is fixed. The bad JSON file is NOT auto-repaired.

**User feedback:**
- ❌ No user-facing feedback. Web UI may load the config and show whatever happens to be in the (broken) file via `read_cfg()` (iris_web.py:21-23), which silently returns `{}` on parse failure. UI shows blank/default form fields — inconsistent with the assistant's actually-loaded defaults but only if the user opens the web UI.
- Log shows the parse error.

**Severity:** **MED.** Silent loss of user customizations. The fallback to defaults is the safest behavior, but a user noticing "OWW_THRESHOLD reverted to 0.9" without knowing why is a debug-hostile failure mode.

---

## Scenario f — Ollama response with no `[EMOTION:X]` tag

**Trace:**

1. `stream_ollama` iterates response chunks.
2. `extract_emotion_from_reply` semantics inside the streaming loop (llm.py:100-108):
   ```python
   if not emotion_done:
       stripped = buffer.lstrip()
       m = EMOTION_TAG_RE.match(stripped)
       if m:
           emotion = m.group(1).upper()
           ...
       elif len(buffer) > 40:
           emotion_done = True   # no tag found after 40 chars -> NEUTRAL
   ```
3. After 40 chars of buffer with no tag match, `emotion = "NEUTRAL"` (initial value, line 89) is locked in.
4. First yield emits `(chunk, "NEUTRAL")`. `emit_emotion(teensy, leds, "NEUTRAL")` at assistant.py:531.
5. Rest of response plays normally.

**Recovery:** Not a failure — graceful default. Emotion is NEUTRAL, eyes/mouth/LEDs go to neutral state. No state corruption.

**User feedback:**
- ✅ Voice still plays.
- ✅ Eyes/mouth show NEUTRAL expression.
- No error, no warning.

**Severity:** **LOW.** This is design-intended behavior, not a failure. Listed here per task spec but the answer is "system handles it correctly."

---

## Scenario g — Ollama response with emotion tag not in `VALID_EMOTIONS`

**Trace:**

1. `stream_ollama` extracts `emotion = m.group(1).upper()` at llm.py:103.
2. Validation at lines 104-105:
   ```python
   if emotion not in VALID_EMOTIONS:
       emotion = "NEUTRAL"
   ```
3. Same downstream path as scenario f.

**Recovery:** Graceful default to NEUTRAL.

**User feedback:** Identical to scenario f. The unknown emotion is silently stripped — user sees NEUTRAL eyes/mouth/LEDs. Log shows `[EYES] Emotion from LLM: NEUTRAL` (assistant.py:121, only printed in `ask_ollama` path; the streaming path at assistant.py:530 doesn't log the emotion explicitly).

**Severity:** **LOW.** Same as scenario f — by-design fallback. The pre-S47 AMUSED gap was exactly this scenario: `[EMOTION:AMUSED]` emitted by LLM, stripped to NEUTRAL with no visible cue.

---

## Scenario h — Wakeword fires during sleep mode while GandalfAI is offline

**Trace:**

1. `/tmp/iris_sleep_mode` exists → enters sleep-wake branch at `assistant.py:295-310`.
2. `_do_wake(teensy, leds)` at line 297. This sends `EYES:WAKE`, `MOUTH:0`, `MOUTH_INTENSITY:8` to Teensy, sets `state.eyes_sleeping = False`, removes the sleep flag, shows idle LEDs.
3. `ensure_gandalf_up(leds, pa)` at line 298.
4. WoL beep plays immediately. Spinner anim starts.
5. If GandalfAI boots within 120s: continues to greeting TTS.
   - `synthesize(greeting)` at line 305. `play_pcm_speaking` plays "Good morning." / "Good evening." / "Hello." depending on hour.
6. If GandalfAI does NOT boot within 120s: `ensure_gandalf_up` returns False. assistant.py:299-301 calls `leds.show_error()` + 2s sleep + `show_idle_for_mode(leds)` + `continue`.
7. **`state.eyes_sleeping` is now False** (set by `_do_wake` at step 2) but the sleep window is still in effect. The user has woken IRIS but no greeting plays.
8. Main loop returns to wakeword wait. The flag file is gone. The assistant is now "awake" but unable to do anything until GandalfAI boots.
9. If the assistant later detects another wakeword: it tries to record + transcribe, but Whisper is unreachable. `transcribe()` raises (`socket.timeout` or `ConnectionError`); caught at assistant.py:340-343, `[ERR] STT: ...` logged, returns to idle.
10. **In sleep window**: at end of main loop iteration (after `continue`), `in_sleep_window()` check at line 644 will fire because the hour is still ≥21 or <8. `return_to_sleep(teensy, state)` runs — sets `state.eyes_sleeping = True` and recreates `/tmp/iris_sleep_mode`. BUT this only happens at the end of a *successful* iteration (line 645). The failure paths use `continue` which skips line 644-645.

**Edge case:** After failed-wake during sleep window, IRIS stays in an inconsistent state — `state.eyes_sleeping` is False, sleep flag is absent, but the LEDs are showing idle. User triggers wakeword again, same failure cycle. Sleep flag only restored when a successful turn completes inside the sleep window.

**Recovery:** Eventual auto-recover when GandalfAI comes back online. State inconsistency window between failed wake and next successful turn.

**User feedback:**
- ✅ WoL beep plays — confirms wakeword was heard.
- ✅ Eyes wake (LEDs change from sleep breathe to idle breathe).
- ✅ Spinner anim during wait.
- ❌ No spoken explanation when timeout fires. Red flash + return to idle.
- ❌ Inconsistent state (LEDs idle, flag absent) gives no indication IRIS is still in sleep window.

**Severity:** **MED.** The functional path works (eyes wake, beep plays, system tries to bring up GandalfAI). The state inconsistency on timeout is a latent bug — IRIS appears awake but the sleep window is still active, and subsequent failed turns don't restore the sleep flag.

---

## Scenario i — Pi4 unexpected reboot, overlayfs RAM layer cleared

**Trace:**

1. Pi4 boots. Filesystem mounts overlayfs with SD as lower layer and RAM as upper.
2. RAM layer is empty (just rebooted). All writes since last persist are gone.
3. `/home/pi/iris_config.json` resolves to the SD copy (`/media/root-ro/home/pi/iris_config.json`). Whatever was last persisted via `/api/persist_config` is the active config.
4. If user made web-UI changes after last persist: those changes are gone. The web UI's `read_cfg()` (iris_web.py:21-23) re-reads the (now SD-backed) file and shows the persisted state — UI is consistent with reality.
5. **If `/api/persist_config` was missing the chown step** (Task 2 Finding HIGH-1): the SD copy of `iris_config.json` is root-owned. On boot, `assistant.service` runs as user `pi`. `config.py:215` does `open(_CONFIG_PATH)` which reads the file — read permission on root-owned 644 file is fine, so config loads correctly. But any subsequent `write_cfg()` call from iris_web (also user `pi`) would fail because the file is root-owned and likely 644 (not pi-writable). Per IRIS_ARCH.md "S22B post-mortem" this is the documented silent-failure path: web UI saves appear to succeed but the file write actually fails.
6. ALSA state at `/var/lib/alsa/asound.state` — if last persisted, audio comes up correctly via `alsa-init.sh`. If not persisted since last edit, the per-reboot ALSA defaults apply.
7. `assistant.service` and `iris-web.service` start automatically.
8. Wakeword listener boots. `state.eyes_sleeping = False` (StateManager init defaults). `/tmp/iris_sleep_mode` is on tmpfs — cleared by reboot. If reboot happens in sleep window, IRIS comes up *awake* but should be sleeping until 7:30 AM cron triggers.

**Recovery:** Partial auto-recovery. Config and ALSA recover to last-persisted state. Sleep state is **lost** — reboot in sleep window leaves IRIS awake until next cron trigger.

**User feedback:**
- ❌ No notification of reboot. User sees IRIS idle (LEDs animating, eyes neutral) at a time when it should be asleep. May confuse users monitoring overnight.
- ❌ If S22B chown bug is present and a config save happens post-reboot: silent failure mode triggers (assistant.py reload no longer picks up changes).

**Severity:** **MED → HIGH** depending on whether `/api/persist_config` chown bug is active. If chown is missing (Task 2 Finding 2.2 confirmed HIGH), this reboot scenario degrades the entire web UI silently — the S22B cascade.

---

## Scenario j — Follow-up loop receives Whisper hallucination on turn 2 or 3

**Trace (assistant.py:582-635):**

1. Initial turn completes. `implies_followup(reply)` returns True (reply ends with "?"). Loop entered.
2. Turn 2: `record_followup` records audio. `transcribe()` returns hallucination, e.g., "Thank you for watching".
3. Hallucination gate at lines 600-604:
   ```python
   if _text_norm in _WHISPER_HALLUCINATIONS:
       print(f"[FLWP] Hallucination filtered: '{text}'", flush=True); break
   if any(p in _text_norm for p in ("www.", ".gov", ".com", ".org", "for more information", "subscribe", "don't forget")):
       print(f"[FLWP] Hallucination filtered: '{text}'", flush=True); break
   ```
4. "Thank you for watching" → IS in `_WHISPER_HALLUCINATIONS` set (audio_io.py:42). Caught at line 601, `break`.
5. **However** there's a subtler case: a hallucination that's NOT in the set. The set has ~15 phrases. Common Whisper hallucinations not in the set: "Translated by", "Subtitle by", "...", etc. These pass the filter and go to `ask_ollama()` at line 614.
6. `ask_ollama()` appends the hallucinated user turn to history (line 134), queries Ollama, appends assistant reply (line 138). User sees IRIS respond to a phantom utterance.

**Recovery:** No recovery from a hallucination-not-in-set. The conversation continues with phantom turn appended to history. Subsequent turns include the phantom in context.

**User feedback:**
- ✅ Polite dismissals (`FOLLOWUP_DISMISSALS`) caught at line 605, follow-up ends cleanly.
- ✅ Known hallucinations caught and follow-up ends silently.
- ❌ Novel hallucinations slip through — IRIS speaks an unprovoked reply. User confused.
- ❌ History is poisoned with phantom user turn.

**Severity:** **MED.** Most hallucinations are in the set, so this is a low-frequency failure. When it occurs, the false response is conversationally jarring and pollutes context for the rest of the session.

---

## Summary Table

| Scenario | Auto-recover | User feedback | Severity |
|---|---|---|---|
| a — GandalfAI offline at wake | Yes (within 120s) / No (after timeout) | WoL beep + amber spinner; red flash on timeout | MED |
| b — Kokoro + Piper both down | No (per turn) | Long silence + red flash | **HIGH** |
| c — Kokoro down, Piper up | Yes (per turn, no caching) | Audible voice change | LOW |
| d — Teensy serial unresponsive | Yes (5s reconnect) | Eyes/mouth frozen, LEDs animate | MED |
| e — Malformed iris_config.json | Yes (defaults used) | No user feedback; web UI shows blank | MED |
| f — No emotion tag | Yes (NEUTRAL default) | Normal response, NEUTRAL face | LOW |
| g — Unknown emotion tag | Yes (NEUTRAL default) | Normal response, NEUTRAL face | LOW |
| h — Wake-during-sleep + GandalfAI offline | Eventually | WoL beep, spinner, red flash | MED |
| i — Pi4 reboot, overlayfs cleared | Partial | None; sleep flag lost | MED→HIGH (with chown bug) |
| j — Follow-up loop hallucination | Set-based filter (incomplete) | Phantom IRIS response | MED |

---

## Top 3 Highest-Severity Unhandled Failures — Minimal Graceful Degradation

### 1. Scenario b — Both TTS engines down (HIGH)

**Current behavior:** Up to 90s of silence, then red flash, no spoken explanation.

**Minimal degradation path (3 sentences):**
Cache "Kokoro is down" / "Piper is down" state for 60s after first failure to fast-fail subsequent attempts. If both fail, play a pre-synthesized error beep (already exists as `play_beep`) plus a short LED sequence distinct from generic error flash to signal "TTS unavailable". Log the failure to `iris_intent.log` so the web UI Logs tab shows it.

### 2. Scenario i — Pi4 reboot with S22B chown bug active (HIGH if chown bug present)

**Current behavior:** Web UI saves silently fail after reboot if `/api/persist_config` was used post-reboot without an intervening chown. Documented in IRIS_ARCH.md "Pi4 - api_persist_config Ownership Bug" but not fixed in current code (Task 2 Finding 2.2).

**Minimal degradation path:**
Add `sudo chown pi:pi {SD_CONFIG}` to the `/api/persist_config` bash command in iris_web.py:281-285. This is a 1-line fix that prevents the documented April 16-18 cascade. No new tests required — the existing `_sd_synced()` md5 check already validates the copy.

### 3. Scenario h — Wake-during-sleep timeout leaves inconsistent state (MED, but high-frequency)

**Current behavior:** If `ensure_gandalf_up` returns False after wake, `_do_wake` already cleared `state.eyes_sleeping` and `/tmp/iris_sleep_mode`. The failure path `continue`s, skipping the `in_sleep_window` check at the end of the loop iteration. IRIS is awake without GandalfAI in sleep window.

**Minimal degradation path:**
After the `ensure_gandalf_up` failure in the sleep-mode branch (assistant.py:299-301), call `return_to_sleep(teensy, state)` before `continue`. This restores `state.eyes_sleeping = True` and recreates the flag file. Optionally play a short failure tone (different from WoL beep) to inform the user the wake attempt did not complete.

---

*End Task 5.*

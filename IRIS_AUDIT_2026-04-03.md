# IRIS System Audit — 2026-04-03
Read-only diagnostic. No changes made.

---

## STEP 1 — FILE STRUCTURE INTEGRITY

| File | Status |
|---|---|
| `pi4/core/config.py` | [OK] present, non-empty |
| `pi4/assistant.py` | [OK] present, non-empty (root-level, not core/) |
| `core/assistant.py` | [SKIP] Does not exist — by design; assistant.py lives at pi4/ root |
| `core/led_controller.py` | [SKIP] Does not exist — by design; LED is in hardware/led.py |
| `pi4/services/tts.py` | [OK] |
| `pi4/services/stt.py` | [OK] |
| `pi4/services/wakeword.py` | [OK] |
| `pi4/state/state_manager.py` | [OK] |
| `pi4/hardware/teensy_bridge.py` | [OK] |
| `pi4/hardware/led.py` | [OK] (repo = 10% brightness version, pending deploy) |
| `pi4/hardware/audio_io.py` | [OK] (not read but present per glob) |
| `pi4/hardware/io.py` | [OK] |
| `pi4/iris_sleep.py` | [WARN] see Step 5 |
| `pi4/iris_wake.py` | [WARN] see Step 5 |
| `SNAPSHOT_LATEST.md` | [OK] present, dated 2026-04-02 S3 |
| `CLAUDE.md` | [OK] |

---

## STEP 2 — CONFIG CONSISTENCY CHECK

| Check | Result |
|---|---|
| `ELEVENLABS_ENABLED` | [WARN] Default=`True` in config.py. Only False via iris_config.json override. If that file is lost, ElevenLabs activates. |
| `OLLAMA_HOST` | [OK] `GANDALF=192.168.1.3`, `OLLAMA_PORT=11434` → `http://192.168.1.3:11434` |
| `STT_HOST` | [OK] `GANDALF:WHISPER_PORT` = `192.168.1.3:10300` |
| `TTS_HOST` | [OK] `GANDALF:PIPER_PORT` = `192.168.1.3:10200` |
| `WAKEWORD_HOST` | [OK] `127.0.0.1:10400` |
| `NUM_PREDICT` | [FAIL] config.py default = **150**. NOT overridden in iris_config.json. Audit requires 120. The jarvis-kids modelfile has `num_predict 120` baked in, but the API call sends `"options": {"num_predict": NUM_PREDICT}` = 150, which **overrides** the modelfile value. |
| `iris_config.json` (live Pi4) | `{"OWW_THRESHOLD": 0.9, "ELEVENLABS_ENABLED": false, "CHATTERBOX_ENABLED": true}` |
| `OWW_THRESHOLD` | [WARN] Live Pi4 = **0.9** (via iris_config.json). config.py default = 0.85. Memory says expected is 0.85. Inconsistency — current live value is tighter. |
| `VOL_MAX` | [WARN] NOT in iris_config.json. config.py default = 127. But main() hardcodes `set_volume(110)` on startup. Effective startup volume = 110. Memory says VOL_MAX=110 in iris_config.json — this is **outdated/wrong**; it's a hardcoded call, not a config override. |

---

## STEP 3 — EMOTION / MOUTH / LED ALIGNMENT

| Check | Result |
|---|---|
| `emit_emotion()` signature | [OK] Calls `send_emotion(emotion)` + `send_command(MOUTH:n)` + `show_emotion(emotion)` in one call. All three dispatched together. |
| MOUTH_MAP coverage | [WARN] Covers 0–7 (NEUTRAL through CONFUSED). **SLEEP:8 is absent.** MOUTH:8 is only sent explicitly by iris_sleep.py via raw UDP, not via emit_emotion. Functionally works but not aligned with audit spec. |
| LED color table | [OK] All 8 emotions verified in `_EMOTION_LED`: NEUTRAL=cyan, HAPPY=warm yellow, CURIOUS=bright cyan, ANGRY=red, SLEEPY=dim purple, SURPRISED=white flash→cyan, SAD=dim blue, CONFUSED=magenta. All correct. |
| CONFUSED dispatch | [OK] `emit_emotion(teensy, leds, "CONFUSED")` dispatches EMOTION:CONFUSED + MOUTH:7 + LED magenta. No special-casing needed. |

---

## STEP 4 — SERIAL COMMAND INTEGRITY

| Check | Result |
|---|---|
| Serial port path | [OK] `TEENSY_PORT="/dev/ttyACM0"` from config.py. No hardcoding elsewhere. |
| `EMOTION:X` format | [OK] `send_emotion` writes `f"EMOTION:{emotion}\n"` |
| `MOUTH:n`, `EYES:SLEEP/WAKE`, `EYE:n` | [OK] All go through `send_command(cmd)` which writes `f"{cmd}\n"` |
| Duplicate writes | [OK] No duplicate sends found on same event |
| `FACE:1/FACE:0` inbound | [WARN] Received and logged (`[EYES] << FACE:1`). Confirmed in live journal. Not stored in state or used to gate behavior. No state.face_detected field. This is intentional per current design but limits future use. |
| Serial ownership | [OK] Only TeensyBridge opens `/dev/ttyACM0`. All others use UDP → CMD_PORT. |

---

## STEP 5 — SLEEP / WAKE PIPELINE

### iris_sleep.py

| Check | Result |
|---|---|
| Sends EYES:SLEEP before /tmp flag | [OK] UDP EYES:SLEEP → assistant.py CMD listener creates the flag |
| Sends MOUTH:8 | [OK] UDP `MOUTH:8\n` sent |
| Piper TTS "Goodnight" | [FAIL] **Pi4 live version does NOT call Piper TTS.** Pi4 iris_sleep.py is a diverged version that only sends UDP commands. Repo version has the Piper call but Pi4 never received it. |
| sleep 20 delay | [FAIL] Not present in Pi4 version or repo version. |
| CMD_PORT usage | [WARN] Pi4 version imports `CMD_PORT` from `core.config`. Repo version hardcodes `CMD_PORT = 10500`. The two versions have diverged. |

### iris_wake.py

| Check | Result |
|---|---|
| Sends EYES:WAKE | [OK] UDP `EYES:WAKE\n` sent |
| Sends MOUTH:0 | [OK] UDP `MOUTH:0\n` sent |
| Removes /tmp/iris_sleep_mode | [OK] Done by assistant.py CMD listener when it processes EYES:WAKE |
| "Good morning" TTS | [OK] In assistant.py wakeword-during-sleep handler (lines 465–470), not in iris_wake.py itself. Correct by design — cron wake does NOT speak; only wakeword-during-sleep does. |

### assistant.py sleep-mode handling

| Check | Result |
|---|---|
| `show_sleep()` LED animation | [FAIL] **`leds.show_sleep()` is NEVER CALLED anywhere in assistant.py** (repo or live Pi4). Sleep LED stays on whatever animation was last running. Pi4 led.py has the method but it's dead code. |
| `state.eyes_sleeping = False` in wakeword-during-sleep path | [FAIL] Lines 458–471: `os.remove('/tmp/iris_sleep_mode')` and Teensy EYES:WAKE are sent, but `state.eyes_sleeping` is never set to False. State remains inconsistent until next interaction triggers the auto-wake at line 531. Results in a redundant EYES:WAKE command on the very next interaction. Low severity but wrong. |

---

## STEP 6 — VOICE PIPELINE END-TO-END

| Stage | Result |
|---|---|
| Wakeword → OWW:10400 | [OK] subprocess + socket.create_connection("127.0.0.1", OWW_PORT) |
| OWW → STT Whisper:10300 | [OK] Wyoming protocol, timeout=30 |
| `[EMOTION:X]` tag strip | [OK] `extract_emotion_from_reply()` strips before TTS |
| Ollama gemma3:27b @ 192.168.1.3:11434 | [OK] |
| Dispatch: EMOTION+MOUTH | [OK] `emit_emotion()` fires before TTS synthesis |
| Dispatch: LED | [OK] via `emit_emotion → show_emotion()` |
| Dispatch: TTS | [WARN] Not truly parallel — serial: emit_emotion → synthesize → play. LED and emotion are set *before* speaking, but TTS itself is not parallelized with serial sends. This is acceptable behavior but differs from audit spec wording "parallel dispatch". |
| TTS routing: Chatterbox → ElevenLabs → Piper | [OK] CHATTERBOX_ENABLED=True, ELEVENLABS_ENABLED=False (iris_config.json), Piper fallback |
| play_pcm_speaking | [OK] 3x gain applied in audio_io.py |
| End-to-end tested | [WARN] Per snapshot: **not yet tested.** iris_voice.wav not uploaded to Chatterbox. Voice clone will fail silently on first live run, fall through to Piper. |

---

## STEP 7 — KIDS MODE

| Check | Result |
|---|---|
| Voice toggle → jarvis-kids model | [OK] `state.kids_mode = True` → `get_model()` returns `OLLAMA_MODEL_KIDS` |
| Yellow LED on entry | [OK] `show_kids_mode_on()` (3x yellow flash) then `show_idle_kids()` (yellow breathe) |
| Extended thresholds | [OK] KIDS_RECORD_SECONDS=14, KIDS_SILENCE_SECS=3.5, KIDS_SILENCE_RMS=150, KIDS_FOLLOWUP_TIMEOUT=15 |
| Context timeout 300s | [OK] Not separately overridden for kids mode; watchdog uses CONTEXT_TIMEOUT_SECS=300 |

---

## STEP 8 — CONTEXT TIMEOUT + HISTORY MANAGEMENT

| Check | Result |
|---|---|
| 300s idle reset | [OK] `_context_watchdog()` thread polls every 30s, clears on 300s elapsed |
| History cleared properly | [OK] `state.clear_conversation()` clears list + person context |
| No accumulation leak | [OK] `ask_ollama()` enforces 20-message rolling window (pops 2 when > 20) |

---

## STEP 9 — NETWORK DEPENDENCY HEALTH

| Service | Timeout | Fallback | Result |
|---|---|---|---|
| Ollama | 30s | `leds.show_error()` + continue | [OK] |
| Whisper STT | 30s | `leds.show_error()` + continue | [OK] |
| Chatterbox TTS | 60s | Falls to ElevenLabs → Piper | [OK] |
| ElevenLabs TTS | 15s | Falls to Piper | [OK] |
| Piper TTS | 60s | No fallback (final tier) | [OK] — if Piper fails, exception propagates to TTS error handler in main loop |
| WoL / GandalfAI | 120s poll, 5s interval | `leds.show_error()` + continue | [OK] |
| Weather (wttr.in) | 6s | Returns "I could not get the weather" string | [OK] |
| Vision / Person recog | 30s | Exception caught, sets person=None | [OK] |

---

## STEP 10 — OVERLAYFS / PERSISTENCE AUDIT

| Check | Result |
|---|---|
| `assistant.py` RAM vs SD md5 | [OK] Both = `ea6639c5ee2604194431a9af030546dc` |
| `assistant.py` Pi4 vs repo md5 | [WARN] Pi4=`ea6639c5`, repo=`ffb0cdd4`. **MISMATCH.** Likely CRLF (Windows repo vs Linux Pi4) but not fully verified. Pi4 may also have minor code differences. |
| `led.py` RAM vs SD md5 | [OK] Both = `2119c2e82e8201a3a8b58a0956778226` |
| `led.py` Pi4 vs repo md5 | [FAIL] Pi4=`2119c2e8`, repo=`c4f2f5ac`. **Expected mismatch** (pending 10% brightness deploy), but see CRITICAL ISSUE #2. |
| `iris_config.json` | [OK] `{"OWW_THRESHOLD": 0.9, "ELEVENLABS_ENABLED": false, "CHATTERBOX_ENABLED": true}` |
| `assistant.service` | [OK] enabled, active (running) since 2026-04-02 23:52 MDT |
| Cron — sleep | [OK] `0 21 * * *` = 9:00 PM ✓ |
| Cron — wake | [OK] `30 7 * * *` = 7:30 AM ✓ |
| Bonus cron | [INFO] `0 3 * * 0 sudo iris_backup.sh` — weekly Sunday backup, not audited |

---

## CRITICAL ISSUES (FAIL)

1. **`leds.show_sleep()` never called anywhere.**
   Pi4 `led.py` has `show_sleep()` implemented. Neither repo nor live Pi4 `assistant.py` ever calls it. When EYES:SLEEP arrives (via cron or web UI), the LED just freezes on whatever was last displayed. Sleep LED indigo breathe is silently broken.

2. **Pending repo `led.py` deploy will permanently destroy `show_sleep()`.**
   The 10% brightness rewrite in `pi4/hardware/led.py` removed `show_sleep()` and the `brightness` parameter from `_write()`. Deploying it as-is will make the sleep LED fix impossible without another rewrite. **Do not deploy the current repo led.py without first merging `show_sleep()` back in.**

3. **`NUM_PREDICT = 150`, not 120.**
   config.py default is 150, iris_config.json has no `NUM_PREDICT` key. The Ollama API call sends `"options": {"num_predict": 150}` which overrides the jarvis-kids modelfile's `num_predict 120`. Add `"NUM_PREDICT": 120` to iris_config.json to fix, or change config.py default.

4. **`iris_sleep.py` on Pi4 does not call Piper TTS "Goodnight".**
   Pi4 version and repo version of iris_sleep.py have diverged. Pi4 version only sends UDP commands; no spoken "Goodnight." The repo version has the Piper call but also has hardcoded `CMD_PORT = 10500` instead of importing from config. Neither version is correct-and-complete.

5. **`state.eyes_sleeping` not reset in wakeword-during-sleep path.**
   `assistant.py` lines 458–471: when a wakeword fires during sleep, the code removes `/tmp/iris_sleep_mode` and sends `EYES:WAKE` to Teensy — but never sets `state.eyes_sleeping = False`. The first real voice interaction after this will redundantly re-send EYES:WAKE (harmless but wrong state).

---

## WARNINGS

1. **`ELEVENLABS_ENABLED = True` is the hardcoded config.py default.** Only False because of iris_config.json. If that file is deleted, reset, or malformed, ElevenLabs activates on next restart and burns credits.

2. **`OWW_THRESHOLD` mismatch.** Live Pi4 = 0.9 (iris_config.json). config.py default = 0.85. Last documented intent (memory) was 0.85. Current live setting is more restrictive (fewer false positives but harder to trigger). Verify intent.

3. **iris_sleep.py/iris_wake.py: repo and Pi4 versions diverged.** Pi4 versions import CMD_PORT from core.config (better) but lack the spoken "Goodnight" TTS. Repo versions have TTS but hardcode CMD_PORT. A single canonical version should be established and deployed.

4. **Pending firmware flash still outstanding.** `src/mouth.h` (normal intensity 0x01), `src/main.cpp` (PersonSensor LED off), `src/sleep_renderer.h` (starfield boost) — all edited, not flashed. Mouth brightness awake == sleep (both 0x01) until this flash.

5. **End-to-end voice pipeline untested.** iris_voice.wav not uploaded to Chatterbox. Chatterbox will fail on first real run (voice not found), fall through to Piper. Voice clone unverified.

6. **`MOUTH_MAP` has no `SLEEP:8` entry.** SLEEP is intentionally separate from the emotion system, but this diverges from the audit spec which lists SLEEP(8) as a required entry.

7. **`FACE:1/FACE:0` inbound not reflected in state.** Teensy sends tracking state but `state.py` has no `face_detected` field. Currently just logged. No behavioral gating.

8. **`assistant.py` repo vs Pi4 md5 mismatch.** Likely CRLF line endings only, but a byte-level diff was not performed. Cannot guarantee repo and Pi4 are semantically identical.

---

## RECOMMENDED NEXT ACTIONS (by priority)

1. **Fix `led.py` before deploying it.** Port `show_sleep()` and `brightness` parameter from Pi4 version into the repo 10%-brightness version. Then wire `leds.show_sleep()` into the CMD listener (`EYES:SLEEP` handler) and `leds.show_idle_for_mode()` into the `EYES:WAKE` handler. Then deploy.

2. **Add `NUM_PREDICT: 120` to iris_config.json on Pi4** (and persist). Ensures jarvis-kids reply length is actually capped at 120.

3. **Fix `state.eyes_sleeping = False`** in the wakeword-during-sleep handler (assistant.py ~line 462).

4. **Reconcile iris_sleep.py.** Decide: does it speak "Goodnight"? If yes, merge the Piper TTS call into the Pi4 version (which uses config import). If no, update repo to match Pi4. Deploy and persist whichever wins.

5. **Verify `OWW_THRESHOLD` intent.** If 0.85 is desired, update iris_config.json. If 0.9 is the tested sweet spot, update the memory record.

6. **Change `ELEVENLABS_ENABLED` default to `False` in config.py.** Safety net so a missing iris_config.json can't activate billing.

7. **Flash firmware** (mouth.h + main.cpp + sleep_renderer.h) via `/flash`.

8. **Upload `iris_voice.wav`** to Chatterbox web UI (http://192.168.1.3:8004) and run end-to-end voice test.

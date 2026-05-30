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

## 2026-05-03 | S47 | Cross-stack / Emotion

**Symptom:** LLM emits `[EMOTION:AMUSED]` but IRIS displays NEUTRAL. No LED, no mouth, no firmware response to AMUSED.
**Root cause:** AMUSED present in `ollama/iris_modelfile.txt` valid-values but absent from `pi4/core/config.py` VALID_EMOTIONS, MOUTH_MAP, `pi4/hardware/led.py` _EMOTION_LED, and `src/main.cpp` EmotionID enum + parseEmotion. `extract_emotion_from_reply()` drops unknown emotions to NEUTRAL.
**Fix (RD-002):** Full implementation. AMUSED added to all five locations. Mouth reuses index 2 (CURIOUS/smirk). LED: sinusoidal breathe, amber [255,160,0], floor=10, peak=80, period=1.5s, gamma=1.8, duration=3s. Firmware: EmotionID=8, EmotionParams {0.55f, false, 3000}, no eye swap. Kids modelfile: AMUSED added to valid emotion list.
**Files:** `pi4/core/config.py`, `pi4/hardware/led.py`, `src/main.cpp`, `pi4/iris_web.html`, `ollama/iris-kids_modelfile.txt`
**Commit:** pending
**Status:** Fixed

---

## OPEN ISSUES

---

## open | Pi4 / STT

**Symptom:** Single-word utterances ("stop", "quiet") transcribed incorrectly by Whisper — "stop" → "What are you doing?" Intent router then classifies correctly for the hallucinated phrase, not the intended command.
**Root cause:** Whisper is unreliable on sub-1-second audio with minimal phonetic content. Hallucination rate spikes on very short recordings.
**Proposed fix:** Pre-STT RMS duration gate — if post-wakeword audio < ~0.5s, route directly to local keyword match (stop/cancel/quiet) without Whisper. OR add known short-command words to a local keyword list checked before STT.
**Status:** Deferred — Option 1 STOP gate is deployed; pre-STT intercept is not current active scope.

---

## open | GandalfAI / Ollama model — RECURRING

**Symptom:** IRIS personality drifts — robotic/formal responses, flat affect, or adversarial inputs not handled in character. May occur even when NEVER-say block is present in running model.
**Root cause:** Three-way desync: SuperMaster repo / GitHub / GandalfAI running model. `ollama create iris` must be run on GandalfAI after every modelfile commit. GandalfAI clone at `C:\IRIS\IRIS-Robot-Face\` does not auto-pull. Local edits to modelfiles on the GandalfAI clone can also accumulate silently and block `git pull`.
**Confirmed incident (S49 / 2026-05-04):** GandalfAI clone had local uncommitted changes to both `iris_modelfile.txt` and `iris-kids_modelfile.txt` blocking pull. NEVER-say block was present in running model but PT-001 few-shot adversarial examples and/or AMUSED guidance were likely absent or diverged. Resolved via `git reset --hard origin/main` + `ollama create` for both models.
**Pattern:** Personality drift that survives NEVER-say verification but still produces flat/formal affect or poor adversarial handling → suspect PT-001 few-shot block missing from running model.
**Standing rule:** Any LLM drift → run `ollama show iris --modelfile` on GandalfAI. Check for PT-001 few-shot block ("You're dumb." / "Bold start.") in addition to NEVER-say. Compare full SYSTEM block to repo before any persona changes.
**Status:** Open — recurring operational hazard. Expect recurrence. No code fix planned; mitigation is procedural.

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
**Status:** Deferred — LOCAL-PIPER BROKEN, LOW-LOW priority. Not worth fixing until Kokoro primary fails.

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

---

## 2026-05-25 | S63 | Pi4 / WebUI + Teensy serial — USB port swap + sleep mode display bypass

**Symptom:** All webUI buttons (emotion, eye select, mouth, sleep) produce no response on Teensy 4.1 eye displays or TFT mouth. APA LEDs respond to sleep button. Pi4 logs show serial writes (`[EYES] >> EYE:1`) with no Teensy echo (`[EYES] <<`).
**Root cause (primary):** Teensy 4.0 and Teensy 4.1 USB cables were physically swapped on Pi4. Linux `/dev/ttyACM*` device assignment is port-position-based. Swapping USB ports swapped device names: Teensy 4.1 (eye displays) received `/dev/ttyACM1` (expected by base_mount_bridge.py) and Teensy 4.0 (servo/gesture) received `/dev/ttyACM0` (expected by teensy_bridge.py). All eye/mouth commands went to the wrong MCU.
**Root cause (secondary):** Even with correct USB assignment, when `eyesSleeping=true`, Teensy 4.1 `loop()` returns early after `processSerial()`. EMOTION:/EYE:/MOUTH: commands are parsed but the eye engine and mouth TFT are never called. Commands silently "succeed" at the serial level with zero visual output. APA LEDs responded because they are Pi4-driven in `_do_sleep()` before the serial write, not gated by the Teensy sleep state.
**Fix 1:** udev rules in `/etc/udev/rules.d/99-iris-teensy.rules` bind `/dev/ttyIRIS_EYES` and `/dev/ttyIRIS_SERVO` to Teensy hardware USB serial numbers (13625440 and 12763490 respectively). Symlinks survive USB port swaps and Pi4 reboots.
**Fix 2:** `core/config.py` updated: `TEENSY_PORT = "/dev/ttyIRIS_EYES"`, `BASE_MOUNT_PORT = "/dev/ttyIRIS_SERVO"`.
**Fix 3:** CMD listener in `assistant.py` auto-wake: if `state.eyes_sleeping` and EMOTION:/EYE:/MOUTH: command arrives, calls `_do_wake()` before forwarding the command. Display commands no longer silently fail while sleeping.
**Files:** `pi4/scripts/99-iris-teensy.rules` (NEW), `pi4/core/config.py`, `pi4/assistant.py`
**Hard rule added:** Never hardcode `/dev/ttyACM*` in code, config, or commands. Always use `/dev/ttyIRIS_EYES` (Teensy 4.1) or `/dev/ttyIRIS_SERVO` (Teensy 4.0).
**Status:** Fixed and deployed to Pi4 (S63)

---

## open | HW-004 | Teensy 4.0 — PAJ7620U2 gesture sensor dead

**Symptom:** `DIAG: PAJ7620U2 0x73 ACK=NO` and `init=FAIL` on every boot. No gesture commands fire. `pajOk=0` in all telemetry. I2C scan (full 1–127 sweep) finds no device at 0x73 or any valid PAJ7620U2 address (0x13, 0x1B, 0x23, 0x2B, 0x5B, 0x63, 0x6B, 0x73).
**Root cause:** Sensor IC hardware failure. Ruled out: I2C bus fault (Person Sensor 0x62 responds correctly), VIN power (3.3V confirmed with multimeter), SDA/SCL wiring (continuity confirmed to Teensy pins 18/19), VBUS (GY-PAJ7620 5-pin breakout ties VBUS to VIN internally), cold joint on header pins (reflow attempted — no change).
**Fix:** Replace GY-PAJ7620 breakout module. Replacement on order.
**Blocked:** TS40-S1 firmware flash, gesture debounce verify, GESTURE_SENSOR_REQUIRED=True Pi4 deploy.
**Files:** None — firmware complete (TS40-S1 + TS40-S2 REPO-ONLY), blocked on hardware only.
**Status:** Open — BLOCKED on hardware replacement (2026-05-29)

---

## 2026-05-29 | TS40-S1 | Firmware / Teensy 4.0 base mount

**Symptom:** `teensy40_base_mount.ino` carried a full capacitive touch pad subsystem on pin 15 (T3): `TOUCH3_PIN/THRESH/HOLD_MS` defines, `capTouch()` ADC-discharge sampler, `pollTouch3()` with STOP-tap / LISTEN-hold logic and a `DIAG: touch3=` monitor. No such pad was ever physically wired to the board.
**Root cause:** S69 introduced the touch3 code (plus a build-fix comment claiming `touchRead()` is unimplemented in the PlatformIO Teensy 4.x framework) for hardware that was never installed — a hallucinated-hardware addition that shipped as dead weight into S70/S72/TS40-S2.
**Fix:** Removed all touch3 code from the sketch (defines, `capTouch()`, `pollTouch3()` + its SERIAL_DIAG block, the `loop()` call, header pin/trigger comments, build-fix comment). Removed touch3 / pin 15 references from `docs/sysmap.json`, `IRIS_ARCH.md`, `servo_teensy40/README.md`. `LISTEN` preserved as a valid command/action (invoked via FORWARD-gesture default and web UI). Same pass completed the modular split (`person_sensor.*`, `pan_servo.*`, `diag.h`); `.ino` 345 → 94 lines.
**Files:** `servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino`, `person_sensor.h/.cpp` (NEW), `pan_servo.h/.cpp` (NEW), `diag.h` (NEW), `docs/sysmap.json`, `IRIS_ARCH.md`, `servo_teensy40/README.md`
**Status:** Fixed — REPO-ONLY, pending user PlatformIO flash (flash itself blocked by HW-004, dead PAJ7620U2)

---

## 2026-05-29 | S74 | GandalfAI / LLM output contamination — stage directions + ellipsis in TTS

**Symptom:** TTS spoke stage directions aloud ("makes a dramatically disgusted face", "crosses arms and glares") and spoke `...` as "dot dot dot." IRIS response tone was incongruent with adult persona (playful, not dry) on insults. Example webui log: `{NEUTRAL}: Ugh. makes a dramatically disgusted face`.
**Root cause (primary):** GandalfAI `iris` model was running the `iris-kids` SYSTEM prompt. Kids persona has no voice-interface constraints and a more expressive/demonstrative style. GandalfAI clone was at S61b; `iris` model was rebuilt at an unknown point with the wrong modelfile.
**Root cause (secondary):** `clean_llm_reply()` in `pi4/services/llm.py` stripped `*` characters individually — left action-phrase text from `*...*` blocks intact. No ellipsis handling.
**Fix 1 (GandalfAI):** Wrote correct adult `iris_modelfile.txt` to GandalfAI clone. Ran `ollama create iris`. Adult SYSTEM + PT-001 confirmed via `ollama show iris --modelfile`.
**Fix 2 (Pi4 / llm.py):** Added regex passes to strip multi-word `*...*` / `_..._` blocks entirely and collapse `\.{2,}` to `.`.
**Fix 3 (modelfile / identity):** Expanded HOW YOU SPEAK with positive identity framing — "personality lives entirely in word choice, no gesture, no expression, no aside" — making stage directions behaviorally incompatible with the persona rather than explicitly forbidden.
**Files:** `pi4/services/llm.py`, `ollama/iris_modelfile.txt`
**Status:** Fixed — DEPLOYED+VERIFIED S74. Live behavior confirmed by user 2026-05-29: responses clean, adult persona active, no stage directions or ellipsis in TTS output.

---

## 2026-05-30 | S76 | Pi4 / audio_io.py + assistant.py — Emotion expression invisible during speech

**Symptom:** IRIS emits an emotion (HAPPY, ANGRY, SLEEPY, etc.) when the LLM reply arrives, but the emotion mouth is never visible during speech. After speech, NEUTRAL mouth is always restored regardless of what emotion was active. Eyes remain in the emotion's pupil state (SLEEPY drooped, SAD pupil ratio) while IRIS is talking, which looks wrong.
**Root cause (3-part):**
1. `play_pcm_speaking()` used `_SPEAK_FRAMES = [0, 1, 5, 1]` (neutral/happy/surprised cycling) regardless of emotion. Every speech utterance showed the same neutral-to-happy animation overwriting the LLM emotion.
2. No hold between `emit_emotion()` and animation thread start — emotion mouth expression was visible for 0ms before speech animation began.
3. `restore_mouth_idx` defaulted to 0 (NEUTRAL) at every call site — emotion mouth never restored after speech.
**Fix:**
- `play_pcm_speaking()`: per-emotion `_EMOTION_SPEAK_FRAMES` dict; `emotion` parameter; 350ms hold before animation thread; restores to `restore_mouth_idx` (caller-supplied emotion's static mouth index).
- `assistant.py` main LLM path: `_current_emotion` tracking variable; `EMOTION:NEUTRAL` command before speech (resets pupil ratio without changing eye definition); `emotion=_current_emotion` + `restore_mouth_idx=MOUTH_MAP.get(_current_emotion, 0)` passed to `play_pcm_speaking`; `emit_emotion(teensy, leds, _current_emotion)` after speech to restore.
- Follow-up loop: `emotion=emotion, restore_mouth_idx=MOUTH_MAP.get(emotion, 0)` passed through.
**Files:** `pi4/hardware/audio_io.py`, `pi4/assistant.py`
**Status:** Fixed — DEPLOYED+VERIFIED S76. POST 21/22 PASS AUTHORIZED confirmed 2026-05-30.

## 2026-05-30 | S77 | GandalfAI / LLM persona

**Symptom:** IRIS broke character under adversarial/pressure input — produced helpful-AI-assistant boilerplate ("I understand", "as an AI...") regardless of modelfile quality.
**Root cause:** gemma3:27b-it-qat RLHF safety layer overrode the persona system prompt on confrontational input.
**Fix:** Swapped base model to qwen2.5vl:32b-q4_K_M (weaker safety RLHF interference, multimodal preserved); rebuilt iris + iris-kids; sharpened adult persona. Smoke-tested 5/5, zero boilerplate, vision intact.
**File:** `ollama/iris_modelfile.txt`, `ollama/iris-kids_modelfile.txt`
**Commit:** S77
**Status:** Fixed

---

## 2026-05-30 | S79 | Pi4 / SD card full — iris_bench.jsonl unbounded accumulation

**Symptom:** `iris_web.html` deploy failed with "No space left on device" on /media/root-ro. SD card 100% full (29G/29G).
**Root cause:** S67 added a bench JSONL append block to `iris_log_export.sh` that appended new bench records from RAM to `/media/root-ro/home/pi/logs/iris_bench.jsonl` on every 5-min cron tick. No size cap or rotation. Over ~3 weeks this grew to 24GB, filling the 29GB SD partition.
**Fix:** Remounted SD rw, truncated `iris_bench.jsonl` on SD to 0 bytes (freeing 24GB — SD now 19% used). Removed the SD bench append block entirely from `iris_log_export.sh`. Bench data is already archived to GandalfAI `C:\IRIS\iris-logs\` via SCP on every cron run — SD persistence was redundant. RAM bench log at `/home/pi/logs/iris_bench.jsonl` is unaffected.
**Files:** `pi4/scripts/iris_log_export.sh`
**Commit:** S79b
**Status:** Fixed — DEPLOYED+VERIFIED. md5 RAM=SD verified.

---

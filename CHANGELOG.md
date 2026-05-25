<!-- Completed history only. Do not edit prior entries. Append new entries at the bottom. -->

# IRIS Changelog

Entries are in chronological order, oldest first. Active and forward-looking items are in `ROADMAP.md`.

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

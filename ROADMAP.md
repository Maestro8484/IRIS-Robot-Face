<!-- Forward-looking work only. Do not add completed items. Completed history is in CHANGELOG.md. -->

# IRIS Roadmap

All items below are active or queued. Completed work is in `CHANGELOG.md`.

---

## RD-031 — Eliminate log spam / unbounded disk writes  ⚠️ TOP PRIORITY (S130)

**Status:** OPEN — **first-order priority** (user directive S130). A disk/space runout crippled the
Pi4 ~3 weeks ago (≈late May 2026); this item exists to remove every unbounded/high-rate writer so it
can't recur. Dedicated handoff with full detail + model recommendation: `docs/handoff_RD031_logspam.md`.

**Quantified S130 findings (live Pi4):**
- `[SR] frame=N` (Teensy sleep-renderer debug print, relayed by the bridge) = **52%** of the last 5000
  `assistant` journal lines; all `[EYES] >>/<<` serial echo = **60%**. Together ~**90%** of journal
  volume is routine serial traffic — emitted continuously through the ~10 h/night sleep window.
- **journald has no size cap** (`SystemMaxUse`/`RuntimeMaxUse` unset → defaults) on a 1.9 GB overlay.
- `/home/pi/logs` = **48 MB** of daily `iris-YYYYMMDD.log` exports (one 19 MB day), unbounded, no
  retention/rotation (driven by `pi4/scripts/iris_log_export.sh` + `iris-logs.cron`).
- `/home/pi/.cache/pip` ≈ **150 MB** stale wheels/bodies.

**Fix targets (each its own small batch; verify + SD-persist each):**
1. **Firmware** — stop/gate the `[SR] frame=N` print (Teensy sleep renderer; grep `[SR] frame` in
   `src/sleep_renderer*.h` / `src/main.cpp`). Behind a compile-time `DEBUG_SR` flag or removed. REPO-ONLY → flash.
2. **Pi4 bridge** (`pi4/hardware/teensy_bridge.py`) — gate the per-line `[EYES] >>/<<` serial logging
   behind a debug flag, or suppress routine frames (`[SR]`, `SLEEP_CFG:`, repetitive `MOUTH:`). This is
   the systemic fix — even with the firmware print gone, the bridge logging policy is the root spam driver.
3. **journald** — set conservative `SystemMaxUse=` + `RuntimeMaxUse=` (e.g. 50M) in
   `/etc/systemd/journald.conf`. **System-path file — must be persisted to
   `/media/root-ro/etc/systemd/journald.conf` individually** (CLAUDE.md: the `/home/pi` procedure does
   NOT cover system paths — this exact class of miss caused the S63 8 h outage). Restart `systemd-journald`.
4. **Daily log export retention** — add age-based pruning (e.g. delete exports >7 days) to
   `iris_log_export.sh` or a `logrotate` rule; persist the script + cron.
5. **One-time** — prune `/home/pi/.cache/pip`; consider `pip --no-cache-dir` for future installs.
6. **Audit** — confirm SD vs RAM (overlay) location of each writer and which path actually filled space
   before (`/var/log/journal` exists but `du`=0 → journal is effectively in RAM; daily exports may be the
   real SD vector). Sweep for any other append-only/high-rate file.

**Verification:** after fixes, idle/sleep ~10 min, then `journalctl -u assistant -n 5000 | grep -c '\[SR\] frame'`
≈ 0; `journalctl --disk-usage` stable; `du -sh /home/pi/logs` bounded; `df -h` flat over a sleep cycle.

**Deployment gate:** firmware (flash) + Pi4 (explicit auth) + system-path persistence. Higher-risk than
usual — a bad `journald.conf` or a missed SD-persist can brick logging or re-fill space.

**Recommended model: Opus** — cross-layer (firmware + systemd/journald + bridge Python), open-ended audit
("ANY other spam source"), and high-stakes (prior space-exhaustion crippled the device + system-path
persistence discipline). Not a mechanical one-file edit.

---

## RD-032 — WebUI resource monitor + trend collector (S130, sibling of RD-031)

**Status:** Collector **DEPLOYED (S130)**; WebUI panel **OPEN**. Build alongside RD-031 (same Opus session).

**Why:** No historical resource logging existed (no sysstat, no cron) — which is why the May space
runout wasn't caught early. Live snapshot at open was healthy (load ~0.5, 452 MB used / 3.3 GB free,
44.8 °C, `throttled=0x0`, uptime 3.5 d), confirming the risk is slow disk accumulation, not CPU/RAM.

**Done this session — capped trend collector:**
- `pi4/scripts/res_trend.sh` (DEPLOYED `/home/pi/res_trend.sh`, SD-persisted) + cron `* * * * *`.
  Appends one CSV line/min to `/home/pi/logs/res_trend.csv` (load, mem, overlay %, journal size,
  logs MB, temp, throttle) and **self-trims to 4320 lines (~3 days, <500 KB)** — bounded by design,
  RAM-resident, never grows the SD. Read: `tail -n 60 /home/pi/logs/res_trend.csv`. This gives the
  RD-031 session 24–48 h of real trend data to work from.

**Remaining — WebUI panel:**
- Add `/api/sysstat` to `pi4/iris_web.py` returning live load / CPU% / mem / temp / throttle / uptime
  **and disk-first numbers**: overlay % used, `journalctl --disk-usage`, `/home/pi/logs` size. Computed
  on request — **never logged** (don't let the monitor become a writer, per RD-031).
- WebUI card in `iris_web.html` + poll in `iris_web.js` (every ~5–10 s), with the disk/journal/logs
  figures prominent (the actual failure mode) and a small sparkline from `res_trend.csv` if cheap.

**Deployment gate:** Pi4 (explicit auth) + md5 RAM=SD. No firmware. **Recommended model: Opus**
(bundle with RD-031).

---

## RD-033 — Person Sensor probe reliability + face-tracking quality (S130)

**Status:** OPEN — own session (do NOT fold into RD-031; different domain). Recommended model: Opus
(firmware + hardware reasoning + observe-iterate; tracking debug is delicate).

**Symptom (S130):** After the S130 flash, **two consecutive boots logged `[DBG] No Person Sensor found`**
(08:24:45 fresh boot included) and **zero `FACE:` events** were emitted with a face in frame — so the
firmware's loop skips the sensor block entirely (`hasPersonSensor()==false`) and the eyes run autoMove
(autonomous wander), which reads as "brief lock then redirect." A reflash (MCU reset) did **not** restore
detection; only a power cycle (Pi4 reboot / USB unplug) was expected to clear a wedged sensor I2C state.
**S130 power-cycle result: did NOT restore detection.** Pi4 rebooted 08:40 (USB 5V drop → Teensy
power-cycle). Definitive live test: bridge logs every serial line (`teensy_bridge.py:56`, unfiltered), and
a forced step-out→step-in produced **zero `FACE:` events** → firmware is not reading the sensor; eyes run
autoMove. So **reflash (MCU reset) AND power cycle both failed** — rules out a transient probe race;
implicates a **physical I2C connection / sensor fault** (reseat the Person Sensor connector first) or a
consistently-losing boot-probe timing. Also note: a clean Pi4 reboot does NOT capture the `[VER]` or
`Person Sensor` setup() lines (Teensy boots before the assistant opens the port → POST logs
`firmware version … WARN (no [VER])`) — so on reboots, `FACE:` transitions are the only detection signal.
NOTE: the Pi4 has no `FACE:` consumer — tracking is firmware-internal; `FACE:1/0` to the Pi4 is informational.

**Root-cause candidates:**
1. **One-shot boot probe with no retry** — `setup()` probes I2C 5× over ~400 ms once; a flash/glitch or a
   slow sensor power-up leaves `personSensorFound=false` latched for the whole boot. (Firmware: `src/main.cpp`
   `setup()` PersonSensor block + `hasPersonSensor()`.)
2. **I2C wedge** clearable only by a sensor power cycle (USB 5V drop), not an MCU reset.
3. **Connector/hardware** intermittency (check physically if power cycle doesn't fix).
4. **Downstream tracking quality** — even with the sensor live, the "brief lock then interrupt" matches a
   prior EyeController bug (see memory `project_tracking_eyecontroller_fix`, fix ed8fa41 in
   `setTargetPosition`/`eyeOldX` seeding) + autoMove re-engagement timing (`FACE_LOST_TIMEOUT_MS=5000`).

**Fix targets:**
- **Firmware probe hardening:** retry/re-probe — e.g. if `!personSensorFound`, periodically re-attempt
  `personSensor.isPresent()` in `loop()` (rate-limited) so a flash/glitch never leaves tracking dead until
  a manual power cycle. REPO-ONLY → flash.
- **Tracking quality:** only assess once the sensor is confirmed `detected` + `FACE:` events flow. Per the
  standing rule, **add serial debug output BEFORE any tracking reflash** (memory
  `feedback_dont_push_unverified_tracking`); observe-iterate with the user in frame.

**Deployment gate:** firmware (flash) REPO-ONLY at close; user flashes. Bump `FIRMWARE_VERSION` (live=S130).

---

## RD-030 — Anthropomorphic Mouth Enhancements (S130)

**Status:** #2 + #3 **IMPLEMENTED REPO-ONLY (S130)** — firmware builds clean, pending user PlatformIO
flash (`FIRMWARE_VERSION=S130`). #1 (amplitude-reactive lip-sync) **still proposed/deferred** — it
spans Pi4 (`audio_io.py` envelope in the hot playback loop) + firmware (new `MOUTH_OPEN` command +
parametric draw) and risks the S101 eye-jitter tuning, so it deserves its own session with bench
measurement of the SWSPI redraw budget. See CHANGELOG S130 firmware addendum for the #2/#3 build.

Three options to make the TFT mouth project more lifelike. All are additive to the existing
`src/mouth_tft.cpp` idle engine + emotion palette; none require new hardware.

1. **Amplitude-reactive TTS mouth (lip-sync feel).** Today the mouth cycles through a fixed `frames[]`
   list at a fixed rate during TTS (`pi4/hardware/audio_io.py` `play_pcm_stream`/`play_pcm_speaking`).
   Instead, derive a per-chunk RMS/envelope from the PCM being played and send a mouth-openness level
   (e.g. a new `MOUTH_OPEN:<0-15>` firmware command, or reuse `MOUTH:` indices mapped to open amounts)
   so the mouth opens wider on loud syllables and closes on pauses. Approximates lip-sync without
   phoneme analysis. Firmware: a parametric open-mouth draw. Risk: SWSPI redraw cost at 2Hz cap —
   keep the openness quantized to a few levels to stay within the eye-loop budget.

2. **Emotion-tinted idle breathing.** The firmware idle BREATHE/DRIFT animations only modulate the
   backlight around the neutral cyan mouth. Carry the last emotion's color (the existing RGB565
   palette in `mouth_tft.cpp`) into the idle resting expression and breathe *that* hue, so after a
   happy exchange IRIS idles warmly (yellow) and after a sad one cooler (blue), decaying back to
   neutral cyan over a few minutes. Pi4 sends the last sentiment; firmware tints the idle draw.
   Cheap, high personality payoff. Pairs naturally with the now-visible idle level (S130).

3. **"Noticed you" greet on face-acquire.** The Teensy already has the Person Sensor and emits
   `FACE:1`/`FACE:0` (`src/main.cpp` `reportFaceState`). On a fresh `FACE:1` after idle, trigger a
   brief one-shot mouth greet (e.g. a quick SURPRISED→SMILE "boop", reusing the existing BOING/
   SIDESMIRK idle primitives) and a small backlight bump, so IRIS visibly reacts to a person
   entering frame even before any wakeword. Optional Pi4-side pairing with a soft RPQR quip. Risk:
   debounce against the existing `FACE_COOLDOWN_MS` so it doesn't re-greet on flicker.

**Deployment gate:** All three touch firmware (`src/mouth_tft.cpp`, `src/main.cpp`) → REPO-ONLY at
session close; user performs the PlatformIO upload. Options 1–2 also touch `pi4/` (audio_io.py /
emotion plumbing) → Pi4 deploy with explicit authorization.

---

## RD-001 — Stop/Cancel Pre-STT Intercept

**Status:** Deferred — Option 1 (post-STT STOP phrase gate) deployed to Pi4 (commit 54d576c, 2026-05-02). Pre-STT RMS intercept (Option 2) is not currently active scope.

**Problem:** Whisper hallucinates on very short post-wakeword audio (< ~0.5s). Single-word utterances like "stop" are transcribed as unrelated phrases. The intent router then classifies the hallucinated text rather than the intended command, causing IRIS to respond incorrectly instead of aborting.

**Goal:** For post-wakeword audio bursts below an RMS or duration threshold, route directly to a local keyword match ("stop", "quiet", "cancel") without invoking Whisper. If matched, execute the command. If not matched, fall through to Whisper normally.

**Impact:** IRIS will reliably respond to short abort commands mid-interaction, improving trust and responsiveness during real household use.

**Risk:** Threshold tuning — too aggressive a gate will skip legitimate short utterances. Threshold must be validated on real household audio before deployment.

**Deployment gate:** Pi4 — requires explicit user authorization. No GandalfAI changes needed.

**Rollback:** Revert the changed Pi4 files to prior commit and redeploy to Pi4.

**Files:** `pi4/assistant.py`, possibly `pi4/services/stt.py`; `pi4/core/intent_router.py` only if command routing is changed.

---

## RD-004 — Teensy Hardware/Firmware Pass (Batch 2)

**Status:** Open — blocked until Pi4 runtime is stable

**Problem:** Teensy 4.1 firmware has known candidate hardening items that have not been addressed: sleep render pointer guards, serial overflow discard-and-log, and potential mouth command gating during sleep.

**Goal:** Implement Batch 2 hardening scope after confirming Pi4 runtime stability. Each Teensy change must be a separate firmware commit and a separate PlatformIO build.

**Impact:** More robust embedded behavior — prevents display corruption during unexpected state transitions and overflow conditions. Improves IRIS's reliability as a persistent display device.

**Risk:** Firmware changes are harder to roll back than Python changes. Each Teensy change must be independently validated before proceeding to the next.

**Deployment gate:** Firmware only — user uploads via PlatformIO. No Pi4 or GandalfAI deployment needed for firmware-only changes.

**Rollback:** Re-flash prior firmware build via PlatformIO.

**Files:** `src/main.cpp`, possibly new Teensy utility files. Do not touch `src/eyes/EyeController.h` without explicit instruction.

---

## RD-005 — GandalfAI Inference Settings Review

**Status:** Open — low priority, post-Batch D

**Problem:** Inference settings (temperature, num_ctx, etc.) were set during the mistral-small3.2:24b migration (S119) and have not been fully validated for IRIS's conversational persona and latency targets at scale.

**Goal:** Audit `ollama/iris_modelfile.txt` PARAMETER block. Validate temperature (currently 0.75), num_ctx (currently 6144), top_p, repeat_penalty, and any other relevant parameters. Adjust and rebuild iris model if warranted.

**Impact:** May improve response quality, character consistency, or latency. Risk of regression if changes are not validated against real household use.

**Risk:** Parameter changes require iris model rebuild on GandalfAI. A poorly chosen temperature or context window can degrade persona quality or increase latency.

**Deployment gate:** GandalfAI — requires explicit `DEPLOY`. Current VRAM: Kokoro ~2GB + mistral-small3.2:24b ~15GB = ~17GB of 24GB (headroom ~7GB at num_ctx 6144).

**Rollback:** Revert `ollama/iris_modelfile.txt` to prior commit. Rebuild iris model on GandalfAI.

**Files:** `ollama/iris_modelfile.txt`

---

## RD-006 — Custom Wakeword Experiment (Future)

**Status:** Deferred — no active timeline

**Problem:** The production wakeword (`hey_jarvis`) is functional but not IRIS-specific. A custom wakeword trained on real household voice samples would improve ownership and recognition accuracy.

**Goal:** When ready, run a new experiment using real household voice samples, single-model training, and live Pi4 validation before any production deployment. Prior experiments (details in `CHANGELOG.md`) did not meet production reliability requirements.

**Impact:** A reliable custom wakeword would complete IRIS's identity as a self-contained robot assistant with a distinct name.

**Risk:** Real-world reliability is difficult to achieve. Prior experiments failed. Do not deploy any experimental wakeword to production without explicit user approval, live Pi4 state confirmation, clean process restart, and one-model-at-a-time testing.

**Deployment gate:** Pi4 — requires explicit user authorization. One wakeword model tested at a time.

**Rollback:** Restore `hey_jarvis` configuration on Pi4 and restart wakeword service.

**Files:** Pi4 wakeword configuration scripts. `iris_config.json` is protected — do not touch without explicit instruction.

---

## RD-007 — Bench Trend Viewer in iris_web

**Status:** Deferred — waiting for enough `iris_bench.jsonl` data to accumulate before building trend UI.

**Problem:** `iris_bench.jsonl` (added S50) stores per-turn timing data but is only readable via SSH. The existing Bench tab in the web UI shows current-session timings from journald only. No trend view exists.

**Goal:** Add a new panel or sub-tab in the Bench page that reads `iris_bench.jsonl`, parses all records, and displays a trend chart (e.g., `total_ms` over time, with `gandalf_was_cold` flagged). Allow filtering by route, date range. Minimum viable: table view of last 25 records with stage columns.

**Impact:** User can identify latency trends and outliers without SSH. Can compare slow-turn data across days/weeks.

**Risk:** iris_web.py runs as root on Pi4 overlayfs. Reading a log file is low-risk. Chart rendering likely needs a JS library (Chart.js) loaded from CDN or bundled.

**Blocked on:** S50 deploy so `iris_bench.jsonl` has data to read. At least ~1 week of normal use (~25-35 turns) recommended before building the viewer.

**Deployment gate:** Pi4 — iris_web.py + iris_web.html. Standard `/media/root-ro` persist pattern.

**Files:** `pi4/iris_web.py` (`/api/bench_jsonl` endpoint), `pi4/iris_web.html` (Bench tab panel).

---


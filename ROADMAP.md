<!-- Forward-looking work only. Do not add completed items. Completed history is in CHANGELOG.md. -->

# IRIS Roadmap

All items below are active or queued. Completed work is in `CHANGELOG.md`.

---

## RD-030 — Anthropomorphic Mouth Enhancements (proposed S130)

**Status:** Proposed — design only, not implemented. Logged during the S130 awake/idle mouth brightness fix.

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


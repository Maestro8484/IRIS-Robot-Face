<!-- Forward-looking work only. Do not add completed items. Completed history is in CHANGELOG.md. -->

# IRIS Roadmap

All items below are active or queued. Completed work is in `CHANGELOG.md`.

---

## RD-001 — Stop/Cancel Pre-STT Intercept

**Status:** Open — Batch D priority 1

**Problem:** Whisper hallucinates on very short post-wakeword audio (< ~0.5s). Single-word utterances like "stop" are transcribed as unrelated phrases. The intent router then classifies the hallucinated text rather than the intended command, causing IRIS to respond incorrectly instead of aborting.

**Goal:** For post-wakeword audio bursts below an RMS or duration threshold, route directly to a local keyword match ("stop", "quiet", "cancel") without invoking Whisper. If matched, execute the command. If not matched, fall through to Whisper normally.

**Impact:** IRIS will reliably respond to short abort commands mid-interaction, improving trust and responsiveness during real household use.

**Risk:** Threshold tuning — too aggressive a gate will skip legitimate short utterances. Threshold must be validated on real household audio before deployment.

**Deployment gate:** Pi4 — requires explicit user authorization. No GandalfAI changes needed.

**Rollback:** Revert the changed Pi4 files to prior commit and redeploy to Pi4.

**Files:** `pi4/assistant.py`, possibly `pi4/services/stt.py`; `pi4/core/intent_router.py` only if command routing is changed.

---

## RD-002 — AMUSED Emotion: Full Implementation

**Status:** Complete in local repo (S47, 2026-05-03) — pending Pi4 deploy + firmware upload

**Decision:** Full implementation chosen over removal. AMUSED = dry amusement at teasing, insults, or identity challenges — distinct from CONFUSED (genuinely baffling input).

**Implemented (S47):**
- `pi4/core/config.py` — AMUSED added to VALID_EMOTIONS; MOUTH_MAP → index 2 (smirk/CURIOUS expression)
- `pi4/hardware/led.py` — AMUSED: sinusoidal breathe, amber [255,160,0], floor=10, peak=80, period=1.5s, gamma=1.8, duration=3s (special case in show_emotion)
- `src/main.cpp` — AMUSED added to EmotionID enum (=8), emotionTable ({0.55f, false, 3000}), parseEmotion
- `pi4/iris_web.html` — AMUSED button added to Emotion Test grid
- `ollama/iris_modelfile.txt` — AMUSED already present and correctly described; no change needed
- `ollama/iris-kids_modelfile.txt` — AMUSED added to valid emotion list

**Remaining deploy steps (requires explicit authorization):**
- Pi4: copy config.py, led.py, iris_web.html → persist + restart assistant
- Firmware: PlatformIO upload (user action)
- GandalfAI: `ollama create iris-kids` rebuild required — iris-kids_modelfile.txt changed

---

## RD-003 — Duplicate Sleep Log Cleanup

**Status:** Open — Low priority

**Problem:** `/home/pi/iris_sleep.log` (Pi4 root home) may duplicate `/home/pi/logs/iris_sleep.log`. Duplicate logs waste space and create ambiguity when diagnosing sleep/wake issues.

**Goal:** Confirm which log is actively written by the current sleep/wake system. If duplicate, remove the stale path and update any log-reading references to point to the canonical location.

**Impact:** Cleaner diagnostics. Less ambiguity when tracing sleep-related bugs.

**Risk:** Low — log file only. No runtime behavior changes unless a log reader references the stale path.

**Deployment gate:** Pi4 — requires explicit user authorization. Use standard `/media/root-ro` persistence pattern documented in `CLAUDE.md`.

**Rollback:** Restore deleted log file, symlink, or path reference from prior commit or Pi4 backup if any log reader depends on the removed path.

**Files:** Pi4 runtime only — `/home/pi/iris_sleep.log`, `/home/pi/logs/iris_sleep.log`, relevant `pi4/` sleep/wake scripts if they reference the log path.

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

**Problem:** Current inference settings (temperature, num_ctx, etc.) have not been reviewed since gemma3:27b-it-qat was adopted. Defaults may not be optimal for IRIS's conversational persona and latency targets.

**Goal:** Audit `ollama/iris_modelfile.txt` PARAMETER block. Validate temperature (currently 0.82), num_ctx (currently ≤ 4096 per VRAM constraint), and any other relevant parameters. Adjust and rebuild iris model if warranted.

**Impact:** May improve response quality, character consistency, or latency. Risk of regression if changes are not validated against real household use.

**Risk:** Parameter changes require iris model rebuild on GandalfAI. A poorly chosen temperature or context window can degrade persona quality or increase latency.

**Deployment gate:** GandalfAI — requires explicit `DEPLOY`. Do not raise num_ctx above 4096 (VRAM constraint: Kokoro ~2GB + gemma3:27b-it-qat ~14.1GB = ~16.1GB of 24GB).

**Rollback:** Revert `ollama/iris_modelfile.txt` to prior commit. Rebuild iris model on GandalfAI.

**Files:** `ollama/iris_modelfile.txt`

---

## RD-006 — Custom Wakeword Experiment (Future)

**Status:** Open — deferred, no active timeline

**Problem:** The production wakeword (`hey_jarvis`) is functional but not IRIS-specific. A custom wakeword trained on real household voice samples would improve ownership and recognition accuracy.

**Goal:** When ready, run a new experiment using real household voice samples, single-model training, and live Pi4 validation before any production deployment. Prior experiments (details in `CHANGELOG.md`) did not meet production reliability requirements.

**Impact:** A reliable custom wakeword would complete IRIS's identity as a self-contained robot assistant with a distinct name.

**Risk:** Real-world reliability is difficult to achieve. Prior experiments failed. Do not deploy any experimental wakeword to production without explicit user approval, live Pi4 state confirmation, clean process restart, and one-model-at-a-time testing.

**Deployment gate:** Pi4 — requires explicit user authorization. One wakeword model tested at a time.

**Rollback:** Restore `hey_jarvis` configuration on Pi4 and restart wakeword service.

**Files:** Pi4 wakeword configuration scripts. `iris_config.json` is protected — do not touch without explicit instruction.

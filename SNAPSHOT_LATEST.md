# IRIS Snapshot

> **WARNING: DO NOT USE PROJECT-ATTACHED .md FILES.**
> Read live repo via filesystem MCP only. Claude.ai project knowledge base attachments are stale (last updated S49, May 2026 -- 48 sessions behind as of S97). Any session that reads them instead of this file gets wrong hardware state, wrong serial numbers, wrong firmware version, and wrong deploy status.

**Session:** S103c | **Date:** 2026-06-07 | **Branch:** `main` | **Last commit:** S103c

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## WHAT'S NEXT (Priority Queue)

1. **T40 mechanical damper** — servo tracking confirmed working, user tuning physically. No firmware change needed.
2. **Deploy iris_web.js** — EYE:6 Striking Blue fix (3 locations). REPO-ONLY. iris_web.html DEPLOYED S102.
4. **qwen2.5vl rollback when registry updated** — Ollama 0.30.6 broke CLIP loader. Pivot to qwen2.5:32b (text-only) is live S103. When upstream registry pushes a compatible mmproj blob, run model rebuild. See CHANGELOG S103 rollback steps.
5. **RD-003** — Duplicate sleep log: `/home/pi/iris_sleep.log` vs `/home/pi/logs/iris_sleep.log`.
6. **Wake-from-sleep UX** — wakeword during sleep now plays time-of-day quip (S103b). UX question: should it fall through to listening after quip? Currently returns to idle; user must say "hey jarvis" again to converse.

---

## Machine Status

| System | Status |
|---|---|
| Pi4 192.168.1.200 | Operational. assistant.service active. ttyIRIS_EYES → ttyACM0 (serial 13625440, T41). udev corrected + SD persisted S97. |
| GandalfAI 192.168.1.3 | Operational. iris/iris-kids on **qwen2.5:32b** (S103 restore — text-only, no vision). Ollama 0.30.5 (firewall blocks auto-update to 0.30.6). Kokoro TTS port 8004. |
| Teensy 4.1 (eyes+mouth) | **FLASHED S101.** [VER] confirmed `firmware=S101 built=Jun 7 2026`. Bridge live, no DROPs. Mouth update rate 2Hz during TTS (eye jitter fix). |
| Teensy 4.0 (servo+gesture) | **FLASHED S97** (FACE_RETURN_MS 30000ms). Tracking confirmed working. Mechanical damper tuning ongoing. |
| TTS | Kokoro primary (Docker 8004), Piper fallback (Wyoming 10200). |

---

## Active Issues

- **LOW: iris_web.js deploy pending** — EYE:6 fix (3 locations). REPO-ONLY. iris_web.html DEPLOYED S102.
- **LOW: qwen2.5vl vision restore pending** — GGUF blob missing `clip.vision.n_wa_pattern` AND `fullatt_block_indexes=[]` (empty). Patch requires 20GB file rewrite; deferred. Watch for Ollama registry update or proven GGUF patch tooling. See S103 CHANGELOG for details.
- **LOW: RD-003** — Duplicate sleep log paths.
- **LOW: Wake-from-sleep UX** — wakeword during sleep plays greeting + returns to idle; needs "hey jarvis" twice to converse. Evaluate fall-through behavior.

---

## udev Serial Numbers — Confirmed S97

| Symlink | Serial | Device |
|---|---|---|
| `/dev/ttyIRIS_EYES` | `13625440` | Teensy 4.1 (eyes + TFT mouth) |
| `/dev/ttyIRIS_SERVO` | `12763490` | Teensy 4.0 (servo + gesture) |

S94b had these swapped. Corrected S97 by connecting T41 alone and observing which serial appeared. IRIS_ARCH.md, pi4/scripts/99-iris-teensy.rules, and live Pi4 udev rules all updated.

---

## Do Not Touch

- `iris_config.json` — gesture map + emotion map live config
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

---

## Last Session Changes (S103c — 2026-06-07)

- **`src/config.h`** — `FIRMWARE_VERSION` bumped `S100c` → `S101`. T41 reflashed. FLASHED+VERIFIED. `[VER] IRIS-EYES firmware=S101 built=Jun 7 2026` confirmed in journal.
- **S101 eye jitter fix** — mouth update rate 8Hz→2Hz during TTS now active on live hardware.

## Previous Session Changes (S103b — 2026-06-07)

- **`pi4/assistant.py`** — Wake quips system added: `_WAKE_QUIPS` (12 lines / 6 time windows), `_pre_synthesize_quips()` at startup, `_play_wake_quip()` at sleep-wake (always) and normal wakeword (rate-limited: >60min idle AND >2 wakewords since last quip). DEPLOYED+VERIFIED+PERSISTED. md5=`7aefc6a237e8ad131504586dcf8ff4a7`. All 11 unique quip lines confirmed cached in journal.

## Previous Session Changes (S103 — 2026-06-07)

- **`ollama/iris_modelfile.txt`** — FROM qwen2.5:32b (was gemma3:27b-it-qat), stop `<|im_end|>`. DEPLOYED+VERIFIED on GandalfAI.
- **`ollama/iris-kids_modelfile.txt`** — Same FROM + stop change. DEPLOYED+VERIFIED on GandalfAI.
- **GandalfAI Ollama** — Downgraded to 0.30.5. Windows Firewall rule blocks `ollama app.exe` outbound (no auto-update to 0.30.6).
- **Pi4 assistant.service** — Restarted. POST L1 Ollama models iris+iris-kids PASS.

## Previous Session Changes (S102 — 2026-06-06)

- **`ollama/iris_modelfile.txt`** — FROM gemma3:27b-it-qat (was qwen2.5vl:32b-q4_K_M), stop `<end_of_turn>`. DEPLOYED+VERIFIED on GandalfAI.
- **`ollama/iris-kids_modelfile.txt`** — Same FROM + stop change. DEPLOYED+VERIFIED on GandalfAI.
- **`pi4/services/tts.py`** — Removed `_PIPER_DIRECT_PHRASES` direct Piper routing. Kokoro-first for all text. DEPLOYED+PERSISTED. md5=`8130b382bc38699ed14cd907be641e6d`.
- **`pi4/iris_web.html`** — Vision card: "Pi Camera + Gemma" → "Pi Camera + Vision Model". DEPLOYED+PERSISTED. md5=`1fe42d456dbaec5cd3ea34b1372630fe`.
- **`iris_config.json` (live Pi4)** — Removed stale keys: EMOTION_MOUTH_MAP, EMOTION_EYE_MAP, GESTURE_PROXIMITY_THRESHOLD. md5=`19f0ed24d983d097a3c17b099b6399c3`.

**T41 status:** FLASHED S97. **T40 status:** FLASHED S97.

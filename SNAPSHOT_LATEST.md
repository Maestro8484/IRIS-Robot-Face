# IRIS Snapshot

> **WARNING: DO NOT USE PROJECT-ATTACHED .md FILES.**
> Read live repo via filesystem MCP only. Claude.ai project knowledge base attachments are stale (last updated S49, May 2026 -- 48 sessions behind as of S97). Any session that reads them instead of this file gets wrong hardware state, wrong serial numbers, wrong firmware version, and wrong deploy status.

**Session:** S108 | **Date:** 2026-06-08 | **Branch:** `main` | **Last commit:** S108

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## WHAT'S NEXT (Priority Queue)

1. **T40 mechanical damper** — servo tracking confirmed working, user tuning physically. No firmware change needed.
2. **qwen2.5vl rollback when registry updated** — Ollama 0.30.6 broke CLIP loader. Pivot to qwen2.5:32b (text-only) is live S103. When upstream registry pushes a compatible mmproj blob, run model rebuild. See CHANGELOG S103 rollback steps.
3. **Wake-from-sleep UX** — wakeword during sleep plays quip then re-enters sleep (S104 fix). UX question: should it fall through to listening after quip instead? Currently: wake → quip → sleep again; user must say "hey jarvis" twice to converse. Evaluate fall-through behavior.

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

- **LOW: qwen2.5vl vision restore pending** — GGUF blob missing `clip.vision.n_wa_pattern` AND `fullatt_block_indexes=[]` (empty). Patch requires 20GB file rewrite; deferred. Watch for Ollama registry update or proven GGUF patch tooling. See S103 CHANGELOG for details.
- **LOW: Wake-from-sleep UX** — wakeword during sleep: IRIS wakes, plays quip, re-enters sleep (S104). Evaluate whether it should fall through to active listening instead of re-sleeping.

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

## Last Session Changes (S108 — 2026-06-08)

- **`pi4/core/config.py`** — `TTS_MAX_CHARS=2500` (was 900). DEPLOYED+VERIFIED. md5 RAM=SD=`9d75f68d02d2a6f1cb2754d7df342b05`.
- **`pi4/services/llm.py`** — `clean_llm_reply()`: added opener/trailer/separator/list-artifact cleanup patterns. DEPLOYED+VERIFIED. md5 RAM=SD=`01b72e4c981c545bfe0cac016f8936a5`.
- **`pi4/services/vision.py`** — `ask_vision()`: HTTP 400 now returns "vision not available" message instead of raising. DEPLOYED+VERIFIED. md5 RAM=SD=`60a66d3a94310f90757d46ca1cbe5dc7`.

## Previous Session Changes (S107 — 2026-06-08)

- **`pi4/core/config.py`** — `LED_SLEEP_PEAK=8` (was 26), `LED_SLEEP_FLOOR=1` (was 3), `LED_SLEEP_BRIGHT=0xE3` (was 0xFF; 3/31 global brightness). Added `LED_SLEEP_BRIGHT` to `_OVERRIDABLE`/`_TYPE_COERCE`. DEPLOYED+VERIFIED. md5 RAM=SD=`f6f55fb58bc42532e673b334b8a04c05`.
- **`pi4/hardware/led.py`** — `show_sleep()` rewritten to read `iris_config.json` each animation cycle via `_load()`. WebUI peak/floor/period changes now take effect without service restart. DEPLOYED+VERIFIED. md5 RAM=SD=`b4a78a069bbd331ae4f73c829e86e256`.
- **`pi4/iris_web.html`** — Sleep LEDs card hint updated (no restart required, new defaults). DEPLOYED+VERIFIED. md5 RAM=SD=`b3ef97e941de491571f099df5557d140`.

## Previous Session Changes (S106 — 2026-06-07)

- **`tools/workbench/index.html`** — Latency Bench tab: added `lat-analysis-spinner`, `lat-analysis-panel`, and `lat-result-actions` action bar (Generate Handoff + Run AI Analysis). REPO-ONLY.
- **`tools/workbench/workbench.js`** — Added 5 new functions: `callAnthropicLatencyAnalysis`, `renderLatencyAnalysisPanel`, `saveLatencyBenchCases`, `runLatencyAnalysis`, `generateLatencyHandoff`. AI prompt asks for per-case tier, bottlenecks, prioritized optimizations, and new stress-test bench cases. REPO-ONLY.
- **`tools/workbench/workbench.css`** — Added `#lat-result-actions`, `#lat-analysis-spinner`, `.lat-opt-card` + header/meta/tradeoff classes. REPO-ONLY.
- **`.claude/launch.json`** — Added `autoPort: true` so preview server picks free port when 8080 is occupied. REPO-ONLY.

## Previous Session Changes (S105 — 2026-06-07)

- **`pi4/iris_web.py`** — `/api/bench` JSONL fallback added: if journalctl returns 0 cycles, reads `iris_bench.jsonl` and returns historical records to the frontend. Fixes empty Bench tab after reboots. DEPLOYED+VERIFIED. md5 RAM=SD=`856def24589ecae2e405f610db42958a`.
- **`pi4/assistant.py`** — `_bench_write()` now captures `emotion`, `tier`, `num_predict`, and `engine` in JSONL record. DEPLOYED+VERIFIED. md5 RAM=SD=`5db3b7f77ab3892ea8ec42967f168d80`.
- **`pi4/iris_bench.jsonl` (SD)** — Persisted 4 existing records to SD. Was 0 bytes since 2026-05-30.
- **`pi4/iris_bench_report.py`** — CLI comment wrong service name fixed (`iris-assistant.service` → `assistant`). REPO-ONLY.
- **`docs/bench_audit_S105.md`** — NEW. Full three-tier bench audit, gaps G1–G7, JSONL live state, architecture recommendations. REPO-ONLY.

## Previous Session Changes (S104 — 2026-06-07)

- **`pi4/assistant.py`** — Sleep-resume fix: added `if in_sleep_window(): _do_sleep(teensy, leds)` after `_play_wake_quip()` in the wakeword-during-sleep branch. DEPLOYED+VERIFIED. md5 RAM=SD=`0220719693fe3d6a6f52b0acfd46a4fa`.
- **`pi4/core/config.py`** — Mouth brightness fix: `MOUTH_INTENSITY_SLEEP = 1` → `5` (BL_MAP[1]=0.8% → BL_MAP[5]=6%). DEPLOYED+VERIFIED. md5 RAM=SD=`bfd247cc880cf2a7ad3fda790357a170`.

## Previous Session Changes (S103c — 2026-06-07)

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

# IRIS Snapshot

> **WARNING: DO NOT USE PROJECT-ATTACHED .md FILES.**
> Read live repo via filesystem MCP only. Claude.ai project knowledge base attachments are stale (last updated S49, May 2026 -- 48 sessions behind as of S97). Any session that reads them instead of this file gets wrong hardware state, wrong serial numbers, wrong firmware version, and wrong deploy status.

**Session:** S119 | **Date:** 2026-06-09 | **Branch:** `main` | **Last commit:** S119

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## WHAT'S NEXT (Priority Queue)

1. **T40 mechanical damper** — servo tracking confirmed working, user tuning physically. No firmware change needed.
2. **Pure Pi4-local STT commands** — deferred from S110. Evaluate simple wakeword-only commands ("hey jarvis… go to sleep") handled by Pi4 Whisper without LLM, for cases where GandalfAI is asleep. Design session needed.
3. **Wake-from-sleep fall-through** — still deferred. Current: wakeword during sleep → quip → re-sleep. Evaluate whether it should fall through to active listening after the quip.

---

## Machine Status

| System | Status |
|---|---|
| Pi4 192.168.1.200 | Operational. assistant.service active. ttyIRIS_EYES → ttyACM0 (serial 13625440, T41). udev corrected + SD persisted S97. |
| GandalfAI 192.168.1.3 | **OPERATIONAL.** iris/iris-kids on **mistral-small3.2:24b** (S119, was qwen3.5:27b). Ollama **0.30.7**. arch=`mistral3`, 24.0B, caps include `vision` (Pixtral baked in, no mmproj). 15GB Q4, **100% GPU** confirmed (no CPU offload). Text 35.8 tok/s; vision warm 1.4s/0.3s first-token, vision cold-after-text ~12s (4096↔6144 ctx reload, vs 29s on qwen3.5). PT-001 15/20, persona-locked, no token bleed. Env (Machine scope): FLASH_ATTENTION=1, CONTEXT_LENGTH=4096, NUM_PARALLEL=1, KV_CACHE=q8_0. Kokoro TTS 8004 OK. |
| Teensy 4.1 (eyes+mouth) | **FLASHED S101.** [VER] confirmed `firmware=S101 built=Jun 7 2026`. Bridge live, no DROPs. Mouth update rate 2Hz during TTS (eye jitter fix). |
| Teensy 4.0 (servo+gesture) | **FLASHED S97** (FACE_RETURN_MS 30000ms). Tracking confirmed working. Mechanical damper tuning ongoing. |
| TTS | Kokoro primary (Docker 8004), Piper fallback (Wyoming 10200). **Streaming dispatch live (S116):** main LLM replies synthesized per sentence and played overlapped. |

---

## Active Issues

- **LOW: Wake-from-sleep fall-through** — wakeword during sleep: IRIS wakes, plays quip, re-enters sleep (S104). Evaluate whether it should fall through to active listening instead of re-sleeping.
- **LOW: Ollama version pin** — Currently 0.30.7 (runs mistral-small3.2:24b fine). Firewall outbound block on ollama app.exe in place; user unchecked auto-update in Ollama UI (S110). The qwen3.5 pin rationale is moot post-S119, but keep the firewall/pin to avoid surprise upgrades.
- **REC (S119): unify iris num_ctx to 6144.** Vision forces `num_ctx=6144` per request while text uses the modelfile `num_ctx=4096`, so Ollama ping-pong-reloads the model on every text↔vision switch (~12s cold vision; also leaves only ~395 tok for generation against the ~3700-tok system prompt — the MAX 400-tok tier overflows). Mistral is 15GB so 6144 ctx is VRAM-safe (15+2 Kokoro = 17/24 GB; `ollama ps` shows 15GB at 6144). Deferred at modelfile level because sysmap documents a `num_ctx ≤ 4096` hard limit (gemma3/qwen-era, now obsolete) — needs user sign-off to raise.

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

## Last Session Changes (S119 — 2026-06-09)

- **LLM migrated qwen3.5:27b → mistral-small3.2:24b** (iris + iris-kids). Both rebuilt on GandalfAI. arch=`mistral3`, dense, Pixtral vision baked in. DEPLOYED+VERIFIED.
- **`ollama/iris_modelfile.txt`** — FROM mistral-small3.2:24b. PARAMETER block replaced: num_gpu 99, num_ctx 4096, temperature 0.75, top_p 0.9, repeat_penalty 1.1, stop `[INST]`/`[/INST]`/`</s>`/`User:`. SYSTEM + all few-shot/calibration/VISION blocks preserved verbatim. The `User:` stop was added (beyond brief spec) to kill few-shot turn-bleed Mistral exhibits without Qwen's `<|im_end|>` boundary. DEPLOYED.
- **`ollama/iris-kids_modelfile.txt`** — same FROM + PARAMETER block + stop set. Kids persona preserved. DEPLOYED.
- **`pi4/services/llm.py`** — removed `"think": False` from `stream_ollama()` payload (Mistral has no thinking mode; was dead weight from S114 qwen3.5). md5 RAM=SD=`911261166ce7aeed07a8e3ef1a2d044e`. DEPLOYED+VERIFIED. assistant.service restarted, POST L1 iris+iris-kids PASS, live path emits correct emotion tags with zero `[INST]/</s>/User:` bleed.
- **Gates:** PT-001 15/20 (persona-locked, no RLHF tells; cleaner than gemma3; `goodnight→NEUTRAL` and `motor/servo` now pass; remaining misses are borderline/fixture-debatable). Latency: text 35.8 tok/s, vision 100% GPU, warm 1.4s, cold 12s (vs 29s qwen3.5).
- **Housekeeping:** stray root files (`$null`, `Update-IRISProjectFiles.*`) swept to `_housekeeping/S119_root_sweep/` with MANIFEST; `LICENSE` restored (was an unstaged deletion).
- **NOT done (REPO-ONLY/follow-up):** num_ctx unification to 6144 (see Active Issues REC); `think:False` still present in 4 other Pi4 callers (assistant.py, vision.py, iris_web.py, iris_post.py) — harmless dead weight on Mistral, sweep next session. Live voice (wakeword→TTS) and camera-vision human checks pending.

## Last Session Changes (S118 — 2026-06-09)

- **Vision 400 fixed.** Web UI "describe what you see" returned `400 Bad Request` from `/api/generate`. Root cause: a real camera frame = ~4570 vision tokens > the model's default 4096 `num_ctx` (`"exceeds the available context size"`). NOT a vision-support issue — iris has the `vision` capability. Broke both web UI and voice paths since the S113/S114 qwen2.5vl→qwen3.5 swap.
- **`pi4/services/vision.py`** — `ask_vision()` adds `"options": {"num_ctx": 6144}`. md5=`1e5500958db39e888db4bb4294150b9d` RAM=SD. DEPLOYED.
- **`pi4/iris_web.py`** — `api_vision()` adds `"think": False` (was missing → empty reply on thinking model) + `"options": {"num_ctx": cfg.get("VISION_NUM_CTX", 6144)}`. md5=`9f7af3a6d023edd794cb067abdff3871` RAM=SD. DEPLOYED.
- **VERIFIED:** `POST /api/vision` → HTTP 200 in ~29 s with a correct scene description. (~29 s is inflated by an Ollama model reload — vision's 6144 ctx differs from the 4096 text default; see Proactive Flags.)

## Previous Session Changes (S117 — 2026-06-09)

- **`pi4/core/config.py`** — Response-length tiers retuned for a voice robot (were narrator-length). `num_predict` SHORT 120→40 (~9s), MEDIUM 350→90 (~21s), LONG 700→180 (~41s), MAX 1200→400 (~92s≈1.5min), default 300→100. `TTS_MAX_CHARS` 2500→1500 (~100s hard backstop, all tiers). Basis: measured ~0.23s speech/token (S116). Inline rationale+rollback in file. md5=`5391ed8c079dee4527c72ec8e148237f` RAM=SD. DEPLOYED+VERIFIED.
- **`pi4/services/llm.py`** — `_MAX_PATTERNS` now triggers MAX (story tier) ONLY on explicit "tell me a story"/essay/long-form requests; removed the `word_count>15` LONG→MAX promotion so wordy "explain…" stays LONG. md5=`b94427979460d21805765f817b8cf522` RAM=SD. DEPLOYED+VERIFIED (live: story→400, explain→180, history→180, essay→400, hello→40).

## Previous Session Changes (S116 — 2026-06-09)

- **`pi4/hardware/audio_io.py`** — New `play_pcm_stream()`: gapless back-to-back playback of a queue of per-sentence PCM blobs with one EYES:SPEAKING/mouth-anim/interrupt-listener spanning the whole utterance. `play_pcm`/`play_pcm_speaking` untouched. md5=`ada50cfc3ab6b8ae52efdc7c7f9aab9c` RAM=SD. DEPLOYED.
- **`pi4/assistant.py`** — Main LLM block rewired: `stream_ollama()` → per-sentence `synthesize()` → background `play_pcm_stream` player. First audio now starts on the first sentence (was: full response synthesized in one blocking call). STOP checked per sentence dispatch. Emotion-on-first-chunk, Piper fallback, length classifier, follow-up loop all preserved. md5=`fe79c67bd5dfea50f5559e0304d37c35` RAM=SD. DEPLOYED.
- **Latency (LLM-start→first-audio, n=10 long prompts):** NEW p50=2086ms / p90=4257ms vs OLD (blocking) p50≈23.3s on these long replies. Resolves S98 streaming flag. Behavioral hardware checks (speaker/emotion-face/spoken-STOP/Piper) need a human — handed off.

## Previous Session Changes (S115 — 2026-06-09)

- **`pi4/core/intent_router.py`** — `_TIME_RE` pattern: added `what time is it` explicit literal + `time please` variant. "what time is it" now routes to UTILITY (was falling through to LLM at ~1434ms). md5=ea9e0d82425f76d98053c2b71221ef99 RAM=SD. DEPLOYED+VERIFIED.
- **`ollama/iris_modelfile.txt`** — Adversarial few-shot "You're dumb." example: `[EMOTION:ANGRY]` → `[EMOTION:AMUSED]`. Old ANGRY example was overriding S112 EMOTION CALIBRATION block. iris rebuilt on GandalfAI. DEPLOYED+VERIFIED.
- **VAD** — `SILENCE_SECS=1.2` confirmed in iris_config.json. No change needed.

## Previous Session Changes (S114 — 2026-06-09)

- **GandalfAI Ollama** — Already at 0.30.7 (no upgrade needed). GPU dispatch confirmed for qwen3.5:27b: 35.2 tok/s VERIFIED.
- **`ollama/iris_modelfile.txt`** — Removed `PARAMETER think false` (unsupported in Ollama 0.30.7; causes `ollama create` error). `"think": false` moved to API call level. iris rebuilt on GandalfAI. DEPLOYED+VERIFIED.
- **`ollama/iris-kids_modelfile.txt`** — Same removal. iris-kids rebuilt. DEPLOYED+VERIFIED.
- **`pi4/assistant.py`** — `"think": False` added to `ask_ollama()` and warmup call. DEPLOYED+VERIFIED. md5=1c42e3dd707281eaacc2cb2380394743 RAM=SD.
- **`pi4/services/llm.py`** — `"think": False` added to `stream_ollama()` payload. DEPLOYED+VERIFIED. md5=e93c69c2430415826baeaf05e247c853 RAM=SD.
- **`pi4/core/config.py`** — `VISION_MODEL` changed from `"qwen2.5vl:32b-q4_K_M"` → `"iris"` (qwen3.5:27b handles vision natively). DEPLOYED+VERIFIED. md5=f7a143d855a06c9b3fb8292e58ef363c RAM=SD.
- **`pi4/iris_post.py`** — `"think": False` added to l3_llm POST test. DEPLOYED+VERIFIED. md5=2bf0723a7f06d8f72896f3178af0e8ec RAM=SD.
- **`pi4/services/vision.py`** — `"think": False` added to ask_vision() /api/generate call. DEPLOYED+VERIFIED. md5=a60ffceaa8364678d2dffd04cbb951fc RAM=SD.
- **`tools/workbench/workbench.js`** — `"think": false` added to both /api/generate calls in harness + latency tester. REPO-ONLY.
- **Pi4 POST** — 20/23 PASS, WARN: 3, FAIL: 0 (was 19/23, FAIL: 1 on LLM smoke). All FAIL resolved.
- **pt001 persona harness** — 16/20 PASS (80%). Target ≥13/20 MET.

## Previous Session Changes (S112 — 2026-06-09)

- **`ollama/iris_modelfile.txt`** — `FROM qwen2.5vl:32b-q4_K_M` (was qwen2.5:32b). AMUSED calibration block added. DEPLOYED+VERIFIED. Smoke test: "You're dumb." → `[EMOTION:AMUSED]`. Both models rebuilt on GandalfAI. `ollama list` 21GB fresh timestamps.
- **`ollama/iris-kids_modelfile.txt`** — `FROM qwen2.5vl:32b-q4_K_M` (was qwen2.5:32b). No other changes. DEPLOYED+VERIFIED. Smoke test: "tell me a joke" → `[EMOTION:HAPPY]` + kid-appropriate response.
- **`IRIS_ARCH.md`** — VRAM baseline updated (VL base ~21GB, ~23GB total). Vision live note added S112.
- **`HANDOFF_CURRENT.md`** — GandalfAI status updated. S111 Chat flags marked RESOLVED.

## Previous Session Changes (S110 — 2026-06-09)

- **`pi4/assistant.py`** — RPQR + pipeline latency overhaul. DEPLOYED+VERIFIED. md5=`fa5bf5b065951bdbf34ab27b3af0ea4e` RAM=SD.
  - **RPQR sleep-path fix**: removed `ensure_gandalf_up()` from sleep-wakeword branch — pre-cached quip now plays instantly without Ollama check.
  - **Quip on every wakeword**: beep replaced by time-of-day quip on all activations. `_WAKE_QUIPS` expanded to 4–5 lines/band (26 total cached).
  - **New RPQR triggers** (all pre-cached PCM, fire before Gandalf gate): double-tap (<30s), post-speech (<5s after reply), top-of-hour (±2 min, 13 hour variants cached), first-of-day ("Morning."/"Finally.").
  - **`t_last_spoke` tracking**: set after LLM main response and follow-up responses to drive post-speech trigger.
  - **Removed** stale `_quip_state` dict (replaced by `_rpqr_state`).
- **`pi4/iris_config.json`** — `SILENCE_SECS=1.2` (was 1.5, -0.3s per interaction). DEPLOYED+VERIFIED. md5=`9dbd091fff10409f1e6d544d9e26b603` RAM=SD.
- **`docs/prompt_pipeline_latency_audit.md`** — NEW. Canned Claude Code prompt for pipeline latency troubleshooting: bottleneck table, fix templates, deploy sequence, bench check commands. REPO-ONLY.

## Previous Session Changes (S109 — 2026-06-08)

- **`pi4/core/config.py`** — `VISION_MODEL = "qwen2.5vl:32b-q4_K_M"` (was `"iris"` — text-only model broke vision). DEPLOYED+VERIFIED. md5 RAM=SD=`2978ca89d5d9e6172a0153b1802f179c`.
- **GandalfAI Ollama** — Downgraded 0.30.6 → **0.24.0** (0.30.x CLIP loader requires `clip.vision.n_wa_pattern` key missing from qwen2.5vl GGUF; 0.24.0 old engine does not check this). Installer via `$env:OLLAMA_VERSION="0.24.0"; irm https://ollama.com/install.ps1 | iex`.
- **GandalfAI Firewall** — Rule re-applied blocking `ollama app.exe` outbound (prevents auto-update from restoring a broken version).
- **Vision verified** — HTTP 200 from `/api/generate` with qwen2.5vl:32b-q4_K_M on Ollama 0.24.0. Pi4 assistant POST L1 PASS.

## Previous Session Changes (S108 — 2026-06-08)

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

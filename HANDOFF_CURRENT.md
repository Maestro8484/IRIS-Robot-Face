<!-- Short session-start handoff only. Do not expand. Operational rules are in CLAUDE.md. -->

# IRIS Handoff — Current

> **WARNING: DO NOT USE PROJECT-ATTACHED .md FILES.**
> Read live repo via filesystem MCP only. Claude.ai project knowledge base attachments are stale (last updated S49, May 2026 -- 48 sessions behind as of S97). Any session that reads them instead of this file gets wrong deploy state, wrong next-work pointer, and wrong production baseline.

## Session Startup Order

1. `git status` — branch must be `main`; tree must be clean.
2. Read `CLAUDE.md` — operating rules and hard constraints.
3. Read `SNAPSHOT_LATEST.md` — verified machine state and active issues.
4. Read this file — next-work pointer.
5. Read `IRIS_ARCH.md` — only when architecture, pins, services, or deploy details are needed.

## Source of Truth

`C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face`

GitHub is a secondary mirror. Local state outranks it until explicitly synced.

## Production Baseline

| System | State |
|---|---|
| Pi4 | Operational — assistant.service active. **S123 (gesture MUTE/RIGHT + router polish), md5 repo=RAM=SD all 8:** assistant.py=`db96f785b796b9a61bed0b591f6fe5d8`, hardware/audio_io.py=`035d43b6d7e623f959354a9938110c5a`, hardware/base_mount_bridge.py=`9ba56cbb0862c11d2b28823700c4d2ad`, core/intent_router.py=`692c8e17b5340c0336bb1ade476ef1e0`, core/config.py=`d9ebc9c5751a2db89af9424b1af7c83f`, iris_web.py=`1fe3acc39ce4f54bc16c0e5621dd51d4`, iris_web.js=`5ffc825a52a53816a79d832cc37fd56e`, iris_web.html=`5925e0afd477917f37a62becba4efd18`. Unchanged from prior sessions: **hardware/teensy_bridge.py md5=f662309a45b8aa065dad1f0a40c27f85** (S122), **services/llm.py md5=911261166ce7aeed07a8e3ef1a2d044e** (S119), **iris_post.py md5=18748f348149590879f8a43b83f83f11** (S120), **services/vision.py md5=31cb7a089060ce3102c86281ac2936c6** (S120). POST 20/23 PASS, 0 FAIL, AUTHORIZED (S123). |
| GandalfAI | **OPERATIONAL (S119).** iris/iris-kids on **mistral-small3.2:24b** (was qwen3.5:27b), Ollama **0.30.7**. arch=mistral3, 15GB Q4, 100% GPU, **num_ctx 6144 (S119b, unified text+vision)**. Text ~42 tok/s; vision cold-after-text 2.4s / warm 1.6s (no reload). VISION_MODEL="iris" (Pixtral vision native). stop set includes `User:` (few-shot bleed fix). Kokoro TTS port 8004 OK. |
| Teensy 4.1 | Operational — firmware S101. Eye jitter fix (mouth 2Hz during TTS). |
| Teensy 4.0 | S97 FLASHED. FACE_RETURN_MS 30000ms. Tracking working. Mechanical damper tuning ongoing. |
| TTS | Kokoro primary (Docker 8004), Piper fallback (Wyoming 10200). |

## Navigation

- `SNAPSHOT_LATEST.md` — current verified state, active issues, last session changes.
- `ROADMAP.md` — all forward-looking tasks with full spec per item.
- `CHANGELOG.md` — completed sessions and batches.

## Deployment Gates

- Pi4 and GandalfAI mutations require explicit user authorization.
- GandalfAI model rebuilds require explicit `DEPLOY`.
- Pi4 persistence: direct `/media/root-ro` remount only — see `CLAUDE.md`.
- **Ollama 0.30.7** (runs mistral-small3.2:24b fine). Firewall outbound block on ollama app.exe in place; keep it to avoid surprise auto-upgrades. (qwen3.5 pin rationale is moot post-S119.)

## Next Work

- **DONE (S123): gesture MUTE/RIGHT fixes + router word-boundary polish (Session 3 of S121 review handoffs)** — CW now truly mutes to 0 and second CW restores; right swipe maps to STOP (default-merge in `_load_gesture_map`); "stopwatch…" no longer REFLEX/STOP; `SILENCE_RMS` constant used in main-loop gate; dead `GESTURE_SENSOR_REQUIRED` deleted; RD-003 closed. DEPLOYED + VERIFIED on live Pi4 (see CHANGELOG S123). **Remaining human check:** physical right swipe → journal `[GESTURE] gesture=RIGHT action=STOP`; physical CW rotate twice → silence then prior volume.
- **DONE (S122): playback pipeline hardening (Session 2 of S121 review handoffs)** — STOP race, cumulative TTS_MAX_CHARS cap, TeensyBridge reader death. DEPLOYED + VERIFIED via live Pi4 harness (real stream_ollama+Kokoro+play_pcm_stream; see CHANGELOG S122). **Remaining human check:** say "stop" through the mic during a LONG reply ("explain how radios work") — journal should show dispatch halt within ~1 sentence and the next wakeword accepted immediately.
- **DONE (S119b): num_ctx unified to 6144.** iris/iris-kids modelfiles raised 4096→6144 + GandalfAI rebuild; text+vision share one context. Vision cold-after-text 12.4s→2.4s (no reload), warm 1.6s, 100% GPU, 15GB at 6144 (VRAM safe). Resolves the long-standing S118 vision-latency item (`docs/handoff_vision_latency.md` now historical).
- **DONE (S120 Batch 3): `think:False` swept from the 4 remaining Pi4 callers** — assistant.py (ask_ollama + warmup), services/vision.py (ask_vision), iris_web.py (api_vision), iris_post.py (l3_llm). Stale qwen comments refreshed; vision num_ctx 6144 kept. DEPLOYED + VERIFIED (POST AUTHORIZED, LLM+vision smoke clean, no token bleed). See CHANGELOG S120 Batch 3 for live md5s + a flagged repo↔Pi4 line-ending/ASCII drift on assistant.py & iris_post.py (cosmetic, non-behavioral).

- **Pure Pi4-local STT commands (deferred S110):** Simple commands like "hey jarvis… go to sleep" handled by Pi4 Whisper without waking GandalfAI. Design session needed — user flagged this during RPQR work.
- **Wake-from-sleep fall-through:** Currently quip → re-sleep. Evaluate fall-through to active listening after quip (user must say "hey jarvis" twice to converse from sleep).
- **T40 mechanical damper** — servo tracking confirmed working, user tuning physically. No firmware change needed.
- **Bench tab dur_audio gap (G4):** `_from_jsonl` cycles missing `dur_audio` (play duration). Tracked in `docs/bench_audit_S105.md`.
- **Latency Bench AI analysis (S106 — REPO-ONLY):** Run AI Analysis + Generate Handoff wired on Latency Bench tab. Use after running bench iteration.
- **pt001 calibration tightening (optional):** 3 remaining failures — pt001_04 (ANGRY not NEUTRAL on "Shut up."), pt001_18 (CURIOUS not NEUTRAL on motor/servo), pt001_19 (NEUTRAL not AMUSED on sleep advice). pt001_01 "You're dumb." RESOLVED S115.

---

## Proactive Flags

*Cumulative. Append each session. Do not overwrite.*

- **[S118]** Vision requests are slow (~29 s) mostly because Ollama RELOADS iris each call: vision uses `num_ctx=6144`, text uses the 4096 default, and a ctx change forces a model reload (and the next text query reloads back to 4096). To eliminate the reloads, unify the context — either bump the iris/iris-kids modelfile `num_ctx` to 6144 (GandalfAI rebuild + slightly more KV-cache VRAM, watch the ~1 GB headroom) so text+vision share one context, or have the Pi4 text callers (`stream_ollama`, `ask_ollama`, warmup) also pass `num_ctx=6144`. Functional already; this is a latency optimization.
- **[S120]** Repo↔Pi4 drift on two deployed files (cosmetic, non-behavioral): repo `pi4/assistant.py` is CRLF while the live Pi4 copy is LF (content identical); repo `pi4/iris_post.py` uses Unicode punctuation (`→ × ── —`) and has one extra `l2_display` comment line, while the live Pi4 copy is ASCII-normalized (`-> x -- -`). vision.py and iris_web.py byte-match. A future session should normalize line endings repo-wide (add `.gitattributes` `* text=auto eol=lf`) and re-sync iris_post.py so RAM md5 == repo md5 cleanly; today's S120 deploy verified RAM==SD only (the project's actual gate), not RAM==repo.
- **[S118]** Vision was silently broken on the VOICE path too (not just web UI) since the S113/S114 model swap — `ask_vision()` swallowed the 400 and spoke "the current AI model doesn't support images." Fixed S118. Any future base-model swap must re-test vision with a REAL camera frame, not assume the capability flag is enough (context budget matters).

- **[S98 Chat → S116 RESOLVED]** LLM streaming into sentence-boundary TTS now implemented. `stream_ollama()` → per-sentence `synthesize()` → background `play_pcm_stream` player; first audio starts on the first sentence. Latency harness: LLM-start→first-audio p50=2086ms (was ~23s blocking on long replies). DEPLOYED S116, md5 RAM=SD verified. Behavioral hardware checks (speaker/emotion-face/spoken-STOP/Piper) still need a human in front of IRIS.
- **[S98 Chat]** VAD silence threshold likely default 500-800ms — tighten to 200-300ms for free latency reduction with no accuracy impact.
- **[S98 Chat → S111 VERIFIED]** Whisper model confirmed `large-v3-turbo` with `COMPUTE_TYPE=int8_float16`, `WHISPER_BEAM=1`. Already optimal — no change needed.
- **[S98 Chat → S111 VERIFIED]** Ollama tok/s confirmed **17.6 tok/s** for iris (qwen2.5:32b Q4_K_M) on Ollama 0.24.0, RTX 3090. Not the worst-case 12 tok/s, not the pre-regression 35 tok/s. Use 17-18 tok/s as the planning baseline (may shift slightly on VL base — re-bench if needed).
- **[S98 Chat → S111 VERIFIED → S112 UPDATE]** VRAM: iris/iris-kids now on qwen2.5vl:32b-q4_K_M (21GB file, ~23GB loaded with Kokoro). RTX 3090 = 24GB. Headroom ~1GB estimated. Vision queries no longer require model swap — VL base handles both text and vision natively.
- **[S98 Chat]** No weather handler in intent router Layer 2 — falls to LLM which cannot answer accurately; wttr.in call would make this a zero-LLM sub-100ms response.
- **[S98 Chat]** Jokes route to LLM despite 20-joke modelfile bank — local Layer 1 joke handler would serve these with no round trip.
- **[S111 Chat → S112 RESOLVED]** iris/iris-kids modelfiles now FROM qwen2.5vl:32b-q4_K_M. Vision live as of S112. DEPLOYED+VERIFIED.
- **[S111 Chat → S112 RESOLVED]** AMUSED calibration block added to iris modelfile. iris smoke test confirmed [EMOTION:AMUSED] on "You're dumb." input.
- **[S111 Chat → S112 RESOLVED]** All docs now correctly reflect qwen2.5vl:32b-q4_K_M as the active LLM base for iris/iris-kids.
- **[S114]** `"think": false` must be passed at API call level for every Ollama request to iris (qwen3.5:27b is a thinking model — without it, `response` field is empty). `PARAMETER think false` in modelfiles is NOT supported in Ollama 0.30.7 (error: unknown parameter). All five Pi4 Ollama callers patched: assistant.py, services/llm.py, iris_post.py, services/vision.py, and warmup call.
- **[S114]** qwen3.5:27b handles vision natively via /api/generate with `images` field. Separate VISION_MODEL config no longer needed — but kept as "iris" for fallback compatibility.
- **[S114 → S115 RESOLVED]** pt001_01 "You're dumb." ANGRY overtrigger fixed. Adversarial few-shot example in SYSTEM block changed ANGRY→AMUSED. Smoke test confirmed [EMOTION:AMUSED].
- **[S115 RESOLVED]** "what time is it" intent routing fixed. Was falling through to LLM (~1434ms). Now routes to UTILITY (<200ms). `_TIME_RE` now includes explicit `what time is it` literal and `time please` variant.
- **[S116 → S117 RESOLVED]** LONG/MAX-tier prompts generated 2400–2900 char (~2.5–3 min) replies. S117 retuned the tiers (SHORT/MED/LONG/MAX = 40/90/180/400 tok ≈ 9/21/41/92 s) and dropped `TTS_MAX_CHARS` to 1500 (~100 s hard backstop). MAX (story tier) is now reached only by explicit "tell me a story"/essay triggers; the word-count LONG→MAX promotion was removed. DEPLOYED+VERIFIED S117. Watch in real use that LONG (~41 s) and MAX (~92 s) truncations read naturally mid-stream; loosen toward the prior values if legitimate answers get clipped.
- **[S119]** Mistral exhibits few-shot turn-bleed: with the few-shot-heavy SYSTEM prompt it would, after answering, emit a fake `User: … IRIS: …` next turn (qwen's `<|im_end|>` had implicitly bounded this). Fixed by adding `PARAMETER stop "User:"` to both modelfiles. Any future few-shot-prompted base model swap: re-check for this and keep the `User:` stop.
- **[S119]** Vision residual latency is a num_ctx RELOAD, not GPU offload — confirmed `ollama ps` = 100% GPU during vision. The brief's assumption (>10s ⇒ offload) is wrong for Mistral; the lever is unifying num_ctx, not env vars/num_gpu. See Next Work.
- **[S119]** `num_ctx 4096` + ~3700-tok system prompt ⇒ only ~395 tok generation headroom; the MAX (400-tok) tier can overflow context before num_predict. Strong reason to raise modelfile num_ctx to 6144 now that Mistral (15GB) leaves the VRAM for it.
- **[S119]** sysmap.json `gandalf.services.ollama.model_base`/`stop_token` were stale (gemma3/`<end_of_turn>`); updated to mistral-small3.2 / `[INST]` this session. The `num_ctx_hard_limit: 4096` + "do not raise above 4096" warning in sysmap is gemma3/qwen-era (two-model 21GB VRAM math) and no longer applies to the single 15GB Mistral — treat as obsolete pending the num_ctx 6144 decision.
- **[S121]** [S98 Chat] VAD-tightening flag superseded — VAD silence threshold was tightened deliberately per S110/S115 tuning; current SILENCE_SECS value is intentional, not a loose default. Stale flag can be removed.
- **[S121]** S120 CRLF drift scope also covers `pi4/hardware/base_mount_bridge.py` (repo file is CRLF-only, verified S121) — include in any future line-ending normalization sweep alongside `assistant.py` and `iris_post.py`.
- **[S122]** POST's L2 firmware-version check WARNs (`no [VER] in journal`) on every service restart without a Teensy power cycle — [VER] is only emitted at Teensy boot. Cosmetic, but it makes the PASS count drift (20/23 vs 19/23) for reasons unrelated to actual health; POST could fall back to a serial VERSION query or remember the last seen [VER].
- **[S123]** 4 pre-existing pytest failures (verified present before this session's edits): 3 params of `tests/test_base_mount_bridge.py::test_gesture_map_dispatch` expect old bridge defaults (BACKWARD→SLEEP, CW→VOL+, CCW→VOL-) but `_DEFAULT_GESTURE_MAP` has had BACKWARD→WAKE, CW→MUTE, CCW→SKIP since before S123; plus `tests/test_iris_post.py::test_fail_outcome`. Also: bridge and iris_web `_DEFAULT_GESTURE_MAP` copies intentionally differ on BACKWARD/CW/CCW — reconcile or document which is canonical when fixing the tests.
- **[S123]** Live `iris_config.json` still contains a stale `GESTURE_SENSOR_REQUIRED` key (config loader logs it under "ignored unknown keys" at startup — harmless; file is PROTECTED, left untouched). `tools/workbench/index.html` also still has a GESTURE_SENSOR_REQUIRED toggle for the now-deleted constant.

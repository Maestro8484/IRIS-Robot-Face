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
| Pi4 | Operational — assistant.service active. **assistant.py md5=fe79c67bd5dfea50f5559e0304d37c35** (S116 streaming). **hardware/audio_io.py md5=ada50cfc3ab6b8ae52efdc7c7f9aab9c** (S116). **services/llm.py md5=911261166ce7aeed07a8e3ef1a2d044e** (S119: think:False removed for Mistral). **core/config.py md5=5391ed8c079dee4527c72ec8e148237f** (S117 tiers). iris_post.py md5=2bf0723a7f06d8f72896f3178af0e8ec. **services/vision.py md5=1e5500958db39e888db4bb4294150b9d** (S118 num_ctx). **iris_web.py md5=9f7af3a6d023edd794cb067abdff3871** (S118 vision fix). core/intent_router.py md5=ea9e0d82425f76d98053c2b71221ef99. RAM=SD (S118). POST 20/23 PASS. |
| GandalfAI | **OPERATIONAL (S119).** iris/iris-kids on **mistral-small3.2:24b** (was qwen3.5:27b), Ollama **0.30.7**. arch=mistral3, 15GB Q4, 100% GPU. Text 35.8 tok/s; vision warm 1.4s / cold ~12s. VISION_MODEL="iris" (Pixtral vision native). stop set includes `User:` (few-shot bleed fix). Kokoro TTS port 8004 OK. |
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

- **Vision latency — unify num_ctx to 6144 (S119 follow-up, needs user sign-off).** S119 mistral swap already cut cold vision 29s→~12s and warm to 1.4s at 100% GPU. The residual ~12s is the same num_ctx reload (vision 6144 vs text/modelfile 4096). To kill it: set iris/iris-kids modelfile `num_ctx 6144` + GandalfAI rebuild so text+vision share one context (also fixes the cramped ~395-tok generation budget vs the ~3700-tok system prompt). VRAM verified safe on mistral (15+2 Kokoro = 17/24 GB; `ollama ps` shows 15GB at 6144). Blocked only by the sysmap `num_ctx ≤ 4096` documented hard limit (now obsolete) — confirm before raising. Old spec: `docs/handoff_vision_latency.md`.
- **Sweep `think:False` from remaining Pi4 callers (S119 follow-up).** assistant.py, services/vision.py, iris_web.py, iris_post.py still send `think:False` (harmless dead weight on Mistral, no thinking mode). Remove for consistency + stale qwen comments. Deferred to keep S119 deploy surface to the one file the brief scoped (llm.py).

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

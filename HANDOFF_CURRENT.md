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
| Pi4 | Operational — assistant.service active. assistant.py DEPLOYED+VERIFIED S110. md5=fa5bf5b065951bdbf34ab27b3af0ea4e RAM=SD. iris_config.json SILENCE_SECS=1.2 DEPLOYED S110. md5=9dbd091fff10409f1e6d544d9e26b603 RAM=SD. |
| GandalfAI | **DEGRADED — TEXT BROKEN (S113).** iris/iris-kids on **qwen3.5:27b**. Ollama **0.24.0** does not GPU-dispatch qwen3.5 — 2.8 tok/s CPU-only. Upgrade to **Ollama 0.30.0** required (P0 before next IRIS use). AMUSED calibration preserved. Vision gone (off VL base). Kokoro TTS port 8004 OK. |
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
- **Upgrade Ollama to 0.30.0 on GandalfAI — P0.** 0.30.x CLIP restriction no longer applies (we are off qwen2.5vl). Run: `$env:OLLAMA_VERSION="0.30.0"; irm https://ollama.com/install.ps1 | iex` then re-apply Windows Firewall outbound block for `ollama app.exe` to pin at 0.30.0. After upgrade: rebuild iris + iris-kids, verify tok/s ≥ 30.

## Next Work

- **[P0 — IRIS BROKEN] Ollama 0.30.0 upgrade on GandalfAI:** Run PS command to install 0.30.0, re-apply firewall block for ollama app.exe, rebuild iris + iris-kids, verify tok/s ≥ 30. Then run persona harness pt001 (target ≥ 13/20). Update SNAPSHOT, HANDOFF, IRIS_ARCH.md VRAM section after confirmation.
- **[P0 — IRIS BROKEN] HANDOFF_CURRENT.md + CLAUDE.md firewall note:** After upgrade confirmed, update Deployment Gates to "DO NOT upgrade past 0.30.0, pinned for qwen3.5 stability."
- **Pure Pi4-local STT commands (deferred S110):** Simple commands like "hey jarvis… go to sleep" handled by Pi4 Whisper without waking GandalfAI. Design session needed — user flagged this during RPQR work.
- **Wake-from-sleep fall-through:** Currently quip → re-sleep. Evaluate fall-through to active listening after quip (user must say "hey jarvis" twice to converse from sleep).
- **T40 mechanical damper** — servo tracking confirmed working, user tuning physically. No firmware change needed.
- **Bench tab dur_audio gap (G4):** `_from_jsonl` cycles missing `dur_audio` (play duration). Tracked in `docs/bench_audit_S105.md`.
- **Latency Bench AI analysis (S106 — REPO-ONLY):** Run AI Analysis + Generate Handoff wired on Latency Bench tab. Use after running bench iteration.

---

## Proactive Flags

*Cumulative. Append each session. Do not overwrite.*

- **[S98 Chat]** LLM streaming into sentence-boundary TTS not implemented — pipeline waits for full LLM response before TTS starts, adding 1-2.5s perceived latency; streaming cuts this 40-60%.
- **[S98 Chat]** VAD silence threshold likely default 500-800ms — tighten to 200-300ms for free latency reduction with no accuracy impact.
- **[S98 Chat → S111 VERIFIED]** Whisper model confirmed `large-v3-turbo` with `COMPUTE_TYPE=int8_float16`, `WHISPER_BEAM=1`. Already optimal — no change needed.
- **[S98 Chat → S111 VERIFIED]** Ollama tok/s confirmed **17.6 tok/s** for iris (qwen2.5:32b Q4_K_M) on Ollama 0.24.0, RTX 3090. Not the worst-case 12 tok/s, not the pre-regression 35 tok/s. Use 17-18 tok/s as the planning baseline (may shift slightly on VL base — re-bench if needed).
- **[S98 Chat → S111 VERIFIED → S112 UPDATE]** VRAM: iris/iris-kids now on qwen2.5vl:32b-q4_K_M (21GB file, ~23GB loaded with Kokoro). RTX 3090 = 24GB. Headroom ~1GB estimated. Vision queries no longer require model swap — VL base handles both text and vision natively.
- **[S98 Chat]** No weather handler in intent router Layer 2 — falls to LLM which cannot answer accurately; wttr.in call would make this a zero-LLM sub-100ms response.
- **[S98 Chat]** Jokes route to LLM despite 20-joke modelfile bank — local Layer 1 joke handler would serve these with no round trip.
- **[S111 Chat → S112 RESOLVED]** iris/iris-kids modelfiles now FROM qwen2.5vl:32b-q4_K_M. Vision live as of S112. DEPLOYED+VERIFIED.
- **[S111 Chat → S112 RESOLVED]** AMUSED calibration block added to iris modelfile. iris smoke test confirmed [EMOTION:AMUSED] on "You're dumb." input.
- **[S111 Chat → S112 RESOLVED]** All docs now correctly reflect qwen2.5vl:32b-q4_K_M as the active LLM base for iris/iris-kids.

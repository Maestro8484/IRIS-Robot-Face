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
| GandalfAI | Operational — iris/iris-kids on **qwen2.5:32b** (text LLM). **Vision: qwen2.5vl:32b-q4_K_M active (S109)**. **Ollama 0.24.0** (firewall blocks auto-update — 0.30.x CLIP engine broken for this model). Kokoro TTS (Docker port 8004). |
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
- **DO NOT upgrade Ollama on GandalfAI.** 0.30.x series breaks qwen2.5vl CLIP loader. Firewall rule is in place. Leave it alone.

## Next Work

- **Pure Pi4-local STT commands (deferred S110):** Simple commands like "hey jarvis… go to sleep" handled by Pi4 Whisper without waking GandalfAI. Design session needed — user flagged this during RPQR work.
- **Wake-from-sleep fall-through:** Currently quip → re-sleep. Evaluate fall-through to active listening after quip (user must say "hey jarvis" twice to converse from sleep).
- **T40 mechanical damper** — servo tracking confirmed working, user tuning physically. No firmware change needed.
- **Bench tab dur_audio gap (G4):** `_from_jsonl` cycles missing `dur_audio` (play duration). Tracked in `docs/bench_audit_S105.md`.
- **Latency Bench AI analysis (S106 — REPO-ONLY):** Run AI Analysis + Generate Handoff wired on Latency Bench tab. Use after running bench iteration.

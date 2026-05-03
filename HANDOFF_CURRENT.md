<!-- Short session-start handoff only. Do not expand. Operational rules are in CLAUDE.md. -->

# IRIS Handoff — Current

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
| Pi4 | Operational — assistant.py, intent_router.py, iris_web.py deployed and persisted. |
| GandalfAI | Operational — gemma3:27b-it-qat, Kokoro TTS (Docker port 8004), iris model current. |
| Teensy 4.1 | Operational — eye movement suspended during TTS. |
| STT / TTS | Whisper (GandalfAI) / Kokoro primary, Piper fallback (Wyoming port 10200). |
| Wakeword | `hey_jarvis` (production). Experimental wakewords require explicit user approval, live Pi4 state confirmation, clean process restart, and one-model-at-a-time testing. Failed experiment names are in `CHANGELOG.md`. |

## Navigation

- `SNAPSHOT_LATEST.md` — current verified state, active issues, last session changes.
- `ROADMAP.md` — all forward-looking tasks with full spec per item.
- `CHANGELOG.md` — completed sessions and batches.

## Deployment Gates

- Pi4 and GandalfAI mutations require explicit user authorization.
- GandalfAI model rebuilds require explicit `DEPLOY`.
- Pi4 persistence: direct `/media/root-ro` remount only — see `CLAUDE.md`.

## Next Work

Batch D — AMUSED removal and "stop" pre-STT intercept. See `ROADMAP.md` (RD-001, RD-002).

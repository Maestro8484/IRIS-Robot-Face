# IRIS Session Primer - Wakeword Baseline Audit

Paste at the start of a new Claude Code session.

---

STOP. Do not respond yet.

IRIS project. Claude Desktop GUI on SuperMaster. Filesystem MCP active.

Source of truth:

```text
C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face
```

GitHub is secondary mirror only and may lag local state.

---

## Required Startup

Before any response:

1. Run `git status`.
2. Read `CLAUDE.md`.
3. Read `SNAPSHOT_LATEST.md`.
4. Read `HANDOFF_CURRENT.md`.
5. Read `HANDOFF_WAKEWORD_DEPLOY.md`.

Do not read `IRIS_ARCH.md` unless architecture, pins, deploy commands, or service config is needed.

---

## Pre-flight Output

Output:

- Branch, must be `main`; if not, stop.
- Last commit hash and message.
- Working tree clean or dirty; if dirty, stop and summarize.
- Current production wakeword according to docs.
- Wakeword files likely involved.
- Risk.
- Rollback.
- Whether the requested task is read-only or deploy.

Then wait for confirmation.

---

## Current Wakeword Decision

Production baseline:

```text
hey_jarvis
```

Custom wakeword attempt failed:

- `hey_der_iris`
- `real_quick_iris`

These are experimental only and must not be redeployed without explicit user approval.

---

## Task

Audit wakeword runtime state only.

Do not modify files.
Do not deploy.
Do not restart services.
Do not push to GitHub.

Report:

1. Current git status.
2. Exact wakeword-related modified or untracked files.
3. Whether assistant.py currently launches wyoming-openwakeword with stock `hey_jarvis`, `--preload-model`, or `--custom-model-dir`.
4. Whether Pi4 currently has `hey_jarvis`, `hey_der_iris`, or `real_quick_iris` ONNX/TFLite files.
5. Current `WAKE_WORD` in Pi4 `/home/pi/iris_config.json`.
6. Active wyoming-openwakeword process command line.
7. Whether port 10400 is owned by the expected wakeword process.
8. Recommended rollback path to stable `hey_jarvis`, if needed.
9. Recommended future path to test one custom wakeword only, if user later asks.

Wait for approval before any edits or deployment.

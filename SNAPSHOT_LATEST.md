# IRIS Robot Face — Session Snapshot
**Date:** 2026-04-20
**Session:** S25
**Branch:** `main`
**Last commit:** aa49b52 — refactor: dashboard v3 — dark theme, live polling, action buttons

> Architecture, pins, constants, cron, deploy commands: see [IRIS_ARCH.md](IRIS_ARCH.md)

---

## Machine Status

| System | Status |
|---|---|
| Pi4 (192.168.1.200) | Operational. assistant.py running. |
| GandalfAI (192.168.1.3) | Ollama iris/iris-kids on gemma3:12b. Chatterbox port 8004. IRISDashboard v3 port 8080. |
| Teensy 4.1 | Firmware built clean S22B (mouthSleepFrame). Awaiting manual flash. |
| TTS | Chatterbox primary, Piper fallback. |
| Web UI | Port 5000. Sleep/wake routes operational. |
| Cron sleep/wake | 9PM sleep / 7:30AM wake. Hardened S15. |

---

## Active Issues

- **HIGH: Teensy needs manual flash** — mouthSleepFrame + mouthSleepReset firmware built S22B, not yet flashed. Flash before verifying sleep animation.
- **HIGH: Mouth smoke test** — MOUTH:0–8 never confirmed post-installation. Do before any further firmware work.
- **MED: iris-kids asterisk** — gemma3 uses `*word*` emphasis. tts.py strips before TTS (cosmetic in web UI only).
- **MED: iris_config.json stale key** — `ELEVENLABS_ENABLED` still present, silently ignored.
- **LOW: /home/pi/iris_sleep.log** — stale root-level log from pre-S2.

---

## Session Scope (S25)
Deploy dashboard v3 — dark theme redesign, live Status tab (5s polling, VRAM bar, GPU/latency lines, 15-log terminal), Force Sleep/Wake action buttons, two new Flask routes.

---

## Do Not Touch (static)
`iris_config.json`, `alsa-init.sh`, `src/TeensyEyes.ino`, `src/eyes/EyeController.h` (seed fix intact), `pi4/services/tts.py` (ElevenLabs removal complete), `pi4/core/config.py`

---

## Last Session Changes (S25 — 2026-04-20)
**Task:** Dashboard v3 redesign + deploy

- `tools/iris_dashboard/app.py` — full HTML replaced with v3 dark-theme design. Status tab polls `/api/status` every 5s: 5 service pills (IRIS/Ollama/Whisper/Piper/Chatterbox) with green/red dots + per-service restart buttons; VRAM horizontal bar (green/amber/red thresholds); single-line GPU stats; single-line latency; 15-line auto-scrolling terminal log box; 4 action buttons (Restart IRIS, Restart All, Force Sleep, Force Wake). Logs tab: label+command+copy only, no prose. Playbooks/FalseWakeword: all collapsed by default, prose stripped to note-boxes only.
- `tools/iris_dashboard/app.py` — added `POST /api/action/sleep` (calls `python3 /home/pi/iris_sleep.py` via Pi4 SSH) and `POST /api/action/wake` routes.
- GandalfAI: sftp_write to `C:\Users\gandalf\iris_dashboard\app.py`, IRISDashboard service restarted, 200 OK confirmed.

## Previous Session Changes (S24 — 2026-04-19)
**Task:** Dashboard v2 deploy
- `tools/iris_dashboard/app.py` — HTML replaced with tabbed v2 layout: Log Viewers, Quick Links, Playbooks (8 playbooks), False Wakeword tabs. Python backend unchanged.
- GandalfAI: sftp_write + service restart, 200 OK verified.

---

## Known TODO (carry-forward)
- **Flash Teensy** — firmware built S22B (mouthSleepFrame), user must click PlatformIO upload
- Smoke test mouth TFT: Pi4 SSH → UDP 127.0.0.1:10500 → MOUTH:0 through MOUTH:8 → verify TFT renders
- Smoke test sleep animation: flash → web UI Sleep → verify BL breathes + sine + Z on TFT
- Smoke test return-to-sleep: trigger wakeword after 9PM → confirm IRIS returns to sleep after reply
- Exaggeration tuning: 0.45 starting point, tune after live voice test
- Piper standalone routing for iris_sleep.py Goodnight if Wyoming is down
- Chatterbox auto-start on GandalfAI boot (requires manual `docker compose up` after reboot)

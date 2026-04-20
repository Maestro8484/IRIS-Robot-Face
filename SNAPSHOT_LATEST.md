# IRIS Robot Face — Session Snapshot
**Date:** 2026-04-19
**Session:** S23
**Branch:** `main`
**Last commit:** ded77db — add IRIS mission control dashboard (GandalfAI Flask service, port 8080)

> Architecture, pins, constants, cron, deploy commands: see [IRIS_ARCH.md](IRIS_ARCH.md)

---

## Machine Status

| System | Status |
|---|---|
| Pi4 (192.168.1.200) | Operational. assistant.py + iris-web running. Ready confirmed S22B. |
| GandalfAI (192.168.1.3) | Ollama iris/iris-kids on gemma3:12b. Chatterbox port 8004. IRISDashboard Windows service port 8080. |
| Teensy 4.1 | Firmware built clean S22B (mouthSleepFrame). Awaiting manual flash. |
| TTS | Chatterbox primary, Piper fallback. ElevenLabs fully removed S20. |
| Web UI | Port 5000. Sleep/wake routes fixed S22B. |
| Cron sleep/wake | 9PM sleep / 7:30AM wake. Hardened S15. |

---

## Active Issues

- **HIGH: Teensy needs manual flash** — mouthSleepFrame + mouthSleepReset firmware built S22B, not yet flashed. Flash before verifying sleep animation.
- **HIGH: Mouth smoke test** — MOUTH:0–8 never confirmed post-installation. Do before any further firmware work.
- **MED: iris-kids asterisk** — gemma3 uses `*word*` emphasis. tts.py strips before TTS (cosmetic in web UI only).
- **MED: iris_config.json stale key** — `ELEVENLABS_ENABLED` still present, silently ignored.
- **LOW: /home/pi/iris_sleep.log** — stale root-level log from pre-S2.

---

## Session Scope (S23)
Deploy IRIS Mission Control Dashboard on GandalfAI as a persistent Windows service (port 8080).

---

## Do Not Touch (static)
`iris_config.json`, `alsa-init.sh`, `src/TeensyEyes.ino`, `src/eyes/EyeController.h` (seed fix intact), `pi4/services/tts.py` (ElevenLabs removal complete), `pi4/core/config.py`

---

## Last Session Changes (S23 — 2026-04-19)
**Task:** IRIS Mission Control Dashboard deploy

- `tools/iris_dashboard/app.py` — Flask server: `/` serves dark-theme dashboard UI, `/api/status` returns VRAM/GPU (Prometheus), service dots (port checks), Pi4 logs + assistant status (paramiko SSH), latency parse. `/api/restart/<service>` restarts assistant (Pi4 SSH) or docker containers (local subprocess).
- `tools/iris_dashboard/install_service.py` — pywin32 Windows service wrapper. Hardcoded `PYTHON_EXE = C:\Python314\python.exe` — `sys.executable` in service context resolves to `pythonservice.exe`, not python.exe (silent failure without hardcode).
- GandalfAI: service installed, StartType=Automatic, port 8080 LISTENING. Firewall rule "IRIS Dashboard 8080" added (inbound TCP 8080 Any). `requests` pip-installed (was missing from base env).
- `SNAPSHOT_LATEST.md` — updated to S23.

## Previous Session Changes (S22B — 2026-04-17)
**Task:** Sleep system fixes
- `pi4/iris_web.py`, `pi4/assistant.py`, `pi4/core/config.py` — sleep/wake sequence, return-to-sleep, SLEEP_WINDOW hours.
- `src/mouth_tft.cpp/.h`, `src/main.cpp` — mouthSleepFrame breathing animation, mouthSleepReset on wake.

---

## Known TODO (carry-forward)
- **Flash Teensy** — firmware built S22B (mouthSleepFrame), user must click PlatformIO upload
- Smoke test mouth TFT: Pi4 SSH → UDP 127.0.0.1:10500 → MOUTH:0 through MOUTH:8 → verify TFT renders
- Smoke test sleep animation: flash → web UI Sleep → verify BL breathes + sine + Z on TFT
- Smoke test return-to-sleep: trigger wakeword after 9PM → confirm IRIS returns to sleep after reply
- Exaggeration tuning: 0.45 starting point, tune after live voice test
- Piper standalone routing for iris_sleep.py Goodnight if Wyoming is down
- Chatterbox auto-start on GandalfAI boot (requires manual `docker compose up` after reboot)

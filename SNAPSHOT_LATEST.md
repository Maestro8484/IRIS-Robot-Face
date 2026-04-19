# IRIS Robot Face — Session Snapshot
**Date:** 2026-04-19
**Session:** S23
**Branch:** `main`
**Last commit:** (see git log)

> Architecture, pins, constants, cron, deploy commands: see [IRIS_ARCH.md](IRIS_ARCH.md)

---

## Machine Status

| System | Status |
|---|---|
| Pi4 (192.168.1.200) | Operational. assistant.py + iris-web running. Both services restarted and Ready S22B. |
| GandalfAI (192.168.1.3) | Ollama iris/iris-kids on gemma3:12b. Chatterbox port 8004. IRISDashboard Windows service on port 8080. |
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
Deploy IRIS Mission Control Dashboard on GandalfAI as a persistent Windows service.

## IRIS Mission Control Dashboard — DEPLOYED (S23)
- **Location:** GandalfAI `C:\Users\gandalf\iris_dashboard\app.py`
- **Repo:** `tools/iris_dashboard/`
- **Service:** `IRISDashboard` (Windows service, StartType=Automatic, port 8080)
- **Access:** http://192.168.1.3:8080 from any LAN browser
- **Data:** Prometheus GPU metrics (localhost:9090), port checks, Pi4 SSH (paramiko, password auth pi/ohs)
- **Grafana link:** points to Nvidia GPU metrics dashboard directly
- **Pi4 SSH:** password auth only (pi/ohs) — no key, uses paramiko
- **Note:** `sys.executable` in Windows service context resolves to `pythonservice.exe` — hardcoded `C:\Python314\python.exe` in install_service.py
- **Firewall:** inbound rule "IRIS Dashboard 8080" added

## Previous Session Scope (S22B)

---

## Do Not Touch (static)
`iris_config.json`, `alsa-init.sh`, `src/TeensyEyes.ino`, `src/eyes/EyeController.h` (seed fix intact), `pi4/services/tts.py` (ElevenLabs removal complete), `pi4/core/config.py`

---

## Last Session Changes (S22B — 2026-04-17)
**Task:** Sleep system fixes

- `pi4/iris_web.py` — `/api/sleep`: added `send_teensy("MOUTH:8")` + `open(SLEEP_FLAG).close()`. `/api/wake`: added `send_teensy("MOUTH:0")` + flag file removal.
- `src/mouth_tft.cpp` — `mouthSleepFrame()` implemented: breathing BL (8–22, -cos envelope), sine wave cy ±10px around 115 (amp=8, freq=0.028, stroke=5), Z glyph drifts upward over 60 frames / repeats every 150. `mouthSetSleepIntensity()` BL 40→8. File-scope `_sleepFrameCount`. `mouthSleepReset()` added.
- `src/mouth_tft.h` — `mouthSleepReset()` declaration added.
- `src/main.cpp` — `mouthSleepReset()` called in EYES:WAKE handler before `mouthRestoreIntensity()`.
- `pi4/core/config.py` — `SLEEP_WINDOW_START_HOUR = 21`, `SLEEP_WINDOW_END_HOUR = 8` added.
- `pi4/assistant.py` — `in_sleep_window()` + `return_to_sleep(teensy, st)` helpers added. Called after follow-up loop in main().
- Deployed + persisted to Pi4 SD. md5 match verified (iris_web.py: 8a77ef, assistant.py: 42cf90, config.py: 458b17). Both services restarted, Ready confirmed.

## Previous Session Changes (S22 — 2026-04-17)
**Task:** Token efficiency overhaul
- `IRIS_ARCH.md` created; arch tables, pins, constants, cron, serial protocol, deploy commands extracted here.
- `SNAPSHOT_LATEST.md` rewritten to lean 60–80 line format.
- 14 stale root files deleted; `CLAUDE.md` arch sections replaced with `See IRIS_ARCH.md`.

---

## Known TODO (carry-forward)
- **Flash Teensy** — firmware built S22B (mouthSleepFrame), user must click PlatformIO upload
- Smoke test mouth TFT: Pi4 SSH → UDP 127.0.0.1:10500 → MOUTH:0 through MOUTH:8 → verify TFT renders
- Smoke test sleep animation: flash → web UI Sleep → verify BL breathes + sine + Z on TFT
- Smoke test return-to-sleep: trigger wakeword after 9PM → confirm IRIS returns to sleep after reply
- Exaggeration tuning: 0.45 starting point, tune after live voice test
- Piper standalone routing for iris_sleep.py Goodnight if Wyoming is down
- Chatterbox auto-start on GandalfAI boot (requires manual `docker compose up` after reboot)

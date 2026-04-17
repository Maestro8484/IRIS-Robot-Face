# IRIS Robot Face — Session Snapshot
**Date:** 2026-04-17
**Session:** 22
**Branch:** `main`
**Last commit:** 4138cbc — docs: snapshot S21 2026-04-17 — web UI mouth matrix replaced with TFT controls

> Architecture, pins, constants, cron, deploy commands: see [IRIS_ARCH.md](IRIS_ARCH.md)

---

## Machine Status

| System | Status |
|---|---|
| Pi4 (192.168.1.200) | Operational. assistant.py running. |
| GandalfAI (192.168.1.3) | Ollama iris/iris-kids on gemma3:12b. Chatterbox port 8004. |
| Teensy 4.1 | Flashed. Eyes + mouth TFT build clean. Mouth smoke test pending. |
| TTS | Chatterbox primary, Piper fallback. ElevenLabs fully removed S20. |
| Web UI | Port 5000. TFT mouth controls live (S21). MAX7219 refs purged. |
| Cron sleep/wake | 9PM sleep / 7:30AM wake. Hardened S15. |

---

## Active Issues

- **HIGH: Mouth smoke test** — MOUTH:0–8 never confirmed post-installation. Do before any firmware work. Route: Pi4 SSH → UDP 127.0.0.1:10500 → TeensyBridge → TFT.
- **MED: iris-kids asterisk** — gemma3 uses `*word*` emphasis. tts.py strips before TTS (cosmetic in web UI only).
- **MED: iris_config.json stale key** — `ELEVENLABS_ENABLED` still present, silently ignored. Clean next file touch.
- **MED: Old GandalfAI source locations** — `C:\docker\whisper\`, `C:\docker\piper\`, `C:\Users\gandalf\Chatterbox-TTS-Server\` safe to delete after stability confirmed.
- **LOW: /home/pi/iris_sleep.log** — stale root-level log from pre-S2.

---

## Session Scope (S22)
Token efficiency overhaul: lean snapshot format, IRIS_ARCH.md extraction, repo root cleanup, session_start.py 80-line truncation.

---

## Do Not Touch (static)
`iris_config.json`, `alsa-init.sh`, `src/TeensyEyes.ino`, `src/eyes/EyeController.h` (seed fix intact), `pi4/services/tts.py` (ElevenLabs removal complete), `pi4/core/config.py`

---

## Last Session Changes (S21 — 2026-04-17)
**Task:** Web UI mouth tab — replace MAX7219/matrix refs with TFT mouth controls
- `pi4/iris_web.html` — "Mouth Matrix" → "TFT Mouth"; sleep tab two intensity inputs → single range slider
- `pi4/iris_web.html` — `saveMouthIntensity()` simplified to single `MOUTH_INTENSITY` value
- Deployed + persisted to Pi4 SD. md5: `86baeaffbc639cf12c3ac1b2c5db01cb` ✓
- `iris_web.py` had no matrix refs — unchanged
- Not touched: `src/` firmware, `iris_web.py`, `core/config.py`, `services/tts.py`, `iris_config.json`

## Previous Session Changes (S20 — 2026-04-16)
**Task:** Remove ElevenLabs; fix CLAUDE.md model refs; harden iris-kids no-asterisk
- `pi4/services/tts.py` — ElevenLabs branch removed; Chatterbox→Piper only
- `pi4/core/config.py` — ElevenLabs constants removed
- `ollama/iris-kids_modelfile.txt` — strengthened no-asterisk constraint (3 locations)
- `CLAUDE.md` — corrected model IDs to claude-sonnet-4-6 / claude-haiku-4-5

---

## Known TODO (carry-forward)
- Smoke test mouth TFT: Pi4 SSH → UDP 127.0.0.1:10500 → MOUTH:0 through MOUTH:8 → verify TFT renders
- Smoke test sleep LED: web UI Sleep button → indigo breathe; Wake → idle cyan
- Exaggeration tuning: 0.45 starting point, tune after live voice test
- Piper standalone routing for iris_sleep.py Goodnight if Wyoming is down
- Chatterbox auto-start on GandalfAI boot (requires manual `docker compose up` after reboot)
- TTS truncation threshold: 220 chars, monitor real responses

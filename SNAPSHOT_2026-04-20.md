# IRIS Snapshot
**Session:** S28 | **Date:** 2026-04-20 | **Branch:** `main` | **Last commit:** edb34ce

> Architecture, pins, constants, deploy commands: see IRIS_ARCH.md (load on demand)

---

## Machine Status

| System | Status |
|---|---|
| Pi4 192.168.1.200 | Operational. assistant.py running. |
| GandalfAI 192.168.1.3 | Ollama iris/iris-kids on gemma3:12b. Chatterbox port 8004. IRISDashboard port 8080. |
| Teensy 4.1 | Flashed (mouthSleepFrame). /dev/ttyACM0 present. |
| TTS | Chatterbox primary, Piper fallback. |
| Web UI | Port 5000 operational. |
| Cron sleep/wake | 9PM/7:30AM. Sleep wakeword silent (Piper path broken). |

---

## Active Issues

- **MED: Piper sleep routing** — `/usr/local/bin/piper` missing. `iris_sleep.py` says nothing on wakeword. Fix: route through Wyoming Piper at GandalfAI:10200.
- **MED: Volume persistence** — SPEAKER_VOLUME resets on reboot. Fix: add to iris_config.json + ALSA state write on web UI persist.
- **LOW: iris_config.json stale key** — ELEVENLABS_ENABLED silently ignored.
- **LOW: /home/pi/iris_sleep.log** — stale root-level log.

---

## Session Scope

S28: Add insult handling and response depth tiers to iris modelfile; rebuild and smoke test iris on GandalfAI.

---

## Do Not Touch

- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

---

## Last Session Changes (S28)

- `ollama/iris_modelfile.txt` — added insult handling to EMOTIONAL STATE AND EXPRESSION (dry wit, one line, no AI deflection, no break-character); added 4-tier depth guidance to HOW YOU SPEAK (one sentence / 1-2 / 2-4 / up to 6)
- GandalfAI: rebuilt `iris` model (`ollama create iris`); smoke tested — test 1 (Wisconsin Dells) 4 sentences clean, test 2 (insult) dry one-liner, both pass

## Previous Session Changes (S27)

- `ollama/iris_modelfile.txt` + `iris-kids_modelfile.txt`: num_predict 200, identity-first language, rebuilt both models
- `CLAUDE.md` + `SNAPSHOT_LATEST.md`: lean token-efficient reformat
- `IRIS_ARCH.md`: stale items corrected

---

## Known TODO

- Route Piper fallback through Wyoming Piper (GandalfAI:10200) in iris_sleep.py
- Persist SPEAKER_VOLUME across reboots via iris_config.json + ALSA write

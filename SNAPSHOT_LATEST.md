# IRIS Snapshot

**Session:** S33 | **Date:** 2026-04-24 | **Branch:** `main` | **Last commit:** verify with `git log --oneline -1`

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.
> Current state and roadmap: see `HANDOFF_CURRENT.md`.

---

## Machine Status

| System | Status |
|---|---|
| SuperMaster Desktop | Canonical local repo and control node. Claude Desktop, filesystem MCP, SSH MCP, VS Code, PlatformIO, and git available. |
| Pi4 192.168.1.200 | Operational. assistant.py running. Wakeword responding. |
| GandalfAI 192.168.1.3 | Ollama iris/iris-kids on gemma3:12b. Chatterbox port 8004. Whisper and Piper services hosted here. |
| Teensy 4.1 | Operational. All displays working. `/dev/ttyACM0` present when connected. |
| TTS | Chatterbox primary, Piper fallback. |
| Web UI | Operational. |
| Cron sleep/wake | 9PM/7:30AM. Sleep wakeword greeting still needs Wyoming Piper route in Batch 1C. |

---

## Delivery Model

MAD Loop is active for non-trivial changes.

Batch status:
- Batch 1A complete.
- Batch 1B complete.
- Next target: Batch 1C.

Canonical source of truth:
`C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face`

GitHub is a secondary mirror and may lag local state.

---

## Active Issues

- **MED: Piper sleep routing** - local `/usr/local/bin/piper` path is broken. Wakeword-during-sleep greeting should route through Wyoming Piper on GandalfAI:10200 in Batch 1C.
- **MED: Volume persistence** - `SPEAKER_VOLUME` may reset on reboot. Batch 1C should persist through `iris_config.json` and/or ALSA state workflow.
- **LOW: iris_config.json stale keys** - unknown keys such as `ELEVENLABS_ENABLED` may still exist and are ignored by `core/config.py`.
- **LOW: root-level stale sleep log** - `/home/pi/iris_sleep.log` may be stale or duplicated relative to `/home/pi/logs/iris_sleep.log`.

---

## Do Not Touch Without Explicit Instruction

- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

---

## !! HIGH PRIORITY - Active Tuning Area !!

### Dynamic Response Length (needs live testing + tuning)

`classify_response_length()` in `services/llm.py` classifies each utterance into SHORT/MEDIUM/LONG/MAX tiers before calling Ollama. Tier values are runtime-overridable via `iris_config.json`. Modelfile floor raised to 800 tokens. System prompt "default to less" instruction removed.

**What to watch for:**
- SHORT tier (120 tokens) cutting off greetings or factual responses -- widen SHORT patterns or raise NUM_PREDICT_SHORT
- MEDIUM tier (350) insufficient for conversational depth -- raise to 450-500
- LONG tier (700) triggering on questions that don't need it -- tighten _LONG_PATTERNS list
- MAX tier (1200) latency impact -- may need to cap lower for voice UX
- Word-count heuristics in classify_response_length() are a first pass -- adjust thresholds after observing real transcripts

**Tuning levers (no redeploy needed):**
Add to `iris_config.json`: `"NUM_PREDICT_SHORT": 150, "NUM_PREDICT_MEDIUM": 400, "NUM_PREDICT_LONG": 700, "NUM_PREDICT_MAX": 1000`

**Files:**
- `pi4/services/llm.py` -- `classify_response_length()`, `_SHORT_PATTERNS`, `_LONG_PATTERNS`, `_MAX_PATTERNS`
- `pi4/core/config.py` -- tier constants NUM_PREDICT_SHORT/MEDIUM/LONG/MAX
- `pi4/assistant.py` -- two call sites logging `num_predict=N` in `[LLM]` lines
- `ollama/iris_modelfile.txt` / `ollama/iris-kids_modelfile.txt` -- num_predict 800 floor

---

## Last Completed Work

### Batch 1A - Runtime Survival

- OpenWakeWord startup retry/backoff implemented.
- Runtime restart if OWW process dies.
- Wakeword socket timeout added.
- Wakeword failures return `"error"` instead of silent hang.
- Main loop skips STT/LLM/TTS when wakeword error occurs.
- Deployed, persisted, committed, and pushed.

### Batch 1B - Sleep/Wake Authority

- `_do_sleep()` and `_do_wake()` introduced in assistant runtime.
- Sleep/wake state centralized for assistant command handling and wakeword-during-sleep path.
- `/tmp/iris_sleep_mode` synchronized with runtime state.
- `send_command()` and `send_emotion()` return bool.
- Web sleep/wake routes update mouth intensity.
- `iris_wake.py` clears `/tmp/iris_sleep_mode`.

---

## Immediate Handoff

Next work is Batch 1C only.

Batch 1C target:
- Fix sleep wakeword greeting through Wyoming Piper.
- Persist `SPEAKER_VOLUME` across reboot.
- Add TTS hard-cap fallback.
- Add config validation/coercion.
- Replace unsafe temp file creation in vision service.
- Add rate-limited malformed JSON logging in LLM stream.
- Remove dead code only if verified unused.

Rules:
- One batch only.
- Minimal diffs.
- No broad refactors.
- Use direct `/media/root-ro` persistence only.
- Test before continuing.

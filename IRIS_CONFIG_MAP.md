# IRIS Configuration Map
**Generated:** S35 | 2026-04-25
**Purpose:** Every beneficially-editable value in the IRIS system — mapped to file, web UI location, type/range, and feature relationship.

---

## Overlayfs Write Model (Pi4)

All iris_config.json changes write to RAM layer (`/home/pi/iris_config.json`) first.
Changes survive assistant restarts but are **lost on reboot** unless persisted.
Use the **"Persist to SD"** button (always visible in the web UI top bar) to commit to SD layer.

Pattern: RAM write → SD copy via `/media/root-ro` remount → md5 verify → remount ro.

---

## Pi4 — `iris_config.json` + `core/config.py`

All values below are stored as defaults in `core/config.py` and overridden at runtime
from `iris_config.json`. The web UI reads and writes `iris_config.json` only.

### Audio — Recording
| Key | Type | Range | Default | Web UI Tab | Feature |
|---|---|---|---|---|---|
| RECORD_SECONDS | int | 1–60 | 10 | Audio | Max recording window per adult utterance |
| SILENCE_SECS | float | 0.1–10.0 | 1.5 | Audio | Silence duration that ends recording |
| SILENCE_RMS | int | 50–5000 | 300 | Audio | RMS floor below which counts as silence |
| KIDS_RECORD_SECONDS | int | 1–60 | 14 | Audio | Kids mode max record window |
| KIDS_SILENCE_SECS | float | 0.1–15.0 | 3.5 | Audio | Kids silence timeout (slower talkers) |
| KIDS_SILENCE_RMS | int | 50–5000 | 150 | Audio | Kids RMS floor (quieter voices) |

### Wake Word — OpenWakeWord
| Key | Type | Range | Default | Web UI Tab | Feature |
|---|---|---|---|---|---|
| OWW_THRESHOLD | float | 0.5–1.0 | 0.90 | Wake Word | Confidence gate for wakeword trigger. Higher = fewer false positives. |
| OWW_DRAIN_SECS | float | 0.05–1.0 | 0.15 | Wake Word | Audio flushed after wakeword before recording starts. Controls wakeword bleed-in. |

> `WAKE_WORD` (string, e.g. `"hey_der_iris"`) is stored in iris_config.json and shown
> read-only on the Wake Word tab. Changing it requires a wyoming-openwakeword restart
> (not wired to the UI save — must be done via assistant restart).

### Voice / TTS — Chatterbox (Primary)
| Key | Type | Range | Default | Web UI Tab | Feature |
|---|---|---|---|---|---|
| CHATTERBOX_ENABLED | bool | — | true | Voice | Use Chatterbox. False falls through to Piper. |
| CHATTERBOX_VOICE | string | — | iris_voice.wav | Voice | Reference audio file for voice cloning (GandalfAI:8004/voices/) |
| CHATTERBOX_EXAGGERATION | float | 0.0–2.0 | 0.45 | Voice | Vocal expression intensity. 0=flat, 0.45=dry wit, 1.0=dramatic. |

### Conversation / LLM — Follow-up & Context
| Key | Type | Range | Default | Web UI Tab | Feature |
|---|---|---|---|---|---|
| FOLLOWUP_TIMEOUT | int | 1–60 | 2 | Conversation | Seconds to wait for follow-up after IRIS finishes speaking |
| KIDS_FOLLOWUP_TIMEOUT | int | 1–120 | 15 | Conversation | Kids mode follow-up wait (longer for slower responses) |
| FOLLOWUP_MAX_TURNS | int | 1–20 | 3 | Conversation | Max back-and-forth turns before returning to idle |
| CONTEXT_TIMEOUT_SECS | int | 30–3600 | 300 | Conversation | Inactivity seconds before conversation history is cleared |

### Conversation / LLM — Response Length Tiers
IRIS classifies each query into a tier and uses the matching token budget.
Tier selection is automatic based on question complexity.

| Key | Type | Range | Default | Web UI Tab | Feature |
|---|---|---|---|---|---|
| NUM_PREDICT_SHORT | int | 10–2000 | 120 | Conversation | Token budget: greetings, yes/no, simple facts |
| NUM_PREDICT_MEDIUM | int | 10–2000 | 350 | Conversation | Token budget: explanations, multi-step answers |
| NUM_PREDICT_LONG | int | 10–2000 | 700 | Conversation | Token budget: stories, how-to, lists, comparisons |
| NUM_PREDICT_MAX | int | 10–2000 | 1200 | Conversation | Token budget: essays, code, "tell me everything" |
| TTS_MAX_CHARS | int | 100–4000 | 900 | Conversation | Character cap before TTS truncation at sentence boundary (~5–8 sentences) |

### Gandalf AI — Ollama Models
| Key | Type | Range | Default | Web UI Tab | Feature |
|---|---|---|---|---|---|
| OLLAMA_MODEL_ADULT | string | — | iris | Gandalf AI | Ollama model name used in adult mode |
| OLLAMA_MODEL_KIDS | string | — | iris-kids | Gandalf AI | Ollama model name used in kids mode |

### Sleep / Display — Mouth (MAX7219)
| Key | Type | Range | Default | Web UI Tab | Feature |
|---|---|---|---|---|---|
| MOUTH_INTENSITY_AWAKE | int | 0–15 | 8 | Sleep | MAX7219 backlight when IRIS is active |
| MOUTH_INTENSITY_SLEEP | int | 0–15 | 1 | Sleep | MAX7219 backlight when IRIS is sleeping |

### Sleep / Display — LEDs (APA102, Sleep)
| Key | Type | Range | Default | Web UI Tab | Feature |
|---|---|---|---|---|---|
| LED_SLEEP_PEAK | int | 0–255 | 26 | Sleep | APA102 peak brightness during sleep breathe (indigo) |
| LED_SLEEP_FLOOR | int | 0–255 | 3 | Sleep | APA102 floor brightness during sleep breathe |
| LED_SLEEP_PERIOD | float | 0.5–30.0 | 8.0 | Sleep | Sleep LED breathe cycle period in seconds |

### Lights — LEDs (APA102, Idle + Kids)
| Key | Type | Range | Default | Web UI Tab | Feature |
|---|---|---|---|---|---|
| LED_IDLE_PEAK | int | 0–255 | 65 | Lights | APA102 peak brightness when listening/idle (cyan) |
| LED_IDLE_FLOOR | int | 0–255 | 3 | Lights | APA102 floor brightness when idle |
| LED_IDLE_PERIOD | float | 0.5–30.0 | 5.0 | Lights | Idle LED breathe cycle period in seconds |
| LED_KIDS_PEAK | int | 0–255 | 62 | Lights | APA102 peak brightness in kids mode (yellow) |
| LED_KIDS_PERIOD | float | 0.5–30.0 | 4.0 | Lights | Kids mode LED breathe cycle period in seconds |

### System — Volume (wm8960)
| Key | Type | Range | Default | Web UI Tab | Feature |
|---|---|---|---|---|---|
| SPEAKER_VOLUME | int | 60–127 | 121 | System | wm8960 ALSA speaker level applied at startup (~95%) |
| VOL_MAX | int | 60–127 | 127 | System | Hard ceiling for voice volume commands ("louder"/"quieter") |

---

## Pi4 — `core/config.py` (hardcoded, not in iris_config.json)

These require a code edit + deploy to change. Not exposed in the web UI.

| Constant | Value | Feature |
|---|---|---|
| SAMPLE_RATE | 16000 Hz | Microphone sample rate |
| CHANNELS | 2 | Mic channel count |
| CHUNK | 1024 | Audio buffer chunk size |
| SLEEP_WINDOW_START_HOUR | 21 (9 PM) | Auto-sleep hour (cron-driven) |
| SLEEP_WINDOW_END_HOUR | 8 (8 AM) | Auto-wake hour |
| WOL_BOOT_TIMEOUT | 120 s | Max wait for GandalfAI after WoL packet |
| WOL_POLL_INTERVAL | 5 s | WoL poll interval |
| CAMERA_ENABLED | True | Enable/disable vision pipeline |
| CAMERA_WIDTH/HEIGHT | 1024×768 | Vision capture resolution |
| CAMERA_TIMEOUT | 5000 ms | Vision capture timeout |
| VISION_MODEL | "iris" | Ollama model used for image queries |
| CONVERSATION_LOG | /home/pi/logs/conversations.jsonl | Session log path |
| FOLLOWUP_SHORT_LEN | 60 chars | Min reply length to trigger follow-up prompt |
| NUM_PREDICT | 300 | Legacy fallback token budget (pre-tier system) |
| PIPER_VOICE | en_US-ryan-high | Piper TTS voice (fallback engine) |
| OWW_PORT | 10400 | Wyoming-openwakeword TCP port |
| WHISPER_PORT | 10300 | Wyoming Whisper TCP port |
| PIPER_PORT | 10200 | Wyoming Piper TCP port |
| OLLAMA_PORT | 11434 | Ollama HTTP port |
| CMD_PORT | 10500 | Web UI → assistant UDP bridge port |

---

## GandalfAI — `C:\IRIS\chatterbox\config.yaml`

These are **Chatterbox server defaults** for the Chatterbox Web UI (port 8004).
IRIS pipeline does not use these directly — IRIS sends per-request parameters
via `CHATTERBOX_EXAGGERATION` from iris_config.json.

| Key | Value | Feature |
|---|---|---|
| generation_defaults.temperature | 0.8 | Sampling temperature for Chatterbox Web UI |
| generation_defaults.exaggeration | 0.5 | Web UI default (IRIS overrides with CHATTERBOX_EXAGGERATION) |
| generation_defaults.cfg_weight | 0.5 | Classifier-free guidance weight |
| generation_defaults.speed_factor | 1.0 | Speech rate multiplier (1.0 = normal) |
| generation_defaults.seed | 0 | 0 = random; non-zero = reproducible output |
| audio_output.max_reference_duration_sec | 30 | Max reference audio clip length for voice cloning |
| server.port | 8000 | Internal Chatterbox port (mapped to 8004 externally) |

> To expose speed_factor or cfg_weight in the IRIS web UI: add to iris_config.json schema,
> pass through services/tts.py Chatterbox POST body. ~30 min work.

---

## GandalfAI — Ollama Modelfiles (`ollama show iris`)

Stored in Ollama's internal model registry. Edit via `ollama create iris -f Modelfile`.

| Parameter | Current | VRAM constraint | Feature |
|---|---|---|---|
| System prompt | IRIS personality text | — | Tone, rules, persona, response style |
| num_ctx | ≤4096 | Hard limit — RTX 3090 with Chatterbox loaded leaves <4GB headroom | Context window size |
| num_predict | model default | Overridden per-query by IRIS tier system | Max tokens per response |
| temperature | model default | — | LLM creativity / randomness |
| top_p / top_k | model default | — | Nucleus / top-k sampling |

---

## GandalfAI — Wyoming Services (Docker)

Configured in `C:\IRIS\docker\docker-compose.yml` and `docker-compose.gandalf.yml`.
Port changes require docker-compose restart and matching config.py updates.

| Service | Port | Model/Voice | Notes |
|---|---|---|---|
| Wyoming Whisper | 10300 | faster-whisper-large-v3-turbo | STT. Model fixed in docker image. |
| Wyoming Piper | 10200 | en_US-ryan-high | TTS fallback. Voice selectable via PIPER_VOICE in config.py. |

---

## Pi4 — wyoming-openwakeword

Launched by `assistant.py`. Config split between iris_config.json and launch args.

| Parameter | Location | Restart needed | Notes |
|---|---|---|---|
| WAKE_WORD | iris_config.json | Yes — wyoming restarts on assistant restart | Model file loaded from custom dir |
| OWW_THRESHOLD | iris_config.json | No | Confidence gate, read each detection cycle |
| OWW_DRAIN_SECS | iris_config.json | No | Buffer drain after detection, read each cycle |
| Custom model dir | assistant.py:334 | Yes | `/home/pi/wyoming-openwakeword/custom/` |

---

## Stale / Orphan Keys

| Key | Location | Status |
|---|---|---|
| MOUTH_INTENSITY | iris_config.json (live) | Dead key — not in _OVERRIDABLE. Replace with MOUTH_INTENSITY_AWAKE/SLEEP via web UI save + persist. |
| ELEVENLABS_ENABLED | iris_config.json (live) | Ignored — ElevenLabs not implemented. Safe to remove manually. |
| NUM_PREDICT | iris_config.json (if set) | Legacy. Superseded by tier system (SHORT/MEDIUM/LONG/MAX). Still applied as fallback if tier logic skips. |

---

## Deploy Checklist (after web UI changes)

1. Make changes in web UI
2. Click **"Persist to SD"** — waits for green "SD: synced" confirmation
3. Restart assistant via **System → Restart IRIS Assistant**
4. Verify in Logs tab that `[CFG] iris_config.json loaded:` shows the new values
5. For wakeword model changes: also confirm wyoming restarted with new model in logs

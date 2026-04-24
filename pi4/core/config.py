"""
core/config.py - IRIS assistant configuration constants
All static config and iris_config.json overrides live here.
Import with: from core.config import *
"""

import json as _json
import os as _os
import re

# ── Network ───────────────────────────────────────────────────────────────────
GANDALF        = "192.168.1.3"
WHISPER_PORT   = 10300
PIPER_PORT     = 10200
OLLAMA_PORT    = 11434
OWW_PORT       = 10400
CMD_PORT       = 10500  # web UI → Teensy command bridge

# ── Models ────────────────────────────────────────────────────────────────────
OLLAMA_MODEL_ADULT = "iris"
OLLAMA_MODEL_KIDS  = "iris-kids"
WAKE_WORD      = "hey_jarvis"
PIPER_VOICE    = "en_US-ryan-high"

# ── Chatterbox TTS ────────────────────────────────────────────────────────────
CHATTERBOX_BASE_URL     = "http://192.168.1.3:8004"
CHATTERBOX_VOICE        = "iris_voice.wav"
CHATTERBOX_EXAGGERATION = 0.45
CHATTERBOX_ENABLED      = True

# ── Audio ─────────────────────────────────────────────────────────────────────
SAMPLE_RATE    = 16000
CHANNELS       = 2
CHUNK          = 1024
RECORD_SECONDS = 10
SILENCE_SECS   = 1.5
SILENCE_RMS    = 300

# Kids mode overrides -- applied dynamically when _kids_mode is True
KIDS_RECORD_SECONDS   = 14
KIDS_SILENCE_SECS     = 3.5
KIDS_SILENCE_RMS      = 150

# ── Hardware ──────────────────────────────────────────────────────────────────
BUTTON_PIN     = 17
NUM_LEDS       = 3
TEENSY_PORT    = "/dev/ttyACM0"
TEENSY_BAUD    = 115200

# ── APA102 LED animations ─────────────────────────────────────────────────────
LED_IDLE_PEAK      = 65     # cyan breathe normal max (0-255)
LED_IDLE_FLOOR     = 3
LED_IDLE_PERIOD    = 5.0    # seconds per full cycle
LED_KIDS_PEAK      = 62     # yellow breathe kids mode max
LED_KIDS_PERIOD    = 4.0
LED_SLEEP_PEAK     = 26     # indigo breathe sleep max (~10% of 255)
LED_SLEEP_FLOOR    = 3
LED_SLEEP_PERIOD   = 8.0
LED_SLEEP_BRIGHT   = 0xFF   # APA102 global brightness byte (31/31, color value controls level)

# ── Volume ────────────────────────────────────────────────────────────────────
VOL_CONTROL    = "Speaker"
VOL_MIN        = 60
VOL_MAX        = 127
VOL_STEP       = 10
SPEAKER_VOLUME = 121   # default 95%; overridden by iris_config.json

# ── Follow-up / context ───────────────────────────────────────────────────────
FOLLOWUP_TIMEOUT      = 2
KIDS_FOLLOWUP_TIMEOUT = 15
FOLLOWUP_SHORT_LEN    = 60
FOLLOWUP_MAX_TURNS    = 3
CONTEXT_TIMEOUT_SECS  = 300
NUM_PREDICT           = 150
CONVERSATION_LOG      = "/home/pi/logs/conversations.jsonl"

# ── Camera / Vision ───────────────────────────────────────────────────────────
CAMERA_ENABLED = True
CAMERA_WIDTH   = 1024
CAMERA_HEIGHT  = 768
CAMERA_TIMEOUT = 5000
VISION_MODEL   = "iris"

VISION_TRIGGERS = {
    # contracted forms
    "what's this", "what's in front of you", "what's that",
    # Whisper spells contractions out -- always add the expanded version
    "what is this", "what is in front of you", "what is that",
    "what do you see", "what can you see",
    "look at this", "look at that",
    "what am i holding",
    "can you see", "can you see this",
    "describe this", "describe what you see",
    "what do you think this is",
    "take a picture", "take a photo",
    "what are you looking at",
    "identify this", "identify what",
    "who is this", "who is that",
}

# ── Sleep window ─────────────────────────────────────────────────────────────
SLEEP_WINDOW_START_HOUR = 21  # 9 PM
SLEEP_WINDOW_END_HOUR   = 8   # 8 AM

# ── Eye trigger phrases ───────────────────────────────────────────────────────
EYES_SLEEP_TRIGGERS = {
    "turn off your eyes", "turn off eyes", "turn off the eyes",
    "close your eyes", "close eyes", "eyes off", "eyes sleep",
    "sleep your eyes", "sleep eyes", "shut your eyes", "shut eyes",
    "deactivate your eyes", "disable your eyes"
}
EYES_WAKE_TRIGGERS = {
    "turn on your eyes", "turn on eyes", "turn on the eyes",
    "open your eyes", "open eyes", "eyes on", "eyes wake",
    "wake your eyes", "wake eyes", "wake up eyes",
    "activate your eyes", "enable your eyes"
}

# ── WoL / GandalfAI ───────────────────────────────────────────────────────────
GANDALF_MAC      = "A4:BB:6D:CA:83:20"
GANDALF_WOL_IP   = "192.168.1.3"
GANDALF_WOL_PORT = 7
WOL_BOOT_TIMEOUT  = 120
WOL_POLL_INTERVAL = 5

# ── Wake word ─────────────────────────────────────────────────────────────────
OWW_THRESHOLD  = 0.90

# ── Mouth MAX7219 intensity ───────────────────────────────────────────────────
MOUTH_INTENSITY_AWAKE = 8   # MAX7219 register 0x0A, range 0-15
MOUTH_INTENSITY_SLEEP = 1

# ── Emotion ───────────────────────────────────────────────────────────────────
VALID_EMOTIONS = {"NEUTRAL", "HAPPY", "CURIOUS", "ANGRY", "SLEEPY", "SURPRISED", "SAD", "CONFUSED"}
MOUTH_MAP = {
    "NEUTRAL":   0,
    "HAPPY":     1,
    "CURIOUS":   2,
    "ANGRY":     3,
    "SLEEPY":    4,
    "SURPRISED": 5,
    "SAD":       6,
    "CONFUSED":  7,
}
EMOTION_TAG_RE = re.compile(r'^\[EMOTION:([A-Z]+)\]\s*', re.IGNORECASE)

# ── iris_config.json loader (web UI overrides) ────────────────────────────────
_OVERRIDABLE = {
    "RECORD_SECONDS", "SILENCE_SECS", "SILENCE_RMS",
    "KIDS_RECORD_SECONDS", "KIDS_SILENCE_SECS", "KIDS_SILENCE_RMS",
    "OWW_THRESHOLD", "FOLLOWUP_TIMEOUT", "KIDS_FOLLOWUP_TIMEOUT",
    "FOLLOWUP_MAX_TURNS", "CONTEXT_TIMEOUT_SECS", "NUM_PREDICT",
    "CHATTERBOX_VOICE", "CHATTERBOX_EXAGGERATION", "CHATTERBOX_ENABLED",
    "VOL_MAX", "SPEAKER_VOLUME", "OLLAMA_MODEL_ADULT", "OLLAMA_MODEL_KIDS",
    "LED_IDLE_PEAK", "LED_IDLE_FLOOR", "LED_IDLE_PERIOD",
    "LED_KIDS_PEAK", "LED_KIDS_PERIOD",
    "LED_SLEEP_PEAK", "LED_SLEEP_FLOOR", "LED_SLEEP_PERIOD",
    "MOUTH_INTENSITY_AWAKE", "MOUTH_INTENSITY_SLEEP",
}

_CONFIG_PATH = "/home/pi/iris_config.json"

try:
    with open(_CONFIG_PATH) as _f:
        _cfg = _json.load(_f)
    _applied = []
    _ignored = []
    for _k, _v in _cfg.items():
        if _k in _OVERRIDABLE:
            globals()[_k] = _v
            _applied.append(f"{_k}={_v!r}")
        else:
            _ignored.append(_k)
    print(f"[CFG]  iris_config.json loaded: {', '.join(_applied) if _applied else 'no overrides'}", flush=True)
    if _ignored:
        print(f"[CFG]  iris_config.json ignored unknown keys: {_ignored}", flush=True)
except FileNotFoundError:
    print(f"[CFG]  iris_config.json not found, using defaults", flush=True)
except _json.JSONDecodeError as _e:
    print(f"[CFG]  iris_config.json parse error: {_e} — using defaults", flush=True)
except Exception as _e:
    print(f"[CFG]  iris_config.json load failed: {_e} — using defaults", flush=True)

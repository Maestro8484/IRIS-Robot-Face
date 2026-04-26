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

# ── Kokoro TTS ────────────────────────────────────────────────────────────────
KOKORO_BASE_URL  = "http://192.168.1.3:8004"
KOKORO_VOICE     = "bm_lewis"
KOKORO_ENABLED   = True

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
NUM_PREDICT           = 300
# ── Response length tiers ──────────────────────────────────────────────────────
NUM_PREDICT_SHORT     = 120   # greetings, yes/no, simple facts
NUM_PREDICT_MEDIUM    = 350   # explanations, multi-step answers
NUM_PREDICT_LONG      = 700   # stories, detailed how-to, lists, comparisons
NUM_PREDICT_MAX       = 1200  # "tell me everything about", essays, code
# ── TTS ───────────────────────────────────────────────────────────────────────
TTS_MAX_CHARS         = 900   # Chatterbox hard-cap; ~5-8 spoken sentences
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
OWW_DRAIN_SECS = 0.15   # audio drained after wakeword before recording starts

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
    "FOLLOWUP_MAX_TURNS", "CONTEXT_TIMEOUT_SECS", "NUM_PREDICT", "NUM_PREDICT_SHORT", "NUM_PREDICT_MEDIUM", "NUM_PREDICT_LONG", "NUM_PREDICT_MAX", "TTS_MAX_CHARS",
    "CHATTERBOX_VOICE", "CHATTERBOX_EXAGGERATION", "CHATTERBOX_ENABLED",
    "KOKORO_VOICE", "KOKORO_ENABLED",
    "VOL_MAX", "SPEAKER_VOLUME", "OLLAMA_MODEL_ADULT", "OLLAMA_MODEL_KIDS",
    "LED_IDLE_PEAK", "LED_IDLE_FLOOR", "LED_IDLE_PERIOD",
    "LED_KIDS_PEAK", "LED_KIDS_PERIOD",
    "LED_SLEEP_PEAK", "LED_SLEEP_FLOOR", "LED_SLEEP_PERIOD",
    "MOUTH_INTENSITY_AWAKE", "MOUTH_INTENSITY_SLEEP",
    "OWW_DRAIN_SECS",
}

# Type coercion and range bounds for overridable numeric/bool keys.
# String keys (CHATTERBOX_VOICE, OLLAMA_MODEL_*) are not listed -- passed through as-is.
# Range is (min_inclusive, max_inclusive). None = no range check (bool only).
_TYPE_COERCE = {
    "RECORD_SECONDS":          (int,   (1, 60)),
    "SILENCE_SECS":            (float, (0.1, 10.0)),
    "SILENCE_RMS":             (int,   (50, 5000)),
    "KIDS_RECORD_SECONDS":     (int,   (1, 60)),
    "KIDS_SILENCE_SECS":       (float, (0.1, 15.0)),
    "KIDS_SILENCE_RMS":        (int,   (50, 5000)),
    "OWW_THRESHOLD":           (float, (0.5, 1.0)),
    "FOLLOWUP_TIMEOUT":        (int,   (1, 60)),
    "KIDS_FOLLOWUP_TIMEOUT":   (int,   (1, 120)),
    "FOLLOWUP_MAX_TURNS":      (int,   (1, 20)),
    "CONTEXT_TIMEOUT_SECS":    (int,   (30, 3600)),
    "NUM_PREDICT":             (int,   (10, 2000)),
    "NUM_PREDICT_SHORT":       (int,   (10, 2000)),
    "NUM_PREDICT_MEDIUM":      (int,   (10, 2000)),
    "NUM_PREDICT_LONG":        (int,   (10, 2000)),
    "NUM_PREDICT_MAX":         (int,   (10, 2000)),
    "TTS_MAX_CHARS":           (int,   (100, 4000)),
    "CHATTERBOX_EXAGGERATION": (float, (0.0, 2.0)),
    "CHATTERBOX_ENABLED":      (bool,  None),
    "KOKORO_ENABLED":          (bool,  None),
    "VOL_MAX":                 (int,   (60, 127)),
    "SPEAKER_VOLUME":          (int,   (60, 127)),
    "LED_IDLE_PEAK":           (int,   (0, 255)),
    "LED_IDLE_FLOOR":          (int,   (0, 255)),
    "LED_IDLE_PERIOD":         (float, (0.5, 30.0)),
    "LED_KIDS_PEAK":           (int,   (0, 255)),
    "LED_KIDS_PERIOD":         (float, (0.5, 30.0)),
    "LED_SLEEP_PEAK":          (int,   (0, 255)),
    "LED_SLEEP_FLOOR":         (int,   (0, 255)),
    "LED_SLEEP_PERIOD":        (float, (0.5, 30.0)),
    "MOUTH_INTENSITY_AWAKE":   (int,   (0, 15)),
    "MOUTH_INTENSITY_SLEEP":   (int,   (0, 15)),
    "OWW_DRAIN_SECS":          (float, (0.05, 1.0)),
}


def _coerce_value(key, val):
    """
    Coerce val to the type registered in _TYPE_COERCE[key].
    Returns (coerced_value, warn_message_or_None).
    Raises ValueError if the value cannot be coerced at all.
    """
    if key not in _TYPE_COERCE:
        return val, None  # string key -- pass through

    typ, bounds = _TYPE_COERCE[key]

    if typ is bool:
        if isinstance(val, bool):
            coerced = val
        elif isinstance(val, int) and val in (0, 1):
            coerced = bool(val)
        elif isinstance(val, str) and val.lower() in (
            "true", "false", "yes", "no", "on", "off", "y", "n"
        ):
            coerced = val.lower() in ("true", "yes", "on", "y")
        else:
            raise ValueError(f"cannot convert {val!r} to bool")
        return coerced, None

    # int or float
    coerced = typ(val)  # raises ValueError/TypeError on bad input

    if bounds is not None:
        lo, hi = bounds
        if coerced < lo:
            return lo, f"{key}={val!r} below minimum {lo}, clamped to {lo}"
        if coerced > hi:
            return hi, f"{key}={val!r} above maximum {hi}, clamped to {hi}"

    return coerced, None


_CONFIG_PATH = "/home/pi/iris_config.json"

try:
    with open(_CONFIG_PATH) as _f:
        _cfg = _json.load(_f)
    _applied = []
    _ignored = []
    for _k, _v in _cfg.items():
        if _k in _OVERRIDABLE:
            try:
                _coerced, _warn = _coerce_value(_k, _v)
                if _warn:
                    print(f"[CFG]  WARN: {_warn}", flush=True)
                globals()[_k] = _coerced
                _applied.append(f"{_k}={_coerced!r}")
            except (ValueError, TypeError) as _ce:
                print(f"[CFG]  WARN: bad value for {_k}={_v!r} ({_ce}) -- keeping default", flush=True)
        else:
            _ignored.append(_k)
    print(f"[CFG]  iris_config.json loaded: {', '.join(_applied) if _applied else 'no overrides'}", flush=True)
    if _ignored:
        print(f"[CFG]  iris_config.json ignored unknown keys: {_ignored}", flush=True)
except FileNotFoundError:
    print(f"[CFG]  iris_config.json not found, using defaults", flush=True)
except _json.JSONDecodeError as _e:
    print(f"[CFG]  iris_config.json parse error: {_e} -- using defaults", flush=True)
except Exception as _e:
    print(f"[CFG]  iris_config.json load failed: {_e} -- using defaults", flush=True)

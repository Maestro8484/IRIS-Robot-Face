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
OLLAMA_MODEL_ADULT = "jarvis"
OLLAMA_MODEL_KIDS  = "jarvis-kids"
WAKE_WORD      = "hey_jarvis"
PIPER_VOICE    = "en_US-ryan-high"

# ── ElevenLabs TTS ────────────────────────────────────────────────────────────
ELEVENLABS_API_KEY  = "sk_752184d377335347d38c185ba56a1bebe9deba4da50ce082"
ELEVENLABS_VOICE_ID = "90eMKEeSf5nhJZMJeeVZ"
ELEVENLABS_MODEL    = "eleven_turbo_v2_5"
ELEVENLABS_ENABLED  = True

# ── Audio ─────────────────────────────────────────────────────────────────────
SAMPLE_RATE    = 16000
CHANNELS       = 1
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

# ── Volume ────────────────────────────────────────────────────────────────────
VOL_CONTROL    = "Headphone"
VOL_MIN        = 60
VOL_MAX        = 127
VOL_STEP       = 10

# ── Follow-up / context ───────────────────────────────────────────────────────
FOLLOWUP_TIMEOUT      = 2
KIDS_FOLLOWUP_TIMEOUT = 15
FOLLOWUP_SHORT_LEN    = 60
FOLLOWUP_MAX_TURNS    = 3
CONTEXT_TIMEOUT_SECS  = 300
NUM_PREDICT           = 350
CONVERSATION_LOG      = "/home/pi/logs/conversations.jsonl"

# ── Camera / Vision ───────────────────────────────────────────────────────────
CAMERA_ENABLED = True
CAMERA_WIDTH   = 1024
CAMERA_HEIGHT  = 768
CAMERA_TIMEOUT = 5000
VISION_MODEL   = "jarvis"

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
OWW_THRESHOLD  = 0.85

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
try:
    with open("/home/pi/iris_config.json") as _f:
        _cfg = _json.load(_f)
    RECORD_SECONDS        = _cfg.get("RECORD_SECONDS",        RECORD_SECONDS)
    SILENCE_SECS          = _cfg.get("SILENCE_SECS",          SILENCE_SECS)
    SILENCE_RMS           = _cfg.get("SILENCE_RMS",           SILENCE_RMS)
    KIDS_RECORD_SECONDS   = _cfg.get("KIDS_RECORD_SECONDS",   KIDS_RECORD_SECONDS)
    KIDS_SILENCE_SECS     = _cfg.get("KIDS_SILENCE_SECS",     KIDS_SILENCE_SECS)
    KIDS_SILENCE_RMS      = _cfg.get("KIDS_SILENCE_RMS",      KIDS_SILENCE_RMS)
    OWW_THRESHOLD         = _cfg.get("OWW_THRESHOLD",         OWW_THRESHOLD)
    FOLLOWUP_TIMEOUT      = _cfg.get("FOLLOWUP_TIMEOUT",      FOLLOWUP_TIMEOUT)
    KIDS_FOLLOWUP_TIMEOUT = _cfg.get("KIDS_FOLLOWUP_TIMEOUT", KIDS_FOLLOWUP_TIMEOUT)
    FOLLOWUP_MAX_TURNS    = _cfg.get("FOLLOWUP_MAX_TURNS",    FOLLOWUP_MAX_TURNS)
    CONTEXT_TIMEOUT_SECS  = _cfg.get("CONTEXT_TIMEOUT_SECS",  CONTEXT_TIMEOUT_SECS)
    NUM_PREDICT           = _cfg.get("NUM_PREDICT",           NUM_PREDICT)
    ELEVENLABS_VOICE_ID   = _cfg.get("ELEVENLABS_VOICE_ID",   ELEVENLABS_VOICE_ID)
    ELEVENLABS_MODEL      = _cfg.get("ELEVENLABS_MODEL",      ELEVENLABS_MODEL)
    ELEVENLABS_ENABLED    = _cfg.get("ELEVENLABS_ENABLED",    ELEVENLABS_ENABLED)
    VOL_MAX               = _cfg.get("VOL_MAX",               VOL_MAX)
    OLLAMA_MODEL_ADULT    = _cfg.get("OLLAMA_MODEL_ADULT",    OLLAMA_MODEL_ADULT)
    OLLAMA_MODEL_KIDS     = _cfg.get("OLLAMA_MODEL_KIDS",     OLLAMA_MODEL_KIDS)
    print("[CFG]  iris_config.json loaded", flush=True)
except Exception as _e:
    print(f"[CFG]  iris_config.json not found or invalid, using defaults: {_e}", flush=True)

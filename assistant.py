#!/usr/bin/env python3
"""
assistant.py - Pi4 IRIS voice assistant
Wake: wyoming-openwakeword hey_jarvis (:10400) OR button press (GPIO17)
STT:  Wyoming Whisper  @ 192.168.1.3:10300
LLM:  Ollama           @ 192.168.1.3:11434
TTS:  Wyoming Piper    @ 192.168.1.3:10200
Audio: wm8960-soundcard (dynamic card detection)
LEDs: 3x APA102 via SPI -- status indicator
Eyes: Teensy 4.0 Wall-E face via /dev/ttyACM0
"""

import io, json, os, re, select, serial, socket, subprocess, sys, threading, time, wave
import numpy as np
import pyaudio
import requests
import spidev
import RPi.GPIO as GPIO
import warnings; warnings.filterwarnings("ignore")

# ── Config ────────────────────────────────────────────────────────────────────
GANDALF        = "192.168.1.3"
WHISPER_PORT   = 10300
PIPER_PORT     = 10200
OLLAMA_PORT    = 11434
OWW_PORT       = 10400
OLLAMA_MODEL_ADULT = "jarvis"
OLLAMA_MODEL_KIDS  = "jarvis-kids"
WAKE_WORD      = "hey_jarvis"
PIPER_VOICE    = "en_US-ryan-high"
# ── ElevenLabs TTS ────────────────────────────────────────────────────────────
ELEVENLABS_API_KEY  = "sk_752184d377335347d38c185ba56a1bebe9deba4da50ce082"
ELEVENLABS_VOICE_ID = "90eMKEeSf5nhJZMJeeVZ"
ELEVENLABS_MODEL    = "eleven_turbo_v2_5"
ELEVENLABS_ENABLED  = True
SAMPLE_RATE    = 16000
CHANNELS       = 1
CHUNK          = 1024
RECORD_SECONDS = 10
SILENCE_SECS   = 1.5
SILENCE_RMS    = 300
# Kids mode overrides -- applied dynamically when _kids_mode is True
KIDS_RECORD_SECONDS = 14
KIDS_SILENCE_SECS   = 3.5
KIDS_SILENCE_RMS    = 150
BUTTON_PIN     = 17
NUM_LEDS       = 3
VOL_CONTROL    = "Headphone"
VOL_MIN        = 60
VOL_MAX        = 127
VOL_STEP       = 10
FOLLOWUP_TIMEOUT   = 2
KIDS_FOLLOWUP_TIMEOUT = 15
FOLLOWUP_SHORT_LEN = 60
FOLLOWUP_MAX_TURNS = 3
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
GANDALF_MAC    = "A4:BB:6D:CA:83:20"
GANDALF_WOL_IP = "192.168.1.3"
GANDALF_WOL_PORT = 7
WOL_BOOT_TIMEOUT = 120
WOL_POLL_INTERVAL = 5
TEENSY_PORT    = "/dev/ttyACM0"
TEENSY_BAUD    = 115200

OWW_THRESHOLD  = 0.85
CONTEXT_TIMEOUT_SECS = 300
NUM_PREDICT = 350
CONVERSATION_LOG = "/home/pi/logs/conversations.jsonl"

# ── iris_config.json loader (web UI overrides) ────────────────────────────────
try:
    import json as _json
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
# ─────────────────────────────────────────────────────────────────────────────

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
_EMOTION_TAG_RE = re.compile(r'^\[EMOTION:([A-Z]+)\]\s*', re.IGNORECASE)

# ── Runtime state ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = ""
conversation_history = []
_kids_mode = False
_last_interaction = [0.0]
_eyes_sleeping = False
_person_context = {"name": None, "desc": ""}  # set by background recognition thread
_last_recognition_time = [0.0]


def get_model() -> str:
    return OLLAMA_MODEL_KIDS if _kids_mode else OLLAMA_MODEL_ADULT


# ── Conversation logger ───────────────────────────────────────────────────────

def flush_conversation_log(reason: str = "timeout"):
    if not conversation_history:
        return
    import datetime
    os.makedirs(os.path.dirname(CONVERSATION_LOG), exist_ok=True)
    record = {
        "ts":       datetime.datetime.now().isoformat(timespec="seconds"),
        "reason":   reason,
        "mode":     "kids" if _kids_mode else "adult",
        "model":    get_model(),
        "turns":    sum(1 for m in conversation_history if m["role"] == "user"),
        "messages": list(conversation_history),
    }
    try:
        with open(CONVERSATION_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"[LOG]  Session logged ({record['turns']} turns, reason={reason})", flush=True)
    except Exception as e:
        print(f"[ERR]  Failed to write conversation log: {e}", flush=True)


# ── Context timeout watchdog ──────────────────────────────────────────────────

def _context_watchdog():
    if CONTEXT_TIMEOUT_SECS <= 0:
        return
    while True:
        time.sleep(30)
        if _last_interaction[0] == 0.0:
            continue
        elapsed = time.time() - _last_interaction[0]
        if elapsed >= CONTEXT_TIMEOUT_SECS and conversation_history:
            flush_conversation_log(reason="timeout")
            conversation_history.clear()
            _person_context["name"] = None; _person_context["desc"] = ""
            _last_recognition_time[0] = 0.0
            _last_interaction[0] = 0.0
            print(f"[CTX]  Context cleared after {CONTEXT_TIMEOUT_SECS}s of silence", flush=True)


# ── WoL + GandalfAI readiness ─────────────────────────────────────────────────

def send_wol(mac: str, ip: str = "255.255.255.255", port: int = 9):
    mac_bytes = bytes.fromhex(mac.replace(":", "").replace("-", ""))
    magic = b"\xff" * 6 + mac_bytes * 16
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(magic, (ip, port))
    print(f"[WOL]  Magic packet sent to {mac} via {ip}:{port}", flush=True)


def gandalf_is_up() -> bool:
    try:
        with socket.create_connection((GANDALF, OLLAMA_PORT), timeout=3):
            return True
    except (OSError, ConnectionRefusedError):
        return False


def ensure_gandalf_up(leds) -> bool:
    if gandalf_is_up():
        return True
    print("[WOL]  GandalfAI is offline -- sending Wake-on-LAN...", flush=True)
    send_wol(GANDALF_MAC, GANDALF_WOL_IP, GANDALF_WOL_PORT)

    def waking_anim(stop_evt):
        while not stop_evt.is_set():
            for v in list(range(0, 70, 4)) + list(range(70, 0, -4)):
                if stop_evt.is_set(): return
                leds._write([(v, v//3, 0)] * leds.n)
                time.sleep(0.05)

    stop_evt = threading.Event()
    anim_t = threading.Thread(target=waking_anim, args=(stop_evt,), daemon=True)
    anim_t.start()
    deadline = time.time() + WOL_BOOT_TIMEOUT
    while time.time() < deadline:
        time.sleep(WOL_POLL_INTERVAL)
        if gandalf_is_up():
            stop_evt.set(); anim_t.join(timeout=2)
            print("[WOL]  GandalfAI is up.", flush=True)
            return True
        print(f"[WOL]  Waiting for GandalfAI... ({int(deadline-time.time())}s remaining)", flush=True)
    stop_evt.set(); anim_t.join(timeout=2)
    print("[ERR]  GandalfAI did not come up in time.", flush=True)
    return False


# ── APA102 LED driver ─────────────────────────────────────────────────────────

class APA102:
    def __init__(self, n=3):
        self.n = n
        self.spi = spidev.SpiDev()
        self.spi.open(0, 1)
        self.spi.max_speed_hz = 1000000
        self._pixels = [(0, 0, 0)] * n
        self._lock = threading.Lock()
        self._anim_thread = None
        self._stop_anim = threading.Event()

    def _write(self, pixels):
        buf = [0x00] * 4
        for r, g, b in pixels:
            buf += [0xFF, b, g, r]
        buf += [0xFF] * 4
        with self._lock:
            self.spi.xfer2(buf)

    def set_all(self, r, g, b): self._write([(r, g, b)] * self.n)

    def set_pixel(self, i, r, g, b):
        px = list(self._pixels); px[i] = (r, g, b); self._pixels = px; self._write(px)

    def off(self): self._write([(0, 0, 0)] * self.n)

    def stop_anim(self):
        self._stop_anim.set()
        if self._anim_thread and self._anim_thread.is_alive():
            self._anim_thread.join(timeout=2)
        self._stop_anim.clear()

    def _run_anim(self, fn):
        self.stop_anim()
        self._anim_thread = threading.Thread(target=fn, daemon=True)
        self._anim_thread.start()

    def show_idle(self):
        def anim():
            import math
            steps = 80; period = 5.0; floor = 3; peak = 65
            while not self._stop_anim.is_set():
                for i in range(steps):
                    if self._stop_anim.is_set(): return
                    # full sine cycle 0->1->0, remapped to floor->peak->floor
                    t = i / steps
                    s = (math.sin(2 * math.pi * t - math.pi / 2) + 1) / 2
                    v = int(floor + (peak - floor) * (s ** 1.8))
                    self._write([(0, v, v)] * self.n); time.sleep(period / steps)
        self._run_anim(anim)

    def show_idle_kids(self):
        def anim():
            import math
            steps = 80; period = 4.0; floor = 3; peak = 62
            while not self._stop_anim.is_set():
                for i in range(steps):
                    if self._stop_anim.is_set(): return
                    t = i / steps
                    s = (math.sin(2 * math.pi * t - math.pi / 2) + 1) / 2
                    v = int(floor + (peak - floor) * (s ** 1.8))
                    self._write([(v, v, 0)] * self.n); time.sleep(period / steps)
        self._run_anim(anim)

    def show_kids_mode_on(self):
        def anim():
            for _ in range(3):
                if self._stop_anim.is_set(): return
                self._write([(100, 100, 0)] * self.n); time.sleep(0.15)
                self._write([(0, 0, 0)] * self.n); time.sleep(0.1)
        self._run_anim(anim)

    def show_kids_mode_off(self):
        def anim():
            for _ in range(3):
                if self._stop_anim.is_set(): return
                self._write([(0, 100, 100)] * self.n); time.sleep(0.15)
                self._write([(0, 0, 0)] * self.n); time.sleep(0.1)
        self._run_anim(anim)

    def show_wake(self): self.stop_anim(); self.set_all(80, 80, 80)
    def show_recording(self): self.stop_anim(); self.set_all(120, 0, 0)

    def show_thinking(self):
        def anim():
            i = 0
            while not self._stop_anim.is_set():
                px = [(0, 0, 0)] * self.n; px[i % self.n] = (0, 0, 100)
                self._write(px); time.sleep(0.12); i += 1
        self._run_anim(anim)

    def show_speaking(self): self.stop_anim(); self.set_all(0, 80, 0)

    def show_error(self):
        def anim():
            for _ in range(6):
                if self._stop_anim.is_set(): return
                self._write([(120, 0, 0)] * self.n); time.sleep(0.1)
                self._write([(0, 0, 0)] * self.n); time.sleep(0.1)
        self._run_anim(anim)

    def show_followup(self):
        def anim():
            while not self._stop_anim.is_set():
                for v in list(range(0, 60, 3)) + list(range(60, 0, -3)):
                    if self._stop_anim.is_set(): return
                    self._write([(v, 0, v)] * self.n); time.sleep(0.04)
        self._run_anim(anim)

    def show_ptt(self): self.stop_anim(); self.set_all(80, 60, 0)

    # Emotion-linked LED breathing colors
    _EMOTION_LED = {
        'NEUTRAL':   (0,   80,  80,  4.0, False),  # soft cyan, 4s
        'HAPPY':     (100, 80,  0,   3.0, False),  # warm yellow, 3s
        'CURIOUS':   (0,   100, 100, 3.5, False),  # bright cyan, 3.5s
        'ANGRY':     (100, 0,   0,   2.0, False),  # red, 2s fast
        'SLEEPY':    (40,  0,   60,  6.0, False),  # dim purple, 6s slow
        'SURPRISED': (120, 120, 120, 0.3, True),   # white flash -> cyan
        'SAD':       (0,   0,   60,  6.0, False),  # dim blue, 6s
        'CONFUSED':  (80,  0,   80,  2.5, False),  # pulsing magenta, 2.5s
    }

    def show_emotion(self, emotion: str):
        cfg = self._EMOTION_LED.get(emotion.upper(), self._EMOTION_LED['NEUTRAL'])
        r, g, b, period, flash = cfg
        import time as _t
        if flash:
            def anim():
                for _ in range(4):
                    if self._stop_anim.is_set(): return
                    self._write([(120, 120, 120)] * self.n); _t.sleep(0.1)
                    if self._stop_anim.is_set(): return
                    self._write([(0, 0, 0)] * self.n); _t.sleep(0.08)
                steps = list(range(3, 81, 3))
                while not self._stop_anim.is_set():
                    for v in steps:
                        if self._stop_anim.is_set(): return
                        self._write([(0, v, v)] * self.n); _t.sleep(0.04)
                    for v in reversed(steps):
                        if self._stop_anim.is_set(): return
                        self._write([(0, v, v)] * self.n); _t.sleep(0.04)
            self._run_anim(anim)
        else:
            half = period / 2.0
            steps = max(10, int(half / 0.04))
            def anim(r=r, g=g, b=b, steps=steps, half=half):
                import time as _t2
                while not self._stop_anim.is_set():
                    for i in range(steps):
                        if self._stop_anim.is_set(): return
                        v = i / steps
                        self._write([(int(r*v), int(g*v), int(b*v))] * self.n)
                        _t2.sleep(half / steps)
                    for i in range(steps):
                        if self._stop_anim.is_set(): return
                        v = max(0.07, 1.0 - i / steps)
                        self._write([(int(r*v), int(g*v), int(b*v))] * self.n)
                        _t2.sleep(half / steps)
            self._run_anim(anim)

    def close(self):
        self.stop_anim(); self.off(); self.spi.close()


# ── GPIO button ───────────────────────────────────────────────────────────────

def setup_button():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN)

def button_pressed():
    return GPIO.input(BUTTON_PIN) == 0


# ── Teensy Serial Bridge ──────────────────────────────────────────────────────

class TeensyBridge:
    def __init__(self, port: str, baud: int):
        self._port = port; self._baud = baud
        self._ser = None; self._lock = threading.Lock(); self._active = True
        threading.Thread(target=self._reader, daemon=True).start()

    def _open(self):
        try:
            s = serial.Serial(self._port, self._baud, timeout=1)
            s.reset_input_buffer()
            print(f"[EYES] Teensy connected on {self._port}", flush=True)
            return s
        except (serial.SerialException, OSError):
            return None

    def _reader(self):
        while self._active:
            with self._lock:
                if self._ser is None or not self._ser.is_open:
                    self._ser = self._open()
            if self._ser is None:
                time.sleep(5); continue
            try:
                line = self._ser.readline().decode(errors="ignore").strip()
                if line: print(f"[EYES] << {line}", flush=True)
            except (serial.SerialException, OSError):
                print("[EYES] Serial disconnected -- will retry", flush=True)
                with self._lock:
                    try: self._ser.close()
                    except Exception: pass
                    self._ser = None
                time.sleep(5)

    def send_emotion(self, emotion: str):
        with self._lock:
            if self._ser is None or not self._ser.is_open: return
            try:
                self._ser.write(f"EMOTION:{emotion}\n".encode())
                self._ser.flush()
                print(f"[EYES] >> EMOTION:{emotion}", flush=True)
            except (serial.SerialException, OSError) as e:
                print(f"[EYES] Send failed: {e}", flush=True)
                try: self._ser.close()
                except Exception: pass
                self._ser = None

    def send_command(self, cmd: str):
        """Send a raw command string (no EMOTION: prefix) to the Teensy."""
        with self._lock:
            if self._ser is None or not self._ser.is_open: return
            try:
                self._ser.write(f"{cmd}\n".encode())
                self._ser.flush()
                print(f"[EYES] >> {cmd}", flush=True)
            except (serial.SerialException, OSError) as e:
                print(f"[EYES] Send failed: {e}", flush=True)
                try: self._ser.close()
                except Exception: pass
                self._ser = None

    def close(self):
        self._active = False
        with self._lock:
            if self._ser:
                try: self._ser.close()
                except Exception: pass


# ── Emotion extraction ────────────────────────────────────────────────────────

def extract_emotion_from_reply(raw: str) -> tuple:
    """
    Parse [EMOTION:X] tag from start of LLM reply.
    Returns (emotion, cleaned_reply). Falls back to NEUTRAL if tag missing/bad.
    """
    m = _EMOTION_TAG_RE.match(raw)
    if m:
        emotion = m.group(1).upper()
        reply = raw[m.end():].strip()
        if emotion not in VALID_EMOTIONS:
            emotion = "NEUTRAL"
        return emotion, reply
    return "NEUTRAL", raw.strip()


# ── Emotion + LED sync helper ────────────────────────────────────────────────
def emit_emotion(teensy, leds, emotion: str):
    """Send emotion to Teensy eyes AND sync LED color in one call."""
    teensy.send_emotion(emotion)
    teensy.send_command(f"MOUTH:{MOUTH_MAP.get(emotion, 0)}")
    leds.show_emotion(emotion)


# ── Wyoming helpers ───────────────────────────────────────────────────────────

def wy_send(sock, etype, data, payload=b""):
    hdr = {"type": etype, "data": data}
    if payload: hdr["payload_length"] = len(payload)
    sock.sendall((json.dumps(hdr) + "\n").encode())
    if payload: sock.sendall(payload)


def read_line(sock, buf):
    while b"\n" not in buf:
        buf += sock.recv(4096)
    nl = buf.index(b"\n")
    return buf[:nl], buf[nl+1:]


# ── Wake word ─────────────────────────────────────────────────────────────────

def wait_for_wakeword_or_button(mic, oww_sock):
    detected = threading.Event()
    trigger = [None]

    def reader():
        buf = b""
        while not detected.is_set():
            try:
                ready, _, _ = select.select([oww_sock], [], [], 0.05)
                if not ready: continue
                chunk = oww_sock.recv(4096)
                if not chunk: break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    try:
                        hdr = json.loads(line.decode())
                        if hdr.get("type") == "detection":
                            score = hdr.get("data", {}).get("score", 1.0)
                            if score < OWW_THRESHOLD:
                                print(f"[OWW]  Low-confidence ignored (score={score:.2f})", flush=True)
                                continue
                            trigger[0] = "wake"; detected.set(); return
                    except json.JSONDecodeError: pass
            except Exception: break

    wy_send(oww_sock, "detect", {"names": [WAKE_WORD]})
    wy_send(oww_sock, "audio-start", {"rate": SAMPLE_RATE, "width": 2, "channels": CHANNELS})
    t = threading.Thread(target=reader, daemon=True); t.start()
    while not detected.is_set():
        audio = mic.read(CHUNK, exception_on_overflow=False)
        wy_send(oww_sock, "audio-chunk", {"rate": SAMPLE_RATE, "width": 2, "channels": CHANNELS}, audio)
        if button_pressed():
            trigger[0] = "button"; detected.set(); time.sleep(0.05)
    t.join(timeout=1)
    return trigger[0]


# ── STT ───────────────────────────────────────────────────────────────────────

def transcribe(audio_bytes):
    with socket.create_connection((GANDALF, WHISPER_PORT), timeout=30) as s:
        wy_send(s, "transcribe", {"name": "", "language": "en"})
        wy_send(s, "audio-start", {"rate": SAMPLE_RATE, "width": 2, "channels": CHANNELS})
        for i in range(0, len(audio_bytes), 4096):
            wy_send(s, "audio-chunk", {"rate": SAMPLE_RATE, "width": 2, "channels": CHANNELS}, audio_bytes[i:i+4096])
        wy_send(s, "audio-stop", {})
        buf = b""
        while True:
            chunk = s.recv(4096)
            if not chunk: break
            buf += chunk
            lines = buf.split(b"\n"); buf = lines[-1]
            for line in lines[:-1]:
                line = line.strip()
                if not line: continue
                try:
                    obj = json.loads(line.decode())
                    if obj.get("type") == "transcript":
                        plen = obj.get("data_length", 0)
                        while len(buf) < plen: buf += s.recv(4096)
                        try: return json.loads(buf[:plen].decode()).get("text", "").strip()
                        except Exception: return ""
                except json.JSONDecodeError: pass
    return ""


# ── LLM output cleaner ────────────────────────────────────────────────────────

def clean_llm_reply(text: str) -> str:
    """Strip markdown artifacts. Does NOT strip emotion tag -- that's done before this."""
    text = re.sub(r'[*_#`]', '', text)
    text = re.sub(r'^[-=]{3,}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n+', ' ', text)
    openers = [
        r"^okay[,!.]?\s+here[''\u2019s]*\s+(a|is|one)[^.]*[.!]?\s*",
        r"^here[''\u2019s]*\s+(a|is|one)[^.]*[.!]?\s*",
        r"^sure[,!.]?\s*",
        r"^of course[,!.]?\s*",
        r"^alright[,!.]?\s*",
    ]
    for pat in openers:
        text = re.sub(pat, '', text, flags=re.IGNORECASE)
    return text.strip()


# ── Local command handlers ────────────────────────────────────────────────────

def handle_kids_mode_command(text: str):
    global _kids_mode
    t = text.lower().strip().rstrip(".!?")
    on_triggers  = ("kids mode on", "enable kids mode", "turn on kids mode", "switch to kids mode",
                    "kids mode please", "activate kids mode", "children's mode on", "kid mode on")
    off_triggers = ("kids mode off", "disable kids mode", "turn off kids mode", "switch to adult mode",
                    "adult mode", "deactivate kids mode", "kid mode off", "normal mode")
    if any(tr in t for tr in on_triggers):
        _kids_mode = True
        flush_conversation_log(reason="mode_switch_kids_on"); conversation_history.clear(); _person_context["name"] = None; _person_context["desc"] = ""; _last_recognition_time[0] = 0.0
        print(f"[MODE] Kids mode ON -- model: {OLLAMA_MODEL_KIDS}", flush=True)
        return "Kids mode activated.", True
    if any(tr in t for tr in off_triggers):
        _kids_mode = False
        flush_conversation_log(reason="mode_switch_kids_off"); conversation_history.clear(); _person_context["name"] = None; _person_context["desc"] = ""; _last_recognition_time[0] = 0.0
        print(f"[MODE] Kids mode OFF -- model: {OLLAMA_MODEL_ADULT}", flush=True)
        return "Kids mode deactivated.", False
    return None, None


def handle_time_command(text: str):
    t = text.lower().strip().rstrip(".!?")
    time_triggers = ("what time", "what's the time", "whats the time", "current time",
                     "tell me the time", "time is it", "what hour")
    date_triggers = ("what day", "what date", "what's the date", "whats the date",
                     "today's date", "todays date", "what month", "what year", "day is it", "date is it")
    is_time = any(tr in t for tr in time_triggers)
    is_date = any(tr in t for tr in date_triggers)
    if not (is_time or is_date): return None
    now = time.localtime()
    hour = now.tm_hour; minute = now.tm_min
    period = "AM" if hour < 12 else "PM"
    hour12 = hour % 12 or 12
    if minute == 0: time_str = f"{hour12} {period}"
    elif minute < 10: time_str = f"{hour12} oh {minute} {period}"
    else: time_str = f"{hour12} {minute} {period}"
    day_name   = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"][now.tm_wday]
    month_name = ["January","February","March","April","May","June","July",
                  "August","September","October","November","December"][now.tm_mon - 1]
    if is_time and is_date: return f"It is {time_str} on {day_name}, {month_name} {now.tm_mday}."
    elif is_time: return f"It is {time_str}."
    else: return f"Today is {day_name}, {month_name} {now.tm_mday}, {now.tm_year}."


# ── Weather ───────────────────────────────────────────────────────────────────

WEATHER_TRIGGERS = (
    "weather", "how's it outside", "hows it outside", "temperature outside",
    "what's it like outside", "whats it like outside", "is it cold", "is it hot",
    "is it raining", "is it snowing", "should i bring a jacket", "do i need a coat",
    "how cold is it", "how warm is it", "how hot is it", "what's the forecast",
    "whats the forecast", "forecast today", "will it rain", "will it snow",
)

def fetch_weather() -> str:
    """Fetch current conditions from wttr.in for Ogden UT. Returns spoken sentence."""
    try:
        r = requests.get("https://wttr.in/Ogden,UT?format=j1", timeout=6)
        r.raise_for_status()
        d = r.json()
        c = d["current_condition"][0]
        temp_f   = c["temp_F"]
        feels_f  = c["FeelsLikeF"]
        desc     = c["weatherDesc"][0]["value"]
        wind_mph = c["windspeedMiles"]
        try:
            precip_chance = max(int(h.get("chanceofrain", 0)) for h in d["weather"][0]["hourly"])
        except Exception:
            precip_chance = 0
        reply = f"It is {temp_f} degrees in Ogden, feeling like {feels_f}. Conditions are {desc.lower()}."
        if int(wind_mph) >= 10:
            reply += f" Wind at {wind_mph} miles per hour."
        if precip_chance >= 40:
            reply += f" There is a {precip_chance} percent chance of rain today."
        return reply
    except Exception as e:
        print(f"[WX]   Weather fetch failed: {e}", flush=True)
        return "I could not get the weather right now."

def handle_weather_command(text: str):
    t = text.lower().strip().rstrip(".!?")
    if any(tr in t for tr in WEATHER_TRIGGERS):
        print("[WX]   Weather trigger detected", flush=True)
        return fetch_weather()
    return None


# ── Daily briefing ────────────────────────────────────────────────────────────

BRIEFING_TRIGGERS = (
    "good morning", "daily briefing", "morning briefing",
    "what's today look like", "whats today look like",
    "what do i have today", "morning update", "start my day",
    "what's going on today", "whats going on today",
)

def handle_daily_briefing(text: str):
    t = text.lower().strip().rstrip(".!?")
    if not any(tr in t for tr in BRIEFING_TRIGGERS):
        return None
    print("[BRIEF] Daily briefing triggered", flush=True)
    import datetime
    now = datetime.datetime.now()
    hour = now.hour; minute = now.minute
    period = "AM" if hour < 12 else "PM"
    hour12 = hour % 12 or 12
    if minute == 0:    time_str = f"{hour12} {period}"
    elif minute < 10:  time_str = f"{hour12} oh {minute} {period}"
    else:              time_str = f"{hour12} {minute} {period}"
    wx = fetch_weather()
    return f"Good morning. It is {time_str} on {now.strftime('%A, %B')} {now.day}. {wx}"


# ── Person recognition (background, non-blocking) ────────────────────────────

PERSON_RECOG_PROMPT = (
    "Look at this image. Is there a person visible? "
    "If yes, which of these people does it look like: "
    "Leo (boy, age 9), Mae (girl, age 5), Megan (adult woman), or Maestro (adult man)? "
    "If you cannot tell or nobody is visible, say unknown. "
    "Reply with ONLY one word: Leo, Mae, Megan, Maestro, or unknown."
)

PERSON_SYSTEM_LINES = {
    "Leo":     "The person speaking is Leo, a 9-year-old boy. Use his name naturally. Match his energy. Explain clearly but don't talk down to him.",
    "Mae":     "The person speaking is Mae, a 5-year-old girl. Use very simple words. Be warm and encouraging. Use her name. Keep answers to one or two sentences.",
    "Megan":   "The person speaking is Megan, an adult woman. Be direct and efficient. Use her name sparingly, only when natural.",
    "Maestro": "The person speaking is Maestro, the owner and systems administrator. Be direct, technical when relevant, skip pleasantries. Dry humor is welcome.",
}

def _run_person_recognition():
    """Capture image and identify who is present. Stores result in _person_context."""
    global _person_context
    if not CAMERA_ENABLED:
        return
    if conversation_history and (time.time() - _last_recognition_time[0]) <= 300:
        return
    img = capture_image()
    if img is None:
        _person_context = {"name": None, "desc": ""}
        return
    try:
        import base64
        img_b64 = base64.b64encode(img).decode()
        r = requests.post(
            f"http://{GANDALF}:{OLLAMA_PORT}/api/generate",
            json={"model": VISION_MODEL, "prompt": PERSON_RECOG_PROMPT,
                  "images": [img_b64], "stream": False},
            timeout=30,
        )
        r.raise_for_status()
        raw = r.json().get("response", "").strip()
        name = re.sub(r"[^a-zA-Z]", "", raw).capitalize()
        if name not in {"Leo", "Mae", "Megan", "Maestro"}:
            name = None
        _person_context = {"name": name, "desc": raw}
        _last_recognition_time[0] = time.time()
        print(f"[PERS] Recognized: {name or 'unknown'} (raw='{raw}')", flush=True)
    except Exception as e:
        print(f"[PERS] Recognition failed: {e}", flush=True)
        _person_context = {"name": None, "desc": ""}


# ── LLM ───────────────────────────────────────────────────────────────────────

def ask_ollama(text):
    """
    Query Ollama. Returns (reply, emotion) tuple.
    Strips [EMOTION:X] tag from reply before returning -- tag never reaches TTS.
    Falls back to NEUTRAL if tag absent (e.g. kids model).
    """
    _last_interaction[0] = time.time()
    conversation_history.append({"role": "user", "content": text})
    import datetime
    now = datetime.datetime.now()
    date_inject = {
        "role": "system",
        "content": f"Current date and time: {now.strftime('%A, %B %d %Y, %I:%M %p')} (Mountain Time)."
    }
    # Inject person-recognition context if available
    person_inject = None
    _pname = _person_context.get("name")
    if _pname and _pname in PERSON_SYSTEM_LINES:
        person_inject = {"role": "system", "content": PERSON_SYSTEM_LINES[_pname]}
    if person_inject:
        messages_with_date = [date_inject, person_inject] + conversation_history
    else:
        messages_with_date = [date_inject] + conversation_history
    r = requests.post(
        f"http://{GANDALF}:{OLLAMA_PORT}/api/chat",
        json={"model": get_model(), "messages": messages_with_date, "stream": False, "options": {"num_predict": NUM_PREDICT}},
        timeout=30
    )
    r.raise_for_status()
    raw = r.json()["message"]["content"]

    # Extract and strip emotion tag BEFORE cleaning
    emotion, stripped = extract_emotion_from_reply(raw)
    reply = clean_llm_reply(stripped)

    print(f"[EYES] Emotion from LLM: {emotion}", flush=True)

    conversation_history.append({"role": "assistant", "content": reply})
    if len(conversation_history) > 20:
        conversation_history.pop(0); conversation_history.pop(0)
    return reply, emotion


# ── TTS ───────────────────────────────────────────────────────────────────────

def _synthesize_elevenlabs(text: str) -> bytes:
    """ElevenLabs TTS -> raw s16le PCM at 22050 Hz. Free tier returns MP3; decode with miniaudio."""
    import miniaudio
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": ELEVENLABS_MODEL,
        "voice_settings": {"stability": 0.45, "similarity_boost": 0.85, "style": 0.15, "use_speaker_boost": True},
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    mp3 = resp.content
    if len(mp3) < 100:
        raise RuntimeError(f"[EL] Response too short: {len(mp3)} bytes")
    decoded = miniaudio.decode(mp3, output_format=miniaudio.SampleFormat.SIGNED16, nchannels=1, sample_rate=22050)
    raw = np.frombuffer(bytes(decoded.samples), dtype=np.int16).astype(np.float32)
    # ElevenLabs is mastered ~16 dB quieter than Piper (measured RMS ~2 000 vs Piper ~15 000).
    # Normalise to a target RMS; allow modest peak clipping (broadcast-style speech
    # compression) so perceived loudness matches the Piper fallback voice.
    # Raise _EL_TARGET_RMS toward 8000 if still quieter than Piper; lower if too hot.
    _EL_TARGET_RMS = 5500.0
    _rms = float(np.sqrt(np.mean(raw ** 2))) if raw.size else 0.0
    if _rms > 10.0:
        _peak_safe = 32700.0 / float(np.max(np.abs(raw)))   # gain that avoids ALL clipping
        _norm_gain = min(_EL_TARGET_RMS / _rms, _peak_safe * 2.5)  # allow up to 2.5x clip headroom
        raw = np.clip(raw * _norm_gain, -32768.0, 32767.0)
        print(f"[EL]   Norm gain={_norm_gain:.2f}x  RMS {_rms:.0f}→{np.sqrt(np.mean(raw**2)):.0f}", flush=True)
    samples = raw.astype(np.int16)
    # Pad 80ms silence before and after to absorb PAM8403 pop/thump transient
    silence = bytes(int(22050 * 0.08) * 2 * 2)  # 80ms @ 22050Hz, 16bit, stereo after expansion
    silence_mono = bytes(int(22050 * 0.08) * 2)  # mono before stereo expansion
    samples_padded = np.concatenate([
        np.zeros(int(22050 * 0.08), dtype=np.int16),
        samples,
        np.zeros(int(22050 * 0.08), dtype=np.int16)
    ])
    pcm = samples_padded.tobytes()
    print(f"[EL]   OK {len(mp3)}b MP3 -> {len(pcm)}b PCM ({decoded.duration:.1f}s)", flush=True)
    return pcm


def _synthesize_piper(text: str) -> bytes:
    """Piper TTS fallback via Wyoming protocol on GandalfAI."""
    with socket.create_connection((GANDALF, PIPER_PORT), timeout=60) as s:
        wy_send(s, "synthesize", {"text": text, "voice": {"name": PIPER_VOICE}})
        s.settimeout(60)
        audio_chunks = []; buf = b""
        while True:
            line, buf = read_line(s, buf)
            hdr = json.loads(line.decode())
            etype = hdr.get("type", "")
            dlen = hdr.get("data_length", 0); plen = hdr.get("payload_length", 0)
            while len(buf) < dlen + plen: buf += s.recv(8192)
            pcm = buf[dlen:dlen+plen]; buf = buf[dlen+plen:]
            if etype == "audio-chunk" and pcm: audio_chunks.append(pcm)
            elif etype == "audio-stop": return b"".join(audio_chunks)
            elif etype == "error": raise RuntimeError(f"Piper error: {hdr}")



def spoken_numbers(text: str) -> str:
    """Convert numeric tokens to spoken English before TTS (no inflect dependency)."""
    _ONES = ["zero","one","two","three","four","five","six","seven","eight","nine",
             "ten","eleven","twelve","thirteen","fourteen","fifteen","sixteen",
             "seventeen","eighteen","nineteen"]
    _TENS = ["","","twenty","thirty","forty","fifty","sixty","seventy","eighty","ninety"]
    def _int_to_words(n: int) -> str:
        if n < 0:
            return "negative " + _int_to_words(-n)
        if n < 20:
            return _ONES[n]
        if n < 100:
            rest = (" " + _ONES[n % 10]) if n % 10 else ""
            return _TENS[n // 10] + rest
        if n < 1000:
            rest = (" " + _int_to_words(n % 100)) if n % 100 else ""
            return _ONES[n // 100] + " hundred" + rest
        return str(n)
    # Temperature: 50F / 50°F / 50ºF
    text = re.sub(r'(\d+)\s*[°º]?F\b', lambda m: _int_to_words(int(m.group(1))) + " degrees", text)
    # Speed: 2mph / 2 mph
    text = re.sub(r'(\d+)\s*mph\b', lambda m: _int_to_words(int(m.group(1))) + " miles per hour", text, flags=re.IGNORECASE)
    # Percent: 46%
    text = re.sub(r'(\d+)\s*%', lambda m: _int_to_words(int(m.group(1))) + " percent", text)
    # Bare integers <= 999 not already converted
    text = re.sub(r'\b(\d+)\b', lambda m: _int_to_words(int(m.group(1))) if int(m.group(1)) <= 999 else m.group(0), text)
    return text

def synthesize(text: str) -> bytes:
    """ElevenLabs first, Piper fallback on any failure."""
    text = spoken_numbers(text)
    if ELEVENLABS_ENABLED:
        try:
            return _synthesize_elevenlabs(text)
        except Exception as e:
            print(f"[EL]   Failed: {e} -- falling back to Piper", flush=True)
    return _synthesize_piper(text)


# ── Playback ──────────────────────────────────────────────────────────────────

_stop_playback = threading.Event()

# RMS threshold for mid-playback voice interrupt.
# User speaking above this level while IRIS talks → immediate stop.
# Tune upward if ambient noise causes false triggers; lower if voice not detected.
# NOTE: raised from 1200 → 4000 because the external amp (5V 3W, 3.5mm headphone path)
# at -5dB DAC now bleeds acoustically into the ReSpeaker mics at ~1200-4500 RMS.
# A human voice on top of that bleed reaches 5000-8000, so 4000 still catches interrupts
# while ignoring IRIS's own speaker output.
INTERRUPT_RMS_THRESHOLD = 4000

# Stop phrases checked via lightweight STT during playback
STOP_PHRASES = {
    "stop", "cancel", "nevermind", "never mind", "quiet", "shut up",
    "be quiet", "stop talking", "that's enough", "enough", "hey jarvis",
    "jarvis stop", "ok stop", "please stop",
}

# Polite filler responses that end the follow-up loop without LLM processing
FOLLOWUP_DISMISSALS = {
    "thank you", "thanks", "thank you very much", "thanks very much",
    "thank you so much", "thanks so much",
    "ok", "okay", "ok thanks", "okay thanks", "ok thank you", "okay thank you",
    "great", "great thanks", "great thank you", "sounds great",
    "got it", "got it thanks", "got it thank you",
    "alright", "all right", "alright thanks", "sounds good", "perfect",
    "no", "no thanks", "no thank you", "nope", "that's all", "that is all",
    "that's it", "that is it", "i'm good", "im good", "i'm all good",
    "cool", "cool thanks", "awesome", "wonderful", "excellent",
}

def _playback_interrupt_listener(pa_ref, stop_event, interrupted_event):
    """
    Background thread: opens a separate mic stream during playback.
    Triggers interrupted_event if:
      - Button pressed
      - Voice energy significantly exceeds the measured speaker-bleed baseline

    Uses an adaptive threshold: the first ~0.75 s of playback are used to
    measure the acoustic bleed from the speaker into the mics at the current
    potentiometer/amp level.  The interrupt threshold is then set to
    max(INTERRUPT_RMS_THRESHOLD, bleed_baseline * _VOICE_MULTIPLIER).
    This means the pot can be at any position and the threshold self-adjusts --
    a human voice must be _VOICE_MULTIPLIER times louder than the bleed to fire.
    """
    # How many chunks to sample for baseline (~0.5 s at 16kHz/1024)
    _BASELINE_CHUNKS = int(SAMPLE_RATE / CHUNK * 0.5)
    # Voice must exceed baseline by this factor to count as an interrupt
    _VOICE_MULTIPLIER = 4.0

    try:
        mon = pa_ref.open(rate=SAMPLE_RATE, channels=CHANNELS,
                          format=pyaudio.paInt16, input=True,
                          frames_per_buffer=CHUNK)

        # ── Phase 1: measure speaker-bleed baseline ───────────────────────────
        baseline_vals = []
        for _ in range(_BASELINE_CHUNKS):
            if stop_event.is_set():
                break
            try:
                data = mon.read(CHUNK, exception_on_overflow=False)
                rms = np.sqrt(np.mean(np.frombuffer(data, dtype=np.int16).astype(np.float32) ** 2))
                baseline_vals.append(rms)
            except Exception:
                break

        if baseline_vals:
            bleed_rms = float(np.percentile(baseline_vals, 90))
            effective_threshold = max(float(INTERRUPT_RMS_THRESHOLD), min(bleed_rms + 2500.0, 8000.0))
        else:
            bleed_rms = 0.0
            effective_threshold = float(INTERRUPT_RMS_THRESHOLD)
        print(f"[INT]  Bleed baseline RMS={bleed_rms:.0f}  eff_threshold={effective_threshold:.0f}", flush=True)
        # ─────────────────────────────────────────────────────────────────────

        # ── Phase 2: monitor for human voice above adaptive threshold ─────────
        speech_frames = []
        speech_detected = False
        while not stop_event.is_set():
            try:
                data = mon.read(CHUNK, exception_on_overflow=False)
            except Exception:
                break
            rms = np.sqrt(np.mean(np.frombuffer(data, dtype=np.int16).astype(np.float32) ** 2))
            if rms > effective_threshold:
                if not speech_detected:
                    speech_detected = True
                    speech_frames = [data]
                    print(f"[INT]  Voice detected mid-playback (RMS={rms:.0f})", flush=True)
                else:
                    speech_frames.append(data)
                    # 2 consecutive chunks (~0.13s) above threshold fires interrupt.
                    # Short words like "STOP" should trigger this reliably.
                    if len(speech_frames) >= 2:
                        print("[INT]  Interrupt triggered", flush=True)
                        interrupted_event.set()
                        _stop_playback.set()
                        break
            else:
                if speech_detected and len(speech_frames) < 1:
                    # Only reset if we haven't even accumulated a single chunk
                    speech_detected = False
                    speech_frames = []
        # ─────────────────────────────────────────────────────────────────────

        mon.stop_stream()
        mon.close()
    except Exception as e:
        print(f"[INT]  Monitor error: {e}", flush=True)


def play_pcm(pcm_bytes, pa, rate=22050):
    _stop_playback.clear()
    # Central gain for the headphone→external-amp path (3.5mm jack → 5V 3W amp).
    # Previously 1.5x for the Speaker/JST path; raised to 2.5x after hardware move.
    raw = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32)
    samples = np.clip(raw * 1.0, -32768, 32767).astype(np.int16)
    stereo = np.column_stack([samples, samples]).flatten().tobytes()
    interrupted = threading.Event(); pos = [0]

    def callback(in_data, frame_count, time_info, status):
        if interrupted.is_set() or _stop_playback.is_set() or button_pressed():
            interrupted.set(); return (b"\x00" * frame_count * 4, pyaudio.paComplete)
        chunk = stereo[pos[0]:pos[0] + frame_count * 4]; pos[0] += frame_count * 4
        if len(chunk) < frame_count * 4:
            return (chunk + b"\x00" * (frame_count * 4 - len(chunk)), pyaudio.paComplete)
        return (chunk, pyaudio.paContinue)

    # Start background interrupt listener
    _int_stop = threading.Event()
    _int_thread = threading.Thread(
        target=_playback_interrupt_listener,
        args=(pa, _int_stop, interrupted),
        daemon=True
    )
    _int_thread.start()

    stream = pa.open(format=pyaudio.paInt16, channels=2, rate=rate, output=True,
                     frames_per_buffer=512, stream_callback=callback)
    stream.start_stream()
    while stream.is_active():
        time.sleep(0.02)
        if button_pressed() or _stop_playback.is_set(): interrupted.set()
    stream.stop_stream(); stream.close()

    # Stop interrupt listener
    _int_stop.set()
    _int_thread.join(timeout=1.0)

    if interrupted.is_set(): print("[STOP] Playback interrupted", flush=True)
    _stop_playback.clear()


def play_beep(pa):
    rate = 44100; t = np.linspace(0, 0.2, int(rate * 0.2), False)
    tone = (np.sin(2 * np.pi * 880 * t) * 6000).astype(np.int16)
    stereo = np.column_stack([tone, tone]).flatten()
    stream = pa.open(format=pyaudio.paInt16, channels=2, rate=rate, output=True)
    stream.write(stereo.tobytes()); stream.stop_stream(); stream.close()


def play_double_beep(pa):
    rate = 44100; t = np.linspace(0, 0.12, int(rate * 0.12), False)
    tone = (np.sin(2 * np.pi * 660 * t) * 4000).astype(np.int16)
    gap = np.zeros(int(rate * 0.08), dtype=np.int16)
    sequence = np.concatenate([tone, gap, tone])
    stereo = np.column_stack([sequence, sequence]).flatten()
    stream = pa.open(format=pyaudio.paInt16, channels=2, rate=rate, output=True)
    stream.write(stereo.tobytes()); stream.stop_stream(); stream.close()


# ── Record ────────────────────────────────────────────────────────────────────

def record_command(mic, ptt_mode=False):
    frames = []; silence = 0
    rec_secs  = KIDS_RECORD_SECONDS if _kids_mode else RECORD_SECONDS
    sil_secs  = KIDS_SILENCE_SECS   if _kids_mode else SILENCE_SECS
    sil_rms   = KIDS_SILENCE_RMS    if _kids_mode else SILENCE_RMS
    max_chunks = int(SAMPLE_RATE / CHUNK * rec_secs)
    sil_limit  = int(SAMPLE_RATE / CHUNK * sil_secs)
    for _ in range(max_chunks):
        f = mic.read(CHUNK, exception_on_overflow=False); frames.append(f)
        if ptt_mode:
            if not button_pressed(): break
        else:
            rms = np.sqrt(np.mean(np.frombuffer(f, dtype=np.int16).astype(np.float32)**2))
            silence = silence + 1 if rms < sil_rms else 0
            if silence >= sil_limit: break
    return b"".join(frames)


# ── Camera + Vision ───────────────────────────────────────────────────────────

def capture_image():
    import tempfile, os as _os
    tmp = tempfile.mktemp(suffix='.jpg')
    try:
        result = subprocess.run(
            ['rpicam-still', '-o', tmp, '--width', str(CAMERA_WIDTH),
             '--height', str(CAMERA_HEIGHT), '--nopreview', '-t', str(CAMERA_TIMEOUT)],
            capture_output=True, timeout=CAMERA_TIMEOUT/1000 + 5)
        if result.returncode != 0:
            print(f"[CAM]  Capture failed: {result.stderr.decode()[:100]}", flush=True); return None
        with open(tmp, 'rb') as f: return f.read()
    except Exception as e:
        print(f"[CAM]  Exception: {e}", flush=True); return None
    finally:
        try: _os.unlink(tmp)
        except: pass


def is_vision_trigger(text: str) -> bool:
    return any(trigger in text.lower().strip().rstrip(".!?") for trigger in VISION_TRIGGERS)


def ask_vision(image_bytes: bytes, prompt: str) -> str:
    import base64
    img_b64 = base64.b64encode(image_bytes).decode()
    vision_prompt = (
        f"Describe what you see in plain spoken sentences only. "
        f"No markdown, no lists, no preamble. 2-3 sentences max. "
        f"The user asked: {prompt}"
    )
    r = requests.post(
        f"http://{GANDALF}:{OLLAMA_PORT}/api/generate",
        json={"model": VISION_MODEL, "prompt": vision_prompt, "images": [img_b64], "stream": False},
        timeout=90,
    )
    r.raise_for_status()
    data = r.json()
    reply = data.get("response", "") or data.get("message", {}).get("content", "")
    # Strip thinking blocks
    reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL).strip()
    # Strip emotion tag -- vision uses same jarvis model which emits [EMOTION:X]
    _, reply = extract_emotion_from_reply(reply)
    return reply or "I could not make out what I was looking at."


# ── Volume ────────────────────────────────────────────────────────────────────

def _find_wm8960_card() -> int:
    try:
        out = subprocess.check_output(['aplay', '-l'], text=True)
        for line in out.splitlines():
            if 'wm8960' in line.lower(): return int(line.split()[1].rstrip(':'))
    except Exception: pass
    return 1

def get_volume() -> int:
    out = subprocess.check_output(["amixer", "-c", str(_find_wm8960_card()), "sget", VOL_CONTROL], text=True)
    for line in out.splitlines():
        if "Playback" in line and "[" in line:
            m = re.search(r"Playback (\d+)", line)
            if m: return int(m.group(1))
    return 110

def set_volume(level: int) -> int:
    level = max(VOL_MIN, min(VOL_MAX, level))
    subprocess.run(["amixer", "-c", str(_find_wm8960_card()), "sset", VOL_CONTROL, str(level)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return level

def handle_volume_command(text: str):
    t = text.lower().strip().rstrip(".!?"); current = get_volume()
    pct_match = re.search(r'(\d+)\s*(?:percent|%)', t)
    if pct_match and 'volume' in t:
        target_vol = max(VOL_MIN, min(VOL_MAX, int(int(pct_match.group(1)) / 100 * VOL_MAX)))
        set_volume(target_vol); return f"Volume set to {int(target_vol/VOL_MAX*100)} percent."
    if any(p in t for p in ("all the way up","max volume","volume max","full volume","maximum volume","as loud")):
        set_volume(VOL_MAX); return "Volume set to maximum."
    if any(p in t for p in ("all the way down","volume low","minimum volume","volume minimum","as quiet")):
        set_volume(VOL_MIN); return "Volume set to minimum."
    if any(p in t for p in ("volume up","louder","turn it up","increase volume","turn up","raise volume","higher volume","more volume")):
        return f"Volume increased to {int(set_volume(current+VOL_STEP)/VOL_MAX*100)} percent."
    if any(p in t for p in ("volume down","quieter","turn it down","decrease volume","lower volume","turn down","reduce volume","less volume","softer","too loud")):
        return f"Volume decreased to {int(set_volume(current-VOL_STEP)/VOL_MAX*100)} percent."
    if any(p in t for p in ("what's the volume","whats the volume","current volume","volume level","how loud","what volume")):
        return f"Volume is at {int(current/VOL_MAX*100)} percent."
    if 'volume' in set(t.split()) and len(t.split()) <= 6:
        return f"Volume is at {int(current/VOL_MAX*100)} percent."
    return None


# ── Follow-up ─────────────────────────────────────────────────────────────────

def implies_followup(reply: str) -> bool:
    r = reply.strip()
    if r.endswith('?'): return True
    rl = r.lower()
    return any(rl.endswith(p) or rl.endswith(p+'.') for p in
               ("want me to","shall i","would you like me to","let me know if","go ahead"))

def record_followup(mic, pa, leds, timeout=None):
    if timeout is None:
        timeout = KIDS_FOLLOWUP_TIMEOUT if _kids_mode else FOLLOWUP_TIMEOUT
    leds.show_followup(); play_double_beep(pa)
    frames = []; silence = 0; speech_detected = False
    sil_secs  = KIDS_SILENCE_SECS   if _kids_mode else SILENCE_SECS
    sil_rms   = KIDS_SILENCE_RMS    if _kids_mode else SILENCE_RMS
    rec_secs  = KIDS_RECORD_SECONDS if _kids_mode else RECORD_SECONDS
    sil_limit = int(SAMPLE_RATE / CHUNK * sil_secs)
    max_chunks = int(SAMPLE_RATE / CHUNK * (timeout + rec_secs))
    timeout_chunks = int(SAMPLE_RATE / CHUNK * timeout); chunks_read = 0
    mic.start_stream()
    for _ in range(max_chunks):
        f = mic.read(CHUNK, exception_on_overflow=False); chunks_read += 1
        rms = np.sqrt(np.mean(np.frombuffer(f, dtype=np.int16).astype(np.float32)**2))
        if not speech_detected:
            if rms > sil_rms: speech_detected = True; frames.append(f)
            elif chunks_read >= timeout_chunks: mic.stop_stream(); return None
        else:
            frames.append(f); silence = silence + 1 if rms < sil_rms else 0
            if silence >= sil_limit: break
    mic.stop_stream()
    return b"".join(frames) if speech_detected else None


def show_idle_for_mode(leds):
    if _kids_mode: leds.show_idle_kids()
    else: leds.show_idle()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    leds = APA102(NUM_LEDS)
    setup_button()
    ctx_thread = threading.Thread(target=_context_watchdog, daemon=True); ctx_thread.start()
    teensy = TeensyBridge(TEENSY_PORT, TEENSY_BAUD)

    print("[INFO] Starting wyoming-openwakeword...", flush=True)
    leds.show_thinking()
    oww_proc = subprocess.Popen(
        ["/home/pi/wyoming-openwakeword/.venv/bin/python3", "-m", "wyoming_openwakeword",
         "--uri", f"tcp://127.0.0.1:{OWW_PORT}", "--preload-model", WAKE_WORD],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):
        try: socket.create_connection(("127.0.0.1", OWW_PORT), timeout=1).close(); break
        except (ConnectionRefusedError, OSError): time.sleep(0.5)
    else:
        print("[ERR] openwakeword failed to start", flush=True)
        leds.show_error(); time.sleep(2); leds.close(); oww_proc.kill(); sys.exit(1)

    print("[INFO] openwakeword ready", flush=True)
    pa = pyaudio.PyAudio()
    mic = pa.open(rate=SAMPLE_RATE, channels=CHANNELS, format=pyaudio.paInt16,
                  input=True, frames_per_buffer=CHUNK)

    print(f"[INFO] Wake word  : {WAKE_WORD}", flush=True)
    print(f"[INFO] LLM adult  : {OLLAMA_MODEL_ADULT} @ {GANDALF}:{OLLAMA_PORT}", flush=True)
    print(f"[INFO] LLM kids   : {OLLAMA_MODEL_KIDS}", flush=True)
    print(f"[INFO] Teensy     : {TEENSY_PORT}", flush=True)
    print("[INFO] Ready.", flush=True)
    show_idle_for_mode(leds)

    try:
        while True:
            oww_sock = socket.create_connection(("127.0.0.1", OWW_PORT), timeout=10)
            trigger = wait_for_wakeword_or_button(mic, oww_sock); oww_sock.close()
            ptt_mode = (trigger == "button")

            if ptt_mode: print("\n[PTT]  Button pressed", flush=True); leds.show_ptt()
            else: print("\n[WAKE] Wake word detected", flush=True); leds.show_wake()

            if not ensure_gandalf_up(leds):
                leds.show_error(); time.sleep(2); show_idle_for_mode(leds); continue

            play_beep(pa)
            # Drain mic 400 ms: clears the beep echo so it cannot bleed into
            # record_command and be transcribed as "BEEP" / "1" by Whisper.
            _drain_n = int(SAMPLE_RATE / CHUNK * 0.40)
            for _ in range(_drain_n):
                try: mic.read(CHUNK, exception_on_overflow=False)
                except Exception: break
            # Fire person recognition in background while user is speaking
            _pr_thread = threading.Thread(target=_run_person_recognition, daemon=True)
            _pr_thread.start()
            leds.show_recording(); print("[REC]  Listening...", flush=True)
            raw = record_command(mic, ptt_mode=ptt_mode)
            arr = np.frombuffer(raw, dtype=np.int16).astype(float)
            rms = np.sqrt(np.mean(arr**2))
            print(f"[REC]  {len(raw)/2/SAMPLE_RATE:.1f}s  RMS={rms:.0f}", flush=True)

            if rms < 400:
                print("[REC]  Near-silent (Whisper gate), ignoring", flush=True); show_idle_for_mode(leds); continue

            leds.show_thinking(); print("[STT]  Transcribing...", flush=True)
            try: text = transcribe(raw)
            except Exception as e:
                print(f"[ERR]  STT: {e}", flush=True)
                leds.show_error(); time.sleep(1); show_idle_for_mode(leds); continue

            if not text:
                print("[STT]  Empty transcript", flush=True); show_idle_for_mode(leds); continue
            print(f"[STT]  '{text}'", flush=True)

            _text_norm = text.lower().strip().strip(".!?,;:")
            if any(_text_norm == phrase or _text_norm.startswith(phrase)
                   for phrase in STOP_PHRASES):
                print("[STOP] Stop command received", flush=True)
                _stop_playback.set(); emit_emotion(teensy, leds, "NEUTRAL")
                show_idle_for_mode(leds); continue

            # ── Eyes sleep/wake voice commands ────────────────────────────────
            global _eyes_sleeping
            _tnorm = text.lower().strip().strip(".!?,;:")
            if any(_tnorm == p or _tnorm.startswith(p) for p in EYES_SLEEP_TRIGGERS):
                if not _eyes_sleeping:
                    _eyes_sleeping = True
                    teensy.send_command("EYES:SLEEP")
                    print("[EYES] Eyes deactivated by voice", flush=True)
                show_idle_for_mode(leds); continue

            if any(_tnorm == p or _tnorm.startswith(p) for p in EYES_WAKE_TRIGGERS):
                if _eyes_sleeping:
                    _eyes_sleeping = False
                    teensy.send_command("EYES:WAKE")
                    print("[EYES] Eyes activated by voice", flush=True)
                show_idle_for_mode(leds); continue

            # Auto-wake: any non-sleep/wake interaction restores the eyes
            if _eyes_sleeping:
                _eyes_sleeping = False
                teensy.send_command("EYES:WAKE")
                print("[EYES] Eyes auto-waked by interaction", flush=True)

            kids_reply, new_mode = handle_kids_mode_command(text)
            if kids_reply is not None:
                print(f"[MODE] {kids_reply}", flush=True)
                leds.show_kids_mode_on() if new_mode else leds.show_kids_mode_off()
                time.sleep(0.6)
                try:
                    pcm_data = synthesize(kids_reply)
                    leds.show_speaking(); mic.stop_stream(); play_pcm(pcm_data, pa); mic.start_stream()
                except Exception as e: print(f"[ERR]  TTS mode switch: {e}", flush=True)
                emit_emotion(teensy, leds, "NEUTRAL"); show_idle_for_mode(leds)
                print("[INFO] Ready.", flush=True); continue

            time_reply = handle_time_command(text)
            if time_reply is not None:
                print(f"[TIME] {time_reply}", flush=True)
                try:
                    pcm_data = synthesize(time_reply)
                    leds.show_speaking(); mic.stop_stream(); play_pcm(pcm_data, pa); mic.start_stream()
                except Exception as e: print(f"[ERR]  TTS time: {e}", flush=True)
                emit_emotion(teensy, leds, "NEUTRAL"); show_idle_for_mode(leds)
                print("[INFO] Ready.", flush=True); continue

            if CAMERA_ENABLED and is_vision_trigger(text):
                print("[CAM]  Vision trigger detected", flush=True)
                emit_emotion(teensy, leds, "CURIOUS"); leds.show_thinking()
                img = capture_image()
                if img is None: reply = "Sorry, I could not capture an image right now."
                else:
                    print(f"[CAM]  Captured {len(img)//1024}KB", flush=True)
                    try: reply = ask_vision(img, text); print(f"[VIS]  '{reply}'", flush=True)
                    except Exception as e:
                        reply = "I had trouble processing the image."
                        print(f"[ERR]  Vision: {e}", flush=True)
                try:
                    pcm_data = synthesize(reply)
                    leds.show_speaking(); mic.stop_stream(); play_pcm(pcm_data, pa); mic.start_stream()
                except Exception as e: print(f"[ERR]  TTS vision: {e}", flush=True)
                emit_emotion(teensy, leds, "NEUTRAL"); show_idle_for_mode(leds)
                print("[INFO] Ready.", flush=True); continue

            weather_reply = handle_weather_command(text)
            if weather_reply is not None:
                print(f"[WX]   {weather_reply}", flush=True)
                try:
                    pcm_data = synthesize(weather_reply)
                    leds.show_speaking(); mic.stop_stream(); play_pcm(pcm_data, pa); mic.start_stream()
                except Exception as e: print(f"[ERR]  TTS weather: {e}", flush=True)
                emit_emotion(teensy, leds, "NEUTRAL"); show_idle_for_mode(leds)
                print("[INFO] Ready.", flush=True); continue

            briefing_reply = handle_daily_briefing(text)
            if briefing_reply is not None:
                print(f"[BRIEF] {briefing_reply[:80]}...", flush=True)
                try:
                    pcm_data = synthesize(briefing_reply)
                    leds.show_speaking(); mic.stop_stream(); play_pcm(pcm_data, pa); mic.start_stream()
                except Exception as e: print(f"[ERR]  TTS briefing: {e}", flush=True)
                emit_emotion(teensy, leds, "NEUTRAL"); show_idle_for_mode(leds)
                print("[INFO] Ready.", flush=True); continue

            vol_reply = handle_volume_command(text)
            if vol_reply is not None:
                print(f"[VOL]  {vol_reply}", flush=True)
                try:
                    pcm_data = synthesize(vol_reply)
                    leds.show_speaking(); mic.stop_stream(); play_pcm(pcm_data, pa); mic.start_stream()
                except Exception as e: print(f"[ERR]  TTS vol: {e}", flush=True)
                emit_emotion(teensy, leds, "NEUTRAL"); show_idle_for_mode(leds)
                print("[INFO] Ready.", flush=True); continue

            print(f"[LLM]  Thinking... (model={get_model()})", flush=True)
            try: reply, emotion = ask_ollama(text)
            except Exception as e:
                print(f"[ERR]  LLM: {e}", flush=True)
                leds.show_error(); time.sleep(1); show_idle_for_mode(leds); continue
            print(f"[LLM]  '{reply}'", flush=True)

            emit_emotion(teensy, leds, emotion)

            print("[TTS]  Synthesizing...", flush=True)
            try: pcm_data = synthesize(reply)
            except Exception as e:
                print(f"[ERR]  TTS: {e}", flush=True)
                leds.show_error(); time.sleep(1); show_idle_for_mode(leds); continue

            leds.show_speaking(); mic.stop_stream(); play_pcm(pcm_data, pa)
            if button_pressed(): time.sleep(0.4)

            # Follow-up loop
            _followup_turns = 0
            while implies_followup(reply) and _followup_turns < FOLLOWUP_MAX_TURNS:
                print(f"[FLWP] Follow-up turn {_followup_turns+1}/{FOLLOWUP_MAX_TURNS}...", flush=True)
                _followup_turns += 1
                followup_audio = record_followup(mic, pa, leds)
                if followup_audio is None: print("[FLWP] No response", flush=True); break
                rms = np.sqrt(np.mean(np.frombuffer(followup_audio, dtype=np.int16).astype(np.float32)**2))
                if rms < 100: print("[FLWP] Silent", flush=True); break
                leds.show_thinking(); print("[STT]  Transcribing follow-up...", flush=True)
                try: text = transcribe(followup_audio)
                except Exception as e: print(f"[ERR]  STT follow-up: {e}", flush=True); break
                if not text: print("[FLWP] Empty transcript", flush=True); break
                print(f"[STT]  '{text}'", flush=True)
                _text_norm = text.lower().strip().strip(".!?,;:")
                if any(_text_norm == phrase or _text_norm.startswith(phrase)
                       for phrase in STOP_PHRASES):
                    print("[STOP] Stop in follow-up", flush=True); break
                if any(_text_norm == phrase or _text_norm.startswith(phrase)
                       for phrase in FOLLOWUP_DISMISSALS):
                    print("[FLWP] Polite dismissal, ending follow-up", flush=True); break
                time_reply = handle_time_command(text)
                if time_reply is not None:
                    reply = time_reply; emotion = "NEUTRAL"
                else:
                    vol_reply = handle_volume_command(text)
                    if vol_reply is not None:
                        reply = vol_reply; emotion = "NEUTRAL"
                    else:
                        print(f"[LLM]  Thinking... (model={get_model()})", flush=True)
                        try: reply, emotion = ask_ollama(text)
                        except Exception as e: print(f"[ERR]  LLM follow-up: {e}", flush=True); break
                        print(f"[LLM]  '{reply}'", flush=True)
                emit_emotion(teensy, leds, emotion)
                print("[TTS]  Synthesizing...", flush=True)
                try: pcm_data = synthesize(reply)
                except Exception as e: print(f"[ERR]  TTS follow-up: {e}", flush=True); break
                leds.show_speaking(); mic.stop_stream(); play_pcm(pcm_data, pa)
                if button_pressed(): time.sleep(0.4)

            mic.start_stream()
            emit_emotion(teensy, leds, "NEUTRAL")
            show_idle_for_mode(leds)
            print("[INFO] Ready.", flush=True)

    except KeyboardInterrupt:
        print("\n[INFO] Shutting down.", flush=True)
    finally:
        flush_conversation_log(reason="shutdown")
        emit_emotion(teensy, leds, "NEUTRAL"); teensy.close()
        leds.close(); GPIO.cleanup()
        mic.stop_stream(); mic.close(); pa.terminate()
        oww_proc.terminate()


if __name__ == "__main__":
    main()

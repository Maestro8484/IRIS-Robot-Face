#!/usr/bin/env python3
"""
assistant.py - Pi4 IRIS voice assistant
Wake: wyoming-openwakeword hey_jarvis (:10400) OR button press (GPIO17)
STT:  Wyoming Whisper  @ 192.168.1.3:10300
LLM:  Ollama           @ 192.168.1.3:11434 (streaming)
TTS:  Kokoro           @ 192.168.1.3:8004 (primary) / Piper @ :10200 (fallback)
Audio: wm8960-soundcard (dynamic card detection)
LEDs: 3x APA102 via SPI -- status indicator
Eyes: Teensy 4.1 via /dev/ttyIRIS_EYES
Base: Teensy 4.0 servo/gesture via /dev/ttyIRIS_SERVO (BaseMountBridge)
"""

import json, os, queue, re, socket, subprocess, sys, threading, time
import numpy as np
import pyaudio
import requests
import warnings; warnings.filterwarnings("ignore")

from core.config import *
from hardware.teensy_bridge import TeensyBridge
from hardware.base_mount_bridge import BaseMountBridge
from hardware.led import APA102
from hardware.io import setup_button, button_pressed, gpio_cleanup
from hardware.audio_io import (
    _find_mic_device_index, get_volume, set_volume, handle_volume_command,
    play_pcm, play_pcm_speaking, play_pcm_stream, play_beep, play_double_beep, play_wol_beep,
    record_command, _stop_playback, STOP_PHRASES, FOLLOWUP_DISMISSALS,
)
from services.wyoming import wy_send, read_line
from services.stt import transcribe
from services.tts import synthesize, spoken_numbers
from services.llm import extract_emotion_from_reply, clean_llm_reply, stream_ollama, classify_response_length
from services.vision import capture_image, is_vision_trigger, ask_vision
from services.wakeword import wait_for_wakeword_or_button
from state.state_manager import state
from core.intent_router import (
    IntentRouter, IntentResult,
    ROUTE_REFLEX, ROUTE_COMMAND, ROUTE_UTILITY, ROUTE_AMBIGUOUS, ROUTE_LLM,
)


def get_model() -> str:
    return OLLAMA_MODEL_KIDS if state.kids_mode else OLLAMA_MODEL_ADULT


# ── Wake quips ────────────────────────────────────────────────────────────────

_WAKE_QUIPS = [
    # (hour_start, hour_end, emotion, [lines...])
    (5,  8,  "SLEEPY", ["It's early. Go ahead.",    "You're up. Fine.",
                         "Early start. Go on.",      "Right then. What?"          ]),
    (8,  12, "HAPPY",  ["Yeah, what?",               "Go ahead.",
                         "Go on then.",              "Yes?",          "What's up?"]),
    (12, 17, "AMUSED", ["Go.",                       "What is it?",
                         "Mm?",                      "Yeah?",         "Go on."    ]),
    (17, 21, "HAPPY",  ["What do you need?",         "Yeah, go.",
                         "Evening. What is it?",     "Go on."                     ]),
    (21, 23, "AMUSED", ["Still at it. Go ahead.",    "Getting late. Go.",
                         "What is it?",              "Yeah?"                      ]),
    (23, 24, "SLEEPY", ["It's late. Make it quick.", "This better be good.",
                         "Go on then.",              "Right. What?"               ]),
    (0,  5,  "SLEEPY", ["It's the middle of the night.", "This better be good.",
                         "Really. Go on.",           "Go. Quickly."               ]),
]

# ── Rapid Pre-canned Quick Responses (RPQR) ───────────────────────────────────

_DOUBLE_TAP_QUIPS = [
    "Still here. Haven't moved.",
    "Yes, still on.",
    "I didn't go anywhere.",
]

_POST_SPEECH_QUIPS = [
    "I literally just answered that.",
    "Give it a moment.",
    "I just finished. Go on.",
]

_HOUR_NAMES = [
    "Midnight", "One", "Two", "Three", "Four", "Five", "Six",
    "Seven", "Eight", "Nine", "Ten", "Eleven", "Noon",
    "One", "Two", "Three", "Four", "Five", "Six",
    "Seven", "Eight", "Nine", "Ten", "Eleven",
]

_wake_quip_cache: dict = {}
_rpqr_cache: dict = {}
_last_quip_line: str = ""

# mutable state dict — avoids global declarations in main loop
_rpqr_state: dict = {
    "t_last_wake":          0.0,
    "t_last_spoke":         0.0,
    "last_interaction_date": None,
    "t_last_top_of_hour":   0.0,
}


def _pick_wake_quip(hour: int) -> tuple:
    import random
    global _last_quip_line
    for h_start, h_end, emotion, lines in _WAKE_QUIPS:
        if h_start <= hour < h_end:
            choices = [l for l in lines if l != _last_quip_line] or lines
            line = random.choice(choices)
            _last_quip_line = line
            return line, emotion
    return "Yeah.", "NEUTRAL"


def _play_wake_quip(hour: int, pa, teensy, leds) -> None:
    line, emotion = _pick_wake_quip(hour)
    pcm = _wake_quip_cache.get(line)
    if not pcm:
        print(f"[QUIP] No cache for '{line}' -- skipping", flush=True)
        return
    try:
        emit_emotion(teensy, leds, emotion)
        play_pcm_speaking(pcm, pa, teensy, restore_mouth_idx=0)
        print(f"[QUIP] {emotion}: {line!r}", flush=True)
    except Exception as _e:
        print(f"[QUIP] Failed: {_e}", flush=True)


def _play_rpqr(line: str, emotion: str, pa, teensy, leds) -> None:
    pcm = _rpqr_cache.get(line)
    if not pcm:
        print(f"[RPQR] No cache for '{line}' -- skipping", flush=True)
        return
    try:
        emit_emotion(teensy, leds, emotion)
        play_pcm_speaking(pcm, pa, teensy, restore_mouth_idx=0)
        print(f"[RPQR] {emotion}: {line!r}", flush=True)
    except Exception as _e:
        print(f"[RPQR] Failed: {_e}", flush=True)


def _pre_synthesize_quips() -> None:
    unique_wake = {l for _, _, _, lines in _WAKE_QUIPS for l in lines}
    for line in unique_wake:
        try:
            _wake_quip_cache[line] = synthesize(line)
            print(f"[QUIP] Cached: {line!r}", flush=True)
        except Exception as _e:
            print(f"[QUIP] Cache miss '{line}': {_e}", flush=True)

    rpqr_lines: list = list(_DOUBLE_TAP_QUIPS) + list(_POST_SPEECH_QUIPS) + ["Morning.", "Finally."]
    seen_toh: set = set()
    for h in range(24):
        name = _HOUR_NAMES[h]
        toh = f"{name}. That's the whole thought." if name in ("Midnight", "Noon") \
              else f"{name} o'clock. That's the whole thought."
        if toh not in seen_toh:
            rpqr_lines.append(toh)
            seen_toh.add(toh)
    for line in rpqr_lines:
        try:
            _rpqr_cache[line] = synthesize(line)
            print(f"[RPQR] Cached: {line!r}", flush=True)
        except Exception as _e:
            print(f"[RPQR] Cache miss '{line}': {_e}", flush=True)


# ── Conversation logger ───────────────────────────────────────────────────────

def flush_conversation_log(reason: str = "timeout"):
    if not state.conversation_history:
        return
    import datetime
    os.makedirs(os.path.dirname(CONVERSATION_LOG), exist_ok=True)
    record = {
        "ts":       datetime.datetime.now().isoformat(timespec="seconds"),
        "reason":   reason,
        "mode":     "kids" if state.kids_mode else "adult",
        "model":    get_model(),
        "turns":    sum(1 for m in state.conversation_history if m["role"] == "user"),
        "messages": list(state.conversation_history),
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
        if state.last_interaction == 0.0:
            continue
        elapsed = time.time() - state.last_interaction
        if elapsed >= CONTEXT_TIMEOUT_SECS and state.conversation_history:
            flush_conversation_log(reason="timeout")
            state.clear_conversation()
            state.last_interaction = 0.0
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


def ensure_gandalf_up(leds, pa=None) -> bool:
    if gandalf_is_up():
        return True
    print("[WOL]  GandalfAI is offline -- sending Wake-on-LAN...", flush=True)
    send_wol(GANDALF_MAC, GANDALF_WOL_IP, GANDALF_WOL_PORT)
    if pa is not None:
        play_wol_beep(pa)

    leds.show_wol()
    deadline = time.time() + WOL_BOOT_TIMEOUT
    while time.time() < deadline:
        time.sleep(WOL_POLL_INTERVAL)
        if gandalf_is_up():
            leds.stop_anim()
            print("[WOL]  GandalfAI is up.", flush=True)
            return True
        print(f"[WOL]  Waiting for GandalfAI... ({int(deadline-time.time())}s remaining)", flush=True)
    leds.stop_anim()
    print("[ERR]  GandalfAI did not come up in time.", flush=True)
    return False


# ── CMD listener + Emotion helper ─────────────────────────────────────────────

def start_cmd_listener(teensy, leds):
    """UDP listener on CMD_PORT. iris_web.py sends raw commands here."""
    def _listener():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("127.0.0.1", CMD_PORT))
            print(f"[CMD] Listening for web UI commands on UDP port {CMD_PORT}", flush=True)
            while True:
                try:
                    data, _ = s.recvfrom(256)
                    cmd = data.decode(errors="ignore").strip()
                    if cmd:
                        if cmd in ("STOP_PLAYBACK", "STOP"):
                            _stop_playback.set()
                            print(f"[CMD] {cmd}: playback interrupted", flush=True)
                        else:
                            print(f"[CMD] -> teensy: {cmd}", flush=True)
                            if state.eyes_sleeping and (
                                cmd.startswith("EMOTION:") or cmd.startswith("EYE:")
                                or cmd.startswith("MOUTH:")
                            ):
                                _do_wake(teensy, leds)
                                print(f"[CMD] Auto-woke eyes for: {cmd}", flush=True)
                            teensy.send_command(cmd)
                            if cmd == "EYES:SLEEP":
                                _do_sleep(teensy, leds)
                            elif cmd == "EYES:WAKE":
                                _do_wake(teensy, leds)
                except Exception as e:
                    print(f"[CMD] Listener error: {e}", flush=True)
    threading.Thread(target=_listener, daemon=True).start()


def emit_emotion(teensy, leds, emotion: str):
    """Send emotion to Teensy eyes AND sync LED color in one call."""
    eye_idx = EMOTION_EYE_MAP.get(emotion, -1)
    if eye_idx >= 0:
        teensy.send_command(f"EYE:{eye_idx}")
    teensy.send_emotion(emotion)
    teensy.send_command(f"MOUTH:{MOUTH_MAP.get(emotion, 0)}")
    leds.show_emotion(emotion)


# ── Local command handlers ────────────────────────────────────────────────────

def handle_kids_mode_command(text: str):
    t = text.lower().strip().rstrip(".!?")
    on_triggers  = ("kids mode on", "enable kids mode", "turn on kids mode", "switch to kids mode",
                    "kids mode please", "activate kids mode", "children's mode on", "kid mode on")
    off_triggers = ("kids mode off", "disable kids mode", "turn off kids mode", "switch to adult mode",
                    "adult mode", "deactivate kids mode", "kid mode off", "normal mode")
    if any(tr in t for tr in on_triggers):
        state.kids_mode = True
        flush_conversation_log(reason="mode_switch_kids_on")
        state.clear_conversation()
        print(f"[MODE] Kids mode ON -- model: {OLLAMA_MODEL_KIDS}", flush=True)
        return "Kids mode activated.", True
    if any(tr in t for tr in off_triggers):
        state.kids_mode = False
        flush_conversation_log(reason="mode_switch_kids_off")
        state.clear_conversation()
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



# ── LLM helpers ───────────────────────────────────────────────────────────────

def _build_messages() -> list:
    """Build the messages list for Ollama including date inject and person context."""
    import datetime
    now = datetime.datetime.now()
    date_inject = {
        "role": "system",
        "content": f"Current date and time: {now.strftime('%A, %B %d %Y, %I:%M %p')} Mountain Time."
    }
    return [date_inject] + list(state.conversation_history)


def ask_ollama(text, num_predict=None):
    """
    Blocking LLM query. Used for followup loop and vision path.
    Returns (reply, emotion) tuple.
    """
    state.last_interaction = time.time()
    state.conversation_history.append({"role": "user", "content": text})
    r = requests.post(
        f"http://{GANDALF}:{OLLAMA_PORT}/api/chat",
        json={"model": get_model(), "messages": _build_messages(),
              "stream": False, "think": False, "options": {"num_predict": num_predict if num_predict is not None else NUM_PREDICT}},
        timeout=30
    )
    r.raise_for_status()
    raw = r.json()["message"]["content"]
    emotion, stripped = extract_emotion_from_reply(raw)
    reply = clean_llm_reply(stripped)
    print(f"[EYES] Emotion from LLM: {emotion}", flush=True)
    state.conversation_history.append({"role": "assistant", "content": reply})
    if len(state.conversation_history) > 20:
        state.conversation_history.pop(0); state.conversation_history.pop(0)
    return reply, emotion


# ── Follow-up ─────────────────────────────────────────────────────────────────

def implies_followup(reply: str) -> bool:
    r = reply.strip()
    if r.endswith('?'): return True
    rl = r.lower()
    return any(rl.endswith(p) or rl.endswith(p+'.') for p in
               ("want me to", "shall i", "would you like me to", "let me know if", "go ahead"))

def record_followup(mic, pa, leds, timeout=None):
    if timeout is None:
        timeout = KIDS_FOLLOWUP_TIMEOUT if state.kids_mode else FOLLOWUP_TIMEOUT
    leds.show_followup(); play_double_beep(pa)
    frames = []; silence = 0; speech_detected = False
    sil_secs  = KIDS_SILENCE_SECS   if state.kids_mode else SILENCE_SECS
    sil_rms   = KIDS_SILENCE_RMS    if state.kids_mode else SILENCE_RMS
    rec_secs  = KIDS_RECORD_SECONDS if state.kids_mode else RECORD_SECONDS
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
    if state.kids_mode: leds.show_idle_kids()
    else: leds.show_idle()


def in_sleep_window() -> bool:
    hour = time.localtime().tm_hour
    return hour >= SLEEP_WINDOW_START_HOUR or hour < SLEEP_WINDOW_END_HOUR


def _bench_write(stages, transcript, reply_chars, model, gandalf_was_cold, route, interrupted, emotion=None):
    """Append one structured JSON record to iris_bench.jsonl. Never raises."""
    import datetime
    try:
        os.makedirs(os.path.dirname(BENCH_LOG), exist_ok=True)
        record = {
            "ts":               datetime.datetime.now().isoformat(timespec="seconds"),
            "stages":           stages,
            "total_ms":         stages.get("play_start_ms"),
            "transcript":       transcript,
            "reply_chars":      reply_chars,
            "model":            model,
            "gandalf_was_cold": gandalf_was_cold,
            "route":            route,
            "interrupted":      interrupted,
        }
        if emotion is not None:
            record["emotion"] = emotion
        with open(BENCH_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
    except Exception as e:
        print(f"[BENCH] JSONL write failed: {e}", flush=True)


SLEEP_CFG_MAP = {
    "speed":           "SLEEP_ANIM_SPEED",
    "starBrightMin":   "SLEEP_ANIM_STAR_BRIGHT_MIN",
    "starBrightMax":   "SLEEP_ANIM_STAR_BRIGHT_MAX",
    "starTwinkleAmp":  "SLEEP_ANIM_STAR_TWINKLE",
    "shootCount":      "SLEEP_ANIM_SHOOT_COUNT",
    "shootSpeed":      "SLEEP_ANIM_SHOOT_SPEED",
    "shootLen":        "SLEEP_ANIM_SHOOT_LEN",
    "shootBright":     "SLEEP_ANIM_SHOOT_BRIGHT",
    "warpCount":       "SLEEP_ANIM_WARP_COUNT",
    "warpSpeed":       "SLEEP_ANIM_WARP_SPEED",
    "warpBright":      "SLEEP_ANIM_WARP_BRIGHT",
    "moonR":           "SLEEP_ANIM_MOON_R",
    "moonDrift":       "SLEEP_ANIM_MOON_DRIFT",
    "saturnR":         "SLEEP_ANIM_SATURN_R",
    "saturnDrift":     "SLEEP_ANIM_SATURN_DRIFT",
    "nebulaAlpha":     "SLEEP_ANIM_NEBULA_ALPHA",
    "waveAmp0":        "SLEEP_ANIM_WAVE_AMP0",
    "waveAmp1":        "SLEEP_ANIM_WAVE_AMP1",
    "waveAmp2":        "SLEEP_ANIM_WAVE_AMP2",
    "waveOscAmp":      "SLEEP_ANIM_WAVE_OSC_AMP",
    "mouthPulseAlpha": "SLEEP_ANIM_MOUTH_PULSE_A",
    "zzzAlpha0":       "SLEEP_ANIM_ZZZ_ALPHA0",
    "zzzAlpha1":       "SLEEP_ANIM_ZZZ_ALPHA1",
    "zzzAlpha2":       "SLEEP_ANIM_ZZZ_ALPHA2",
}


def _do_sleep(teensy, leds):
    teensy.send_command("EYES:SLEEP")
    try:
        import core.config as _cc
        try:
            with open("/home/pi/iris_config.json") as _f:
                _live = json.load(_f)
        except Exception:
            _live = {}
        for key, cfg_key in SLEEP_CFG_MAP.items():
            val = _live.get(cfg_key, getattr(_cc, cfg_key, None))
            if val is not None:
                teensy.send_command(f"SLEEP_CFG:{key}={val}")
    except Exception as _e:
        print(f"[SLEEP] SLEEP_CFG push failed: {_e}", flush=True)
    teensy.send_command("MOUTH:8")
    teensy.send_command(f"MOUTH_INTENSITY:{MOUTH_INTENSITY_SLEEP}")
    state.eyes_sleeping = True
    open("/tmp/iris_sleep_mode", "w").close()
    leds.show_sleep()
    print("[SLEEP] _do_sleep() complete", flush=True)


def _do_wake(teensy, leds):
    teensy.send_command("EYES:WAKE")
    teensy.send_command("MOUTH:0")
    teensy.send_command(f"MOUTH_INTENSITY:{MOUTH_INTENSITY_AWAKE}")
    state.eyes_sleeping = False
    try: os.remove("/tmp/iris_sleep_mode")
    except FileNotFoundError: pass
    show_idle_for_mode(leds)
    print("[WAKE] _do_wake() complete", flush=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    leds = APA102(NUM_LEDS)
    setup_button()
    from core.config import SPEAKER_VOLUME as _startup_vol
    set_volume(_startup_vol)
    print(f"[VOL]  Startup volume: {_startup_vol}/127 ({round(_startup_vol/127*100)}%)", flush=True)
    ctx_thread = threading.Thread(target=_context_watchdog, daemon=True); ctx_thread.start()
    teensy = TeensyBridge(TEENSY_PORT, TEENSY_BAUD)
    import core.config as _bm_cfg
    if BASE_MOUNT_ENABLED:
        base_bridge = BaseMountBridge(_bm_cfg, leds)
        base_bridge.start()
    start_cmd_listener(teensy, leds)
    router = IntentRouter()

    def _start_oww():
        proc = subprocess.Popen(
            ["/home/pi/wyoming-openwakeword/.venv/bin/python3", "-m", "wyoming_openwakeword",
             "--uri", f"tcp://127.0.0.1:{OWW_PORT}", "--preload-model", WAKE_WORD,
             "--threshold", str(OWW_THRESHOLD)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(30):
            try:
                socket.create_connection(("127.0.0.1", OWW_PORT), timeout=1).close()
                return proc
            except (ConnectionRefusedError, OSError):
                time.sleep(0.5)
        proc.kill()
        return None

    print("[INFO] Starting wyoming-openwakeword...", flush=True)
    leds.show_thinking()
    oww_proc = None
    for _attempt in range(3):
        oww_proc = _start_oww()
        if oww_proc is not None:
            break
        print(f"[ERR] openwakeword start attempt {_attempt+1}/3 failed", flush=True)
        time.sleep(2 ** _attempt)
    if oww_proc is None:
        print("[ERR] openwakeword could not start after 3 attempts -- will retry in main loop", flush=True)
        leds.show_error(); time.sleep(2)
    else:
        print("[INFO] openwakeword ready", flush=True)
    pa = pyaudio.PyAudio()
    mic_idx = _find_mic_device_index()
    mic = pa.open(rate=SAMPLE_RATE, channels=CHANNELS, format=pyaudio.paInt16,
                  input=True, frames_per_buffer=CHUNK,
                  input_device_index=mic_idx)

    print(f"[INFO] Wake word  : {WAKE_WORD}", flush=True)
    print(f"[INFO] LLM adult  : {OLLAMA_MODEL_ADULT} @ {GANDALF}:{OLLAMA_PORT}", flush=True)
    print(f"[INFO] LLM kids   : {OLLAMA_MODEL_KIDS}", flush=True)
    _tts_engine = "Kokoro" if KOKORO_ENABLED else "Piper"
    print(f"[INFO] TTS        : {_tts_engine} @ {GANDALF}:8004", flush=True)
    print(f"[INFO] Teensy     : {TEENSY_PORT}", flush=True)
    print(f"[INFO] Base mount : {BASE_MOUNT_PORT} (enabled={BASE_MOUNT_ENABLED})", flush=True)
    print("[INFO] Ready.", flush=True)
    show_idle_for_mode(leds)

    # ── Power-On Self-Test ────────────────────────────────────────────────────
    try:
        from iris_post import run_post as _iris_post
        _post_result = _iris_post(leds=leds, teensy=teensy, pa=pa, verbose=True)
        if _post_result.get("verdict") == "FAIL":
            print("[POST] FAIL -- IRIS startup blocked. Check /home/pi/logs/iris_post.log",
                  flush=True)
            sys.exit(1)
    except Exception as _pe:
        print(f"[POST] POST skipped: {_pe}", flush=True)
    # Restore eye to configured default after POST display exercise
    teensy.send_command(f"EYE:{DEFAULT_EYE_IDX}")
    print(f"[EYES] Default eye restored: EYE:{DEFAULT_EYE_IDX}", flush=True)
    _pre_synthesize_quips()
    # Pre-warm Ollama: eliminates ~10-12s cold-start penalty on first user interaction
    if gandalf_is_up():
        try:
            requests.post(
                f"http://{GANDALF}:{OLLAMA_PORT}/api/generate",
                json={"model": get_model(), "prompt": ".", "stream": False,
                      "think": False, "options": {"num_predict": 1}},
                timeout=30
            )
            print("[LLM]  Model warmed.", flush=True)
        except Exception as _e:
            print(f"[LLM]  Warmup skipped: {_e}", flush=True)
    # ─────────────────────────────────────────────────────────────────────────

    try:
        while True:
            # Restart OWW process if it has died
            if oww_proc is None or oww_proc.poll() is not None:
                print("[WARN] openwakeword process not running -- attempting restart", flush=True)
                if oww_proc is not None:
                    try: oww_proc.kill()
                    except Exception: pass
                oww_proc = None
                for _attempt in range(3):
                    oww_proc = _start_oww()
                    if oww_proc is not None:
                        print("[INFO] openwakeword restarted", flush=True)
                        break
                    print(f"[ERR] openwakeword restart attempt {_attempt+1}/3 failed", flush=True)
                    time.sleep(2 ** _attempt)
                if oww_proc is None:
                    print("[ERR] openwakeword unavailable -- retrying in 10s", flush=True)
                    leds.show_error(); time.sleep(10); show_idle_for_mode(leds); continue

            try:
                oww_sock = socket.create_connection(("127.0.0.1", OWW_PORT), timeout=10)
            except (OSError, ConnectionRefusedError) as e:
                print(f"[ERR] Cannot connect to openwakeword: {e} -- retrying in 5s", flush=True)
                leds.show_error(); time.sleep(5); show_idle_for_mode(leds); continue

            try:
                trigger = wait_for_wakeword_or_button(mic, oww_sock)
            except Exception as e:
                print(f"[ERR] wait_for_wakeword_or_button exception: {e}", flush=True)
                trigger = "error"
            finally:
                try: oww_sock.close()
                except Exception: pass

            if trigger == "error":
                print("[WARN] Wakeword socket error -- reconnecting", flush=True)
                leds.show_error(); time.sleep(2); show_idle_for_mode(leds); continue

            ptt_mode = (trigger == "button")
            _t_mono_wake = 0.0
            _gandalf_was_cold = False
            _bench_stages = {
                "wake_to_record_start_ms": None, "record_duration_ms": None,
                "stt_ms": None, "router_ms": None, "llm_first_token_ms": None,
                "llm_total_ms": None, "tts_ms": None, "play_start_ms": None,
            }
            _bench_transcript = ""
            _bench_reply_chars = 0
            _bench_route = ROUTE_LLM
            _bench_interrupted = False

            if ptt_mode: print("\n[PTT]  Button pressed", flush=True); leds.show_ptt()
            else: print("\n[WAKE] Wake word detected", flush=True); leds.show_wake()

            # Sleep mode check — quip is pre-cached PCM, no Gandalf needed
            if os.path.exists('/tmp/iris_sleep_mode'):
                _do_wake(teensy, leds)
                _play_wake_quip(time.localtime().tm_hour, pa, teensy, leds)
                if in_sleep_window():
                    _do_sleep(teensy, leds)
                show_idle_for_mode(leds); continue

            # ── RPQR trigger cascade (pre-cached PCM, fires before Gandalf gate) ──
            import random as _rnd
            _now_rpqr = time.time()
            _tm_rpqr  = time.localtime()
            _h_rpqr   = _tm_rpqr.tm_hour
            _mn_rpqr  = _tm_rpqr.tm_min
            _today    = (_tm_rpqr.tm_year, _tm_rpqr.tm_mon, _tm_rpqr.tm_mday)

            if _rpqr_state["last_interaction_date"] != _today:
                _first_line = "Morning." if _h_rpqr < 9 else "Finally."
                _play_rpqr(_first_line, "AMUSED", pa, teensy, leds)
                _rpqr_state["last_interaction_date"] = _today
            elif (_rpqr_state["t_last_wake"] > 0
                  and _now_rpqr - _rpqr_state["t_last_wake"] < 30):
                _play_rpqr(_rnd.choice(_DOUBLE_TAP_QUIPS), "AMUSED", pa, teensy, leds)
            elif (_rpqr_state["t_last_spoke"] > 0
                  and _now_rpqr - _rpqr_state["t_last_spoke"] < 5):
                _play_rpqr(_rnd.choice(_POST_SPEECH_QUIPS), "AMUSED", pa, teensy, leds)
            elif (_mn_rpqr <= 2
                  and (_rpqr_state["t_last_top_of_hour"] == 0
                       or _now_rpqr - _rpqr_state["t_last_top_of_hour"] > 600)):
                _toh_name = _HOUR_NAMES[_h_rpqr]
                _toh_line = (f"{_toh_name}. That's the whole thought."
                             if _toh_name in ("Midnight", "Noon")
                             else f"{_toh_name} o'clock. That's the whole thought.")
                _play_rpqr(_toh_line, "AMUSED", pa, teensy, leds)
                _rpqr_state["t_last_top_of_hour"] = _now_rpqr
            else:
                _play_wake_quip(_h_rpqr, pa, teensy, leds)

            _rpqr_state["t_last_wake"] = _now_rpqr
            # ─────────────────────────────────────────────────────────────────────

            try:
                _gandalf_was_cold = not gandalf_is_up()
            except Exception:
                pass
            if not ensure_gandalf_up(leds, pa):
                leds.show_error(); time.sleep(2); show_idle_for_mode(leds); continue
            teensy.send_command(f"MOUTH_INTENSITY:{MOUTH_INTENSITY_AWAKE}")
            _t_wake = time.time()
            _t_mono_wake = time.monotonic()
            try:
                print(f"[BENCH] t={_t_wake:.3f} stage=wake_detected trigger={'ptt' if ptt_mode else 'wake'} gandalf_was_cold={str(_gandalf_was_cold).lower()}", flush=True)
            except Exception:
                pass
            _drain_n = int(SAMPLE_RATE / CHUNK * OWW_DRAIN_SECS)
            _pre_buf = []
            for _ in range(_drain_n):
                try: _pre_buf.append(mic.read(CHUNK, exception_on_overflow=False))
                except Exception: break
            leds.show_recording(); print("[REC]  Listening...", flush=True)
            _t_mono_rec_start = time.monotonic()
            raw = b"".join(_pre_buf) + record_command(mic, ptt_mode=ptt_mode, kids_mode=state.kids_mode)
            _t_mono_rec = time.monotonic()
            arr = np.frombuffer(raw, dtype=np.int16).astype(float)
            rms = np.sqrt(np.mean(arr**2))
            print(f"[REC]  {len(raw)/2/SAMPLE_RATE:.1f}s  RMS={rms:.0f}", flush=True)
            _t_rec = time.time()
            try:
                _bench_stages["wake_to_record_start_ms"] = round((_t_mono_rec_start - _t_mono_wake) * 1000)
                _bench_stages["record_duration_ms"] = round((_t_mono_rec - _t_mono_rec_start) * 1000)
                print(f"[BENCH] t={_t_rec:.3f} stage=rec_done dur_rec={_t_rec-_t_wake:.2f} wake_to_rec_start_ms={_bench_stages['wake_to_record_start_ms']} record_duration_ms={_bench_stages['record_duration_ms']} rms={rms:.0f}", flush=True)
            except Exception:
                print(f"[BENCH] t={_t_rec:.3f} stage=rec_done dur_rec={_t_rec-_t_wake:.2f} rms={rms:.0f}", flush=True)

            # ── RMS gate + Whisper hallucination filter ────────────────────────
            if rms < 300:
                print(f"[REC]  Below RMS gate ({rms:.0f} < 300), ignoring", flush=True)
                show_idle_for_mode(leds); continue

            leds.show_thinking(); print("[STT]  Transcribing...", flush=True)
            try: text = transcribe(raw)
            except Exception as e:
                print(f"[ERR]  STT: {e}", flush=True)
                leds.show_error(); time.sleep(1); show_idle_for_mode(leds); continue

            if not text:
                print("[STT]  Empty transcript", flush=True); show_idle_for_mode(leds); continue
            print(f"[STT]  '{text}'", flush=True)
            _t_stt = time.time()
            _t_mono_stt = time.monotonic()
            _bench_transcript = text
            _snip = text[:30].replace('"', "'")
            try:
                _bench_stages["stt_ms"] = round((_t_mono_stt - _t_mono_rec) * 1000)
                print(f"[BENCH] t={_t_stt:.3f} stage=stt_done dur_stt={_t_stt-_t_rec:.2f} stt_ms={_bench_stages['stt_ms']} transcript=\"{_snip}\"", flush=True)
            except Exception:
                print(f"[BENCH] t={_t_stt:.3f} stage=stt_done dur_stt={_t_stt-_t_rec:.2f} transcript=\"{_snip}\"", flush=True)

            _text_norm = text.lower().strip().strip(".!?,;:")

            # ── STOP phrase gate (pre-router; mirrors follow-up loop) ─────────────
            # Exact match or phrase followed by space — avoids false matches on
            # "stopwatch", "quietly", "cancelled", etc.
            if any(_text_norm == phrase or _text_norm.startswith(phrase + " ")
                   for phrase in STOP_PHRASES):
                print(f"[STOP] Main-loop STOP phrase: '{text}'", flush=True)
                _stop_playback.set()
                emit_emotion(teensy, leds, "NEUTRAL")
                show_idle_for_mode(leds)
                print("[INFO] Ready.", flush=True)
                continue

            _WHISPER_HALLUCINATIONS = {
                "thank you", "thanks", "thank you very much", "thanks for watching",
                "you", "the", "bye", "bye bye", "goodbye", "see you next time",
                "please subscribe", ".", "", " ",
            }
            _WHISPER_HALLUCINATION_PATTERNS = (
                "for more information", "visit www.", "www.", ".gov", ".com",
                "subscribe to", "like and subscribe", "don't forget to",
            )
            if _text_norm in _WHISPER_HALLUCINATIONS or \
               any(_text_norm.startswith(p) or p in _text_norm for p in _WHISPER_HALLUCINATION_PATTERNS):
                print(f"[STT]  Hallucination filtered: '{text}'", flush=True)
                show_idle_for_mode(leds); continue

            # ── Intent routing ────────────────────────────────────────────────
            _result = router.classify(text, state)
            _route  = _result.route
            _bench_route = _route
            _t_mono_router = time.monotonic()
            print(f"[ROUTE] {_route}/{_result.action} conf={_result.confidence}", flush=True)
            try:
                _bench_stages["router_ms"] = round((_t_mono_router - _t_mono_stt) * 1000)
                print(f"[BENCH] stage=router_done router_ms={_bench_stages['router_ms']} route={_route}", flush=True)
            except Exception:
                pass

            # Auto-wake eyes for any route that requires interaction (not sleep/stop)
            _needs_eye_wake = (
                _route in (ROUTE_COMMAND, ROUTE_UTILITY, ROUTE_LLM)
                or (_route == ROUTE_AMBIGUOUS and _result.action not in ("SLEEP", "STOP"))
            )
            if state.eyes_sleeping and _needs_eye_wake:
                state.eyes_sleeping = False
                teensy.send_command("EYES:WAKE")
                teensy.send_command(f"MOUTH_INTENSITY:{MOUTH_INTENSITY_AWAKE}")
                print("[EYES] Eyes auto-waked by interaction", flush=True)

            if _route == ROUTE_REFLEX:
                if _result.action == "SLEEP":
                    _do_sleep(teensy, leds)
                    if _result.response:
                        try:
                            pcm_data = synthesize(_result.response)
                            leds.show_speaking(); mic.stop_stream()
                            _t_mono_play = time.monotonic()
                            try: _bench_stages["play_start_ms"] = round((_t_mono_play - _t_mono_wake) * 1000)
                            except Exception: pass
                            play_pcm_speaking(pcm_data, pa, teensy); mic.start_stream()
                            _bench_write(_bench_stages, _bench_transcript, 0, get_model(), _gandalf_was_cold, ROUTE_REFLEX, False)
                        except Exception as e:
                            print(f"[ERR]  TTS reflex sleep: {e}", flush=True)
                    show_idle_for_mode(leds); print("[INFO] Ready.", flush=True); continue
                elif _result.action == "STOP":
                    print("[STOP] Stop command received", flush=True)
                    _stop_playback.set(); emit_emotion(teensy, leds, "NEUTRAL")
                    show_idle_for_mode(leds); continue
                elif _result.action == "WAKE":
                    _do_wake(teensy, leds)
                    show_idle_for_mode(leds); print("[INFO] Ready.", flush=True); continue

            elif _route == ROUTE_COMMAND:
                if _result.action == "EYES_SLEEP":
                    if not state.eyes_sleeping:
                        state.eyes_sleeping = True
                        teensy.send_command("EYES:SLEEP")
                        teensy.send_command(f"MOUTH_INTENSITY:{MOUTH_INTENSITY_SLEEP}")
                        print("[EYES] Eyes deactivated by voice", flush=True)
                    show_idle_for_mode(leds); continue
                elif _result.action == "EYES_WAKE":
                    if state.eyes_sleeping:
                        state.eyes_sleeping = False
                        teensy.send_command("EYES:WAKE")
                        teensy.send_command(f"MOUTH_INTENSITY:{MOUTH_INTENSITY_AWAKE}")
                        print("[EYES] Eyes activated by voice", flush=True)
                    show_idle_for_mode(leds); continue
                elif _result.action in ("KIDS_ON", "KIDS_OFF"):
                    kids_reply, new_mode = handle_kids_mode_command(text)
                    if kids_reply is not None:
                        print(f"[MODE] {kids_reply}", flush=True)
                        leds.show_kids_mode_on() if new_mode else leds.show_kids_mode_off()
                        time.sleep(0.6)
                        try:
                            pcm_data = synthesize(kids_reply)
                            leds.show_speaking(); mic.stop_stream()
                            _t_mono_play = time.monotonic()
                            try: _bench_stages["play_start_ms"] = round((_t_mono_play - _t_mono_wake) * 1000)
                            except Exception: pass
                            play_pcm_speaking(pcm_data, pa, teensy); mic.start_stream()
                            _bench_write(_bench_stages, _bench_transcript, 0, get_model(), _gandalf_was_cold, ROUTE_COMMAND, False)
                        except Exception as e:
                            print(f"[ERR]  TTS mode switch: {e}", flush=True)
                    emit_emotion(teensy, leds, "NEUTRAL"); show_idle_for_mode(leds)
                    print("[INFO] Ready.", flush=True); continue
                else:
                    # Volume commands
                    vol_reply = handle_volume_command(text)
                    if vol_reply is not None:
                        print(f"[VOL]  {vol_reply}", flush=True)
                        try:
                            pcm_data = synthesize(vol_reply)
                            leds.show_speaking(); mic.stop_stream()
                            _t_mono_play = time.monotonic()
                            try: _bench_stages["play_start_ms"] = round((_t_mono_play - _t_mono_wake) * 1000)
                            except Exception: pass
                            play_pcm_speaking(pcm_data, pa, teensy); mic.start_stream()
                            _bench_write(_bench_stages, _bench_transcript, 0, get_model(), _gandalf_was_cold, ROUTE_COMMAND, False)
                        except Exception as e:
                            print(f"[ERR]  TTS vol: {e}", flush=True)
                        emit_emotion(teensy, leds, "NEUTRAL"); show_idle_for_mode(leds)
                        print("[INFO] Ready.", flush=True); continue

            elif _route == ROUTE_UTILITY:
                if _result.action == "VISION":
                    if CAMERA_ENABLED:
                        print("[CAM]  Vision trigger detected", flush=True)
                        emit_emotion(teensy, leds, "CURIOUS"); leds.show_thinking()
                        img = capture_image()
                        if img is None:
                            reply = "Sorry, I could not capture an image right now."
                        else:
                            print(f"[CAM]  Captured {len(img)//1024}KB", flush=True)
                            try:
                                reply = ask_vision(img, text)
                                print(f"[VIS]  '{reply}'", flush=True)
                            except Exception as e:
                                reply = "I had trouble processing the image."
                                print(f"[ERR]  Vision: {e}", flush=True)
                        try:
                            pcm_data = synthesize(reply)
                            leds.show_speaking(); mic.stop_stream()
                            _t_mono_play = time.monotonic()
                            try: _bench_stages["play_start_ms"] = round((_t_mono_play - _t_mono_wake) * 1000)
                            except Exception: pass
                            play_pcm_speaking(pcm_data, pa, teensy); mic.start_stream()
                            _bench_write(_bench_stages, _bench_transcript, len(reply), get_model(), _gandalf_was_cold, ROUTE_UTILITY, False)
                        except Exception as e:
                            print(f"[ERR]  TTS vision: {e}", flush=True)
                        emit_emotion(teensy, leds, "NEUTRAL"); show_idle_for_mode(leds)
                        print("[INFO] Ready.", flush=True); continue
                elif _result.response is not None:
                    print(f"[UTIL] {_result.action}: {_result.response}", flush=True)
                    try:
                        pcm_data = synthesize(_result.response)
                        leds.show_speaking(); mic.stop_stream()
                        _t_mono_play = time.monotonic()
                        try: _bench_stages["play_start_ms"] = round((_t_mono_play - _t_mono_wake) * 1000)
                        except Exception: pass
                        play_pcm_speaking(pcm_data, pa, teensy); mic.start_stream()
                        _bench_write(_bench_stages, _bench_transcript, len(_result.response), get_model(), _gandalf_was_cold, ROUTE_UTILITY, False)
                    except Exception as e:
                        print(f"[ERR]  TTS utility: {e}", flush=True)
                    emit_emotion(teensy, leds, "NEUTRAL"); show_idle_for_mode(leds)
                    print("[INFO] Ready.", flush=True); continue

            elif _route == ROUTE_AMBIGUOUS:
                if _result.action == "STOP":
                    print("[STOP] Ambiguous stop command received", flush=True)
                    _stop_playback.set(); emit_emotion(teensy, leds, "NEUTRAL")
                    show_idle_for_mode(leds); continue
                elif _result.action == "SLEEP":
                    _do_sleep(teensy, leds)
                    if _result.response:
                        try:
                            pcm_data = synthesize(_result.response)
                            leds.show_speaking(); mic.stop_stream()
                            _t_mono_play = time.monotonic()
                            try: _bench_stages["play_start_ms"] = round((_t_mono_play - _t_mono_wake) * 1000)
                            except Exception: pass
                            play_pcm_speaking(pcm_data, pa, teensy); mic.start_stream()
                            _bench_write(_bench_stages, _bench_transcript, 0, get_model(), _gandalf_was_cold, ROUTE_AMBIGUOUS, False)
                        except Exception as e:
                            print(f"[ERR]  TTS ambiguous sleep: {e}", flush=True)
                    show_idle_for_mode(leds); print("[INFO] Ready.", flush=True); continue
                # AMBIGUOUS/LLM falls through to LLM below

            # ── Streaming LLM → per-sentence TTS → overlapped playback ─────────
            # stream_ollama() yields cleaned sentence chunks (emotion on the first).
            # Each sentence is synthesized as it arrives and queued to a background
            # player that plays blobs back-to-back, so first audio starts on the
            # first sentence while later sentences are still being generated and
            # synthesized. STOP is checked per sentence dispatch, not just at end.
            _num_predict = classify_response_length(text)
            _tier = {NUM_PREDICT_SHORT: "SHORT", NUM_PREDICT_MEDIUM: "MEDIUM",
                     NUM_PREDICT_LONG: "LONG", NUM_PREDICT_MAX: "MAX"}.get(_num_predict, "CUSTOM")
            print(f"[LLM]  Streaming... (model={get_model()}, num_predict={_num_predict})", flush=True)
            _t_llm0 = time.time()
            _t_mono_llm0 = time.monotonic()
            _t_mono_llm_first = _t_mono_llm0
            _t_llm_first = _t_llm0
            try:
                _bench_stages["tier"] = _tier
                _bench_stages["num_predict"] = _num_predict
                print(f"[BENCH] t={_t_llm0:.3f} stage=llm_start tier={_tier} num_predict={_num_predict} model={get_model()} gandalf_was_cold={str(_gandalf_was_cold).lower()}", flush=True)
            except Exception:
                pass
            state.last_interaction = time.time()
            state.conversation_history.append({"role": "user", "content": text})

            reply_parts = []
            _interrupted = False
            _emotion_set = False
            _current_emotion = "NEUTRAL"
            _bench_first_chunk = True
            _tts_first_done = False

            _pcm_q = queue.Queue()
            _player_thread = None
            _player_result = {"interrupted": False}

            def _run_player(_emotion):
                _player_result["interrupted"] = play_pcm_stream(
                    _pcm_q, pa, teensy, emotion=_emotion,
                    restore_mouth_idx=MOUTH_MAP.get(_emotion, 0))

            try:
                for chunk, chunk_emotion in stream_ollama(
                    _build_messages(), get_model(), _num_predict
                ):
                    # STOP checked per sentence dispatch (UDP CMD, stop phrase, etc.)
                    if _stop_playback.is_set():
                        _interrupted = True
                        print("[STOP] Stop flag set mid-stream -- halting dispatch", flush=True)
                        break
                    if chunk_emotion is not None and not _emotion_set:
                        emit_emotion(teensy, leds, chunk_emotion)
                        _current_emotion = chunk_emotion
                        _emotion_set = True
                    if _bench_first_chunk:
                        _t_llm_first = time.time()
                        _t_mono_llm_first = time.monotonic()
                        try:
                            _bench_stages["llm_first_token_ms"] = round((_t_mono_llm_first - _t_mono_llm0) * 1000)
                            print(f"[BENCH] t={_t_llm_first:.3f} stage=llm_first_chunk dur_ttfc={_t_llm_first-_t_llm0:.2f} llm_first_token_ms={_bench_stages['llm_first_token_ms']}", flush=True)
                        except Exception:
                            print(f"[BENCH] t={_t_llm_first:.3f} stage=llm_first_chunk dur_ttfc={_t_llm_first-_t_llm0:.2f}", flush=True)
                        _bench_first_chunk = False
                    reply_parts.append(chunk)

                    # Synthesize this sentence. synthesize() does Kokoro->Piper
                    # fallback internally; it only raises if BOTH engines fail, in
                    # which case skip this sentence rather than killing the turn.
                    try:
                        _pcm = synthesize(chunk)
                    except Exception as _se:
                        print(f"[ERR]  TTS sentence skipped: {_se}", flush=True)
                        continue

                    if not _tts_first_done:
                        _t_tts = time.time()
                        _t_mono_tts = time.monotonic()
                        try:
                            _bench_stages["tts_ms"] = round((_t_mono_tts - _t_mono_llm_first) * 1000)
                            _bench_stages["engine"] = "kokoro" if KOKORO_ENABLED else "piper"
                            print(f"[BENCH] t={_t_tts:.3f} stage=tts_first dur_tts={_t_tts-_t_llm_first:.2f} tts_ms={_bench_stages['tts_ms']} engine={_bench_stages['engine']}", flush=True)
                        except Exception:
                            pass
                        _tts_first_done = True

                    # Start the player on the first synthesized sentence -- this is
                    # where first audio begins (perceived latency = play_start_ms).
                    if _player_thread is None:
                        leds.show_speaking(); mic.stop_stream()
                        teensy.send_command("EMOTION:NEUTRAL")
                        _t_mono_play = time.monotonic()
                        try:
                            _bench_stages["play_start_ms"] = round((_t_mono_play - _t_mono_wake) * 1000)
                            print(f"[BENCH] stage=play_start play_start_ms={_bench_stages['play_start_ms']} total_ms={_bench_stages['play_start_ms']}", flush=True)
                        except Exception:
                            pass
                        _player_thread = threading.Thread(
                            target=_run_player, args=(_current_emotion,), daemon=True)
                        _player_thread.start()

                    _pcm_q.put(_pcm)
            except Exception as e:
                print(f"[ERR]  LLM stream: {e}", flush=True)
                if _player_thread is not None:
                    _pcm_q.put(None)
                    _player_thread.join(timeout=30)
                    _interrupted = _player_result["interrupted"]
                else:
                    leds.show_error(); time.sleep(1)
                    show_idle_for_mode(leds); continue

            if not _emotion_set:
                emit_emotion(teensy, leds, "NEUTRAL")

            reply = " ".join(reply_parts).strip()
            print(f"[LLM]  '{reply}'", flush=True)
            _t_llm1 = time.time()
            _t_mono_llm1 = time.monotonic()
            try:
                _bench_stages["llm_total_ms"] = round((_t_mono_llm1 - _t_mono_llm0) * 1000)
                print(f"[BENCH] t={_t_llm1:.3f} stage=llm_done dur_llm={_t_llm1-_t_llm0:.2f} llm_total_ms={_bench_stages['llm_total_ms']} reply_chars={len(reply)}", flush=True)
            except Exception:
                print(f"[BENCH] t={_t_llm1:.3f} stage=llm_done dur_llm={_t_llm1-_t_llm0:.2f} reply_chars={len(reply)}", flush=True)

            # Signal end-of-stream and wait for overlapped playback to drain.
            if _player_thread is not None:
                _pcm_q.put(None)
                _player_thread.join()
                _interrupted = _player_result["interrupted"] or _interrupted
            elif not reply:
                print("[LLM]  Empty reply -- nothing to play", flush=True)

            _rpqr_state["t_last_spoke"] = time.time()
            _bench_interrupted = _interrupted
            try:
                _t_audio = time.time()
                print(f"[BENCH] t={_t_audio:.3f} stage=audio_done dur_total={_t_audio-_t_wake:.2f}", flush=True)
            except Exception:
                pass
            emit_emotion(teensy, leds, _current_emotion)
            _bench_write(_bench_stages, _bench_transcript, len(reply), get_model(), _gandalf_was_cold, _bench_route, _interrupted, emotion=_current_emotion)

            state.conversation_history.append({"role": "assistant", "content": reply})
            if len(state.conversation_history) > 20:
                state.conversation_history.pop(0); state.conversation_history.pop(0)

            if button_pressed(): time.sleep(0.4)

            # ── Follow-up loop ─────────────────────────────────────────────────
            _followup_turns = 0
            while implies_followup(reply) and _followup_turns < FOLLOWUP_MAX_TURNS and not _interrupted:
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
                # Gate: known Whisper hallucinations (brief phrases Whisper hallucinates when silent)
                if _text_norm in _WHISPER_HALLUCINATIONS:
                    print(f"[FLWP] Hallucination filtered: '{text}'", flush=True); break
                # Gate: URL/spam hallucination patterns
                if any(p in _text_norm for p in ("www.", ".gov", ".com", ".org",
                       "for more information", "subscribe", "don't forget")):
                    print(f"[FLWP] Hallucination filtered: '{text}'", flush=True); break
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
                        _followup_predict = classify_response_length(text)
                        print(f"[LLM]  Thinking... (model={get_model()}, num_predict={_followup_predict})", flush=True)
                        try: reply, emotion = ask_ollama(text, num_predict=_followup_predict)
                        except Exception as e: print(f"[ERR]  LLM follow-up: {e}", flush=True); break
                        print(f"[LLM]  '{reply}'", flush=True)
                emit_emotion(teensy, leds, emotion)
                print("[TTS]  Synthesizing...", flush=True)
                try: pcm_data = synthesize(reply)
                except Exception as e: print(f"[ERR]  TTS follow-up: {e}", flush=True); break
                leds.show_speaking(); mic.stop_stream()
                _interrupted = play_pcm_speaking(pcm_data, pa, teensy, emotion=emotion,
                                                 restore_mouth_idx=MOUTH_MAP.get(emotion, 0))
                _rpqr_state["t_last_spoke"] = time.time()
                if button_pressed(): time.sleep(0.4)
                if _interrupted:
                    print("[STOP] Playback interrupted mid-follow-up", flush=True); break

            try:
                mic.start_stream()
            except OSError:
                pass
            # Discard mic audio captured during/after TTS playback to prevent
            # speaker echo from triggering a false wake on the next listen cycle.
            _post_drain_n = int(SAMPLE_RATE / CHUNK * OWW_POST_PLAY_DRAIN_SECS)
            for _ in range(_post_drain_n):
                try:
                    mic.read(CHUNK, exception_on_overflow=False)
                except Exception:
                    break
            emit_emotion(teensy, leds, "NEUTRAL")
            teensy.send_command(f"MOUTH_INTENSITY:{MOUTH_INTENSITY_IDLE}")
            show_idle_for_mode(leds)
            if in_sleep_window():
                _do_sleep(teensy, leds)
                print("[SLEEP] Returned to sleep (sleep window active)", flush=True)
            print("[INFO] Ready.", flush=True)

    except KeyboardInterrupt:
        print("\n[INFO] Shutting down.", flush=True)
    finally:
        flush_conversation_log(reason="shutdown")
        emit_emotion(teensy, leds, "NEUTRAL"); teensy.close()
        leds.close(); gpio_cleanup()
        mic.stop_stream(); mic.close(); pa.terminate()
        if oww_proc is not None:
            oww_proc.terminate()


if __name__ == "__main__":
    main()

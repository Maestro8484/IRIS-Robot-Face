#!/usr/bin/env python3
"""
assistant.py - Pi4 IRIS voice assistant
Wake: wyoming-openwakeword hey_jarvis (:10400) OR button press (GPIO17)
STT:  Wyoming Whisper  @ 192.168.1.3:10300
LLM:  Ollama           @ 192.168.1.3:11434 (streaming)
TTS:  Chatterbox       @ 192.168.1.3:8004 (primary)
Audio: wm8960-soundcard (dynamic card detection)
LEDs: 3x APA102 via SPI -- status indicator
Eyes: Teensy face via /dev/ttyACM0
"""

import json, os, re, socket, subprocess, sys, threading, time
import numpy as np
import pyaudio
import requests
import warnings; warnings.filterwarnings("ignore")

from core.config import *
from hardware.teensy_bridge import TeensyBridge
from hardware.led import APA102
from hardware.io import setup_button, button_pressed, gpio_cleanup
from hardware.audio_io import (
    _find_mic_device_index, get_volume, set_volume, handle_volume_command,
    play_pcm, play_pcm_speaking, play_beep, play_double_beep,
    record_command, _stop_playback, STOP_PHRASES, FOLLOWUP_DISMISSALS,
)
from services.wyoming import wy_send, read_line
from services.stt import transcribe
from services.tts import synthesize, spoken_numbers
from services.llm import extract_emotion_from_reply, clean_llm_reply, stream_ollama
from services.vision import capture_image, is_vision_trigger, ask_vision
from services.wakeword import wait_for_wakeword_or_button
from state.state_manager import state


def get_model() -> str:
    return OLLAMA_MODEL_KIDS if state.kids_mode else OLLAMA_MODEL_ADULT


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
                        print(f"[CMD] -> teensy: {cmd}", flush=True)
                        teensy.send_command(cmd)
                        if cmd == "EYES:SLEEP":
                            state.eyes_sleeping = True
                            open("/tmp/iris_sleep_mode", "w").close()
                            leds.show_sleep()
                            lvl = globals().get("MOUTH_INTENSITY_SLEEP", 1)
                            teensy.send_command(f"MOUTH_INTENSITY:{lvl}")
                        elif cmd == "EYES:WAKE":
                            state.eyes_sleeping = False
                            try: os.remove("/tmp/iris_sleep_mode")
                            except FileNotFoundError: pass
                            show_idle_for_mode(leds)
                            lvl = globals().get("MOUTH_INTENSITY_AWAKE", 8)
                            teensy.send_command(f"MOUTH_INTENSITY:{lvl}")
                except Exception as e:
                    print(f"[CMD] Listener error: {e}", flush=True)
    threading.Thread(target=_listener, daemon=True).start()


def emit_emotion(teensy, leds, emotion: str):
    """Send emotion to Teensy eyes AND sync LED color in one call."""
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


def ask_ollama(text):
    """
    Blocking LLM query. Used for followup loop and vision path.
    Returns (reply, emotion) tuple.
    """
    state.last_interaction = time.time()
    state.conversation_history.append({"role": "user", "content": text})
    r = requests.post(
        f"http://{GANDALF}:{OLLAMA_PORT}/api/chat",
        json={"model": get_model(), "messages": _build_messages(),
              "stream": False, "options": {"num_predict": NUM_PREDICT}},
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


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    leds = APA102(NUM_LEDS)
    setup_button()
    from core.config import SPEAKER_VOLUME as _startup_vol
    set_volume(_startup_vol)
    print(f"[VOL]  Startup volume: {_startup_vol}/127 ({round(_startup_vol/127*100)}%)", flush=True)
    ctx_thread = threading.Thread(target=_context_watchdog, daemon=True); ctx_thread.start()
    teensy = TeensyBridge(TEENSY_PORT, TEENSY_BAUD)
    start_cmd_listener(teensy, leds)

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

            # Sleep mode check
            if os.path.exists('/tmp/iris_sleep_mode'):
                print('[SLEEP] Wakeword during sleep -- waking IRIS', flush=True)
                os.remove('/tmp/iris_sleep_mode')
                state.eyes_sleeping = False
                teensy.send_command('EYES:WAKE')
                teensy.send_command('MOUTH:0')
                if not ensure_gandalf_up(leds):
                    leds.show_error(); time.sleep(2); show_idle_for_mode(leds); continue
                subprocess.run([
                    'bash', '-c',
                    'echo "Good morning." | /usr/local/bin/piper'
                    ' --model /home/pi/piper/en_US-ryan-high.onnx'
                    ' --output_raw | aplay -r 22050 -f S16_LE -t raw -'
                ])
                show_idle_for_mode(leds); continue

            if not ensure_gandalf_up(leds):
                leds.show_error(); time.sleep(2); show_idle_for_mode(leds); continue

            play_beep(pa)
            _drain_n = int(SAMPLE_RATE / CHUNK * 0.15)
            _pre_buf = []
            for _ in range(_drain_n):
                try: _pre_buf.append(mic.read(CHUNK, exception_on_overflow=False))
                except Exception: break
            leds.show_recording(); print("[REC]  Listening...", flush=True)
            raw = b"".join(_pre_buf) + record_command(mic, ptt_mode=ptt_mode, kids_mode=state.kids_mode)
            arr = np.frombuffer(raw, dtype=np.int16).astype(float)
            rms = np.sqrt(np.mean(arr**2))
            print(f"[REC]  {len(raw)/2/SAMPLE_RATE:.1f}s  RMS={rms:.0f}", flush=True)

            # ── RMS gate + Whisper hallucination filter ────────────────────────
            if rms < 700:
                print(f"[REC]  Below RMS gate ({rms:.0f} < 700), ignoring", flush=True)
                show_idle_for_mode(leds); continue

            leds.show_thinking(); print("[STT]  Transcribing...", flush=True)
            try: text = transcribe(raw)
            except Exception as e:
                print(f"[ERR]  STT: {e}", flush=True)
                leds.show_error(); time.sleep(1); show_idle_for_mode(leds); continue

            if not text:
                print("[STT]  Empty transcript", flush=True); show_idle_for_mode(leds); continue
            print(f"[STT]  '{text}'", flush=True)

            _text_norm = text.lower().strip().strip(".!?,;:")
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

            if any(_text_norm == phrase or _text_norm.startswith(phrase)
                   for phrase in STOP_PHRASES):
                print("[STOP] Stop command received", flush=True)
                _stop_playback.set(); emit_emotion(teensy, leds, "NEUTRAL")
                show_idle_for_mode(leds); continue

            # ── Eyes sleep/wake voice commands ─────────────────────────────────
            _tnorm = text.lower().strip().strip(".!?,;:")
            if any(_tnorm == p or _tnorm.startswith(p) for p in EYES_SLEEP_TRIGGERS):
                if not state.eyes_sleeping:
                    state.eyes_sleeping = True
                    teensy.send_command("EYES:SLEEP")
                    lvl = globals().get("MOUTH_INTENSITY_SLEEP", 1)
                    teensy.send_command(f"MOUTH_INTENSITY:{lvl}")
                    print("[EYES] Eyes deactivated by voice", flush=True)
                show_idle_for_mode(leds); continue

            if any(_tnorm == p or _tnorm.startswith(p) for p in EYES_WAKE_TRIGGERS):
                if state.eyes_sleeping:
                    state.eyes_sleeping = False
                    teensy.send_command("EYES:WAKE")
                    lvl = globals().get("MOUTH_INTENSITY_AWAKE", 8)
                    teensy.send_command(f"MOUTH_INTENSITY:{lvl}")
                    print("[EYES] Eyes activated by voice", flush=True)
                show_idle_for_mode(leds); continue

            if state.eyes_sleeping:
                state.eyes_sleeping = False
                teensy.send_command("EYES:WAKE")
                lvl = globals().get("MOUTH_INTENSITY_AWAKE", 8)
                teensy.send_command(f"MOUTH_INTENSITY:{lvl}")
                print("[EYES] Eyes auto-waked by interaction", flush=True)

            kids_reply, new_mode = handle_kids_mode_command(text)
            if kids_reply is not None:
                print(f"[MODE] {kids_reply}", flush=True)
                leds.show_kids_mode_on() if new_mode else leds.show_kids_mode_off()
                time.sleep(0.6)
                try:
                    pcm_data = synthesize(kids_reply)
                    leds.show_speaking(); mic.stop_stream(); play_pcm_speaking(pcm_data, pa, teensy); mic.start_stream()
                except Exception as e: print(f"[ERR]  TTS mode switch: {e}", flush=True)
                emit_emotion(teensy, leds, "NEUTRAL"); show_idle_for_mode(leds)
                print("[INFO] Ready.", flush=True); continue

            time_reply = handle_time_command(text)
            if time_reply is not None:
                print(f"[TIME] {time_reply}", flush=True)
                try:
                    pcm_data = synthesize(time_reply)
                    leds.show_speaking(); mic.stop_stream(); play_pcm_speaking(pcm_data, pa, teensy); mic.start_stream()
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
                    leds.show_speaking(); mic.stop_stream(); play_pcm_speaking(pcm_data, pa, teensy); mic.start_stream()
                except Exception as e: print(f"[ERR]  TTS vision: {e}", flush=True)
                emit_emotion(teensy, leds, "NEUTRAL"); show_idle_for_mode(leds)
                print("[INFO] Ready.", flush=True); continue

            vol_reply = handle_volume_command(text)
            if vol_reply is not None:
                print(f"[VOL]  {vol_reply}", flush=True)
                try:
                    pcm_data = synthesize(vol_reply)
                    leds.show_speaking(); mic.stop_stream(); play_pcm_speaking(pcm_data, pa, teensy); mic.start_stream()
                except Exception as e: print(f"[ERR]  TTS vol: {e}", flush=True)
                emit_emotion(teensy, leds, "NEUTRAL"); show_idle_for_mode(leds)
                print("[INFO] Ready.", flush=True); continue

            # ── Streaming LLM (emotion early) + single TTS call ───────────────
            print(f"[LLM]  Streaming... (model={get_model()})", flush=True)
            state.last_interaction = time.time()
            state.conversation_history.append({"role": "user", "content": text})

            reply_parts = []
            _interrupted = False
            _emotion_set = False

            try:
                for chunk, chunk_emotion in stream_ollama(
                    _build_messages(), get_model(), NUM_PREDICT
                ):
                    if chunk_emotion is not None and not _emotion_set:
                        emit_emotion(teensy, leds, chunk_emotion)
                        _emotion_set = True
                    reply_parts.append(chunk)
            except Exception as e:
                print(f"[ERR]  LLM stream: {e}", flush=True)
                leds.show_error(); time.sleep(1)
                show_idle_for_mode(leds); continue

            if not _emotion_set:
                emit_emotion(teensy, leds, "NEUTRAL")

            reply = " ".join(reply_parts).strip()
            print(f"[LLM]  '{reply}'", flush=True)

            print("[TTS]  Synthesizing...", flush=True)
            try:
                pcm_data = synthesize(reply)
            except Exception as e:
                print(f"[ERR]  TTS: {e}", flush=True)
                leds.show_error(); time.sleep(1)
                show_idle_for_mode(leds); continue

            leds.show_speaking(); mic.stop_stream()
            _interrupted = play_pcm_speaking(pcm_data, pa, teensy)

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
                # Gate: < 3 words is noise/hallucination
                if len(_text_norm.split()) < 3:
                    print(f"[FLWP] Short transcript filtered: '{text}'", flush=True); break
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
                        print(f"[LLM]  Thinking... (model={get_model()})", flush=True)
                        try: reply, emotion = ask_ollama(text)
                        except Exception as e: print(f"[ERR]  LLM follow-up: {e}", flush=True); break
                        print(f"[LLM]  '{reply}'", flush=True)
                emit_emotion(teensy, leds, emotion)
                print("[TTS]  Synthesizing...", flush=True)
                try: pcm_data = synthesize(reply)
                except Exception as e: print(f"[ERR]  TTS follow-up: {e}", flush=True); break
                leds.show_speaking(); mic.stop_stream()
                _interrupted = play_pcm_speaking(pcm_data, pa, teensy)
                if button_pressed(): time.sleep(0.4)
                if _interrupted:
                    print("[STOP] Playback interrupted mid-follow-up", flush=True); break

            try:
                mic.start_stream()
            except OSError:
                pass
            emit_emotion(teensy, leds, "NEUTRAL")
            show_idle_for_mode(leds)
            print("[INFO] Ready.", flush=True)

    except KeyboardInterrupt:
        print("\n[INFO] Shutting down.", flush=True)
    finally:
        flush_conversation_log(reason="shutdown")
        emit_emotion(teensy, leds, "NEUTRAL"); teensy.close()
        leds.close(); gpio_cleanup()
        mic.stop_stream(); mic.close(); pa.terminate()
        oww_proc.terminate()


if __name__ == "__main__":
    main()

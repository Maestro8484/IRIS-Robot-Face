#!/usr/bin/env python3
"""IRIS Web Config Panel — Flask server (Pi4)."""
import json, os, subprocess, time, wave, tempfile, threading, re as _re, glob as _glob
import requests
from flask import Flask, request, jsonify
import sys; sys.path.insert(0, "/home/pi")
from core.config import CMD_PORT

app = Flask(__name__)

# ── Log parsing — module-level constants ───────────────────────────────────────
_SD_LOG_DIR   = "/media/root-ro/home/pi/logs"
_SD_MONTH_MAP = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,
                 'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}

_BENCH_RE     = _re.compile(r'\[BENCH\](.*)')
_TS_RE        = _re.compile(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})')
# Fixed: journal uses python3[PID]: not assistant[PID]:
_MSG_RE       = _re.compile(r'(?:python3|assistant|iris[\-_]web)\[\d+\]:\s*(.*)')
_TAG_RE       = _re.compile(
    r'\[(INFO|ERR|WARN|STT|LLM|TTS|ROUTE|WAKEWORD|STOP|CMD|GESTURE)\](.*)')
_GESTURE_RE   = _re.compile(r'\[GESTURE\]\s+gesture=(\S+)\s+action=(\S+)')
_BASE_GEST_RE = _re.compile(r'\[BASE\]\s+(VOL[+\-]|STOP|LISTEN)\s*$')
# SD daily log line: "May 22 17:30:00 pi4-satellite python3[1139]: message"
_SD_LINE_RE   = _re.compile(
    r'^(\w{3})\s+(\d{1,2})\s+(\d{2}):(\d{2}):(\d{2})\s+\S+\s+'
    r'(?:python3|assistant|iris[\-_]web)\[\d+\]:\s*(.*)')
_DRIFT_SIGNALS = ("certainly", "of course", "i'd be happy", "as an ai",
                  "great question", "i cannot help with", "i apologize",
                  "i'm sorry, but", "as an assistant", "i understand that")

def _kv(s):
    d = {}
    for p in s.split():
        if '=' in p:
            k, _, v = p.partition('=')
            d[k] = v.strip('"\'')
    return d

def _parse_event_msg(ts, ts_s, msg):
    """Parse a log message into an event dict, or return None if not interesting."""
    bm = _BENCH_RE.search(msg)
    if bm:
        kv    = _kv(bm.group(1))
        stage = kv.get("stage", "")
        ev    = {"t": ts, "ts": ts_s, "detail": ""}
        if stage == "wake_detected":
            ev.update(cat="wakeword", msg="Wakeword detected",
                      detail=f'trigger={kv.get("trigger","?")}')
        elif stage == "stt_done":
            tx = kv.get("transcript", "")
            ev.update(cat="stt", msg=f'Heard: "{tx}"',
                      detail=f'STT {kv.get("dur_stt","?")}s')
        elif stage == "llm_start":
            ev.update(cat="route", msg=f'→ LLM  tier={kv.get("tier","?")}',
                      detail=f'np={kv.get("num_predict","?")}')
        elif stage == "llm_first_chunk":
            ev.update(cat="llm", msg="First LLM chunk",
                      detail=f'ttfc={kv.get("dur_ttfc","?")}s')
        elif stage == "llm_done":
            ev.update(cat="llm", msg="LLM response complete",
                      detail=f'{kv.get("dur_llm","?")}s')
        elif stage == "tts_done":
            ev.update(cat="tts", msg="TTS synthesized",
                      detail=f'{kv.get("dur_tts","?")}s')
        elif stage == "audio_done":
            ev.update(cat="tts", msg=f'Spoken — total {kv.get("dur_total","?")}s')
        elif stage == "ollama_stats":
            ev.update(cat="llm",
                      msg=f'Tokens: eval={kv.get("eval_tokens","?")} prompt={kv.get("prompt_tokens","?")}')
        else:
            return None
        return ev

    gm = _GESTURE_RE.search(msg)
    if gm:
        gesture, action = gm.group(1), gm.group(2)
        label = f"{gesture} -> {action}" if action != gesture else gesture
        return {"t": ts, "ts": ts_s, "cat": "gesture",
                "msg": f"Gesture: {label}", "detail": ""}

    bsm = _BASE_GEST_RE.search(msg)
    if bsm:
        return {"t": ts, "ts": ts_s, "cat": "gesture",
                "msg": f"Gesture: {bsm.group(1)}", "detail": ""}

    tm = _TAG_RE.search(msg)
    if tm:
        tag     = tm.group(1)
        content = tm.group(2).strip()
        cat_map = {"INFO": "info", "ERR": "error", "WARN": "warn", "STT": "stt",
                   "LLM": "llm", "TTS": "tts", "ROUTE": "route",
                   "WAKEWORD": "wakeword", "STOP": "stop", "CMD": "cmd",
                   "GESTURE": "gesture"}
        cat = cat_map.get(tag, "info")
        if any(p in content.lower() for p in _DRIFT_SIGNALS):
            return {"t": ts, "ts": ts_s, "cat": "drift",
                    "msg": "DRIFT: boilerplate/formal opener",
                    "detail": content[:120]}
        if tag in ("STOP", "INFO") and ("stop phrase" in content.lower()
                   or "stop gate" in content.lower() or "[stop]" in content.lower()):
            cat = "stop"
        return {"t": ts, "ts": ts_s, "cat": cat,
                "msg": content[:140], "detail": ""}

    lower = msg.lower()
    if "stop phrase" in lower or "stop gate" in lower:
        return {"t": ts, "ts": ts_s, "cat": "stop",
                "msg": msg[:140], "detail": ""}
    return None

def _sd_events(n_days=3650):
    """Parse SD daily assistant log files into event dicts (history across reboots)."""
    results = []
    files = sorted(_glob.glob(os.path.join(_SD_LOG_DIR, "iris-????????.log")))[-n_days:]
    for fpath in files:
        fname = os.path.basename(fpath)
        try:
            year = int(fname[5:9])
        except (ValueError, IndexError):
            continue
        try:
            with open(fpath, errors="ignore") as f:
                for line in f:
                    m = _SD_LINE_RE.match(line.rstrip())
                    if not m:
                        continue
                    mon_s, day_s, hh, mm, ss, msg = m.groups()
                    mo = _SD_MONTH_MAP.get(mon_s, 0)
                    if not mo:
                        continue
                    try:
                        ts   = f"{year}-{mo:02d}-{int(day_s):02d}T{hh}:{mm}:{ss}"
                        ts_s = f"{hh}:{mm}:{ss}"
                    except Exception:
                        continue
                    ev = _parse_event_msg(ts, ts_s, msg.strip())
                    if ev:
                        results.append(ev)
        except Exception:
            continue
    return results

GANDALF      = "192.168.1.3"
OLLAMA_PORT  = 11434
TEENSY_PORT  = "/dev/ttyACM0"
TEENSY_BAUD  = 115200
KOKORO_URL = "http://192.168.1.3:8004"
CONFIG_FILE  = "/home/pi/iris_config.json"
SD_CONFIG    = "/media/root-ro/home/pi/iris_config.json"
HTML_FILE    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "iris_web.html")
SLEEP_FLAG   = "/tmp/iris_sleep_mode"

# ── helpers ────────────────────────────────────────────────────────────────────
def read_cfg():
    try:
        with open(CONFIG_FILE) as f: return json.load(f)
    except Exception: return {}

def write_cfg(patch):
    cfg = read_cfg(); cfg.update(patch)
    with open(CONFIG_FILE, "w") as f: json.dump(cfg, f, indent=2)

def cpu_temp():
    try: return round(int(open("/sys/class/thermal/thermal_zone0/temp").read()) / 1000.0, 1)
    except Exception: return 0.0

def uptime_str():
    try:
        s = float(open("/proc/uptime").read().split()[0])
        return f"{int(s//3600)}h {int((s%3600)//60)}m"
    except Exception: return "?"

def send_teensy(cmd):
    """Forward command to assistant.py via UDP -- it owns the serial port."""
    try:
        import socket as _socket
        with _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM) as s:
            s.sendto((cmd.strip() + "\n").encode(), ("127.0.0.1", CMD_PORT))
        return True
    except Exception as e:
        print(f"[WEB] Teensy UDP: {e}"); return False

def _sd_synced():
    """Return True if iris_config.json in RAM matches the SD card copy."""
    try:
        r = subprocess.run(
            ["bash", "-c",
             f"md5sum {CONFIG_FILE} {SD_CONFIG} 2>/dev/null | awk '{{print $1}}' | sort -u | wc -l"],
            capture_output=True, text=True, timeout=5)
        return r.stdout.strip() == "1"
    except Exception:
        return False

# ── TTS playback (async, non-blocking) ────────────────────────────────────────
_speak_lock = threading.Lock()

def _speak_worker(text: str, cfg: dict):
    """Synthesize via Kokoro direct (reads voice/speed from cfg); Piper fallback."""
    with _speak_lock:
        pcm = None
        try:
            import miniaudio
            voice   = cfg.get("KOKORO_VOICE", "bm_lewis")
            speed   = float(cfg.get("KOKORO_SPEED", 1.0))
            payload = {"model": "kokoro", "input": text, "voice": voice,
                       "response_format": "wav", "speed": speed}
            resp = requests.post(f"{KOKORO_URL}/v1/audio/speech", json=payload, timeout=30)
            resp.raise_for_status()
            decoded = miniaudio.decode(resp.content,
                                       output_format=miniaudio.SampleFormat.SIGNED16,
                                       nchannels=1, sample_rate=48000)
            pcm = bytes(decoded.samples)
            print(f"[WEB-TTS] Kokoro OK {len(pcm)}b voice={voice}", flush=True)
        except Exception as e:
            print(f"[WEB-TTS] Kokoro failed ({e}), falling back to Piper", flush=True)
            try:
                from services.tts import synthesize
                pcm = synthesize(text)
            except Exception as e2:
                print(f"[WEB-TTS] Piper fallback failed: {e2}", flush=True)
        if not pcm:
            return
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wav_path = f.name
            with wave.open(wav_path, "wb") as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(48000)
                wf.writeframes(pcm)
            subprocess.run(["aplay", "-q", wav_path])
            os.unlink(wav_path)
            print(f"[WEB-TTS] played {len(pcm)}b PCM", flush=True)
        except Exception as e:
            print(f"[WEB-TTS] playback error: {e}", flush=True)

def speak_async(text: str, cfg: dict):
    threading.Thread(target=_speak_worker, args=(text, cfg), daemon=True).start()

# ── routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    with open(HTML_FILE) as f: return f.read()

@app.route("/api/status")
def api_status():
    running = subprocess.run(["systemctl","is-active","assistant"],
                             capture_output=True, text=True).stdout.strip() == "active"
    return jsonify(cpu_temp=cpu_temp(), running=running, uptime=uptime_str(),
                   sleeping=os.path.exists(SLEEP_FLAG))

@app.route("/api/config", methods=["GET","POST"])
def api_config():
    if request.method == "POST":
        write_cfg(request.get_json(force=True)); return jsonify(ok=True)
    # Return all overridable defaults merged with current iris_config.json overrides
    # so web UI form fields always show the current effective value.
    try:
        import core.config as _cc
        merged = {k: getattr(_cc, k) for k in _cc._OVERRIDABLE if hasattr(_cc, k)}
    except Exception:
        merged = {}
    merged.update(read_cfg())
    return jsonify(merged)

@app.route("/api/teensy", methods=["POST"])
def api_teensy():
    cmd = request.get_json(force=True).get("cmd","")
    return jsonify(ok=send_teensy(cmd), sent=cmd)

@app.route("/api/sleep_state")
def api_sleep_state():
    return jsonify(sleeping=os.path.exists(SLEEP_FLAG))

@app.route("/api/sleep", methods=["POST"])
def api_sleep():
    send_teensy("EYES:SLEEP")
    ok = send_teensy("MOUTH:8")
    send_teensy("MOUTH_INTENSITY:1")
    open(SLEEP_FLAG, "w").close()
    return jsonify(ok=ok, sleeping=True)

@app.route("/api/wake", methods=["POST"])
def api_wake():
    send_teensy("EYES:WAKE")
    ok = send_teensy("MOUTH:0")
    send_teensy("MOUTH_INTENSITY:8")
    if os.path.exists(SLEEP_FLAG): os.remove(SLEEP_FLAG)
    return jsonify(ok=ok, sleeping=False)

_SLEEP_CFG_KEYS = {
    "speed":          "SLEEP_ANIM_SPEED",
    "starBrightMin":  "SLEEP_ANIM_STAR_BRIGHT_MIN",
    "starBrightMax":  "SLEEP_ANIM_STAR_BRIGHT_MAX",
    "starTwinkleAmp": "SLEEP_ANIM_STAR_TWINKLE",
    "shootCount":     "SLEEP_ANIM_SHOOT_COUNT",
    "shootSpeed":     "SLEEP_ANIM_SHOOT_SPEED",
    "shootLen":       "SLEEP_ANIM_SHOOT_LEN",
    "shootBright":    "SLEEP_ANIM_SHOOT_BRIGHT",
    "warpCount":      "SLEEP_ANIM_WARP_COUNT",
    "warpSpeed":      "SLEEP_ANIM_WARP_SPEED",
    "warpBright":     "SLEEP_ANIM_WARP_BRIGHT",
    "moonR":          "SLEEP_ANIM_MOON_R",
    "moonDrift":      "SLEEP_ANIM_MOON_DRIFT",
    "saturnR":        "SLEEP_ANIM_SATURN_R",
    "saturnDrift":    "SLEEP_ANIM_SATURN_DRIFT",
    "nebulaAlpha":    "SLEEP_ANIM_NEBULA_ALPHA",
    "waveAmp0":       "SLEEP_ANIM_WAVE_AMP0",
    "waveAmp1":       "SLEEP_ANIM_WAVE_AMP1",
    "waveAmp2":       "SLEEP_ANIM_WAVE_AMP2",
    "waveOscAmp":     "SLEEP_ANIM_WAVE_OSC_AMP",
    "mouthPulseAlpha":"SLEEP_ANIM_MOUTH_PULSE_A",
    "zzzAlpha0":      "SLEEP_ANIM_ZZZ_ALPHA0",
    "zzzAlpha1":      "SLEEP_ANIM_ZZZ_ALPHA1",
    "zzzAlpha2":      "SLEEP_ANIM_ZZZ_ALPHA2",
}

@app.route("/api/sleep_cfg", methods=["GET","POST"])
def api_sleep_cfg():
    if request.method == "POST":
        patch = request.get_json(force=True) or {}
        # Map short key names to SLEEP_ANIM_* config keys and write
        cfg_patch = {}
        for short_key, val in patch.items():
            cfg_key = _SLEEP_CFG_KEYS.get(short_key)
            if cfg_key:
                cfg_patch[cfg_key] = val
        if cfg_patch:
            write_cfg(cfg_patch)
        return jsonify(ok=True)
    # GET: return current values keyed by short names
    try:
        import core.config as _cc
        live = read_cfg()
        result = {}
        for short_key, cfg_key in _SLEEP_CFG_KEYS.items():
            result[short_key] = live.get(cfg_key, getattr(_cc, cfg_key, None))
        return jsonify(result)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/logs")
def api_logs():
    # 1. Current journalctl (live, current boot — last 1000 lines)
    try:
        raw = subprocess.check_output(
            ["journalctl", "-u", "assistant", "-n", "1000", "--no-pager", "--output=short-iso"],
            text=True, stderr=subprocess.DEVNULL).strip().splitlines()
    except Exception as e:
        raw = [f"ERR journalctl: {e}"]

    events = []
    for line in raw:
        ts_m  = _TS_RE.match(line)
        ts    = ts_m.group(1) if ts_m else ""
        ts_s  = ts[11:19] if len(ts) >= 19 else ""
        msg_m = _MSG_RE.search(line)
        msg   = msg_m.group(1).strip() if msg_m else ""
        if not msg:
            continue
        ev = _parse_event_msg(ts, ts_s, msg)
        if ev:
            events.append(ev)

    # 2. iris_intent.log
    try:
        with open("/home/pi/logs/iris_intent.log", encoding="utf-8") as f:
            intent_lines = [l.rstrip() for l in f.readlines()[-80:] if l.strip()]
        for il in intent_lines:
            lower = il.lower()
            ts_m2 = _TS_RE.search(il)
            ts2   = ts_m2.group(1) if ts_m2 else ""
            ts2_s = ts2[11:19] if len(ts2) >= 19 else ""
            if any(p in lower for p in _DRIFT_SIGNALS):
                cat = "drift"
            elif "stop" in lower or "reflex" in lower:
                cat = "stop"
            elif "err" in lower:
                cat = "error"
            else:
                cat = "route"
            events.append({"t": ts2, "ts": ts2_s, "cat": cat,
                            "msg": il[:200], "detail": ""})
    except Exception:
        pass

    # 3. SD daily log files — persistent history across reboots (30 days)
    events.extend(_sd_events())

    # 4. Deduplicate by (timestamp[:19], msg[:50]), sort, cap at 500
    seen, merged = set(), []
    for ev in events:
        key = (ev.get("t", "")[:19], ev.get("msg", "")[:50])
        if key not in seen:
            seen.add(key)
            merged.append(ev)
    merged.sort(key=lambda e: e.get("t", ""))
    return jsonify(events=merged[-500:])


@app.route("/api/gesture_log")
def api_gesture_log():
    """Return recent gesture events from SD history + current journal."""
    all_evs = []
    for ev in _sd_events():
        if ev.get("cat") == "gesture":
            all_evs.append(ev)
    try:
        raw = subprocess.check_output(
            ["journalctl", "-u", "assistant", "-n", "500", "--no-pager", "--output=short-iso"],
            text=True, stderr=subprocess.DEVNULL).strip().splitlines()
    except Exception:
        raw = []
    for line in raw:
        ts_m  = _TS_RE.match(line)
        ts    = ts_m.group(1) if ts_m else ""
        ts_s  = ts[11:19] if len(ts) >= 19 else ""
        msg_m = _MSG_RE.search(line)
        msg   = msg_m.group(1).strip() if msg_m else ""
        if not msg:
            continue
        ev = _parse_event_msg(ts, ts_s, msg)
        if ev and ev.get("cat") == "gesture":
            all_evs.append(ev)
    seen, result = set(), []
    for ev in all_evs:
        key = (ev.get("t", "")[:19], ev.get("msg", "")[:50])
        if key not in seen:
            seen.add(key)
            result.append(ev)
    result.sort(key=lambda e: e.get("t", ""))
    return jsonify(events=result[-200:])


_KOKORO_FALLBACK_VOICES = [
    "af_alloy", "af_bella", "af_heart", "af_jessica", "af_nicole", "af_nova",
    "af_sarah", "af_sky", "am_adam", "am_echo", "am_eric", "am_liam",
    "am_michael", "am_onyx", "bf_alice", "bf_emma", "bf_isabella",
    "bm_daniel", "bm_fable", "bm_george", "bm_lewis", "bm_myles",
]

@app.route("/api/kokoro_voices")
def api_kokoro_voices():
    try:
        r = requests.get(f"{KOKORO_URL}/v1/voices", timeout=5)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            voices = data
        elif isinstance(data, dict):
            voices = data.get("voices", data.get("data", _KOKORO_FALLBACK_VOICES))
        else:
            voices = _KOKORO_FALLBACK_VOICES
        return jsonify(voices=voices)
    except Exception as e:
        return jsonify(voices=_KOKORO_FALLBACK_VOICES, error=str(e))

@app.route("/api/restart", methods=["POST"])
def api_restart():
    subprocess.Popen(["sudo","systemctl","restart","assistant"]); return jsonify(ok=True)

@app.route("/api/vram")
def api_vram():
    try:
        r = requests.get(f"http://{GANDALF}:{OLLAMA_PORT}/api/ps", timeout=5)
        return jsonify(r.json())
    except Exception as e: return jsonify(error=str(e)), 503

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data  = request.get_json(force=True)
    text  = data.get("text","").strip()
    speak = bool(data.get("speak", False))
    mode  = data.get("mode", "adult")
    if not text: return jsonify(error="empty"), 400
    cfg   = read_cfg()
    model = cfg.get("OLLAMA_MODEL_KIDS" if mode == "kids" else "OLLAMA_MODEL_ADULT", "iris")
    try:
        import datetime as _dt
        _now = _dt.datetime.now()
        _sys = f"Current date and time: {_now.strftime('%A, %B %d %Y, %I:%M %p')} Mountain Time."
        r = requests.post(f"http://{GANDALF}:{OLLAMA_PORT}/api/generate",
            json={"model": model, "prompt": text, "system": _sys, "stream": False},
            timeout=90)
        r.raise_for_status()
        raw_reply = r.json().get("response", "").strip()
        from services.llm import extract_emotion_from_reply, clean_llm_reply
        emotion, clean_reply = extract_emotion_from_reply(raw_reply)
        clean_reply = clean_llm_reply(clean_reply)
        if speak and clean_reply:
            speak_async(clean_reply, cfg)
        return jsonify(reply=clean_reply, emotion=emotion, spoken=speak and bool(clean_reply))
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/api/speak", methods=["POST"])
def api_speak():
    """Speak text verbatim via TTS — no LLM."""
    data = request.get_json(force=True)
    text = data.get("text", "").strip()
    if not text:
        return jsonify(error="empty"), 400
    cfg = read_cfg()
    speak_async(text, cfg)
    return jsonify(ok=True, spoken=text)

@app.route("/api/sd_status")
def api_sd_status():
    """Check if iris_config.json in RAM matches the SD card copy."""
    return jsonify(synced=_sd_synced())

@app.route("/api/persist_config", methods=["POST"])
def api_persist_config():
    """Copy iris_config.json through overlayfs to SD card. Returns ok + verified."""
    try:
        result = subprocess.run(
            ["sudo", "bash", "-c",
             f"mount -o remount,rw /media/root-ro && "
             f"cp {CONFIG_FILE} {SD_CONFIG} && "
             f"chown pi:pi {SD_CONFIG} && "
             f"chmod 644 {SD_CONFIG} && "
             f"sync && "
             f"mount -o remount,ro /media/root-ro"],
            capture_output=True, text=True, timeout=20)
        if result.returncode != 0:
            return jsonify(ok=False, error=result.stderr.strip() or "mount/cp failed"), 500
        verified = _sd_synced()
        # Copy ALSA state to SD layer
        alsa_src = "/var/lib/alsa/asound.state"
        alsa_dst = "/media/root-ro/var/lib/alsa/asound.state"
        alsa_result = subprocess.run(
            ["sudo", "bash", "-c",
             f"mount -o remount,rw /media/root-ro && "
             f"cp {alsa_src} {alsa_dst} && "
             f"sync && "
             f"mount -o remount,ro /media/root-ro"],
            capture_output=True, text=True, timeout=20)
        alsa_ok = alsa_result.returncode == 0
        return jsonify(ok=verified, verified=verified, alsa_persisted=alsa_ok)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.route("/api/volume", methods=["GET","POST"])
def api_volume():
    """Get or set wm8960 speaker volume (0-127). POST accepts {"level": <abs>} or {"delta": <±n>}."""
    import re as _re
    card = subprocess.check_output(
        ["bash","-c","aplay -l 2>/dev/null | grep wm8960 | head -1 | awk '{print $2}' | tr -d ':'"],
        text=True).strip() or "0"
    if request.method == "POST":
        data = request.get_json(force=True)
        if "delta" in data:
            out = subprocess.check_output(["amixer","-c",card,"sget","Speaker"], text=True)
            current = 110
            for line in out.splitlines():
                if "Front Left:" in line:
                    m = _re.search(r"Playback (\d+)", line)
                    if m:
                        current = int(m.group(1))
                        break
            level = max(0, min(127, current + int(data["delta"])))
        else:
            level = max(0, min(127, int(data.get("level", 110))))
        subprocess.run(["amixer","-c",card,"sset","Speaker",str(level)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["alsactl", "store"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cfg = read_cfg(); cfg["SPEAKER_VOLUME"] = level
        with open(CONFIG_FILE, "w") as f: json.dump(cfg, f, indent=2)
        return jsonify(ok=True, level=level, pct=round(level/127*100))
    out = subprocess.check_output(["amixer","-c",card,"sget","Speaker"], text=True)
    for line in out.splitlines():
        if "Front Left:" in line:
            m = _re.search(r"Playback (\d+)", line)
            if m:
                level = int(m.group(1))
                return jsonify(level=level, pct=round(level/127*100))
    return jsonify(level=110, pct=87)


@app.route("/api/stop", methods=["POST"])
def api_stop():
    """Interrupt current TTS playback."""
    ok = send_teensy("STOP_PLAYBACK")
    return jsonify(ok=ok)


@app.route("/api/listen", methods=["POST"])
def api_listen():
    """Trigger a manual listen cycle without saying the wakeword."""
    try:
        open("/tmp/iris_manual_listen", "w").close()
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500


@app.route("/api/bench")
def api_bench():
    """Parse recent [BENCH] log lines and return structured cycle data + tuning levers."""
    import re as _re
    try:
        raw = subprocess.check_output(
            ["journalctl", "-u", "assistant", "-n", "600", "--no-pager", "--output=short-iso"],
            text=True, stderr=subprocess.DEVNULL)
        lines = raw.splitlines()
    except Exception as e:
        return jsonify(error=str(e), cycles=[], levers={})

    def _parse(line):
        m = _re.search(r'\[BENCH\](.*)', line)
        if not m: return None
        kv = {}
        for part in m.group(1).split():
            if '=' in part:
                k, v = part.split('=', 1)
                kv[k] = v.strip('"\'')
        return kv if kv else None

    cycles, cur = [], {}
    for line in lines:
        kv = _parse(line)
        if not kv: continue
        stage = kv.get('stage')
        if not stage: continue
        if stage == 'wake_detected':
            if cur: cycles.append(cur)
            cur = {'trigger': kv.get('trigger', '?'), 't': kv.get('t', '')}
        elif cur:
            cur[stage] = kv
    if cur:
        cycles.append(cur)

    try:
        import core.config as _cc
        levers = {k: getattr(_cc, k) for k in
                  ('NUM_PREDICT_SHORT', 'NUM_PREDICT_MEDIUM', 'NUM_PREDICT_LONG',
                   'NUM_PREDICT_MAX', 'TTS_MAX_CHARS', 'KOKORO_ENABLED')
                  if hasattr(_cc, k)}
    except Exception:
        levers = {}

    return jsonify(cycles=cycles[-20:], levers=levers)


@app.route("/api/vision", methods=["POST"])
def api_vision():
    """Capture Pi camera frame, send to Ollama vision model, return description."""
    data   = request.get_json(force=True)
    prompt = data.get("prompt", "Describe in detail what you see.").strip()
    speak  = bool(data.get("speak", False))
    try:
        import base64, tempfile as _tf
        cfg = read_cfg()
        with _tf.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            img_path = f.name
        result = subprocess.run(
            ["rpicam-still", "-o", img_path, "--nopreview", "-t", "500",
             "--width", "1024", "--height", "768"],
            capture_output=True, timeout=15)
        if result.returncode != 0:
            try: os.unlink(img_path)
            except Exception: pass
            return jsonify(error="Camera capture failed: " + result.stderr.decode()[:200]), 500
        with open(img_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()
        try: os.unlink(img_path)
        except Exception: pass
        model = cfg.get("VISION_MODEL", "iris")
        r = requests.post(
            f"http://{GANDALF}:{OLLAMA_PORT}/api/generate",
            json={"model": model, "prompt": prompt, "images": [image_b64], "stream": False},
            timeout=120)
        r.raise_for_status()
        raw_reply = r.json().get("response", "").strip()
        from services.llm import extract_emotion_from_reply, clean_llm_reply
        emotion, clean_reply = extract_emotion_from_reply(raw_reply)
        clean_reply = clean_llm_reply(clean_reply)
        if speak and clean_reply:
            speak_async(clean_reply, cfg)
        return jsonify(reply=clean_reply, emotion=emotion, spoken=speak and bool(clean_reply))
    except Exception as e:
        return jsonify(error=str(e)), 500


_DEFAULT_GESTURE_MAP = {
    "VOL+":   "VOL+",
    "VOL-":   "VOL-",
    "STOP":   "STOP",
    "LISTEN": "LISTEN",
}
_VALID_GESTURE_ACTIONS = {"VOL+", "VOL-", "STOP", "LISTEN", "SKIP"}


@app.route("/api/gesture_config", methods=["GET", "POST"])
def api_gesture_config():
    if request.method == "POST":
        data = request.get_json(force=True)
        raw_map = data.get("GESTURE_MAP", {})
        cleaned = {k: v for k, v in raw_map.items() if v in _VALID_GESTURE_ACTIONS}
        threshold = max(0, min(255, int(data.get("GESTURE_PROXIMITY_THRESHOLD", 150))))
        write_cfg({"GESTURE_MAP": cleaned, "GESTURE_PROXIMITY_THRESHOLD": threshold})
        return jsonify(ok=True)
    cfg = read_cfg()
    return jsonify(
        GESTURE_MAP=cfg.get("GESTURE_MAP", _DEFAULT_GESTURE_MAP),
        GESTURE_PROXIMITY_THRESHOLD=cfg.get("GESTURE_PROXIMITY_THRESHOLD", 150),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)

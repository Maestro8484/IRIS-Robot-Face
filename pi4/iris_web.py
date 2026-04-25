#!/usr/bin/env python3
"""IRIS Web Config Panel — Flask server (Pi4)."""
import json, os, subprocess, time, wave, tempfile, threading
import requests
from flask import Flask, request, jsonify
import sys; sys.path.insert(0, "/home/pi")
from core.config import CMD_PORT

app = Flask(__name__)

GANDALF      = "192.168.1.3"
OLLAMA_PORT  = 11434
TEENSY_PORT  = "/dev/ttyACM0"
TEENSY_BAUD  = 115200
CHATTERBOX_URL = "http://192.168.1.3:8004"
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
    """Synthesize via services.tts (Chatterbox->Piper routing)."""
    with _speak_lock:
        try:
            from services.tts import synthesize
            pcm = synthesize(text)   # s16le, 22050 Hz, mono
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wav_path = f.name
            with wave.open(wav_path, "wb") as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(22050)
                wf.writeframes(pcm)
            subprocess.run(["aplay", "-q", wav_path])
            os.unlink(wav_path)
            print(f"[WEB-TTS] played {len(pcm)}b PCM", flush=True)
        except Exception as e:
            print(f"[WEB-TTS] error: {e}", flush=True)

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

@app.route("/api/logs")
def api_logs():
    try:
        out = subprocess.check_output(
            ["journalctl","-u","assistant","-u","iris-web","-n","150","--no-pager","--output=short-iso"],
            text=True, stderr=subprocess.DEVNULL)
        lines = [l for l in out.strip().splitlines() if l][-120:]
        return jsonify(lines=lines)
    except Exception as e: return jsonify(lines=[f"[ERR] {e}"])


@app.route("/api/chatterbox_voices")
def api_chatterbox_voices():
    try:
        r = requests.get(f"{CHATTERBOX_URL}/get_reference_files", timeout=5)
        r.raise_for_status()
        return jsonify(files=r.json())
    except Exception as e:
        return jsonify(files=[], error=str(e))

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
    model = cfg.get("OLLAMA_MODEL_KIDS" if mode == "kids" else "OLLAMA_MODEL_ADULT", "jarvis")
    try:
        import datetime as _dt
        _now = _dt.datetime.now()
        _sys = f"Current date and time: {_now.strftime('%A, %B %d %Y, %I:%M %p')} Mountain Time."
        r = requests.post(f"http://{GANDALF}:{OLLAMA_PORT}/api/chat",
            json={"model": model,
                  "messages": [{"role":"system","content":_sys},{"role":"user","content":text}],
                  "stream": False},
            timeout=90)
        r.raise_for_status()
        reply = r.json().get("message",{}).get("content","").strip()
        if speak and reply:
            speak_async(reply, cfg)
        return jsonify(reply=reply, spoken=speak and bool(reply))
    except Exception as e: return jsonify(error=str(e)), 500

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
             f"mount -o remount,ro /media/root-ro"],
            capture_output=True, text=True, timeout=20)
        alsa_ok = alsa_result.returncode == 0
        return jsonify(ok=verified, verified=verified, alsa_persisted=alsa_ok)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.route("/api/volume", methods=["GET","POST"])
def api_volume():
    """Get or set wm8960 speaker volume (0-127)."""
    import re as _re
    card = subprocess.check_output(
        ["bash","-c","aplay -l 2>/dev/null | grep wm8960 | head -1 | awk '{print $2}' | tr -d ':'"],
        text=True).strip() or "0"
    if request.method == "POST":
        level = max(0, min(127, int(request.get_json(force=True).get("level", 110))))
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
                   'NUM_PREDICT_MAX', 'TTS_MAX_CHARS', 'CHATTERBOX_ENABLED')
                  if hasattr(_cc, k)}
    except Exception:
        levers = {}

    return jsonify(cycles=cycles[-25:], levers=levers)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)

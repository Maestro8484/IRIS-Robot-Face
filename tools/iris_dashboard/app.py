
import json, threading, time, socket, os
from datetime import datetime
import paramiko
import requests
from flask import Flask, jsonify, Response

app = Flask(__name__)

PROMETHEUS = "http://localhost:9090"
PI4_IP = "192.168.1.200"
PI4_USER = "pi"
PI4_PASS = os.environ.get("PI4_PASS", "ohs")


def prom_query(query):
    try:
        r = requests.get(f"{PROMETHEUS}/api/v1/query", params={"query": query}, timeout=3)
        results = r.json().get("data", {}).get("result", [])
        if results:
            return float(results[0]["value"][1])
    except Exception:
        pass
    return None


def check_port(port):
    try:
        s = socket.create_connection(("localhost", port), timeout=2)
        s.close()
        return True
    except Exception:
        return False


def pi4_exec(cmd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(PI4_IP, username=PI4_USER, password=PI4_PASS, timeout=6)
        _, stdout, _ = client.exec_command(cmd, timeout=8)
        result = stdout.read().decode("utf-8", errors="replace")
        client.close()
        return result
    except Exception:
        try:
            client.close()
        except Exception:
            pass
        return ""


def get_pi4_logs(n=80):
    out = pi4_exec(f"sudo journalctl -u assistant -n {n} --no-pager 2>/dev/null")
    if not out.strip():
        out = pi4_exec(f"tail -{n} /tmp/iris.log 2>/dev/null")
    if not out.strip():
        return ["(Pi4 unreachable or no logs found)"]
    return out.strip().splitlines()


def get_assistant_status():
    out = pi4_exec("systemctl is-active assistant")
    return out.strip() == "active"


def parse_latency(lines):
    stages = {"wakeword": None, "stt": None, "llm": None, "tts": None}
    for line in reversed(lines):
        ll = line.lower()
        for key in stages:
            if stages[key] is None and key in ll and "ms" in ll:
                parts = ll.replace("ms", "").split()
                for p in reversed(parts):
                    p = p.strip("=:,")
                    try:
                        stages[key] = float(p)
                        break
                    except ValueError:
                        continue
    return stages


@app.route("/api/status")
def api_status():
    vram_used  = prom_query("nvidia_smi_memory_used_bytes")
    vram_free  = prom_query("nvidia_smi_memory_free_bytes")
    vram_total = prom_query("nvidia_smi_memory_total_bytes")
    gpu_util   = prom_query("nvidia_smi_utilization_gpu_ratio")
    gpu_temp   = prom_query("nvidia_smi_temperature_gpu")
    gpu_power  = prom_query("nvidia_smi_power_draw_watts")

    logs = get_pi4_logs(80)
    latency = parse_latency(logs)

    def gb(v):
        return round(v / 1e9, 2) if v is not None else None

    return jsonify({
        "ts": datetime.now().isoformat(),
        "vram": {
            "used_gb":  gb(vram_used),
            "free_gb":  gb(vram_free),
            "total_gb": gb(vram_total),
            "pct": round(vram_used / vram_total * 100) if vram_used and vram_total else None,
        },
        "gpu": {
            "util_pct": round((gpu_util or 0) * 100),
            "temp_c":   round(gpu_temp)  if gpu_temp  is not None else None,
            "power_w":  round(gpu_power) if gpu_power is not None else None,
        },
        "services": {
            "ollama":       check_port(11434),
            "whisper":      check_port(10300),
            "piper":        check_port(10200),
            "chatterbox":   check_port(8004),
            "assistant_pi4": get_assistant_status(),
        },
        "latency": latency,
        "logs": logs[-30:],
    })


@app.route("/api/restart/<service>", methods=["POST"])
def restart_service(service):
    import subprocess
    allowed = {
        "assistant":  None,
        "whisper":    ["powershell", "-Command", "docker restart wyoming-whisper-1"],
        "piper":      ["powershell", "-Command", "docker restart wyoming-piper-1"],
        "chatterbox": ["powershell", "-Command", "docker restart wyoming-chatterbox-1"],
    }
    if service not in allowed:
        return jsonify({"ok": False, "error": "unknown service"}), 400

    if service == "assistant":
        out = pi4_exec("sudo systemctl restart assistant")
        return jsonify({"ok": True, "out": out.strip()})

    try:
        result = subprocess.run(allowed[service], capture_output=True, text=True, timeout=20)
        return jsonify({"ok": result.returncode == 0,
                        "out": result.stdout.strip(),
                        "err": result.stderr.strip()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/action/sleep", methods=["POST"])
def action_sleep():
    out = pi4_exec("python3 /home/pi/iris_sleep.py")
    return jsonify({"ok": True, "out": out.strip()})


@app.route("/api/action/wake", methods=["POST"])
def action_wake():
    out = pi4_exec("python3 /home/pi/iris_wake.py")
    return jsonify({"ok": True, "out": out.strip()})


@app.route("/")
def index():
    return Response(HTML, mimetype="text/html")


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>IRIS Mission Control</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0d1117;--surf:#161b22;--bdr:#21262d;--text:#e6edf3;--text2:#8b949e;--green:#3fb950;--amber:#d29922;--red:#f85149;--blue:#58a6ff}
body{background:var(--bg);color:var(--text);font-family:'Courier New',Menlo,Monaco,monospace;font-size:13px;min-height:100vh;padding:16px 20px}
.hdr{display:flex;align-items:center;gap:10px;padding-bottom:12px;border-bottom:1px solid var(--bdr);margin-bottom:14px}
.iris-dot{width:8px;height:8px;border-radius:50%;background:var(--green);box-shadow:0 0 6px var(--green);flex-shrink:0}
.hdr-title{font-size:14px;font-weight:600;letter-spacing:0.06em}
.hdr-sub{font-size:11px;color:var(--text2)}
.tabs{display:flex;border:1px solid var(--bdr);border-radius:6px;overflow:hidden;margin-bottom:14px}
.tab{padding:6px 16px;font-size:12px;cursor:pointer;background:var(--bg);color:var(--text2);border-right:1px solid var(--bdr);white-space:nowrap;font-family:inherit}
.tab:last-child{border-right:none}
.tab.active{background:var(--surf);color:var(--text);font-weight:600}
.tab:hover:not(.active){background:var(--surf)}
.panel{display:none}
.panel.active{display:block}
.svc-strip{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.svc-pill{display:flex;align-items:center;gap:6px;background:var(--surf);border:1px solid var(--bdr);border-radius:4px;padding:5px 10px;font-size:12px}
.svc-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.dot-green{background:var(--green)}
.dot-red{background:var(--red)}
.svc-label{color:var(--text);white-space:nowrap}
.rst-btn{font-size:10px;padding:1px 7px;border:1px solid var(--bdr);border-radius:3px;cursor:pointer;background:transparent;color:var(--text2);font-family:inherit;margin-left:4px}
.rst-btn:hover{border-color:var(--amber);color:var(--amber)}
.stat-row{background:var(--surf);border:1px solid var(--bdr);border-radius:6px;padding:10px 12px;margin-bottom:10px}
.stat-label{font-size:11px;color:var(--text2);margin-bottom:6px;text-transform:uppercase;letter-spacing:0.08em}
.vram-bar-wrap{background:var(--bg);border:1px solid var(--bdr);border-radius:3px;height:10px;overflow:hidden;margin-bottom:5px}
.vram-bar{height:100%;border-radius:3px;transition:width 0.5s,background 0.5s}
.vram-text{font-size:12px;color:var(--text)}
.one-line{font-size:12px;color:var(--text2)}
.log-box{background:var(--bg);border:1px solid var(--bdr);border-radius:4px;padding:8px 10px;height:220px;overflow-y:auto;font-size:11px;color:var(--text2);line-height:1.6;font-family:inherit}
.log-line{white-space:pre-wrap;word-break:break-all}
.action-strip{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.act-btn{font-size:12px;padding:5px 14px;border-radius:4px;cursor:pointer;font-family:inherit;font-weight:600}
.act-red{background:#3d1515;color:var(--red);border:1px solid var(--red)}
.act-red:hover{background:var(--red);color:#000}
.act-amber{background:#2e2100;color:var(--amber);border:1px solid var(--amber)}
.act-amber:hover{background:var(--amber);color:#000}
.act-gray{background:var(--surf);color:var(--text2);border:1px solid var(--bdr)}
.act-gray:hover{color:var(--text);border-color:var(--text2)}
.sec-label{font-size:11px;color:var(--text2);text-transform:uppercase;letter-spacing:0.08em;margin:14px 0 6px}
.log-entry{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid var(--bdr)}
.log-entry:last-of-type{border-bottom:none}
.log-entry-label{font-size:12px;color:var(--text2);flex:1}
.cmd{background:var(--surf);border:1px solid var(--bdr);border-radius:4px;padding:4px 8px;font-size:11px;color:var(--text);display:flex;align-items:center;gap:8px;margin:4px 0}
.cmd-text{flex:1;word-break:break-all;line-height:1.5}
.copy-btn{font-size:10px;padding:2px 8px;border:1px solid var(--bdr);border-radius:3px;cursor:pointer;background:var(--bg);color:var(--text2);font-family:inherit;white-space:nowrap;flex-shrink:0}
.copy-btn:hover{border-color:var(--blue);color:var(--blue)}
.play-card{border:1px solid var(--bdr);border-radius:6px;overflow:hidden;margin-bottom:8px;background:var(--surf)}
.play-header{display:flex;align-items:center;gap:8px;cursor:pointer;padding:10px 12px;user-select:none}
.play-header:hover{background:rgba(255,255,255,0.03)}
.play-title{font-size:12px;font-weight:500;color:var(--text2);flex:1}
.play-title.open{color:var(--text)}
.play-chevron{font-size:11px;color:var(--text2);transition:transform 0.15s;flex-shrink:0}
.play-chevron.open{transform:rotate(90deg)}
.play-body{display:none;padding:0 12px 10px}
.play-body.open{display:block}
.badge{display:inline-block;font-size:10px;padding:2px 6px;border-radius:3px;font-weight:600;font-family:inherit}
.badge-red{background:#3d1515;color:var(--red)}
.badge-amber{background:#2e2100;color:var(--amber)}
.badge-gray{background:var(--bg);color:var(--text2);border:1px solid var(--bdr)}
.badge-blue{background:#0c1f3a;color:var(--blue)}
.node-pill{display:inline-flex;align-items:center;font-size:10px;padding:2px 7px;border-radius:3px;font-family:inherit;font-weight:500}
.node-pi4{background:#0c1f3a;color:var(--blue)}
.node-gandalf{background:#2e2100;color:var(--amber)}
.node-teensy{background:#0d2915;color:var(--green)}
.step-row{display:flex;gap:8px;margin:5px 0;align-items:flex-start}
.step-num{min-width:20px;height:20px;border-radius:50%;background:var(--bg);border:1px solid var(--bdr);display:flex;align-items:center;justify-content:center;font-size:10px;color:var(--text2);flex-shrink:0;margin-top:1px}
.step-body{flex:1;font-size:12px;color:var(--text2);line-height:1.6}
.step-body strong{color:var(--text)}
.note-box{background:var(--bg);border-left:2px solid var(--bdr);padding:7px 10px;font-size:11px;color:var(--text2);line-height:1.6;margin:6px 0}
.divider{height:1px;background:var(--bdr);margin:10px 0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.flag{color:var(--red);font-weight:600}
</style>
</head>
<body>

<div class="hdr">
  <div class="iris-dot"></div>
  <div>
    <div class="hdr-title">IRIS MISSION CONTROL</div>
    <div class="hdr-sub">Pi4: 192.168.1.200 &nbsp;|&nbsp; GandalfAI: 192.168.1.3 &nbsp;|&nbsp; Dashboard: 192.168.1.3:8080</div>
  </div>
</div>

<div class="tabs">
  <div class="tab active" onclick="switchTab('status')">Status</div>
  <div class="tab" onclick="switchTab('logs')">Logs</div>
  <div class="tab" onclick="switchTab('playbooks')">Playbooks</div>
  <div class="tab" onclick="switchTab('falsewake')">False Wakeword</div>
</div>

<!-- STATUS TAB -->
<div id="tab-status" class="panel active">
  <div class="svc-strip" id="svc-strip">
    <div class="svc-pill"><div class="svc-dot dot-red"></div><span class="svc-label">loading...</span></div>
  </div>
  <div class="stat-row">
    <div class="stat-label">VRAM</div>
    <div class="vram-bar-wrap"><div class="vram-bar" id="vram-bar" style="width:0%;background:var(--green)"></div></div>
    <div class="vram-text" id="vram-text">— / 24.0 GB (—%)</div>
  </div>
  <div class="stat-row">
    <div class="one-line" id="gpu-line">GPU: — | —C | —W</div>
  </div>
  <div class="stat-row">
    <div class="one-line" id="lat-line">STT: —s | LLM: —s | TTS: —s</div>
  </div>
  <div class="stat-row">
    <div class="stat-label">Last 15 log lines</div>
    <div class="log-box" id="log-box">(loading...)</div>
  </div>
  <div class="action-strip">
    <button class="act-btn act-red"   onclick="doRestart('assistant',this)">Restart IRIS</button>
    <button class="act-btn act-amber" onclick="doRestartAll()">Restart All</button>
    <button class="act-btn act-gray"  onclick="doPost('/api/action/sleep')">Force Sleep</button>
    <button class="act-btn act-gray"  onclick="doPost('/api/action/wake')">Force Wake</button>
  </div>
</div>

<!-- LOGS TAB -->
<div id="tab-logs" class="panel">
  <div class="sec-label">Pi4 — main voice pipeline logs</div>

  <div class="log-entry"><span class="log-entry-label"><span class="node-pill node-pi4">Pi4</span> &nbsp;IRIS assistant — live tail</span></div>
  <div class="cmd"><span class="cmd-text">journalctl -u assistant -f --no-pager | grep -v "ALSA\|Jack\|pulse\|seeed\|pcm\|conf\|hdmi\|usb\|modem\|JackShm\|server"</span><button class="copy-btn" onclick="cp(this,'journalctl -u assistant -f --no-pager | grep -v \"ALSA\\|Jack\\|pulse\\|seeed\\|pcm\\|conf\\|hdmi\\|usb\\|modem\\|JackShm\\|server\"')">copy</button></div>

  <div class="log-entry"><span class="log-entry-label"><span class="node-pill node-pi4">Pi4</span> &nbsp;Key events only — filtered</span></div>
  <div class="cmd"><span class="cmd-text">journalctl -u assistant -n 60 --no-pager | grep -E "CMD|SLEEP|WAKE|EYES|LED|MOUTH|ERROR|WARN|FACE"</span><button class="copy-btn" onclick="cp(this,'journalctl -u assistant -n 60 --no-pager | grep -E \"CMD|SLEEP|WAKE|EYES|LED|MOUTH|ERROR|WARN|FACE\"')">copy</button></div>

  <div class="log-entry"><span class="log-entry-label"><span class="node-pill node-pi4">Pi4</span> &nbsp;Service status + last 20 lines</span></div>
  <div class="cmd"><span class="cmd-text">systemctl status assistant && journalctl -u assistant -n 20 --no-pager</span><button class="copy-btn" onclick="cp(this,'systemctl status assistant && journalctl -u assistant -n 20 --no-pager')">copy</button></div>

  <div class="log-entry"><span class="log-entry-label"><span class="node-pill node-pi4">Pi4</span> &nbsp;Wakeword confidence scores — live</span></div>
  <div class="cmd"><span class="cmd-text">journalctl -u openwakeword -f --no-pager 2>/dev/null || journalctl -u wyoming-openwakeword -f --no-pager</span><button class="copy-btn" onclick="cp(this,'journalctl -u openwakeword -f --no-pager 2>/dev/null || journalctl -u wyoming-openwakeword -f --no-pager')">copy</button></div>

  <div class="log-entry"><span class="log-entry-label"><span class="node-pill node-pi4">Pi4</span> &nbsp;Current iris_config.json</span></div>
  <div class="cmd"><span class="cmd-text">cat /home/pi/iris_config.json | python3 -m json.tool</span><button class="copy-btn" onclick="cp(this,'cat /home/pi/iris_config.json | python3 -m json.tool')">copy</button></div>

  <div class="log-entry"><span class="log-entry-label"><span class="node-pill node-pi4">Pi4</span> &nbsp;Sleep + wake cron logs</span></div>
  <div class="cmd"><span class="cmd-text">tail -30 /home/pi/logs/iris_sleep.log && tail -20 /home/pi/logs/iris_wake.log</span><button class="copy-btn" onclick="cp(this,'tail -30 /home/pi/logs/iris_sleep.log && tail -20 /home/pi/logs/iris_wake.log')">copy</button></div>

  <div class="sec-label">GandalfAI — AI inference + TTS logs</div>

  <div class="log-entry"><span class="log-entry-label"><span class="node-pill node-gandalf">GandalfAI</span> &nbsp;Docker containers — status + VRAM</span></div>
  <div class="cmd"><span class="cmd-text">docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" ; nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv,noheader</span><button class="copy-btn" onclick="cp(this,'docker ps --format \"table {{.Names}}\\t{{.Status}}\\t{{.Ports}}\" ; nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv,noheader')">copy</button></div>

  <div class="log-entry"><span class="log-entry-label"><span class="node-pill node-gandalf">GandalfAI</span> &nbsp;Chatterbox TTS — live log</span></div>
  <div class="cmd"><span class="cmd-text">docker logs chatterbox --tail 40 -f</span><button class="copy-btn" onclick="cp(this,'docker logs chatterbox --tail 40 -f')">copy</button></div>

  <div class="log-entry"><span class="log-entry-label"><span class="node-pill node-gandalf">GandalfAI</span> &nbsp;Whisper STT — transcription log</span></div>
  <div class="cmd"><span class="cmd-text">docker logs whisper --tail 30 -f</span><button class="copy-btn" onclick="cp(this,'docker logs whisper --tail 30 -f')">copy</button></div>

  <div class="log-entry"><span class="log-entry-label"><span class="node-pill node-gandalf">GandalfAI</span> &nbsp;Ollama LLM — inference log (PowerShell)</span></div>
  <div class="cmd"><span class="cmd-text">Get-Content "$env:USERPROFILE\.ollama\logs\server.log" -Tail 40 -Wait</span><button class="copy-btn" onclick="cp(this,'Get-Content \"$env:USERPROFILE\\.ollama\\logs\\server.log\" -Tail 40 -Wait')">copy</button></div>
</div>

<!-- PLAYBOOKS TAB -->
<div id="tab-playbooks" class="panel">

  <div class="play-card">
    <div class="play-header" onclick="togglePlay(this)">
      <span class="badge badge-red">CRITICAL</span>
      <span class="node-pill node-pi4">Pi4</span>
      <span class="play-title">IRIS hears wakeword, then nothing happens</span>
      <span class="play-chevron">&#x203A;</span>
    </div>
    <div class="play-body">
      <div class="note-box">Most common failure: assistant crashed, GandalfAI asleep, or audio pipeline stalled.</div>
      <div class="step-row"><div class="step-num">1</div><div class="step-body"><strong>Check Pi4 service:</strong></div></div>
      <div class="cmd"><span class="cmd-text">systemctl status assistant | head -5</span><button class="copy-btn" onclick="cp(this,'systemctl status assistant | head -5')">copy</button></div>
      <div class="step-row"><div class="step-num">2</div><div class="step-body"><strong>Restart if stopped/failed:</strong></div></div>
      <div class="cmd"><span class="cmd-text">sudo systemctl restart assistant && journalctl -u assistant -n 20 --no-pager</span><button class="copy-btn" onclick="cp(this,'sudo systemctl restart assistant && journalctl -u assistant -n 20 --no-pager')">copy</button></div>
      <div class="step-row"><div class="step-num">3</div><div class="step-body"><strong>Check GandalfAI is awake:</strong></div></div>
      <div class="cmd"><span class="cmd-text">ping -c 3 192.168.1.3</span><button class="copy-btn" onclick="cp(this,'ping -c 3 192.168.1.3')">copy</button></div>
      <div class="step-row"><div class="step-num">4</div><div class="step-body"><strong>GandalfAI not responding — Wake-on-LAN:</strong></div></div>
      <div class="cmd"><span class="cmd-text">wakeonlan A4:BB:6D:CA:83:20</span><button class="copy-btn" onclick="cp(this,'wakeonlan A4:BB:6D:CA:83:20')">copy</button></div>
      <div class="step-row"><div class="step-num">5</div><div class="step-body"><strong>Check containers (GandalfAI PowerShell):</strong></div></div>
      <div class="cmd"><span class="cmd-text">docker ps --format "table {{.Names}}\t{{.Status}}"</span><button class="copy-btn" onclick="cp(this,'docker ps --format \"table {{.Names}}\\t{{.Status}}\"')">copy</button></div>
      <div class="step-row"><div class="step-num">6</div><div class="step-body"><strong>Restart containers:</strong></div></div>
      <div class="cmd"><span class="cmd-text">cd C:\docker && docker-compose up -d</span><button class="copy-btn" onclick="cp(this,'cd C:\\docker && docker-compose up -d')">copy</button></div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-header" onclick="togglePlay(this)">
      <span class="badge badge-red">CRITICAL</span>
      <span class="node-pill node-gandalf">GandalfAI</span>
      <span class="play-title">30+ second delay, response cut off</span>
      <span class="play-chevron">&#x203A;</span>
    </div>
    <div class="play-body">
      <div class="note-box">VRAM pressure. gemma3:12b (~7GB) + Chatterbox (~4.5GB). Close any GPU apps on GandalfAI.</div>
      <div class="step-row"><div class="step-num">1</div><div class="step-body"><strong>Check VRAM (GandalfAI PowerShell):</strong></div></div>
      <div class="cmd"><span class="cmd-text">nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv,noheader</span><button class="copy-btn" onclick="cp(this,'nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv,noheader')">copy</button></div>
      <div class="step-row"><div class="step-num">2</div><div class="step-body">Healthy: ~11-12GB used. <span class="flag">Bad: 23-24GB</span> — close browser/GUI apps on GandalfAI.</div></div>
      <div class="step-row"><div class="step-num">3</div><div class="step-body"><strong>Check Ollama model registered:</strong></div></div>
      <div class="cmd"><span class="cmd-text">Invoke-RestMethod http://localhost:11434/api/tags | Select-Object -ExpandProperty models | Select-Object name</span><button class="copy-btn" onclick="cp(this,'Invoke-RestMethod http://localhost:11434/api/tags | Select-Object -ExpandProperty models | Select-Object name')">copy</button></div>
      <div class="step-row"><div class="step-num">4</div><div class="step-body"><strong>Check num_predict in modelfile (target: 120):</strong></div></div>
      <div class="cmd"><span class="cmd-text">Select-String "num_predict" C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt</span><button class="copy-btn" onclick="cp(this,'Select-String \"num_predict\" C:\\IRIS\\IRIS-Robot-Face\\ollama\\iris_modelfile.txt')">copy</button></div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-header" onclick="togglePlay(this)">
      <span class="badge badge-red">CRITICAL</span>
      <span class="node-pill node-pi4">Pi4</span>
      <span class="play-title">Web UI config changes don't survive reboot</span>
      <span class="play-chevron">&#x203A;</span>
    </div>
    <div class="play-body">
      <div class="note-box">Pi4 uses overlayfs — all writes go to RAM. Persist can fail silently if iris_config.json is root-owned.</div>
      <div class="step-row"><div class="step-num">1</div><div class="step-body"><strong>Check file ownership:</strong></div></div>
      <div class="cmd"><span class="cmd-text">ls -la /home/pi/iris_config.json</span><button class="copy-btn" onclick="cp(this,'ls -la /home/pi/iris_config.json')">copy</button></div>
      <div class="step-row"><div class="step-num">2</div><div class="step-body"><strong>Fix ownership if root:</strong></div></div>
      <div class="cmd"><span class="cmd-text">sudo chown pi:pi /home/pi/iris_config.json && sudo chmod 644 /home/pi/iris_config.json</span><button class="copy-btn" onclick="cp(this,'sudo chown pi:pi /home/pi/iris_config.json && sudo chmod 644 /home/pi/iris_config.json')">copy</button></div>
      <div class="step-row"><div class="step-num">3</div><div class="step-body"><strong>Persist to SD:</strong></div></div>
      <div class="cmd"><span class="cmd-text">sudo mount -o remount,rw /media/root-ro && sudo cp /home/pi/iris_config.json /media/root-ro/home/pi/iris_config.json && sudo mount -o remount,ro /media/root-ro</span><button class="copy-btn" onclick="cp(this,'sudo mount -o remount,rw /media/root-ro && sudo cp /home/pi/iris_config.json /media/root-ro/home/pi/iris_config.json && sudo mount -o remount,ro /media/root-ro')">copy</button></div>
      <div class="step-row"><div class="step-num">4</div><div class="step-body"><strong>Verify md5 hashes match:</strong></div></div>
      <div class="cmd"><span class="cmd-text">md5sum /home/pi/iris_config.json /media/root-ro/home/pi/iris_config.json</span><button class="copy-btn" onclick="cp(this,'md5sum /home/pi/iris_config.json /media/root-ro/home/pi/iris_config.json')">copy</button></div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-header" onclick="togglePlay(this)">
      <span class="badge badge-amber">MED</span>
      <span class="node-pill node-pi4">Pi4</span>
      <span class="play-title">Robotic voice — Piper fallback active</span>
      <span class="play-chevron">&#x203A;</span>
    </div>
    <div class="play-body">
      <div class="note-box">Chatterbox container down or CHATTERBOX_ENABLED=false in iris_config.json.</div>
      <div class="step-row"><div class="step-num">1</div><div class="step-body"><strong>Check config:</strong></div></div>
      <div class="cmd"><span class="cmd-text">cat /home/pi/iris_config.json</span><button class="copy-btn" onclick="cp(this,'cat /home/pi/iris_config.json')">copy</button></div>
      <div class="step-row"><div class="step-num">2</div><div class="step-body"><strong>Check Chatterbox container (GandalfAI PowerShell):</strong></div></div>
      <div class="cmd"><span class="cmd-text">docker ps | Select-String "chatterbox"</span><button class="copy-btn" onclick="cp(this,'docker ps | Select-String \"chatterbox\"')">copy</button></div>
      <div class="step-row"><div class="step-num">3</div><div class="step-body"><strong>Start containers:</strong></div></div>
      <div class="cmd"><span class="cmd-text">cd C:\IRIS\docker && docker compose up -d</span><button class="copy-btn" onclick="cp(this,'cd C:\\IRIS\\docker && docker compose up -d')">copy</button></div>
      <div class="step-row"><div class="step-num">4</div><div class="step-body"><strong>Test health:</strong></div></div>
      <div class="cmd"><span class="cmd-text">Invoke-WebRequest -Uri "http://localhost:8004/health" -UseBasicParsing</span><button class="copy-btn" onclick="cp(this,'Invoke-WebRequest -Uri \"http://localhost:8004/health\" -UseBasicParsing')">copy</button></div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-header" onclick="togglePlay(this)">
      <span class="badge badge-amber">MED</span>
      <span class="node-pill node-pi4">Pi4</span>
      <span class="play-title">Sleep/wake broken — wrong eyes, no mouth animation</span>
      <span class="play-chevron">&#x203A;</span>
    </div>
    <div class="play-body">
      <div class="note-box">Sleep requires: starfield eyes, MOUTH:8, /tmp/iris_sleep_mode flag. All three must be set.</div>
      <div class="step-row"><div class="step-num">1</div><div class="step-body"><strong>Check sleep flag:</strong></div></div>
      <div class="cmd"><span class="cmd-text">ls /tmp/iris_sleep_mode && echo "SLEEP FLAG: SET" || echo "SLEEP FLAG: NOT SET"</span><button class="copy-btn" onclick="cp(this,'ls /tmp/iris_sleep_mode && echo \"SLEEP FLAG: SET\" || echo \"SLEEP FLAG: NOT SET\"')">copy</button></div>
      <div class="step-row"><div class="step-num">2</div><div class="step-body"><strong>Check sleep log:</strong></div></div>
      <div class="cmd"><span class="cmd-text">tail -20 /home/pi/logs/iris_sleep.log</span><button class="copy-btn" onclick="cp(this,'tail -20 /home/pi/logs/iris_sleep.log')">copy</button></div>
      <div class="step-row"><div class="step-num">3</div><div class="step-body"><strong>Force sleep:</strong></div></div>
      <div class="cmd"><span class="cmd-text">python3 /home/pi/iris_sleep.py</span><button class="copy-btn" onclick="cp(this,'python3 /home/pi/iris_sleep.py')">copy</button></div>
      <div class="step-row"><div class="step-num">4</div><div class="step-body"><strong>Force wake:</strong></div></div>
      <div class="cmd"><span class="cmd-text">python3 /home/pi/iris_wake.py</span><button class="copy-btn" onclick="cp(this,'python3 /home/pi/iris_wake.py')">copy</button></div>
      <div class="step-row"><div class="step-num">5</div><div class="step-body"><strong>Confirm EYES:SLEEP + MOUTH:8 sent:</strong></div></div>
      <div class="cmd"><span class="cmd-text">journalctl -u assistant -n 40 --no-pager | grep -E "EYES|MOUTH|SLEEP|WAKE"</span><button class="copy-btn" onclick="cp(this,'journalctl -u assistant -n 40 --no-pager | grep -E \"EYES|MOUTH|SLEEP|WAKE\"')">copy</button></div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-header" onclick="togglePlay(this)">
      <span class="badge badge-amber">MED</span>
      <span class="node-pill node-teensy">Teensy</span>
      <span class="play-title">Eyes or mouth blank, frozen, or wrong</span>
      <span class="play-chevron">&#x203A;</span>
    </div>
    <div class="play-body">
      <div class="note-box">Teensy receives serial over USB from Pi4. USB loss or crash drops all display commands silently.</div>
      <div class="step-row"><div class="step-num">1</div><div class="step-body"><strong>Verify Teensy recognized:</strong></div></div>
      <div class="cmd"><span class="cmd-text">ls /dev/ttyACM* && dmesg | tail -10 | grep -i "tty\|usb\|teensy"</span><button class="copy-btn" onclick="cp(this,'ls /dev/ttyACM* && dmesg | tail -10 | grep -i \"tty\\|usb\\|teensy\"')">copy</button></div>
      <div class="step-row"><div class="step-num">2</div><div class="step-body">If /dev/ttyACM0 missing — unplug and replug USB.</div></div>
      <div class="step-row"><div class="step-num">3</div><div class="step-body"><strong>Send test command:</strong></div></div>
      <div class="cmd"><span class="cmd-text">echo "EMOTION:HAPPY" > /dev/ttyACM0</span><button class="copy-btn" onclick="cp(this,'echo \"EMOTION:HAPPY\" > /dev/ttyACM0')">copy</button></div>
      <div class="step-row"><div class="step-num">4</div><div class="step-body">Eyes go yellow = serial working. Problem is Pi4 not sending commands.</div></div>
      <div class="step-row"><div class="step-num">5</div><div class="step-body">Mouth TFT blank white — power-cycle Teensy (unplug USB 5s, replug).</div></div>
      <div class="step-row"><div class="step-num">6</div><div class="step-body">Still wrong — reflash from PlatformIO on SuperMaster.</div></div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-header" onclick="togglePlay(this)">
      <span class="badge badge-amber">MED</span>
      <span class="node-pill node-pi4">Pi4</span>
      <span class="play-title">IRIS not hearing anything — mic dead</span>
      <span class="play-chevron">&#x203A;</span>
    </div>
    <div class="play-body">
      <div class="note-box">ReSpeaker 2-Mic HAT is ALSA card "seeed2micvoicec". Check ALSA registration and mic volume.</div>
      <div class="step-row"><div class="step-num">1</div><div class="step-body"><strong>Confirm mic detected:</strong></div></div>
      <div class="cmd"><span class="cmd-text">arecord -l | grep -i "seeed\|reSpeaker\|wm8960"</span><button class="copy-btn" onclick="cp(this,'arecord -l | grep -i \"seeed\\|reSpeaker\\|wm8960\"')">copy</button></div>
      <div class="step-row"><div class="step-num">2</div><div class="step-body"><strong>Record + playback 5s test:</strong></div></div>
      <div class="cmd"><span class="cmd-text">arecord -D plughw:seeed2micvoicec,0 -f S16_LE -r 16000 -c 1 -d 5 /tmp/test.wav && aplay /tmp/test.wav</span><button class="copy-btn" onclick="cp(this,'arecord -D plughw:seeed2micvoicec,0 -f S16_LE -r 16000 -c 1 -d 5 /tmp/test.wav && aplay /tmp/test.wav')">copy</button></div>
      <div class="step-row"><div class="step-num">3</div><div class="step-body"><strong>Restore mic gain if silent:</strong></div></div>
      <div class="cmd"><span class="cmd-text">amixer -c seeed2micvoicec sget Capture && amixer -c seeed2micvoicec sset Capture 90%</span><button class="copy-btn" onclick="cp(this,'amixer -c seeed2micvoicec sget Capture && amixer -c seeed2micvoicec sset Capture 90%')">copy</button></div>
      <div class="step-row"><div class="step-num">4</div><div class="step-body"><strong>Check OWW_THRESHOLD (normal: 0.85–0.95):</strong></div></div>
      <div class="cmd"><span class="cmd-text">cat /home/pi/iris_config.json | python3 -c "import sys,json; d=json.load(sys.stdin); print('OWW_THRESHOLD:', d.get('OWW_THRESHOLD','check config.py'))"</span><button class="copy-btn" onclick="cp(this,'cat /home/pi/iris_config.json | python3 -c \"import sys,json; d=json.load(sys.stdin); print(\'OWW_THRESHOLD:\', d.get(\'OWW_THRESHOLD\',\'check config.py\'))\"')">copy</button></div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-header" onclick="togglePlay(this)">
      <span class="badge badge-gray">LOW</span>
      <span class="node-pill node-pi4">Pi4</span>
      <span class="play-title">Wrong personality — kids mode stuck on or off</span>
      <span class="play-chevron">&#x203A;</span>
    </div>
    <div class="play-body">
      <div class="note-box">Two modelfiles: iris (adult), iris-kids. Kids mode stuck = /tmp/iris_kids_mode flag present.</div>
      <div class="step-row"><div class="step-num">1</div><div class="step-body"><strong>Check kids mode flag:</strong></div></div>
      <div class="cmd"><span class="cmd-text">ls /tmp/iris_kids_mode 2>/dev/null && echo "KIDS MODE: ON" || echo "KIDS MODE: OFF"</span><button class="copy-btn" onclick="cp(this,'ls /tmp/iris_kids_mode 2>/dev/null && echo \"KIDS MODE: ON\" || echo \"KIDS MODE: OFF\"')">copy</button></div>
      <div class="step-row"><div class="step-num">2</div><div class="step-body"><strong>Clear if stuck on:</strong></div></div>
      <div class="cmd"><span class="cmd-text">rm /tmp/iris_kids_mode</span><button class="copy-btn" onclick="cp(this,'rm /tmp/iris_kids_mode')">copy</button></div>
      <div class="step-row"><div class="step-num">3</div><div class="step-body">Wrong personality in adult mode — modelfile may have drifted. Flag to Claude Code.</div></div>
    </div>
  </div>

</div>

<!-- FALSE WAKEWORD TAB -->
<div id="tab-falsewake" class="panel">

  <div class="play-card">
    <div class="play-header" onclick="togglePlay(this)">
      <span class="badge badge-blue">Step 1</span>
      <span class="play-title">Confirm it is a false trigger, not a real one</span>
      <span class="play-chevron">&#x203A;</span>
    </div>
    <div class="play-body">
      <div class="cmd"><span class="cmd-text">journalctl -u assistant --since "1 hour ago" --no-pager | grep -E "WAKE|wake|detected|threshold"</span><button class="copy-btn" onclick="cp(this,'journalctl -u assistant --since \"1 hour ago\" --no-pager | grep -E \"WAKE|wake|detected|threshold\"')">copy</button></div>
      <div class="cmd"><span class="cmd-text">journalctl -u assistant --since "1 hour ago" --no-pager | grep -E "STT|transcri"</span><button class="copy-btn" onclick="cp(this,'journalctl -u assistant --since \"1 hour ago\" --no-pager | grep -E \"STT|transcri\"')">copy</button></div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-header" onclick="togglePlay(this)">
      <span class="badge badge-blue">Step 2</span>
      <span class="play-title">Check and adjust OWW_THRESHOLD</span>
      <span class="play-chevron">&#x203A;</span>
    </div>
    <div class="play-body">
      <div class="note-box">Higher = fewer false triggers. Lower = more responsive. Current default: 0.90.</div>
      <div class="step-row"><div class="step-num">1</div><div class="step-body"><strong>Current threshold:</strong></div></div>
      <div class="cmd"><span class="cmd-text">cat /home/pi/iris_config.json | python3 -c "import sys,json; d=json.load(sys.stdin); print('OWW_THRESHOLD:', d.get('OWW_THRESHOLD','check core/config.py'))"</span><button class="copy-btn" onclick="cp(this,'cat /home/pi/iris_config.json | python3 -c \"import sys,json; d=json.load(sys.stdin); print(\'OWW_THRESHOLD:\', d.get(\'OWW_THRESHOLD\', \'check core/config.py\'))\"')">copy</button></div>
      <div class="divider"></div>
      <div class="grid2" style="margin:6px 0">
        <div style="background:var(--bg);border:1px solid var(--bdr);border-radius:4px;padding:8px 10px;font-size:11px"><strong>0.75 — sensitive</strong><br><span style="color:var(--text2)">Triggers easily. False-triggers on TV.</span></div>
        <div style="background:var(--bg);border:1px solid var(--bdr);border-radius:4px;padding:8px 10px;font-size:11px"><strong>0.85 — balanced</strong><br><span style="color:var(--text2)">Good for normal home noise.</span></div>
        <div style="background:var(--bg);border:1px solid var(--blue);border-radius:4px;padding:8px 10px;font-size:11px"><strong>0.90 — default</strong><br><span style="color:var(--text2)">Strict. Requires clear speech.</span></div>
        <div style="background:var(--bg);border:1px solid var(--bdr);border-radius:4px;padding:8px 10px;font-size:11px"><strong>0.95 — very strict</strong><br><span style="color:var(--text2)">May miss soft triggers.</span></div>
      </div>
      <div class="step-row"><div class="step-num">2</div><div class="step-body"><strong>Raise threshold to 0.92:</strong></div></div>
      <div class="cmd"><span class="cmd-text">sudo bash -c 'python3 -c "import json; d=json.load(open(\"/home/pi/iris_config.json\")); d[\"OWW_THRESHOLD\"]=0.92; open(\"/home/pi/iris_config.json\",\"w\").write(json.dumps(d,indent=2))"'</span><button class="copy-btn" onclick="cp(this,'sudo bash -c \'python3 -c \"import json; d=json.load(open(\\\"/home/pi/iris_config.json\\\")); d[\\\"OWW_THRESHOLD\\\"]=0.92; open(\\\"/home/pi/iris_config.json\\\",\\\"w\\\").write(json.dumps(d,indent=2))\"\'')">copy</button></div>
      <div class="step-row"><div class="step-num">3</div><div class="step-body"><strong>Restart:</strong></div></div>
      <div class="cmd"><span class="cmd-text">sudo systemctl restart assistant</span><button class="copy-btn" onclick="cp(this,'sudo systemctl restart assistant')">copy</button></div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-header" onclick="togglePlay(this)">
      <span class="badge badge-blue">Step 3</span>
      <span class="play-title">Watch live wakeword confidence scores</span>
      <span class="play-chevron">&#x203A;</span>
    </div>
    <div class="play-body">
      <div class="note-box">Normal ambient: 0.0–0.3. Spike above 0.7 means audio similar to "hey jarvis." Your threshold is the trigger line.</div>
      <div class="cmd"><span class="cmd-text">journalctl -u wyoming-openwakeword -f --no-pager</span><button class="copy-btn" onclick="cp(this,'journalctl -u wyoming-openwakeword -f --no-pager')">copy</button></div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-header" onclick="togglePlay(this)">
      <span class="badge badge-blue">Step 4</span>
      <span class="play-title">Identify the audio source causing false triggers</span>
      <span class="play-chevron">&#x203A;</span>
    </div>
    <div class="play-body">
      <div class="note-box">OWW recognizes sound patterns, not words. Common culprits in this household:</div>
      <div class="step-row"><div class="step-num">TV</div><div class="step-body">Dialogue with similar syllable patterns. Keep TV volume lower or reposition mic away from TV.</div></div>
      <div class="step-row"><div class="step-num">Kids</div><div class="step-body">Leo and Mae's voices at certain pitches score surprisingly high. Raise threshold.</div></div>
      <div class="step-row"><div class="step-num">IRIS</div><div class="step-body">IRIS's own voice at high volume can trigger a second wakeword. Lower speaker volume slightly.</div></div>
      <div class="step-row"><div class="step-num">Boot</div><div class="step-body">ALSA noise burst at startup. Normal one-time occurrence, not a real problem.</div></div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-header" onclick="togglePlay(this)">
      <span class="badge badge-blue">Step 5</span>
      <span class="play-title">Check SILENCE_RMS — responding to empty audio</span>
      <span class="play-chevron">&#x203A;</span>
    </div>
    <div class="play-body">
      <div class="note-box">Target: 300. Raise to 400–500 if IRIS responds to nothing (wakeword fires, Whisper transcribes silence).</div>
      <div class="cmd"><span class="cmd-text">journalctl -u assistant --since "2 hours ago" --no-pager | grep -A2 "WAKE"</span><button class="copy-btn" onclick="cp(this,'journalctl -u assistant --since \"2 hours ago\" --no-pager | grep -A2 \"WAKE\"')">copy</button></div>
      <div class="cmd"><span class="cmd-text">cat /home/pi/iris_config.json | python3 -c "import sys,json; d=json.load(sys.stdin); print('SILENCE_RMS:', d.get('SILENCE_RMS','not set'))"</span><button class="copy-btn" onclick="cp(this,'cat /home/pi/iris_config.json | python3 -c \"import sys,json; d=json.load(sys.stdin); print(\'SILENCE_RMS:\', d.get(\'SILENCE_RMS\', \'not set\'))\"')">copy</button></div>
      <div class="cmd"><span class="cmd-text">sudo bash -c 'python3 -c "import json; d=json.load(open(\"/home/pi/iris_config.json\")); d[\"SILENCE_RMS\"]=350; open(\"/home/pi/iris_config.json\",\"w\").write(json.dumps(d,indent=2))"' && sudo systemctl restart assistant</span><button class="copy-btn" onclick="cp(this,'sudo bash -c \'python3 -c \"import json; d=json.load(open(\\\"/home/pi/iris_config.json\\\")); d[\\\"SILENCE_RMS\\\"]=350; open(\\\"/home/pi/iris_config.json\\\",\\\"w\\\").write(json.dumps(d,indent=2))\"\'&& sudo systemctl restart assistant')">copy</button></div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-header" onclick="togglePlay(this)">
      <span class="badge badge-blue">Step 6</span>
      <span class="play-title">Nuclear option — switch to a less common wakeword</span>
      <span class="play-chevron">&#x203A;</span>
    </div>
    <div class="play-body">
      <div class="note-box">If threshold tuning fails, switch to a wakeword with no phonetic overlap with normal conversation.</div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin:8px 0;font-size:11px">
        <div style="background:var(--bg);border:1px solid var(--bdr);border-radius:4px;padding:7px 9px"><strong>computer</strong><br><span style="color:var(--text2)">Short, distinctive. Star Trek feel.</span></div>
        <div style="background:var(--bg);border:1px solid var(--bdr);border-radius:4px;padding:7px 9px"><strong>hey_mycroft</strong><br><span style="color:var(--text2)">Unusual name. Low speech overlap.</span></div>
        <div style="background:var(--bg);border:1px solid var(--bdr);border-radius:4px;padding:7px 9px"><strong>hey_rhasspy</strong><br><span style="color:var(--text2)">Lowest false trigger rate available.</span></div>
      </div>
      <div class="cmd"><span class="cmd-text">grep -n "hey_jarvis\|wakeword\|model_path\|OWW_MODEL" /home/pi/assistant.py | head -10</span><button class="copy-btn" onclick="cp(this,'grep -n \"hey_jarvis\\|wakeword\\|model_path\\|OWW_MODEL\" /home/pi/assistant.py | head -10')">copy</button></div>
    </div>
  </div>

</div>

<script>
const SVCS = [
  {key:'assistant_pi4', label:'IRIS / Pi4',     restart:'assistant'},
  {key:'ollama',        label:'Ollama 11434',   restart:null},
  {key:'whisper',       label:'Whisper 10300',  restart:'whisper'},
  {key:'piper',         label:'Piper 10200',    restart:'piper'},
  {key:'chatterbox',    label:'Chatterbox 8004',restart:'chatterbox'},
];

function buildSvcStrip(svcs) {
  return SVCS.map(s => {
    const up  = svcs[s.key];
    const dot = `<div class="svc-dot ${up ? 'dot-green' : 'dot-red'}"></div>`;
    const rst = s.restart
      ? `<button class="rst-btn" onclick="doRestart('${s.restart}',this)">restart</button>`
      : '';
    return `<div class="svc-pill">${dot}<span class="svc-label">${s.label}</span>${rst}</div>`;
  }).join('');
}

function poll() {
  fetch('/api/status').then(r => r.json()).then(d => {
    document.getElementById('svc-strip').innerHTML = buildSvcStrip(d.services);

    const v = d.vram;
    if (v && v.used_gb != null) {
      const pct = v.pct || 0;
      const bar = document.getElementById('vram-bar');
      bar.style.width      = pct + '%';
      bar.style.background = pct > 85 ? 'var(--red)' : pct > 70 ? 'var(--amber)' : 'var(--green)';
      document.getElementById('vram-text').textContent =
        `${v.used_gb} / ${v.total_gb || 24.0} GB (${pct}%)`;
    }

    const g = d.gpu;
    if (g) {
      document.getElementById('gpu-line').textContent =
        `GPU: ${g.util_pct ?? '—'}% | ${g.temp_c ?? '—'}C | ${g.power_w ?? '—'}W`;
    }

    const lat = d.latency || {};
    const fmt = v => v != null ? (v / 1000).toFixed(1) + 's' : '—';
    document.getElementById('lat-line').textContent =
      `STT: ${fmt(lat.stt)} | LLM: ${fmt(lat.llm)} | TTS: ${fmt(lat.tts)}`;

    const lines = (d.logs || []).slice(-15);
    const box   = document.getElementById('log-box');
    box.innerHTML = lines.map(l => `<div class="log-line">${esc(l)}</div>`).join('');
    box.scrollTop = box.scrollHeight;
  }).catch(() => {});
}

function esc(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function doRestart(svc, btn) {
  if (btn) { btn.textContent = '...'; btn.disabled = true; }
  fetch('/api/restart/' + svc, {method:'POST'}).then(() => {
    if (btn) { btn.textContent = 'restart'; btn.disabled = false; }
    poll();
  }).catch(() => { if (btn) { btn.textContent = 'restart'; btn.disabled = false; } });
}

function doRestartAll() {
  ['assistant','whisper','piper','chatterbox'].forEach(s =>
    fetch('/api/restart/' + s, {method:'POST'})
  );
  setTimeout(poll, 3000);
}

function doPost(url) {
  fetch(url, {method:'POST'}).then(() => poll()).catch(() => {});
}

function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelector('[onclick="switchTab(\'' + name + '\')"]').classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
}

function togglePlay(el) {
  const body = el.nextElementSibling;
  const title = el.querySelector('.play-title');
  const chev  = el.querySelector('.play-chevron');
  const open  = body.classList.contains('open');
  body.classList.toggle('open', !open);
  title.classList.toggle('open', !open);
  chev.classList.toggle('open', !open);
}

function cp(btn, text) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.textContent;
    btn.textContent = 'copied';
    setTimeout(() => btn.textContent = orig, 1500);
  });
}

poll();
setInterval(poll, 5000);
</script>
</body>
</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)

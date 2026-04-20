
import json, threading, time, socket
from datetime import datetime
import paramiko
import requests
from flask import Flask, jsonify, Response

app = Flask(__name__)

PROMETHEUS = "http://localhost:9090"
PI4_IP = "192.168.1.200"
PI4_USER = "pi"
PI4_PASS = "ohs"


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
:root{--font-mono:'Courier New',Menlo,Monaco,monospace;--color-text-primary:#1a1a1a;--color-text-secondary:#6b7280;--color-background-primary:#ffffff;--color-background-secondary:#f7f7f6;--color-border-primary:#c9c8c2;--color-border-secondary:#e2e0d9;--color-border-tertiary:#eeece6;--border-radius-md:6px;--border-radius-lg:10px}
body{background:var(--color-background-secondary);min-height:100vh;padding:20px 24px}
</style>
</head>
<body>
<h2 class="sr-only">IRIS Mission Control Dashboard — System health, log viewers, and troubleshooting playbooks</h2>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--font-mono,'Courier New',monospace);color:var(--color-text-primary);font-size:13px}
.hdr{display:flex;align-items:center;gap:12px;padding:16px 0 12px;border-bottom:0.5px solid var(--color-border-tertiary);margin-bottom:16px}
.hdr-title{font-size:15px;font-weight:500;letter-spacing:0.04em}
.hdr-sub{font-size:11px;color:var(--color-text-secondary)}
.iris-dot{width:8px;height:8px;border-radius:50%;background:#1D9E75;flex-shrink:0;box-shadow:0 0 0 2px #9FE1CB}
.tabs{display:flex;gap:0;border:0.5px solid var(--color-border-tertiary);border-radius:var(--border-radius-md);overflow:hidden;margin-bottom:16px;flex-wrap:wrap}
.tab{padding:6px 14px;font-size:12px;font-family:var(--font-mono);cursor:pointer;background:var(--color-background-secondary);color:var(--color-text-secondary);border-right:0.5px solid var(--color-border-tertiary);white-space:nowrap}
.tab:last-child{border-right:none}
.tab.active{background:var(--color-background-primary);color:var(--color-text-primary);font-weight:500}
.tab:hover:not(.active){background:var(--color-background-primary)}
.panel{display:none}
.panel.active{display:block}
.section-label{font-size:11px;color:var(--color-text-secondary);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;font-family:var(--font-mono)}
.card{background:var(--color-background-primary);border:0.5px solid var(--color-border-tertiary);border-radius:var(--border-radius-lg);padding:12px 14px;margin-bottom:10px}
.card-title{font-size:13px;font-weight:500;margin-bottom:6px;display:flex;align-items:center;gap:8px}
.card-body{font-size:12px;color:var(--color-text-secondary);line-height:1.6}
.cmd{background:var(--color-background-secondary);border:0.5px solid var(--color-border-tertiary);border-radius:var(--border-radius-md);padding:8px 10px;font-family:var(--font-mono);font-size:11px;color:var(--color-text-primary);margin:6px 0;display:flex;align-items:flex-start;justify-content:space-between;gap:8px;word-break:break-all}
.cmd-text{flex:1;line-height:1.5}
.copy-btn{font-size:10px;font-family:var(--font-mono);padding:2px 8px;border:0.5px solid var(--color-border-secondary);border-radius:4px;cursor:pointer;background:var(--color-background-primary);color:var(--color-text-secondary);flex-shrink:0;white-space:nowrap}
.copy-btn:hover{background:var(--color-background-secondary)}
.badge{display:inline-block;font-size:10px;padding:2px 7px;border-radius:4px;font-weight:500;font-family:var(--font-mono)}
.badge-red{background:#FCEBEB;color:#A32D2D}
.badge-amber{background:#FAEEDA;color:#854F0B}
.badge-green{background:#EAF3DE;color:#3B6D11}
.badge-blue{background:#E6F1FB;color:#185FA5}
.badge-gray{background:#F1EFE8;color:#5F5E5A}
.step-row{display:flex;gap:10px;margin:5px 0;align-items:flex-start}
.step-num{width:18px;height:18px;border-radius:50%;background:var(--color-background-secondary);border:0.5px solid var(--color-border-secondary);display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:500;flex-shrink:0;margin-top:1px}
.step-body{flex:1;font-size:12px;color:var(--color-text-secondary);line-height:1.6}
.step-body strong{color:var(--color-text-primary);font-weight:500}
.divider{height:0.5px;background:var(--color-border-tertiary);margin:12px 0}
.link-row{display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:0.5px solid var(--color-border-tertiary)}
.link-row:last-child{border-bottom:none}
.link-label{font-size:12px;flex:1;color:var(--color-text-secondary)}
.link-btn{font-size:11px;font-family:var(--font-mono);padding:3px 10px;border:0.5px solid var(--color-border-secondary);border-radius:4px;cursor:pointer;background:var(--color-background-secondary);color:var(--color-text-primary);white-space:nowrap;text-decoration:none}
.link-btn:hover{background:var(--color-background-primary);border-color:var(--color-border-primary)}
.play-header{display:flex;align-items:center;gap:10px;cursor:pointer;padding:10px 0;user-select:none}
.play-header:hover .play-title{color:var(--color-text-primary)}
.play-title{font-size:13px;font-weight:500;color:var(--color-text-secondary)}
.play-title.open{color:var(--color-text-primary)}
.play-chevron{font-size:11px;color:var(--color-text-secondary);transition:transform 0.15s;flex-shrink:0}
.play-chevron.open{transform:rotate(90deg)}
.play-body{display:none;padding-bottom:4px}
.play-body.open{display:block}
.play-card{border:0.5px solid var(--color-border-tertiary);border-radius:var(--border-radius-lg);overflow:hidden;margin-bottom:8px}
.play-card-inner{padding:12px 14px}
.node-pill{display:inline-flex;align-items:center;gap:4px;font-size:10px;padding:2px 8px;border-radius:3px;font-family:var(--font-mono);font-weight:500}
.node-pi4{background:#E6F1FB;color:#185FA5}
.node-gandalf{background:#FAEEDA;color:#854F0B}
.node-teensy{background:#EAF3DE;color:#3B6D11}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.note-box{background:var(--color-background-secondary);border-left:2px solid var(--color-border-secondary);border-radius:0;padding:8px 10px;font-size:11px;color:var(--color-text-secondary);line-height:1.6;margin:6px 0}
.flag{font-size:11px;font-weight:500;color:#A32D2D;font-family:var(--font-mono)}
</style>

<div class="hdr">
  <div class="iris-dot"></div>
  <div>
    <div class="hdr-title">IRIS MISSION CONTROL</div>
    <div class="hdr-sub">Pi4: 192.168.1.200 &nbsp;|&nbsp; GandalfAI: 192.168.1.3 &nbsp;|&nbsp; Dashboard: 192.168.1.3:8080</div>
  </div>
</div>

<div class="tabs">
  <div class="tab active" onclick="switchTab('logs')">Log Viewers</div>
  <div class="tab" onclick="switchTab('links')">Quick Links</div>
  <div class="tab" onclick="switchTab('playbooks')">Playbooks</div>
  <div class="tab" onclick="switchTab('falsewake')">False Wakeword</div>
</div>

<div id="tab-logs" class="panel active">
  <div class="section-label">Pi4 — main voice pipeline logs</div>
  <div class="card">
    <div class="card-title"><span class="badge badge-blue">Pi4</span> IRIS assistant service — live tail</div>
    <div class="card-body">Your primary diagnostic view. Shows every wakeword hit, STT result, LLM call, emotion tag, and TTS playback event. Start here for almost every problem.</div>
    <div class="cmd"><span class="cmd-text">journalctl -u assistant -f --no-pager | grep -v "ALSA\|Jack\|pulse\|seeed\|pcm\|conf\|hdmi\|usb\|modem\|JackShm\|server"</span><button class="copy-btn" onclick="cp(this,'journalctl -u assistant -f --no-pager | grep -v \"ALSA\\|Jack\\|pulse\\|seeed\\|pcm\\|conf\\|hdmi\\|usb\\|modem\\|JackShm\\|server\"')">copy</button></div>
    <div class="card-body" style="margin-top:6px">What you want to see: <strong>[WAKE] detected</strong> then <strong>[STT]</strong> then <strong>[LLM]</strong> then <strong>[TTS]</strong> in sequence. Any gap = that stage failed.</div>
  </div>
  <div class="card">
    <div class="card-title"><span class="badge badge-blue">Pi4</span> Key events only — filtered diagnostic view</div>
    <div class="card-body">Strips noise, shows only the commands IRIS sends to the Teensy (eyes, mouth, LEDs) plus sleep/wake transitions and errors.</div>
    <div class="cmd"><span class="cmd-text">journalctl -u assistant -n 60 --no-pager | grep -E "CMD|SLEEP|WAKE|EYES|LED|MOUTH|ERROR|WARN|FACE"</span><button class="copy-btn" onclick="cp(this,'journalctl -u assistant -n 60 --no-pager | grep -E \"CMD|SLEEP|WAKE|EYES|LED|MOUTH|ERROR|WARN|FACE\"')">copy</button></div>
  </div>
  <div class="card">
    <div class="card-title"><span class="badge badge-blue">Pi4</span> Service status + last 20 lines</div>
    <div class="card-body">Quick health check. Should say <strong>active (running)</strong>. If it says <strong>failed</strong> or <strong>inactive</strong>, IRIS will not respond to any wakeword.</div>
    <div class="cmd"><span class="cmd-text">systemctl status assistant && journalctl -u assistant -n 20 --no-pager</span><button class="copy-btn" onclick="cp(this,'systemctl status assistant && journalctl -u assistant -n 20 --no-pager')">copy</button></div>
  </div>
  <div class="card">
    <div class="card-title"><span class="badge badge-blue">Pi4</span> Wakeword confidence scores — live</div>
    <div class="card-body">Watch the raw score openwakeword assigns to each audio chunk. Score must exceed threshold (currently 0.9) to trigger. Useful when IRIS is not responding or false-triggering.</div>
    <div class="cmd"><span class="cmd-text">journalctl -u openwakeword -f --no-pager 2>/dev/null || journalctl -u wyoming-openwakeword -f --no-pager</span><button class="copy-btn" onclick="cp(this,'journalctl -u openwakeword -f --no-pager 2>/dev/null || journalctl -u wyoming-openwakeword -f --no-pager')">copy</button></div>
  </div>
  <div class="card">
    <div class="card-title"><span class="badge badge-blue">Pi4</span> Current IRIS config values</div>
    <div class="card-body">Shows what IRIS is actually running with. If behavior is wrong after a UI change, check here first — the web UI save may not have persisted through a reboot.</div>
    <div class="cmd"><span class="cmd-text">cat /home/pi/iris_config.json | python3 -m json.tool</span><button class="copy-btn" onclick="cp(this,'cat /home/pi/iris_config.json | python3 -m json.tool')">copy</button></div>
  </div>
  <div class="divider"></div>
  <div class="section-label">GandalfAI — AI inference + TTS logs</div>
  <div class="card">
    <div class="card-title"><span class="badge badge-amber">GandalfAI</span> Docker containers — status + VRAM</div>
    <div class="card-body">Shows whether Whisper, Piper, and Chatterbox containers are running. Run this on GandalfAI in PowerShell.</div>
    <div class="cmd"><span class="cmd-text">docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" ; nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv,noheader</span><button class="copy-btn" onclick="cp(this,'docker ps --format \"table {{.Names}}\\t{{.Status}}\\t{{.Ports}}\" ; nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv,noheader')">copy</button></div>
    <div class="card-body" style="margin-top:6px">Healthy VRAM at rest: <strong>~1-5%</strong> (nothing loaded). After first IRIS query: <strong>~19-21GB used</strong>. If stuck at 95%+ with no active query, something leaked VRAM.</div>
  </div>
  <div class="card">
    <div class="card-title"><span class="badge badge-amber">GandalfAI</span> Chatterbox TTS — live container log</div>
    <div class="card-body">Shows each TTS request arriving, processing, and streaming back. 3-4 seconds per audio chunk is normal. More than 10s per chunk = VRAM pressure.</div>
    <div class="cmd"><span class="cmd-text">docker logs chatterbox --tail 40 -f</span><button class="copy-btn" onclick="cp(this,'docker logs chatterbox --tail 40 -f')">copy</button></div>
  </div>
  <div class="card">
    <div class="card-title"><span class="badge badge-amber">GandalfAI</span> Whisper STT — transcription log</div>
    <div class="card-body">Shows each audio segment being transcribed. If IRIS hears the wakeword but never speaks, check here to confirm Whisper received the audio.</div>
    <div class="cmd"><span class="cmd-text">docker logs whisper --tail 30 -f</span><button class="copy-btn" onclick="cp(this,'docker logs whisper --tail 30 -f')">copy</button></div>
  </div>
  <div class="card">
    <div class="card-title"><span class="badge badge-amber">GandalfAI</span> Ollama LLM — inference log</div>
    <div class="card-body">Shows LLM requests arriving and token generation starting. If Whisper works but IRIS never speaks, check here — the LLM may have crashed or is generating too slowly.</div>
    <div class="cmd"><span class="cmd-text">Get-Content "$env:USERPROFILE\.ollama\logs\server.log" -Tail 40 -Wait</span><button class="copy-btn" onclick="cp(this,'Get-Content \"$env:USERPROFILE\\.ollama\\logs\\server.log\" -Tail 40 -Wait')">copy</button></div>
    <div class="note-box">Run this in PowerShell on GandalfAI. It is the Windows equivalent of tail -f.</div>
  </div>
  <div class="card">
    <div class="card-title"><span class="badge badge-blue">Pi4</span> Sleep + wake cron logs</div>
    <div class="card-body">If IRIS doesn't say goodnight or doesn't wake on schedule, check here. Written by the 9PM and 7:30AM cron jobs.</div>
    <div class="cmd"><span class="cmd-text">tail -30 /home/pi/logs/iris_sleep.log && tail -20 /home/pi/logs/iris_wake.log</span><button class="copy-btn" onclick="cp(this,'tail -30 /home/pi/logs/iris_sleep.log && tail -20 /home/pi/logs/iris_wake.log')">copy</button></div>
  </div>
</div>

<div id="tab-links" class="panel">
  <div class="section-label">Web interfaces</div>
  <div class="card">
    <div class="link-row"><span class="link-label">IRIS Web UI — control panel, eye/emotion buttons, config, sleep/wake</span><a class="link-btn" href="http://192.168.1.200:5000" target="_blank">open</a></div>
    <div class="link-row"><span class="link-label">IRIS Mission Control Dashboard — this dashboard, hosted on GandalfAI</span><a class="link-btn" href="http://192.168.1.3:8080" target="_blank">open</a></div>
    <div class="link-row"><span class="link-label">Grafana — GPU metrics, VRAM over time, container health</span><a class="link-btn" href="http://192.168.1.3:3000" target="_blank">open</a></div>
    <div class="link-row"><span class="link-label">Home Assistant</span><a class="link-btn" href="http://192.168.1.22:8123" target="_blank">open</a></div>
    <div class="link-row"><span class="link-label">Proxmox</span><a class="link-btn" href="https://192.168.1.5:8006" target="_blank">open</a></div>
  </div>
  <div class="section-label" style="margin-top:12px">SSH quick-connect (paste in terminal)</div>
  <div class="card">
    <div class="link-row"><span class="link-label">Pi4 — Jarvis voice pipeline</span><div class="cmd" style="margin:0;flex:0 0 auto;max-width:300px"><span class="cmd-text">ssh pi@192.168.1.200</span><button class="copy-btn" onclick="cp(this,'ssh pi@192.168.1.200')">copy</button></div></div>
    <div class="link-row"><span class="link-label">GandalfAI — AI inference workstation</span><div class="cmd" style="margin:0;flex:0 0 auto;max-width:300px"><span class="cmd-text">ssh gandalf@192.168.1.3</span><button class="copy-btn" onclick="cp(this,'ssh gandalf@192.168.1.3')">copy</button></div></div>
    <div class="link-row"><span class="link-label">Home Assistant</span><div class="cmd" style="margin:0;flex:0 0 auto;max-width:300px"><span class="cmd-text">ssh root@192.168.1.22</span><button class="copy-btn" onclick="cp(this,'ssh root@192.168.1.22')">copy</button></div></div>
  </div>
</div>

<div id="tab-playbooks" class="panel">
  <div class="section-label">Click any playbook to expand — ordered by frequency of occurrence</div>

  <div class="play-card">
    <div class="play-card-inner">
      <div class="play-header" onclick="togglePlay(this)">
        <span class="badge badge-red">CRITICAL</span>
        <span class="node-pill node-pi4">Pi4</span>
        <span class="play-title">IRIS hears wakeword, then nothing happens</span>
        <span class="play-chevron">&#x203A;</span>
      </div>
      <div class="play-body">
        <div class="note-box">Most common failure. Usually one of 3 things: assistant service crashed, GandalfAI is asleep, or the audio pipeline stalled.</div>
        <div class="step-row"><div class="step-num">1</div><div class="step-body"><strong>Check Pi4 service is alive:</strong></div></div>
        <div class="cmd"><span class="cmd-text">systemctl status assistant | head -5</span><button class="copy-btn" onclick="cp(this,'systemctl status assistant | head -5')">copy</button></div>
        <div class="step-row"><div class="step-num">2</div><div class="step-body"><strong>If stopped or failed — restart it:</strong></div></div>
        <div class="cmd"><span class="cmd-text">sudo systemctl restart assistant && journalctl -u assistant -n 20 --no-pager</span><button class="copy-btn" onclick="cp(this,'sudo systemctl restart assistant && journalctl -u assistant -n 20 --no-pager')">copy</button></div>
        <div class="step-row"><div class="step-num">3</div><div class="step-body"><strong>If Pi4 service is fine</strong> — check GandalfAI is awake:</div></div>
        <div class="cmd"><span class="cmd-text">ping -c 3 192.168.1.3</span><button class="copy-btn" onclick="cp(this,'ping -c 3 192.168.1.3')">copy</button></div>
        <div class="step-row"><div class="step-num">4</div><div class="step-body"><strong>GandalfAI not responding</strong> — send Wake-on-LAN from Pi4:</div></div>
        <div class="cmd"><span class="cmd-text">wakeonlan A4:BB:6D:CA:83:20</span><button class="copy-btn" onclick="cp(this,'wakeonlan A4:BB:6D:CA:83:20')">copy</button></div>
        <div class="step-row"><div class="step-num">5</div><div class="step-body"><strong>GandalfAI is up but containers stopped?</strong> Check on GandalfAI (PowerShell):</div></div>
        <div class="cmd"><span class="cmd-text">docker ps --format "table {{.Names}}\t{{.Status}}"</span><button class="copy-btn" onclick="cp(this,'docker ps --format \"table {{.Names}}\\t{{.Status}}\"')">copy</button></div>
        <div class="step-row"><div class="step-num">6</div><div class="step-body"><strong>Restart containers:</strong></div></div>
        <div class="cmd"><span class="cmd-text">cd C:\docker && docker-compose up -d</span><button class="copy-btn" onclick="cp(this,'cd C:\\docker && docker-compose up -d')">copy</button></div>
        <div class="note-box">After restart, VRAM shows 1-5% until first query. That is normal — models lazy-load on demand.</div>
      </div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-card-inner">
      <div class="play-header" onclick="togglePlay(this)">
        <span class="badge badge-red">CRITICAL</span>
        <span class="node-pill node-gandalf">GandalfAI</span>
        <span class="play-title">30+ second response delay, response gets cut off</span>
        <span class="play-chevron">&#x203A;</span>
      </div>
      <div class="play-body">
        <div class="note-box">Root cause is almost always VRAM pressure. gemma3:12b takes ~7GB + Chatterbox ~4.5GB. If Chrome, Claude Desktop, or any other GPU app is open on GandalfAI, VRAM overflows into system RAM and inference drops to 3-10 tok/s.</div>
        <div class="step-row"><div class="step-num">1</div><div class="step-body"><strong>Check VRAM on GandalfAI (PowerShell):</strong></div></div>
        <div class="cmd"><span class="cmd-text">nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv,noheader</span><button class="copy-btn" onclick="cp(this,'nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv,noheader')">copy</button></div>
        <div class="step-row"><div class="step-num">2</div><div class="step-body"><strong>Healthy: ~11-12GB used</strong> with IRIS active. <span class="flag">Bad: 23-24GB used</span> — close any browser or GUI apps on GandalfAI.</div></div>
        <div class="step-row"><div class="step-num">3</div><div class="step-body"><strong>Check Ollama model is registered:</strong></div></div>
        <div class="cmd"><span class="cmd-text">Invoke-RestMethod http://localhost:11434/api/tags | Select-Object -ExpandProperty models | Select-Object name</span><button class="copy-btn" onclick="cp(this,'Invoke-RestMethod http://localhost:11434/api/tags | Select-Object -ExpandProperty models | Select-Object name')">copy</button></div>
        <div class="step-row"><div class="step-num">4</div><div class="step-body"><strong>Response length too long?</strong> Check num_predict in modelfile — target is 120:</div></div>
        <div class="cmd"><span class="cmd-text">Select-String "num_predict" C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt</span><button class="copy-btn" onclick="cp(this,'Select-String \"num_predict\" C:\\IRIS\\IRIS-Robot-Face\\ollama\\iris_modelfile.txt')">copy</button></div>
        <div class="step-row"><div class="step-num">5</div><div class="step-body"><strong>Chatterbox latency:</strong> each audio chunk takes ~3-4s. A long response = multiple chunks. Fix is shorter LLM responses via modelfile, not faster TTS.</div></div>
      </div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-card-inner">
      <div class="play-header" onclick="togglePlay(this)">
        <span class="badge badge-red">CRITICAL</span>
        <span class="node-pill node-pi4">Pi4</span>
        <span class="play-title">Web UI config changes don't survive a reboot</span>
        <span class="play-chevron">&#x203A;</span>
      </div>
      <div class="play-body">
        <div class="note-box">The Pi4 uses overlayfs — all writes go to RAM and are wiped on reboot. The web UI persist button can fail silently if iris_config.json is owned by root instead of pi.</div>
        <div class="step-row"><div class="step-num">1</div><div class="step-body"><strong>Check file ownership:</strong></div></div>
        <div class="cmd"><span class="cmd-text">ls -la /home/pi/iris_config.json</span><button class="copy-btn" onclick="cp(this,'ls -la /home/pi/iris_config.json')">copy</button></div>
        <div class="step-row"><div class="step-num">2</div><div class="step-body"><strong>If owner is root — fix it:</strong></div></div>
        <div class="cmd"><span class="cmd-text">sudo chown pi:pi /home/pi/iris_config.json && sudo chmod 644 /home/pi/iris_config.json</span><button class="copy-btn" onclick="cp(this,'sudo chown pi:pi /home/pi/iris_config.json && sudo chmod 644 /home/pi/iris_config.json')">copy</button></div>
        <div class="step-row"><div class="step-num">3</div><div class="step-body"><strong>Persist to SD (required to survive reboot):</strong></div></div>
        <div class="cmd"><span class="cmd-text">sudo mount -o remount,rw /media/root-ro && sudo cp /home/pi/iris_config.json /media/root-ro/home/pi/iris_config.json && sudo mount -o remount,ro /media/root-ro</span><button class="copy-btn" onclick="cp(this,'sudo mount -o remount,rw /media/root-ro && sudo cp /home/pi/iris_config.json /media/root-ro/home/pi/iris_config.json && sudo mount -o remount,ro /media/root-ro')">copy</button></div>
        <div class="step-row"><div class="step-num">4</div><div class="step-body"><strong>Verify both copies match (md5 hashes must be identical):</strong></div></div>
        <div class="cmd"><span class="cmd-text">md5sum /home/pi/iris_config.json /media/root-ro/home/pi/iris_config.json</span><button class="copy-btn" onclick="cp(this,'md5sum /home/pi/iris_config.json /media/root-ro/home/pi/iris_config.json')">copy</button></div>
        <div class="note-box">If md5 hashes differ, the SD copy is out of sync. A mismatch means your change will be lost on reboot.</div>
      </div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-card-inner">
      <div class="play-header" onclick="togglePlay(this)">
        <span class="badge badge-amber">MEDIUM</span>
        <span class="node-pill node-pi4">Pi4</span>
        <span class="play-title">Robotic voice instead of Chatterbox — Piper fallback active</span>
        <span class="play-chevron">&#x203A;</span>
      </div>
      <div class="play-body">
        <div class="note-box">If IRIS sounds like a basic text-to-speech robot, Chatterbox has fallen back to Piper. Happens when the Chatterbox container is down or CHATTERBOX_ENABLED is false in iris_config.json.</div>
        <div class="step-row"><div class="step-num">1</div><div class="step-body"><strong>Check the config:</strong></div></div>
        <div class="cmd"><span class="cmd-text">cat /home/pi/iris_config.json</span><button class="copy-btn" onclick="cp(this,'cat /home/pi/iris_config.json')">copy</button></div>
        <div class="step-row"><div class="step-num">2</div><div class="step-body"><strong>CHATTERBOX_ENABLED should be true.</strong> If false, fix via Web UI or overlayroot-chroot write.</div></div>
        <div class="step-row"><div class="step-num">3</div><div class="step-body"><strong>Check Chatterbox container (GandalfAI PowerShell):</strong></div></div>
        <div class="cmd"><span class="cmd-text">docker ps | Select-String "chatterbox"</span><button class="copy-btn" onclick="cp(this,'docker ps | Select-String \"chatterbox\"')">copy</button></div>
        <div class="step-row"><div class="step-num">4</div><div class="step-body"><strong>Container not running — start it:</strong></div></div>
        <div class="cmd"><span class="cmd-text">cd C:\IRIS\docker && docker compose up -d</span><button class="copy-btn" onclick="cp(this,'cd C:\\IRIS\\docker && docker compose up -d')">copy</button></div>
        <div class="step-row"><div class="step-num">5</div><div class="step-body"><strong>Test Chatterbox directly (GandalfAI PowerShell):</strong></div></div>
        <div class="cmd"><span class="cmd-text">Invoke-WebRequest -Uri "http://localhost:8004/health" -UseBasicParsing</span><button class="copy-btn" onclick="cp(this,'Invoke-WebRequest -Uri \"http://localhost:8004/health\" -UseBasicParsing')">copy</button></div>
        <div class="note-box">If StatusCode 200 — Chatterbox is running. If connection refused: docker logs chatterbox --tail 20</div>
      </div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-card-inner">
      <div class="play-header" onclick="togglePlay(this)">
        <span class="badge badge-amber">MEDIUM</span>
        <span class="node-pill node-pi4">Pi4</span>
        <span class="play-title">Sleep/wake not working — wrong eyes, missing mouth animation</span>
        <span class="play-chevron">&#x203A;</span>
      </div>
      <div class="play-body">
        <div class="note-box">Sleep mode requires: eyes go to starfield, mouth goes blank (MOUTH:8), and /tmp/iris_sleep_mode flag is set. If any one is missing, sleep appears broken even if cron ran.</div>
        <div class="step-row"><div class="step-num">1</div><div class="step-body"><strong>Check sleep flag state:</strong></div></div>
        <div class="cmd"><span class="cmd-text">ls /tmp/iris_sleep_mode && echo "SLEEP FLAG: SET" || echo "SLEEP FLAG: NOT SET"</span><button class="copy-btn" onclick="cp(this,'ls /tmp/iris_sleep_mode && echo \"SLEEP FLAG: SET\" || echo \"SLEEP FLAG: NOT SET\"')">copy</button></div>
        <div class="step-row"><div class="step-num">2</div><div class="step-body"><strong>Check sleep cron log:</strong></div></div>
        <div class="cmd"><span class="cmd-text">tail -20 /home/pi/logs/iris_sleep.log</span><button class="copy-btn" onclick="cp(this,'tail -20 /home/pi/logs/iris_sleep.log')">copy</button></div>
        <div class="step-row"><div class="step-num">3</div><div class="step-body"><strong>Force sleep manually:</strong></div></div>
        <div class="cmd"><span class="cmd-text">python3 /home/pi/iris_sleep.py</span><button class="copy-btn" onclick="cp(this,'python3 /home/pi/iris_sleep.py')">copy</button></div>
        <div class="step-row"><div class="step-num">4</div><div class="step-body"><strong>Force wake:</strong></div></div>
        <div class="cmd"><span class="cmd-text">python3 /home/pi/iris_wake.py</span><button class="copy-btn" onclick="cp(this,'python3 /home/pi/iris_wake.py')">copy</button></div>
        <div class="step-row"><div class="step-num">5</div><div class="step-body"><strong>Confirm EYES:SLEEP and MOUTH:8 were sent to Teensy:</strong></div></div>
        <div class="cmd"><span class="cmd-text">journalctl -u assistant -n 40 --no-pager | grep -E "EYES|MOUTH|SLEEP|WAKE"</span><button class="copy-btn" onclick="cp(this,'journalctl -u assistant -n 40 --no-pager | grep -E \"EYES|MOUTH|SLEEP|WAKE\"')">copy</button></div>
        <div class="note-box">If EYES:SLEEP is logged but starfield does not appear — the USB serial connection to the Teensy is the problem. Check /dev/ttyACM0 exists.</div>
      </div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-card-inner">
      <div class="play-header" onclick="togglePlay(this)">
        <span class="badge badge-amber">MEDIUM</span>
        <span class="node-pill node-teensy">Teensy</span>
        <span class="play-title">Eyes or mouth display blank, frozen, or wrong</span>
        <span class="play-chevron">&#x203A;</span>
      </div>
      <div class="play-body">
        <div class="note-box">The Teensy receives serial commands from Pi4 over USB. If USB is lost or Teensy crashed, all display commands are silently dropped.</div>
        <div class="step-row"><div class="step-num">1</div><div class="step-body"><strong>Verify Teensy is recognized by Pi4:</strong></div></div>
        <div class="cmd"><span class="cmd-text">ls /dev/ttyACM* && dmesg | tail -10 | grep -i "tty\|usb\|teensy"</span><button class="copy-btn" onclick="cp(this,'ls /dev/ttyACM* && dmesg | tail -10 | grep -i \"tty\\|usb\\|teensy\"')">copy</button></div>
        <div class="step-row"><div class="step-num">2</div><div class="step-body"><strong>If /dev/ttyACM0 is missing</strong> — unplug and replug the USB cable. It should reappear.</div></div>
        <div class="step-row"><div class="step-num">3</div><div class="step-body"><strong>Send a test command to Teensy serial:</strong></div></div>
        <div class="cmd"><span class="cmd-text">echo "EMOTION:HAPPY" > /dev/ttyACM0</span><button class="copy-btn" onclick="cp(this,'echo \"EMOTION:HAPPY\" > /dev/ttyACM0')">copy</button></div>
        <div class="step-row"><div class="step-num">4</div><div class="step-body"><strong>If eyes go yellow</strong> — Teensy serial is working. Problem is Pi4 not sending commands.</div></div>
        <div class="step-row"><div class="step-num">5</div><div class="step-body"><strong>Mouth TFT only shows backlight (blank white)</strong> — power-cycle the Teensy (unplug USB 5 seconds, replug).</div></div>
        <div class="step-row"><div class="step-num">6</div><div class="step-body"><strong>Still wrong after power-cycle</strong> — reflash from PlatformIO on SuperMaster.</div></div>
      </div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-card-inner">
      <div class="play-header" onclick="togglePlay(this)">
        <span class="badge badge-amber">MEDIUM</span>
        <span class="node-pill node-pi4">Pi4</span>
        <span class="play-title">IRIS not hearing anything — mic not working</span>
        <span class="play-chevron">&#x203A;</span>
      </div>
      <div class="play-body">
        <div class="note-box">The ReSpeaker 2-Mic HAT is ALSA card "seeed2micvoicec". If IRIS never triggers on a clear "hey jarvis" close to the mic, the mic may have lost ALSA registration or volume dropped to zero.</div>
        <div class="step-row"><div class="step-num">1</div><div class="step-body"><strong>Confirm mic is detected:</strong></div></div>
        <div class="cmd"><span class="cmd-text">arecord -l | grep -i "seeed\|reSpeaker\|wm8960"</span><button class="copy-btn" onclick="cp(this,'arecord -l | grep -i \"seeed\\|reSpeaker\\|wm8960\"')">copy</button></div>
        <div class="step-row"><div class="step-num">2</div><div class="step-body"><strong>Record 5 seconds and play back to confirm mic picks up sound:</strong></div></div>
        <div class="cmd"><span class="cmd-text">arecord -D plughw:seeed2micvoicec,0 -f S16_LE -r 16000 -c 1 -d 5 /tmp/test.wav && aplay /tmp/test.wav</span><button class="copy-btn" onclick="cp(this,'arecord -D plughw:seeed2micvoicec,0 -f S16_LE -r 16000 -c 1 -d 5 /tmp/test.wav && aplay /tmp/test.wav')">copy</button></div>
        <div class="step-row"><div class="step-num">3</div><div class="step-body"><strong>If silent or very quiet — restore mic gain:</strong></div></div>
        <div class="cmd"><span class="cmd-text">amixer -c seeed2micvoicec sget Capture && amixer -c seeed2micvoicec sset Capture 90%</span><button class="copy-btn" onclick="cp(this,'amixer -c seeed2micvoicec sget Capture && amixer -c seeed2micvoicec sset Capture 90%')">copy</button></div>
        <div class="step-row"><div class="step-num">4</div><div class="step-body"><strong>Mic is fine but IRIS still won't trigger — check OWW_THRESHOLD:</strong></div></div>
        <div class="cmd"><span class="cmd-text">cat /home/pi/iris_config.json | python3 -c "import sys,json; d=json.load(sys.stdin); print('OWW_THRESHOLD:', d.get('OWW_THRESHOLD','check config.py'))"</span><button class="copy-btn" onclick="cp(this,'cat /home/pi/iris_config.json | python3 -c \"import sys,json; d=json.load(sys.stdin); print(\'OWW_THRESHOLD:\', d.get(\'OWW_THRESHOLD\',\'check config.py\'))\"')">copy</button></div>
        <div class="note-box">Normal range: 0.85-0.95. Lower = easier to trigger. Higher = requires clearer pronunciation. Default is 0.9.</div>
      </div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-card-inner">
      <div class="play-header" onclick="togglePlay(this)">
        <span class="badge badge-gray">LOW</span>
        <span class="node-pill node-pi4">Pi4</span>
        <span class="play-title">IRIS gives wrong personality — kids mode stuck on or off</span>
        <span class="play-chevron">&#x203A;</span>
      </div>
      <div class="play-body">
        <div class="note-box">IRIS has two modelfiles: iris (adult) and iris-kids. If IRIS is overly cautious or speaking like a kids show host when it should not be, kids mode may be stuck.</div>
        <div class="step-row"><div class="step-num">1</div><div class="step-body"><strong>Check kids mode flag:</strong></div></div>
        <div class="cmd"><span class="cmd-text">ls /tmp/iris_kids_mode 2>/dev/null && echo "KIDS MODE: ON" || echo "KIDS MODE: OFF"</span><button class="copy-btn" onclick="cp(this,'ls /tmp/iris_kids_mode 2>/dev/null && echo \"KIDS MODE: ON\" || echo \"KIDS MODE: OFF\"')">copy</button></div>
        <div class="step-row"><div class="step-num">2</div><div class="step-body"><strong>If stuck on — remove the flag:</strong></div></div>
        <div class="cmd"><span class="cmd-text">rm /tmp/iris_kids_mode</span><button class="copy-btn" onclick="cp(this,'rm /tmp/iris_kids_mode')">copy</button></div>
        <div class="step-row"><div class="step-num">3</div><div class="step-body"><strong>If personality is wrong in adult mode</strong> — modelfile may have drifted or was not rebuilt after the last edit. Flag to Claude Code.</div></div>
      </div>
    </div>
  </div>
</div>

<div id="tab-falsewake" class="panel">
  <div class="section-label" style="color:#A32D2D">Playbook: investigating false wakeword triggers</div>
  <div class="card">
    <div class="card-body">IRIS fires without you saying "hey jarvis." This playbook walks through all known causes and how to diagnose which one is responsible — from threshold settings to mic placement to TV audio interference.</div>
  </div>

  <div class="play-card">
    <div class="play-card-inner">
      <div class="play-header" onclick="togglePlay(this)">
        <span class="badge badge-blue">Step 1</span>
        <span class="play-title">Confirm it is actually a false trigger — not a real one</span>
        <span class="play-chevron">&#x203A;</span>
      </div>
      <div class="play-body">
        <div class="note-box">Before diagnosing, confirm the trigger happened and what audio caused it. The assistant log timestamps every wakeword detection.</div>
        <div class="cmd"><span class="cmd-text">journalctl -u assistant --since "1 hour ago" --no-pager | grep -E "WAKE|wake|detected|threshold"</span><button class="copy-btn" onclick="cp(this,'journalctl -u assistant --since \"1 hour ago\" --no-pager | grep -E \"WAKE|wake|detected|threshold\"')">copy</button></div>
        <div class="step-row"><div class="step-num">?</div><div class="step-body">Look for <strong>[WAKE] Wake word detected</strong> lines with timestamps. What was happening in the room at that time? TV? Kids talking? Music?</div></div>
        <div class="step-row"><div class="step-num">?</div><div class="step-body">Also check what Whisper transcribed — empty string or gibberish means the wakeword model got confused by noise, not speech:</div></div>
        <div class="cmd"><span class="cmd-text">journalctl -u assistant --since "1 hour ago" --no-pager | grep -E "STT|transcri"</span><button class="copy-btn" onclick="cp(this,'journalctl -u assistant --since \"1 hour ago\" --no-pager | grep -E \"STT|transcri\"')">copy</button></div>
      </div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-card-inner">
      <div class="play-header" onclick="togglePlay(this)">
        <span class="badge badge-blue">Step 2</span>
        <span class="play-title">Check and adjust the wakeword threshold</span>
        <span class="play-chevron">&#x203A;</span>
      </div>
      <div class="play-body">
        <div class="note-box">The threshold is how confident openwakeword must be before triggering IRIS. Higher = fewer false triggers. Lower = more responsive but TV/conversation can trigger it.</div>
        <div class="step-row"><div class="step-num">1</div><div class="step-body"><strong>Current threshold:</strong></div></div>
        <div class="cmd"><span class="cmd-text">cat /home/pi/iris_config.json | python3 -c "import sys,json; d=json.load(sys.stdin); print('OWW_THRESHOLD:', d.get('OWW_THRESHOLD','check core/config.py'))"</span><button class="copy-btn" onclick="cp(this,'cat /home/pi/iris_config.json | python3 -c \"import sys,json; d=json.load(sys.stdin); print(\'OWW_THRESHOLD:\', d.get(\'OWW_THRESHOLD\', \'check core/config.py\'))\"')">copy</button></div>
        <div class="divider"></div>
        <div class="grid2" style="font-size:11px;margin:6px 0">
          <div class="card" style="padding:8px 10px"><div style="font-weight:500;margin-bottom:4px">0.75 — sensitive</div><div style="color:var(--color-text-secondary)">Triggers easily. Good for quiet rooms. Will false-trigger on TV or similar phonemes.</div></div>
          <div class="card" style="padding:8px 10px"><div style="font-weight:500;margin-bottom:4px">0.85 — balanced</div><div style="color:var(--color-text-secondary)">Good starting point for normal home noise. May miss soft "hey jarvis" from far away.</div></div>
          <div class="card" style="padding:8px 10px;border:0.5px solid #B5D4F4"><div style="font-weight:500;margin-bottom:4px">0.90 — default (current)</div><div style="color:var(--color-text-secondary)">Strict. Requires clear, close pronunciation. Significantly reduces TV and ambient false triggers.</div></div>
          <div class="card" style="padding:8px 10px"><div style="font-weight:500;margin-bottom:4px">0.95 — very strict</div><div style="color:var(--color-text-secondary)">Only deliberate, clear speech close to mic. May frustrate if IRIS frequently misses you.</div></div>
        </div>
        <div class="step-row"><div class="step-num">2</div><div class="step-body"><strong>Raise threshold to reduce false triggers:</strong></div></div>
        <div class="cmd"><span class="cmd-text">sudo bash -c 'python3 -c "import json; d=json.load(open(\"/home/pi/iris_config.json\")); d[\"OWW_THRESHOLD\"]=0.92; open(\"/home/pi/iris_config.json\",\"w\").write(json.dumps(d,indent=2))"'</span><button class="copy-btn" onclick="cp(this,'sudo bash -c \'python3 -c \"import json; d=json.load(open(\\\"/home/pi/iris_config.json\\\")); d[\\\"OWW_THRESHOLD\\\"]=0.92; open(\\\"/home/pi/iris_config.json\\\",\\\"w\\\").write(json.dumps(d,indent=2))\"\'')">copy</button></div>
        <div class="step-row"><div class="step-num">3</div><div class="step-body"><strong>Restart assistant:</strong></div></div>
        <div class="cmd"><span class="cmd-text">sudo systemctl restart assistant</span><button class="copy-btn" onclick="cp(this,'sudo systemctl restart assistant')">copy</button></div>
        <div class="note-box">Always persist this change to SD after verifying it works. A reboot without persisting will reset to the old value.</div>
      </div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-card-inner">
      <div class="play-header" onclick="togglePlay(this)">
        <span class="badge badge-blue">Step 3</span>
        <span class="play-title">Watch live wakeword confidence scores</span>
        <span class="play-chevron">&#x203A;</span>
      </div>
      <div class="play-body">
        <div class="note-box">The most useful diagnostic. Watch the raw confidence score in real-time. You can see exactly when scores spike above threshold and what was happening at that moment.</div>
        <div class="cmd"><span class="cmd-text">journalctl -u wyoming-openwakeword -f --no-pager</span><button class="copy-btn" onclick="cp(this,'journalctl -u wyoming-openwakeword -f --no-pager')">copy</button></div>
        <div class="step-row"><div class="step-num">?</div><div class="step-body">Walk around the room, turn the TV on, have a conversation. Watch the scores. Normal ambient: <strong>0.0-0.3</strong>. Spike above <strong>0.7</strong> means the model heard something similar to "hey jarvis." Your threshold is the line that determines whether that spike fires IRIS.</div></div>
        <div class="step-row"><div class="step-num">?</div><div class="step-body">If scores regularly spike to <strong>0.8+</strong> from TV audio, your threshold needs to go above that spike level, or the mic needs repositioning away from the TV.</div></div>
      </div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-card-inner">
      <div class="play-header" onclick="togglePlay(this)">
        <span class="badge badge-blue">Step 4</span>
        <span class="play-title">Identify the audio source causing false triggers</span>
        <span class="play-chevron">&#x203A;</span>
      </div>
      <div class="play-body">
        <div class="note-box">The openwakeword model was trained on recordings of people saying "hey jarvis." It does not understand words — only sound patterns. Common culprits in this household:</div>
        <div class="step-row"><div class="step-num">TV</div><div class="step-body"><strong>TV / streaming audio</strong> — dialogue frequently contains syllable patterns similar to "hey jarvis." Keep TV volume lower in IRIS's room, or reposition the mic away from the TV.</div></div>
        <div class="step-row"><div class="step-num">Kids</div><div class="step-body"><strong>Leo and Mae's voices</strong> — children's speech at certain pitches can score surprisingly high. Raise the threshold if this is the source.</div></div>
        <div class="step-row"><div class="step-num">IRIS</div><div class="step-body"><strong>IRIS's own voice</strong> — rare, but IRIS speaking loudly can occasionally trigger a second wakeword mid-response. Lower speaker volume slightly if this happens repeatedly.</div></div>
        <div class="step-row"><div class="step-num">Boot</div><div class="step-body"><strong>ALSA noise burst at startup</strong> — the audio system generates a spike when initializing. Normal one-time occurrence at boot. Not a real problem.</div></div>
      </div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-card-inner">
      <div class="play-header" onclick="togglePlay(this)">
        <span class="badge badge-blue">Step 5</span>
        <span class="play-title">Check SILENCE_RMS — IRIS responding to empty audio</span>
        <span class="play-chevron">&#x203A;</span>
      </div>
      <div class="play-body">
        <div class="note-box">A subtle false-trigger variant: the wakeword fires correctly, but Whisper transcribes empty audio as silence or gibberish. IRIS should drop these. If IRIS is responding to nothing, SILENCE_RMS may be too low.</div>
        <div class="cmd"><span class="cmd-text">journalctl -u assistant --since "2 hours ago" --no-pager | grep -A2 "WAKE"</span><button class="copy-btn" onclick="cp(this,'journalctl -u assistant --since \"2 hours ago\" --no-pager | grep -A2 \"WAKE\"')">copy</button></div>
        <div class="step-row"><div class="step-num">?</div><div class="step-body">Look for [WAKE] lines followed by [STT] with an empty or 1-2 character string. That means the wakeword triggered but no real speech followed.</div></div>
        <div class="step-row"><div class="step-num">?</div><div class="step-body"><strong>Check current SILENCE_RMS:</strong></div></div>
        <div class="cmd"><span class="cmd-text">cat /home/pi/iris_config.json | python3 -c "import sys,json; d=json.load(sys.stdin); print('SILENCE_RMS:', d.get('SILENCE_RMS','not set'))"</span><button class="copy-btn" onclick="cp(this,'cat /home/pi/iris_config.json | python3 -c \"import sys,json; d=json.load(sys.stdin); print(\'SILENCE_RMS:\', d.get(\'SILENCE_RMS\', \'not set\'))\"')">copy</button></div>
        <div class="note-box">Target value: 300. If near-silence is passing through, raise to 400-500.</div>
        <div class="cmd"><span class="cmd-text">sudo bash -c 'python3 -c "import json; d=json.load(open(\"/home/pi/iris_config.json\")); d[\"SILENCE_RMS\"]=350; open(\"/home/pi/iris_config.json\",\"w\").write(json.dumps(d,indent=2))"' && sudo systemctl restart assistant</span><button class="copy-btn" onclick="cp(this,'sudo bash -c \'python3 -c \"import json; d=json.load(open(\\\"/home/pi/iris_config.json\\\")); d[\\\"SILENCE_RMS\\\"]=350; open(\\\"/home/pi/iris_config.json\\\",\\\"w\\\").write(json.dumps(d,indent=2))\"\'&& sudo systemctl restart assistant')">copy</button></div>
      </div>
    </div>
  </div>

  <div class="play-card">
    <div class="play-card-inner">
      <div class="play-header" onclick="togglePlay(this)">
        <span class="badge badge-blue">Step 6</span>
        <span class="play-title">Nuclear option — switch to a less common wakeword</span>
        <span class="play-chevron">&#x203A;</span>
      </div>
      <div class="play-body">
        <div class="note-box">If threshold tuning doesn't solve it, the "hey jarvis" model may just be too similar to audio in this home. The easiest long-term fix is switching to a wakeword with no phonetic overlap with normal conversation or TV dialogue.</div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin:8px 0">
          <div class="card" style="padding:7px 9px;font-size:11px"><strong>computer</strong><br><span style="color:var(--color-text-secondary)">Short, distinctive. Star Trek feel. Lower false-trigger rate than "hey X" phrases.</span></div>
          <div class="card" style="padding:7px 9px;font-size:11px"><strong>hey_mycroft</strong><br><span style="color:var(--color-text-secondary)">Unusual name. Very low chance of natural speech overlap.</span></div>
          <div class="card" style="padding:7px 9px;font-size:11px"><strong>hey_rhasspy</strong><br><span style="color:var(--color-text-secondary)">Unusual name. Lowest false trigger rate of available models.</span></div>
        </div>
        <div class="step-row"><div class="step-num">?</div><div class="step-body"><strong>Find the current model path in assistant.py (Claude Code task):</strong></div></div>
        <div class="cmd"><span class="cmd-text">grep -n "hey_jarvis\|wakeword\|model_path\|OWW_MODEL" /home/pi/assistant.py | head -10</span><button class="copy-btn" onclick="cp(this,'grep -n \"hey_jarvis\\|wakeword\\|model_path\\|OWW_MODEL\" /home/pi/assistant.py | head -10')">copy</button></div>
      </div>
    </div>
  </div>

  <div class="card" style="margin-top:12px;background:var(--color-background-secondary)">
    <div class="card-title" style="font-size:12px">Quick decision tree — false wakeword</div>
    <div class="step-row"><div class="step-num">1</div><div class="step-body">Check log timestamps vs room activity — confirm it is a false trigger vs one you forgot about</div></div>
    <div class="step-row"><div class="step-num">2</div><div class="step-body">Watch live OWW confidence scores — see how close ambient audio is to your threshold</div></div>
    <div class="step-row"><div class="step-num">3</div><div class="step-body">Raise OWW_THRESHOLD from 0.90 to 0.92 to 0.95 until false triggers stop, then confirm IRIS still responds to you</div></div>
    <div class="step-row"><div class="step-num">4</div><div class="step-body">If IRIS responds to nothing (empty audio): raise SILENCE_RMS from 300 to 400</div></div>
    <div class="step-row"><div class="step-num">5</div><div class="step-body">If problem persists regardless of threshold: switch wakeword model (Claude Code task)</div></div>
  </div>
</div>

<script>
function switchTab(name){document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));document.querySelector('[onclick="switchTab(\''+name+'\')"]').classList.add('active');document.getElementById('tab-'+name).classList.add('active')}
function togglePlay(el){const body=el.nextElementSibling;const title=el.querySelector('.play-title');const chev=el.querySelector('.play-chevron');const open=body.classList.contains('open');body.classList.toggle('open',!open);title.classList.toggle('open',!open);chev.classList.toggle('open',!open)}
function cp(btn,text){navigator.clipboard.writeText(text).then(()=>{const orig=btn.textContent;btn.textContent='copied';setTimeout(()=>btn.textContent=orig,1500)})}
</script>
</body>
</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)

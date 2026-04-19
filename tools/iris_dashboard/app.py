
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
:root{--bg:#0d0f14;--bg2:#151820;--bg3:#1c1f2a;--bd:#252836;--text:#e2e4ed;--muted:#6b6e7e;--green:#1db87a;--amber:#d4870f;--red:#d94848;--blue:#3b8add;--cyan:#1a9a8a;font-family:'Segoe UI',system-ui,sans-serif;font-size:14px}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);padding:18px;min-height:100vh}
.hdr{display:flex;align-items:center;justify-content:space-between;padding-bottom:14px;border-bottom:1px solid var(--bd);margin-bottom:18px}
.hdr-l{display:flex;align-items:center;gap:12px}
.eye{width:30px;height:30px;border-radius:50%;background:var(--cyan);display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0}
h1{font-size:17px;font-weight:600;letter-spacing:-.3px}
.sub{font-size:11px;color:var(--muted);margin-top:2px}
.ts-label{font-size:11px;color:var(--muted);font-family:monospace}
.grafana-btn{display:inline-flex;align-items:center;gap:6px;background:var(--bg2);border:1px solid var(--bd);border-radius:8px;padding:8px 13px;font-size:12px;color:var(--text);text-decoration:none;margin-bottom:18px;transition:border-color .15s}
.grafana-btn:hover{border-color:var(--amber)}
.section{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.07em;margin-bottom:9px}
.grid4{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:18px}
.card{background:var(--bg2);border:1px solid var(--bd);border-radius:10px;padding:14px 16px}
.card-lbl{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px}
.big{font-size:26px;font-weight:600;font-family:monospace;line-height:1}
.card-sub{font-size:11px;color:var(--muted);margin-top:4px}
.bar-wrap{margin-top:10px;background:var(--bg3);border-radius:4px;height:7px;overflow:hidden}
.bar{height:100%;border-radius:4px;transition:width .6s,background .6s}
.svcs{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin-bottom:18px}
.svc{background:var(--bg2);border:1px solid var(--bd);border-radius:8px;padding:10px 13px;display:flex;align-items:center;justify-content:space-between}
.svc-name{font-size:12px;font-weight:500}
.svc-port{font-size:10px;color:var(--muted);margin-top:2px}
.dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;transition:background .4s}
.dot-on{background:var(--green);box-shadow:0 0 5px var(--green)}
.dot-off{background:var(--red)}
.dot-uk{background:var(--muted)}
.lat-card{background:var(--bg2);border:1px solid var(--bd);border-radius:10px;padding:14px 16px;margin-bottom:18px}
.lat-row{display:flex;align-items:center;gap:10px;padding:5px 0;border-bottom:1px solid var(--bd)}
.lat-row:last-child{border:none}
.lat-lbl{font-size:11px;color:var(--muted);width:72px;flex-shrink:0}
.lat-bw{flex:1;background:var(--bg3);border-radius:3px;height:5px;overflow:hidden}
.lat-b{height:100%;border-radius:3px;background:var(--cyan);transition:width .5s}
.lat-val{font-size:11px;font-family:monospace;color:var(--muted);width:56px;text-align:right}
.btn-row{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:6px}
.btn{background:var(--bg3);border:1px solid var(--bd);color:var(--text);border-radius:6px;padding:7px 13px;font-size:12px;cursor:pointer;transition:all .15s}
.btn:hover{border-color:var(--blue);color:var(--blue)}
.btn:active{transform:scale(.97)}
.restart-msg{font-size:11px;color:var(--muted);min-height:16px;margin-bottom:14px}
.log-box{background:var(--bg2);border:1px solid var(--bd);border-radius:10px;padding:12px 14px;font-family:monospace;font-size:11px;line-height:1.7;color:#8a8da0;max-height:240px;overflow-y:auto;margin-bottom:18px;white-space:pre-wrap;word-break:break-all}
.lerr{color:var(--red)}.lwarn{color:var(--amber)}.lok{color:var(--green)}
.acc{margin-bottom:7px}
.acc-hdr{background:var(--bg2);border:1px solid var(--bd);border-radius:8px;padding:11px 15px;cursor:pointer;display:flex;align-items:center;justify-content:space-between;transition:background .15s;user-select:none}
.acc-hdr:hover{background:var(--bg3)}
.acc-title{font-size:12px;font-weight:500;display:flex;align-items:center;gap:7px}
.chev{font-size:10px;color:var(--muted);transition:transform .18s}
.chev.open{transform:rotate(90deg)}
.acc-body{display:none;background:var(--bg2);border:1px solid var(--bd);border-top:none;border-radius:0 0 8px 8px;padding:12px 15px}
.acc-body.open{display:block}
.step{display:flex;gap:9px;align-items:flex-start;padding:7px 0;border-bottom:1px solid var(--bd);font-size:12px;line-height:1.6}
.step:last-child{border:none}
.snum{width:17px;height:17px;border-radius:50%;background:rgba(59,138,221,.18);color:var(--blue);font-size:10px;font-weight:500;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:2px}
.stxt{color:var(--muted)}.stxt strong{color:var(--text)}
.cmd{background:var(--bg3);border:1px solid var(--bd);border-radius:5px;padding:7px 10px;font-family:monospace;font-size:10px;color:#8a8da0;margin:5px 0;position:relative;white-space:pre-wrap;word-break:break-all;padding-right:52px}
.cpbtn{position:absolute;top:4px;right:6px;background:var(--bg2);border:1px solid var(--bd);border-radius:4px;font-size:9px;padding:2px 6px;cursor:pointer;color:var(--muted);font-family:'Segoe UI',sans-serif}
.cpbtn:hover{color:var(--text)}
.badge{display:inline-block;font-size:9px;font-weight:500;padding:1px 6px;border-radius:8px;margin-left:5px;background:rgba(212,135,15,.15);color:var(--amber)}
hr{border:none;border-top:1px solid var(--bd);margin:18px 0}
</style>
</head>
<body>

<div class="hdr">
  <div class="hdr-l">
    <div class="eye">&#128065;</div>
    <div>
      <h1>IRIS Mission Control</h1>
      <div class="sub">GandalfAI &middot; Pi4 &middot; Teensy &mdash; live pipeline dashboard</div>
    </div>
  </div>
  <span class="ts-label" id="ts">--</span>
</div>

<a class="grafana-btn" href="http://192.168.1.3:3001/d/vlvPlrgnk/nvidia-gpu-metrics?orgId=1&from=now-30m&to=now&timezone=browser&var-job=nvidia_gpu_exporter&var-node=localhost:9835&var-gpu=f9c212bc-0533-d705-4e10-9377be35c908&refresh=5s" target="_blank">
  &#128202; Grafana &mdash; LLM utilization &amp; GPU history &rarr;
</a>

<div class="section">GPU / VRAM &mdash; GandalfAI RTX 3090</div>
<div class="grid4">
  <div class="card">
    <div class="card-lbl">VRAM used</div>
    <div class="big" id="vram-used">--</div>
    <div class="card-sub" id="vram-sub">of -- GB</div>
    <div class="bar-wrap"><div class="bar" id="vram-bar" style="width:0%"></div></div>
  </div>
  <div class="card">
    <div class="card-lbl">VRAM free</div>
    <div class="big" id="vram-free">--</div>
    <div class="card-sub">GB available</div>
  </div>
  <div class="card">
    <div class="card-lbl">GPU utilization</div>
    <div class="big" id="gpu-util">--</div>
    <div class="card-sub">percent</div>
  </div>
  <div class="card">
    <div class="card-lbl">Temp / power</div>
    <div class="big" id="gpu-temp">--</div>
    <div class="card-sub" id="gpu-power">-- W</div>
  </div>
</div>

<div class="section">Service status</div>
<div class="svcs">
  <div class="svc"><div><div class="svc-name">Ollama LLM</div><div class="svc-port">:11434 &mdash; GandalfAI</div></div><div class="dot dot-uk" id="s-ollama"></div></div>
  <div class="svc"><div><div class="svc-name">Whisper STT</div><div class="svc-port">:10300 &mdash; GandalfAI</div></div><div class="dot dot-uk" id="s-whisper"></div></div>
  <div class="svc"><div><div class="svc-name">Piper TTS</div><div class="svc-port">:10200 &mdash; GandalfAI</div></div><div class="dot dot-uk" id="s-piper"></div></div>
  <div class="svc"><div><div class="svc-name">Chatterbox</div><div class="svc-port">:8004 &mdash; GandalfAI</div></div><div class="dot dot-uk" id="s-chatterbox"></div></div>
  <div class="svc"><div><div class="svc-name">Assistant</div><div class="svc-port">Pi4 systemd unit</div></div><div class="dot dot-uk" id="s-assistant"></div></div>
</div>

<div class="section">Pipeline latency &mdash; last interaction</div>
<div class="lat-card">
  <div class="lat-row"><span class="lat-lbl">Wakeword</span><div class="lat-bw"><div class="lat-b" id="lb-wakeword" style="width:0%"></div></div><span class="lat-val" id="lv-wakeword">--</span></div>
  <div class="lat-row"><span class="lat-lbl">STT</span><div class="lat-bw"><div class="lat-b" id="lb-stt" style="width:0%"></div></div><span class="lat-val" id="lv-stt">--</span></div>
  <div class="lat-row"><span class="lat-lbl">LLM</span><div class="lat-bw"><div class="lat-b" id="lb-llm" style="width:0%"></div></div><span class="lat-val" id="lv-llm">--</span></div>
  <div class="lat-row"><span class="lat-lbl">TTS</span><div class="lat-bw"><div class="lat-b" id="lb-tts" style="width:0%"></div></div><span class="lat-val" id="lv-tts">--</span></div>
</div>

<div class="section">Restart services</div>
<div class="btn-row">
  <button class="btn" onclick="restart('assistant')">&#8635; Restart assistant (Pi4)</button>
  <button class="btn" onclick="restart('whisper')">&#8635; Restart Whisper</button>
  <button class="btn" onclick="restart('piper')">&#8635; Restart Piper</button>
  <button class="btn" onclick="restart('chatterbox')">&#8635; Restart Chatterbox</button>
</div>
<div class="restart-msg" id="rmsg"></div>

<div class="section">Pi4 assistant log &mdash; last 30 lines</div>
<div class="log-box" id="logbox">Loading...</div>

<hr>
<div class="section">Troubleshooting playbooks</div>
<div id="playbooks"></div>

<script>
const PB = [
  {icon:"&#128034;",title:"Response is slow (15-45 seconds)",badge:"Most common",steps:[
    {t:"Check VRAM first",n:"If free VRAM is under 200 MB, Ollama is spilling to system RAM and runs 5-10x slower. The VRAM free card above shows this directly.",cmd:"powershell -Command \"nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader\"",where:"GandalfAI"},
    {t:"Close GPU apps on GandalfAI",n:"Chrome, Claude Desktop, or any video playing on GandalfAI eat VRAM. Only Chatterbox and Ollama should run."},
    {t:"Restart the assistant service",n:"Clears stuck pipeline state on Pi4.",cmd:"sudo systemctl restart assistant",where:"Pi4"},
    {t:"First response after idle is always 4-5s slower",n:"Ollama reloads the 27b model from disk on first use after OLLAMA_KEEP_ALIVE (20m) expires. Normal. Second response is fast."},
  ]},
  {icon:"&#9986;",title:"Response cut off mid-sentence",steps:[
    {t:"Check logs for TTS errors around the cutoff time",cmd:"sudo journalctl -u assistant -n 80 --no-pager | grep -E \"ERROR|TTS|CHATTER|chunk|timeout\"",where:"Pi4"},
    {t:"Check Chatterbox health",n:"If no response, Chatterbox crashed mid-generation. Use the restart button above.",cmd:"powershell -Command \"Invoke-RestMethod http://localhost:8004/health\"",where:"GandalfAI"},
    {t:"Restart assistant - usually fixes it",n:"Most cutoffs are a one-off buffer timing issue, not a persistent fault.",cmd:"sudo systemctl restart assistant",where:"Pi4"},
    {t:"If it happens consistently on long replies",n:"num_predict may have been lost from the modelfile. Tell Claude Code to verify PARAMETER num_predict 80 is in jarvis_modelfile.txt on GandalfAI."},
  ]},
  {icon:"&#128566;",title:"Wakeword heard but no response",steps:[
    {t:"Check GandalfAI is awake",n:"Pi4 should send WoL automatically. Wait 30 seconds after no ping response, then try again.",cmd:"ping 192.168.1.3 -c 2",where:"Pi4"},
    {t:"Check Wyoming containers",n:"Both wyoming-whisper-1 and wyoming-piper-1 should show Up.",cmd:"powershell -Command \"docker ps --filter 'name=wyoming' --format '{{.Names}} {{.Status}}'\"",where:"GandalfAI"},
    {t:"Read log tail for the exact error",cmd:"sudo journalctl -u assistant -n 40 --no-pager",where:"Pi4"},
    {t:"Restart Wyoming stack if containers are stopped",cmd:"powershell -Command \"cd C:\\docker; docker compose up -d\"",where:"GandalfAI"},
  ]},
  {icon:"&#129302;",title:"Robotic Piper voice instead of IRIS voice",steps:[
    {t:"Confirm Chatterbox is enabled in config",cmd:"cat /home/pi/iris_config.json | python3 -m json.tool | grep -i chatterbox",where:"Pi4",n:"CHATTERBOX_ENABLED should be true."},
    {t:"Check Chatterbox health",n:"If connection refused, Chatterbox is not running. Use the restart button above.",cmd:"powershell -Command \"Invoke-RestMethod http://localhost:8004/health\"",where:"GandalfAI"},
    {t:"Chatterbox does not auto-start on GandalfAI boot",n:"Known gap. If GandalfAI rebooted, Chatterbox needs manual start. Ask Claude Code to wire up auto-start."},
  ]},
  {icon:"&#128565;",title:"Config changes not surviving reboot",steps:[
    {t:"Check RAM vs SD card diff",n:"Any output means the SD copy is stale and changes will be lost on next reboot.",cmd:"diff <(cat /home/pi/iris_config.json) <(sudo cat /media/root-ro/home/pi/iris_config.json 2>/dev/null || echo NOT_ON_SD)",where:"Pi4"},
    {t:"Pi4 uses overlayfs - writes go to RAM, not SD",n:"The web UI save-to-SD button is unreliable. Always hand persistent config changes to Claude Code using overlayroot-chroot."},
    {t:"Verify every config change survived reboot",n:"After any edit: reboot Pi4, then run cat /home/pi/iris_config.json to confirm the value is still there."},
  ]},
  {icon:"&#127769;",title:"Sleep or wake not working",steps:[
    {t:"Check if sleep flag exists right now",cmd:"ls -la /tmp/iris_sleep_mode 2>/dev/null && echo SLEEPING || echo AWAKE",where:"Pi4"},
    {t:"Check cron entries",n:"Should show 9PM sleep and 7:30AM wake. If missing, cron was lost - tell Claude Code.",cmd:"crontab -l | grep iris",where:"Pi4"},
    {t:"Manually trigger sleep to test",cmd:"sudo -u pi python3 /home/pi/iris_sleep.py",where:"Pi4"},
    {t:"Manually trigger wake to test",cmd:"sudo -u pi python3 /home/pi/iris_wake.py",where:"Pi4"},
  ]},
  {icon:"&#128065;",title:"Eyes or mouth display not responding",steps:[
    {t:"Check Teensy is visible on USB",n:"Should show /dev/ttyACM0. If missing, reseat the USB cable from Teensy to Pi4.",cmd:"ls /dev/ttyACM* 2>/dev/null || echo 'No Teensy device found'",where:"Pi4"},
    {t:"Send a test serial command",n:"If the eyes change expression, serial communication is working.",cmd:"echo 'EYES:WAKE' | sudo tee /dev/ttyACM0",where:"Pi4"},
    {t:"Check logs for serial errors",cmd:"sudo journalctl -u assistant -n 50 --no-pager | grep -iE 'serial|teensy|tty|EYES|MOUTH'",where:"Pi4"},
    {t:"If Teensy is missing after USB reseat",n:"Firmware reflash required. That needs SuperMaster + PlatformIO. Do not attempt via SSH."},
  ]},
];

function cp(btn, text) {
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = "copied";
    setTimeout(() => btn.textContent = "copy", 1200);
  });
}

function acc(i) {
  document.getElementById("ab-" + i).classList.toggle("open");
  document.getElementById("ac-" + i).classList.toggle("open");
}

function renderPB() {
  document.getElementById("playbooks").innerHTML = PB.map((p, i) => `
    <div class="acc">
      <div class="acc-hdr" onclick="acc(${i})">
        <span class="acc-title">${p.icon} ${p.title}${p.badge ? `<span class="badge">${p.badge}</span>` : ""}</span>
        <span class="chev" id="ac-${i}">&#8250;</span>
      </div>
      <div class="acc-body" id="ab-${i}">
        ${p.steps.map((s, j) => `
          <div class="step">
            <div class="snum">${j + 1}</div>
            <div class="stxt">
              <strong>${s.t}</strong>${s.where ? ` <span style="font-size:10px;color:var(--muted)">[run on ${s.where}]</span>` : ""}
              ${s.n ? `<br>${s.n}` : ""}
              ${s.cmd ? `<div class="cmd">${s.cmd}<button class="cpbtn" onclick="cp(this,'${s.cmd.replace(/\\/g,"\\\\").replace(/'/g,"\\'")}')">copy</button></div>` : ""}
            </div>
          </div>`).join("")}
      </div>
    </div>`).join("");
}

function setDot(id, state) {
  const el = document.getElementById(id);
  if (!el) return;
  el.className = "dot " + (state === null ? "dot-uk" : state ? "dot-on" : "dot-off");
}

function refresh() {
  fetch("/api/status")
    .then(r => r.json())
    .then(d => {
      document.getElementById("ts").textContent = "Updated " + new Date(d.ts).toLocaleTimeString();

      const v = d.vram;
      if (v.used_gb !== null) {
        document.getElementById("vram-used").textContent = v.used_gb + " GB";
        document.getElementById("vram-free").textContent = v.free_gb + " GB";
        document.getElementById("vram-sub").textContent = "of " + v.total_gb + " GB total";
        const pct = v.pct || 0;
        const bar = document.getElementById("vram-bar");
        bar.style.width = pct + "%";
        bar.style.background = pct > 97 ? "var(--red)" : pct > 88 ? "var(--amber)" : "var(--cyan)";
      }

      const g = d.gpu;
      document.getElementById("gpu-util").textContent = g.util_pct !== null ? g.util_pct + "%" : "--";
      document.getElementById("gpu-temp").textContent = g.temp_c !== null ? g.temp_c + " C" : "--";
      document.getElementById("gpu-power").textContent = g.power_w !== null ? g.power_w + " W" : "--";

      const s = d.services;
      setDot("s-ollama",     s.ollama);
      setDot("s-whisper",    s.whisper);
      setDot("s-piper",      s.piper);
      setDot("s-chatterbox", s.chatterbox);
      setDot("s-assistant",  s.assistant_pi4);

      const lat = d.latency;
      const vals = Object.values(lat).filter(Boolean);
      const maxLat = vals.length ? Math.max(...vals) : 1000;
      ["wakeword", "stt", "llm", "tts"].forEach(k => {
        const val = lat[k];
        document.getElementById("lv-" + k).textContent = val ? val + "ms" : "--";
        document.getElementById("lb-" + k).style.width = val ? Math.min(100, val / maxLat * 100) + "%" : "0%";
      });

      const logEl = document.getElementById("logbox");
      logEl.innerHTML = (d.logs || []).map(line => {
        const l = line.toLowerCase();
        const cls = (l.includes("error") || l.includes("failed") || l.includes("traceback")) ? "lerr"
                  : (l.includes("warn") || l.includes("timeout") || l.includes("retry"))     ? "lwarn"
                  : (l.includes("started") || l.includes("ready") || l.includes("active"))   ? "lok"
                  : "";
        return cls ? `<span class="${cls}">${line}</span>` : line;
      }).join("\n");
      logEl.scrollTop = logEl.scrollHeight;
    })
    .catch(() => {
      document.getElementById("ts").textContent = "Connection error";
    });
}

async function restart(svc) {
  const msg = document.getElementById("rmsg");
  msg.style.color = "var(--muted)";
  msg.textContent = "Restarting " + svc + "...";
  try {
    const r = await fetch("/api/restart/" + svc, { method: "POST" });
    const d = await r.json();
    msg.style.color = d.ok ? "var(--green)" : "var(--red)";
    msg.textContent = d.ok ? svc + " restarted successfully" : svc + " restart failed: " + (d.error || d.err || "unknown error");
  } catch (e) {
    msg.style.color = "var(--red)";
    msg.textContent = "Request failed: " + e.message;
  }
  setTimeout(() => msg.textContent = "", 6000);
}

renderPB();
refresh();
setInterval(refresh, 6000);
</script>
</body>
</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)

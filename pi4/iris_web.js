// ── Sleep Animation slider builder ────────────────────────────────────────────
const _SA_SLIDERS = [
  // [group-id, key, label, min, max, step, defaultVal]
  ["sa-stars-warps","speed","Speed",0.2,2.0,0.1,0.85],
  ["sa-stars-warps","starBrightMin","Star brightness min",20,200,5,115],
  ["sa-stars-warps","starBrightMax","Star brightness max",100,255,5,205],
  ["sa-stars-warps","starTwinkleAmp","Star twinkle amp",20,255,5,140],
  ["sa-stars-warps","warpCount","Warp particle count",0,60,2,32],
  ["sa-stars-warps","warpSpeed","Warp speed",5,100,5,28],
  ["sa-stars-warps","warpBright","Warp brightness",40,255,5,175],
  ["sa-shoots","shootCount","Shoot count",0,10,1,4],
  ["sa-shoots","shootSpeed","Shoot speed",5,120,5,38],
  ["sa-shoots","shootLen","Trail length (px)",10,120,5,55],
  ["sa-shoots","shootBright","Shoot brightness",50,255,5,210],
  ["sa-objects","moonR","Moon radius (px)",10,50,1,28],
  ["sa-objects","moonDrift","Moon drift amp (px)",0,15,1,3],
  ["sa-objects","saturnR","Saturn radius (px)",8,35,1,18],
  ["sa-objects","saturnDrift","Saturn drift amp (px)",0,15,1,4],
  ["sa-objects","nebulaAlpha","Nebula alpha",0,120,4,44],
  ["sa-mouth","waveAmp0","Wave amp primary (px)",5,60,1,28],
  ["sa-mouth","waveAmp1","Wave amp secondary (px)",3,40,1,18],
  ["sa-mouth","waveAmp2","Wave amp tertiary (px)",2,25,1,10],
  ["sa-mouth","waveOscAmp","Wave vertical osc (px)",0,60,2,34],
  ["sa-mouth","mouthPulseAlpha","Mouth pulse alpha",20,255,5,140],
  ["sa-mouth","zzzAlpha0","ZZZ alpha (large)",30,255,5,191],
  ["sa-mouth","zzzAlpha1","ZZZ alpha (medium)",30,255,5,158],
  ["sa-mouth","zzzAlpha2","ZZZ alpha (small)",30,255,5,128],
];

function _buildSaSliders(data) {
  _SA_SLIDERS.forEach(([grp, key, lbl, mn, mx, step, def]) => {
    const container = document.getElementById(grp);
    if (!container) return;
    const val = (data && data[key] != null) ? data[key] : def;
    const row = document.createElement('div');
    row.className = 'field-row';
    row.innerHTML =
      `<label style="width:220px">${lbl}</label>` +
      `<input type="range" id="sa-${key}" min="${mn}" max="${mx}" step="${step}" value="${val}"` +
      ` style="width:160px;accent-color:var(--indigo);height:6px;cursor:pointer"` +
      ` oninput="document.getElementById('sa-v-${key}').textContent=this.value;_saCfgSend('${key}',this.value)">` +
      `<span id="sa-v-${key}" style="width:34px;color:var(--text);font-size:13px;flex-shrink:0">${val}</span>`;
    container.appendChild(row);
  });
}

let _saDebounce = {};
function _saCfgSend(key, val) {
  clearTimeout(_saDebounce[key]);
  _saDebounce[key] = setTimeout(() => {
    const numVal = parseFloat(val);
    fetch('/api/sleep_cfg', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({[key]: numVal})
    }).then(r=>r.json()).catch(()=>{});
  }, 180);
}

function _loadSaSliders() {
  fetch('/api/sleep_cfg').then(r=>r.json()).then(d=>{
    _buildSaSliders(d);
  }).catch(()=>{
    _buildSaSliders(null);
  });
}

// Load sliders when Sleep tab is first shown
var _saLoaded = false;
function _saTabHook() { if (!_saLoaded) { _saLoaded = true; _loadSaSliders(); } }

// ── Tab switching ──────────────────────────────────────────────────────────────
function tab(name, btn) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('sec-' + name).classList.add('active');
  btn.classList.add('active');
  if (name === 'logs') fetchLogs();
  if (name === 'system') { pollStatus(); checkSDStatus(); refreshVolume(); }
  if (name === 'voice') { loadKokoroVoices(); }
  if (name === 'gandalf') loadVram();
  if (name === 'bench') fetchBench();
  if (name === 'gestures') { loadGestureConfig(); fetchGestureLog(); }
  if (name === 'eyes') { pollSleepState(); loadEmotionMap(); }
  if (name === 'sleep') {
    pollSleepState();
    const ma = document.getElementById('MOUTH_INTENSITY_AWAKE');
    if (ma) document.getElementById('mouth-awake-display').textContent = ma.value;
    const ms = document.getElementById('MOUTH_INTENSITY_SLEEP');
    if (ms) document.getElementById('mouth-sleep-display').textContent = ms.value;
  }
}

// ── Toast ──────────────────────────────────────────────────────────────────────
let _toastTimer = null;
function toast(msg, ok=true, duration=2500) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.background = ok ? '#1d4ed8' : '#b91c1c';
  t.classList.add('show');
  if (_toastTimer) clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => t.classList.remove('show'), duration);
}

// ── SD status bar ──────────────────────────────────────────────────────────────
async function checkSDStatus() {
  try {
    const r = await fetch('/api/sd_status');
    const j = await r.json();
    _updateSDBar(j.synced ? 'synced' : 'dirty',
      j.synced ? 'SD: synced' : 'Unsaved changes — not persisted to SD (will be lost on reboot)');
  } catch(e) {
    _updateSDBar('checking', 'SD status unknown');
  }
}

function _updateSDBar(state, text) {
  const bar = document.getElementById('sd-bar');
  const txt = document.getElementById('sd-status-text');
  const sys = document.getElementById('sys-sd-status');
  bar.className = 'sd-bar ' + state;
  txt.textContent = text;
  if (sys) {
    sys.textContent = state === 'synced' ? 'synced' : state === 'dirty' ? 'not persisted' : '--';
    sys.style.color = state === 'synced' ? 'var(--green)' : state === 'dirty' ? 'var(--amber)' : 'var(--muted)';
  }
}

async function persistToSD() {
  _updateSDBar('checking', 'Persisting to SD…');
  try {
    const r = await fetch('/api/persist_config', {method: 'POST'});
    const j = await r.json();
    if (j.ok) {
      _updateSDBar('synced', 'SD: synced — persisted ' + new Date().toLocaleTimeString());
      toast('Config persisted to SD card', true, 4000);
    } else {
      _updateSDBar('error', 'Persist FAILED: ' + (j.error || 'unknown error'));
      toast('Persist failed: ' + (j.error || 'error'), false, 5000);
    }
  } catch(e) {
    _updateSDBar('error', 'Persist error: ' + e);
    toast('Persist error', false);
  }
}

// ── Config load/save ──────────────────────────────────────────────────────────
let _cfg = {};
async function loadConfig() {
  const r = await fetch('/api/config');
  _cfg = await r.json();
  for (const [k, v] of Object.entries(_cfg)) {
    const el = document.getElementById(k);
    if (!el) continue;
    if (el.tagName === 'SELECT') el.value = String(v);
    else el.value = v;
  }
  // Sync range slider display spans after values are populated
  const ma = document.getElementById('MOUTH_INTENSITY_AWAKE');
  if (ma) document.getElementById('mouth-awake-display').textContent = ma.value;
  const ms = document.getElementById('MOUTH_INTENSITY_SLEEP');
  if (ms) document.getElementById('mouth-sleep-display').textContent = ms.value;
  // Show active wakeword model name
  const wakeLabel = document.getElementById('wakeword-model-label');
  if (wakeLabel && _cfg.WAKE_WORD) wakeLabel.textContent = _cfg.WAKE_WORD;
  // Pre-select current default eye
  const defEyeSel = document.getElementById('default-eye-sel');
  if (defEyeSel && _cfg.DEFAULT_EYE_IDX !== undefined) defEyeSel.value = String(_cfg.DEFAULT_EYE_IDX);
}

async function saveFields(keys) {
  const patch = {};
  for (const k of keys) {
    const el = document.getElementById(k);
    if (!el) continue;
    const raw = el.value;
    patch[k] = isNaN(raw) || raw === '' ? raw : Number(raw);
  }
  const r = await fetch('/api/config', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(patch)});
  const j = await r.json();
  toast(j.ok ? 'Saved to RAM' : 'Error', j.ok);
  if (j.ok) checkSDStatus();
}

async function saveDefaultEye() {
  const sel = document.getElementById('default-eye-sel');
  if (!sel) return;
  const idx = parseInt(sel.value);
  const r = await fetch('/api/config', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({DEFAULT_EYE_IDX: idx})});
  const j = await r.json();
  toast(j.ok ? 'Default eye saved — applies on next IRIS restart' : 'Save failed', j.ok);
  if (j.ok) checkSDStatus();
}

// ── Teensy ─────────────────────────────────────────────────────────────────────
async function loadKokoroVoices() {
  const sel = document.getElementById('KOKORO_VOICE');
  if (!sel) return;
  sel.innerHTML = '<option>Loading...</option>';
  try {
    const r = await fetch('/api/kokoro_voices');
    const j = await r.json();
    const voices = j.voices || [];
    sel.innerHTML = '';
    const current = (_cfg && _cfg.KOKORO_VOICE) ? _cfg.KOKORO_VOICE : 'bm_lewis';
    if (!voices.length) { sel.innerHTML = '<option value="">No voices found</option>'; return; }
    voices.forEach(function(name) {
      const o = document.createElement('option');
      o.value = name; o.textContent = name;
      if (name === current) o.selected = true;
      sel.appendChild(o);
    });
  } catch(e) { sel.innerHTML = '<option>Kokoro offline</option>'; }
}

async function saveKokoroSettings() {
  const enabled = document.getElementById('KOKORO_ENABLED').value === 'true';
  const voice   = document.getElementById('KOKORO_VOICE').value;
  const speedEl = document.getElementById('KOKORO_SPEED');
  const speed   = speedEl ? Math.max(0.5, Math.min(2.0, parseFloat(speedEl.value) || 1.0)) : 1.0;
  const r = await fetch('/api/config', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({KOKORO_ENABLED: enabled, KOKORO_VOICE: voice, KOKORO_SPEED: speed})});
  const j = await r.json();
  toast(j.ok ? 'Kokoro settings saved' : 'Error', j.ok);
  if (j.ok) persistToSD();
}

async function sendTeensy(cmd) {
  const r = await fetch('/api/teensy', {method:'POST',
    headers:{'Content-Type':'application/json'}, body:JSON.stringify({cmd})});
  const j = await r.json();
  toast(j.ok ? cmd : 'Teensy error: ' + cmd, j.ok);
}

// ── Sleep control ──────────────────────────────────────────────────────────────
let _isSleeping = false;

function updateSleepUI(sleeping) {
  _isSleeping = sleeping;
  const dot    = document.getElementById('sleep-dot');
  const lbl    = document.getElementById('sleep-label');
  const btnS   = document.getElementById('btn-sleep');
  const btnW   = document.getElementById('btn-wake');
  const hdrLbl = document.getElementById('lbl-sleep-hdr');
  const sysSleep = document.getElementById('sys-sleep');

  if (sleeping) {
    dot.classList.add('sleeping');
    lbl.textContent = 'IRIS is sleeping — starfield active, mouth snoring';
    lbl.style.color = 'var(--indigo)';
    btnS.classList.add('active-state');
    btnW.classList.remove('active-state');
    btnW.style.background = '#1d4ed8';
    btnW.style.color = '#fff';
    if (hdrLbl) hdrLbl.style.display = 'inline';
    if (sysSleep) { sysSleep.textContent = 'sleeping'; sysSleep.style.color = 'var(--indigo)'; }
  } else {
    dot.classList.remove('sleeping');
    lbl.textContent = 'IRIS is awake';
    lbl.style.color = 'var(--text)';
    btnS.classList.remove('active-state');
    btnW.classList.add('active-state');
    btnW.style.background = '#14532d';
    btnW.style.color = 'var(--green)';
    if (hdrLbl) hdrLbl.style.display = 'none';
    if (sysSleep) { sysSleep.textContent = 'awake'; sysSleep.style.color = 'var(--green)'; }
  }
}

async function pollSleepState() {
  try {
    const r = await fetch('/api/sleep_state');
    const j = await r.json();
    updateSleepUI(j.sleeping);
  } catch(e) {}
}

async function triggerSleep() {
  const r = await fetch('/api/sleep', {method:'POST'});
  const j = await r.json();
  if (j.ok) { await pollSleepState(); toast('IRIS sleeping'); }
  else toast('Sleep command failed', false);
}

async function triggerWake() {
  const r = await fetch('/api/wake', {method:'POST'});
  const j = await r.json();
  if (j.ok) { await pollSleepState(); toast('IRIS awake'); }
  else toast('Wake command failed', false);
}

// ── Mouth intensity ────────────────────────────────────────────────────────────
async function saveMouthIntensity() {
  const awake = Math.max(0, Math.min(15, parseInt(document.getElementById('MOUTH_INTENSITY_AWAKE').value)));
  const sleep  = Math.max(0, Math.min(15, parseInt(document.getElementById('MOUTH_INTENSITY_SLEEP').value)));
  await fetch('/api/config', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({MOUTH_INTENSITY_AWAKE: awake, MOUTH_INTENSITY_SLEEP: sleep})});
  const intensity = _isSleeping ? sleep : awake;
  await fetch('/api/teensy', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({cmd: 'MOUTH_INTENSITY:' + intensity})});
  toast('Mouth intensity saved and applied');
  checkSDStatus();
}

// ── Logs ───────────────────────────────────────────────────────────────────────
let _logFilter = 'all';
let _logAutoTimer = null;
let _logEvents = [];

const _CAT_LABELS = {
  wakeword:'WAKE', stt:'HEARD', route:'ROUTE', llm:'LLM',
  tts:'SPOKEN', stop:'STOP', drift:'DRIFT', error:'ERR',
  info:'INFO', cmd:'CMD', warn:'WARN', gesture:'GESTURE'
};

function _esc(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function setLogFilter(cat, btn) {
  _logFilter = cat;
  document.querySelectorAll('.btn-filter').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderLogEvents();
}

function renderLogEvents() {
  const box = document.getElementById('log-events');
  const cnt = document.getElementById('log-count');
  const evs = _logFilter === 'all' ? _logEvents
             : _logEvents.filter(e => e.cat === _logFilter);
  if (cnt) cnt.textContent = evs.length + ' event' + (evs.length !== 1 ? 's' : '');
  if (!evs.length) {
    box.innerHTML = '<div style="color:var(--muted);padding:16px;text-align:center">No events in this category</div>';
    return;
  }
  // Newest first
  box.innerHTML = evs.slice().reverse().map(e => {
    const label  = _CAT_LABELS[e.cat] || (e.cat||'?').toUpperCase();
    const detail = e.detail ? `<span class="log-detail">${_esc(e.detail)}</span>` : '';
    return `<div class="log-event cat-${_esc(e.cat||'info')}">` +
           `<span class="log-ts">${_esc(e.ts)}</span>` +
           `<span class="log-cat">[${label}]</span>` +
           `<span class="log-msg" title="${_esc(e.msg)}">${_esc(e.msg)}</span>` +
           `${detail}</div>`;
  }).join('');
  window.requestAnimationFrame(function() { box.scrollTop = 0; });
}

async function fetchLogs() {
  const box = document.getElementById('log-events');
  box.innerHTML = '<div style="color:var(--muted);padding:16px;text-align:center">Loading...</div>';
  try {
    const r = await fetch('/api/logs');
    const j = await r.json();
    _logEvents = j.events || [];
    renderLogEvents();
  } catch(e) {
    box.innerHTML = `<div style="color:var(--red);padding:12px">Error: ${_esc(String(e))}</div>`;
  }
}

function toggleLogsAuto(cb) {
  if (_logAutoTimer) { clearInterval(_logAutoTimer); _logAutoTimer = null; }
  if (cb.checked) _logAutoTimer = setInterval(fetchLogs, 15000);
}

// ── Status ─────────────────────────────────────────────────────────────────────
async function pollStatus() {
  const r = await fetch('/api/status');
  const j = await r.json();
  const dot = document.getElementById('dot-assistant');
  const lbl = document.getElementById('lbl-assistant');
  document.getElementById('lbl-temp').textContent = j.cpu_temp + 'C';
  document.getElementById('lbl-uptime').textContent = j.uptime;
  dot.className = 'dot' + (j.running ? ' on' : '');
  lbl.textContent = j.running ? 'running' : 'stopped';
  const sr = document.getElementById('sys-running');
  const st = document.getElementById('sys-temp');
  const su = document.getElementById('sys-uptime');
  if(sr) { sr.textContent = j.running ? 'running' : 'stopped'; sr.style.color = j.running ? 'var(--green)' : 'var(--red)'; }
  if(st) st.textContent = j.cpu_temp + 'C';
  if(su) su.textContent = j.uptime;
  if (typeof j.sleeping === 'boolean') updateSleepUI(j.sleeping);
}

async function restartAssistant() {
  await fetch('/api/restart', {method:'POST'});
  toast('Restarting IRIS...');
  setTimeout(pollStatus, 3000);
}

// ── VRAM ───────────────────────────────────────────────────────────────────────
async function loadVram() {
  const box = document.getElementById('vram-box');
  box.textContent = 'Loading...';
  try {
    const r = await fetch('/api/vram');
    const j = await r.json();
    if (j.error) { box.textContent = 'Gandalf offline: ' + j.error; return; }
    const models = j.models || [];
    if (!models.length) { box.textContent = 'No models loaded in VRAM'; return; }
    box.textContent = models.map(m =>
      `${m.name}\n  size: ${(m.size/1e9).toFixed(1)} GB  vram: ${(m.size_vram/1e9).toFixed(1)} GB`
    ).join('\n\n');
  } catch(e) { box.textContent = 'Error: ' + e; }
}

// ── Chat ───────────────────────────────────────────────────────────────────────
let _chatMode    = 'silent';   // 'silent' | 'speak' | 'verbatim'
let _chatPersona = 'adult';

const _CHAT_MODE_HINTS = {
  silent:   '',
  speak:    'IRIS will generate a response via LLM and speak it aloud. May conflict with active voice pipeline.',
  verbatim: 'IRIS will speak your exact text through TTS — no LLM. Use when voice pipeline is idle.'
};

function updateChatMode(radio) {
  _chatMode = radio.value;
  const hint = document.getElementById('chat-mode-hint');
  if (hint) hint.textContent = _CHAT_MODE_HINTS[_chatMode] || '';
}

async function sendChat() {
  const inp  = document.getElementById('chat-input');
  const box  = document.getElementById('chat-box');
  const text = inp.value.trim();
  if (!text) return;
  const persona = document.querySelector('input[name="chat-persona"]:checked');
  _chatPersona = persona ? persona.value : 'adult';
  inp.value = '';

  const userMsg = document.createElement('div');
  userMsg.className = 'chat-msg user';
  userMsg.textContent = 'You: ' + text;
  box.appendChild(userMsg);
  box.scrollTop = box.scrollHeight;

  if (_chatMode === 'verbatim') {
    const out = document.createElement('div');
    out.className = 'chat-msg iris';
    out.textContent = 'IRIS [verbatim]: ' + text;
    box.appendChild(out);
    box.scrollTop = box.scrollHeight;
    try {
      const r = await fetch('/api/speak', {method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({text})});
      const j = await r.json();
      if (!j.ok) { out.className = 'chat-msg err'; out.textContent = 'Speak error: ' + (j.error||'unknown'); }
    } catch(e) {
      out.className = 'chat-msg err';
      out.textContent = 'Speak error: ' + e;
    }
    return;
  }

  const thinking = document.createElement('div');
  thinking.className = 'chat-msg iris';
  thinking.textContent = _chatMode === 'speak' ? 'IRIS: thinking (will speak)...' : 'IRIS: thinking...';
  box.appendChild(thinking);
  try {
    const r = await fetch('/api/chat', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({text, speak: _chatMode === 'speak', mode: _chatPersona})});
    const j = await r.json();
    if (j.reply) {
      const spokenTag  = j.spoken  ? ' [spoken]'           : '';
      const emotionTag = j.emotion ? ` {${j.emotion}}`     : '';
      thinking.textContent = 'IRIS' + spokenTag + emotionTag + ': ' + j.reply;
    } else {
      thinking.className = 'chat-msg err';
      thinking.textContent = 'Error: ' + (j.error || 'unknown');
    }
  } catch(e) {
    thinking.className = 'chat-msg err';
    thinking.textContent = 'Error: ' + e;
  }
  box.scrollTop = box.scrollHeight;
}

function clearChat() {
  document.getElementById('chat-box').innerHTML = '';
}

// ── Vision Demo ───────────────────────────────────────────────────────────────
async function sendVision(prompt) {
  prompt = (prompt || '').trim();
  if (!prompt) { toast('Enter a prompt', false); return; }
  const resultBox  = document.getElementById('vision-result');
  const statusEl   = document.getElementById('vision-status');
  const speakCheck = document.getElementById('vision-speak');
  resultBox.style.display = 'none';
  resultBox.textContent   = '';
  statusEl.textContent    = 'Capturing frame and querying vision model...';
  try {
    const r = await fetch('/api/vision', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({prompt, speak: speakCheck && speakCheck.checked})
    });
    const j = await r.json();
    if (j.error) {
      statusEl.textContent = 'Error: ' + j.error;
      statusEl.style.color = 'var(--red)';
    } else {
      resultBox.textContent   = j.reply || '(no reply)';
      resultBox.style.display = 'block';
      const spokenTag = j.spoken ? ' — speaking via Kokoro' : '';
      statusEl.textContent  = 'Done' + spokenTag + (j.emotion ? '  {' + j.emotion + '}' : '');
      statusEl.style.color  = 'var(--muted)';
    }
  } catch(e) {
    statusEl.textContent = 'Request failed: ' + e;
    statusEl.style.color = 'var(--red)';
  }
}

// ── Emotion Display Mapping ────────────────────────────────────────────────────
const _EMOTION_NAMES = ['NEUTRAL','HAPPY','CURIOUS','ANGRY','SLEEPY','SURPRISED','SAD','CONFUSED','AMUSED'];
const _EYE_OPT = [[-1,'Default (auto)'],[0,'0 - Nordic Blue'],[1,'1 - Flame'],[2,'2 - Hypno Red'],
  [3,'3 - Hazel'],[4,'4 - Blue Flame 1'],[5,'5 - Dragon'],[6,'6 - Striking Blue']];
const _MOUTH_OPT = [[0,'0 - Neutral'],[1,'1 - Happy'],[2,'2 - Curious'],[3,'3 - Angry'],
  [4,'4 - Sleepy'],[5,'5 - Surprised'],[6,'6 - Sad'],[7,'7 - Confused'],
  [8,'8 - Sleep'],[9,'9 - Silly (tongue)']];

let _emotionMap = {mouth_map:{}, eye_map:{}};

function _buildEmotionMapUI(data) {
  _emotionMap = data;
  const tbl = document.getElementById('emotion-map-tbl');
  if (!tbl) return;
  tbl.innerHTML = '';
  for (const emo of _EMOTION_NAMES) {
    const curM = data.mouth_map[emo] ?? 0;
    const curE = data.eye_map[emo] ?? -1;
    const eOpts = _EYE_OPT.map(([v,l])=>`<option value="${v}"${v==curE?' selected':''}>${l}</option>`).join('');
    const mOpts = _MOUTH_OPT.map(([v,l])=>`<option value="${v}"${v==curM?' selected':''}>${l}</option>`).join('');
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="padding:5px 8px;font-size:13px;color:var(--amber);white-space:nowrap">${emo}</td>
      <td style="padding:3px 8px"><select id="em-eye-${emo}">${eOpts}</select></td>
      <td style="padding:3px 8px"><select id="em-mouth-${emo}">${mOpts}</select></td>
      <td style="padding:3px 8px"><button class="btn btn-sm" onclick="testEmotionEntry('${emo}')">Test</button></td>`;
    tbl.appendChild(tr);
  }
}

async function loadEmotionMap() {
  try {
    const r = await fetch('/api/emotion_map');
    _buildEmotionMapUI(await r.json());
  } catch(e) { _buildEmotionMapUI({mouth_map:{},eye_map:{}}); }
}

async function saveEmotionMap() {
  const mouthMap={}, eyeMap={};
  for (const emo of _EMOTION_NAMES) {
    const mSel = document.getElementById('em-mouth-'+emo);
    const eSel = document.getElementById('em-eye-'+emo);
    if (mSel) mouthMap[emo] = parseInt(mSel.value);
    if (eSel) eyeMap[emo]   = parseInt(eSel.value);
  }
  const r = await fetch('/api/emotion_map', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({EMOTION_MOUTH_MAP:mouthMap, EMOTION_EYE_MAP:eyeMap})});
  const j = await r.json();
  toast(j.ok ? 'Emotion map saved' : 'Error saving', j.ok);
  if (j.ok) { _emotionMap = {mouth_map:mouthMap, eye_map:eyeMap}; checkSDStatus(); }
}

async function testEmotionEntry(emotion) {
  const eSel = document.getElementById('em-eye-'+emotion);
  const mSel = document.getElementById('em-mouth-'+emotion);
  const eIdx = eSel ? parseInt(eSel.value) : -1;
  const mIdx = mSel ? parseInt(mSel.value) : 0;
  if (eIdx >= 0) await sendTeensy('EYE:'+eIdx);
  await sendTeensy('EMOTION:'+emotion);
  await sendTeensy('MOUTH:'+mIdx);
}

// Uses loaded emotion map if available, falls back to the passed mouthIdx
async function sendEmotion(emotion, fallbackMouthIdx) {
  const eIdx = (_emotionMap.eye_map && emotion in _emotionMap.eye_map) ? _emotionMap.eye_map[emotion] : -1;
  const mIdx = (_emotionMap.mouth_map && emotion in _emotionMap.mouth_map)
    ? _emotionMap.mouth_map[emotion]
    : (fallbackMouthIdx !== undefined ? fallbackMouthIdx : 0);
  if (typeof eIdx === 'number' && eIdx >= 0) await sendTeensy('EYE:'+eIdx);
  await sendTeensy('EMOTION:'+emotion);
  await sendTeensy('MOUTH:'+mIdx);
}

// ── Volume ────────────────────────────────────────────────────────────────────
async function refreshVolume() {
  try {
    const r = await fetch('/api/volume');
    const j = await r.json();
    document.getElementById('vol-slider').value = j.level;
    document.getElementById('vol-display').textContent = `${j.level} (${j.pct}%)`;
  } catch(e) {}
}

async function setVolume() {
  const level = parseInt(document.getElementById('vol-slider').value);
  const r = await fetch('/api/volume', {method:'POST',
    headers:{'Content-Type':'application/json'}, body: JSON.stringify({level})});
  const j = await r.json();
  if (j.ok) {
    document.getElementById('vol-display').textContent = `${j.level} (${j.pct}%)`;
    toast(`Volume set to ${j.level} (${j.pct}%)`);
  }
}

// ── Bench ──────────────────────────────────────────────────────────────────────
let _benchAutoTimer = null;

function _fmt(v) {
  if (v == null) return '-';
  const n = parseFloat(v);
  return isNaN(n) ? '-' : n.toFixed(2) + 's';
}
function _ts(t) {
  if (!t) return '-';
  try { return new Date(parseFloat(t) * 1000).toLocaleTimeString(); }
  catch(e) { return String(t).slice(0,8); }
}

async function fetchBench() {
  const tbody = document.getElementById('bench-body');
  const cnt   = document.getElementById('bench-count');
  tbody.innerHTML = '<tr><td colspan="15" style="text-align:center;color:var(--muted);padding:16px">Loading...</td></tr>';
  try {
    const r = await fetch('/api/bench');
    const j = await r.json();
    if (j.error) {
      tbody.innerHTML = `<tr><td colspan="15" style="color:var(--red);padding:12px">${j.error}</td></tr>`;
      return;
    }
    const cycles = j.cycles || [];
    cnt.textContent = cycles.length ? cycles.length + ' cycle(s)' : '';
    if (!cycles.length) {
      tbody.innerHTML = '<tr><td colspan="15" style="text-align:center;color:var(--muted);padding:20px">No [BENCH] cycles yet — trigger IRIS to speak first</td></tr>';
    } else {
      tbody.innerHTML = cycles.slice().reverse().map((c, i) => {
        const ls        = c.llm_start || {};
        const tier      = ls.tier || '-';
        const np        = ls.num_predict || '-';
        const rec       = _fmt((c.rec_done || {}).dur_rec);
        const stt       = _fmt((c.stt_done || {}).dur_stt);
        const ttfc      = _fmt((c.llm_first_chunk || {}).dur_ttfc);
        const llm       = _fmt((c.llm_done || {}).dur_llm);
        const tts       = _fmt((c.tts_done || {}).dur_tts);
        const aud       = _fmt((c.audio_done || {}).dur_audio);
        const total     = _fmt((c.audio_done || {}).dur_total);
        const totalRaw  = parseFloat((c.audio_done || {}).dur_total);
        const audRaw    = parseFloat((c.audio_done || {}).dur_audio);
        const ttfwRaw   = (!isNaN(totalRaw) && !isNaN(audRaw)) ? totalRaw - audRaw : NaN;
        const ttfw      = isNaN(ttfwRaw) ? '-' : ttfwRaw.toFixed(2) + 's';
        const ttfwcol   = isNaN(ttfwRaw) ? '' : ttfwRaw < 4 ? 'style="color:var(--green)"' : ttfwRaw < 7 ? 'style="color:var(--amber)"' : 'style="color:var(--red)"';
        const os        = c.ollama_stats || {};
        const ep        = (os.eval_tokens || '-') + '/' + (os.prompt_tokens || '-');
        const snip      = ((c.stt_done || {}).transcript || '').slice(0, 45);
        const n         = totalRaw;
        const tcol      = isNaN(n) ? '' : n < 6 ? 'style="color:var(--green)"' : n < 10 ? 'style="color:var(--amber)"' : 'style="color:var(--red)"';
        return `<tr>
          <td>${cycles.length - i}</td><td>${_ts(c.t)}</td>
          <td>${c.trigger||'?'}</td>
          <td class="tier-${tier}">${tier}</td><td>${np}</td>
          <td>${rec}</td><td>${stt}</td><td>${ttfc}</td><td>${llm}</td><td>${tts}</td><td>${aud}</td>
          <td ${ttfwcol}>${ttfw}</td><td ${tcol}>${total}</td><td>${ep}</td><td title="${((c.stt_done||{}).transcript||'')}">${snip}</td></tr>`;
      }).join('');
    }
    const lev = j.levers || {};
    const levDiv = document.getElementById('bench-levers');
    if (Object.keys(lev).length) {
      const sep = '<span style="color:var(--border);margin:0 2px">|</span>';
      levDiv.innerHTML = [
        'SHORT=<span>' + lev.NUM_PREDICT_SHORT + '</span>',
        'MEDIUM=<span>' + lev.NUM_PREDICT_MEDIUM + '</span>',
        'LONG=<span>' + lev.NUM_PREDICT_LONG + '</span>',
        'MAX=<span>' + lev.NUM_PREDICT_MAX + '</span>',
        'TTS_MAX_CHARS=<span>' + lev.TTS_MAX_CHARS + '</span>',
        'TTS=<span>' + (lev.KOKORO_ENABLED ? 'kokoro' : 'piper') + '</span>',
      ].join(sep);
    } else { levDiv.textContent = 'Could not load config'; }
  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="15" style="color:var(--red);padding:12px">Error: ${e}</td></tr>`;
  }
}

function toggleBenchAuto(cb) {
  if (_benchAutoTimer) { clearInterval(_benchAutoTimer); _benchAutoTimer = null; }
  if (cb.checked) _benchAutoTimer = setInterval(fetchBench, 15000);
}

// ── Gesture config ────────────────────────────────────────────────────────────
const _GESTURE_KEYS    = ['VOL+', 'VOL-', 'STOP', 'RIGHT', 'FORWARD', 'BACKWARD', 'CW', 'CCW'];
const _GESTURE_ACTIONS = ['VOL+', 'VOL-', 'STOP', 'LISTEN', 'SLEEP', 'WAKE', 'MUTE', 'SKIP'];
const _GESTURE_LABELS  = {
  'VOL+':    'VOL+ — volume up',
  'VOL-':    'VOL- — volume down',
  'STOP':    'STOP — stop playback',
  'LISTEN':  'LISTEN — trigger listen',
  'SLEEP':   'SLEEP — full sleep sequence',
  'WAKE':    'WAKE — full wake sequence',
  'MUTE':    'MUTE — toggle mute/unmute',
  'SKIP':    'SKIP — do nothing',
};

function _populateGestureSelects() {
  _GESTURE_KEYS.forEach(function(key) {
    const sel = document.getElementById('gesture-' + key);
    if (!sel || sel.options.length > 1) return;
    sel.innerHTML = '';
    _GESTURE_ACTIONS.forEach(function(act) {
      const o = document.createElement('option');
      o.value = act;
      o.textContent = _GESTURE_LABELS[act] || act;
      sel.appendChild(o);
    });
  });
}

async function loadGestureConfig() {
  _populateGestureSelects();
  try {
    const r = await fetch('/api/gesture_config');
    const j = await r.json();
    const map = j.GESTURE_MAP || {};
    _GESTURE_KEYS.forEach(function(key) {
      const sel = document.getElementById('gesture-' + key);
      if (sel && map[key]) sel.value = map[key];
    });
  } catch(e) { toast('Failed to load gesture config', false); }
}

async function saveGestureConfig() {
  const map = {};
  _GESTURE_KEYS.forEach(function(key) {
    const sel = document.getElementById('gesture-' + key);
    if (sel) map[key] = sel.value;
  });
  const r = await fetch('/api/gesture_config', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({GESTURE_MAP: map})
  });
  const j = await r.json();
  toast(j.ok ? 'Gesture config saved' : 'Error saving gesture config', j.ok);
  if (j.ok) checkSDStatus();
}

// ── Gesture log ───────────────────────────────────────────────────────────────
let _gestureLogAutoTimer = null;

async function fetchGestureLog() {
  const box = document.getElementById('gesture-log-events');
  const cnt = document.getElementById('gesture-log-count');
  if (!box) return;
  box.innerHTML = '<div style="color:var(--muted);padding:16px;text-align:center">Loading...</div>';
  try {
    const r = await fetch('/api/gesture_log');
    const j = await r.json();
    const evs = j.events || [];
    if (cnt) cnt.textContent = evs.length + ' event' + (evs.length !== 1 ? 's' : '');
    if (!evs.length) {
      box.innerHTML = '<div style="color:var(--muted);padding:16px;text-align:center">No gesture events yet — swipe, push, or rotate over PAJ7620U2 sensor</div>';
      return;
    }
    // Reverse so newest is first in DOM; rAF ensures scrollTop=0 takes effect after paint
    box.innerHTML = evs.slice().reverse().map(e => {
      const dateStr = (e.t || '').slice(0, 10);
      const timeStr = e.ts || '';
      const label   = dateStr ? `${dateStr} ${timeStr}` : timeStr;
      return `<div class="log-event cat-gesture">` +
             `<span class="log-ts" style="width:130px">${_esc(label)}</span>` +
             `<span class="log-cat">[GESTURE]</span>` +
             `<span class="log-msg">${_esc(e.msg || '')}</span>` +
             `</div>`;
    }).join('');
    window.requestAnimationFrame(function() { box.scrollTop = 0; });
  } catch(e) {
    box.innerHTML = `<div style="color:var(--red);padding:12px">Error: ${_esc(String(e))}</div>`;
  }
}

function toggleGestureLogAuto(cb) {
  if (_gestureLogAutoTimer) { clearInterval(_gestureLogAutoTimer); _gestureLogAutoTimer = null; }
  if (cb.checked) _gestureLogAutoTimer = setInterval(fetchGestureLog, 30000);
}

// ── POST diagnostic ───────────────────────────────────────────────────────────
let _postPollTimer = null;

const _POST_STATUS_COLORS = {
  PASS: 'var(--green)', WARN: 'var(--amber)', FAIL: 'var(--red)',
  SKIP: 'var(--muted)', ERROR: 'var(--red)'
};

async function runPost() {
  const btn = document.getElementById('btn-post');
  const statusEl = document.getElementById('post-status');
  const resultEl = document.getElementById('post-result');
  btn.disabled = true;
  statusEl.textContent = 'starting...';
  statusEl.style.color = 'var(--blue)';
  resultEl.style.display = 'none';
  try {
    const r = await fetch('/api/post', {method: 'POST'});
    const j = await r.json();
    if (!j.ok && j.error) {
      statusEl.textContent = j.error;
      statusEl.style.color = 'var(--red)';
      btn.disabled = false;
      return;
    }
  } catch(e) {
    statusEl.textContent = 'request failed';
    statusEl.style.color = 'var(--red)';
    btn.disabled = false;
    return;
  }
  statusEl.textContent = 'running...';
  if (_postPollTimer) clearInterval(_postPollTimer);
  _postPollTimer = setInterval(_pollPost, 2000);
}

async function _pollPost() {
  const btn = document.getElementById('btn-post');
  const statusEl = document.getElementById('post-status');
  try {
    const r = await fetch('/api/post');
    const j = await r.json();
    if (j.running) { statusEl.textContent = 'running...'; return; }
    clearInterval(_postPollTimer); _postPollTimer = null;
    btn.disabled = false;
    _renderPostResult(j.result);
  } catch(e) {
    statusEl.textContent = 'poll error';
  }
}

function _renderPostResult(result) {
  if (!result) return;
  const statusEl  = document.getElementById('post-status');
  const resultEl  = document.getElementById('post-result');
  const verdictEl = document.getElementById('post-verdict');
  const rowsEl    = document.getElementById('post-rows');

  const ok = result.verdict === 'AUTHORIZED';
  statusEl.textContent = `done — ${result.ts || ''}`;
  statusEl.style.color = ok ? 'var(--green)' : 'var(--red)';

  const vColor = ok ? 'var(--green)' : 'var(--red)';
  verdictEl.innerHTML =
    `<span style="color:${vColor}">${_esc(result.verdict)}</span>` +
    `&nbsp; ${result.n_pass}/${result.n_total} PASS` +
    (result.n_warn ? `&nbsp; <span style="color:var(--amber)">${result.n_warn} WARN</span>` : '') +
    (result.n_fail ? `&nbsp; <span style="color:var(--red)">${result.n_fail} FAIL</span>` : '');

  rowsEl.innerHTML = (result.checks || []).map(c => {
    const col = _POST_STATUS_COLORS[c.status] || 'var(--muted)';
    return `<tr>
      <td style="text-align:left;color:var(--muted)">${_esc(c.layer)}</td>
      <td style="text-align:left">${_esc(c.check)}</td>
      <td style="text-align:left;color:${col};font-weight:700">${_esc(c.status)}</td>
      <td style="text-align:left;color:var(--muted);max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(c.detail || '')}</td>
    </tr>`;
  }).join('');

  resultEl.style.display = 'block';
}

// ── Init ───────────────────────────────────────────────────────────────────────
loadConfig();
loadEmotionMap();
pollStatus();
pollSleepState();
checkSDStatus();
setInterval(pollStatus, 15000);
setInterval(pollSleepState, 5000);
setInterval(checkSDStatus, 30000);

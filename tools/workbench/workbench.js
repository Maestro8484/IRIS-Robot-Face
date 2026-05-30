const PI4_BASE     = "http://192.168.1.200:5000";
const GANDALF_OLLAMA = "http://192.168.1.3:11434";

let state = {
  activeTab: "harness",
  harnessResults: [],
  connectionStatus: { pi4: null, gandalf: null },
  modelState: null,
  fixtureCases: []
};

// ─── init ──────────────────────────────────────────────────────────────────

async function init() {
  try {
    const res = await fetch("fixtures/pt001_cases.json");
    state.fixtureCases = await res.json();
  } catch (e) {
    console.error("Failed to load fixtures:", e);
    state.fixtureCases = [];
  }
  renderFixtures();
  await checkConnections();
  await loadModelState();
  setInterval(checkConnections, 30000);
}

// ─── connections ───────────────────────────────────────────────────────────

async function checkConnections() {
  const [pi4ok, gandalfok] = await Promise.all([
    fetch(PI4_BASE + "/api/logs", { signal: AbortSignal.timeout(5000) })
      .then(r => r.ok).catch(() => false),
    fetch(GANDALF_OLLAMA + "/api/tags", { signal: AbortSignal.timeout(5000) })
      .then(r => r.ok).catch(() => false)
  ]);

  state.connectionStatus.pi4     = pi4ok;
  state.connectionStatus.gandalf = gandalfok;

  setDot("pi4-dot",     pi4ok);
  setDot("gandalf-dot", gandalfok);
  setText("pi4-label",     pi4ok     ? "Pi4 connected"       : "Pi4 unreachable");
  setText("gandalf-label", gandalfok ? "GandalfAI connected" : "GandalfAI unreachable");
}

function setDot(id, ok) {
  const el = document.getElementById(id);
  if (el) el.className = "dot " + (ok ? "green" : "red");
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

// ─── model state ───────────────────────────────────────────────────────────

async function loadModelState() {
  try {
    const res = await fetch(PI4_BASE + "/api/model_state",
                            { signal: AbortSignal.timeout(10000) });
    const data = await res.json();
    state.modelState = data;

    if (!data.ok) {
      document.getElementById("model-info-wrap").innerHTML =
        `<span class="model-name">iris</span> <span class="model-warn">model state unavailable</span>`;
      setText("model-state-excerpt", data.error || "Unable to reach model");
      setText("model-ts-card", "—");
      return;
    }

    const ts    = data.modified_at ? new Date(data.modified_at) : null;
    const tsStr = ts ? ts.toLocaleString() : "unknown";
    const stale = ts ? (Date.now() - ts.getTime()) > 86400000 : false;

    document.getElementById("model-info-wrap").innerHTML =
      `<span class="model-name">${esc(data.model || "iris")}</span>` +
      ` <span class="model-ts">Modified: ${esc(tsStr)}</span>` +
      (stale ? ` <span class="model-warn">stale &gt;24h</span>` : "");

    setText("model-state-excerpt", data.modelfile_excerpt || "(no excerpt)");
    setText("model-ts-card", tsStr + (stale ? " — stale (>24h)" : ""));
  } catch (e) {
    document.getElementById("model-info-wrap").innerHTML =
      `<span class="model-name">iris</span> <span class="model-warn">model state error</span>`;
    setText("model-state-excerpt", "Error: " + e.message);
    setText("model-ts-card", "—");
  }
}

// ─── fixture rendering ─────────────────────────────────────────────────────

function renderFixtures() {
  const container = document.getElementById("fixture-list");
  if (!container) return;
  container.innerHTML = "";
  state.fixtureCases.forEach((c, i) => {
    const item = document.createElement("div");
    item.className = "fixture-item";
    item.innerHTML =
      `<input type="checkbox" id="fx-${i}" value="${i}" checked>` +
      `<div style="flex:1;min-width:0">` +
        `<div style="display:flex;gap:8px;align-items:baseline">` +
          `<span class="fi-id">${esc(c.id)}</span>` +
          `<span class="fi-input">${esc(c.input)}</span>` +
        `</div>` +
        `<div class="fi-expected">expect: ${esc(c.expected_emotion)}</div>` +
      `</div>`;
    container.appendChild(item);
  });
}

function getSelectedCases() {
  const checks = document.querySelectorAll(
    "#fixture-list input[type=checkbox]:checked");
  return Array.from(checks)
    .map(cb => state.fixtureCases[parseInt(cb.value)])
    .filter(Boolean);
}

// ─── harness run ───────────────────────────────────────────────────────────

async function runHarness(cases) {
  if (!cases || cases.length === 0) { alert("No cases selected."); return; }

  state.harnessResults = [];
  document.getElementById("results-area").innerHTML =
    `<div class="empty-state">` +
    `<span class="spinner"></span>&nbsp; Running ${cases.length} cases...</div>`;
  setText("summary-bar", "");

  for (let i = 0; i < cases.length; i++) {
    const c  = cases[i];
    const t0 = performance.now();
    let actual_emotion = null, raw_response = "", cleaned_response = "", pass = false;

    try {
      const res = await fetch(GANDALF_OLLAMA + "/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: "iris", prompt: c.input, stream: false }),
        signal: AbortSignal.timeout(60000)
      });
      const data   = await res.json();
      raw_response = data.response || "";
      const parsed = parseEmotion(raw_response);
      actual_emotion   = parsed.emotion;
      cleaned_response = parsed.cleaned;
      pass = actual_emotion === c.expected_emotion;
    } catch (e) {
      raw_response     = "ERROR: " + e.message;
      cleaned_response = raw_response;
    }

    const latency_ms = Math.round(performance.now() - t0);
    state.harnessResults.push({
      id: c.id, input: c.input,
      expected_emotion: c.expected_emotion,
      actual_emotion, pass,
      raw_response, cleaned_response, latency_ms
    });

    renderHarnessResults(state.harnessResults);
    setText("summary-bar", `Running: ${i + 1}/${cases.length}`);
  }

  renderHarnessResults(state.harnessResults);
  const passed = state.harnessResults.filter(r => r.pass).length;
  const total  = state.harnessResults.length;
  setText("summary-bar",
    `${passed}/${total} passed (${Math.round(passed / total * 100)}%)`);

  offerDownload(state.harnessResults);
}

// ─── emotion parser ────────────────────────────────────────────────────────

function parseEmotion(text) {
  const m = text.match(/\[EMOTION:([A-Z]+)\]/);
  if (!m) return { emotion: null, cleaned: text.trim() };
  return {
    emotion: m[1],
    cleaned: text.replace(/\[EMOTION:[A-Z]+\]\s*/g, "").trim()
  };
}

// ─── download ──────────────────────────────────────────────────────────────

function offerDownload(results) {
  const ts  = new Date();
  const pad = n => String(n).padStart(2, "0");
  const stamp = `${ts.getFullYear()}${pad(ts.getMonth()+1)}${pad(ts.getDate())}` +
                `_${pad(ts.getHours())}${pad(ts.getMinutes())}${pad(ts.getSeconds())}`;
  const blob = new Blob([JSON.stringify(results, null, 2)],
                        { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a   = document.createElement("a");
  a.href = url;
  a.download = `harness_${stamp}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

// ─── results render ────────────────────────────────────────────────────────

function renderHarnessResults(results) {
  const container = document.getElementById("results-area");
  if (!results || results.length === 0) {
    container.innerHTML = `<div class="empty-state">Run harness to see results</div>`;
    return;
  }
  const rows = results.map(r =>
    `<tr class="result-row ${r.pass ? "pass" : "fail"}">
      <td style="font-family:monospace;font-size:11px">${esc(r.id)}</td>
      <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
          title="${esc(r.input)}">${esc(r.input)}</td>
      <td>${esc(r.expected_emotion || "—")}</td>
      <td>${esc(r.actual_emotion   || "—")}</td>
      <td>${r.pass ? `<span class="badge-pass">PASS</span>`
                   : `<span class="badge-fail">FAIL</span>`}</td>
      <td style="color:var(--muted);font-size:11px">${r.latency_ms}ms</td>
    </tr>`
  ).join("");

  container.innerHTML =
    `<table class="result-table">
      <thead><tr>
        <th>ID</th><th>Input</th><th>Expected</th><th>Actual</th>
        <th>Result</th><th>Latency</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

// ─── handoff ───────────────────────────────────────────────────────────────

async function generateHandoff() {
  let logEvents = [];
  try {
    const res = await fetch(PI4_BASE + "/api/logs",
                            { signal: AbortSignal.timeout(8000) });
    const data = await res.json();
    logEvents  = (data.events || []).slice(-10);
  } catch (_) {}

  const ts      = new Date().toLocaleString();
  const results = state.harnessResults;
  const passed  = results.filter(r => r.pass).length;
  const total   = results.length;
  const pct     = total > 0 ? Math.round(passed / total * 100) : 0;
  const failed  = results.filter(r => !r.pass);

  const ms          = state.modelState;
  const modelName   = (ms && ms.ok && ms.model) ? ms.model : "iris";
  const modifiedAt  = (ms && ms.ok && ms.modified_at)
    ? new Date(ms.modified_at).toLocaleString() : "unknown";
  const ageMs       = (ms && ms.ok && ms.modified_at)
    ? (Date.now() - new Date(ms.modified_at).getTime()) : 0;
  const desync      = ageMs > 86400000;

  const failedLines = failed.length > 0
    ? failed.map(r =>
        `  ${r.id}: expected ${r.expected_emotion}, got ${r.actual_emotion || "null"}\n` +
        `    Input: "${r.input}"\n` +
        `    Response: ${(r.cleaned_response || "").slice(0, 200)}`
      ).join("\n\n")
    : "  (none)";

  const logLines = logEvents.length > 0
    ? logEvents.map(e =>
        `  [${e.ts || ""}] [${e.cat || ""}] ${e.msg || ""}`
      ).join("\n")
    : "  (no events)";

  const text =
`TASK: [IRIS Workbench auto-generated -- review and edit before use]
Harness run: ${ts}
Pass rate: ${passed}/${total} (${pct}%)
Failed cases:
${failedLines}

LIVE STATE (auto-gathered):
  Pi4 assistant: ${state.connectionStatus.pi4 ? "reachable" : "unreachable"}
  GandalfAI model: ${modelName} | modified_at: ${modifiedAt}
  Model desync: ${desync ? "yes -- modelfile may not match running model" : "no"}

RECENT LOG EVENTS:
${logLines}

LIKELY FILES:
  ollama/iris_modelfile.txt
  ollama/iris-kids_modelfile.txt

CONTEXT:
${failedLines}`;

  const textarea = document.getElementById("handoff-textarea");
  if (textarea) textarea.value = text;
  document.getElementById("modal-overlay").classList.add("open");
}

function closeModal() {
  document.getElementById("modal-overlay").classList.remove("open");
}

async function copyHandoff() {
  const text = document.getElementById("handoff-textarea").value;
  try {
    await navigator.clipboard.writeText(text);
    const btn = document.getElementById("copy-btn");
    btn.textContent = "Copied!";
    setTimeout(() => { btn.textContent = "Copy to Clipboard"; }, 2000);
  } catch (e) {
    alert("Copy failed: " + e.message);
  }
}

// ─── rebuild model ─────────────────────────────────────────────────────────

async function rebuildModel(target) {
  const statusEl  = document.getElementById("rebuild-status");
  const rebuildBtn = document.getElementById("rebuild-btn");
  rebuildBtn.disabled = true;
  statusEl.className  = "";
  statusEl.innerHTML  =
    `<span class="spinner"></span> Rebuilding ${target}... this takes 30-60s`;

  try {
    const res = await fetch(PI4_BASE + "/api/rebuild_model", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: target }),
      signal: AbortSignal.timeout(130000)
    });
    const data = await res.json();
    if (!data.ok) {
      statusEl.className = "error";
      statusEl.textContent = (data.error || "").includes(".iris_secrets")
        ? "Configure /home/pi/.iris_secrets on Pi4 to enable model rebuild"
        : "Error: " + (data.error || "unknown");
    } else {
      statusEl.className  = "ok";
      statusEl.textContent = `Rebuilt ${target} OK`;
      await loadModelState();
    }
  } catch (e) {
    statusEl.className  = "error";
    statusEl.textContent = "Request failed: " + e.message;
  } finally {
    rebuildBtn.disabled = false;
  }
}

// ─── tab switching ─────────────────────────────────────────────────────────

function switchTab(tabName) {
  state.activeTab = tabName;
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.tab === tabName);
  });
  document.querySelectorAll(".tab-panel").forEach(panel => {
    panel.classList.toggle("active", panel.id === "tab-" + tabName);
  });
}

// ─── helpers ───────────────────────────────────────────────────────────────

function esc(s) {
  if (!s) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ─── bootstrap ─────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", init);

# IRIS Benchmarking Audit — S105 (2026-06-07)

## Summary

The IRIS benchmarking system is split across three distinct layers:
1. Pi4 control panel **Bench tab** (live pipeline timing — `journalctl`-based)
2. Pi4 persistent **JSONL log** (`iris_bench.jsonl` — never read by control panel)
3. Local developer **Workbench tool** (`tools/workbench/` — personality harness, latency bench, AI analysis)

The "lack of logs in the control panel" is real but has a specific cause: the `/api/bench`
endpoint reads from `journalctl` only, and the Pi4 journal is volatile (RAM-backed, wiped on
reboot). After today's S103/S104 restarts with no new LLM interactions, the journal has
**zero [BENCH] lines**. The Bench tab shows empty.

---

## Layer 1 — Control Panel Bench Tab (`/api/bench`)

**How it works:**
- `iris_web.py` `/api/bench` runs `journalctl -u assistant -n 600 --output=short-iso`
- Parses `[BENCH]` tagged lines emitted by `assistant.py` and `services/llm.py`
- Returns last 20 cycles as JSON to the frontend
- `iris_web.js` `fetchBench()` renders the timing table + Active Tuning Levers panel

**Stages captured:**
| Stage | Source | Fields |
|---|---|---|
| `wake_detected` | assistant.py | trigger (wake/ptt), gandalf_was_cold |
| `rec_done` | assistant.py | dur_rec, wake_to_rec_start_ms, record_duration_ms, rms |
| `stt_done` | assistant.py | dur_stt, stt_ms, transcript |
| `router_done` | assistant.py | router_ms, route |
| `llm_start` | assistant.py | tier, num_predict, model, gandalf_was_cold |
| `llm_first_chunk` | assistant.py | dur_ttfc, llm_first_token_ms |
| `llm_done` | assistant.py | dur_llm, llm_total_ms, reply_chars |
| `tts_done` | assistant.py | dur_tts, tts_ms, reply_chars, **engine** (kokoro/piper) |
| `play_start` | assistant.py | play_start_ms |
| `audio_done` | assistant.py | dur_audio, dur_total |
| `ollama_stats` | services/llm.py | eval_tokens, prompt_tokens, eval_ms, prompt_ms |

**Columns rendered in the table:**
`#` · `Time` · `Trigger` · `Tier` · `Token Limit` · `Recording` · `Transcription` ·
`1st LLM Chunk` · `LLM Stream` · `TTS Synth` · `Playback` · `To First Word` ·
`End-to-End` · `Tokens (Eval/Prompt)` · `Transcript`

**Status: Working, but ephemeral.**

---

## Why the Bench Tab Shows Empty

### Root cause: volatile journal

The Pi4 runs an overlay filesystem (read-only SD + RAM tmpfs). `journald` is configured
`#Storage=auto` — with no `/var/log/journal` directory on the RO SD, journald falls back to
volatile (in-RAM) storage at `/run/log/journal`. On every reboot, all journal entries are lost.

After today's S103/S104 restarts with sleep/wake testing (no LLM interactions), the journal
has **0 [BENCH] lines**. The tab is empty until a user actually speaks to IRIS and triggers
the LLM path.

**This is not a bug in the control panel — it's a data availability problem.**

---

## Layer 2 — JSONL Bench Log (`iris_bench.jsonl`)

**How it works:**
- `_bench_write()` in `assistant.py` appends one JSON record per completed cycle
- Path: `/home/pi/logs/iris_bench.jsonl`
- SD mirror defined in config: `/media/root-ro/home/pi/logs/iris_bench.jsonl`

**Live state (checked 2026-06-07):**
- RAM JSONL: **4 records**, 1640 bytes, last entry 2026-06-06T21:56
- SD JSONL: **0 bytes** (created 2026-05-30, never populated — persistence was never done)
- **All 4 records will be lost on next reboot**

**What the JSONL captures (vs journal):**
```json
{
  "ts":               "2026-06-06T19:59:09",
  "stages":           { "wake_to_record_start_ms": 302, "record_duration_ms": 9877,
                        "stt_ms": 404, "router_ms": 0, "llm_first_token_ms": 3214,
                        "llm_total_ms": 14125, "tts_ms": 683, "play_start_ms": 25404 },
  "total_ms":         25404,
  "transcript":       "Are you a stupid robot?",
  "reply_chars":      220,
  "model":            "iris",
  "gandalf_was_cold": false,
  "route":            "LLM",
  "interrupted":      false
}
```

**Missing from JSONL (present in journal only):**
- `engine` (kokoro / piper) — in `tts_done` stage but not passed to `_bench_write()`
- `eval_tokens` / `prompt_tokens` — from `ollama_stats` stage, never written to JSONL
- `tier` + `num_predict` — from `llm_start` stage, not in JSONL
- **`emotion`** — `_current_emotion` is known at call site but not passed to `_bench_write()`

**Critical gap: the control panel `/api/bench` never reads from this file.**
The JSONL exists as a persistent record but is currently dead data — nothing reads it.

---

## Layer 3 — IRIS Workbench (`tools/workbench/`)

A standalone local developer tool at `tools/workbench/index.html`. Opens in a browser, runs
from the local machine (not served from Pi4). Connects directly to GandalfAI Ollama API and
Pi4 Flask API.

**Tabs and capability:**

| Tab | What it does |
|---|---|
| **Personality Harness** | Runs test cases from `fixtures/pt001_cases.json` directly against `iris` model on GandalfAI Ollama. Parses `[EMOTION:X]` tags. Tracks pass/fail against expected emotion. Downloads JSON results. |
| **Latency Bench** | Runs each fixture N times (1/3/5/10×), measures round-trip ms to GandalfAI. Shows p50/p90/p99, sparklines, histogram. |
| **POST / Diagnostics** | Triggers Pi4 `/api/post` L0–L4 diagnostic. |
| **Feature Setup** | Live VOL_MAX, SPEAKER_VOLUME, GESTURE_SENSOR_REQUIRED, gesture map. |
| **Run AI Analysis** | Sends harness failures + modelfile excerpt to Claude Sonnet API. Classifies each failure as FIXTURE_WRONG or MODEL_WRONG, suggests modelfile patches, generates new edge cases. |
| **Generate Handoff** | Produces session handoff text from harness results + Pi4 log events + model state. |

**Key design property: tests Ollama in isolation, not the full pipeline.**
The workbench sends text directly to Ollama. It does NOT test: wakeword, recording, STT,
routing, TTS synthesis, playback, or emotion→display dispatch. A model that passes 17/17
here could still behave differently in production if temperature/context differs.

**Phase 2 analysis results (2026-05-30 run, pt001 fixture):**
- 12/17 passed (71%) on qwen2.5:32b
- 5 failures: pt001_08/09/12/13/17
- pt001_12/13: MODEL_WRONG (exact few-shot existed, emotion tag drifted anyway — temperature 0.92 suspected)
- pt001_17 ("goodnight"): MODEL_WRONG — no few-shot, reverted to cheerful-assistant; `Night.` example added to modelfile (S102)
- Fixture corrections for pt001_08/09 pending AI analysis confirmation (status: TBD in phase2_analysis.md)

---

## Benchmarking Was NOT Relocated to GandalfAI

GandalfAI runs no benchmarking code. It only serves Ollama and Kokoro TTS. The workbench
tool connects TO GandalfAI from a local machine for pre-flight testing, but the actual
telemetry infrastructure (journal, JSONL, bench API) lives entirely on Pi4.

---

## Gaps and Issues

### G1 — JSONL not read by control panel (critical)
`/api/bench` uses only journalctl. After any reboot the bench tab is empty until new
interactions occur. Fix: add JSONL fallback (or primary read) to `/api/bench`.

### G2 — JSONL not SD-persisted (critical)
`/media/root-ro/home/pi/logs/iris_bench.jsonl` is 0 bytes. All 4 existing records will
be lost on next reboot. Fix: add `iris_bench.jsonl` to the SD persist workflow.

### G3 — Emotion tag not in BENCH record (significant)
`_current_emotion` is available at the `_bench_write()` call site but not passed.
The JSONL has timing and transcript but no record of what emotion was expressed.
Without this, there's no way to track personality drift over time in production.

### G4 — TTS engine, tier, num_predict, tokens not in JSONL (moderate)
These are all emitted in `[BENCH]` journal lines but not saved to JSONL. The journal is
volatile, so these fields are effectively ephemeral.

### G5 — `iris_bench_report.py` has wrong service name in comment (minor)
Line 6 says `journalctl -u iris-assistant.service` — service is actually `assistant.service`.
Running the script with that command returns nothing.

### G6 — No congruency tracking in production (design gap)
The workbench tests personality pre-flight (emotion accuracy). Production responses are
never evaluated against expected emotion/tone for the input. IRIS could drift in production
without any signal appearing in the control panel. Closing this gap would require either:
  a) Adding the emotion tag to JSONL + surfacing it in the Bench tab (quick)
  b) A live "personality score" stream that compares each production response against
     the workbench fixture set (significant engineering)

### G7 — Bench tab not linked to active modelfile state (moderate)
The Workbench shows "Model State" (modified_at, modelfile excerpt) next to harness results.
The control panel Bench tab shows timing but has no "which modelfile was active" column.
When a modelfile change changes behavior, you can't correlate that in the bench tab.

---

## Quick Fix Recommendations (priority order)

1. **Persist JSONL to SD** — single command, prevents data loss.
   ```
   cp /home/pi/logs/iris_bench.jsonl /media/root-ro/home/pi/logs/iris_bench.jsonl
   ```
   Then add to the standard deploy persist workflow.

2. **Add `emotion` field to `_bench_write()`** — pass `_current_emotion` at all call sites.
   Control panel can then show emotion tag per cycle in the bench table.

3. **Add `tier`, `num_predict`, `engine`, `eval_tokens`, `prompt_tokens` to JSONL** —
   or change `/api/bench` to fall back to JSONL when journalctl returns no cycles.

4. **Fix `iris_bench_report.py` CLI comment** — change `iris-assistant.service` → `assistant`.

5. **`/api/bench` JSONL fallback** — if journalctl returns 0 cycles, read from JSONL.
   This makes the bench tab persistent across reboots without changing the journal setup.

---

## Congruency Tracking Architecture (if desired)

To track personality/congruency in production responses:

```
assistant.py [BENCH] stage=response_tagged  emotion=AMUSED  transcript="..." reply_snip="..."
```

Combined with:
- JSONL field: `"emotion": "AMUSED"`
- Control panel Bench tab: color-coded Emotion column next to Transcript
- Optional: alert when the same input class (insult/identity probe/greeting) produces a
  different emotion than the fixture expected (requires fixture lookup at runtime)

The workbench already has the fixture dataset and the AI analysis loop. The gap is
that production responses don't flow back into that loop.

---

## Current JSONL Sample (4 records, 2026-06-06)

| Time | Transcript | Route | Total ms | TTFC ms | gandalf_cold |
|---|---|---|---|---|---|
| 19:58 | Tell me something funny. | LLM | 36,238 | 20,657 | **true** |
| 19:59 | Are you a stupid robot? | LLM | 25,404 | 3,214 | false |
| 20:56 | Why did the queen go to the dentist? | LLM | 37,276 | 17,931 | false |
| 21:56 | What is your name? Are you fat?... | LLM | 32,313 | 10,808 | false |

Note: First cycle (36s total, 20.6s TTFC) shows Gandalf cold-start penalty.
Subsequent cycles (25s, 37s, 32s) are warm — TTFC varies 3–18s with qwen2.5:32b.

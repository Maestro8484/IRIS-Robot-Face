# IRIS Snapshot

**Session:** S54 | **Date:** 2026-05-19 | **Branch:** `main` | **Last commit:** S54(D): Pi4 idle backlight dimming — MOUTH_INTENSITY_IDLE

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.
> Current state and roadmap: see `HANDOFF_CURRENT.md`.

---

## Machine Status

| System | Status |
|---|---|
| SuperMaster Desktop | Canonical local repo. Claude Desktop, filesystem MCP, SSH MCP active. |
| Pi4 192.168.1.200 | Operational. S54(D): assistant.py + config.py (MOUTH_INTENSITY_IDLE) deployed, md5 verified (config `535d62b3`, assistant `259dd0a1`), SD persisted, assistant restarted — [INFO] Ready. confirmed. |
| GandalfAI 192.168.1.3 | Operational. iris + iris-kids models rebuilt (S48) — PT-001 few-shot adversarial examples live. |
| Teensy 4.1 | Firmware updated (S54 A+B+C) — REPO-ONLY. BL_MAP log curve + idle animations committed. Flash pending user action (PlatformIO upload). |
| TTS | Kokoro primary (Docker, GandalfAI port 8004), Piper fallback (Wyoming port 10200). |
| Web UI | Operational. S53 DEPLOYED (2026-05-19): Bench tab — 20-cycle history, To First Word column, expanded headers, trigger full name, color coding. md5 iris_web.py `5fc8b075e52bf0dd4bc26f39e507f3dc`, iris_web.html `7d3a63f629a5195085a753e93b541cff`. |

---

## Workflow Rule: Status Terminology (adopted S47)

Status words are strictly defined. Claude Code must use only these terms:

- REPO-ONLY: files changed/committed locally, live IRIS unchanged.
- PUSHED: changes on GitHub, live IRIS may still be unchanged.
- DEPLOYED: changes copied/rebuilt/flashed to relevant live system.
- VERIFIED: behavior tested on live IRIS and confirmed.

No change is "done," "complete," "implemented," or "working" until VERIFIED.

Every session close must include this block, fully filled out:

```text
Repo status:
GitHub status:
Pi4 live status:
Teensy firmware status:
GandalfAI model status:
Live IRIS behavior right now:
Remaining steps before user-visible behavior changes:
```

---

## Active Issues

- **LOW: "stop" Whisper hallucination** — RD-001 Option 1 (post-STT STOP phrase gate) deployed and handles most cases. Residual: Whisper may hallucinate "stop" into unrelated text before the gate sees it. Pre-STT RMS intercept deferred as not required.
- **MED: LLM personality inconsistency** — Standing rule: any LLM drift = check GandalfAI sync first (`ollama show iris --modelfile` vs repo). See memory: project_gandalf_modelfile_sync.md.
- **LOW: root-level stale sleep log** — /home/pi/iris_sleep.log may duplicate /home/pi/logs/iris_sleep.log.
- **MED: Perceived wake-to-response latency (30-40s on slow turns)** — INSTRUMENTED + DEPLOYED (S50). Bench timing in all stages live on Pi4. JSONL log at `/home/pi/logs/iris_bench.jsonl` — fills after first voice turn. After ~1 week of use, review to identify dominant stage. Pending user action: set `OLLAMA_KEEP_ALIVE=30m` on GandalfAI (Windows machine env var + restart Ollama service). KOKORO_SPEED slider live in Web UI Voice tab — set to 1.15 and persist to SD for faster TTS.

---

## Session Scope

S50: Latency hardening + observability. KOKORO_SPEED config param, complete bench timing instrumentation (new stages + JSONL log), journald retention (500MB/1yr), intent log retention (365 days). DEPLOYED — assistant active, [INFO] Ready. confirmed. Pending: user voice verification + OLLAMA_KEEP_ALIVE + KOKORO_SPEED dial-in via Web UI.

---

## Last Session Changes (S54)

RD-008: Mouth TFT visual overhaul. Firmware (A+B+C) REPO-ONLY, Pi4 (D) DEPLOYED.

- **`src/mouth_tft.cpp`** — BL_MAP[16] log curve replaces linear map. `_currentBLLevel` + `_currentMouthIdx` tracking. All analogWrite calls use BL_MAP. Idle animation engine: 6 animations (BREATHE/DRIFT/TWITCH/BLINK/YAWN/SIDESMIRK), millis-based, interruptible. mouthIdleStart/Stop/Tick/IsActive API.
- **`src/mouth_tft.h`** — 4 new idle API declarations.
- **`src/main.cpp`** — lastCommandMs + IDLE_AUTO_MS. mouthIdleStop() on all MOUTH/EMOTION/EYES commands. IDLE:START/STOP handlers. Auto-start after 120s. mouthIdleTick() in non-sleep loop.
- **`pi4/core/config.py`** — MOUTH_INTENSITY_IDLE=3 added, _OVERRIDABLE + _TYPE_COERCE registered.
- **`pi4/assistant.py`** — MOUTH_INTENSITY_AWAKE sent on wakeword. MOUTH_INTENSITY_IDLE sent after LLM+TTS+followup cycle ends.
- Commits: `4e7c61b` (firmware), `bd6598b` (Pi4). Pi4 md5 verified, SD persisted, assistant running.

## Previous Session Changes (S53)

Bench tab improvements. No firmware, no GandalfAI, no assistant.py changes.

- Bench tab: 20-cycle history, To First Word column, expanded headers. S53 DEPLOYED (2026-05-19). md5 iris_web.py `5fc8b075e52bf0dd4bc26f39e507f3dc`, iris_web.html `7d3a63f629a5195085a753e93b541cff`.

## Previous Session Changes (S52)

Web UI changes only. No firmware, no GandalfAI, no assistant.py changes.

- **`pi4/iris_web.py`** — `_speak_worker` rewritten: calls Kokoro API directly from live `cfg` dict (`KOKORO_VOICE` + `KOKORO_SPEED`); Piper fallback retained. Fix: module-level `KOKORO_ENABLED` import was stale, causing all chat TTS to fall back to Piper. New `/api/vision` endpoint: libcamera-still → base64 → Ollama vision model → emotion strip + clean → optional Kokoro speak.
- **`pi4/iris_web.html`** — Voice tab: `KOKORO_SPEED` field added (0.5–2.0), Kokoro Web UI link fixed to `/web`, `saveKokoroSettings()` includes KOKORO_SPEED. Chat tab: Vision Demo card added (5 presets + custom prompt + Kokoro speak toggle).
- **`CLAUDE.md`** — Approval gate removed (pre-flight summary + wait-for-confirmation steps). Commit `bda42c9` pushed.
- Pi4 DEPLOYED, md5 verified (`iris_web.py` `59115bdda6f063faffde1f7593f54c61`, `iris_web.html` `e1ddf120dc8d0667544eda105d9cf1ec`), iris-web restarted — Flask serving on 0.0.0.0:5000 confirmed.

## Previous Session Changes (S51)

Intent router regex hardening. No firmware, no GandalfAI, no assistant.py changes.

- **`pi4/core/intent_router.py`** — 5 changes: `_DATE_RE` + `_TIME_RE` negative lookaheads blocking historical context words; `_KIDS_OFF_RE` bare adult/normal mode removed; `digit` range fixed 1–100 → 0–9; RANDOM_NUMBER payload logs result. Commit: `6b6ea48`. Pi4 DEPLOYED, md5 `184e38ae685ce03f00e05cf29b3c0adf` verified, assistant restarted active.
- **Deploy note:** Overlayfs direct-write truncation workaround confirmed — sftp_write to `/tmp/`, then `mv`. Both overlay paths are same inode.

## Previous Session Changes (S50)

Pi4 code deploy + journald config install. No firmware, no GandalfAI, no iris_web changes.

- **`pi4/assistant.py`** — `_bench_write()` helper. Full bench stage coverage with `time.monotonic()`: `wake_to_record_start_ms`, `record_duration_ms`, `stt_ms`, `router_ms`, `llm_first_token_ms`, `llm_total_ms`, `tts_ms`, `play_start_ms`. JSONL written to `/home/pi/logs/iris_bench.jsonl` on every turn. All bench logging guarded in try/except.
- **`pi4/core/config.py`** — `KOKORO_SPEED = 1.0` added; registered in `_OVERRIDABLE` and `_TYPE_COERCE` (float, 0.5–2.0). Web UI can override without restart.
- **`pi4/services/tts.py`** — `_synthesize_kokoro()` lazy-imports `KOKORO_SPEED` per call; passes `"speed"` to Kokoro-FastAPI payload.
- **`pi4/core/intent_router.py`** — `backupCount` 7 → 365 days.
- **`pi4/etc/journald.iris.conf`** + **`pi4/scripts/install_journald.sh`** (new) — 500MB/1yr journald retention. Conf installed to `/etc/systemd/journald.conf.d/iris.conf`, persisted to SD.
- Commit: `bae8da0`. Pi4 DEPLOYED, all 6 files md5 verified, assistant restarted — `[INFO] Ready.` confirmed.

## Previous Session Changes (S49)

Web UI fixes only. No firmware, no GandalfAI, no assistant.py changes.

- **`pi4/iris_web.py`** — `/api/generate` route renamed to `/api/chat` (was causing 404 on all chat sends). Response cleaning added in `api_chat()`: `extract_emotion_from_reply()` + `clean_llm_reply()` now called before TTS — emotion tags and markdown no longer spoken aloud. New `/api/speak` endpoint for verbatim TTS (bypasses LLM). `/api/logs` rewritten to return structured `{events: [...]}` JSON with category, timestamp, message, detail fields.
- **`pi4/iris_web.html`** — Log tab: replaced raw journalctl dump with categorized event panel + filter bar (All / Wakeword / Heard / Route / LLM / Spoken / STOP / Drift / Errors). Chat tab: verbatim speak mode added (sends to `/api/speak` directly, no LLM). Chat response now displays emotion tag inline. TTS conflict warning note added to UI.
- Commit: `6509cca`. Pi4 DEPLOYED, SD persisted, md5 verified, iris-web restarted active.

## Previous Session Changes (S48)

Two tasks completed. No firmware changes. No GandalfAI changes.

- **`/home/pi/iris_config.json` (Pi4 live)** — `NUM_PREDICT: 200` key removed. SD persisted (md5 verified). assistant.py restarted — `[INFO] Ready.` confirmed. Tiered classifier (SHORT/MEDIUM/LONG/MAX) now controls LLM response length unconstrained.
- **`ollama/iris_modelfile.txt`** — PT-001: 8 few-shot adversarial examples added (insults, identity challenges, NEUTRAL deflections). DEPLOYED.
- **`ollama/iris-kids_modelfile.txt`** — PT-001: 4 kid-appropriate AMUSED/NEUTRAL examples added (warm, playful redirect). DEPLOYED.

## Previous Session Changes (S47)

RD-002 AMUSED emotion — FULLY DEPLOYED (2026-05-03). Pi4 live (md5 verified), Teensy 4.1 firmware flashed, iris-kids model rebuilt on GandalfAI.

- **`pi4/core/config.py`** — Added "AMUSED" to `VALID_EMOTIONS`; added `"AMUSED": 2` to `MOUTH_MAP` (reuses CURIOUS/smirk expression).
- **`pi4/hardware/led.py`** — AMUSED: sinusoidal breathe, amber [255,160,0], floor=10, peak=80, period=1.5s, gamma=1.8, duration=3s. Special case in show_emotion(); not in _EMOTION_LED dict.
- **`src/main.cpp`** — Added AMUSED to `EmotionID` enum; added `{0.55f, false, 3000}` entry to `emotionTable`; added AMUSED case to `parseEmotion`. No eye swap — falls to default `else` branch in `applyEmotion`.
- **`pi4/iris_web.html`** — Added AMUSED button to Emotion Test grid (`sendEmotion('AMUSED', 2)`).
- **`ollama/iris-kids_modelfile.txt`** — AMUSED added to valid emotion list.
- Docs updated: SNAPSHOT_LATEST.md, HANDOFF_CURRENT.md, ROADMAP.md, CHANGELOG.md, docs/iris_issue_log.md.

## Previous Session Changes (S46)

WoL acknowledgement beep. Code only. Deployed and verified on Pi4.

- **`pi4/hardware/audio_io.py`** — Added `play_wol_beep(pa)`: ascending 2-tone 660→880 Hz, ~360 ms, exported.
- **`pi4/assistant.py`** — Imported `play_wol_beep`; added `pa=None` param to `ensure_gandalf_up`; beep fires inside function immediately after WoL send; both call sites updated to pass `pa`.

## Previous Session Changes (S45)

Batch A docs-only cleanup. No code, no deploy, no Pi4/GandalfAI changes.

- **`IRIS_ARCH.md`** — Chatterbox→Kokoro primary; Batch 1C marked Complete; gemma3:27b-it-qat in repo structure.
- **`README.md`** — Teensy 4.1; 7-eye table corrected; PROG button note removed.
- **`CLAUDE.md`** — GandalfAI role updated: Kokoro primary, Piper fallback, Chatterbox rollback only.

## Next Work

- **IMMEDIATE: Flash Teensy firmware** — click PlatformIO upload. Firmware build `4e7c61b` is ready (pio run PASSED). Unlocks BL_MAP + idle animations.
- After flash: dark-room verify — sleep=nearly off, idle=dim (level 3), wakeword fires + brightens, post-speech dims to 3.
- `MOUTH_INTENSITY_IDLE` can be tuned via iris_config.json (range 0-15).
- S50 pending user actions: OLLAMA_KEEP_ALIVE on GandalfAI.
- PT-001: DEPLOYED. Pending: live adversarial testing.

See `ROADMAP.md` for full forward-looking task list and item specs.

---

## Do Not Touch Without Explicit Instruction

- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

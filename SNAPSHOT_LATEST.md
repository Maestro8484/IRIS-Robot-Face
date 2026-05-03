# IRIS Snapshot

**Session:** S48 | **Date:** 2026-05-03 | **Branch:** `main` | **Last commit:** S47: RD-002 AMUSED emotion full implementation

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.
> Current state and roadmap: see `HANDOFF_CURRENT.md`.

---

## Machine Status

| System | Status |
|---|---|
| SuperMaster Desktop | Canonical local repo. Claude Desktop, filesystem MCP, SSH MCP active. |
| Pi4 192.168.1.200 | Operational. assistant.py + intent_router.py + iris_web.py deployed, persisted, verified. |
| GandalfAI 192.168.1.3 | Operational. iris + iris-kids models rebuilt (S48) — PT-001 few-shot adversarial examples live. |
| Teensy 4.1 | Operational. Eye movement suspended during TTS (S36). |
| TTS | Kokoro primary (Docker, GandalfAI port 8004), Piper fallback (Wyoming port 10200). |
| Web UI | Operational. Bench tab live. Logs tab now shows intent routing decisions. |

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

---

## Session Scope

S48: Two tasks. (1) NUM_PREDICT override removed from Pi4 iris_config.json — tiered classifier now controls response length (SHORT=120, MEDIUM=350, LONG=700, MAX=1200). DEPLOYED+VERIFIED. (2) PT-001 — few-shot adversarial examples added to iris_modelfile.txt and iris-kids_modelfile.txt. Both models rebuilt on GandalfAI. DEPLOYED.

---

## Last Session Changes (S48)

Two tasks completed. No firmware changes. No GandalfAI changes.

- **`/home/pi/iris_config.json` (Pi4 live)** — `NUM_PREDICT: 200` key removed. SD persisted (md5 verified). assistant.py restarted — `[INFO] Ready.` confirmed. Tiered classifier (SHORT/MEDIUM/LONG/MAX) now controls LLM response length unconstrained.
- **`ollama/iris_modelfile.txt`** — PT-001: 8 few-shot adversarial examples added (insults, identity challenges, NEUTRAL deflections). DEPLOYED.
- **`ollama/iris-kids_modelfile.txt`** — PT-001: 4 kid-appropriate AMUSED/NEUTRAL examples added (warm, playful redirect). DEPLOYED.

Kids modelfile (iris-kids_modelfile.txt): edited — 4 kid-appropriate AMUSED/NEUTRAL examples added (warm, playful redirect).
Model rebuild: DEPLOYED — iris and iris-kids rebuilt on GandalfAI (S48).

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

- RD-002 AMUSED: FULLY DEPLOYED. Pending: live behavior verification.
- PT-001: DEPLOYED. Pending: live adversarial testing.
- RD-001: COMPLETE. RD-003 (duplicate sleep log) is next low-priority item.

See `ROADMAP.md` for full forward-looking task list and item specs.

---

## Do Not Touch Without Explicit Instruction

- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

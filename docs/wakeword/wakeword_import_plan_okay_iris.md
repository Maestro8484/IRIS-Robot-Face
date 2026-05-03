# Wakeword Import Plan — okay_iris / "Okay, IRIS"
**Session:** S44 prep | **Date:** 2026-04-28 | **Status:** Review only — no files written

---

## 1. Current Wakeword Runtime Architecture

Wyoming OpenWakeWord (OWW) is the detection backend, running as a subprocess on Pi4.

**Startup flow (`assistant.py:336-349`):**
```
subprocess: /home/pi/wyoming-openwakeword/.venv/bin/python3 -m wyoming_openwakeword
  --uri tcp://127.0.0.1:{OWW_PORT}
  --preload-model {WAKE_WORD}        ← model name string
  --threshold {OWW_THRESHOLD}        ← server-side score gate
```

**Detection flow (`services/wakeword.py`):**
- Sends audio chunks to OWW socket via Wyoming protocol
- OWW emits `detection` events when score >= server threshold
- `wakeword.py` applies `OWW_THRESHOLD` as a second client-side gate
- Returns `"wake"` to `assistant.py` main loop

**Current model:** `hey_jarvis` — a built-in OWW bundled model (no file needed).  
**Current threshold:** `OWW_THRESHOLD = 0.90` (config.py:139), mirrored as `--threshold` arg.

**How custom models are loaded:**  
wyoming-openwakeword supports a `--custom-model-dir <path>` CLI flag. Any `.onnx` file in that dir
is loadable by name (filename without extension). Without this flag, only bundled models are available.

---

## 2. Files That Reference Wakeword Loading / Config

| File | Line(s) | What it does |
|---|---|---|
| `pi4/core/config.py` | 22 | `WAKE_WORD = "hey_jarvis"` — model name string |
| `pi4/core/config.py` | 139 | `OWW_THRESHOLD = 0.90` — score gate |
| `pi4/core/config.py` | 186 | OWW_THRESHOLD range validator (0.5–1.0) |
| `pi4/assistant.py` | 338–340 | Subprocess launch: `--preload-model WAKE_WORD --threshold OWW_THRESHOLD` |
| `pi4/services/wakeword.py` | 69 | `wy_send(oww_sock, "detect", {"names": [WAKE_WORD]})` |
| `iris_config.json` | (protected) | Can override OWW_THRESHOLD at runtime |

**Not touched by this change:** `wakeword.py` logic, Wyoming protocol, audio pipeline.

---

## 3. Recommended Repo Location for Deployable Model

```
pi4/wakewords/okay_iris.onnx       ← ONLY this file gets deployed to Pi4
```

**Rationale:**
- `pi4/` mirrors `/home/pi/` on Pi4 — this makes the deploy path obvious.
- wyoming-openwakeword will need `--custom-model-dir /home/pi/wakewords` added to the subprocess args.
- Keeps model physically near the runtime code that uses it.
- Do NOT commit `okay_iris.pt` here — it is the PyTorch training checkpoint (~MB), runtime doesn't use it.

---

## 4. Artifact Disposition

| File | Action | Reason |
|---|---|---|
| `okay_iris.onnx` | **Commit to `pi4/wakewords/`** | Runtime model — needed on Pi4 |
| `okay_iris.pt` | **Archive to `docs/wakeword_training/okay_iris/`** | Training checkpoint; not used at runtime; keep for retraining |
| `okay_iris.yaml` | **Archive to `docs/wakeword_training/okay_iris/`** | Training config; needed if retraining |
| `okay_iris_eval.json` | **Archive to `docs/wakeword_training/okay_iris/`** | Audit trail for model quality |
| `okay_iris_metrics.json` | **Archive to `docs/wakeword_training/okay_iris/`** | Audit trail for training convergence |
| `okay_iris_det.png` | **Archive to `docs/wakeword_training/okay_iris/`** | Detection distribution chart |

Training artifacts are NOT imported to `IRIS_wakeword_import/` — they stay in `docs/` only.
No WAVs or feature files exist in the import package — confirmed clean.

---

## 5. CRITICAL: Model Quality Concern

**The eval numbers are weak at the configured threshold.**

From `okay_iris_eval.json`:

| Threshold | Recall | FPPH |
|---|---|---|
| 0.5 (training default) | 29.55% | 0.0 |
| 0.2 (optimal) | 86.75% | 0.168 |

At the current IRIS production threshold of **0.90**, this model will have recall near **0%** — it will
essentially never fire. The model's score distribution peaks far below 0.9.

**Before deploying, one of these must be true:**
- (A) OWW score normalization re-maps the custom model output differently than eval suggests — needs live test.
- (B) `OWW_THRESHOLD` must be lowered significantly for this model. 0.2–0.3 range is the operative window.
  - 0.168 FPPH = ~1 false wake per 6 hours. Acceptable for a robot context.
  - The current range validator (`config.py:186`) enforces min=0.5 — this would need relaxing to 0.1.

**Recommendation:** Do a live Pi4 score test before finalizing the threshold value.
Run OWW with `--custom-model-dir` and log raw scores against "Okay, IRIS" utterances.
Do not change WAKE_WORD in production until recall is confirmed >70% in live conditions.

---

## 6. Rollback Path

The current model (`hey_jarvis`) is a **bundled OWW model** — no file to restore.

Rollback is a single config revert:
```python
# pi4/core/config.py
WAKE_WORD = "hey_jarvis"    # restore
OWW_THRESHOLD = 0.90        # restore
```
And remove `--custom-model-dir` from `assistant.py` subprocess args.

No Pi4 filesystem deletions required. The `pi4/wakewords/` directory can remain.

---

## 7. Minimal Patch Plan

**Step 1 — Repo structure (SuperMaster, no deploy):**
- Create `pi4/wakewords/` directory in repo.
- Copy `okay_iris.onnx` → `pi4/wakewords/okay_iris.onnx`.
- Create `docs/wakeword_training/okay_iris/` directory.
- Copy remaining 5 artifacts there (pt, yaml, eval.json, metrics.json, det.png).
- Commit: `"feat: import okay_iris wakeword model and archive training artifacts"`

**Step 2 — Config change (SuperMaster, no deploy):**
- `pi4/core/config.py:22`: `WAKE_WORD = "okay_iris"`
- `pi4/core/config.py:139`: `OWW_THRESHOLD = 0.25`  ← provisional; tune after live test
- `pi4/core/config.py:186`: OWW_THRESHOLD range min: `0.5` → `0.1`
- `pi4/assistant.py:338`: add `"--custom-model-dir", "/home/pi/wakewords"` to subprocess args
- Commit: `"feat: switch wakeword to okay_iris, lower OWW_THRESHOLD for custom model"`

**Step 3 — Deploy (requires explicit DEPLOY instruction):**
- `rsync` or SFTP `okay_iris.onnx` → `/home/pi/wakewords/okay_iris.onnx` on Pi4
- Persist to SD layer (standard Pi4 persistence pattern)
- Deploy updated `assistant.py` and `config.py` to Pi4
- Restart `iris.service`
- Live score test: say "Okay, IRIS" 10x, log `[OWW] score=` output
- Tune threshold based on observed scores
- Do NOT remove `hey_jarvis` from OWW install

---

## 8. Files Likely Touched

**Step 1 (structural):**
- `pi4/wakewords/okay_iris.onnx` (new)
- `docs/wakeword_training/okay_iris/okay_iris.pt` (new)
- `docs/wakeword_training/okay_iris/okay_iris.yaml` (new)
- `docs/wakeword_training/okay_iris/okay_iris_eval.json` (new)
- `docs/wakeword_training/okay_iris/okay_iris_metrics.json` (new)
- `docs/wakeword_training/okay_iris/okay_iris_det.png` (new)

**Step 2 (config):**
- `pi4/core/config.py` (lines 22, 139, 186)
- `pi4/assistant.py` (line 338, subprocess args)

**NOT touched:**
- `pi4/services/wakeword.py` — no changes needed
- `iris_config.json` — protected; threshold override can be set there post-deploy
- `alsa-init.sh`, `TeensyEyes.ino`, `EyeController.h` — unrelated

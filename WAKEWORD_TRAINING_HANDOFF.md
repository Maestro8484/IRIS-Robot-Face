# Wakeword Training Handoff — 2026-04-25

## Resource Expenditure

### Time
- **Session 1** (previous context, now summarized): ~2–3 hours. Covered Wyoming protocol debugging, persistent Piper socket, pythonw vs Start-Process discovery, OWW model download fix, int16 dtype fix, speechbrain/k2 root cause analysis.
- **Session 2** (this context): ~1.5 hours. Covered pure-PyTorch rewrite, deploy/launch iterations, onnxscript discovery, ml_dtypes conflict diagnosis.
- **Total wall-clock time across both sessions**: ~4–5 hours.

### Claude Code Turns / Tool Calls (this session only)
- SSH exec calls to GandalfAI: ~20
- SFTP write calls: 2
- SFTP read calls: 3
- Local file reads/edits: ~8
- ScheduleWakeup calls: 2
- Approximate tool calls total: ~35

### Iterations / Attempts
| Attempt | What ran | Outcome |
|---|---|---|
| 1 | Old script (pre-session, OWW Model) | Crash: speechbrain k2 ImportError |
| 2 | New script via `pythonw.exe` (PID 19424) | Log not updated — suspected stale .pyc or relaunch confusion |
| 3 | `py -3.11` direct (PID 15088) | Ran old script somehow — log shows old output |
| 4 | `py -3.11` direct (PID 16528) | _WakewordNet trained OK; ONNX export: onnxscript missing |
| 5 | After installing onnxscript — same process mid-run | ONNX export: ml_dtypes.float4_e2m1fn AttributeError |
| **6** | **Next run (not yet done)** | **Should succeed with manual ONNX export fix** |

### Token Estimate (approximate, cannot be measured precisely from within session)
Claude Code does not expose token counts or cost to the running agent. To get exact figures: check the Anthropic Console billing dashboard for 2026-04-25, filter by API key or project. The session involved two long conversations (context was compacted once), multiple large file reads, and one full-file SFTP write (~19 KB). Rough order-of-magnitude estimate for a 4–5 hour Claude Sonnet 4.6 session with this volume of tool use: **500K–1.5M tokens total** (input + output across both sessions). Actual cost visible only in Console.

### What Was Generated / Side Effects
- Installed on GandalfAI (Python 3.11): `onnxscript 0.7.0`, `ml_dtypes` upgraded from 0.3.1 → 0.5.4
- `tensorflow-intel 2.15.1` now has a dependency conflict with `ml_dtypes 0.5.4` (was 0.3.1). TFLite conversion will likely fail; `.onnx` output is sufficient for wyoming-openwakeword.
- 1660 WAV training samples generated in `C:\IRIS\wakeword_training\` on GandalfAI (~total disk use estimate: 500 WAV × ~64 KB + 660 WAV × ~32 KB ≈ ~50 MB)
- No Pi4 changes. No GitHub push. No IRIS config changes.

## Goal
Produce `C:\IRIS\wakewords\hey_der_iris.onnx` and `real_quick_iris.onnx` on GandalfAI (192.168.1.3, gandalf/5309, Windows/PowerShell). Both files must be >50 KB. Do not touch Pi4, `config.py`, `wakeword.py`, or `assistant.py`. Do not push to GitHub.

## Current State
- **All training samples are generated** (on GandalfAI):
  - `C:\IRIS\wakeword_training\hey_der_iris\positive\` → 500 WAV files
  - `C:\IRIS\wakeword_training\hey_der_iris\negative\` → 360 WAV files
  - `C:\IRIS\wakeword_training\real_quick_iris\positive\` → 500 WAV files
  - `C:\IRIS\wakeword_training\real_quick_iris\negative\` → 300 WAV files
- **Training (DNN) works**: Pure PyTorch `_WakewordNet` runs successfully to completion
- **ONNX export is broken** — this is the only remaining blocker
- **No ONNX output files yet** — `C:\IRIS\wakewords\` exists but is empty

## Script Location
- **Local (canonical)**: `scripts/train_wakewords.py` in IRIS repo on SuperMaster
- **Deployed**: `C:\IRIS\train_wakewords.py` on GandalfAI (may be slightly stale)
- **Log**: `C:\IRIS\train_wakewords.log` on GandalfAI

## Error Chain — Full History

### Error 1 (RESOLVED): speechbrain / k2 import crash
**Symptom**: `openwakeword.train.Model(...)` crashed because `torch.optim.Adam.__init__` triggers `torch._dynamo` import → `inspect.getmodule` iterates `sys.modules` → hits speechbrain `LazyModule(k2_fsa)` → `ImportError: Please install k2`

**Fix applied**: Replaced `openwakeword.train.Model` entirely with a self-contained `_WakewordNet` class (pure PyTorch `nn.Sequential`). The `_WakewordNet.train()` method uses the same `torch.optim.Adam` but in a fresh context without speechbrain in `sys.modules`, so the crash does not recur.

**Status**: RESOLVED — `_WakewordNet` trains to completion without crashing.

### Error 2 (CURRENT BLOCKER): `torch.onnx.export` fails — onnxscript/onnx/ml_dtypes conflict

**Symptom A** (first occurrence): `ModuleNotFoundError: No module named 'onnxscript'`  
`torch.onnx.export` in PyTorch 2.11.0 uses a new onnxscript-based exporter by default, which requires `onnxscript` to be installed.

**Fix applied**: Installed `onnxscript 0.7.0` via `py -3.11 -m pip install onnxscript`.

**Symptom B** (after onnxscript install): `AttributeError: module 'ml_dtypes' has no attribute 'float4_e2m1fn'`

Full traceback path:
```
torch.onnx.export()
  → torch.onnx._internal.exporter._compat
  → torch.onnx._internal.exporter._core  (imports onnxscript)
  → onnxscript.__init__
  → onnxscript.ir
  → onnx_ir.__init__
  → onnx_ir.convenience
  → onnx.__init__  ← onnx first loaded here
  → onnx.compose
  → onnx.helper
  → onnx._mapping  ← CRASH: ml_dtypes.float4_e2m1fn
```

`onnx 1.19.0` references `ml_dtypes.float4_e2m1fn` in `_mapping.py` line 104. But even though `ml_dtypes 0.5.4` is installed and HAS the attribute in a standalone test, importing fails in the training script context. Hypothesis: `onnxruntime` (imported by `openwakeword.utils.AudioFeatures`) imports `onnx` earlier and may cache a different state.

## Installed Package Versions (GandalfAI, Python 3.11)
- `torch`: 2.11.0+cpu
- `onnx`: 1.19.0
- `onnxscript`: 0.7.0
- `ml_dtypes`: 0.5.4
- `onnxruntime`: (version unknown — check with `py -3.11 -c "import onnxruntime; print(onnxruntime.__version__)"`)
- `tensorflow`: 2.15.1 (tensorflow-intel)

## Recommended Fix — Bypass torch.onnx.export Entirely

Instead of using `torch.onnx.export` (which chains through the broken onnxscript/onnx_ir/onnx import stack), export the ONNX model manually using the `onnx.helper` API. This calls `onnx` directly without going through `onnx_ir` or `onnxscript`.

The `_WakewordNet` architecture for `input_size=1536` (16×96):
```
Flatten → Linear(1536,128) → LayerNorm(128) → ReLU
        → Linear(128,128)  → LayerNorm(128) → ReLU
        → Linear(128,1) → Sigmoid
```

Weights are accessible from `net.state_dict()` after training. Key tensors:
```python
sd = net.state_dict()
# sd keys (Sequential with Flatten at index 0):
# 1.weight (128,1536), 1.bias (128,)        ← first Linear
# 2.weight (128,),     2.bias (128,)        ← first LayerNorm
# 4.weight (128,128),  4.bias (128,)        ← second Linear
# 5.weight (128,),     5.bias (128,)        ← second LayerNorm
# 7.weight (1,128),    7.bias (1,)          ← final Linear
```

Manual ONNX export snippet (replace `torch.onnx.export` call in `train_and_export()`):

```python
import onnx
from onnx import helper, TensorProto, numpy_helper
import numpy as np

def _export_onnx_manual(net, label, onnx_path, input_shape):
    """Export _WakewordNet to ONNX without torch.onnx.export."""
    sd = {k: v.detach().numpy() for k, v in net.state_dict().items()}

    # Map state_dict keys to layer names
    # Sequential: 0=Flatten, 1=Linear, 2=LayerNorm, 3=ReLU, 4=Linear, 5=LayerNorm, 6=ReLU, 7=Linear, 8=Sigmoid
    W1 = sd["1.weight"];  b1 = sd["1.bias"]
    LN1_w = sd["2.weight"]; LN1_b = sd["2.bias"]
    W2 = sd["4.weight"];  b2 = sd["4.bias"]
    LN2_w = sd["5.weight"]; LN2_b = sd["5.bias"]
    W3 = sd["7.weight"];  b3 = sd["7.bias"]

    def init(name, arr):
        return numpy_helper.from_array(arr.astype(np.float32), name=name)

    initializers = [
        init("W1", W1), init("b1", b1),
        init("LN1_w", LN1_w), init("LN1_b", LN1_b),
        init("W2", W2), init("b2", b2),
        init("LN2_w", LN2_w), init("LN2_b", LN2_b),
        init("W3", W3), init("b3", b3),
    ]

    flat_size = int(np.prod(input_shape))  # 1536

    nodes = [
        helper.make_node("Flatten", ["input_0"], ["flat"], axis=1),
        helper.make_node("Gemm", ["flat", "W1", "b1"], ["gemm1"], transB=1),
        helper.make_node("LayerNormalization", ["gemm1", "LN1_w", "LN1_b"], ["ln1"]),
        helper.make_node("Relu", ["ln1"], ["relu1"]),
        helper.make_node("Gemm", ["relu1", "W2", "b2"], ["gemm2"], transB=1),
        helper.make_node("LayerNormalization", ["gemm2", "LN2_w", "LN2_b"], ["ln2"]),
        helper.make_node("Relu", ["ln2"], ["relu2"]),
        helper.make_node("Gemm", ["relu2", "W3", "b3"], ["gemm3"], transB=1),
        helper.make_node("Sigmoid", ["gemm3"], [label]),
    ]

    inputs = [helper.make_tensor_value_info("input_0", TensorProto.FLOAT, [None, *input_shape])]
    outputs = [helper.make_tensor_value_info(label, TensorProto.FLOAT, [None, 1])]

    graph = helper.make_graph(nodes, label, inputs, outputs, initializers)
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 8
    onnx.checker.check_model(model)
    onnx.save(model, onnx_path)
```

In `train_and_export()`, replace the `torch.onnx.export(...)` block with:
```python
print(f"[EXPORT] Writing ONNX → {onnx_path}")
_export_onnx_manual(net, label, onnx_path, tuple(pos_feats.shape[1:]))
```

This calls `onnx` directly (not through `onnx_ir` or `onnxscript`), so the broken import chain is avoided.

## Alternative Quick Fix (if manual export is too complex)

Downgrade onnx to 1.16.1 (last version before the `float4_e2m1fn` dependency was added) AND pin onnxscript to a version that works with onnx 1.16:
```powershell
py -3.11 -m pip install "onnx==1.16.1" "onnxscript==0.1.0.dev20240108"
```
Risk: may reintroduce onnxscript import issues.

## Workflow to Complete After Fix

1. Deploy updated `train_wakewords.py` to `C:\IRIS\train_wakewords.py` on GandalfAI
2. Launch: `Start-Process -FilePath 'py' -ArgumentList '-3.11 C:\IRIS\train_wakewords.py' -WindowStyle Hidden`
3. Tail log: `Get-Content C:\IRIS\train_wakewords.log -Wait -Tail 20`
4. Confirm output: `Get-ChildItem C:\IRIS\wakewords *.onnx | Select-Object Name,Length` — both files must be >50 KB
5. No Pi4 deployment yet — verify models with `onnxruntime.InferenceSession` first

## Files Modified This Session (local repo, SuperMaster)
- `scripts/train_wakewords.py` — rewrote `train_and_export()`, added `_WakewordNet`, updated deps list, opset 18

## Files NOT to Touch
- `iris_config.json`, `alsa-init.sh`, `src/TeensyEyes.ino`, `src/eyes/EyeController.h`
- Pi4: nothing until DEPLOY instruction
- GitHub: no push until explicitly authorized

"""
train_wakewords.py v2 - IRIS Custom Wakeword Training Script
Uses OWW Python API directly (no external datasets or YAML config required).
Auto-relaunches under Python 3.11 for TensorFlow/tflite compatibility.

Output:
  C:\IRIS\wakewords\hey_der_iris.onnx  (+ .tflite if conversion succeeds)
  C:\IRIS\wakewords\real_quick_iris.onnx  (+ .tflite)
"""

import os
import sys

# Auto-relaunch under py -3.11 if running 3.12+ (tensorflow not available on 3.14)
if sys.version_info >= (3, 12):
    import subprocess
    print(f"[BOOT] Python {sys.version_info.major}.{sys.version_info.minor} detected.")
    print("[BOOT] Re-launching under Python 3.11 for TF compatibility...")
    r = subprocess.run(["py", "-3.11", __file__] + sys.argv[1:])
    sys.exit(r.returncode)

import json
import time
import socket
import wave
import pathlib
import subprocess
import numpy as np
from math import gcd


# ── Config ────────────────────────────────────────────────────────────────────

WAKEWORDS = {
    "hey_der_iris": {
        "phrase": "hey der iris",
        "negatives": [
            "hey", "hey there", "hey you", "hey iris", "iris",
            "dear iris", "hello iris", "hi iris", "hey siri",
            "hey alexa", "hay there iris", "der iris",
        ],
    },
    "real_quick_iris": {
        "phrase": "real quick iris",
        "negatives": [
            "real quick", "real", "iris", "real quickly",
            "really quick", "quick iris", "real quick question",
            "quick quick", "real fast iris", "real fast",
        ],
    },
}

PIPER_HOST     = "127.0.0.1"
PIPER_PORT     = 10200
PIPER_VOICE    = "en_US-lessac-medium"

OUTPUT_DIR     = r"C:\IRIS\wakewords"
WORK_DIR       = r"C:\IRIS\wakeword_training"
OWW_REPO       = r"C:\IRIS\openWakeWord"

POS_SAMPLES    = 500    # positive samples per wakeword
NEG_PER_PHRASE = 30     # negative samples per adversarial phrase
SPEED_VARIANTS = [0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15]
SAMPLE_RATE    = 16000
CLIP_SAMPLES   = 32000  # 2 seconds — OWW default training clip length
TRAIN_STEPS    = 5000   # per auto_train sequence (3 sequences internally)

# ── Wyoming Piper TTS (newline-delimited JSON, persistent connection) ─────────

_piper_sock = None


def _wy_send(sock, event_type, data=None):
    hdr = {"type": event_type, "version": "1.0.0"}
    data_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8") if data else None
    if data_bytes:
        hdr["data_length"] = len(data_bytes)
    out = json.dumps(hdr).encode() + b"\n"
    if data_bytes:
        out += data_bytes
    sock.sendall(out)


def _wy_readline(sock):
    line = b""
    while not line.endswith(b"\n"):
        c = sock.recv(1)
        if not c:
            raise ConnectionError("Piper socket closed")
        line += c
    return json.loads(line.decode())


def _wy_read(sock):
    hdr = _wy_readline(sock)
    data_len = hdr.get("data_length", 0)
    data = {}
    if data_len > 0:
        buf = b""
        while len(buf) < data_len:
            buf += sock.recv(data_len - len(buf))
        data = json.loads(buf)
    pay_len = hdr.get("payload_length", 0)
    payload = b""
    if pay_len > 0:
        while len(payload) < pay_len:
            payload += sock.recv(pay_len - len(payload))
    return hdr.get("type"), data, payload


def _piper_connect():
    global _piper_sock
    if _piper_sock is not None:
        try: _piper_sock.close()
        except Exception: pass
    _piper_sock = socket.create_connection((PIPER_HOST, PIPER_PORT), timeout=20)
    _piper_sock.settimeout(20)
    print(f"[PIPER] connected to {PIPER_HOST}:{PIPER_PORT}")


def synthesize_piper(text, speed=1.0):
    global _piper_sock
    from scipy.signal import resample_poly
    for attempt in range(3):
        try:
            if _piper_sock is None:
                _piper_connect()
            _wy_send(_piper_sock, "synthesize", {
                "text": text,
                "voice": {"name": PIPER_VOICE},
                "synthesize_options": {"length_scale": 1.0 / speed},
            })
            chunks = []
            src_rate = 22050
            while True:
                t, d, payload = _wy_read(_piper_sock)
                if t == "audio-start":
                    src_rate = d.get("rate", 22050)
                elif t == "audio-chunk":
                    chunks.append(payload)
                elif t == "audio-stop":
                    break
            raw = b"".join(chunks)
            if src_rate != SAMPLE_RATE:
                arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
                g = gcd(src_rate, SAMPLE_RATE)
                arr = resample_poly(arr, SAMPLE_RATE // g, src_rate // g)
                raw = arr.clip(-32768, 32767).astype(np.int16).tobytes()
            return raw
        except Exception as e:
            print(f"[PIPER] attempt {attempt+1} failed: {e} — reconnecting...")
            _piper_sock = None
            time.sleep(2)
    raise RuntimeError(f"Piper synthesis failed after 3 attempts for: {text!r}")


def pcm_to_wav(pcm, path):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm)


def load_wav_array(path):
    import wave as wv
    with wv.open(path, "rb") as wf:
        frames = wf.readframes(wf.getnframes())
    arr = np.frombuffer(frames, dtype=np.int16)  # OWW embed_clips requires int16 PCM
    if len(arr) < CLIP_SAMPLES:
        arr = np.pad(arr, (0, CLIP_SAMPLES - len(arr)))
    else:
        arr = arr[:CLIP_SAMPLES]
    return arr


# ── Setup ─────────────────────────────────────────────────────────────────────

def check_deps():
    import importlib
    required = [
        "torch", "torchinfo", "torchmetrics", "onnx", "onnxruntime", "onnxscript",
        "openwakeword", "pronouncing", "audiomentations", "torch_audiomentations",
        "speechbrain", "mutagen", "acoustics", "librosa", "torchaudio", "scipy",
    ]
    missing = [m for m in required if importlib.util.find_spec(m) is None]
    if missing:
        print(f"[WARN] Missing packages: {missing}")
        subprocess.run(f'"{sys.executable}" -m pip install -q ' + " ".join(missing), shell=True)
    else:
        print("[SETUP] All required packages present.")
    try:
        import openwakeword
        openwakeword.utils.download_models()
        print("[SETUP] OWW feature models present.")
    except Exception as e:
        print(f"[WARN] OWW model download: {e}")
    try:
        import tensorflow
        print(f"[SETUP] tensorflow {tensorflow.__version__} available (tflite conversion enabled)")
    except ImportError:
        print("[SETUP] tensorflow not found — tflite conversion will be skipped, .onnx only")


def check_piper_up():
    try:
        s = socket.create_connection((PIPER_HOST, PIPER_PORT), timeout=3)
        s.close()
        print(f"[CHECK] Piper reachable on {PIPER_HOST}:{PIPER_PORT}")
        return True
    except Exception:
        print(f"[ERROR] Piper NOT reachable on {PIPER_HOST}:{PIPER_PORT}")
        return False


# ── Sample generation ─────────────────────────────────────────────────────────

def generate_positives(phrase, label, work_dir, n=POS_SAMPLES):
    pos_dir = os.path.join(work_dir, "positive")
    os.makedirs(pos_dir, exist_ok=True)
    existing = len(list(pathlib.Path(pos_dir).glob("*.wav")))
    if existing >= n:
        print(f"[GEN]  {existing} positive samples already exist, skipping.")
        return pos_dir

    print(f"[GEN]  Generating {n} positive samples for '{phrase}'...")
    count = existing
    errors = 0
    per_speed = max(1, n // len(SPEED_VARIANTS))

    for speed in SPEED_VARIANTS:
        for _ in range(per_speed):
            if count >= n:
                break
            try:
                pcm = synthesize_piper(phrase, speed=speed)
                pcm_to_wav(pcm, os.path.join(pos_dir, f"{label}_{count:04d}_s{int(speed*100)}.wav"))
                count += 1
                if count % 50 == 0:
                    print(f"  {count}/{n} positive samples")
            except Exception as e:
                errors += 1
                print(f"  [WARN] pos {count} {e}")
                if errors > 50:
                    raise RuntimeError("Too many TTS errors generating positives")
                time.sleep(1.0)

    print(f"[GEN]  {count} positive samples ({errors} errors)")
    return pos_dir


def generate_negatives(neg_phrases, label, work_dir):
    neg_dir = os.path.join(work_dir, "negative")
    os.makedirs(neg_dir, exist_ok=True)
    target = len(neg_phrases) * NEG_PER_PHRASE
    existing = len(list(pathlib.Path(neg_dir).glob("*.wav")))
    if existing >= target:
        print(f"[GEN]  {existing} negative samples already exist, skipping.")
        return neg_dir

    print(f"[GEN]  Generating negatives ({len(neg_phrases)} phrases × {NEG_PER_PHRASE})...")
    count = existing
    errors = 0

    for pi, phrase in enumerate(neg_phrases):
        for i in range(NEG_PER_PHRASE):
            speed = SPEED_VARIANTS[i % len(SPEED_VARIANTS)]
            try:
                pcm = synthesize_piper(phrase, speed=speed)
                pcm_to_wav(pcm, os.path.join(neg_dir, f"{label}_neg_{pi:02d}_{i:03d}.wav"))
                count += 1
                if count % 60 == 0:
                    print(f"  {count}/{target} negative samples")
            except Exception as e:
                errors += 1
                print(f"  [WARN] neg {pi}_{i} {e}")
                if errors > 50:
                    raise RuntimeError("Too many TTS errors generating negatives")
                time.sleep(1.0)

    print(f"[GEN]  {count} negative samples ({errors} errors)")
    return neg_dir


# ── Cyclic DataLoader wrapper ─────────────────────────────────────────────────

class CyclicLoader:
    """Wraps a DataLoader so it cycles indefinitely (needed for multi-epoch OWW training)."""
    def __init__(self, dl):
        self.dl = dl
        self._it = iter(dl)

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return next(self._it)
        except StopIteration:
            self._it = iter(self.dl)
            return next(self._it)


# ── Pure-PyTorch wakeword DNN ─────────────────────────────────────────────────

class _WakewordNet:
    """Minimal DNN that replicates OWW's Model without the speechbrain dependency."""

    def __init__(self, input_size):
        import torch
        import torch.nn as nn
        self.model = nn.Sequential(
            nn.Flatten(),
            nn.Linear(input_size, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid(),
        )

    def train(self, X_tr, y_tr, X_va, y_va, steps):
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset

        device = torch.device("cpu")
        net = self.model.to(device)
        opt = torch.optim.Adam(net.parameters(), lr=1e-3)
        bce = nn.BCELoss()

        bs = min(64, max(1, len(X_tr)))
        dl = CyclicLoader(DataLoader(TensorDataset(X_tr, y_tr), batch_size=bs, shuffle=True))

        best_val = float("inf")
        best_state = None

        net.train()
        for step, (xb, yb) in enumerate(dl):
            if step >= steps:
                break
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            pred = net(xb).squeeze(1)
            loss = bce(pred, yb)
            loss.backward()
            opt.step()

            if (step + 1) % 500 == 0:
                net.eval()
                with torch.no_grad():
                    val_pred = net(X_va.to(device)).squeeze(1)
                    val_loss = bce(val_pred, y_va.to(device)).item()
                if val_loss < best_val:
                    best_val = val_loss
                    best_state = {k: v.clone() for k, v in net.state_dict().items()}
                print(f"  step {step+1}/{steps}  val_loss={val_loss:.4f}  best={best_val:.4f}")
                net.train()

        if best_state is not None:
            net.load_state_dict(best_state)
        net.eval()
        return net


# ── Manual ONNX export (bypasses torch.onnx.export / onnxscript / onnx_ir) ────

def _export_onnx_manual(net, label, onnx_path, input_shape):
    """Export _WakewordNet to ONNX using onnx.helper directly.

    Avoids torch.onnx.export which chains through onnxscript -> onnx_ir -> onnx,
    triggering the ml_dtypes.float4_e2m1fn AttributeError on GandalfAI.
    Calls onnx.helper directly instead.
    """
    import onnx
    from onnx import helper, TensorProto, numpy_helper
    import numpy as np

    sd = {k: v.detach().numpy() for k, v in net.state_dict().items()}

    # Sequential layout:
    # 0=Flatten, 1=Linear(1536,128), 2=LayerNorm(128), 3=ReLU,
    # 4=Linear(128,128), 5=LayerNorm(128), 6=ReLU, 7=Linear(128,1), 8=Sigmoid
    W1    = sd["1.weight"];  b1    = sd["1.bias"]
    LN1_w = sd["2.weight"];  LN1_b = sd["2.bias"]
    W2    = sd["4.weight"];  b2    = sd["4.bias"]
    LN2_w = sd["5.weight"];  LN2_b = sd["5.bias"]
    W3    = sd["7.weight"];  b3    = sd["7.bias"]

    def init(name, arr):
        return numpy_helper.from_array(arr.astype(np.float32), name=name)

    initializers = [
        init("W1", W1), init("b1", b1),
        init("LN1_w", LN1_w), init("LN1_b", LN1_b),
        init("W2", W2), init("b2", b2),
        init("LN2_w", LN2_w), init("LN2_b", LN2_b),
        init("W3", W3), init("b3", b3),
    ]

    nodes = [
        helper.make_node("Flatten",            ["input_0"],           ["flat"],  axis=1),
        helper.make_node("Gemm",               ["flat",  "W1",  "b1"],  ["gemm1"], transB=1),
        helper.make_node("LayerNormalization", ["gemm1", "LN1_w", "LN1_b"], ["ln1"]),
        helper.make_node("Relu",               ["ln1"],               ["relu1"]),
        helper.make_node("Gemm",               ["relu1", "W2",  "b2"],  ["gemm2"], transB=1),
        helper.make_node("LayerNormalization", ["gemm2", "LN2_w", "LN2_b"], ["ln2"]),
        helper.make_node("Relu",               ["ln2"],               ["relu2"]),
        helper.make_node("Gemm",               ["relu2", "W3",  "b3"],  ["gemm3"], transB=1),
        helper.make_node("Sigmoid",            ["gemm3"],             [label]),
    ]

    inputs  = [helper.make_tensor_value_info("input_0", TensorProto.FLOAT, [None, *input_shape])]
    outputs = [helper.make_tensor_value_info(label,     TensorProto.FLOAT, [None, 1])]

    graph = helper.make_graph(nodes, label, inputs, outputs, initializers)
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 8
    onnx.checker.check_model(model)
    onnx.save(model, onnx_path)


# ── Training & export ─────────────────────────────────────────────────────────

def train_and_export(label, pos_dir, neg_dir, output_dir):
    import torch
    from openwakeword.utils import AudioFeatures

    # Load WAV files
    pos_wavs = sorted(pathlib.Path(pos_dir).glob("*.wav"))
    neg_wavs = sorted(pathlib.Path(neg_dir).glob("*.wav"))
    print(f"[TRAIN] {len(pos_wavs)} positive, {len(neg_wavs)} negative clips")

    pos_clips = np.array([load_wav_array(str(p)) for p in pos_wavs])  # (N, 32000) int16
    neg_clips = np.array([load_wav_array(str(p)) for p in neg_wavs])

    print("[TRAIN] Computing OWW features via AudioFeatures (onnx)...")
    AF = AudioFeatures(inference_framework="onnx", device="cpu")

    pos_feats = AF.embed_clips(pos_clips)   # (N, frames, 96)
    neg_feats = AF.embed_clips(neg_clips)
    print(f"[TRAIN] Feature shapes: pos={pos_feats.shape}, neg={neg_feats.shape}")

    input_size = int(np.prod(pos_feats.shape[1:]))  # e.g. 16*96 = 1536

    # Labels and shuffle
    pos_labels = np.ones(len(pos_feats), dtype=np.float32)
    neg_labels = np.zeros(len(neg_feats), dtype=np.float32)
    all_feats  = np.vstack([pos_feats, neg_feats]).astype(np.float32)
    all_labels = np.hstack([pos_labels, neg_labels])

    idx   = np.random.permutation(len(all_feats))
    split = int(len(idx) * 0.8)
    tr, va = idx[:split], idx[split:]

    X_tr = torch.from_numpy(all_feats[tr]);  y_tr = torch.from_numpy(all_labels[tr])
    X_va = torch.from_numpy(all_feats[va]);  y_va = torch.from_numpy(all_labels[va])

    # Train pure-PyTorch model
    print(f"[TRAIN] Pure-PyTorch DNN  input_size={input_size}  steps={TRAIN_STEPS}...")
    net_wrapper = _WakewordNet(input_size)
    net = net_wrapper.train(X_tr, y_tr, X_va, y_va, TRAIN_STEPS)

    # Export ONNX
    onnx_path   = os.path.join(output_dir, f"{label}.onnx")
    tflite_path = os.path.join(output_dir, f"{label}.tflite")

    print(f"[EXPORT] Writing ONNX → {onnx_path}")
    _export_onnx_manual(net, label, onnx_path, tuple(pos_feats.shape[1:]))

    if not os.path.isfile(onnx_path):
        raise FileNotFoundError(f"ONNX export did not produce {onnx_path}")

    onnx_kb = os.path.getsize(onnx_path) // 1024
    print(f"[EXPORT] ONNX: {onnx_kb} KB")

    # Convert ONNX → TFLite (best-effort; does not import openwakeword.train.Model)
    print("[EXPORT] Attempting ONNX → TFLite conversion...")
    try:
        from openwakeword.train import convert_onnx_to_tflite
        convert_onnx_to_tflite(onnx_path, tflite_path)
        tflite_kb = os.path.getsize(tflite_path) // 1024
        print(f"[EXPORT] TFLite: {tflite_kb} KB → {tflite_path}")
    except Exception as e:
        print(f"[WARN] TFLite conversion failed: {e}")
        print("[INFO] ONNX model is usable with wyoming-openwakeword directly")
        tflite_path = None

    return onnx_path, tflite_path


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print(f"IRIS Wakeword Training Script v2  (Python {sys.version.split()[0]})")
    print(f"Phrases: {[v['phrase'] for v in WAKEWORDS.values()]}")
    print("=" * 60)

    if not check_piper_up():
        sys.exit(1)
    _piper_connect()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(WORK_DIR, exist_ok=True)

    check_deps()

    results = {}
    for label, cfg in WAKEWORDS.items():
        print(f"\n{'='*60}\nProcessing: {label} = '{cfg['phrase']}'\n{'='*60}")
        work = os.path.join(WORK_DIR, label)
        os.makedirs(work, exist_ok=True)

        pos_dir = generate_positives(cfg["phrase"], label, work)
        neg_dir = generate_negatives(cfg["negatives"], label, work)

        try:
            onnx_path, tflite_path = train_and_export(label, pos_dir, neg_dir, OUTPUT_DIR)
            results[label] = {"status": "OK", "onnx": onnx_path, "tflite": tflite_path}
        except Exception as e:
            import traceback
            print(f"[ERROR] {label}: {e}")
            traceback.print_exc()
            results[label] = {"status": "FAILED", "error": str(e)}

    print(f"\n{'='*60}\nTRAINING COMPLETE\n{'='*60}")
    all_ok = True
    for label, r in results.items():
        if r["status"] == "OK":
            tflite_str = r["tflite"] or "N/A (use .onnx)"
            print(f"  OK  {label}")
            print(f"      onnx   -> {r['onnx']}")
            print(f"      tflite -> {tflite_str}")
        else:
            print(f"  FAIL {label}: {r.get('error', '?')}")
            all_ok = False

    if all_ok:
        print(f"\nDeploy to Pi4:")
        print(f"  scp {OUTPUT_DIR}\\*.onnx pi@192.168.1.200:/home/pi/wyoming-openwakeword/custom/")
    else:
        sys.exit(1)


if __name__ == "__main__":
    # Self-log to file regardless of how the process was launched (Start-Process, schtasks, etc.)
    # Tee output to both original stdout/stderr AND the log file so interactive runs still print.
    import atexit

    _log_path = r"C:\IRIS\train_wakewords.log"
    _log = open(_log_path, "w", buffering=1, encoding="utf-8")
    atexit.register(_log.close)

    class _Tee:
        def __init__(self, *streams):
            self._streams = streams
        def write(self, data):
            for s in self._streams:
                try:
                    s.write(data)
                except Exception:
                    pass
        def flush(self):
            for s in self._streams:
                try:
                    s.flush()
                except Exception:
                    pass
        def fileno(self):
            return self._streams[0].fileno()

    sys.stdout = _Tee(sys.stdout, _log)
    sys.stderr = _Tee(sys.stderr, _log)

    main()

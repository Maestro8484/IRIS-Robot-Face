# Handoff — Vision Latency Fix (target: ~29 s → under ~8 s)

> **SUPERSEDED by S119b.** The root cause (num_ctx mismatch forcing Ollama reload on text↔vision switch) was resolved in S119b by raising iris/iris-kids modelfile num_ctx to 6144 unified. Vision cold-after-text is now 2.4s (was 29s). This document is kept as historical reference only.

**Created:** S118 (2026-06-09). **For:** next session. **Recommended model:** **Opus** (see "Why Opus" at the end).

---

## Problem

The vision path ("describe what you see" — web UI button AND voice "what do you see") works as of S118 but takes **~29 s** per request. That is far too slow for a conversational robot. Make it **way faster** (target under ~8 s, ideally ~5–7 s).

## Root cause (already diagnosed S118 — do NOT re-litigate, verify and act)

It is **NOT** inference speed and **NOT** the reply being long (the reply is ~60 tokens). It is an **Ollama model RELOAD** caused by a `num_ctx` mismatch:

- Text queries (`stream_ollama`, `ask_ollama`, warmup) use the model's default context = **4096**.
- A camera frame encodes to **~4570 vision tokens**, which overflows 4096 → HTTP 400. S118 fixed the 400 by sending `options.num_ctx=6144` on the vision call only.
- But because vision asks for **6144** while the resident instance is loaded at **4096**, Ollama **reloads iris** for the vision call (and reloads back to 4096 on the next text query). Each reload is ~10–15 s.

**Evidence (S118 probes, RTX 3090, Ollama 0.30.7, iris=qwen3.5:27b):**
- 512×384 image at default 4096 ctx (NO reload): **3.4 s** total inference (but only ~100 ctx tokens left for the reply — too tight).
- Same image forcing `num_ctx=6144` (RELOAD): **15.7 s**.
- `num_ctx=8192` (RELOAD): **17.5 s**.
- Full web `/api/vision` (camera + reload + inference): **28.8 s**.
- Vision token counts barely move with resolution: 512×384=3994, 640×480=4102, 768×576=4234, 1024×768=4570. So you CANNOT fit a real image + a usable reply inside 4096 — you must run at ctx > 4096, which means the resident instance must ALSO be at that ctx to avoid reloads.

**Conclusion:** make text and vision share ONE context size so iris stays resident at a single ctx and vision needs no reload. Then vision ≈ camera (~2 s) + inference (~3–5 s) ≈ **5–7 s**.

---

## Fix — two options. Recommend Option 1; fall back to Option 2.

### Option 1 (RECOMMENDED, cleanest): raise the modelfile `num_ctx` to 6144 and rebuild

One change, applies to every caller automatically, no per-call `num_ctx` needed, no reloads ever.

1. On the **local repo**, edit `ollama/iris_modelfile.txt` and `ollama/iris-kids_modelfile.txt`:
   - Check whether a `PARAMETER num_ctx ...` line already exists. If yes, set it to `6144`. If no, add `PARAMETER num_ctx 6144`.
   - (qwen3.5/0.30.7 supports `PARAMETER num_ctx`. This is unlike `PARAMETER think false`, which 0.30.7 rejected at S114 — don't confuse the two.)
2. This is a **GandalfAI model rebuild = explicit DEPLOY gate**. With user authorization: `git pull` on GandalfAI clone (`C:\IRIS\IRIS-Robot-Face\`), then `ollama create iris` and `ollama create iris-kids`. See `[[project_gandalf_modelfile_sync]]` and `[[project_gandalf_ssh_longops]]` (run long ollama ops detached + poll a result file; GandalfAI ssh = cmd.exe).
3. **VRAM CHECK (critical — ~1 GB headroom concern):** after rebuild + a warmup query, run `ollama ps` (shows SIZE and whether it's 100% GPU or spilled to CPU) and `nvidia-smi`. iris ~17–21 GB + Kokoro must fit in 24 GB at 6144 ctx. If `ollama ps` shows any CPU offload (e.g., "55%/45% CPU/GPU") or `nvidia-smi` is near 24 GB, the ctx is too big → back off to **5120**, re-test. If even 5120 spills, use Option 2 with the smallest ctx that fits a 4570-token image + ~200 reply (≈5120) and accept that text uses that ctx too.
4. After rebuild, the S118 per-request `num_ctx` in `services/vision.py` / `iris_web.py` becomes harmless (request ctx == model ctx → no reload). You may leave it or remove it; leaving it is safer (explicit).

### Option 2 (fallback, Pi4-only, no GandalfAI rebuild): make ALL Pi4 callers pass the same `num_ctx`

Set `options.num_ctx = 6144` on EVERY iris Ollama call so the model loads once at 6144 and stays. Miss one and it reloads — so all of these must match:
- `pi4/services/llm.py` → `stream_ollama()` payload (`/api/chat`)
- `pi4/assistant.py` → `ask_ollama()` payload (`/api/chat`) AND the warmup `/api/generate` call
- `pi4/iris_post.py` → l3_llm POST `/api/generate`
- `pi4/services/vision.py` → already 6144 (S118)
- `pi4/iris_web.py` → `api_vision` already 6144 (S118); `api_chat` `/api/generate` should match too
Cleanest as a single config constant, e.g. `OLLAMA_NUM_CTX = 6144` in `core/config.py` (add to `_OVERRIDABLE` + `_TYPE_COERCE` with range like (2048, 16384)), referenced everywhere. Same VRAM check as Option 1 applies (text now also runs at 6144).

### Complementary (either option): keep iris warm
Ollama unloads after `keep_alive` (default 5 min) → a cold load on the next vision call. If vision is used intermittently, pass `"keep_alive": "30m"` (or `-1` to pin) on the warmup and/or vision call so iris stays resident. Verify it doesn't starve Kokoro VRAM.

### Optional extra trim
Lowering `CAMERA_WIDTH/HEIGHT` (currently 1024×768) to **640×480** cuts vision tokens ~4570→~4102 and shaves a little encode time, at some quality cost. Test whether description quality is still acceptable; if so it buys a bit more headroom/speed. Not required if Option 1 hits the target.

---

## Verification (must do before claiming fixed)

1. After deploy, confirm iris is resident at the new ctx with NO reload between a text query and a vision query: run a text query, then a vision query back-to-back, and confirm timing is steady (no ~10 s jump). `ollama ps` should show one iris instance the whole time.
2. End-to-end: `curl -s -m 60 -w "HTTP %{http_code} %{time_total}s\n" -X POST http://127.0.0.1:5000/api/vision -H "Content-Type: application/json" -d '{"prompt":"Describe what you see.","speak":false}'` — expect **HTTP 200 in well under ~8 s** with a real description.
3. Confirm normal TEXT replies still work and did not regress (latency, correctness) at the new ctx.
4. `ollama ps` + `nvidia-smi` show 100% GPU, no CPU spill, with Kokoro also loaded.

## Deploy checklist (Pi4 files)
RAM write + SD persist (`/media/root-ro`) + md5 RAM=SD + restart affected services (`iris-web` and/or `assistant`) + log check. GandalfAI rebuild (Option 1) is a separate DEPLOY gate.

## Rollback
- Option 1: `git checkout HEAD~1 -- ollama/iris_modelfile.txt ollama/iris-kids_modelfile.txt`, re-`ollama create` both on GandalfAI. (S118 per-request num_ctx keeps vision working meanwhile.)
- Option 2: `git checkout -- <the Pi4 files touched>`, redeploy, restart.
Current good state to return to: commit `a6fc377` (S118), vision working at ~29 s.

## Baseline md5 (S118, for reference)
- `pi4/services/vision.py` = `1e5500958db39e888db4bb4294150b9d`
- `pi4/iris_web.py` = `9f7af3a6d023edd794cb067abdff3871`

---

## Why Opus (not Sonnet)
This is not a mechanical edit. It needs: (a) a VRAM/architecture judgment under a tight ~1 GB headroom (decide 6144 vs 5120, detect and recover from CPU offload), (b) a GandalfAI model rebuild on a setup that has bitten this project before (S113 GPU-offload failure, S114 `think false` modelfile rejection, Ollama pinned at 0.30.7), and (c) a cross-module `num_ctx` consistency contract if Option 2 is used. Opus is the safer choice for the judgment + recovery. Sonnet could execute it ONLY if you commit to Option 1 exactly as written and treat the VRAM check as a hard gate (back off to 5120 / abort on any CPU spill) — but the recovery paths favor Opus.

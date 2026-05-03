# IRIS TTS Evolution

## Phase 1 — Piper (baseline)

Local, CPU-only Wyoming-compatible service. Runs on GandalfAI via Docker (port 10200).
Voice: `en_US-ryan-high`.
Quality: robotic but intelligible. Zero VRAM cost. Acceptable as fallback only.
Status: **ACTIVE as fallback.** Always in the chain behind Kokoro.

---

## Phase 2 — ElevenLabs (cloud)

Switched for voice quality. "Snarky James Bond" preset voice (Daniel legacy, voice ID `90eMKEeSf5nhJZMJeeVZ`).
Quality: excellent. Latency: ~800ms round trip to cloud.
Problem: paid credits on a monthly cap. Cap was exhausted repeatedly during active development.
Removed: ~S20. No code references remain. API key revoked.
Status: **REMOVED.**

---

## Phase 3 — Chatterbox TTS (local clone)

Switched to keep quality high without cloud dependency.
Ran as Docker container on GandalfAI port 8004. VRAM cost: ~7.5GB.
Voice: cloned from `iris_voice.wav` reference audio.
Quality: good — natural-sounding clone. Problem: VRAM contention with gemma3:27b-it-qat (~16.8GB combined ~24.3GB on a 24GB card). Caused inference stalls and marginal stability.
Removed: S38. Restore script kept at `scripts/restore_chatterbox.ps1`.
Status: **REMOVED.** Config keys retained in `config.py` as rollback scaffolding only.

---

## Phase 4 — Kokoro (current)

Switched for low VRAM footprint (~1–2GB), freeing headroom for Ollama.
Runs as Docker container on GandalfAI port 8004 (same port as Chatterbox was).
Voice: `bm_lewis` (primary British male preset). Blend fallback: `bm_lewis:0.7+bm_george:0.3`.
Quality: solid and consistent. Not clone-based — preset voice, no reference audio needed.
Status: **ACTIVE, primary TTS.**

---

## Fallback Chain (always active)

```
Kokoro (GandalfAI:8004) → Piper (GandalfAI Wyoming:10200)
```

If Kokoro is unavailable (container down, GandalfAI offline), `services/tts.py` falls through to Wyoming Piper automatically.

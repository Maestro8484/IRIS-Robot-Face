# IRIS Ollama Modelfiles

Modelfiles for the two IRIS Ollama personas. Both run on GandalfAI (192.168.1.3) only.
Not tracked by PlatformIO. The local repo (`ollama/`) is the source of truth — GandalfAI's
live models are built from these files.

## Files

| File | Model name | Mode | Base model |
|---|---|---|---|
| `iris_modelfile.txt` | `iris` | Adult (default) | gemma3:27b-it-qat |
| `iris-kids_modelfile.txt` | `iris-kids` | Kids mode | gemma3:27b-it-qat |

## Rebuild (run on GandalfAI)

After editing a modelfile locally, copy to GandalfAI and rebuild:

```powershell
# Copy from SuperMaster to GandalfAI (or edit in place on GandalfAI)
# Then on GandalfAI:
ollama create iris -f "C:\Users\gandalf\iris_modelfile.txt"
ollama create iris-kids -f "C:\Users\gandalf\iris-kids_modelfile.txt"
```

Verify after rebuild:
```powershell
ollama list
ollama run iris "say hello briefly"
```

## Sync check

The live GandalfAI modelfiles live at `C:\Users\gandalf\iris_modelfile.txt` and
`C:\Users\gandalf\iris-kids_modelfile.txt`. Keep these in sync with this directory.
When editing via Claude, always write the local repo copy first, then deploy to GandalfAI
with explicit `DEPLOY` authorization.

## VRAM notes

- gemma3:27b-it-qat: ~14.1GB VRAM
- Kokoro TTS (Docker): ~1–2GB VRAM
- Combined: ~16GB on RTX 3090 (24GB). Headroom ~8GB.
- Required GandalfAI env (set machine-level, S39): `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`
- Do not raise `num_ctx` above 4096.

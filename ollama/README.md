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

After editing a modelfile locally and pushing to GitHub, rebuild on GandalfAI:

```powershell
# On GandalfAI — pull repo then rebuild from it
cd C:\IRIS\IRIS-Robot-Face
git pull origin main
ollama create iris -f "C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt"
ollama create iris-kids -f "C:\IRIS\IRIS-Robot-Face\ollama\iris-kids_modelfile.txt"
```

Verify after rebuild:
```powershell
ollama list
ollama run iris "say hello briefly"
```

## Sync check

GandalfAI has the repo cloned at `C:\IRIS\IRIS-Robot-Face\`. Modelfiles are at
`C:\IRIS\IRIS-Robot-Face\ollama\`. After a push from SuperMaster, run `git pull` on
GandalfAI and then `ollama create` from the repo clone. No manual file copying needed.
Always write the local repo copy first, then deploy to GandalfAI with explicit `DEPLOY` authorization.

## VRAM notes

- gemma3:27b-it-qat: ~14.1GB VRAM
- Kokoro TTS (Docker): ~1–2GB VRAM
- Combined: ~16GB on RTX 3090 (24GB). Headroom ~8GB.
- Required GandalfAI env (set machine-level, S39): `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`
- Do not raise `num_ctx` above 4096.

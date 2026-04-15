# IRIS Task A — Model Swap + num_ctx Reduction
**Prepared:** 2026-04-15
**Depends on:** None (do first, before Task B)
**Machine:** GandalfAI ONLY. No Pi4 SSH. No repo file changes.

---

## PRE-FLIGHT (output before touching anything)

```
Branch:             main  (git branch --show-current MUST output "main")
Last commit:        [hash + message]
Working tree:       [must be clean — if dirty STOP]
Task this session:  Swap Ollama base model from gemma3:27b-it-qat to mistral-small3.2:24b,
                    reduce num_ctx 8192->4096, update stop token in both modelfiles.
Files to modify:    C:\IRIS\ollama\jarvis_modelfile.txt
                    C:\IRIS\ollama\jarvis-kids_modelfile.txt
Files NOT touched:  pi4/ (any file), src/ (any file), CLAUDE.md, iris_config.json,
                    alsa-init.sh, SNAPSHOT_LATEST.md (until /snapshot at session end)
Risk:               Personality drift on new model. May need modelfile tuning after first live test.
Rollback:           Restore FROM gemma3:27b-it-qat, num_ctx 8192, stop <end_of_turn> in both
                    modelfiles. ollama create jarvis + ollama create jarvis-kids. No Pi4 changes.
```

Do not proceed until user confirms.

---

## WHY

VRAM saturation is the root cause of 30-second wakeword-to-audio latency.
`gemma3:27b-it-qat` (~17GB) + Chatterbox (~4.5GB) = ~21.5GB on a 24GB card.
KV cache at `num_ctx 8192` stalls under memory pressure.
`mistral-small3.2:24b` runs ~13GB, freeing ~4-5GB headroom.
Fix this before Task B so streaming tests run against the correct model.

---

## STEP 1 — Pull model and check architecture

```powershell
ollama pull mistral-small3.2:24b
ollama show mistral-small3.2:24b
```

Read `Model architecture` from the output:
- If `llama` → use `FROM mistral-small3.2:24b`
- If `mistral3` → use the Bartowski HF GGUF instead (avoids known 3-4x speed regression):
  ```powershell
  ollama pull hf.co/bartowski/Mistral-Small-3.2-24B-Instruct-2506-GGUF:Q4_K_M
  ```
  Use the HF tag as the FROM line in that case.

---

## STEP 2 — Edit `C:\IRIS\ollama\jarvis_modelfile.txt`

Read the file first via filesystem MCP (C:\IRIS\ is now in scope).

Three targeted changes only:
- Line 1: `FROM gemma3:27b-it-qat` → `FROM mistral-small3.2:24b` (or HF tag)
- `PARAMETER num_ctx 8192` → `PARAMETER num_ctx 4096`
- `PARAMETER stop <end_of_turn>` → `PARAMETER stop </s>`

All other content (SYSTEM block, all other PARAMETER lines) unchanged.

---

## STEP 3 — Edit `C:\IRIS\ollama\jarvis-kids_modelfile.txt`

Same three changes. All other content unchanged.

---

## STEP 4 — Rebuild both models

```powershell
ollama create jarvis -f C:\IRIS\ollama\jarvis_modelfile.txt
ollama create jarvis-kids -f C:\IRIS\ollama\jarvis-kids_modelfile.txt
```

Note the layer sha from each `success` line — record in snapshot.

---

## STEP 5 — Smoke test

```powershell
curl -s http://localhost:11434/api/chat -d '{\"model\":\"jarvis\",\"messages\":[{\"role\":\"user\",\"content\":\"hello\"}],\"stream\":false}' | findstr "content"
```

Confirm:
- Response contains `[EMOTION:` tag
- Plain spoken reply, no markdown, no bullet points
- Response arrives in < 5 seconds

---

## STEP 6 — Optional KV cache VRAM reduction

Run only if `nvidia-smi` shows > 22GB VRAM used after model load:

```powershell
[System.Environment]::SetEnvironmentVariable("OLLAMA_KV_CACHE_TYPE", "q8_0", "Machine")
```

Restart Ollama service after setting.

---

## SESSION END

**This task has NO git commit** — modelfiles live in `C:\IRIS\ollama\` outside the repo.

State what changed, what did NOT change, any personality drift observed.

Run `/snapshot`. Update these snapshot sections:
- **Section 2 — GANDALFAI FILE LAYOUT:** Update ollama entries to new model name and new layer sha values.
- **Section 8 — OLLAMA MODELS:** Base model → `mistral-small3.2:24b`, num_ctx → 4096, new layer sha.
- **Section 14 — CHANGES THIS SESSION:** Document Task A completion and smoke test result.
- **Section 15 — PENDING HIGH:** Add if personality drift observed: "Mistral Small 3.2 personality tuning — observe first 3-5 live interactions, tune modelfile if Jarvis persona drifts."

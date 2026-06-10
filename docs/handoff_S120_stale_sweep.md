# Handoff — S120: Repo + ecosystem stale-reference sweep

**Created:** S119 (2026-06-09). **Type:** documentation/comment accuracy sweep — no behavior change intended.
**Advised model/effort:** **Sonnet 4.6, medium effort** for the doc/markdown edits (mechanical, accuracy-critical, low reasoning). **Switch to Opus** only for the WebUI + Pi4 `think:False` code portion, because that touches a live Pi4 deploy surface (deploy + `/media/root-ro` persist + md5 + restart + verify).

## Ground truth as of S119/S119b (do not contradict)
- iris + iris-kids LLM base = **mistral-small3.2:24b** (arch `mistral3`, dense, Pixtral vision baked in). NOT qwen2.5vl, qwen3.5, gemma3, or qwen2.5:32b — those are all PRIOR/dead bases.
- Stop set: `[INST]`, `[/INST]`, `</s>`, `User:`. (NOT `<|im_end|>` / `<end_of_turn>`.)
- `num_ctx 6144` (unified text+vision, S119b). VRAM: 15GB @ 6144 + Kokoro 2GB = 17/24 GB, 100% GPU.
- Mistral has **no thinking mode** — `think:False` is dead weight (silently ignored), not required.
- Ollama 0.30.7. Pi4 `services/llm.py` md5 = `911261166ce7aeed07a8e3ef1a2d044e` (think:False already removed there).

## Scope — fix these (LIVE docs/comments still referencing dead models)
Run `grep -rin -E 'qwen|gemma|end_of_turn|im_end|<end_of_turn>' <repo>` and reconcile each to ground truth. Known target files (S119 inventory):
- `IRIS_ARCH.md` (~14 hits) — VRAM baseline, model base, stop tokens, vision notes. Highest priority.
- `docs/sysmap.json` — partially done S119 (ollama model_base/stop_token, num_ctx limit). Re-scan for any remaining gemma3/qwen vram fields (`gemma3_27b_gb`, `baseline_used_gb`).
- `docs/IRIS_INVENTORY.md`, `ollama/README.md`, `README.md`, `ROADMAP.md`, `docs/IRIS_SYSMAP_GUIDE.html`, `docs/bench_audit_S105.md`.
- `tools/iris_dashboard/app.py`, `tools/persona_harness/run_harness.py`, `tools/workbench/*` — any hardcoded model strings / fallback labels (e.g. `"iris (qwen...)"`).
- **WebUI** (`pi4/iris_web.html`, `pi4/iris_web.py`) — any "Gemma"/"qwen" UI text or model labels. NOTE: editing these = Pi4 deploy + persist + verify. `iris_web.html` had 0 grep hits (S102 already fixed "Gemma"→"Vision Model"); confirm.

## Code portion (deferred from S119, functionally harmless)
Remove `think:False` from the 4 remaining Pi4 Ollama callers (Mistral has no thinking mode) + fix their stale qwen comments:
- `pi4/assistant.py` (ask_ollama + warmup), `pi4/services/vision.py` (ask_vision), `pi4/iris_web.py` (api_vision), `pi4/iris_post.py` (l3_llm test).
- vision.py / iris_web.py: KEEP `num_ctx 6144` (still needed for image tokens; now matches modelfile). Only drop `think:False` and refresh the qwen3.5 comments.
- Each edited Pi4 file: deploy to RAM + persist to `/media/root-ro` + md5 RAM=SD + restart `assistant`/`iris-web` + verify. Per CLAUDE.md, needs user `DEPLOY`.

## Do NOT touch (intentional / false positives)
- `CHANGELOG.md`, `docs/iris_issue_log.md`, `docs/history/**`, `review/**` — append-only HISTORY; old model names there are correct.
- `src/eyes/**` (EyeController.h, eyes.h, anime.h, 240x240/*) — grep matches are hex colors / "thinking"-like substrings, NOT model refs. Verify, then leave.
- `docs/handoff_vision_latency.md` — historical (S118); mark superseded by S119b at top, don't rewrite.

## Suggested batching (one commit per batch)
1. Markdown/JSON docs (ARCH, README, ROADMAP, INVENTORY, sysmap remainder, guide html). REPO-ONLY → commit.
2. tools/* hardcoded strings. REPO-ONLY → commit.
3. WebUI + 4 Pi4 think:False callers. Needs DEPLOY → deploy+persist+verify → commit.

End each batch by updating SNAPSHOT/HANDOFF/CHANGELOG. Push only on user PUSH.

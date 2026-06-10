# Root Sweep — S119 (2026-06-09)

Untracked clutter swept out of repo root during the mistral-small3.2 migration session.
Nothing here is deleted. Move back or remove deliberately in a later housecleaning pass.
Operating assumption per user: **assume the original purpose is still valid until verified.**

| Now at (final) | Original location | What it is | Confidence | Recommendation |
|---|---|---|---|---|
| `null_emptyfile` | repo root, file literally named `$null` | 0-byte file, created 2026-06-01 22:25. Almost certainly a botched PowerShell redirect that wrote a literal file named `$null` instead of the null device. | High (empty, no content) | Safe to delete next session. Renamed from `$null` because that name is hostile to shells/git. |
| `Update-IRISProjectFiles.bat` | repo root | 96-byte launcher, presumably calls the `.ps1`. | Medium (not opened) | Keep with the `.ps1`. |
| `Update-IRISProjectFiles.ps1` | repo root | **Verified utility.** Copies project docs (SNAPSHOT_LATEST.md, HANDOFF_CURRENT.md, CLAUDE.md, IRIS_ARCH.md, docs/*, etc.) into `.\project-upload-staging\` and prints a per-file last-commit summary, then opens Explorer. Used to stage files for Claude.ai project attachments. | High (read in full) | **Path-sensitive:** uses `$RepoRoot = $PSScriptRoot`. It will NOT work from this folder as-is — it would stage into `_housekeeping/...` and look for docs under this folder. To relocate permanently (e.g. into `tools/`), change line 6 to `$RepoRoot = Split-Path $PSScriptRoot -Parent`. Until then, run it from repo root if needed. |

## Also done in this sweep
- `LICENSE` — was showing as deleted (`D`) in the working tree (unstaged). It's the committed Creative Commons license (commit `ca23ca4`). Restored via `git checkout -- LICENSE`. Not moved here; an accidental deletion, undone.

## Note on Update-IRISProjectFiles.ps1 (observation, not action)
This tool stages docs as Claude.ai project attachments — but CLAUDE.md and SNAPSHOT_LATEST.md both carry a standing warning that project-attached `.md` files are stale and must not be used (the local repo is the source of truth). If the attachment workflow has been abandoned in favor of the filesystem-MCP / raw-GitHub-snapshot flow, this script may be obsolete. Confirm with the user before deleting.

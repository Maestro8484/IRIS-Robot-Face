# IRIS Doc Organization Review — 2026-05-02

**Status: REVIEW ONLY — awaiting approval before any moves**

---

## A. Current Git Status

Working tree is **clean**. Branch: `main`.

The three files mentioned in the task prompt as "untracked" were already committed in the last commit:

```
b00dea9  docs: organize audits and wakeword import plan

A  docs/audits/IRIS_FULL_AUDIT_2026-05-02.md
A  docs/audits/IRIS_ITEMIZED_INVENTORY_2026-05-02.md
A  docs/wakeword/wakeword_import_plan_okay_iris.md
```

No untracked files exist. The three items in the task prompt are already done.

---

## B. Proposed Directories to Create

| Directory | Status |
|---|---|
| `docs/audits/` | Already exists (created in last commit) |
| `docs/wakeword/` | Already exists (created in last commit) |
| `docs/handoffs/` | **New — needs creation** |
| `docs/persona/` | **New — needs creation** |
| `docs/guides/` | **New — needs creation** |
| `docs/history/` | **New — needs creation** |

---

## C. Proposed File Moves

### Root → docs/wakeword/

| Old Path | New Path | Reason | Risk | References Needing Update |
|---|---|---|---|---|
| `HANDOFF_WAKEWORD_DEPLOY.md` | `docs/wakeword/HANDOFF_WAKEWORD_DEPLOY.md` | Wakeword-specific deployment handoff; not a current-session startup doc | Low | `PRIMER_WAKEWORD_DEPLOY.md:29` — text instruction "Read `HANDOFF_WAKEWORD_DEPLOY.md`" needs path update if that file also moves |
| `PRIMER_WAKEWORD_DEPLOY.md` | `docs/wakeword/PRIMER_WAKEWORD_DEPLOY.md` | Wakeword-specific session primer; superseded by main PRIMER.md for current sessions | Low | None that require file-content edits (it's self-referential context) |
| `WAKEWORD_TRAINING_HANDOFF.md` | `docs/wakeword/WAKEWORD_TRAINING_HANDOFF.md` | Wakeword training handoff from S26 era; historical | Low | `snapshots/SNAPSHOT_2026-04-25.md` — old snapshot, text mention only, no action needed |

### Root → docs/audits/

| Old Path | New Path | Reason | Risk | References Needing Update |
|---|---|---|---|---|
| `S42_LOG_AUDIT.md` | `docs/audits/S42_LOG_AUDIT.md` | Dated session audit; belongs with other audit docs | Low | `docs/audits/IRIS_FULL_AUDIT_2026-05-02.md` — text mention only, no hyperlink, no update needed |

### Root → docs/handoffs/

| Old Path | New Path | Reason | Risk | References Needing Update |
|---|---|---|---|---|
| `HANDOFF_S23.md` | `docs/handoffs/HANDOFF_S23.md` | Old session-23 handoff; superseded by HANDOFF_CURRENT.md | Low | None found |

### Root → docs/guides/ (borderline — see note)

| Old Path | New Path | Reason | Risk | References Needing Update |
|---|---|---|---|---|
| `PRIMER.md` | `docs/guides/PRIMER.md` | Not in the protected root list; functions as operator guide | **Medium** | `CLAUDE.md` does not reference PRIMER.md by path. `docs/audits/IRIS_FULL_AUDIT_2026-05-02.md` references `PRIMER.md` as text (no hyperlink). `README.md` — **needs checking** (see note below). |

> **Note on PRIMER.md:** This is borderline. It is operationally referenced by name in the Full Audit doc and is likely referenced in README.md. If it moves, any instructions that say "Read PRIMER.md" at session start would need updating. Recommend leaving PRIMER.md at root unless you specifically want to move it.

### docs/ → docs/persona/

| Old Path | New Path | Reason | Risk | References Needing Update |
|---|---|---|---|---|
| `docs/IRIS_PERSONA_REVIEW_S39.md` | `docs/persona/IRIS_PERSONA_REVIEW_S39.md` | Persona review doc; fits the persona subfolder | Low | None found |

### docs/ → docs/guides/

| Old Path | New Path | Reason | Risk | References Needing Update |
|---|---|---|---|---|
| `docs/GUIDE-settings.md` | `docs/guides/GUIDE-settings.md` | User/operator guide; fits guides subfolder | Low | None found |
| `docs/GUIDE-settings.docx` | `docs/guides/GUIDE-settings.docx` | Companion docx to the guide | Low | None found |

### docs/ → docs/history/

| Old Path | New Path | Reason | Risk | References Needing Update |
|---|---|---|---|---|
| `docs/tts-history.md` | `docs/history/tts-history.md` | Historical TTS subsystem notes | Low | `docs/audits/IRIS_FULL_AUDIT_2026-05-02.md:49` — text mention `tts-history.md`, no hyperlink, no update needed |

---

## D. Files That Should Stay at Root and Why

| File | Reason |
|---|---|
| `README.md` | Public-facing; in protected list |
| `CLAUDE.md` | Session rules; must be at root for Claude Code auto-load |
| `AGENTS.md` | Agent instructions; in protected list |
| `WORKFLOW_RULE.md` | Operational rule; in protected list |
| `HANDOFF_CURRENT.md` | Active session startup doc; in protected list |
| `SNAPSHOT_LATEST.md` | Active session startup doc; in protected list |
| `ROADMAP.md` | Active planning; in protected list |
| `CHANGELOG.md` | Active changelog; in protected list |
| `IRIS_ARCH.md` | Architecture reference; in protected list |
| `IRIS_CONFIG_MAP.md` | Config reference; in protected list |
| `IRIS_STATUS.json` | Runtime status file; in protected list |
| `platformio.ini` | Build config; in protected list |
| `LICENSE` | In protected list |
| `.gitignore` | In protected list |
| `replacements.txt` | Small utility file, not a candidate |

---

## E. Files That Should Stay in Current docs/ Location and Why

| File | Reason |
|---|---|
| `docs/iris_issue_log.md` | Created S45 as the canonical issue/fix log; stays at `docs/` root for easy access |
| `docs/intent-router.md` | Not in task scope; no move proposed without explicit direction |

---

## F. Exact PowerShell Commands for Implementation

```powershell
# Working directory assumed: C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face

# Step 1: Create new subdirectories
New-Item -ItemType Directory -Path "docs\handoffs" -Force
New-Item -ItemType Directory -Path "docs\persona" -Force
New-Item -ItemType Directory -Path "docs\guides" -Force
New-Item -ItemType Directory -Path "docs\history" -Force

# Step 2: Move wakeword docs (root → docs/wakeword/)
git mv HANDOFF_WAKEWORD_DEPLOY.md docs/wakeword/HANDOFF_WAKEWORD_DEPLOY.md
git mv PRIMER_WAKEWORD_DEPLOY.md docs/wakeword/PRIMER_WAKEWORD_DEPLOY.md
git mv WAKEWORD_TRAINING_HANDOFF.md docs/wakeword/WAKEWORD_TRAINING_HANDOFF.md

# Step 3: Move audit doc (root → docs/audits/)
git mv S42_LOG_AUDIT.md docs/audits/S42_LOG_AUDIT.md

# Step 4: Move old handoff (root → docs/handoffs/)
git mv HANDOFF_S23.md docs/handoffs/HANDOFF_S23.md

# Step 5: Move persona review (docs/ → docs/persona/)
git mv docs/IRIS_PERSONA_REVIEW_S39.md docs/persona/IRIS_PERSONA_REVIEW_S39.md

# Step 6: Move guide docs (docs/ → docs/guides/)
git mv docs/GUIDE-settings.md docs/guides/GUIDE-settings.md
git mv docs/GUIDE-settings.docx docs/guides/GUIDE-settings.docx

# Step 7: Move tts history (docs/ → docs/history/)
git mv docs/tts-history.md docs/history/tts-history.md

# --- PRIMER.md: NOT moved by default (medium risk, borderline) ---
# --- Uncomment below ONLY if user explicitly approves PRIMER.md move ---
# git mv PRIMER.md docs/guides/PRIMER.md

# Step 8: Update reference in PRIMER_WAKEWORD_DEPLOY.md (after move)
# File now at: docs/wakeword/PRIMER_WAKEWORD_DEPLOY.md
# Line 29 currently reads: 5. Read `HANDOFF_WAKEWORD_DEPLOY.md`.
# No file-content edit needed — both files are in the same folder after the move,
# and the instruction is prose (not a hyperlink), so paths are not broken.
# If desired, the text could be updated to note the new location, but it is not required.
```

**Total: 4 new directories, 8 file moves. No file content edits required.**

---

## G. Rollback Plan

All moves use `git mv`, so rollback is:

```bash
git reset HEAD
# Then restore each moved file:
git mv docs/wakeword/HANDOFF_WAKEWORD_DEPLOY.md HANDOFF_WAKEWORD_DEPLOY.md
git mv docs/wakeword/PRIMER_WAKEWORD_DEPLOY.md PRIMER_WAKEWORD_DEPLOY.md
git mv docs/wakeword/WAKEWORD_TRAINING_HANDOFF.md WAKEWORD_TRAINING_HANDOFF.md
git mv docs/audits/S42_LOG_AUDIT.md S42_LOG_AUDIT.md
git mv docs/handoffs/HANDOFF_S23.md HANDOFF_S23.md
git mv docs/persona/IRIS_PERSONA_REVIEW_S39.md docs/IRIS_PERSONA_REVIEW_S39.md
git mv docs/guides/GUIDE-settings.md docs/GUIDE-settings.md
git mv docs/guides/GUIDE-settings.docx docs/GUIDE-settings.docx
git mv docs/history/tts-history.md docs/tts-history.md
# Remove empty dirs:
Remove-Item docs/handoffs, docs/persona, docs/guides, docs/history -Recurse
```

Because nothing is committed yet, a `git reset HEAD` unstages all moves and the files return to their original names.

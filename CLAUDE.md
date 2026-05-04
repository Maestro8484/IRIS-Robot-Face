# IRIS - Claude Code Rules

## Mission Context

This repository uses documentation as executable operational guidance for AI agents. Assume these docs may be used to locate systems, edit files, deploy services, flash firmware, verify health, update configs, and coordinate distributed IRIS hardware (Pi4, GandalfAI, Teensy, SuperMaster). Read docs as instructions, not commentary.

---

## Repository Authority

Canonical source of truth:
`C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face`

This is the local repository on SuperMaster desktop.

GitHub is a secondary mirror and backup. It may lag local state until explicitly committed and pushed.

Always trust local repo state first:
1. local file contents
2. local `git status`
3. local `git log`
4. live system checks
5. GitHub remote only after fetch/compare

## Explicit Operational Constraints (Always Enforced)

- Local repo is the only source of truth for all edits.
- Do not push to GitHub unless explicitly instructed by the user.
- Do not edit Pi4 or GandalfAI directly unless the user says DEPLOY.
- Show diff, wait for approval before writing any file.

---

## Session Start

Every Claude Code session must start with:

```text
Branch: [must be main - if not, stop]
Last commit: [hash + message]
Working tree: [clean / dirty - if dirty, stop]
Task: [one sentence]
Files to modify: [explicit list]
Risk: [what could break]
Rollback: [how to undo]
```

Required pre-flight:
1. `git status`
2. Read `HANDOFF_CURRENT.md` only if task involves pipeline, deploy, or architecture changes
3. Read first 50 lines of `SNAPSHOT_LATEST.md`
4. Read `CLAUDE.md`
5. Read task-relevant files in full before writing
6. Output pre-flight summary
7. Wait for user confirmation before edits
8. Complete Session Close Report before ending session.

---

## Session Close Template

**Session summary**:
What changed, what now works, or what was decided? Write this for the human operator who may read it days later and need to remember what actually happened.

**Token-efficiency report**:
- Files read:
- Files edited:
- Commands run:
- Files intentionally not read:
- Large docs avoided:
- IRIS_ARCH.md loaded? Y/N -- reason:
- IRIS_CONFIG_MAP.md loaded? Y/N -- reason:

**Documentation status** - updated / not updated / skipped with reason:
- SNAPSHOT_LATEST.md:
- HANDOFF_CURRENT.md:
- ROADMAP.md:
- CHANGELOG.md:
- docs/iris_issue_log.md:
- Task-specific plan/log files:

**Commit / push status**:
- Commit created? Y/N -- branch:
- Push status:

**Human follow-up needed**:

---
<!-- CONDITIONAL: Complete only if triggered. Mark N/A if not applicable. -->

**Pi4 deploy** - N/A if no files were deployed to Pi4:
- Direct /media/root-ro persistence completed: Y/N
- Sync completed: Y/N
- md5 verified: Y/N
- Service restarted: Y/N
- Logs checked post-restart: Y/N
- Rollback position if revert needed:

**High-risk changes** - N/A if none:
Check all that changed and state which doc was updated, or why it was skipped:
- [ ] Firmware
- [ ] Ollama model / modelfile rebuild
- [ ] Workflow rules
- [ ] Architecture
- [ ] Pin assignments
- [ ] Source mapping / pi4 deploy mapping
- [ ] Config mapping / IRIS_CONFIG_MAP.md
Doc updated:
Doc skipped -- reason:

---

Documentation rules for this report:
- Future, active, queued, or unresolved work goes in ROADMAP.md.
- Completed work goes in CHANGELOG.md.
- Current verified system state and active issues go in SNAPSHOT_LATEST.md.
- Short next-session startup/deploy/rollback handoff goes in HANDOFF_CURRENT.md.
- Issue-specific status changes go in docs/iris_issue_log.md when relevant.
- Do not claim any documentation file was updated unless it was actually edited this session.
- Do not duplicate completed-history details into ROADMAP.md.

---

## Hard Rules

- One task per session.
- One batch per implementation pass.
- Full file outputs only when asked to generate files.
- No partial inserts/additions for user-applied documentation/config/code updates.
- No broad refactors during hardening work.
- No formatting-only changes.
- No import sorting unless required by the task.
- Touch only files required for the approved task.
- Read live files before editing. Never write from memory.
- Preserve working behavior unless behavior is the identified bug.
- Provide rollback steps.
- Commit each batch separately.
- Update docs after meaningful changes.
- Do not stack unverified changes.
- Never push to GitHub unless explicitly authorized in the current session.
- Never write to Pi4 or GandalfAI unless the user says DEPLOY.

---

## Status Terminology Rule

Do not call a change "done," "implemented," "complete," or "working" unless it
has been deployed to the relevant live target and verified.

Use these exact status words only:

- REPO-ONLY: files changed/committed locally, but live IRIS is unchanged.
- PUSHED: changes are on GitHub, but live IRIS may still be unchanged.
- DEPLOYED: changes copied/rebuilt/flashed to the relevant live system.
- VERIFIED: behavior tested on live IRIS and confirmed.

## Required Session Close Status Block

Every session must end with this block, fully filled out:

```text
Repo status:
GitHub status:
Pi4 live status:
Teensy firmware status:
GandalfAI model status:
Live IRIS behavior right now:
Remaining steps before user-visible behavior changes:
```

---

## Protected Files

Do not touch unless explicitly requested:
- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

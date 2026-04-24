# IRIS Codex Rules

## Non-negotiable

- Read-only unless explicitly told to implement.
- If about to modify a file, stop and output proposed change in text first.
- No commits, branches, PRs, pushes unless explicitly requested.
- No formatting-only changes.
- No broad refactors.
- Touch only files required for task.
- Preserve working behavior unless behavior is the identified bug.

---

## Project Priorities

1. Reliability
2. Recoverability
3. Sleep/wake consistency
4. Hardware compatibility
5. Minimal diffs
6. Clear rollback path

---

## Environment

- Canonical source of truth is the local repo on SuperMaster:
  `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face`
- GitHub is a secondary mirror and may lag local state.
- Pi4 uses overlayfs.
- Pi4 persistence uses direct `/media/root-ro` remount method only unless re-verified.
- Teensy 4.1 is canonical.
- Windows host is GandalfAI.
- PowerShell commands preferred on Windows systems.
- Pi4 shell commands are bash/Linux.
- GandalfAI is Windows. Do not use Linux commands on GandalfAI.

---

## Change Style

- Small staged patches.
- One batch at a time.
- Preserve working behavior.
- Add tests/checklists.
- Explain regression risks.
- Provide rollback steps.
- Do not stack unverified changes.

---

## MAD Loop

IRIS uses the MAD Loop for non-trivial changes:

Plan -> Independent Review -> Optional Codex Audit -> Final Handoff -> Claude Code Implementation -> Human Test -> Documentation Update

Codex should normally be used for read-only repo-wide review unless explicitly instructed to implement.
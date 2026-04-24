# IRIS Codex Rules

## Non-negotiable
- Read-only unless explicitly told to implement.
- If about to modify a file, stop and output proposed change in text first.
- No commits, branches, PRs, pushes unless explicitly requested.
- No formatting-only changes.
- No broad refactors.
- Touch only files required for task.

## Project Priorities
1. Reliability
2. Recoverability
3. Sleep/wake consistency
4. Hardware compatibility
5. Minimal diffs

## Environment
- Pi4 uses overlayfs
- Teensy 4.1 is canonical
- Windows host is GandalfAI
- PowerShell commands preferred on Windows

## Change Style
- Small staged patches
- Preserve working behavior
- Add tests/checklists
- Explain regression risks
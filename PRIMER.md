# IRIS Session Primer

Paste at the start of every new Claude Chat or Claude Code session.
Fill in TASK on the last line before pasting.

---

## Standard (default)

STOP. Do not respond yet.

IRIS project. Claude Desktop GUI on SuperMaster. Filesystem MCP active.

Source of truth: C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face
GitHub is secondary mirror only and may lag local state.

REQUIRED before any response — read these files via filesystem MCP in this order:
1. CLAUDE.md
2. SNAPSHOT_LATEST.md
3. HANDOFF_CURRENT.md

Load on demand only: IRIS_ARCH.md

After reading all three, output pre-flight and wait for confirmation:
- Branch (must be main — if not, stop)
- Last commit hash + message
- Working tree (clean / dirty — if dirty, stop)
- Active task from snapshot or handoff
- Files likely involved
- Risk
- Rollback

Do not proceed to the task without explicit confirmation.

TASK: [see TASK at bottom]

---

## Notes

- Docs carry state. Primer is the bootloader only.
- Local repo is always #1 truth. GitHub is #1.5.
- If snapshot conflicts with GitHub, local snapshot wins.
- IRIS_ARCH.md loads only when architecture, pins, deploy commands, or service config is needed.
- GitHub push is never automatic. User must explicitly authorize it.
- Pi4 and GandalfAI are read-only until user says DEPLOY.
- All edits go to local repo only. Show diff, wait for approval before any write.
- Before starting a session, run: .\scripts\iris_status.ps1
  This writes IRIS_STATUS.json which Claude Code loads automatically at session start.

TASK:  [paste task here]

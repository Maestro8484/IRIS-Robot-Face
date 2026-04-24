# IRIS Session Primer

Paste this at the start of every new Claude Chat or Claude Code session.
Fill in TASK before pasting.

---

## Standard (default)

```
IRIS project. Claude Desktop GUI on SuperMaster. Filesystem MCP active.

Source of truth: C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face
GitHub is secondary mirror only and may lag local state.

Read via filesystem MCP before responding:
1. CLAUDE.md
2. SNAPSHOT_LATEST.md
3. HANDOFF_CURRENT.md

Load on demand only: IRIS_ARCH.md

Pre-flight output:
- branch
- last commit
- working tree
- task

Then wait for confirmation.

TASK: [paste here]
```

---

## Risky sessions (deployment, overlayfs writes, firmware, config changes)

Add to pre-flight block:

```
- files likely involved
- risk
- rollback
```

---

## Notes

- Docs carry state. Primer is the bootloader only.
- Local repo is always #1 truth. GitHub is #1.5.
- If snapshot conflicts with GitHub, local snapshot wins.
- IRIS_ARCH.md loads only when architecture, pins, deploy commands, or service config is needed.

# IRIS Project — Workflow Rule (NEVER DROP)

## Claude Chat vs Claude Code

**Claude Chat** = planning, strategy, design decisions, hardware spec, snapshot updates, architecture discussions, visual mockups.

**Claude Code** = ALL implementation: SSH, file writes, firmware builds, PlatformIO, Python edits, deployment, Pi4 overlayfs persistence.

Never implement or deploy from Claude Chat when Claude Code is available.
Always route execution work to Claude Code with the current snapshot as context.

This rule applies to every session, regardless of what else is discussed.

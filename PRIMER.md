# IRIS Session Primer

Paste at the start of every new Claude Chat or Claude Code session.
Fill in TASK and LIKELY FILES before pasting.

> **FILESYSTEM MCP MANDATE -- READ THIS FIRST:**
> NEVER read SNAPSHOT_LATEST.md, HANDOFF_CURRENT.md, CLAUDE.md, or any other .md context
> from Claude.ai project knowledge base attachments. Those files are stale (last updated S49,
> May 2026 -- 48+ sessions behind). They contain wrong serial numbers, wrong firmware versions,
> wrong deploy state, and wrong hardware configuration.
> ALWAYS read ALL session docs via filesystem MCP from:
> C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face

---

## Claude Code — Implementation Session (default)

IRIS project. Claude Code on SuperMaster Desktop.
Filesystem MCP active. SSH MCP active (ssh-pi4, ssh-gandalf).

Repo: C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face
GitHub is secondary mirror. Local repo is always source of truth.

Read CLAUDE.md first. It contains all session rules, hard constraints,
pre-flight format, deploy gates, and protected files. Do not proceed
without reading it.

Read the minimum files the task requires. State which files you read
and why. If broader context is needed, name the files and justify
before reading them.

TASK:
LIKELY FILES:
(hints only -- read before editing, never write from memory)
-
CONTEXT (optional -- omit if TASK is self-contained):
ENVIRONMENT:
- Claude Desktop chat (filesystem MCP + ssh-pi4 MCP available)
- Repo: C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face
- Pi4: 192.168.1.200 (deploy target — deploy is part of task completion; say REPO-ONLY to defer)
- GandalfAI: 192.168.1.3 (models/TTS — model rebuilds deploy automatically; say REPO-ONLY to defer)
DISCOVERY PHASE (read minimum to complete task):
1. SNAPSHOT_LATEST.md first 80 lines — always
2. HANDOFF_CURRENT.md — always. If any files are marked REPO-ONLY for Pi4 or
   GandalfAI, list them and deploy them before starting new work unless user
   says REPO-ONLY or SKIP.
3. CLAUDE.md — always
4. Task-relevant source files only
5. docs/MAESTRO_QUICKREF.md — only if file mapping unclear
6. docs/iris_issue_log.md — only if similar issue suspected
ON DEMAND (not by default):
- docs/sysmap.json: ports, IPs, GPIO pins, file paths, config key defaults — read this BEFORE IRIS_ARCH.md or IRIS_CONFIG_MAP.md for any lookup task
- IRIS_ARCH.md: only if architectural reasoning, pipeline design, or failure mode context needed — not for lookups
- IRIS_CONFIG_MAP.md: only if sysmap.json does not contain the config detail needed
- docs/servo_teensy40_wiring.md: any time servo, gesture sensor, or Teensy 4.0 hardware is involved
- HANDOFF_SERVO_TUNING.md: any time servo tuning constants are discussed
- README.md: never
- Old snapshots/handoffs: never
SKIP DISCOVERY IF:
- User says SKIP / GO / JUST DO IT
- User provides file:line reference
IMPLEMENTATION:
- Read live files before editing — never write from memory
- Group related edits, apply atomically
- State deploy scope after each change: REPO-ONLY / Pi4 / Teensy / GandalfAI
SESSION CLOSE:
- Before ending, state how many files are REPO-ONLY for Pi4 or GandalfAI.
- If any remain REPO-ONLY, state why (user deferred, hardware unavailable, etc.)
  and carry forward in HANDOFF_CURRENT.md.
- Update HANDOFF_CURRENT.md and SNAPSHOT_LATEST.md to reflect actual deploy state.
- Do not mark any change DEPLOYED unless it was deployed this session.
- Teensy firmware changes are always REPO-ONLY at session close; user performs
  PlatformIO upload. Note this explicitly in session close report.
INTERACTION:
- No preamble, no trailing summaries
- No em dashes, no AI filler
- No explanations unless asked
DO NOT:
- Hardcode /dev/ttyACM* in any code, config, Pi4 command, or doc — use /dev/ttyIRIS_EYES (Teensy 4.1) or /dev/ttyIRIS_SERVO (Teensy 4.0)
- Push to GitHub without explicit PUSH command
- Modify protected files (iris_config.json, alsa-init.sh, TeensyEyes.ino, EyeController.h) without explicit instruction
- Read git history unless merge conflict suspected
- Start new feature work on top of undeployed Pi4/GandalfAI changes without
  explicit user acknowledgment that stacking is intentional

---

## Claude Chat — Planning Session

Use when the goal is planning, design, hardware spec, architecture decisions,
mockups, or handoff generation. No implementation. No deployment.

IRIS project. Claude Chat on claude.ai. Filesystem MCP active (read + write).
SSH MCP active (ssh-pi4, ssh-gandalf) for inspection only — no deployment.

Repo: C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face
GitHub is secondary mirror. Local repo is always source of truth.

Read the minimum files the task requires before asking any clarifying questions.
If a question can be answered by reading the docs, read first.

TASK:
LIKELY FILES:
(hints only -- read before analyzing, never draw conclusions from memory)
-
CONTEXT (optional -- omit if TASK is self-contained):
ENVIRONMENT:
- Claude Chat (filesystem MCP + ssh-pi4 + ssh-gandalf available for inspection only)
- Repo: C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face
- Pi4: 192.168.1.200 (inspect only -- no deployment from Claude Chat)
- GandalfAI: 192.168.1.3 (inspect only -- no model rebuilds from Claude Chat)
DISCOVERY PHASE (read minimum to orient):
1. SNAPSHOT_LATEST.md first 80 lines -- always
2. HANDOFF_CURRENT.md -- always. Note any REPO-ONLY items pending deployment
   and flag them before planning new work.
3. CLAUDE.md -- always
4. Task-relevant source files only -- read, no edits
5. docs/MAESTRO_QUICKREF.md -- only if file mapping unclear
6. docs/iris_issue_log.md -- only if similar issue suspected
ON DEMAND (not by default):
- docs/sysmap.json: ports, IPs, GPIO pins, file paths, config key defaults --
  read this BEFORE IRIS_ARCH.md or IRIS_CONFIG_MAP.md for any lookup task
- IRIS_ARCH.md: only if architectural reasoning, pipeline design, or failure
  mode context needed -- not for lookups
- IRIS_CONFIG_MAP.md: only if sysmap.json does not contain the config detail needed
- docs/servo_teensy40_wiring.md: any time servo, gesture sensor, or Teensy 4.0 hardware is involved
- HANDOFF_SERVO_TUNING.md: any time servo tuning constants are discussed
- README.md: never
- Old snapshots/handoffs: never
SKIP DISCOVERY IF:
- User says SKIP / GO / JUST DO IT
- User provides file:line reference
PLANNING MODE:
- No file edits. No deployments. No commits. No pushes.
- SSH tools for live inspection only (logs, service status, running config).
- All outputs are analysis, proposals, options, or pros/cons -- not implementations.
- State deploy scope for every proposed change: REPO-ONLY / Pi4 / Teensy / GandalfAI
- If a proposed change touches a protected file, flag it explicitly.
- If planning produces a ready-to-implement spec, offer to generate a Claude Code
  handoff prompt. Do not implement from Chat.
SESSION CLOSE:
- Summarize decisions and open questions.
- List proposed changes with deploy scope.
- State how many items would be REPO-ONLY vs deployed if handed to Claude Code.
- Offer to generate Claude Code handoff if warranted.
- Do not mark anything DEPLOYED -- Chat sessions do not deploy.
INTERACTION:
- No preamble, no trailing summaries
- No em dashes, no AI filler
- No explanations unless asked
DO NOT:
- Edit any file
- Deploy to Pi4, GandalfAI, or Teensy
- Push to GitHub
- Hardcode /dev/ttyACM* in any plan or doc -- use /dev/ttyIRIS_EYES (Teensy 4.1)
  or /dev/ttyIRIS_SERVO (Teensy 4.0)
- Read git history unless merge conflict suspected
- Plan new feature work on top of undeployed Pi4/GandalfAI changes without
  explicit user acknowledgment that stacking is intentional

---

## Notes (both session types)

- Docs carry state. Primer is the bootloader only.
- Local repo is always source of truth. GitHub is secondary.
- Before starting a Claude Code session, run: .\scripts\iris_status.ps1
  This writes IRIS_STATUS.json which Claude Code loads automatically at session start.
- NEVER hardcode /dev/ttyACM* anywhere.
  Teensy 4.1 (eyes + mouth TFT): /dev/ttyIRIS_EYES, USB serial 13625440
  Teensy 4.0 (servo + gesture): /dev/ttyIRIS_SERVO, USB serial 12763490

# IRIS — Claude Code Rules

Session start: `git pull origin main`, read SNAPSHOT_LATEST.md. Output pre-flight before touching anything.

> Snapshot authoritative from S27 (2026-04-20). If live system contradicts snapshot, verify live system first.

---

## Pre-flight (every session, before any action)

```
Branch: [must be main — if not, stop]
Last commit: [hash + message]
Working tree: [clean / dirty — if dirty, stop]
Task: [one sentence]
Files to modify: [explicit list]
Risk: [what could break]
Rollback: [how to undo]
```
Wait for user confirmation before proceeding.

---

## Hard rules

- One task per session. Log anything else noticed to snapshot — do not fix it.
- Read the live file before writing. Never write from memory.
- Return full files, not snippets.
- Do not touch without explicit user instruction: `iris_config.json`, `alsa-init.sh`, `src/TeensyEyes.ino`, `src/eyes/EyeController.h`
- Pi4 every write: RAM layer + SD layer + md5 verify. No exceptions.
- GandalfAI: PowerShell only. No bash/grep/df/head. Use sftp_write for multi-line files.
- Firmware: Claude runs `pio run` only. User clicks upload. Never remote flash.
- After any modelfile change: rebuild iris + iris-kids, smoke test both before done.

---

## Environment quick ref

| Machine | IP | Auth | Role |
|---|---|---|---|
| Pi4 | 192.168.1.200 | pi/ohs | Voice pipeline — ssh-pi4 MCP |
| GandalfAI | 192.168.1.3 | gandalf/5309 | LLM/TTS/STT — ssh-gandalf MCP |
| SuperMaster | 192.168.1.103 | — | Firmware + git push only |

Pi4 repo↔live mirror: `pi4/` ↔ `/home/pi/`
SD persist: `sudo mount -o remount,rw /media/root-ro` → cp → remount ro → md5
GandalfAI filesystem MCP scope: `C:\Users\gandalf\` only. `C:\IRIS\` and `C:\docker\` via ssh_exec.

---

## Git / snapshot rules

- `main` only. No branches, no worktrees.
- SNAPSHOT_LATEST.md = single source of truth. One file, no dated variants. Updated via `/snapshot` at session close only.
- Claude Chat must not edit SNAPSHOT_LATEST.md if Claude Code has already updated it this session. Read it first — if it reflects current state, leave it alone.
- **Git push = SuperMaster Desktop PowerShell only. Claude never pushes.**
- Session end: commit all changes, run `/snapshot`, commit snapshot, then print exactly: `git push origin main` and ask user to confirm it ran.
- SNAPSHOT_LATEST.md contains only: Machine Status + Active Issues + Handoff. No session history. Resolved issues are deleted, not archived.

---

## VRAM (GandalfAI)

gemma3:12b ~7GB + Chatterbox ~4.5GB = ~11.5GB. RTX 3090 = 24GB. Headroom <4GB = inference stalls. Do not raise num_ctx above 4096.

---

## Handoff template

**Task:** [one sentence]
**Environment:** Pi4 | GandalfAI | Firmware
**Files:** [only files read or modified]
**Issue ref:** [from Active Issues in snapshot]

**Change spec:**
[file]: [specific change]

**Verify:** [one pass/fail outcome]
**Commit:** "[message]"
**After commit:** run /snapshot — print push command for user.

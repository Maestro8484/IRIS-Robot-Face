# IRIS - Claude Code Rules

## Mission Context

This repository uses documentation as executable operational guidance for AI agents.

Assume these docs may be used to:
- locate systems
- edit files
- deploy services
- flash firmware
- verify health
- update configs
- perform staged hardening
- coordinate Pi4, GandalfAI, Teensy 4.1, and SuperMaster workflows

Read docs as instructions, not commentary.

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
2. Read `HANDOFF_CURRENT.md`
3. Read `SNAPSHOT_LATEST.md`
4. Read `CLAUDE.md`
5. Read task-relevant files in full before writing
6. Output pre-flight summary
7. Wait for user confirmation before edits

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

## Protected Files

Do not touch unless explicitly requested:
- `iris_config.json`
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

---

## Environment Quick Reference

| Machine | IP | Auth | Role |
|---|---|---|---|
| SuperMaster Desktop | 192.168.1.103 | SuperMaster/ohs | Control node, Claude Desktop, local repo, VS Code, PlatformIO, git |
| Pi4 | 192.168.1.200 | pi/ohs | Runtime orchestration, wakeword, audio, web UI, cron, serial bridge - ssh-pi4 MCP |
| GandalfAI | 192.168.1.3 | gandalf/5309 | Ollama, Whisper, Kokoro TTS (primary), Piper TTS (fallback), Chatterbox (rollback only), RTX 3090 inference - ssh-gandalf MCP |
| Teensy 4.1 | USB via SuperMaster/Pi context | N/A | Embedded display controller |

Pi4 live mirror:
`pi4/` in repo maps to `/home/pi/` on Pi4.

GandalfAI:
Use PowerShell syntax. No bash, grep, df, or head. Use PowerShell equivalents.
Filesystem MCP scope: `C:\Users\gandalf\` only. `C:\IRIS\` and `C:\docker\` via ssh_exec or sftp_write.

Firmware:
Claude may run `pio run`. User performs PlatformIO upload unless explicitly directed otherwise. Never remote flash unless an approved workflow says so.

---

## VRAM (GandalfAI)

Kokoro ~2GB + gemma3:27b-it-qat ~14.1GB = ~16.1GB. RTX 3090 = 24GB. Headroom ~7.9GB.
- Do not raise `num_ctx` above 4096.
- Close Chrome and Claude Desktop during inference-heavy sessions.

---

## Pi4 Persistence

Pi4 uses overlayfs. Writes go to RAM layer unless persisted to SD.

Use direct `/media/root-ro` remount method only.

Do not use `overlayroot-chroot` unless explicitly re-verified.

Canonical persistence pattern:
```bash
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/<file> /media/root-ro/home/pi/<file>
sudo chown pi:pi /media/root-ro/home/pi/<file>
sudo chmod 644 /media/root-ro/home/pi/<file>
sync
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/<file> /media/root-ro/home/pi/<file>
```

For executable scripts:
```bash
sudo chmod 755 /media/root-ro/home/pi/<script>.py
```

Every Pi4 file write must include:
- RAM layer update
- SD layer persistence
- md5 verification
- service restart if needed
- log check

No exceptions.

---

## Git / Snapshot Rules

- `main` only.
- No branches unless explicitly requested.
- GitHub is secondary mirror, not canonical truth.
- Claude never pushes unless explicitly authorized.
- User normally runs `git push origin main` from SuperMaster PowerShell.
- `SNAPSHOT_LATEST.md` records current machine status, active issues, and immediate handoff.
- `HANDOFF_CURRENT.md` records authoritative workflow and current roadmap.
- If Claude Code updates snapshot/docs and commits, Claude Chat must not re-snapshot unless explicitly asked.
- When Claude Chat and Claude Code are both active: Claude Code is authoritative for all file writes, commits, and snapshots. Claude Chat is read-only for docs unless explicitly directed otherwise.

---

## MAD Loop - Required Change Workflow

MAD Loop = Multi-Agent Adversarial Dev Loop.

Use for all non-trivial changes:

Plan -> ChatGPT Review -> Optional Codex Audit -> Final Handoff -> Claude Code Implementation -> Human Validation -> Documentation Update

Rules:
- One batch per session.
- Minimal diffs.
- Preserve working behavior unless behavior is the bug.
- Include rollback steps.
- Test before next batch.
- Do not stack unverified changes.
- Human operator has final authority.

---

## Batch Model

Current hardening sequence:
- Batch 1A = runtime survival / wakeword anti-crash and anti-hang
- Batch 1B = sleep/wake authority and state consistency
- Batch 1C = reliability hygiene and diagnostics
- Batch 2 = Teensy hardware/firmware pass
- Batch 3 = GandalfAI personality/pipeline pass

Future batches may supersede this order only after review.

---

## Handoff Template

```text
Task: [one sentence]
Environment: Pi4 | GandalfAI | Firmware | SuperMaster
Files: [only files read or modified]
Issue ref: [from Active Issues or HANDOFF_CURRENT]

Change spec:
[file]: [specific change]

Verify:
[one pass/fail outcome]

Rollback:
[exact revert method]

Commit:
"[message]"

After commit:
run snapshot/docs update if required, then print push command for user.
```

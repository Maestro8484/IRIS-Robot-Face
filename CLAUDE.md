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
6. Complete Session Close Report before ending session.

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

**Proactive Flags** - Optional. Add if anything was observed during the session worth surfacing for future work:
Append a `## Proactive Flags` section to `HANDOFF_CURRENT.md` for any of the following observed during the session:
- Latency bottlenecks or pipeline inefficiencies
- Architectural inefficiencies or technical debt
- Hardware upgrade opportunities
- Model/inference performance issues
- Reliability risks not yet filed as issues
Format: one bullet per flag, one sentence each. Section is cumulative — do not overwrite prior flags, append.

**Human follow-up needed**:

---
<!-- CONDITIONAL: Complete only if triggered. Mark N/A if not applicable. -->

**Pi4 deploy** - N/A if no files were deployed to Pi4:
- Direct /media/root-ro persistence completed: Y/N
- System-path files (outside /home/pi/) persisted: list each one — /etc/udev/rules.d/, /etc/systemd/, etc. must be written to /media/root-ro/<same path> individually. The standard /home/pi/ procedure does NOT cover these automatically.
- Sync completed: Y/N
- md5 verified: Y/N (for every file deployed, including system-path files)
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
- CHANGELOG.md MUST be updated before the session closes. Never defer it to "next session." A session is not done until CHANGELOG.md reflects everything that was completed in it. There is no valid reason to skip this.

---

## Hard Rules

- One task per session.
- One batch per implementation pass.
- Full file outputs only when asked to generate files.
- No partial inserts/additions for user-applied documentation/config/code updates.
- No broad refactors during hardening work.
- No formatting-only changes.
- No import sorting unless required by the task.
- Touch only files required for the task.
- Read live files before editing. Never write from memory.
- Preserve working behavior unless behavior is the identified bug.
- Provide rollback steps.
- Commit each batch separately.
- Update docs after meaningful changes. CHANGELOG.md is not optional — update it in the same session as the work, before closing. "Next session" is not a valid deferral.
- Do not stack unverified changes.
- Never push to GitHub unless explicitly authorized in the current session.
- Never write to Pi4 or GandalfAI unless the user says DEPLOY.
- Before every firmware flash (env:eyes or env:teensy40): update `FIRMWARE_VERSION` in `src/config.h` to the current session tag (e.g. `"S87b"`). After flash, verify the version appears in `journalctl -u assistant | grep VER`. This is the only reliable way to know what firmware the Teensy is running.
- Never hardcode `/dev/ttyACM*` in code, config, or commands. Always use `/dev/ttyIRIS_EYES` (Teensy 4.1 eyes + mouth) or `/dev/ttyIRIS_SERVO` (Teensy 4.0 servo + gesture). These are udev symlinks bound to hardware USB serial numbers — they survive USB port swaps and reboots. ttyACM* numbers are port-position-based and change when cables are moved (confirmed failure S63).
- Every Pi4 file deployment must be persisted to `/media/root-ro`. The Pi4 runs a read-only overlay filesystem — all changes land in RAM and are lost on reboot unless explicitly copied to SD. This applies to ALL paths: `/home/pi/`, `/etc/udev/rules.d/`, `/etc/systemd/system/`, and any other system path. A deploy is not complete and must not be marked DEPLOYED until the file exists in `/media/root-ro/<same relative path>` with md5 verified. (Confirmed failure S63: `99-iris-teensy.rules` deployed to `/etc/udev/rules.d/` RAM only, never persisted to SD, lost on reboot 2026-05-28, caused 8-hour display outage.)

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

---

## Hard Rule: Source-of-Truth Before Any Technical Claim

All factual claims about IRIS hardware, firmware, pin assignments, serial
protocol, deploy state, file paths, ports, models, or sensors must be
verified against the live repo via filesystem MCP in every session. Memory
and prior conversation context are not authoritative.

Never reference `/dev/ttyACM*` by number. Use `/dev/ttyIRIS_EYES` or
`/dev/ttyIRIS_SERVO`.

Never claim a file is REPO-ONLY, DEPLOYED, or VERIFIED without reading the
current `HANDOFF_CURRENT.md` deploy state list this session.

Before writing driver code for any sensor, button, display, or hardware
feature, confirm with the user that the hardware is physically installed.

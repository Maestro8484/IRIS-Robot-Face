# Handoff: Browser Claude Chat -> Claude Desktop + Code on SuperMaster

**Generated:** 2026-05-16
**From:** Browser-based Claude Chat (claude.ai, Sonnet 4.6)
**To:** Claude Desktop GUI + Claude Code on SuperMaster Windows PC
**Project:** IRIS Robot Face
**Repo:** C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face

---

## What This Handoff Is

A planning session was completed in browser-based Claude Chat. The session produced a
structured codebase review plan for the IRIS project. That plan is now saved in the local
repo and ready for execution on SuperMaster via Claude Desktop and Claude Code.

This file gives Claude Desktop the full context it needs to continue without the browser
chat history.

---

## What Was Decided in the Browser Session

### 1. Review Approach

Opus 4.7 was selected as the review model based on its ability to flag missing information
rather than fill gaps with plausible-sounding answers, and its resistance to three-way
desync errors (a known IRIS failure mode documented in iris_issue_log.md).

### 2. Workflow Split (confirmed)

This split is consistent with WORKFLOW_RULE.md and was reconfirmed in the browser session:

- Claude Desktop Chat (Opus 4.7): reads repo via filesystem MCP, produces findings,
  recommends specific changes with diffs or full file outputs
- Claude Code (Sonnet 4.6): receives approved findings as a task spec, implements only
  what was approved, nothing more
- Opus 4.7 is NOT needed in Claude Code for implementation -- Sonnet 4.6 is correct there

### 3. Review Plan File

A file called REVIEW_PLAN.md was generated in the browser session and should now be
located at:

```
C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face\review\REVIEW_PLAN.md
```

If the review/ subfolder does not exist yet, create it before proceeding.

The REVIEW_PLAN.md contains:
- Pre-flight instructions listing all source files to read before starting
- Six sequential audit tasks covering the full IRIS stack
- Output file paths for each task (all go to review/ subfolder)
- A post-task master summary instruction

### 4. Six Audit Tasks (summary)

| Task | Scope | Output file |
|---|---|---|
| 1 | Pi4 pipeline call paths, exception propagation, state mutation, router bypass | review/findings_session_1_pipeline.md |
| 2 | Config keys vs _OVERRIDABLE, chown gaps, stale orphan keys, persistence pattern | review/findings_session_2_config.md |
| 3 | Emotion system matrix across all 5 locations, MOUTH_MAP, LED coverage, AMUSED | review/findings_session_3_emotions.md |
| 4 | Intent router patterns vs spec, false positives, fail-open, log field gaps | review/findings_session_4_router.md |
| 5 | 10 failure scenario trace-throughs, auto-recovery map, degradation paths | review/findings_session_5_failures.md |
| 6 | Doc drift S45-S49, Chatterbox refs, constants cross-ref, protected file audit | review/findings_session_6_drift.md |

After all six tasks: master summary at review/findings_MASTER.md with top-5 ranked
findings and recommended implementation sequence.

---

## How to Execute -- Two Options

### Option A: Claude Code (autonomous, no input between tasks)

This is the recommended option. Claude Code runs all six tasks sequentially without
waiting for input.

Step 1: Confirm review/REVIEW_PLAN.md exists in the repo.

Step 2: Set Claude Code model to Opus 4.7:
```
claude config set model claude-opus-4-7
```

Step 3: Open Claude Code in the repo directory and send this single prompt:
```
Read review/REVIEW_PLAN.md and execute it exactly as written.
```

Claude Code will read all source files listed in the pre-flight section, work through
all six tasks, write all six findings files and the master summary, then stop.
No further input required.

Step 4: After completion, switch model back to Sonnet 4.6 for implementation work:
```
claude config set model claude-sonnet-4-6
```

### Option B: Claude Desktop Chat (Opus 4.7, manual per-task)

Use this if you want to review findings after each task before the next one runs,
or if you want to course-correct mid-audit.

Step 1: Open Claude Desktop. Switch model to Opus 4.7.

Step 2: Start a new conversation. Send this prompt:
```
Read the file at C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face\review\REVIEW_PLAN.md
using the filesystem MCP. Then execute Task 1 only. Write findings to
review/findings_session_1_pipeline.md. Stop after Task 1 and wait.
```

Step 3: Review the findings file. Then send: "Proceed to Task 2." Continue per task.

---

## Context Claude Desktop Needs

The following documents are in the local repo and give full project context.
Claude Desktop can read all of these via filesystem MCP without any pasting.

Core context files (read these if broader context is needed):
- CLAUDE.md -- session rules, hard constraints, deploy gates, protected files
- IRIS_ARCH.md -- full architecture, pins, constants, deploy commands
- IRIS_CONFIG_MAP.md -- every configurable value mapped to file and web UI
- SNAPSHOT_LATEST.md -- current verified machine state and active issues
- HANDOFF_CURRENT.md -- current session startup state and next-work pointer
- ROADMAP.md -- all forward-looking tasks with full spec
- CHANGELOG.md -- completed sessions S1 through S49
- iris_issue_log.md -- structured bug/fix record

Review files (generated by the browser session):
- review/REVIEW_PLAN.md -- the full audit task list (primary handoff artifact)
- review/findings_session_*.md -- audit output (written by Claude Code during execution)
- review/findings_MASTER.md -- ranked summary (written last by Claude Code)

---

## Current IRIS System State (as of browser session)

Pulled from SNAPSHOT_LATEST.md (S49, 2026-05-06):

| System | Status |
|---|---|
| Pi4 192.168.1.200 | Operational. assistant.py, intent_router.py, iris_web.py deployed and persisted. |
| GandalfAI 192.168.1.3 | Operational. iris + iris-kids models rebuilt (S48) with PT-001 few-shot examples. |
| Teensy 4.1 | Operational. Eye movement suspended during TTS (S36). |
| TTS | Kokoro primary (port 8004), Piper fallback (port 10200). |
| Web UI | Operational. S49: log tab reworked, chat verbatim mode, /api/chat fix. |

Pending verifications (live behavior not yet confirmed):
- S49 web UI changes (log tab, verbatim chat, response cleaning)
- PT-001 adversarial examples (live adversarial testing pending)
- RD-002 AMUSED emotion (live behavior verification pending)

Active issues per SNAPSHOT_LATEST.md:
- LOW: "stop" Whisper hallucination (residual -- RD-001 Option 1 deployed but partial)
- MED: LLM personality inconsistency (three-way desync risk, recurring)
- LOW: duplicate sleep log at /home/pi/iris_sleep.log vs /home/pi/logs/iris_sleep.log

---

## Hard Constraints (from CLAUDE.md -- do not relax)

- Local repo is the only source of truth. No GitHub push unless explicitly requested.
- No Pi4 or GandalfAI edits unless user says DEPLOY.
- Show diff, wait for approval before writing any file.
- Do not touch protected files without explicit instruction:
  iris_config.json, alsa-init.sh, src/TeensyEyes.ino, src/eyes/EyeController.h
- The review/ tasks are READ-ONLY. No source file modifications during the audit.
- One task per Claude Code session for any implementation work that follows the audit.

---

## Next Steps After Review Completes

1. Read review/findings_MASTER.md
2. Prioritize findings with the user (human approval required)
3. For each approved finding, create a scoped task spec
4. Hand task spec to Claude Code (Sonnet 4.6) for implementation -- one task per session
5. Follow standard CLAUDE.md session open/close protocol for each implementation session
6. Update SNAPSHOT_LATEST.md, HANDOFF_CURRENT.md, CHANGELOG.md after each implemented batch

---

## Reference: Browser Chat Session Summary

The browser chat session (claude.ai, Sonnet 4.6, 2026-05-16) covered:

- Whether and when Opus 4.7 is appropriate for IRIS code review (yes -- for cross-file
  reasoning, adversarial critique, and interdependency analysis)
- Why Opus 4.7 is NOT needed in Claude Code for implementation (Sonnet 4.6 is correct
  there once findings are pre-defined)
- The correct model split: Opus 4.7 for review/planning, Sonnet 4.6 for implementation
- Generation of REVIEW_PLAN.md (six audit tasks, pre-flight file list, output paths)
- How to run the plan with zero input between tasks via Claude Code
- This handoff file

The browser session did not modify any IRIS source files. No deploys occurred.
The only artifact produced is review/REVIEW_PLAN.md (already in repo) and this file.

---

*End of handoff. Save this file locally and open in Claude Desktop to continue.*

## CDX-1: ROADMAP and iris_issue_log Audit

### Summary
Audited `ROADMAP.md` and `docs/iris_issue_log.md` against the current repo snapshot, handoff, operating rules, and S60-onward changelog entries. Removed or updated stale active roadmap entries, corrected issue-log status lines without deleting history, and appended the Codex session demarcation plus CDX-1 changelog entry.

### Files Changed
- `ROADMAP.md` - removed resolved or superseded active entries RD-002, HW-001, and HW-003; updated stale active statuses for RD-001, RD-006, and RD-007.
- `docs/iris_issue_log.md` - updated status lines for RD-002, single-word STT/pre-STT intercept, and local Piper TTS routing.
- `CHANGELOG.md` - added the Codex secondary-coder session demarcation and CDX-1 entry.

### Files NOT Changed (considered but skipped)
- `pi4/*` - not needed for documentation audit.
- `servo_teensy40/*` - not needed for CDX-1 scope.
- HW-004 content - left BLOCKED as directed.
- RD-003 content - left Open as directed.

### Verification Steps Performed
- Read `SNAPSHOT_LATEST.md`, `HANDOFF_CURRENT.md`, `CLAUDE.md`, `ROADMAP.md`, and `docs/iris_issue_log.md`.
- Cross-checked active ROADMAP items and open issue-log entries against S60-onward `CHANGELOG.md`.
- Confirmed no RD/HW identifiers were renumbered and no issue-log entries were deleted.

### Open Questions for Claude Code Review
None - straightforward execution.

### Recommended Next Action
Claude Code should spot-check RD-001, RD-006, and RD-007 status wording against the current roadmap priorities.

### Git Commit
`f3d8b43` - `CDX-1: ROADMAP + issue log audit pass`

## CDX-2: CHANGELOG Backfill Audit

### Summary
Compared recent git history against `CHANGELOG.md` from S60 onward and appended missing changelog coverage without editing existing entries. Sparse entries were marked as sparse records when `SNAPSHOT_LATEST.md` did not recover details.

### Files Changed
- `CHANGELOG.md` - added backfill entries for S60, S62b, S68b, unlabeled sysmap tracking, and the CDX-2 audit note.

### Files NOT Changed (considered but skipped)
- Existing `CHANGELOG.md` entries - left unchanged per append-only constraint.
- `SNAPSHOT_LATEST.md` - read as source of truth only.

### Verification Steps Performed
- Read first 120 lines of `SNAPSHOT_LATEST.md`.
- Read full `CHANGELOG.md`.
- Compared `git log --oneline -80` labels against changelog labels.
- Confirmed every S60-onward git-log entry now has changelog coverage or sparse-record notation.

### Open Questions for Claude Code Review
None - straightforward execution.

### Recommended Next Action
Claude Code should review sparse-record backfills if more session notes are available outside the repo.

### Git Commit
`2bfcac6` - `CDX-2: CHANGELOG backfill`

## CDX-3: sysmap.json vs IRIS_ARCH.md Consistency Pass

### Summary
Cross-checked `docs/sysmap.json` and `IRIS_ARCH.md` for pin, constant, port, IP, and command drift. Applied non-controversial syncs verified against source files and current repo state, then recorded the mismatch report in `CHANGELOG.md`.

### Files Changed
- `docs/sysmap.json` - updated tracked-status metadata, added missing Teensy 4.0 command strings, corrected `SR_FRAME_MS` to 155, and removed stale touch1/touch2 behavior entries.
- `IRIS_ARCH.md` - updated Teensy 4.0 serial-command wording, removed stale touch-event phrasing, corrected `SR_FRAME_MS`, and refreshed current `core/config.py` constants.
- `CHANGELOG.md` - added CDX-3 entry and mismatch report.

### Files NOT Changed (considered but skipped)
- `pi4/core/config.py` - read for constants, not changed.
- `src/sleep_renderer.h` - read for `SR_FRAME_MS`, not changed.
- `servo_teensy40/teensy40_base_mount/*` - spot-checked command and pin details, not changed.

### Verification Steps Performed
- Read first 80 lines of `SNAPSHOT_LATEST.md`.
- Read `CLAUDE.md`, full `docs/sysmap.json`, and relevant/full `IRIS_ARCH.md` sections.
- Spot-checked `pi4/core/config.py`, `src/sleep_renderer.h`, and Teensy 4.0 firmware headers.
- Validated `docs/sysmap.json` with PowerShell `ConvertFrom-Json`.

### Open Questions for Claude Code Review
- Confirm that tracking `docs/sysmap.json` remains the intended direction. The bundle still called it local-only/gitignored, but local commit `f740844` explicitly made it tracked.

### Recommended Next Action
Claude Code should review the sysmap tracking-status note first, then accept or adjust the architecture wording.

### Git Commit
`2cfe6ef` - `CDX-3: sysmap.json + IRIS_ARCH.md consistency`

## CDX-4: README.md Audit (root + servo_teensy40)

### Summary
Audited the root README and servo Teensy README for stale hardware, model, serial, TTS, and firmware-structure references. Applied surgical documentation corrections while leaving the root README historical changelog section intact.

### Files Changed
- `README.md` - added Teensy 4.0 base-mount context, POST diagnostic, persistent USB identity, current Kokoro/Piper wording, current sleep animation, Teensy 4.0 gesture serial block, and Web UI corrections.
- `servo_teensy40/README.md` - updated TS40-S1/TS40-S2 status, HW-004 sensor note, wiring-doc reference, and modular file list.
- `CHANGELOG.md` - added CDX-4 entry.

### Files NOT Changed (considered but skipped)
- Root `README.md` changelog section - intentionally left unchanged because `CHANGELOG.md` is canonical.
- Firmware/source files - read only, no README task changes required.

### Verification Steps Performed
- Read first 80 lines of `SNAPSHOT_LATEST.md`.
- Read full root `README.md`, full `servo_teensy40/README.md`, `CLAUDE.md`, and relevant `IRIS_ARCH.md` architecture/pin sections.
- Searched for stale patterns including ESP32 servo controller, APDS-9960, touch3/pin 15, MAX7219, `/dev/ttyACM*`, stale model names, and stale TTS chain.

### Open Questions for Claude Code Review
None - straightforward execution.

### Recommended Next Action
Claude Code should verify README wording after HW-004 replacement arrives and TS40 firmware is flashed.

### Git Commit
`31a1599` - `CDX-4: README.md audit — root + servo_teensy40`

## CDX-5: pytest Stubs for Pi4 Python Modules

### Summary
Added repo-only pytest stubs for the Pi4 Python modules named in the bundle, with shared fixtures that block external network calls and mock serial, UDP, audio, ALSA/subprocess, and fake config paths. No `pi4/*` source files were modified.

### Files Changed
- `CHANGELOG.md` - appended CDX-5 entry with verification result and known failing test.
- `pytest.ini` - added pytest discovery config scoped to the CDX-5 stubs.
- `requirements-dev.txt` - added pinned `pytest` and `pytest-mock`.
- `tests/README.md` - added SuperMaster run instructions.
- `tests/__init__.py` - added test package marker.
- `tests/conftest.py` - added shared hardware-free fixtures and network blocker.
- `tests/test_base_mount_bridge.py` - added gesture dispatch, mute, LISTEN/UDP, health-line, and invalid-gesture tests.
- `tests/test_intent_router.py` - converted existing standalone router script into pytest coverage.
- `tests/test_iris_post.py` - added mocked POST LED/verdict/gesture-required tests.
- `tests/test_tts_spoken_numbers.py` - added numeric normalization tests.

### Files NOT Changed (considered but skipped)
- `pi4/hardware/base_mount_bridge.py` - skipped by CDX-5 constraint: tests only.
- `pi4/core/intent_router.py` - skipped by CDX-5 constraint: tests only.
- `pi4/services/tts.py` - skipped by CDX-5 constraint even though negative-number coverage found a behavior gap.
- `pi4/iris_post.py` - skipped by CDX-5 constraint: tests only.
- `tests/test_integration_smoke.py` - left as legacy standalone script; `pytest.ini` scopes collection to CDX-5 pytest stubs.

### Verification Steps Performed
- Read the full Codex bundle, `pi4/hardware/base_mount_bridge.py`, `pi4/core/intent_router.py`, `pi4/services/tts.py`, and `pi4/iris_post.py`.
- Read existing `tests/test_intent_router.py` and `tests/test_integration_smoke.py` before editing test structure.
- Installed pinned dev requirements with `python -m pip install -r requirements-dev.txt`.
- Ran `python -m pytest tests/ -v`: 66 passed, 1 failed.
- Confirmed no tracked `pi4/*` source or protected files were staged for CDX-5.

### Open Questions for Claude Code Review
- `services.tts.spoken_numbers("-42")` currently returns `-forty two`, not `negative forty two`; review whether to update the regex to pass signed integers into `_int_to_words`.
- `tests/test_integration_smoke.py` remains a top-level standalone script with import-time execution; review whether to convert it in a future task.

### Recommended Next Action
Claude Code should review the negative-number TTS failure first, then decide whether to convert or retire the legacy integration smoke script.

### Git Commit
`3205c96` - `CDX-5: pytest stubs for Pi4 Python modules`

## CODEX SESSION CLOSE — 2026-05-29

### Tasks Completed
- CDX-1
- CDX-2
- CDX-3
- CDX-4
- CDX-5

### Tasks Attempted But Not Completed
None.

### Tasks Skipped
None.

### Files Touched Across Session
- `CHANGELOG.md`
- `ROADMAP.md`
- `docs/iris_issue_log.md`
- `docs/sysmap.json`
- `IRIS_ARCH.md`
- `README.md`
- `servo_teensy40/README.md`
- `pytest.ini`
- `requirements-dev.txt`
- `tests/README.md`
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/test_base_mount_bridge.py`
- `tests/test_intent_router.py`
- `tests/test_iris_post.py`
- `tests/test_tts_spoken_numbers.py`

### Protected Files Verification
CONFIRMED - none touched. `git diff --name-only f3d8b43^..HEAD -- iris_config.json alsa-init.sh src/TeensyEyes.ino src/eyes/EyeController.h` returned no paths.

### Git Log This Session
```text
f3d8b43 CDX-1: ROADMAP + issue log audit pass
2bfcac6 CDX-2: CHANGELOG backfill
2cfe6ef CDX-3: sysmap.json + IRIS_ARCH.md consistency
31a1599 CDX-4: README.md audit — root + servo_teensy40
3205c96 CDX-5: pytest stubs for Pi4 Python modules
```

### State Of Tree At Close
```text
 M CLAUDE.md
 M PRIMER.md
?? .codex/hooks.json
?? .codex/hooks/post_tool_use_build_check.py
?? .codex/hooks/session_start.py
?? "docs/S20260521_0006  IRIS1-mockup.png"
?? docs/handoffs/CODEX_DELIVERABLE_2026-05-29.md
?? docs/servo_teensy40_wiring_onenote.html
?? review/HANDOFF_TO_DESKTOP.md
?? review/REVIEW_PLAN.md
?? review/findings_MASTER.md
?? review/findings_esp32_bringup.md
?? review/findings_session_1_pipeline.md
?? review/findings_session_2_config.md
?? review/findings_session_3_emotions.md
?? review/findings_session_4_router.md
?? review/findings_session_5_failures.md
?? review/findings_session_6_drift.md
?? review/postmortem_S65_fuckups.md
?? servo_teensy40/teensy40_base_mount/teens40-90centerCode.ino.bak
?? servo_teensy40/teensy40_base_mount/teensy40_base_mount.code-workspace
?? src/IRIS-Robot-Face-teensy4.1-eyes-mouth.code-workspace
```

### Recommended Claude Code Review Order
1. CDX-5 - review the only failing test first: `spoken_numbers("-42")` negative-number handling.
2. CDX-3 - review architecture/sysmap synchronization and confirm tracked `docs/sysmap.json` remains intended.
3. CDX-1 - review ROADMAP and issue-log status flips because they shape future planning.
4. CDX-2 - review changelog backfills for historical accuracy.
5. CDX-4 - review README wording last because it is lowest risk and mostly public-facing documentation polish.

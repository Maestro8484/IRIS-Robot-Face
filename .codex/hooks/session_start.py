#!/usr/bin/env python3
"""
IRIS SessionStart Hook — Load structured status + snapshot into context.

Fires once at the start of every Claude Code session.
1. Reads IRIS_STATUS.json (machine-readable git/Pi4/Teensy state).
2. Reads SNAPSHOT_LATEST.md (session handoff, first 80 lines).

Run .\scripts\iris_status.ps1 from project root before starting a session
to get fresh Pi4 state. If IRIS_STATUS.json is absent, prints a reminder
and continues to load the snapshot.
"""

import glob
import json
import os
import sys


def load_status(project_root: str) -> None:
    status_path = os.path.join(project_root, "IRIS_STATUS.json")
    if not os.path.exists(status_path):
        print("[IRIS] IRIS_STATUS.json not found. Run: .\\scripts\\iris_status.ps1", flush=True)
        return

    try:
        with open(status_path, "r", encoding="utf-8") as f:
            s = json.load(f)
    except Exception as e:
        print(f"[IRIS] Failed to read IRIS_STATUS.json: {e}", flush=True)
        return

    git  = s.get("git", {})
    pi4  = s.get("pi4", {})
    teen = s.get("teensy", {})
    gen  = s.get("generated", "unknown")

    dirty_warn = " *** DIRTY — STOP AND CHECK ***" if git.get("dirty") else " clean"
    untracked  = git.get("untracked", [])
    ut_str     = f" | untracked: {', '.join(untracked)}" if untracked else ""

    print("[IRIS STATUS]", flush=True)
    print(f"  Generated : {gen}", flush=True)
    print(f"  Branch    : {git.get('branch', 'unknown')}", flush=True)
    print(f"  Commit    : {git.get('commit', '?')} — {git.get('message', '')}", flush=True)
    print(f"  Working   :{dirty_warn}{ut_str}", flush=True)
    print(f"  Last build: {teen.get('last_build', 'unknown')}", flush=True)

    reach = pi4.get("reachable")
    if reach is True:
        print(
            f"  Pi4       : assistant={pi4.get('assistant')} "
            f"iris_web={pi4.get('iris_web')} "
            f"uptime={pi4.get('uptime')}",
            flush=True,
        )
    elif reach == "skipped":
        print("  Pi4       : check skipped (-SkipPi4)", flush=True)
    else:
        print(f"  Pi4       : UNREACHABLE — {pi4.get('error', '')}", flush=True)

    print("", flush=True)


def load_snapshot(project_root: str) -> None:
    latest_path = os.path.join(project_root, "SNAPSHOT_LATEST.md")

    if os.path.exists(latest_path):
        target   = latest_path
        filename = "SNAPSHOT_LATEST.md"
    else:
        pattern   = os.path.join(project_root, "SNAPSHOT_*.md")
        snapshots = sorted(glob.glob(pattern))
        if not snapshots:
            print("[IRIS] No snapshot found. Run /snapshot.", flush=True)
            return
        target   = snapshots[-1]
        filename = os.path.basename(target)
        print(f"[IRIS] SNAPSHOT_LATEST.md missing — falling back to {filename}", flush=True)

    with open(target, "r", encoding="utf-8") as f:
        lines = f.readlines()

    MAX_LINES = 80
    truncated = len(lines) > MAX_LINES
    content   = "".join(lines[:MAX_LINES])

    print(f"[IRIS] Snapshot: {filename}", flush=True)
    print("=" * 70, flush=True)
    print(content, flush=True)
    if truncated:
        print(f"[IRIS] Truncated at {MAX_LINES} lines. Full file: {filename}", flush=True)
    print("=" * 70, flush=True)


def main():
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    load_status(project_root)
    load_snapshot(project_root)
    print("[IRIS] Context loaded. Proceed with the user's task.", flush=True)


if __name__ == "__main__":
    main()

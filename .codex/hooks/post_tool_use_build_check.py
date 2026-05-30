#!/usr/bin/env python3
"""
IRIS PostToolUse Hook — Firmware Build Check
Fires after any Write/Edit tool call. If the modified file is under src/,
runs `pio run` (compile only, no upload) and surfaces errors immediately.
Keeps Claude from stacking 10 edits on top of a broken build.
"""

import json
import os
import subprocess
import sys

def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only trigger on file write/edit tools
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)

    # Get the file path that was modified
    file_path = tool_input.get("file_path") or tool_input.get("path", "")

    # Only check firmware source files
    if not file_path:
        sys.exit(0)

    norm = file_path.replace("\\", "/")
    firmware_triggers = ["/src/", "platformio.ini"]
    if not any(t in norm for t in firmware_triggers):
        sys.exit(0)

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    print(f"\n[IRIS hook] src/ change detected in: {os.path.basename(file_path)}", flush=True)
    print("[IRIS hook] Running firmware build check (pio run, no upload)...", flush=True)

    result = subprocess.run(
        ["pio", "run"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=120
    )

    if result.returncode == 0:
        print("[IRIS hook] Build OK.", flush=True)
    else:
        print("[IRIS hook] BUILD FAILED — fix before continuing.\n", flush=True)
        # Surface the relevant error lines only
        lines = (result.stdout + result.stderr).splitlines()
        for line in lines:
            if any(k in line for k in ["error:", "Error:", "undefined", "fatal:", "note:"]):
                print(f"  {line}", flush=True)
        print("", flush=True)
        # Exit code 2 blocks the agent and surfaces the message
        sys.exit(2)

if __name__ == "__main__":
    main()

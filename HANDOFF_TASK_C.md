# IRIS Task C — implies_followup() Conversation-Active Extension
**Prepared:** 2026-04-15
**Depends on:** Task B complete (streaming deployed and confirmed working)
**Machine:** GandalfAI (repo edit) + Pi4 (SSH deploy)

---

## PRE-FLIGHT (output before touching anything)

```
Branch:             main  (git branch --show-current MUST output "main")
Last commit:        [hash + message]
Working tree:       [must be clean — if dirty STOP]
Task this session:  Extend the followup while-loop condition in assistant.py to stay open
                    when conversation history shows an active exchange, not only when the
                    last reply contains a question or trigger phrase.
Files to modify:    pi4/assistant.py
Files NOT touched:  pi4/services/llm.py, pi4/services/tts.py, pi4/hardware/*, pi4/core/*,
                    pi4/state/*, src/ (any firmware), iris_config.json, alsa-init.sh,
                    SNAPSHOT_LATEST.md (until /snapshot at session end)
Risk:               Low. Mic stays open one extra turn on non-game interactions.
                    Hard cap at FOLLOWUP_MAX_TURNS (unchanged) prevents runaway loops.
Rollback:           Revert the two-line change. Redeploy assistant.py.
```

Do not proceed until user confirms.

---

## WHY

`while implies_followup(reply)` exits as soon as IRIS replies with a declarative sentence
(no `?`, no trigger phrase). In 20 Questions and similar games, after IRIS's first reply
the loop condition fails, mic closes, pipeline returns to wakeword wait.

Fix: also stay open when conversation history shows an active exchange (>= 4 turns = 2
user + 2 assistant messages, meaning a real back-and-forth has started).

---

## STEP 1 — Read the current file

```powershell
Get-Content C:\IRIS\IRIS-Robot-Face\pi4\assistant.py
```

Locate the followup while loop. It looks like:

```python
            while implies_followup(reply) and _followup_turns < FOLLOWUP_MAX_TURNS and not _interrupted:
```

Note the exact indentation and context around it before editing.

---

## STEP 2 — Make the change

Find:
```python
            while implies_followup(reply) and _followup_turns < FOLLOWUP_MAX_TURNS and not _interrupted:
```

Replace with:
```python
            _conv_active = len(state.conversation_history) >= 4
            while (implies_followup(reply) or _conv_active) and _followup_turns < FOLLOWUP_MAX_TURNS and not _interrupted:
                _conv_active = len(state.conversation_history) >= 4
```

Notes:
- The second `_conv_active` assignment inside the loop keeps it current as history grows.
- `FOLLOWUP_MAX_TURNS` hard cap is unchanged — verify its value in the file before saving
  (should be 3 or similar).
- Preserve exact indentation of the original line.

---

## STEP 3 — Deploy to Pi4

```bash
# Write to Pi4 RAM
sshpass -p 'ohs' scp pi4/assistant.py pi@192.168.1.200:/home/pi/assistant.py

# Persist to SD
sshpass -p 'ohs' ssh pi@192.168.1.200 "
  sudo mount -o remount,rw /media/root-ro &&
  sudo cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py &&
  sudo mount -o remount,ro /media/root-ro"

# Verify md5
sshpass -p 'ohs' ssh pi@192.168.1.200 "
  md5sum /home/pi/assistant.py /media/root-ro/home/pi/assistant.py"

# Restart and confirm
sshpass -p 'ohs' ssh pi@192.168.1.200 "
  sudo systemctl restart assistant &&
  sleep 3 &&
  journalctl -u assistant -n 30 --no-pager"
```

Confirm `[INFO] Ready.` in journal before closing.

---

## STEP 4 — Live test

Start a 20 Questions game: "Let's play 20 questions."
- Confirm IRIS asks a question and then stays in the followup loop for subsequent turns
- Confirm the loop still hard-stops at FOLLOWUP_MAX_TURNS on a simple non-game interaction
  (say something like "what time is it" — should return to wakeword after max turns)

---

## SESSION END

1. State: what changed, what did NOT change, any loop runaway observed.

2. Commit and push (user confirmation required before push):
```bash
git add -A
git commit -m "feat: S17 Task C — conversation-active followup loop extension"
git push origin main
```

3. Run `/snapshot`. Update Section 14 — CHANGES THIS SESSION with Task C outcome.

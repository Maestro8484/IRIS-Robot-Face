# IRIS Task D — Phantom STT Gate Hardening
**Prepared:** 2026-04-15
**Depends on:** Task C complete (or can run independently after Task B)
**Machine:** GandalfAI (repo edit) + Pi4 (SSH deploy)

---

## PRE-FLIGHT (output before touching anything)

```
Branch:             main  (git branch --show-current MUST output "main")
Last commit:        [hash + message]
Working tree:       [must be clean — if dirty STOP]
Task this session:  Raise RMS silence gate from 400 to 700 and add Whisper hallucination
                    blacklist to suppress phantom "thank you" and similar triggers.
Files to modify:    pi4/assistant.py
Files NOT touched:  pi4/services/stt.py, pi4/services/llm.py, pi4/services/tts.py,
                    pi4/hardware/*, pi4/core/*, pi4/state/*, src/ (any firmware),
                    iris_config.json, alsa-init.sh,
                    SNAPSHOT_LATEST.md (until /snapshot at session end)
Risk:               RMS gate at 700 may cut quiet speakers (Mae, far-field use). If children's
                    voices get gated, reduce to 550. Observe first 2-3 uses with children.
Rollback:           Revert gate to 400, remove blacklist block. Redeploy assistant.py.
```

Do not proceed until user confirms.

---

## WHY

Whisper `large-v3-turbo` hallucinates common phrases ("thank you", "bye", etc.) on near-silence
audio that passes the `rms < 400` gate. This triggers spurious LLM calls and causes IRIS to
respond to nothing, which breaks conversation flow and wastes LLM cycles.

---

## STEP 1 — Read the current file

```powershell
Get-Content C:\IRIS\IRIS-Robot-Face\pi4\assistant.py
```

Locate both target sites:
1. The RMS gate check (`if rms < 400:`)
2. The line immediately after `print(f"[STT]  '{text}'", flush=True)` where the filter inserts

Note exact context around both sites before editing.

Also confirm whether `_text_norm` is already defined in the current file before the STT print.
If it is not, add `_text_norm = text.strip().lower()` before the blacklist block.

---

## CHANGE 1 — RMS gate

Find:
```python
            if rms < 400:
                print("[REC]  Near-silent (Whisper gate), ignoring", flush=True); show_idle_for_mode(leds); continue
```

Replace:
```python
            if rms < 700:
                print(f"[REC]  Below RMS gate ({rms:.0f} < 700), ignoring", flush=True); show_idle_for_mode(leds); continue
```

---

## CHANGE 2 — Hallucination blacklist

Find the line:
```python
            print(f"[STT]  '{text}'", flush=True)
```

Insert immediately after it (preserving indentation):
```python
            _text_norm = text.strip().lower()
            _WHISPER_HALLUCINATIONS = {
                "thank you", "thanks", "thank you very much", "thanks for watching",
                "you", "the", "bye", "bye bye", "goodbye", "see you next time",
                "please subscribe", ".", "", " ",
            }
            if _text_norm in _WHISPER_HALLUCINATIONS:
                print(f"[STT]  Hallucination filtered: '{text}'", flush=True)
                show_idle_for_mode(leds)
                continue
```

Note: if `_text_norm` is already defined earlier in the same block, do NOT redefine it here —
just use the existing variable in the `if _text_norm in` check and remove the first line above.

---

## STEP 2 — Deploy to Pi4

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

## STEP 3 — Live test

1. Trigger the wakeword, then stay silent for 2 seconds.
   - Journal should show `[REC] Below RMS gate` — no LLM call.
2. Trigger the wakeword and speak a real question normally.
   - Confirm it goes through to LLM normally.
3. If Mae or a child uses it in the next day, note whether their voice gets gated.
   - If gated, reduce threshold to 550 in a quick follow-up patch.

---

## SESSION END

1. State: what changed, what did NOT change, any false-positive gating observed.

2. Commit and push (user confirmation required before push):
```bash
git add -A
git commit -m "fix: S17 Task D — STT RMS gate 700 + Whisper hallucination blacklist"
git push origin main
```

3. Run `/snapshot`. Update Section 14 — CHANGES THIS SESSION with Task D outcome.
   If RMS gate needs tuning for children, note in Section 15 — PENDING HIGH.

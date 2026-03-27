# IRIS Robot Face — Claude Code Rules

## Long output
- Snapshots, full file dumps, large summaries → write to a .md file, then summarize inline.
- Never print large blocks of content as chat text; it will be truncated.

## Firmware rules
- Do NOT modify `TeensyEyes.ino` — upstream engine, off limits.
- After any firmware change: `pio run -t upload` → press PROG on Teensy → test serial at 115200.

## Eye editing workflow
1. Edit `resources/eyes/240x240/<eye>/config.eye`
2. Run `python resources/eyes/240x240/genall.py` to regenerate the `.h`
3. **Re-apply -15% pupil values** to any regenerated .h (nordicBlue, hazel, bigBlue) — config.eye not yet synced
4. PlatformIO Upload

## Pi4 persistence (overlayfs)
- SD is read-only. Always persist after SSH edits:
  ```bash
  sudo mount -o remount,rw /media/root-ro && cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py && sudo mount -o remount,ro /media/root-ro
  ```

## Serial protocol
- Pi4 → Teensy: `EMOTION:x`, `EYES:SLEEP`, `EYES:WAKE`, `EYE:n` (0–8)
- Teensy → Pi4: `FACE:1`, `FACE:0`

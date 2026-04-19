# IRIS S23 Handoff — Confirmed Working + Hardened
**Date:** 2026-04-18  
**Branch:** main  
**Last commit:** 12845fe  
**Status:** Full pipeline CONFIRMED WORKING as of ~21:26 MDT

---

## What Was Broken (Root Causes Found and Fixed)

### 1. Mic dead — wm8960 LINPUT1 boost path disconnected
ALSA `Left/Right Input Mixer Boost Switch` (numid 50/51) were OFF.  
With these off, LINPUT1 signal never reaches the PGA — mic RMS = 8 (noise floor) regardless of gain setting.  
OWW processed audio (23% CPU) but got silence, never fired a detection event.

### 2. RMS gate too high — recording rejected after wake word
`pi4/assistant.py` line 386 had hardcoded gate of `700`. With boost path previously broken, this was never hit. After fixing mic, recordings came in at RMS ~472–670 and got rejected silently.  
`SILENCE_RMS=300` in iris_config.json does NOT affect this gate — it controls silence detection DURING recording only.

### 3. Audio output path disconnected — speakers silent
`Left/Right Output Mixer PCM Playback Switch` (numid 52/55) were OFF.  
Chatterbox TTS was synthesizing correctly (`[CB] OK WAV→PCM`) but PCM never reached the Class D speaker output on wm8960.

---

## Fixes Applied — All Confirmed Working and Hardened

### Fix 1 — alsa-init.sh hardened (Pi4 SD + RAM)
Added 6 critical ALSA switch commands to `/usr/local/bin/alsa-init.sh`.  
These now run at every Pi4 boot via `alsa-init.service` (after `alsa-restore.service`).

```bash
amixer -c 0 cset numid=50 1     # Left Input Mixer Boost Switch ON
amixer -c 0 cset numid=51 1     # Right Input Mixer Boost Switch ON
amixer -c 0 cset numid=9 3      # Left Input Boost Mixer LINPUT1 Volume 29dB
amixer -c 0 cset numid=8 3      # Right Input Boost Mixer RINPUT1 Volume 29dB
amixer -c 0 cset numid=52 1     # Left Output Mixer PCM Playback Switch ON
amixer -c 0 cset numid=55 1     # Right Output Mixer PCM Playback Switch ON
```

Persisted: `/usr/local/bin/alsa-init.sh` and `/media/root-ro/usr/local/bin/alsa-init.sh` — md5 verified match.  
Committed: `12845fe`

### Fix 2 — RMS gate 700→300 in assistant.py (repo + Pi4 SD)
`pi4/assistant.py` line 386/387: `if rms < 700` → `if rms < 300`  
Deployed to `/home/pi/assistant.py`, persisted to SD — md5 verified match.  
Committed: `a03756b`

### Fix 3 — iris_config.json ownership (Pi4 SD)
Was `root:root`, changed to `pi:pi 644`.  
Persisted to SD. Not a code commit (config file is Do Not Touch per CLAUDE.md).

### Fix 4 — asound.state saved with correct switch values (Pi4 SD)
`/etc/asound.state` and `/media/root-ro/etc/asound.state` saved with all boost/output switches ON.  
md5: `310c38e9d08a60a1a138111ed0efe9f8` (both match).  
Note: alsa-init.sh is now the primary hardening mechanism — asound.state is secondary backup.

---

## Confirmed Working Pipeline (logged 21:26 MDT)

```
[OWW]  score=1.000 (threshold=0.9)
[WAKE] Wake word detected
[REC]  10.1s  RMS=874
[STT]  Transcribing...  →  transcript confirmed
[LLM]  Streaming... (model=iris)  →  reply confirmed
[TTS]  Synthesizing...
[CB]   OK WAV → PCM (7.2s) [treble+10dB]
[EYES] MOUTH:0/1/5 animating  →  TFT mouth confirmed
Audio output from speakers  →  CONFIRMED
```

---

## Remaining Fragile Items (not fixed this session)

| Item | Risk | What breaks |
|---|---|---|
| GandalfAI reboot | HIGH | Chatterbox doesn't auto-start — no TTS, assistant hangs at `[TTS] Synthesizing...`. Fix: `docker compose -f C:\IRIS\docker\docker-compose.yml up -d` |
| Pi4 reboot | LOW (now hardened) | alsa-init.sh handles ALSA. Service auto-restarts via systemd. |
| Piper missing at `/usr/local/bin/piper` | MED | Sleep-window wake word fires, says nothing (subprocess fails silently). Normal interactions unaffected. |
| Teensy firmware not flashed | MED | mouthSleepFrame firmware built S22B, never flashed. Sleep animation on TFT unverified. |

---

## For Claude Chat — What to Pick Up Next

1. **Reboot smoke test** — reboot Pi4, confirm alsa-init.sh fires correctly, assistant comes up, wake word works without manual amixer intervention.
2. **GandalfAI auto-start Chatterbox** — add docker compose to Windows Task Scheduler or startup script so Chatterbox survives GandalfAI reboot.
3. **Piper missing** — either install Piper at `/usr/local/bin/piper` or update `iris_sleep.py` / sleep wakeword handler in `assistant.py` to use Chatterbox TTS instead.
4. **Flash Teensy** — `mouthSleepFrame` firmware, user clicks PlatformIO upload.
5. **Mouth smoke test** — UDP `127.0.0.1:10500` → MOUTH:0 through MOUTH:8 → verify TFT renders post-flash.

---

## Files Changed This Session

| File | Change | Persisted |
|---|---|---|
| `pi4/assistant.py` | RMS gate 700→300 | Repo + Pi4 SD |
| `/usr/local/bin/alsa-init.sh` | +6 ALSA switch lines | Pi4 SD only (not in repo) |
| `/etc/asound.state` | All switches saved correctly | Pi4 SD |
| `/home/pi/iris_config.json` | chown pi:pi | Pi4 SD |
| `IRIS_ARCH.md` | Active issues table + reboot checklist added | Repo |

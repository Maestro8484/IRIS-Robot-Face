<!-- Short session-start handoff only. Do not expand. Operational rules are in CLAUDE.md. -->

# IRIS Handoff — Current

## Session Startup Order

1. `git status` — branch must be `main`; tree must be clean.
2. Read `CLAUDE.md` — operating rules and hard constraints.
3. Read `SNAPSHOT_LATEST.md` — verified machine state and active issues.
4. Read this file — next-work pointer.
5. Read `IRIS_ARCH.md` — only when architecture, pins, services, or deploy details are needed.

## Source of Truth

`C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face`

GitHub is a secondary mirror. Local state outranks it until explicitly synced.

## Production Baseline

| System | State |
|---|---|
| Pi4 | Operational — assistant.py, intent_router.py, iris_web.py deployed and persisted. |
| GandalfAI | Operational — gemma3:27b-it-qat, Kokoro TTS (Docker port 8004), iris model current. |
| Teensy 4.1 | Operational — eye movement suspended during TTS. |
| STT / TTS | Whisper (GandalfAI) / Kokoro primary, Piper fallback (Wyoming port 10200). |
| Wakeword | `hey_jarvis` (production). Experimental wakewords require explicit user approval, live Pi4 state confirmation, clean process restart, and one-model-at-a-time testing. Failed experiment names are in `CHANGELOG.md`. |

## Navigation

- `SNAPSHOT_LATEST.md` — current verified state, active issues, last session changes.
- `ROADMAP.md` — all forward-looking tasks with full spec per item.
- `CHANGELOG.md` — completed sessions and batches.

## Deployment Gates

- Pi4 and GandalfAI mutations require explicit user authorization.
- GandalfAI model rebuilds require explicit `DEPLOY`.
- Pi4 persistence: direct `/media/root-ro` remount only — see `CLAUDE.md`.

## Next Work

PT-001 DEPLOYED (S48): few-shot adversarial examples in iris_modelfile.txt + iris-kids_modelfile.txt. Both models rebuilt on GandalfAI. Verification (live adversarial testing) pending.
RD-002 (AMUSED): Pi4 DEPLOYED — config.py, led.py, iris_web.html persisted + md5 verified, assistant restarted. Firmware upload (src/main.cpp) pending user PlatformIO action. iris-kids model rebuild pending (ollama create iris-kids on GandalfAI).
RD-001 (STOP pre-STT intercept): next priority. See `ROADMAP.md`.

---

## S48 — NUM_PREDICT Removal + PT-001 Few-Shot Adversarial Examples

**Status:** Task 1 DEPLOYED+VERIFIED. Task 2 REPO-ONLY (main modelfile only).

**Changes:**
- `/home/pi/iris_config.json` — `NUM_PREDICT: 200` removed. Persisted to SD (md5 match). assistant.py restarted — `[INFO] Ready.` Tiered classifier now controls response length.
- `ollama/iris_modelfile.txt` — PT-001 few-shot block (8 examples) added after ANGRY rule, before NEVER say block.

**Model rebuild:** DEPLOYED — iris and iris-kids rebuilt on GandalfAI.

**Rollback (iris_modelfile.txt):**
```bash
git checkout -- ollama/iris_modelfile.txt
# Then rebuild: cd C:\IRIS\IRIS-Robot-Face && git pull && ollama create iris -f "C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt"
```

---

## S47 — RD-002 AMUSED Emotion — Local Repo Complete

**Status:** Pi4 DEPLOYED (config.py, led.py, iris_web.html — md5 verified, assistant active). Firmware upload pending. iris-kids model rebuild pending.

**Commit:** 734149a (pushed 2026-05-03)

**Changes (local only):**
- `pi4/core/config.py` — AMUSED added to VALID_EMOTIONS and MOUTH_MAP (→ index 2, smirk)
- `pi4/hardware/led.py` — AMUSED: sinusoidal breathe, amber [255,160,0], floor=10 peak=80 period=1.5s gamma=1.8 duration=3s (special case in show_emotion)
- `src/main.cpp` — AMUSED added to EmotionID enum, emotionTable, parseEmotion
- `pi4/iris_web.html` — AMUSED button added to Emotion Test grid
- `ollama/iris-kids_modelfile.txt` — AMUSED added to valid emotion list

**Deploy when authorized:**
- Copy `pi4/core/config.py`, `pi4/hardware/led.py`, `pi4/iris_web.html` to Pi4 RAM + SD layers; restart assistant service
- Upload `src/main.cpp` firmware via PlatformIO (user action)

**Rollback:**
```bash
git checkout -- pi4/core/config.py pi4/hardware/led.py pi4/iris_web.html src/main.cpp
# Then redeploy previous Pi4 files and reflash prior firmware if already deployed/uploaded
```

---

## S46 — WoL Acknowledgement Beep — Deployed

**Status:** Complete and deployed to Pi4.

**Commit:** `2e96703` — S46: Add WoL acknowledgement beep (play_wol_beep)

**Deployment:**
- `pi4/assistant.py` copied to `/home/pi/assistant.py`, persisted to `/media/root-ro/home/pi/assistant.py`
- `pi4/hardware/audio_io.py` copied to `/home/pi/hardware/audio_io.py`, persisted to `/media/root-ro/home/pi/hardware/audio_io.py`
- MD5 verified: RAM and SD layers match for both files
- `assistant` service restarted — `active (running)`, `[INFO] Ready.` confirmed

**Behavior added:**
- When GandalfAI is offline and a WoL packet is sent, an ascending 2-tone beep (660 Hz → 880 Hz, ~360 ms) plays immediately on Pi4 speakers
- No beep when GandalfAI is already up
- `ensure_gandalf_up` gains optional `pa=None` parameter; both call sites pass `pa`

**Rollback:**
```bash
sudo cp /home/pi/assistant.py.s46bak /home/pi/assistant.py
sudo cp /home/pi/hardware/audio_io.py.s46bak /home/pi/hardware/audio_io.py
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
sudo cp /home/pi/hardware/audio_io.py /media/root-ro/home/pi/hardware/audio_io.py
sudo chown pi:pi /media/root-ro/home/pi/assistant.py /media/root-ro/home/pi/hardware/audio_io.py
sync && sudo mount -o remount,ro /media/root-ro
sudo systemctl restart assistant
```

---

## RD-001 Option 1 — Deployed

**Status:** Complete and deployed to Pi4.

**Commit:** `54d576c` — Add main-loop STOP phrase gate

**Deployment:**
- `pi4/assistant.py` was copied to Pi4 runtime path: `/home/pi/assistant.py`
- File was persisted to SD via: `/media/root-ro/home/pi/assistant.py`
- MD5 verification confirmed runtime and persisted copies matched.
- `assistant` service was restarted.
- Runtime file confirmed to contain "Main-loop STOP phrase".

**Behavior added:**
- Main loop now checks `STOP_PHRASES` after Whisper transcript normalization and before router/hallucination handling.
- Matching is boundary-aware:
  - exact STOP phrase match, or
  - STOP phrase followed by a space
- Avoids false matches such as "stopwatch", "quietly", and "cancelled".

**Known limitation:**
- This does not fix cases where Whisper hallucinates "stop" into unrelated text.
- True pre-STT abort handling still requires a future local keyword spotting/lightweight local ASR task.

**Runtime status:**
- Pi4 is live on `assistant.py` from commit `54d576c`.
- Verbal testing still pending.

**Test checklist:**
- wakeword -> "stop" should return to idle
- wakeword -> "stop talking" should return to idle
- wakeword -> "quiet please" should return to idle
- wakeword -> "cancel that" should return to idle
- wakeword -> "stopwatch" should NOT trigger STOP gate
- wakeword -> "turn red" should continue normal routing
- wakeword -> "tell me a joke" should continue normal routing

**Rollback:**
```bash
sudo cp /tmp/assistant.py.bak /home/pi/assistant.py
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
sudo chown pi:pi /media/root-ro/home/pi/assistant.py
sudo chmod 644 /media/root-ro/home/pi/assistant.py
sync && sudo mount -o remount,ro /media/root-ro
sudo systemctl restart assistant
```

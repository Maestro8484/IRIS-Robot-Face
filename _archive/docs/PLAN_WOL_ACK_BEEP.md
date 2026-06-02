# IRIS GandalfAI Wake Acknowledgement Plan

## 1. Pre-flight

- **Branch:** main
- **Last commit:** 50b4e52 Update handoff for RD-001 deploy
- **Working tree:** Staged renames only (docs reorganization), no source changes
- **Files read:**
  - `pi4/assistant.py` (full)
  - `pi4/hardware/audio_io.py` (full)
  - `docs/iris_issue_log.md` (grep filtered to GandalfAI/WoL/TTS/sleep entries)
- **Files intentionally not read:**
  - `pi4/services/tts.py` — not needed; TTS is confirmed GandalfAI-dependent
  - `pi4/core/config.py` — no config flag proposed at this time
  - `IRIS_ARCH.md` — WoL and role tables already clear from assistant.py
  - README, old handoffs, firmware, unrelated sources

---

## 2. Current Flow

```
1. wakeword / button press
      wait_for_wakeword_or_button() in services/wakeword.py

2. Sleep-mode path (if /tmp/iris_sleep_mode exists):
      _do_wake(teensy, leds)               <- eyes wake, LED idle
      ensure_gandalf_up(leds)              <- WoL if needed, poll loop
      synthesize(greeting)                 <- Kokoro TTS on GandalfAI
      play_pcm_speaking(...)               <- audio out

3. Normal path (no sleep file):
      ensure_gandalf_up(leds)              <- WoL if needed, poll loop
      play_beep(pa)                        <- 880 Hz, 200 ms beep
      record_command(mic, ...)             <- record user speech
      transcribe(raw)                      <- Whisper STT on GandalfAI
      stream_ollama(...)                   <- gemma3 LLM on GandalfAI
      synthesize(reply)                    <- Kokoro TTS on GandalfAI
      play_pcm_speaking(...)               <- audio out
```

**`ensure_gandalf_up(leds)` internals:**
- Calls `gandalf_is_up()`: TCP connect to `GANDALF:OLLAMA_PORT` (3 s timeout)
- If offline: sends WoL magic packet, starts orange LED pulse animation (background thread)
- Polls `gandalf_is_up()` every `WOL_POLL_INTERVAL` seconds until `WOL_BOOT_TIMEOUT`
- Returns `True` if up, `False` if timed out
- On timeout: LED error, 2 s sleep, return to idle — no audio

---

## 3. User Experience Gap

When IRIS hears the wakeword and GandalfAI is offline:

- IRIS becomes silent and unresponsive to the user
- The only feedback is an orange LED pulse animation
- No audio occurs until `ensure_gandalf_up` returns — the normal wake beep
  (`play_beep`) is **after** `ensure_gandalf_up`, so it never plays during the wait
- GandalfAI boot takes 60–120 s from cold
- From the user's perspective: IRIS heard the wakeword, did nothing, may
  eventually respond or silently return to idle
- This is easily mistaken for a crash, ignored wakeword, or frozen state

---

## 4. Existing Local Feedback Options

| Feedback type | Available | Notes |
|---|---|---|
| Local beep (Pi4) | **YES** | `play_beep(pa)` and `play_double_beep(pa)` in `audio_io.py`. Pure numpy+pyaudio. No GandalfAI dependency. 880 Hz / 660 Hz. |
| Local non-GandalfAI speech | **NO** | Local Piper binary is broken/deferred (issue log). All TTS routes through Kokoro (GandalfAI primary) or Piper-on-GandalfAI (fallback). Neither available before GandalfAI wakes. |
| LED/mouth cue without GandalfAI | **YES (already active)** | Orange pulse animation already runs during WoL wait via `waking_anim` thread in `ensure_gandalf_up`. |
| Log/web UI cue | **YES (already active)** | `[WOL] GandalfAI is offline -- sending Wake-on-LAN...` prints to console/service log. |

---

## 5. Options Compared

| Option | Description | Dependencies | Risk | Recommendation |
|---|---|---|---|---|
| A | Local beep only — new `play_wol_beep(pa)` (ascending 2-tone) immediately after WoL send | numpy, pyaudio (already present) | Minimal — same pattern as existing `play_beep`; ~360 ms; non-blocking for wakeword/recording | **Recommended** |
| B | Local spoken phrase only — pre-recorded WAV or local Piper | Local Piper (confirmed broken); or bundled WAV asset | Medium — local Piper broken; WAV requires new asset, packaging, volume normalization | Not recommended |
| C | Beep + spoken phrase | All deps from A + B | Medium — adds complexity; B has no confirmed local path | Not recommended at this time |
| D | Visual/log cue only | None (already implemented) | None | Insufficient — user needs audio signal, not just LEDs they may not be watching |

---

## 6. Recommended Minimal Design

**Option A: Local beep only**

### Trigger point
Inside `ensure_gandalf_up(leds, pa=None)`, immediately after `send_wol(...)` is called
and the WoL print fires — before the polling loop begins.

### Feedback
New `play_wol_beep(pa)` function in `audio_io.py`:
- Ascending 2-tone: 660 Hz (150 ms) + 880 Hz (150 ms), 60 ms gap between tones
- Total duration: ~360 ms
- Amplitude: same as `play_beep` (~6000 int16 scale)
- Distinct from: single wake beep (880 Hz), double follow-up beep (660+660 Hz)
- Signals to user: "acknowledged, working on it"
- Synchronous (~360 ms block) — acceptable given the WoL wait is 60–120 s

### Repeat / rate-limit behavior
Natural rate-limit already present. `ensure_gandalf_up` is only called after a wakeword
or button event. During the WoL polling loop, IRIS is blocked and cannot accept a new
wakeword. Therefore the WoL beep fires exactly once per wake cycle. No additional
rate-limit logic required.

### Behavior if GandalfAI wakes successfully
No change. After `ensure_gandalf_up` returns `True`, normal flow resumes. Normal path:
`play_beep` fires as usual. Sleep path: wake greeting TTS plays.
User hears: WoL beep → [wait] → normal wake beep or greeting.

### Behavior if GandalfAI fails to wake
No change from current behavior. `ensure_gandalf_up` returns `False`, LED error + 2 s
sleep + return to idle. The WoL beep already fired at the start; no additional failure
cue proposed in this plan.

### Config flag
Not needed now. If future tuning is desired, add `WOL_ACK_BEEP = True` to
`iris_config.json`. Defer unless the beep proves annoying in practice.

---

## 7. Files Likely Touched

| File | Change |
|---|---|
| `pi4/hardware/audio_io.py` | Add `play_wol_beep(pa)` function (~8 lines); export it |
| `pi4/assistant.py` | 1) Import `play_wol_beep`; 2) Add `pa=None` param to `ensure_gandalf_up`; 3) Call `play_wol_beep(pa)` after `send_wol(...)` inside the function; 4) Pass `pa` at both call sites (lines ~426, ~438) |

Total: 2 files, ~12 lines changed/added.

---

## 8. Risk

| Risk | Likelihood | Mitigation |
|---|---|---|
| Beep plays when GandalfAI is already up | None | Beep is inside the `if gandalf_is_up(): return True` false-branch only |
| Beep blocks wakeword detection | None | Wakeword detection is complete before this code path runs |
| Beep blocks mic / recording | None | `record_command` starts after `ensure_gandalf_up` returns |
| Beep audio teardown conflicts with later playback | Very low | `play_wol_beep` opens/closes its own stream; same pattern as `play_beep` |
| `pa` is None at call site | None | `pa` is constructed before the wakeword loop and passed explicitly |
| Double-beep if user re-triggers after Gandalf is up | None | Second call hits `gandalf_is_up() -> True` and returns immediately |

---

## 9. Rollback

```bash
git checkout HEAD -- pi4/assistant.py pi4/hardware/audio_io.py
```

If already deployed to Pi4:
```bash
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/assistant_backup.py /media/root-ro/home/pi/assistant.py
sudo cp /home/pi/hardware/audio_io_backup.py /media/root-ro/home/pi/hardware/audio_io.py
sync
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
sudo systemctl restart iris
```

---

## 10. Test Plan

| Scenario | Expected behavior |
|---|---|
| GandalfAI already awake, wakeword triggered | No WoL beep. Normal single beep fires. Recording starts normally. |
| GandalfAI asleep/offline, wakeword triggered | WoL beep fires immediately (~360 ms ascending tones). Orange LED animation runs during wait. When Gandalf up: normal wake beep + recording. |
| GandalfAI fails to wake (boot timeout) | WoL beep fires at start. LED error after timeout. No crash. Returns to idle. |
| User repeats wakeword during WoL wait | IRIS blocked in polling loop — wakeword cannot fire again. No double-beep. |
| Sleep-mode wakeword, GandalfAI offline | WoL beep fires after `_do_wake` (eyes wake first). LED animation. On Gandalf up: wake greeting TTS. |
| Sleep-mode wakeword, GandalfAI already up | No WoL beep. Wake greeting TTS fires directly. |
| Normal no-response regression | Existing play_beep, record, STT, LLM, TTS paths unchanged. No new delay when Gandalf is up. |

---

## 11. Recommended Implementation Prompt

```
IRIS FAST TASK MODE - IMPLEMENTATION

Repo: C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face
Branch: main (verify clean before starting)

Task: Add WoL acknowledgement beep to IRIS Pi4 runtime.
Approved design: docs/plans/PLAN_WOL_ACK_BEEP.md

Pre-read these files before writing anything:
  1. pi4/hardware/audio_io.py
  2. pi4/assistant.py

Changes:

FILE 1: pi4/hardware/audio_io.py
  - Add play_wol_beep(pa) after the play_double_beep function.
  - Ascending 2-tone: 660 Hz for 150 ms, 60 ms gap, 880 Hz for 150 ms.
  - Use the same numpy+pyaudio pattern as play_beep and play_double_beep.
  - Add play_wol_beep to the import list in assistant.py.

FILE 2: pi4/assistant.py
  - In the import from hardware.audio_io, add play_wol_beep.
  - Change ensure_gandalf_up(leds) signature to ensure_gandalf_up(leds, pa=None).
  - Inside ensure_gandalf_up, after send_wol(...) and its print statement, add:
        if pa is not None:
            play_wol_beep(pa)
  - Update both call sites of ensure_gandalf_up to pass pa:
      Sleep path  (~line 426): ensure_gandalf_up(leds, pa)
      Normal path (~line 438): ensure_gandalf_up(leds, pa)

Constraints:
  - Do not change any other logic in ensure_gandalf_up.
  - Do not touch waking_anim thread.
  - Do not move or reorder play_beep, play_double_beep.
  - Touch only the two files listed.

After writing:
  - Show diff for both files.
  - Do not deploy.
  - Do not commit unless I say so.
  - Provide rollback command.
```
